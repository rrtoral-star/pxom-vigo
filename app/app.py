"""
app.py — PXOM-Solo Consultor Normativo v3.0
Entrypoint único. Delega todo el RAG en RAGService.
"""

import os
import sys
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent  # pxom-solo/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

print("ROOT:", ROOT)
print("src path:", ROOT / "src")
print("sys.path:", [p for p in sys.path if "src" in p])

load_dotenv(dotenv_path=ROOT / ".env")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PXOM-Solo · Consultor Normativo Vigo",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (igual que antes) ─────────────────────────────────────────────────────
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
def get_service():
    from rag_service import RAGService
    return RAGService()


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

def render_result_cards(resultados):
    for r in resultados:
        fuente_str    = r.fuente or r.coleccion or ""
        fuente_limpia = fuente_str.lower().split()[0].rstrip(",")
        if "nhv" in fuente_limpia:              fuente_limpia = "nhv"
        elif "pxom" in fuente_limpia:           fuente_limpia = "pxom"
        color         = color_fuente(fuente_limpia)
        titulo_limpio = r.payload.get("articulo_titulo", "")
        texto_limpio  = r.payload.get("text", "")[:350]
        if len(r.payload.get("text", "")) > 350:
            texto_limpio += "..."
        label_str = fuente_limpia.upper() if fuente_limpia else "—"
        art_slug  = str(r.payload.get("articulo_numero", "")).replace(".", "-")

        wiki_file = ROOT / "wiki" / fuente_limpia / f"art-{art_slug}.md"

        st.markdown(
            f'<div class="result-card {color}">'
            f'<div class="result-card-label">{label_str} · Art. {r.payload.get("articulo_numero", "")}</div>'
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
    idioma_sel = st.radio(
        "Idioma de respuesta",
        ["Español", "Galego"],
        horizontal=True,
        key="idioma_sidebar",
    )


# ── Estado de memoria conversacional ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

idioma = "gl" if st.session_state.get("idioma_sidebar", "Español") == "Galego" else "es"

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

    # Mostrar historial de conversación
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    query = st.chat_input(
        placeholder="¿Cuál es la altura máxima permitida en zona R1? ¿Qué retranqueos exige la ordenanza U3?",
        key="chat_input_rag",
    )

    if query and query.strip():
        service = get_service()
        filtro_activo = build_filtro_fuente(st.session_state.filtro)

        with st.spinner("Buscando en la normativa..."):
            resultados = service.buscar_contexto(
                query=query.strip(),
                top_k=12,
                filtros=filtro_activo,
            )

        # Mostrar pregunta del usuario
        st.session_state.messages.append({"role": "user", "content": query.strip()})
        with st.chat_message("user"):
            st.markdown(query.strip())

        if not resultados:
            respuesta = (
                "No se encontraron fragmentos relevantes para esta consulta. "
                "Prueba a reformular la pregunta con términos más específicos."
            )
        else:
            with st.spinner("Generando respuesta..."):
                respuesta = service.generar_respuesta(
                    pregunta=query.strip(),
                    results=resultados,
                    historial=st.session_state.messages[:-1],  # excluir el mensaje actual que acabamos de añadir
                    idioma=idioma,
                )

        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            st.markdown(respuesta)

        if resultados:
            st.markdown('<div class="section-title">Artículos de referencia</div>', unsafe_allow_html=True)
            render_result_cards(resultados)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — CATASTRO (placeholder, la lógica completa está en la página dedicada)
# ════════════════════════════════════════════════════════════════════════════════
with tab_cat:
    st.info("Usa la página **🗺️ Consulta Catastral** en el menú lateral para consultas por referencia catastral o dirección.")