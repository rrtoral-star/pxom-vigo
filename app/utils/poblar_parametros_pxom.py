"""
poblar_parametros_pxom.py
=========================
Rellena los campos NULL de zonas_pxom en Supabase usando:
  - Qdrant (pxom_vigo_2025_v2) para recuperar chunks de normativa
  - Groq / Llama3 para extraer parámetros urbanísticos
  - Supabase para actualizar los registros

Uso:
    python poblar_parametros_pxom.py

Variables de entorno necesarias (.env):
    SUPABASE_URL
    SUPABASE_KEY
    QDRANT_URL
    QDRANT_KEY
    GROQ_API_KEY
"""

import json
import os
from dotenv import load_dotenv, dotenv_values
# ── Cargar variables de entorno ───────────────────────────────────────────────
# Cargar .env con ruta absoluta ANTES de todo lo demás
load_dotenv(r"C:\proy\pxom-solo\.env", override=True)

# Verificar carga (puedes borrar estas líneas después)
print("QDRANT_URL:", os.getenv("QDRANT_CLOUD_URL"))
print("GROQ:", os.getenv("GROQ_API_KEY"))

SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")
QDRANT_URL    = os.getenv("QDRANT_CLOUD_URL")
QDRANT_KEY    = os.getenv("QDRANT_CLOUD_API_KEY")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY")
from supabase import create_client
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from FlagEmbedding import BGEM3FlagModel
from groq import Groq




# ── Clientes ──────────────────────────────────────────────────────────────────
supabase    = create_client(SUPABASE_URL, SUPABASE_KEY)
qdrant      = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
embedder    = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

# ── Configuración ─────────────────────────────────────────────────────────────
COLLECTION = "pxom_vigo_2025_v2"

ORDENANZAS = [
    "U1.1", "U1.2", "U1.3",
    "U2", "U3", "U3.A",
    "U4", "U5",
    "U6.1", "U6.2", "U6.3", "U6.4", "U6.5", "U6.6",
    "U7", "U8",
    "U9.1", "U9.2", "U9.3", "U9.4",
]

SCHEMA = """{
  "edificabilidad": número m²/m² o null,
  "altura_maxima": número entero (plantas) o null,
  "ocupacion_maxima": número porcentaje 0-100 o null,
  "retranqueo_frontal": metros o null,
  "retranqueo_lateral": metros o null,
  "retranqueo_posterior": metros o null
}"""


# ── Funciones ─────────────────────────────────────────────────────────────────

def buscar_chunks(ordenanza_codigo: str) -> list[str]:

    # Intento 1: filtro directo
    resultados, _ = qdrant.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="ordenanza_codigo",
                    match=MatchValue(value=ordenanza_codigo)
                )
            ],
            should=[
                FieldCondition(key="define_edificabilidad", match=MatchValue(value=True)),
                FieldCondition(key="define_altura",         match=MatchValue(value=True)),
                FieldCondition(key="define_ocupacion",      match=MatchValue(value=True)),
                FieldCondition(key="define_retranqueos",    match=MatchValue(value=True)),
            ]
        ),
        limit=8,
        with_payload=True
    )

    chunks = [p.payload["texto_con_cabecera"] for p in resultados]

    # Fallback: query_points (API nueva de qdrant-client)
    if not chunks:
        print(f"   ⚠️  Sin chunks directos, usando búsqueda semántica...")
        query = f"ordenanza {ordenanza_codigo} edificabilidad altura retranqueo ocupación parcela mínima"
        vector = embedder.encode([query])["dense_vecs"][0].tolist()

        hits = qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(key="ambito", match=MatchValue(value="urbano"))
                ]
            ),
            limit=6,
            with_payload=True
        )
        chunks = [h.payload["texto_con_cabecera"] for h in hits.points]

    return chunks


def extraer_parametros(ordenanza_codigo: str, chunks: list[str]) -> dict:
    """
    Llama a Groq/Llama3 para extraer parámetros urbanísticos del texto.
    Devuelve un dict con los 6 campos del schema.
    """

    contexto = "\n\n---\n\n".join(chunks)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un extractor de parámetros urbanísticos del PXOM de Vigo. "
                    "Devuelve ÚNICAMENTE un JSON válido, sin markdown, sin explicaciones. "
                    "Si un valor no aparece explícitamente en el texto, usa null."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Ordenanza: {ordenanza_codigo}\n\n"
                    f"Normativa:\n{contexto}\n\n"
                    f"Extrae exactamente este JSON:\n{SCHEMA}"
                )
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    # Limpiar si Groq añade markdown igualmente
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def verificar_resultados():
    """Muestra resumen de NULLs restantes tras el proceso."""

    res = supabase.rpc("verificar_nulos_pxom").execute()
    if res.data:
        print("\n── Verificación final ──────────────────────────")
        for fila in res.data:
            print(fila)
    else:
        # Fallback si no existe la función RPC
        print("\n── Para verificar, ejecuta en Supabase SQL Editor: ──")
        print("""
SELECT
  COUNT(*) FILTER (WHERE edificabilidad IS NULL) AS sin_edificabilidad,
  COUNT(*) FILTER (WHERE altura_maxima IS NULL)  AS sin_altura,
  COUNT(*) FILTER (WHERE ocupacion_maxima IS NULL) AS sin_ocupacion,
  COUNT(*) as total
FROM zonas_pxom;
        """)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  POBLAR PARÁMETROS PXOM - zonas_pxom")
    print("=" * 55)
    print(f"  Colección Qdrant : {COLLECTION}")
    print(f"  Ordenanzas       : {len(ORDENANZAS)}")
    print("=" * 55 + "\n")

    errores = []

    for cod in ORDENANZAS:
        print(f"→ {cod}")

        # 1. Recuperar chunks
        chunks = buscar_chunks(cod)
        print(f"   {len(chunks)} chunks encontrados")

        if not chunks:
            print(f"   ❌ Sin contexto, saltando\n")
            errores.append((cod, "sin_chunks"))
            continue

        # 2. Extraer parámetros con Groq
        try:
            params = extraer_parametros(cod, chunks)
            print(f"   {params}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON inválido: {e}\n")
            errores.append((cod, "json_error"))
            continue
        except Exception as e:
            print(f"   ❌ Error Groq: {e}\n")
            errores.append((cod, str(e)))
            continue

        # 3. Actualizar Supabase
        try:
            supabase.table("zonas_pxom") \
                .update(params) \
                .eq("ordenanza", cod) \
                .execute()
            print(f"   ✅ Actualizado\n")
        except Exception as e:
            print(f"   ❌ Error Supabase: {e}\n")
            errores.append((cod, f"supabase: {e}"))

    # ── Resumen final ──
    print("=" * 55)
    print(f"  Completado. {len(ORDENANZAS) - len(errores)}/{len(ORDENANZAS)} ordenanzas OK")
    if errores:
        print(f"\n  Ordenanzas con error:")
        for cod, motivo in errores:
            print(f"    ⚠️  {cod}: {motivo}")
    print("=" * 55)

    verificar_resultados()


if __name__ == "__main__":
    main()