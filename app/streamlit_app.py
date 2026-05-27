"""
app.py — PXOM-Solo Consultor Normativo
Versión fusionada: RAG (PXOM · NHV · CTE) + Catastro
Uso: streamlit run app.py
"""

import os
import sys
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(".env"))

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PXOM-Solo · Consultor Normativo Vigo",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:        #0f0f0f;
    --surface:   #181818;
    --border:    #2a2a2a;
    --accent:    #c8a96e;
    --accent2:   #7eb8c8;
    --text:      #e8e4dc;
    --muted:     #7a7570;
    --pxom:      #c8a96e;
    --nhv:       #7eb8c8;
    --cte:       #a87ec8;
    --cat:       #7ec87e;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
[data-testid="stMainBlockContainer"] { padding: 2rem 3rem; max-width: 1100px; margin: 0 auto; }

/* ── Header ── */
.app-header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 2rem;
    margin-bottom: 2.5rem;
}
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: var(--accent);
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.1;
}
.app-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

/* ── Result card ── */
.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    border-radius: 2px;
}
.result-card.nhv  { border-left-color: var(--nhv); }
.result-card.cte  { border-left-color: var(--cte); }
.result-card.cat  { border-left-color: var(--cat); }
.result-card-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
}
.result-card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    color: var(--text);
    margin-bottom: 0.6rem;
}
.result-card-text {
    font-size: 0.88rem;
    color: #b8b4ac;
    line-height: 1.65;
}

/* ── LLM answer ── */
.answer-box {
    background: linear-gradient(135deg, #1a1a1a, #141414);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    padding: 1.5rem 1.75rem;
    border-radius: 2px;
    margin-bottom: 2rem;
}
.answer-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.answer-text {
    font-size: 0.95rem;
    line-height: 1.75;
    color: var(--text);
}

/* ── Section title ── */
.section-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}

/* ── Metric card catastro ── */
.cat-metric {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 2px solid var(--cat);
    padding: 1rem 1.25rem;
    border-radius: 2px;
    margin-bottom: 1rem;
}
.cat-metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.cat-metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: var(--cat);
}

/* ── Input overrides ── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder {
    color: #4a4640 !important;
}

/* ── Streamlit button overrides ── */
.stButton button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s !important;
}
.stButton button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border);
    gap: 0;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    padding: 0.5rem 1.25rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

.tag-pill {
    display: inline-block;
    background: #1f1f1f;
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 0.15rem 0.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    margin-right: 0.3rem;
    margin-top: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Recursos cacheados ────────────────────────────────────────────────────────
@st.cache_resource
def get_retriever():
    from retriever import RAGRetriever
    return RAGRetriever()

@st.cache_resource
def get_catastro():
    from utils.catastro_client import CatastroClient
    return CatastroClient(cache_dir="data/cache")

@st.cache_resource
def get_zoning():
    from utils.supabase_zoning import ZoningDB
    return ZoningDB()


# ── Groq LLM ─────────────────────────────────────────────────────────────────
def llamar_llm(query: str, contexto: str, system_extra: str = "") -> str:
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        system = (
            "Eres un experto en normativa urbanística y de edificación española. "
            "Responde de forma precisa y directa basándote ÚNICAMENTE en los artículos "
            "proporcionados como contexto. Si la respuesta no está en el contexto, "
            "indícalo claramente. No inventes normativa."
        )
        if system_extra:
            system += f" {system_extra}"
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Contexto normativo:\n\n{contexto}\n\n---\n\nPregunta: {query}"}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠ Error al consultar el LLM: {e}"


# ── Traducción a gallego ──────────────────────────────────────────────────────
TRADUCCION_PROMPT = """Eres un traductor profesional de español a gallego (galego),
especializado en terminología urbanística y normativa municipal.

Reglas:
- Traduce el texto COMPLETO al gallego. No omitas ni resumas nada.
- Mantén EXACTOS todos los números, medidas, porcentajes y referencias a artículos.
- NO cambies la estructura ni el formato.
- Terminología técnica: edificabilidad→edificabilidade, retranqueo→recuamento,
  aprovechamiento→aproveitamento, planta baja→planta baixa, alineación→aliñación,
  ordenanza→ordenanza, vivienda→vivenda, suelo urbano→solo urbano,
  Plan General→Plan Xeral, medianera→medianeira, cubierta→cuberta, vuelo→voo.
- Las citas a artículos se mantienen: "Art. 81.3" → "Art. 81.3"
Devuelve SOLO la traducción, sin comentarios."""

def traducir_a_galego(texto: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": TRADUCCION_PROMPT},
                {"role": "user", "content": texto},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=2048,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[Error traducción: {e}]\n\n{texto}"


# ── Helpers RAG ───────────────────────────────────────────────────────────────
FUENTES_CTE = [
    "cte-si", "cte-sua", "cte-hs", "cte-se", "cte-se-ae",
    "cte-se-a", "cte-se-c", "cte-se-f", "cte-se-m", "cte-hr", "cte-he"
]

def build_filtro_fuente(seleccion: str):
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
    if seleccion == "pxom":
        return Filter(must=[FieldCondition(key="fuente", match=MatchValue(value="pxom"))])
    elif seleccion == "nhv":
        return Filter(must=[FieldCondition(key="fuente", match=MatchValue(value="nhv"))])
    elif seleccion == "cte":
        return Filter(must=[FieldCondition(key="fuente", match=MatchAny(any=FUENTES_CTE))])
    return None

def color_fuente(fuente: str) -> str:
    if fuente == "pxom":                return "pxom"
    if fuente == "nhv":                 return "nhv"
    if fuente.startswith("cte"):        return "cte"
    return ""

def render_result_cards(resultados, retriever):
    for r in resultados:
        fuente_str    = r.fuente or r.coleccion or ""
        fuente_limpia = fuente_str.lower().split()[0].rstrip(",")
        if "nhv" in fuente_limpia:              fuente_limpia = "nhv"
        elif "pxom" in fuente_limpia:           fuente_limpia = "pxom"
        color         = color_fuente(fuente_limpia)
        titulo_limpio = r.cabecera.split("|")[-1].strip() if "|" in r.cabecera else r.cabecera
        texto_limpio  = r.texto.split("\n\n")[0][:350] if r.texto else ""
        if len(texto_limpio) == 350:
            texto_limpio += "..."
        label_str = fuente_limpia.upper() if fuente_limpia else "—"
        art_slug  = str(r.articulo).replace(".", "-") if r.articulo else ""

        wiki_file = ROOT / "wiki" / fuente_limpia / f"art-{art_slug}.md"

        st.markdown(
            f'<div class="result-card {color}">'
            f'<div class="result-card-label">{label_str} · Art. {r.articulo}</div>'
            f'<div class="result-card-title">{titulo_limpio}</div>'
            f'<div class="result-card-text">{texto_limpio}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if wiki_file.exists():
            with st.expander("→ Ver artículo completo"):
                md_content = wiki_file.read_text(encoding="utf-8")
                if md_content.startswith("---"):
                    partes = md_content.split("---", 2)
                    md_content = partes[2].strip() if len(partes) >= 3 else md_content
                st.markdown(md_content)
        else:
            st.markdown(
                '<p style="font-family:DM Mono,monospace;font-size:0.65rem;'
                'color:#4a4640;margin-top:0.3rem;">Artículo wiki pendiente</p>',
                unsafe_allow_html=True
            )


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <p class="app-title">PXOM · Solo</p>
    <p class="app-subtitle">Consultor Normativo — Vigo · PXOM · NHV · CTE · Catastro</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <p style="font-family:'DM Serif Display',serif;font-size:1.3rem;
    color:#c8a96e;margin-bottom:0.5rem;">Anotaciones</p>
    <p style="font-family:'DM Mono',monospace;font-size:0.65rem;
    color:#7a7570;letter-spacing:0.1em;text-transform:uppercase;
    margin-bottom:1.5rem;">Usuarios avanzados</p>
    """, unsafe_allow_html=True)

    nota_articulo = st.text_input("Artículo de referencia", placeholder="art-45")
    nota_usuario  = st.text_input("Tu nombre")
    nota_texto    = st.text_area("Nota aclaratoria", height=120)

    if st.button("Guardar nota"):
        if nota_texto and nota_articulo and nota_usuario:
            from datetime import datetime
            nota = {
                "usuario":      nota_usuario,
                "fecha":        datetime.now().isoformat(),
                "articulo_ref": nota_articulo,
                "texto":        nota_texto,
            }
            notas_dir = ROOT / "notes"
            notas_dir.mkdir(exist_ok=True)
            slug = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nota_articulo}"
            (notas_dir / f"{slug}.json").write_text(
                json.dumps(nota, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            st.success("✓ Nota guardada")
        else:
            st.warning("Completa todos los campos")

    st.markdown("---")
    idioma = st.radio(
        "Idioma de respuesta",
        ["Español", "Galego"],
        horizontal=True,
    )


# ── Tabs principales ──────────────────────────────────────────────────────────
tab_rag, tab_cat = st.tabs(["📋 Normativa", "🗺️ Catastro"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — RAG NORMATIVA
# ════════════════════════════════════════════════════════════════════════════════
with tab_rag:

    # Filtro de documento
    if "filtro" not in st.session_state:
        st.session_state.filtro = "all"

    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("📋 PXOM"):   st.session_state.filtro = "pxom"
    with col2:
        if st.button("🏠 NHV"):    st.session_state.filtro = "nhv"
    with col3:
        if st.button("🔧 CTE"):    st.session_state.filtro = "cte"
    with col4:
        if st.button("· Todo"):    st.session_state.filtro = "all"

    filtro_label = {
        "all":  "Todos los documentos",
        "pxom": "PXOM — Plan Xeral de Ordenación Municipal",
        "nhv":  "NHV — Normativa de Habitabilidade de Vivenda",
        "cte":  "CTE — Código Técnico de la Edificación",
    }
    st.markdown(
        f'<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;'
        f'color:#7a7570;letter-spacing:0.1em;margin-bottom:1.5rem;">'
        f'▸ {filtro_label[st.session_state.filtro]}</p>',
        unsafe_allow_html=True
    )

    query = st.text_area(
        label="",
        placeholder="¿Cuál es la altura máxima permitida en zona R1? ¿Qué retranqueos exige la ordenanza U3?",
        height=90,
        key="query_input",
        label_visibility="collapsed",
    )
    buscar = st.button("Consultar →", type="primary", key="btn_rag")

    if buscar and query.strip():
        retriever = get_retriever()
        filtro_activo = build_filtro_fuente(st.session_state.filtro)

        with st.spinner("Buscando en la normativa..."):
            resultados = retriever.buscar(
                query=query.strip(),
                top_k=5,
                filtros=filtro_activo,
                verbose=False,
            )

        if not resultados:
            st.markdown(
                '<p style="color:#7a7570;font-size:0.9rem;">Sin resultados para esta consulta.</p>',
                unsafe_allow_html=True
            )
        else:
            contexto = retriever.formatear_contexto(resultados)

            with st.spinner("Generando respuesta..."):
                respuesta = llamar_llm(query.strip(), contexto)

            if idioma == "Galego":
                with st.spinner("Traducindo ao galego..."):
                    respuesta = traducir_a_galego(respuesta)

            st.markdown(
                f'<div class="answer-box">'
                f'<div class="answer-label">▸ Respuesta</div>'
                f'<div class="answer-text">{respuesta}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown('<div class="section-title">Artículos de referencia</div>', unsafe_allow_html=True)
            render_result_cards(resultados, retriever)

    elif buscar and not query.strip():
        st.warning("Escribe una consulta primero.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — CATASTRO
# ════════════════════════════════════════════════════════════════════════════════
with tab_cat:

    st.markdown("""
    <p style="font-family:'DM Mono',monospace;font-size:0.7rem;
    color:#7a7570;letter-spacing:0.1em;margin-bottom:1.5rem;">
    ▸ Introduce una Referencia Catastral para obtener zona PXOM y normativa aplicable</p>
    """, unsafe_allow_html=True)

    col_rc, col_btn = st.columns([3, 1])
    with col_rc:
        rc_input = st.text_input(
            "Referencia Catastral",
            placeholder="Ej: 4643468NG2744S0001WX",
            max_chars=20,
            key="rc_input",
            label_visibility="visible",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar_rc = st.button("Consultar →", key="btn_cat")

    pregunta_rc = st.text_input(
        "Pregunta sobre la parcela (opcional)",
        placeholder="¿Qué usos están permitidos? ¿Cuál es la edificabilidad máxima?",
        key="pregunta_rc",
        label_visibility="visible",
    )

    if buscar_rc and rc_input.strip():
        rc = rc_input.strip().upper()

        if not pregunta_rc.strip():
            pregunta_rc = (
                "¿Cuál es la normativa aplicable, usos permitidos "
                "y parámetros de edificación para esta parcela?"
            )

        # ── 1. Datos catastrales ──────────────────────────────────────────────
        with st.spinner("Consultando Catastro..."):
            try:
                catastro = get_catastro()
                info_cat = catastro.consultar_por_referencia(rc)
            except Exception as e:
                info_cat = None
                st.warning(f"No se pudo conectar al Catastro: {e}")

        # ── 2. Zona PXOM (PostGIS) ────────────────────────────────────────────
        with st.spinner("Consultando zona PXOM..."):
            try:
                zoning = get_zoning()
                zona_data = zoning.consultar_zona_por_rc(rc)
                st.write(zona_data)
            except Exception as e:
                zona_data = None
                st.warning(f"No se pudo consultar la zona PXOM: {e}")

        # ── 3. Mostrar métricas de parcela ────────────────────────────────────
        st.markdown('<div class="section-title">Datos de la parcela</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        if info_cat:
            col1.metric("Superficie", f"{info_cat.get('superficie', '?')} m²")
            col2.metric("Uso", info_cat.get("uso", "?"))
            col3.metric("Año construcción", info_cat.get("anio_construccion", "?"))
            col4.metric("RC", rc[:14])
            if info_cat.get("direccion"):
                st.caption(f"📍 {info_cat.get('direccion', '')}")
        else:
            col1.metric("RC", rc[:14])
            col2.metric("Superficie", "—")
            col3.metric("Uso", "—")
            col4.metric("Año", "—")

        # ── 4. Mostrar zona PXOM ──────────────────────────────────────────────
        st.markdown('<div class="section-title">Zona PXOM</div>', unsafe_allow_html=True)

        ordenanza_codigo = None

        if zona_data:
            # zona_data puede ser lista (RPC Supabase) o dict
            zona = zona_data[0] if isinstance(zona_data, list) else zona_data
            ordenanza_codigo = zona.get("ordenanza_codigo") or zona.get("ordenanza")

            col_z1, col_z2, col_z3 = st.columns(3)
            col_z1.metric("Ordenanza", zona.get("ordenanza", "?"))
            col_z2.metric("Clasificación", zona.get("clasificacion", "?"))
            col_z3.metric("Calificación", zona.get("calificacion", "?"))

            if zona.get("nombre"):
                st.caption(f"**{zona.get('nombre')}**")
        else:
            st.markdown(
                '<p style="color:#7a7570;font-size:0.9rem;">'
                'No se encontró zona PXOM para esta referencia catastral. '
                'Verifica que la parcela esté en el municipio de Vigo.</p>',
                unsafe_allow_html=True
            )

        # ── 5. Normativa aplicable (RAG filtrado por ordenanza) ───────────────
        st.markdown('<div class="section-title">Normativa aplicable</div>', unsafe_allow_html=True)

        with st.spinner("Buscando normativa..."):
            try:
                retriever = get_retriever()

                # Si tenemos ordenanza, filtramos por ella; si no, búsqueda libre
                filtro_ordenanza = None
                if ordenanza_codigo:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue
                    filtro_ordenanza = Filter(
                        must=[FieldCondition(
                            key="ordenanza_codigo",
                            match=MatchValue(value=str(ordenanza_codigo))
                        )]
                    )

                resultados_cat = retriever.buscar(
                    query=pregunta_rc,
                    top_k=5,
                    filtros=filtro_ordenanza,
                    verbose=False,
                )

                # Fallback: si el filtro por ordenanza no devuelve nada, búsqueda libre
                if not resultados_cat and filtro_ordenanza:
                    resultados_cat = retriever.buscar(
                        query=pregunta_rc,
                        top_k=5,
                        filtros=None,
                        verbose=False,
                    )

            except Exception as e:
                resultados_cat = []
                st.error(f"Error en búsqueda RAG: {e}")

        if resultados_cat:
            contexto_cat = retriever.formatear_contexto(resultados_cat)

            system_extra = ""
            if ordenanza_codigo:
                system_extra = (
                    f"La parcela consultada pertenece a la ordenanza {ordenanza_codigo}. "
                    "Centra la respuesta en esa ordenanza cuando sea posible."
                )

            with st.spinner("Generando respuesta normativa..."):
                respuesta_cat = llamar_llm(pregunta_rc, contexto_cat, system_extra)

            if idioma == "Galego":
                with st.spinner("Traducindo ao galego..."):
                    respuesta_cat = traducir_a_galego(respuesta_cat)

            st.markdown(
                f'<div class="answer-box">'
                f'<div class="answer-label">▸ Normativa aplicable</div>'
                f'<div class="answer-text">{respuesta_cat}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown('<div class="section-title">Artículos consultados</div>', unsafe_allow_html=True)
            render_result_cards(resultados_cat, retriever)

        else:
            st.markdown(
                '<p style="color:#7a7570;font-size:0.9rem;">'
                'No se encontró normativa específica para esta consulta.</p>',
                unsafe_allow_html=True
            )

    elif buscar_rc and not rc_input.strip():
        st.warning("Introduce una Referencia Catastral.")
