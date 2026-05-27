"""
Analiza la estructura jerárquica del PDF
Detecta: TÍTULOS, CAPÍTULOS, SECCIONES, Artículos
"""

import re
import pdfplumber

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'

print("\n" + "="*60)
print("ANÁLISIS DE ESTRUCTURA JERÁRQUICA")
print("="*60 + "\n")

# Extraer texto saltando índice
with pdfplumber.open(pdf_path) as pdf:
    texto = '\n'.join([pdf.pages[i].extract_text() for i in range(24, len(pdf.pages))])

# Patrones
patron_titulo = r'TÍTULO\s+([IVX]+)\.\s+([^\n]+)'
patron_capitulo = r'CAPÍTULO\s+([IVX]+)\.\s+([^\n]+)'
patron_seccion = r'Sección\s+(\d+ª)\.\s+([^\n]+)'
patron_articulo = r'Art\.\s+(\d+[a-z]?)\.\s+([^\n\.]+)\.'

# Detectar todos
titulos = re.findall(patron_titulo, texto, re.IGNORECASE)
capitulos = re.findall(patron_capitulo, texto, re.IGNORECASE)
secciones = re.findall(patron_seccion, texto, re.IGNORECASE)
articulos = re.findall(patron_articulo, texto, re.IGNORECASE)

print(f"📚 TÍTULOS encontrados: {len(titulos)}")
for num, nombre in titulos[:5]:
    print(f"   - TÍTULO {num}: {nombre[:60]}...")

print(f"\n📖 CAPÍTULOS encontrados: {len(capitulos)}")
for num, nombre in capitulos[:5]:
    print(f"   - CAPÍTULO {num}: {nombre[:60]}...")

print(f"\n📄 SECCIONES encontradas: {len(secciones)}")
for num, nombre in secciones[:5]:
    print(f"   - Sección {num}: {nombre[:60]}...")

print(f"\n📝 ARTÍCULOS encontrados: {len(articulos)}")
print(f"   Primeros 10:")
for num, nombre in articulos[:10]:
    print(f"   - Art. {num}: {nombre[:50]}...")

print("\n" + "="*60)
print(f"RESUMEN: {len(titulos)} títulos, {len(capitulos)} capítulos, "
      f"{len(secciones)} secciones, {len(articulos)} artículos")
print("="*60 + "\n")