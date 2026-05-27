"""
fix_nhv_raw.py — Limpieza de cabeceras en nhv_raw.md
Corrige palabras fusionadas y errores OCR en las cabeceras ## Articulo N.

Problemas detectados:
1. Número pegado al título:   ## Articulo3.Definiciones
2. Palabras fusionadas:       ## Articulo7.Viviendasenedificacionesdenuevaconstruccion
3. OCR erróneo:               ## Articulo1o → Articulo 10
4. Número sin espacio:        ## Articulo 2.Ambito → ## Articulo 2. Ambito

Uso:
    python scripts/fix_nhv_raw.py
    python scripts/fix_nhv_raw.py --preview   (solo muestra cambios, no escribe)
"""

import re
import sys
import shutil
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parents[1]
NHV_PATH = ROOT / "data/raw/docling/nhv_raw.md"
BACKUP   = NHV_PATH.with_suffix(".md.bak")

PREVIEW  = "--preview" in sys.argv

# ── Correcciones manuales para casos OCR difíciles ───────────────────────────
# Mapa explícito para artículos que el regex no puede resolver solos
CORRECCIONES_MANUALES = {
    # OCR confundió '0' con 'o'
    "Articulo1o.":   "Articulo 10.",
    "Articulo1o ":   "Articulo 10 ",
    "Articulo2o.":   "Articulo 20.",
    "Articulo3o.":   "Articulo 30.",
    # Palabras fusionadas conocidas en títulos
    "Viviendasenedificacionesdenuevaconstruccion": "Viviendas en edificaciones de nueva construccion",
    "Verificaciondesucumplimento":                 "Verificacion de su cumplimento",
    "ComiteAsesordeHabitabilidad":                 "Comite Asesor de Habitabilidad",
    "Obrasdeadecuacionestructural":                "Obras de adecuacion estructural",
    "obrasdeadecuacionfuncionaldeedificios":        "Obras de adecuacion funcional de edificios",
    "Obrasderemodelaciondeedificios":               "Obras de remodelacion de edificios",
    "Obrasdeampliaciondeedificiosoviviendas":       "Obras de ampliacion de edificios o viviendas",
    "Losanexosdehabitabilidad":                     "Los anexos de habitabilidad",
    "deedificiosyviviendas":                        "de edificios y viviendas",
    "deviviendas":                                  "de viviendas",
    "enestedecreto":                                "en este decreto",
    "°. ": "",
    "°.": "",
}

# ── Regex para cabeceras de artículo ─────────────────────────────────────────
# Detecta: ## Articulo[N][.][título]
RE_CABECERA = re.compile(
    r'^(##\s+Articulo)\s*(\d+[a-z]?)\s*[.\s]*(.+?)\.?\s*$',
    re.MULTILINE | re.IGNORECASE
)

def normalizar_numero(num: str) -> str:
    """Corrige errores OCR en el número: 1o→10, 2o→20, etc."""
    return re.sub(r'(\d+)o$', lambda m: str(int(m.group(1)) * 10), num)

def separar_camelcase(texto: str) -> str:
    """
    Intenta separar palabras fusionadas detectando transiciones
    minúscula→Mayúscula dentro de una palabra larga sin espacios.
    Solo actúa si la palabra tiene más de 15 chars sin espacio.
    """
    palabras = texto.split()
    resultado = []
    for palabra in palabras:
        if len(palabra) > 15 and palabra == palabra.replace(' ', ''):
            # Insertar espacio antes de mayúsculas internas
            separada = re.sub(r'([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])', r'\1 \2', palabra)
            resultado.append(separada)
        else:
            resultado.append(palabra)
    return ' '.join(resultado)

def limpiar_linea_cabecera(match: re.Match) -> str:
    """Reconstruye una cabecera ## Articulo N. Título limpio."""
    prefijo = "## Articulo"
    numero  = normalizar_numero(match.group(2))
    titulo  = match.group(3).strip()

    # Aplicar correcciones manuales al título
    for fusionado, correcto in CORRECCIONES_MANUALES.items():
        titulo = titulo.replace(fusionado, correcto)

    # Separar CamelCase residual
    titulo = separar_camelcase(titulo)

    # Capitalizar primera letra
    titulo = titulo[0].upper() + titulo[1:] if titulo else titulo
    titulo = titulo.lstrip("°. ")
    return f"{prefijo} {numero}. {titulo}."

def limpiar_cuerpo(texto: str) -> str:
    """Aplica correcciones manuales al cuerpo del texto (fuera de cabeceras)."""
    for fusionado, correcto in CORRECCIONES_MANUALES.items():
        texto = texto.replace(fusionado, correcto)
    return texto

def procesar(content: str) -> tuple[str, list[str]]:
    """Procesa el contenido completo y devuelve (contenido_limpio, cambios)."""
    cambios = []
    lineas_originales = content.split('\n')
    lineas_nuevas     = []

    for linea in lineas_originales:
        if re.match(r'^##\s+Articulo', linea, re.IGNORECASE):
            m = RE_CABECERA.match(linea)
            if m:
                nueva = limpiar_linea_cabecera(m)
                if nueva.strip() != linea.strip():
                    cambios.append(f"  - '{linea.strip()}'")
                    cambios.append(f"  + '{nueva.strip()}'")
                lineas_nuevas.append(nueva)
            else:
                # Cabecera que no matchea el patrón — limpiar cuerpo al menos
                nueva = limpiar_cuerpo(linea)
                if nueva != linea:
                    cambios.append(f"  - '{linea.strip()}'")
                    cambios.append(f"  + '{nueva.strip()}'")
                lineas_nuevas.append(nueva)
        else:
            # Línea de cuerpo — aplicar correcciones manuales
            nueva = limpiar_cuerpo(linea)
            lineas_nuevas.append(nueva)

    return '\n'.join(lineas_nuevas), cambios

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not NHV_PATH.exists():
        print(f"✗ No encontrado: {NHV_PATH}")
        sys.exit(1)

    content = NHV_PATH.read_text(encoding='utf-8')
    content_limpio, cambios = procesar(content)

    print(f"{'='*60}")
    print(f"  fix_nhv_raw.py")
    print(f"  Archivo: {NHV_PATH.name}")
    print(f"  Cambios detectados: {len(cambios) // 2}")
    print(f"{'='*60}")

    if cambios:
        print("\nCambios:")
        for c in cambios:
            print(c)
    else:
        print("\nSin cambios necesarios.")

    if PREVIEW:
        print("\n[preview] Sin cambios escritos.")
        return

    # Backup
    shutil.copy(NHV_PATH, BACKUP)
    print(f"\n✓ Backup: {BACKUP.name}")

    # Escribir
    NHV_PATH.write_text(content_limpio, encoding='utf-8')
    print(f"✓ Archivo limpio escrito: {NHV_PATH.name}")
    print("\nSiguiente paso:")
    print("  del wiki\\nhv\\*.md")
    print("  del wiki\\nhv\\.checkpoint.json")
    print("  python src/wiki/generate_wiki.py --fuente nhv")

if __name__ == "__main__":
    main()
