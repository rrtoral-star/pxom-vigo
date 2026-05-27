"""
rag_service.py - Servicio RAG v3.0
Único punto de verdad para: búsqueda normativa, GIS dual, generación de respuestas.
"""

import os
from typing import Optional
from dataclasses import dataclass, field

from pathlib import Path
from groq import Groq

# Añadir src al path si es necesario
_root = Path(__file__).resolve().parent.parent
import sys
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from retriever import RAGRetriever


# ============================================================
# ADAPTADOR: ChunkResult → objeto compatible con UI
# ============================================================
@dataclass
class HitAdapter:
    """Envuelve un ChunkResult para la UI."""
    score: float
    payload: dict
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    coleccion: str = ""
    fuente: str = ""

    @classmethod
    def from_chunk(cls, chunk_result):
        return cls(
            score=chunk_result.rerank_score,
            payload={
                "articulo_numero": chunk_result.articulo,
                "articulo_titulo": chunk_result.cabecera,
                "text": chunk_result.texto,
                "ordenanza": chunk_result.ordenanza,
                "fuente": chunk_result.fuente,
                "keywords": chunk_result.keywords,
                "titulo_normativa": getattr(chunk_result, "titulo_normativa", ""),
                "capitulo": getattr(chunk_result, "capitulo", ""),
                "seccion": getattr(chunk_result, "seccion", ""),
                "tablas_md": getattr(chunk_result, "tablas_md", ""),
                "tiene_tablas": getattr(chunk_result, "tiene_tablas", False),
            },
            rrf_score=chunk_result.rrf_score,
            rerank_score=chunk_result.rerank_score,
            coleccion=chunk_result.coleccion,
            fuente=chunk_result.fuente,
        )


# ============================================================
# SERVICIO RAG PRINCIPAL
# ============================================================
class RAGService:
    """
    Interfaz única para todo el pipeline RAG + GIS.
    """

    SCORE_MINIMO = 0.05
    MAX_TOKENS = 4096
    TEMPERATURA = 0.1
    MODELO_DEFAULT = "llama-3.3-70b-versatile"
    TOP_K_DEFAULT = 12

    SYSTEM_PROMPT = """Eres un asistente técnico-jurídico especializado en normativa urbanística y de habitabilidad de Vigo y Galicia.

Tu usuario es un arquitecto profesional que necesita respuestas precisas para su trabajo.

═══ FUENTES DISPONIBLES ═══
Puedes recibir fragmentos de:
- **PXOM Vigo**: Plan Xeral de Ordenación Municipal (ordenanzas, usos, edificabilidad, alturas, retranqueos, etc.)
- **NHV-2010 Habitabilidad**: Decreto 29/2010 (superficies mínimas, alturas, instalaciones)
- **NHV-2023 Habitabilidad**: Decreto 128/2023 (vigente, prevalece sobre 2010)
- **CTE**: Código Técnico de la Edificación (DB-SI, DB-SUA, DB-HS, DB-SE, etc.)

═══ IDIOMA ═══
Responde SIEMPRE en el idioma indicado en las instrucciones del sistema.

═══ FUENTES ═══
- Basa tu respuesta EXCLUSIVAMENTE en los fragmentos normativos proporcionados.
- NO inventes, NO extrapoles, NO añadas información de tu conocimiento general.
- Si los fragmentos no contienen la respuesta o son insuficientes, dilo de forma clara:
  "Los fragmentos consultados no contienen información suficiente sobre este punto.
   Se recomienda revisar directamente el PXOM o consultar con el servicio de urbanismo."

═══ JERARQUÍA NORMATIVA ═══
- NHV-2023 (Decreto 128/2023): VIGENTE. Prevalece siempre.
- NHV-2010 (Decreto 29/2010): DEROGADA por el Decreto 128/2023.
  Si un fragmento NHV-2010 contradice uno NHV-2023, cita el de 2023
  e indica expresamente que la versión anterior está derogada.
- CTE: Vigente en sus documentos básicos aplicables.

═══ CITAS ═══
- Cita SIEMPRE el artículo concreto: "Según el Art. 81.3…", "El Art. NHV-IA2 establece…"
- Indica la fuente cuando sea relevante: "(PXOM)" o "(NHV-2010)" o "(CTE DB-SE)"
- Cuando cites números (alturas, retranqueos, edificabilidad, parcela mínima, etc.),
  transcríbelos con exactitud. Un error numérico puede invalidar un proyecto.

═══ CONFLICTOS NORMATIVOS ═══
- Si dos fragmentos se contradicen, señálalo explícitamente y cita ambos artículos.
- No elijas uno sobre otro salvo que un fragmento indique expresamente su prevalencia.

═══ ESTRUCTURA DE RESPUESTA ═══
1. **Respuesta directa**: contesta la pregunta de forma concisa.
2. **Detalle normativo**: desarrolla con citas a artículos concretos.
3. **Condicionantes o excepciones**: si los fragmentos mencionan excepciones, inclúyelos.
4. **Artículos consultados**: lista los artículos que has utilizado con su fuente."""

    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("Se requiere GROQ_API_KEY")

        self.groq_client = Groq(api_key=self.groq_api_key)
        self.retriever = RAGRetriever()

    # ----------------------------------------------------------
    # BÚSQUEDA
    # ----------------------------------------------------------
    def buscar_contexto(
        self,
        query: str,
        top_k: int = None,
        colecciones: list = None,
        filtros: dict = None,
    ) -> list[HitAdapter]:
        """
        Busca chunks relevantes. Devuelve HitAdapter para la UI.
        """
        top_k = top_k or self.TOP_K_DEFAULT
        try:
            chunks = self.retriever.buscar(
                query=query,
                top_k=top_k,
                filtros=filtros,
                colecciones=colecciones,
                verbose=False,
            )
            hits = [HitAdapter.from_chunk(c) for c in chunks if c.rerank_score >= self.SCORE_MINIMO]
            return hits
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []

    # ----------------------------------------------------------
    # FORMATEAR CONTEXTO PARA LLM (enriquecido)
    # ----------------------------------------------------------
    def formatear_contexto(self, results: list[HitAdapter]) -> str:
        if not results:
            return "(Sin fragmentos relevantes)"

        bloques = []
        for i, hit in enumerate(results, 1):
            p = hit.payload
            fuente = p.get("fuente", "Desconocida")
            art_num = p.get("articulo_numero", "N/A")
            ordenanza = p.get("ordenanza", "")
            titulo = p.get("articulo_titulo", "")
            texto = p.get("text", "")

            # Campos estructurales que ya existen en Qdrant
            titulo_norm = p.get("titulo_normativa", "")
            cap = p.get("capitulo", "")
            sec = p.get("seccion", "")
            tablas = p.get("tablas_md", "")
            tiene_tablas = p.get("tiene_tablas", False)

            bloque = f"### [Fuente {i}] {fuente} | Art. {art_num}"
            if ordenanza:
                bloque += f" | Ordenanza: {ordenanza}"
            if titulo_norm:
                bloque += f"\nNormativa: {titulo_norm}"
            if cap:
                bloque += f"\nCapítulo: {cap}"
            if sec:
                bloque += f" | Sección: {sec}"
            if titulo:
                bloque += f"\nTítulo: {titulo}"

            bloque += f"\n\n{texto}"

            if tiene_tablas and tablas:
                bloque += f"\n\n[Tabla asociada]:\n{tablas}"

            bloques.append(bloque)

        return "\n\n---\n\n".join(bloques)

    # ----------------------------------------------------------
    # GENERAR RESPUESTA (con historial e idioma)
    # ----------------------------------------------------------
    def generar_respuesta(
        self,
        pregunta: str,
        results: list[HitAdapter],
        historial: list[dict] = None,
        idioma: str = "es",  # "es" o "gl"
        modelo: str = None
    ) -> str:
        modelo = modelo or self.MODELO_DEFAULT
        historial = historial or []

        if not results:
            return (
                "No se encontraron fragmentos relevantes para esta consulta. "
                "Prueba a reformular la pregunta con términos más específicos."
            )

        contexto = self.formatear_contexto(results)

        system = self.SYSTEM_PROMPT
        if idioma == "gl":
            system += (
                "\n\nResponde SIEMPRE en GALLEGO (galego). "
                "Usa terminología técnica galega: edificabilidade, recuamento, "
                "aproveitamento, planta baixa, aliñación, vivenda, solo urbano, "
                "Plan Xeral, medianeira, cuberta, voo, cédula de habitabilidade, etc."
            )
        else:
            system += "\n\nResponde SIEMPRE en ESPAÑOL."

        messages = [{"role": "system", "content": system}]
        # Incluir historial reciente (últimos 6 mensajes)
        messages.extend(historial[-6:])

        messages.append({
            "role": "user",
            "content": (
                f"Analiza los siguientes fragmentos normativos y responde a la pregunta.\n\n"
                f"PREGUNTA: {pregunta}\n\n"
                f"FRAGMENTOS:\n{contexto}\n\n"
                f"INSTRUCCIONES INTERNAS (no las incluyas en la respuesta final):\n"
                f"1. Identifica qué artículos son relevantes y por qué.\n"
                f"2. Si hay tablas, extrae los datos exactos.\n"
                f"3. Detecta contradicciones entre fragmentos.\n"
                f"4. Cita artículos concretos y fuentes.\n\n"
                f"RESPUESTA:"
            )
        })

        chat = self.groq_client.chat.completions.create(
            messages=messages,
            model=modelo,
            temperature=self.TEMPERATURA,
            max_tokens=self.MAX_TOKENS,
        )
        return chat.choices[0].message.content

    # ----------------------------------------------------------
    # CONSULTA DUAL: GIS + RAG
    # ----------------------------------------------------------
    def buscar_contexto_dual(
        self,
        rc: str,
        pregunta: str,
        top_k: int = None,
    ) -> dict:
        """
        Orquesta Supabase (GIS) + Qdrant (normativa).
        """
        from supabase import create_client

        top_k = top_k or self.TOP_K_DEFAULT

        # 1. Datos GIS desde Supabase
        sb = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        resp = sb.rpc("info_urbanistica", {"rc": rc}).execute()
        datos_gis = resp.data if resp.data else {"error": f"RC no encontrada: {rc}"}

        # 2. Ordenanza para filtrar búsqueda RAG
        ordenanza = datos_gis.get("zona_pxom", {}).get("ordenanza", "")

        # 3. Enriquecer query con la ordenanza detectada
        query_enriquecida = f"{pregunta} ordenanza {ordenanza}".strip() if ordenanza else pregunta

        # 4. Chunks desde Qdrant CON filtro
        hits = self.buscar_contexto(
            query=query_enriquecida,
            top_k=top_k,
            filtros={"ordenanza_codigo": ordenanza} if ordenanza else None,
        )

        # 5. Fallback: si filtro no devuelve nada, buscar SIN filtro
        if not hits and ordenanza:
            hits = self.buscar_contexto(
                query=pregunta,  # query original, no enriquecida con ordenanza repetida
                top_k=top_k,
                filtros=None,
            )

        return {
            "rc": rc,
            "datos_gis": datos_gis,
            "ordenanza": ordenanza,
            "hits": hits,
        }

    def generar_respuesta_dual(
        self,
        pregunta: str,
        contexto_dual: dict,
        historial: list[dict] = None,
        idioma: str = "es",
        modelo: str = None,
    ) -> str:
        """
        Genera respuesta combinando datos GIS + chunks normativa.
        """
        modelo = modelo or self.MODELO_DEFAULT
        historial = historial or []

        gis = contexto_dual["datos_gis"]
        zona = gis.get("zona_pxom", {})
        parc = gis.get("parcela", {})
        hits = contexto_dual["hits"]

        contexto_normativa = self.formatear_contexto(hits)

        system = self.SYSTEM_PROMPT
        if idioma == "gl":
            system += (
                "\n\nResponde SIEMPRE en GALLEGO (galego). "
                "Usa terminología técnica galega: edificabilidade, recuamento, "
                "aproveitamento, planta baixa, aliñación, vivenda, solo urbano, "
                "Plan Xeral, medianeira, cuberta, voo, cédula de habitabilidade, etc."
            )
        else:
            system += "\n\nResponde SIEMPRE en ESPAÑOL."

        prompt = f"""DATOS DE LA PARCELA (Catastro + PXOM):
- Referencia catastral : {contexto_dual['rc']}
- Superficie           : {parc.get('area_m2', 'N/D')} m²
- Vía / Número         : {parc.get('via', '')} nº {parc.get('numero', '')}
- Zona PXOM            : {zona.get('nombre', 'N/D')} (ordenanza {zona.get('ordenanza', '')})
- Clasificación        : {zona.get('clasificacion', 'N/D')}

════════════════════════════════════════
NORMATIVA APLICABLE:
════════════════════════════════════════
{contexto_normativa}

════════════════════════════════════════
PREGUNTA DEL ARQUITECTO:
{pregunta}

Responde siguiendo esta estructura:
1. Datos de la parcela (resume los datos anteriores)
2. Normativa aplicable (cita artículos concretos)
3. Conclusión y limitaciones detectadas"""

        messages = [{"role": "system", "content": system}]
        messages.extend(historial[-6:])
        messages.append({"role": "user", "content": prompt})

        chat = self.groq_client.chat.completions.create(
            messages=messages,
            model=modelo,
            temperature=self.TEMPERATURA,
            max_tokens=self.MAX_TOKENS,
        )
        return chat.choices[0].message.content