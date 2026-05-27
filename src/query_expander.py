"""
query_expander.py - Expansión de queries con sinónimos urbanísticos
Traduce lenguaje cotidiano a terminología técnica del PXOM y NHV-2010

Uso:
    from query_expander import expandir_query
    query_expandida = expandir_query("¿puedo poner un balcón?")
    # → "¿puedo poner un balcón? vuelo cuerpo volado elemento saliente galería mirador"
"""

# ============================================================
# DICCIONARIO DE SINÓNIMOS
# Clave: término cotidiano / variante
# Valor: lista de términos técnicos del PXOM / NHV-2010
# ============================================================
SINONIMOS = {

    # ── Elementos de fachada ─────────────────────────────────
    "balcón":           ["vuelo", "cuerpo volado", "cuerpo saliente", "galería", "mirador", "voladizo"],
    "balcones":         ["vuelos", "cuerpos volados", "cuerpos salientes", "galerías", "miradores"],
    "terraza":          ["terraza cubierta", "azotea", "cubierta transitable", "espacio libre privado"],
    "voladizo":         ["vuelo", "cuerpo volado", "cuerpo saliente"],
    "marquesina":       ["vuelo", "cuerpo saliente", "cubierta"],
    "porche":           ["soportal", "espacio cubierto", "planta baja libre"],
    "galería":          ["galería acristalada", "cuerpo saliente", "vuelo acristalado"],
    "toldo":            ["elemento saliente", "vuelo", "marquesina"],

    # ── Cubiertas ────────────────────────────────────────────
    "tejado":           ["cubierta", "cubierta inclinada", "faldón de cubierta"],
    "techo":            ["cubierta", "forjado techo", "altura libre", "altura máxima"],
    "tejados":          ["cubiertas", "cubiertas inclinadas"],
    "azotea":           ["cubierta plana", "cubierta transitable", "terraza"],
    "buhardilla":       ["pieza abuhardillada", "bajo cubierta", "planta bajo cubierta"],
    "ático":            ["planta bajo cubierta", "planta ático", "última planta"],
    "lucernario":       ["ventana en faldón de cubierta", "claraboya", "hueco de iluminación"],

    # ── Espacios interiores vivienda ─────────────────────────
    "salón":            ["estancia mayor", "sala de estar", "estancia principal"],
    "salon":            ["estancia mayor", "sala de estar", "estancia principal"],
    "comedor":          ["estancia mayor", "estancia", "sala"],
    "dormitorio":       ["estancia", "habitación", "pieza vividera"],
    "habitación":       ["estancia", "pieza vividera", "dormitorio"],
    "cuarto":           ["estancia", "pieza", "dependencia"],
    "baño":             ["cuarto de baño", "aseo", "servicio sanitario"],
    "aseo":             ["cuarto de aseo", "servicio sanitario", "baño"],
    "cocina":           ["cocina", "zona cocina", "espacio cocina"],
    "pasillo":          ["espacio de comunicación", "pasillo distribuidor", "vestíbulo"],
    "entrada":          ["acceso", "vestíbulo", "espacio de acceso interior", "portal"],
    "trastero":         ["almacenamiento", "trastero anexo", "espacio de almacenamiento general"],
    "lavadero":         ["lavadero", "zona lavado", "espacio lavadero"],
    "tendedero":        ["tendedero", "zona secado", "espacio secado ropa"],
    "armario":          ["almacenamiento personal", "espacio almacenamiento", "trastero"],

    # ── Alturas y medidas ────────────────────────────────────
    "altura del techo": ["altura libre mínima", "altura libre", "altura entre forjados"],
    "techo alto":       ["altura libre mínima", "2,50 m", "2,70 m entre forjados"],
    "techo bajo":       ["altura libre reducida", "altura mínima 2,20 m"],
    "planta baja":      ["planta baja", "planta de acceso", "nivel rasante"],
    "sótano":           ["planta sótano", "sótano", "planta bajo rasante"],
    "semisótano":       ["semisótano", "planta semisótano"],

    # ── Parcela y edificación ────────────────────────────────
    "solar":            ["parcela", "solar edificable", "parcela mínima"],
    "finca":            ["parcela", "finca registral", "solar"],
    "jardín":           ["espacio libre privado", "zona ajardinada", "espacio no edificado"],
    "patio":            ["patio interior", "patio de parcela", "espacio libre"],
    "piscina":          ["instalación deportiva", "uso deportivo privado", "construcción auxiliar"],
    "garaje":           ["garaje-aparcamiento", "aparcamiento", "plaza de garaje", "uso garaje"],
    "parking":          ["aparcamiento", "garaje-aparcamiento", "plaza aparcamiento"],
    "plaza de garaje":  ["plaza de aparcamiento", "garaje", "aparcamiento"],
    "valla":            ["cerramiento", "vallado", "cerramiento de parcela"],
    "muro":             ["cerramiento", "muro de cerramiento", "medianera"],
    "escalera":         ["núcleo de escalera", "escalera interior", "escalera común"],
    "ascensor":         ["ascensor", "instalación de ascensor", "hueco de ascensor"],
    "nave":             ["edificación industrial", "uso industrial", "nave industrial"],
    "local":            ["local comercial", "uso comercial", "planta baja comercial"],
    "tienda":           ["uso comercial", "local comercial", "planta baja uso terciario"],
    "oficina":          ["uso terciario oficinas", "uso oficinas", "categoría oficinas"],
    "hotel":            ["uso hotelero", "uso terciario hotelero", "establecimiento hotelero"],

    # ── Normativa y gestión ──────────────────────────────────
    "reformar":         ["obras de remodelación", "rehabilitación", "reforma interior", "obras de adecuación funcional"],
    "reforma":          ["obras de remodelación", "rehabilitación", "adecuación funcional"],
    "ampliar":          ["obras de ampliación", "ampliación", "incremento superficie"],
    "ampliación":       ["obras de ampliación", "ampliación de edificio", "ampliación de vivienda"],
    "derribar":         ["demolición", "derribo", "eliminación de edificación"],
    "construir":        ["edificación de nueva construcción", "obra nueva", "nueva planta"],
    "licencia":         ["licencia urbanística", "licencia de obras", "licencia municipal"],
    "permiso":          ["licencia urbanística", "autorización municipal", "licencia de obras"],
    "certificado":      ["cédula de habitabilidad", "certificado de habitabilidad", "certificado urbanístico"],
    "informe":          ["informe urbanístico", "consulta urbanística", "certificado urbanístico"],
    "excepción":        ["trámite de excepción", "excepcionalidad", "solicitud de excepción"],
    "ilegal":           ["fuera de ordenación", "infracción urbanística", "sin licencia"],

    # ── Zonas y clasificación ────────────────────────────────
    "zona residencial": ["suelo urbano residencial", "ordenanza U", "uso residencial"],
    "zona industrial":  ["suelo urbano industrial", "uso industrial", "ordenanza I"],
    "casco viejo":      ["conjunto histórico", "casco histórico", "suelo urbano consolidado"],
    "pueblo":           ["núcleo rural", "ordenanza N", "suelo de núcleo rural"],
    "campo":            ["suelo rústico", "suelo no urbanizable", "medio rural"],
    "afueras":          ["suelo rústico", "suelo urbanizable", "área de expansión"],

    # ── Habitabilidad específica ─────────────────────────────
    "ventana":          ["hueco de ventilación", "hueco de iluminación", "superficie de iluminación"],
    "ventilación":      ["ventilación natural", "ventilación mecánica", "hueco de ventilación"],
    "luz natural":      ["iluminación natural", "iluminación directa", "superficie de iluminación"],
    "humedad":          ["salubridad", "impermeabilización", "cámara de aire"],
    "aislamiento":      ["aislamiento térmico", "aislamiento acústico", "impermeabilización"],
}


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def expandir_query(query: str, verbose: bool = False) -> str:
    """
    Expande la query añadiendo términos técnicos equivalentes.
    
    Args:
        query: Pregunta original del usuario
        verbose: Mostrar qué sinónimos se añadieron
    
    Returns:
        Query expandida con términos técnicos adicionales
    """
    query_lower = query.lower()
    terminos_añadidos = []

    for termino, sinonimos in SINONIMOS.items():
        if termino in query_lower:
            # Añadir solo los sinónimos que no están ya en la query
            nuevos = [s for s in sinonimos if s not in query_lower]
            if nuevos:
                terminos_añadidos.extend(nuevos)
                if verbose:
                    print(f"  📎 '{termino}' → {nuevos}")

    if terminos_añadidos:
        # Eliminar duplicados manteniendo orden
        vistos = set()
        unicos = []
        for t in terminos_añadidos:
            if t not in vistos:
                vistos.add(t)
                unicos.append(t)

        query_expandida = query + " " + " ".join(unicos)
    else:
        query_expandida = query

    return query_expandida


def expandir_query_debug(query: str) -> dict:
    """
    Versión debug que devuelve info detallada de la expansión.
    Útil para el panel DEBUG del Streamlit.
    """
    query_lower = query.lower()
    matches = {}

    for termino, sinonimos in SINONIMOS.items():
        if termino in query_lower:
            nuevos = [s for s in sinonimos if s not in query_lower]
            if nuevos:
                matches[termino] = nuevos

    terminos_tecnicos = []
    for sinonimos in matches.values():
        terminos_tecnicos.extend(sinonimos)

    # Eliminar duplicados
    vistos = set()
    unicos = []
    for t in terminos_tecnicos:
        if t not in vistos:
            vistos.add(t)
            unicos.append(t)

    query_expandida = (query + " " + " ".join(unicos)).strip() if unicos else query

    return {
        "query_original": query,
        "query_expandida": query_expandida,
        "terminos_detectados": matches,
        "expandida": len(unicos) > 0,
    }


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    queries_test = [
        "¿puedo colocar un balcón en mi fachada?",
        "quiero reformar mi baño y el dormitorio",
        "altura del techo en la cocina",
        "¿necesito licencia para construir un garaje?",
        "tengo humedad en el sótano",
        "¿puedo poner una piscina en el jardín?",
        "quiero ampliar mi casa con un tejado nuevo",
        "¿cuántas plantas puede tener el edificio?",  # sin sinónimos → sin expansión
    ]

    print("TEST EXPANSIÓN DE QUERIES")
    print("="*60)
    for q in queries_test:
        resultado = expandir_query_debug(q)
        print(f"\n📝 Original:  {resultado['query_original']}")
        if resultado["expandida"]:
            print(f"🔧 Expandida: {resultado['query_expandida'][:120]}...")
            print(f"   Matches:   {resultado['terminos_detectados']}")
        else:
            print("   (sin expansión - terminología técnica correcta)")
    print("="*60)
