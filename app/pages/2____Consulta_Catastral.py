"""
Página V3.1: Consulta Catastral Completa
Fusión V2 (display completo) + V3 (memoria conversacional + RAGService)

Modos de búsqueda:
  1. Por dirección (geocoder → catastro, con fallback callejero Catastro)
  2. Por RC directa (parcela 14 dígitos o unidad 20 dígitos)

Filtros opcionales de unidad: escalera, planta, puerta/letra
Memoria conversacional por parcela activa.
"""

import streamlit as st
import sys
import os
import re
import pandas as pd
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT_PROJ = Path(__file__).resolve().parent.parent.parent  # pxom-solo/
sys.path.insert(0, str(ROOT_PROJ / "src"))
sys.path.insert(0, str(ROOT_PROJ / "app"))
sys.path.insert(0, str(ROOT_PROJ / "app" / "utils"))

from rag_service import RAGService
from geocoding import GeocodingClient
from arcgis_client import ArcGISClient
from catastro_client import CatastroClient
from supabase_zoning import ZoningDB

# ── Configuración página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Consulta Catastral - PXOM Vigo",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Consulta Catastral Completa")
st.markdown("**Sistema integrado:** Geocodificación + ArcGIS + Catastro + PostGIS + Normativa")

with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Esta herramienta integra:**
    - 🗺️ Geocodificación de direcciones
    - 📍 Consulta de zona PXOM (PostGIS)
    - 🏛️ Datos del Catastro oficial
    - 📊 Base de datos PostGIS
    - 📋 Consulta normativa aplicable por ordenanza

    **Modos de búsqueda:**
    - Por dirección (calle + número)
    - Por referencia catastral directa

    **Filtros opcionales:**
    - Escalera, planta, puerta/letra
    """)

    idioma_sel = st.radio(
        "Idioma de respuesta",
        ["Español", "Galego"],
        horizontal=True,
        key="idioma_cat",
    )

idioma = "gl" if st.session_state.get("idioma_cat", "Español") == "Galego" else "es"

# ── Inicializar clientes ─────────────────────────────────────────────────────
@st.cache_resource
def init_clients():
    return {
        'geocoding': GeocodingClient(),
        'arcgis':    ArcGISClient(),
        'catastro':  CatastroClient(),
        'supabase':  ZoningDB(),
    }

@st.cache_resource
def get_service():
    return RAGService()

clients = init_clients()
service = get_service()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def filtrar_unidad(unidades, escalera, planta, puerta):
    def norm(v):
        v = str(v).strip().upper()
        return str(int(v)) if v.isdigit() else v
    resultado = unidades
    if escalera:
        resultado = [u for u in resultado if norm(u.get('escalera', '')) == norm(escalera)]
    if planta:
        resultado = [u for u in resultado if norm(u.get('planta', '')) == norm(planta)]
    if puerta:
        resultado = [u for u in resultado if norm(u.get('puerta', '')) == norm(puerta)]
    return resultado


def procesar_construcciones(construcciones):
    unidades = []
    i = 0
    while i < len(construcciones):
        c = construcciones[i]
        uso = c.get('uso', '').upper()
        if 'COMUN' not in uso and 'COMÚN' not in uso:
            unidad = c.copy()
            unidad['elem_comun'] = 0
            if i + 1 < len(construcciones):
                siguiente = construcciones[i + 1]
                uso_sig = siguiente.get('uso', '').upper()
                if 'COMUN' in uso_sig or 'COMÚN' in uso_sig:
                    unidad['elem_comun'] = siguiente.get('superficie', 0) or 0
                    i += 1
            unidades.append(unidad)
        i += 1

    agrupadas = {}
    for u in unidades:
        ref_u = u.get('ref_catastral', 'SIN_REF')
        if ref_u in agrupadas:
            agrupadas[ref_u]['superficie'] += u.get('superficie', 0)
            agrupadas[ref_u]['elem_comun'] += u.get('elem_comun', 0)
            for campo in ('planta', 'puerta', 'escalera'):
                if not agrupadas[ref_u].get(campo) and u.get(campo):
                    agrupadas[ref_u][campo] = u.get(campo)
        else:
            agrupadas[ref_u] = u.copy()

    return list(agrupadas.values())


def mostrar_tabla_unidades(unidades, titulo=None):
    if titulo:
        st.markdown(f"**{titulo}**")
    datos_tabla = []
    sup_total = 0
    for u in unidades:
        sup_c  = u.get('superficie', 0) or 0
        elem_c = u.get('elem_comun', 0)
        total  = sup_c + elem_c
        sup_total += total
        datos_tabla.append({
            'Ref. Catastral':  u.get('ref_catastral', 'N/A'),
            'Escalera':        u.get('escalera', ''),
            'Planta':          u.get('planta', ''),
            'Puerta':          u.get('puerta', ''),
            'Uso':             u.get('uso', ''),
            'Sup. Construida': f"{sup_c:.0f} m²" if sup_c else 'N/A',
            'Elem. Comunes':   f"{elem_c:.0f} m²" if elem_c else '-',
            'Total':           f"{total:.0f} m²",
        })
    st.info(f"**{len(unidades)} unidades | Superficie total: {sup_total:.0f} m²**")
    df = pd.DataFrame(datos_tabla)
    if 'Planta' in df.columns:
        df = df.sort_values(['Escalera', 'Planta'], na_position='first')
    st.dataframe(df, hide_index=True, use_container_width=True)
    return sup_total


def mostrar_zona_postgis(catastro_result, zona_supabase_coords, clients):
    st.markdown("---")
    st.subheader("💾 Zona PXOM (PostGIS)")

    zona_rc_cache = None
    ref_para_zona = None

    if catastro_result:
        ref_para_zona = (catastro_result.get('ref_catastral', '') or '')[:14]

    if ref_para_zona:
        with st.spinner("Consultando zona por RC catastral..."):
            zona_rc = clients['supabase'].consultar_zona_por_rc(ref_para_zona)
        zona_rc_cache = zona_rc

        if zona_rc and not zona_rc.get('error'):
            parc   = zona_rc.get('parcela', {})
            zona   = zona_rc.get('zona_pxom', {})
            metodo = zona.get('metodo', 'centroide')

            if metodo == 'proximidad':
                st.warning("⚠️ Zona asignada por proximidad (parcela sin cobertura en planimetría PXOM)")
            else:
                st.success("✅ Zona verificada por RC catastral (máxima precisión)")

            col_z1, col_z2 = st.columns(2)
            col_z1.metric("Ordenanza",     zona.get('ordenanza')     or 'Sin datos')
            col_z2.metric("Clasificación", zona.get('clasificacion') or 'Sin datos')
            nombre = zona.get('nombre') or ''
            if nombre:
                st.markdown(f"**{nombre}**")
            st.caption(f"Superficie catastral: {parc.get('area_m2', '?')} m²")
        else:
            if zona_supabase_coords:
                st.info("ℹ️ Zona por coordenadas (RC no encontrada en PostGIS)")
                st.markdown(f"""
                **Código:** {zona_supabase_coords.get('codigo', 'N/A')}
                **Ordenanza:** {zona_supabase_coords.get('ordenanza', 'N/A')}
                **Clasificación:** {zona_supabase_coords.get('clasificacion', 'N/A')}
                """)
            else:
                st.warning("⚠️ Sin datos de zona en PostGIS")
    else:
        if zona_supabase_coords:
            st.info("ℹ️ Zona por coordenadas (sin RC disponible)")
            st.markdown(f"""
            **Código:** {zona_supabase_coords.get('codigo', 'N/A')}
            **Ordenanza:** {zona_supabase_coords.get('ordenanza', 'N/A')}
            **Clasificación:** {zona_supabase_coords.get('clasificacion', 'N/A')}
            """)
        else:
            st.warning("⚠️ Sin datos de zona en PostGIS")

    return zona_rc_cache


# ── FORMULARIO DE BÚSQUEDA ───────────────────────────────────────────────────
st.subheader("📍 Búsqueda")

if "ej_dir" not in st.session_state:
    st.session_state.ej_dir = ""
if "ej_rc" not in st.session_state:
    st.session_state.ej_rc = ""

col_ej1, col_ej2, col_ej3, col_ej4 = st.columns(4)
with col_ej1:
    if st.button("📍 García Barbón 15"):
        st.session_state.ej_dir = "Rúa García Barbón 15"
        st.session_state.ej_rc  = ""
        st.rerun()
with col_ej2:
    if st.button("📍 Urzaiz 1"):
        st.session_state.ej_dir = "Rúa Urzaiz 1"
        st.session_state.ej_rc  = ""
        st.rerun()
with col_ej3:
    if st.button("📍 Camelias 100"):
        st.session_state.ej_dir = "Avenida Camelias 100"
        st.session_state.ej_rc  = ""
        st.rerun()
with col_ej4:
    if st.button("🔑 RC ejemplo"):
        st.session_state.ej_dir = ""
        st.session_state.ej_rc  = "4643468NG2744S"
        st.rerun()

col_dir, col_rc, col_btn = st.columns([3, 2, 1])

with col_dir:
    direccion = st.text_input(
        "Dirección en Vigo",
        value=st.session_state.ej_dir,
        placeholder="Ej: Rúa Urzaiz 1, Av. Camelias 100, Camiño Seara 3...",
        help="Introduce calle y número. Si no funciona, usa la RC directa."
    )

with col_rc:
    rc_directa = st.text_input(
        "Referencia Catastral (opcional)",
        value=st.session_state.ej_rc,
        placeholder="Ej: 3065015NG2726N",
        max_chars=20,
        help="14 dígitos = parcela. 20 dígitos = unidad. Tiene prioridad sobre dirección."
    ).strip().upper()

with col_btn:
    st.write("")
    st.write("")
    consultar = st.button("🔍 Consultar", type="primary", use_container_width=True)

with st.expander("🔎 Filtrar por unidad (opcional)", expanded=False):
    st.caption("Rellena los campos que conozcas para localizar una unidad específica.")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_escalera = st.text_input("Escalera",       placeholder="Ej: A, 1...").strip().upper()
    with col_f2:
        filtro_planta   = st.text_input("Planta",         placeholder="Ej: 01, 02, SS...").strip().upper()
    with col_f3:
        filtro_puerta   = st.text_input("Puerta / Letra", placeholder="Ej: 01, IZ, DR...").strip().upper()
    with col_f4:
        st.write("")

# ── Inicializar memoria ──────────────────────────────────────────────────────
if "cat_messages" not in st.session_state:
    st.session_state.cat_messages = []
if "cat_context" not in st.session_state:
    st.session_state.cat_context = {}

# ── LÓGICA PRINCIPAL ─────────────────────────────────────────────────────────

hay_busqueda = consultar and (direccion or rc_directa)

if hay_busqueda:

    st.markdown("---")

    catastro_result      = None
    geo_result           = None
    lat = lon            = None
    zona_arcgis          = None
    zona_supabase_coords = None
    usos_resumen         = {}

    # ── MODO A: RC DIRECTA ───────────────────────────────────────────────────
    if rc_directa:
        st.info(f"🔑 Consultando por RC directa: `{rc_directa}`")

        with st.spinner("Consultando Catastro por RC..."):
            catastro_result = clients['catastro'].consultar_por_referencia(rc_directa)

        if not catastro_result and len(rc_directa) == 14:
            st.warning("⚠️ RC de parcela con posible división horizontal. Intentando por coordenadas...")
            try:
                from supabase import create_client
                sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                resp_centroide = sb.rpc('get_centroide_parcela', {'rc': rc_directa}).execute()
                if resp_centroide and resp_centroide.data:
                    cen   = resp_centroide.data
                    lat_c = cen.get('lat')
                    lon_c = cen.get('lon')
                    if lat_c and lon_c:
                        catastro_result = clients['catastro'].consultar_por_coordenadas(lat_c, lon_c)
                        if catastro_result:
                            st.info("✅ Encontrado por coordenadas de la parcela")
            except Exception as e:
                st.caption(f"⚠️ Fallback coords falló: {e}")

        if not catastro_result:
            st.error(f"❌ No se encontraron datos para la RC `{rc_directa}`.")
            st.stop()

    # ── MODO B: DIRECCIÓN ────────────────────────────────────────────────────
    else:
        with st.spinner("🗺️ Geocodificando dirección..."):
            geo_result = clients['geocoding'].geocode(direccion)

        if not geo_result:
            # Fallback: callejero Catastro
            numero_fallback = None
            nombre_fallback = None

            m_num = re.search(r'\b(\d+)\b', direccion)
            if m_num:
                numero_fallback = m_num.group(1)
                nombre_fallback = re.sub(r'\b\d+\b', '', direccion).strip()
                _QUITAR = ('estrada ', 'carretera ', 'ctra. ', 'camiño ', 'camino ',
                           'rúa ', 'rua ', 'avenida ', 'av. ', 'plaza ', 'praza ',
                           'paseo ', 'travesía ', 'lugar ', 'calle ', 'c/ ')
                nb_lower = nombre_fallback.lower()
                for q in _QUITAR:
                    if nb_lower.startswith(q):
                        nombre_fallback = nombre_fallback[len(q):].strip()
                        break
                nombre_fallback = nombre_fallback.strip(' ,')

            if nombre_fallback:
                with st.spinner(f"🔎 Buscando '{nombre_fallback}' en callejero Catastro..."):
                    calles_encontradas = clients['catastro'].buscar_calles(
                        'PONTEVEDRA', 'VIGO', nombre_fallback.upper()
                    )
                if calles_encontradas:
                    if len(calles_encontradas) == 1:
                        calle = calles_encontradas[0]
                        st.info(f"✅ Vial encontrado: {calle['tipo']} {calle['nombre']}")
                        with st.spinner("Consultando Catastro..."):
                            catastro_result = clients['catastro'].consultar_por_direccion(
                                provincia='PONTEVEDRA', municipio='VIGO',
                                tipo_via=calle['tipo'], nombre_via=calle['nombre'],
                                numero=numero_fallback or '1'
                            )
                    else:
                        st.warning(f"⚠️ {len(calles_encontradas)} viales encontrados. Selecciona el correcto:")
                        opciones  = [f"{c['tipo']} {c['nombre']}" for c in calles_encontradas]
                        seleccion = st.selectbox("Selecciona el vial:", opciones, key="selector_calle")
                        if st.button("✅ Usar este vial", key="btn_usar_calle"):
                            idx   = opciones.index(seleccion)
                            calle = calles_encontradas[idx]
                            with st.spinner("Consultando Catastro..."):
                                catastro_result = clients['catastro'].consultar_por_direccion(
                                    provincia='PONTEVEDRA', municipio='VIGO',
                                    tipo_via=calle['tipo'], nombre_via=calle['nombre'],
                                    numero=numero_fallback or '1'
                                )
                        else:
                            st.stop()
                else:
                    st.error("❌ No se pudo geocodificar ni encontrar el vial. Usa la RC directa.")
                    st.stop()
            else:
                st.error("❌ No se pudo geocodificar la dirección. Usa la RC directa.")
                st.stop()

        if geo_result:
            st.success(f"✅ Dirección encontrada: {geo_result['direccion_completa']}")
            lat = geo_result['lat']
            lon = geo_result['lon']
            st.info(f"📍 **Coordenadas:** {lat:.6f}, {lon:.6f}")

            with st.spinner("Consultando PostGIS..."):
                zona_supabase_coords = clients['supabase'].consultar_zona(lat, lon)

        if geo_result and not catastro_result:
            with st.spinner("Consultando Catastro..."):
                match_numero = re.search(r'\b(\d+)\b', direccion)
                if match_numero:
                    numero             = match_numero.group(1)
                    direccion_completa = geo_result['direccion_completa']
                    dc                 = direccion_completa.lower()

                    tipo_via   = 'RU'
                    nombre_via = None

                    if 'rúa' in dc or 'rua' in dc:
                        tipo_via = 'RU'
                        m = re.search(r'r[uú]a\s+(?:d[oa]s?\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()
                    elif 'avenida' in dc:
                        tipo_via = 'AV'
                        m = re.search(r'avenida\s+(?:de\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()
                    elif 'praza' in dc or 'plaza' in dc:
                        tipo_via = 'PZ'
                        m = re.search(r'p(?:ra)?za\s+(?:d[oa]s?\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()
                    elif 'camiño' in dc or 'camino' in dc:
                        tipo_via = 'CM'
                        m = re.search(r'cami[nñ]o\s+(?:d[oa]s?\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()
                    elif 'estrada' in dc or 'carretera' in dc:
                        tipo_via = 'CR'
                        m = re.search(r'(?:estrada|carretera)\s+(?:d[oa]s?\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()
                    elif 'paseo' in dc:
                        tipo_via = 'PS'
                        m = re.search(r'paseo\s+(?:de\s+)?([^,]+)', direccion_completa, re.IGNORECASE)
                        if m: nombre_via = m.group(1).strip().upper()

                    _FALLBACKS = {
                        'RU': ['AV', 'CL', 'CM', 'CR', 'PZ'],
                        'AV': ['RU', 'CL', 'PS'],
                        'CM': ['CR', 'RU'],
                        'CR': ['CM', 'RU'],
                        'PZ': ['RU'],
                        'PS': ['AV', 'RU'],
                    }

                    if nombre_via:
                        catastro_result = clients['catastro'].consultar_por_direccion(
                            provincia='PONTEVEDRA', municipio='VIGO',
                            tipo_via=tipo_via, nombre_via=nombre_via, numero=numero
                        )
                        if not catastro_result:
                            for tipo_alt in _FALLBACKS.get(tipo_via, ['RU', 'AV']):
                                catastro_result = clients['catastro'].consultar_por_direccion(
                                    provincia='PONTEVEDRA', municipio='VIGO',
                                    tipo_via=tipo_alt, nombre_via=nombre_via, numero=numero
                                )
                                if catastro_result:
                                    break

                if not catastro_result and lat and lon:
                    catastro_result = clients['catastro'].consultar_por_coordenadas(lat, lon)

    # ── MOSTRAR RESULTADOS ───────────────────────────────────────────────────
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("🗺️ Zona PXOM")

        if lat and lon:
            with st.spinner("Consultando ArcGIS..."):
                zona_arcgis = clients['arcgis'].consultar_zona(lat, lon)

            if zona_arcgis and zona_arcgis.get('ordenanza'):
                with st.expander("📡 ArcGIS (referencia por coordenadas)", expanded=False):
                    st.markdown(f"""
                    **Clasificación:** {zona_arcgis.get('clasificacion', 'N/A')}
                    **Ordenanza:** {zona_arcgis.get('ordenanza', 'N/A')}
                    **Nombre:** {zona_arcgis.get('nombre', 'N/A')}
                    """)
                    if zona_arcgis.get('altura'):
                        st.metric("Altura Máxima", f"{zona_arcgis['altura']} m")
            else:
                st.warning("⚠️ ArcGIS: no se encontró zona PXOM")
        else:
            st.info("ℹ️ ArcGIS no disponible en modo RC directa (sin coordenadas)")

    with col_der:
        st.subheader("🏛️ Datos Catastrales")

        if catastro_result:
            st.success("✅ Datos catastrales obtenidos")

            ref             = catastro_result.get('ref_catastral', 'N/A')
            ref_parcela     = ref[:14] if len(ref) >= 14 else ref
            tipo_finca      = catastro_result.get('tipo_finca', '')
            direccion_finca = catastro_result.get('direccion_finca', '')
            dir_consultada  = catastro_result.get('direccion', '')

            def limpiar_dir(d):
                if not d: return ""
                limpio = re.sub(r'\d+', '', d.split('Es:')[0].split('(')[0])
                limpio = limpio.replace('VIGO', '').replace('PONTEVEDRA', '').strip()
                return ' '.join(limpio.split()[:4]).upper()

            calles_diferentes  = (
                limpiar_dir(direccion_finca) and limpiar_dir(dir_consultada) and
                len(set(limpiar_dir(direccion_finca).split()) &
                    set(limpiar_dir(dir_consultada).split())) < 2
            )
            mostrar_expandible  = 'varios inmuebles' in tipo_finca.lower()
            es_parcela_multiple = calles_diferentes

            st.markdown(f"**Ref. Catastral (Parcela):** `{ref_parcela}`")
            if catastro_result.get('direccion'):
                st.markdown(f"**Dirección Catastro:** {catastro_result['direccion']}")

            num_unidades = catastro_result.get('num_referencias', 1)
            if es_parcela_multiple:
                st.warning("⚠️ **Parcela con múltiples direcciones/unidades**")
            elif num_unidades > 1:
                st.info(f"ℹ️ **Parcela con {num_unidades} unidades catastrales.**")

            if catastro_result.get('construcciones'):
                st.markdown("---")
                st.subheader("🏢 Unidades del Edificio")

                unidades_procesadas = procesar_construcciones(catastro_result['construcciones'])

                hay_filtros = any([filtro_escalera, filtro_planta, filtro_puerta])
                if hay_filtros:
                    unidades_filtradas = filtrar_unidad(
                        unidades_procesadas, filtro_escalera, filtro_planta, filtro_puerta
                    )
                    filtro_txt = " · ".join(filter(None, [
                        f"Esc. {filtro_escalera}" if filtro_escalera else "",
                        f"Pl. {filtro_planta}"    if filtro_planta   else "",
                        f"Pta. {filtro_puerta}"   if filtro_puerta   else "",
                    ]))
                    if unidades_filtradas:
                        st.success(f"✅ Filtro aplicado: {filtro_txt}")
                        mostrar_tabla_unidades(unidades_filtradas, "Unidades que coinciden con el filtro")
                        with st.expander(f"Ver todas las unidades ({len(unidades_procesadas)} total)"):
                            mostrar_tabla_unidades(unidades_procesadas)
                    else:
                        st.warning(f"⚠️ Ninguna unidad coincide con: {filtro_txt}")
                        mostrar_tabla_unidades(unidades_procesadas, "Todas las unidades disponibles")
                else:
                    mostrar_tabla_unidades(unidades_procesadas)

                for u in unidades_procesadas:
                    uso = u.get('uso', 'OTRO')
                    if uso not in usos_resumen:
                        usos_resumen[uso] = {'count': 0, 'superficie': 0}
                    usos_resumen[uso]['count']      += 1
                    usos_resumen[uso]['superficie'] += u.get('superficie', 0) or 0

                if usos_resumen:
                    st.markdown("**📊 Resumen por Usos:**")
                    cols_usos = st.columns(min(len(usos_resumen), 4))
                    for i, (uso, datos) in enumerate(usos_resumen.items()):
                        with cols_usos[i % 4]:
                            st.metric(uso, f"{datos['count']} unidades", f"{datos['superficie']:.0f} m²")

                if mostrar_expandible:
                    with st.expander("🔍 Ver todas las unidades conocidas de la parcela"):
                        unidades_adicionales = []
                        if es_parcela_multiple and direccion_finca:
                            match_dir = re.match(
                                r'(RU|AV|PZ|CL|CM|CR)\s+(.+?)(?:\s+(\d+))?(?:\s+VIGO|\s+\(|$)',
                                direccion_finca
                            )
                            if match_dir:
                                catastro_adicional = clients['catastro'].consultar_por_direccion(
                                    provincia='PONTEVEDRA', municipio='VIGO',
                                    tipo_via=match_dir.group(1),
                                    nombre_via=match_dir.group(2).strip(),
                                    numero=match_dir.group(3) or "1"
                                )
                                if catastro_adicional and catastro_adicional.get('construcciones'):
                                    unidades_adicionales = procesar_construcciones(
                                        catastro_adicional['construcciones']
                                    )
                        todas = list({
                            u.get('ref_catastral'): u
                            for u in (unidades_procesadas + unidades_adicionales)
                        }.values())
                        if todas:
                            mostrar_tabla_unidades(todas)
                        else:
                            st.warning("No se encontraron unidades adicionales")

                st.markdown("---")

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if catastro_result.get('superficie_parcela'):
                    st.metric("Superficie Parcela", f"{catastro_result['superficie_parcela']:.0f} m²")
                if catastro_result.get('uso'):
                    st.metric("Uso", catastro_result['uso'])
            with col_m2:
                if catastro_result.get('superficie_construida'):
                    st.metric("Superficie Construida", f"{catastro_result['superficie_construida']:.0f} m²")
                if catastro_result.get('ano_construccion'):
                    st.metric("Año", catastro_result['ano_construccion'])

            if ref and ref != 'N/A':
                st.markdown(
                    f"[🗺️ Ver en Catastro](https://www1.sedecatastro.gob.es/Cartografia/mapa.aspx?refcat={ref_parcela})"
                )
        else:
            st.warning("⚠️ No se encontraron datos catastrales")
            st.info("Posibles causas: edificio público, zona no catastrada, vial rural. Prueba con la RC directa.")

    with col_izq:
        zona_rc_cache = mostrar_zona_postgis(catastro_result, zona_supabase_coords, clients)

    # ── Resumen completo ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Resumen Completo")

    zona_pxom_resumen = 'N/A'
    zona_nombre       = ''
    if zona_rc_cache and not zona_rc_cache.get('error'):
        zona_pxom_resumen = zona_rc_cache.get('zona_pxom', {}).get('ordenanza') or 'N/A'
        zona_nombre       = zona_rc_cache.get('zona_pxom', {}).get('nombre', '') or ''
    if zona_pxom_resumen == 'N/A' and zona_arcgis:
        zona_pxom_resumen = zona_arcgis.get('ordenanza', 'N/A')
        zona_nombre       = zona_arcgis.get('nombre', '') or ''

    dir_resumen = 'N/A'
    if geo_result:
        dir_resumen = geo_result.get('direccion_completa', 'N/A')
    elif rc_directa:
        dir_resumen = catastro_result.get('direccion', rc_directa) if catastro_result else rc_directa

    ref_parcela_res = catastro_result.get('ref_catastral', 'N/A')[:14] if catastro_result else 'N/A'

    resumen = {
        "📍 Dirección":          dir_resumen,
        "🗺️ Zona PXOM":          zona_pxom_resumen,
        "🏛️ Ref. Catastral":     ref_parcela_res,
        "📏 Superficie Parcela": f"{catastro_result['superficie_parcela']:.0f} m²" if catastro_result and catastro_result.get('superficie_parcela') else 'N/A',
        "🏗️ Sup. Construida":    f"{catastro_result['superficie_construida']:.0f} m²" if catastro_result and catastro_result.get('superficie_construida') else 'N/A',
        "📅 Año Construcción":   str(catastro_result.get('ano_construccion', 'N/A')) if catastro_result else 'N/A',
    }

    cols = st.columns(3)
    for i, (key, value) in enumerate(resumen.items()):
        with cols[i % 3]:
            st.metric(key, value)

    st.info("ℹ️ La zona PXOM se obtiene cruzando la RC catastral con la planimetría oficial del Ayuntamiento de Vigo cargada en PostGIS.")

    # ── Guardar contexto en sesión ────────────────────────────────────────────
    if zona_pxom_resumen != 'N/A' and ref_parcela_res != 'N/A':
        sup_parcela = catastro_result.get('superficie_parcela', 'N/D') if catastro_result else 'N/D'
        via_parcela = catastro_result.get('direccion', '')              if catastro_result else ''
        rc_anterior = st.session_state.cat_context.get('rc', '')

        st.session_state.cat_context = {
            "rc":          ref_parcela_res,
            "ordenanza":   zona_pxom_resumen,
            "zona_nombre": zona_nombre,
            "sup":         sup_parcela,
            "via":         via_parcela,
            "usos":        list(usos_resumen.keys()),
        }
        if ref_parcela_res != rc_anterior:
            st.session_state.cat_messages = []


# ════════════════════════════════════════════════════════════════════════════
# NORMATIVA — Chat conversacional sobre la parcela activa
# ════════════════════════════════════════════════════════════════════════════

ctx = st.session_state.cat_context

if ctx:
    st.markdown("---")
    st.subheader("📋 Normativa aplicable")

    rc_ctx   = ctx.get("rc",          "N/A")
    ord_ctx  = ctx.get("ordenanza",   "N/A")
    sup_ctx  = ctx.get("sup",         "N/D")
    via_ctx  = ctx.get("via",         "")
    usos_ctx = ctx.get("usos",        [])
    zona_ctx = ctx.get("zona_nombre", "")

    st.caption(
        f"Parcela activa: **{rc_ctx}** · Ordenanza: **{ord_ctx}**"
        + (f" — {zona_ctx}" if zona_ctx else "")
        + f" · Sup: **{sup_ctx} m²**"
        + (f" · {via_ctx}" if via_ctx else "")
    )

    for msg in st.session_state.cat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    usos_str      = ", ".join(usos_ctx) if usos_ctx else "N/D"
    pregunta_norm = st.chat_input(
        placeholder=f"¿Qué altura máxima permite la ordenanza {ord_ctx}? ¿Cuántas viviendas caben?",
        key="chat_input_cat",
    )

    if pregunta_norm and pregunta_norm.strip():
        query_enriquecida = (
            f"Parcela RC {rc_ctx}, ordenanza {ord_ctx}, superficie {sup_ctx} m², "
            f"usos actuales: {usos_str}. {pregunta_norm.strip()}"
        )

        st.session_state.cat_messages.append({"role": "user", "content": pregunta_norm.strip()})
        with st.chat_message("user"):
            st.markdown(pregunta_norm.strip())

        with st.spinner("Buscando en normativa..."):
            resultados = service.buscar_contexto(
                query=query_enriquecida, top_k=12,
                filtros={"ordenanza_codigo": ord_ctx},
            )
            if not resultados:
                resultados = service.buscar_contexto(
                    query=pregunta_norm.strip(), top_k=12, filtros=None,
                )

        if resultados:
            contexto_dual = {
                "rc": rc_ctx,
                "datos_gis": {
                    "zona_pxom": {"ordenanza": ord_ctx, "nombre": zona_ctx, "clasificacion": ""},
                    "parcela":   {"area_m2": sup_ctx if isinstance(sup_ctx, (int, float)) else None,
                                  "via": via_ctx, "numero": ""},
                },
                "ordenanza": ord_ctx,
                "hits":      resultados,
            }
            with st.spinner("Generando respuesta..."):
                respuesta = service.generar_respuesta_dual(
                    pregunta=pregunta_norm.strip(),
                    contexto_dual=contexto_dual,
                    historial=st.session_state.cat_messages[:-1],
                    idioma=idioma,
                )
        else:
            respuesta = (
                "No encontré normativa específica para esta consulta. "
                "Prueba a reformular con términos del PXOM: ordenanza, retranqueo, "
                "altura, edificabilidad, usos permitidos..."
            )

        st.session_state.cat_messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            st.markdown(respuesta)

        if resultados:
            with st.expander("📚 Artículos consultados"):
                for r in resultados:
                    fuente = (r.fuente or "").upper()
                    cab    = r.payload.get("articulo_titulo", "")
                    texto  = r.payload.get("text", "")
                    st.markdown(f"**{fuente} · Art. {r.payload.get('articulo_numero', '')}** — {cab}")
                    st.caption(texto[:200] + "..." if texto else "")

    if st.session_state.cat_messages:
        if st.button("🗑 Limpiar conversación", key="clear_cat_chat"):
            st.session_state.cat_messages = []
            st.rerun()

elif hay_busqueda:
    st.warning("⚠️ No se pudo obtener la zona PXOM. Comprueba la dirección o la RC.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "PXOM Vigo V3.1 · Sistema de Consulta Catastral Integrado | "
    "Datos: ArcGIS Ayto. Vigo, Catastro, PostGIS"
)
