"""
00_extraer_nhv2023.py - Extrae PDF escaneado NHV-2023 con OCR (Tesseract)
y lo convierte al JSON estructurado del pipeline de ingesta.

Uso:
    pip install pdf2image pytesseract pillow groq python-dotenv
    python scripts/00_extraer_nhv2023.py

Requiere Tesseract instalado (ya confirmado v5.5)
Requiere poppler para pdf2image:
    https://github.com/oschwartz10612/poppler-windows/releases
    Descargar, extraer y añadir bin/ al PATH
"""

import os
import re
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

PDF_PATH    = "C:/PROY/pxom-solo/data/raw/NHV_es.pdf"
OUTPUT_PATH = "C:/PROY/pxom-solo/data/cleaned/normativa_habitabilidad_galicia_2023.json"
GROQ_MODEL  = "llama-3.3-70b-versatile"
LANG_OCR    = "spa"   # español — asegúrate de tener: tesseract --list-langs | grep spa

PROMPT_ESTRUCTURAR = """Eres un asistente que convierte texto normativo en JSON estructurado.

Dado el siguiente fragmento del Decreto 128/2023 de habitabilidad de viviendas de Galicia,
extrae la información en este formato JSON exacto:

{{
  "numero": "código de la sección (ej: 'A.', 'A.1.', 'B.2.', 'B.2.1.')",
  "titulo_descriptivo": "título descriptivo de la sección",
  "texto_completo": "texto completo de la sección",
  "contenido_estructurado": {{
    "parrafos": ["párrafo 1", "párrafo 2", ...]
  }},
  "contexto": {{
    "capitulo": "bloque principal (A, B o C)",
    "seccion": "subsección si existe, o cadena vacía"
  }},
  "referencias": []
}}

Devuelve SOLO el JSON, sin explicaciones ni marcadores de código.

TEXTO:
{texto}"""


def ocr_pdf(pdf_path: str) -> str:
    """Convierte PDF escaneado a texto usando pdf2image + Tesseract."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("❌ Faltan dependencias:")
        print("   pip install pdf2image pytesseract pillow")
        print("\nTambién necesitas poppler (para pdf2image en Windows):")
        print("   1. Descarga: https://github.com/oschwartz10612/poppler-windows/releases")
        print("   2. Extrae y añade la carpeta bin/ al PATH del sistema")
        raise

    print(f"  Convirtiendo PDF a imágenes...")
    # DPI 300 = buena calidad para OCR, 200 si va lento
    paginas = convert_from_path(pdf_path, dpi=300)
    total = len(paginas)
    print(f"  Total páginas: {total}")

    textos = []
    for i, pagina in enumerate(paginas, 1):
        texto = pytesseract.image_to_string(pagina, lang=LANG_OCR)
        textos.append(texto)
        if i % 5 == 0 or i == total:
            print(f"  OCR: {i}/{total} páginas...", end="\r")

    print(f"  OCR: {total}/{total} páginas ✓        ")
    return "\n".join(textos)


def detectar_secciones(texto: str) -> list[dict]:
    """
    Detecta secciones por el patrón A., A.1., A.1.1., B., B.1., etc.
    El OCR puede introducir ruido, así que usamos varios patrones.
    """
    patrones = [
        r'\n([A-C](?:\.\d+)+\.\s+[A-ZÁÉÍÓÚÑ][^\n]{3,})',   # A.1. Título
        r'\n([A-C]\.\s+[A-ZÁÉÍÓÚÑ][^\n]{5,})',               # A. Título
        r'\n([A-C](?:\.\d+)+\.[ \t]+\S[^\n]{3,})',            # flexible
    ]

    base = '\n' + texto
    matches = []
    for patron in patrones:
        matches = list(re.finditer(patron, base))
        if len(matches) >= 3:
            break

    if not matches:
        print("  ⚠ No se detectaron secciones → modo bloques")
        return dividir_en_bloques(texto)

    print(f"  ✓ {len(matches)} secciones detectadas")

    fragmentos = []
    for i, m in enumerate(matches):
        inicio = m.start()
        fin = matches[i+1].start() if i+1 < len(matches) else len(base)
        frag = base[inicio:fin].strip()
        if len(frag) > 100:
            primera = frag.split('\n')[0].strip()
            codigo = primera.split()[0] if primera else f"Sec.{i+1}"
            fragmentos.append({"indice": i+1, "codigo": codigo, "texto_raw": frag})

    print(f"  ✓ {len(fragmentos)} fragmentos con contenido suficiente")
    return fragmentos


def dividir_en_bloques(texto: str, min_chars: int = 400) -> list[dict]:
    """Fallback: divide por párrafos dobles."""
    bloques_raw = re.split(r'\n\s*\n', texto)
    bloques, buffer, idx = [], "", 1
    for b in bloques_raw:
        b = b.strip()
        if not b:
            continue
        buffer = (buffer + "\n\n" + b) if buffer else b
        if len(buffer) >= min_chars:
            bloques.append({"indice": idx, "codigo": f"Bloque.{idx}", "texto_raw": buffer})
            idx += 1
            buffer = ""
    if len(buffer) > 50:
        bloques.append({"indice": idx, "codigo": f"Bloque.{idx}", "texto_raw": buffer})
    print(f"  ✓ {len(bloques)} bloques generados")
    return bloques


def estructurar_con_groq(fragmento: dict, cliente: Groq) -> dict | None:
    texto = fragmento["texto_raw"]
    if len(texto) > 4000:
        texto = texto[:4000] + "..."
    try:
        chat = cliente.chat.completions.create(
            messages=[{"role": "user", "content": PROMPT_ESTRUCTURAR.format(texto=texto)}],
            model=GROQ_MODEL,
            temperature=0.0,
            max_tokens=2000,
        )
        resp = chat.choices[0].message.content.strip()
        if "```" in resp:
            resp = re.sub(r'```\w*\n?', '', resp).strip()
        return json.loads(resp)
    except json.JSONDecodeError as e:
        print(f" JSON err: {e}")
        return {
            "numero": fragmento.get("codigo", f"Sec.{fragmento['indice']}"),
            "titulo_descriptivo": fragmento["texto_raw"].split('\n')[0].strip()[:100],
            "texto_completo": fragmento["texto_raw"],
            "contenido_estructurado": {
                "parrafos": [p.strip() for p in fragmento["texto_raw"].split('\n\n') if p.strip()]
            },
            "contexto": {"capitulo": fragmento.get("codigo", "")[:1], "seccion": ""},
            "referencias": []
        }
    except Exception as e:
        print(f" Groq err: {e}")
        return None


def main():
    print("\n" + "="*60)
    print("EXTRACCIÓN NHV-2023 (OCR) — PDF → JSON")
    print("="*60)

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY no configurada"); return
    if not Path(PDF_PATH).exists():
        print(f"❌ PDF no encontrado: {PDF_PATH}"); return

    cliente = Groq(api_key=groq_api_key)

    # 1. OCR
    txt_path = PDF_PATH.replace(".pdf", "_raw.txt")
    if Path(txt_path).exists():
        print(f"\n[1/3] Texto OCR ya existe, reutilizando: {txt_path}")
        print(f"  (borra el .txt si quieres re-hacer el OCR)")
        with open(txt_path, encoding="utf-8") as f:
            texto = f.read()
    else:
        print("\n[1/3] OCR DEL PDF (puede tardar varios minutos)...")
        texto = ocr_pdf(PDF_PATH)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"  ✓ Texto OCR guardado: {txt_path}")

    print(f"  ✓ {len(texto):,} caracteres")
    print(f"  → Revisa {txt_path} para verificar que el OCR es correcto")

    # 2. Detectar secciones
    print("\n[2/3] DETECTANDO SECCIONES...")
    fragmentos = detectar_secciones(texto)
    if not fragmentos:
        print("❌ Sin fragmentos"); return

    print(f"\n  Preview primeros 5 fragmentos:")
    for f in fragmentos[:5]:
        print(f"  [{f['codigo']}] {f['texto_raw'][:80].replace(chr(10),' ')}...")

    ok = input(f"\n¿Estructurar {len(fragmentos)} secciones con Groq? [s/N] ")
    if ok.lower() != 's':
        print("Abortado."); return

    # 3. Estructurar con Groq
    print(f"\n[3/3] ESTRUCTURANDO CON GROQ...")
    articulos, errores = [], 0
    for i, frag in enumerate(fragmentos, 1):
        print(f"  [{i:02d}/{len(fragmentos)}] {frag['codigo']:<12}", end=" ")
        art = estructurar_con_groq(frag, cliente)
        if art:
            art["_decreto"] = "Decreto 128/2023"
            art["_fuente"] = "NHV-2023 Habitabilidad"
            articulos.append(art)
            print(f"✓ {art.get('titulo_descriptivo','')[:50]}")
        else:
            errores += 1
            print("✗")
        time.sleep(0.5)

    # 4. Guardar JSON
    output = {
        "metadata": {
            "decreto": "Decreto 128/2023, de 19 de octubre",
            "titulo": "Normas de habitabilidade de vivendas de Galicia",
            "version": "2023",
            "fuente": PDF_PATH,
            "total_articulos": len(articulos),
        },
        "articulos": articulos
    }
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ {len(articulos)} secciones | {errores} errores")
    print(f"✓ Output: {OUTPUT_PATH}")
    print(f"\nPróximo paso:")
    print(f"  Duplicar 02_ingestar_habitabilidad.py")
    print(f"  JSON_PATH  = normativa_habitabilidad_galicia_2023.json")
    print(f"  COLLECTION = habitabilidad_galicia_2023")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()