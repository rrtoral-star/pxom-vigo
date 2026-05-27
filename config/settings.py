"""
Configuración del Crawler PXOM Solo
Aquí defines URLs, rutas y parámetros de extracción
"""

# URL base de la normativa
BASE_URL = "https://xmu.vigo.org"

# URLs extraídas del índice principal
START_URLS = [
    "https://xmu.vigo.org/docs/PXOM_2025/MX_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/NUCLEOS_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/FichasSUNC_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/FichasSUB_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/FichasPEP_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/PINF_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/01_EXE_10000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/02_CL_10000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/03_ORD_2000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/04_SUC_2000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/05_CAT_10000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/06_1SSAA_RD_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/06_2SSAA_PD_AC_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/06_3SSAA_PD_DP_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/06_4SSAA_VUL_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/06_5AFEC_ACUS_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/07_INUN_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/08_resumo_2000_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/CAT_cas.html",
    "https://xmu.vigo.org/docs/PXOM_2025/ORDET_cas.html",
]

# Rutas de guardado
RAW_HTML_DIR = "data/raw"
CLEANED_JSON_DIR = "data/cleaned"
LOG_DIR = "data/logs"

# Configuración de descarga
TIMEOUT = 30  # segundos para esperar respuesta
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Configuración de limpieza HTML
# Tags que queremos eliminar completamente
TAGS_TO_REMOVE = ['script', 'style', 'nav', 'header', 'footer', 'iframe']

# Palabras clave para detectar artículos (ajusta según la web real)
ARTICLE_KEYWORDS = ['artículo', 'articulo', 'art.', 'art ', 'capítulo', 'capitulo', 'sección', 'seccion']