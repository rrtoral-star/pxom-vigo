"""
Extractor de URLs del índice PXOM
Analiza el índice y extrae todas las URLs de artículos HTML
"""

import os
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Importar configuración
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import BASE_URL, RAW_HTML_DIR

def extraer_urls_html(archivo_indice):
    """
    Extrae todas las URLs .html del archivo de índice
    
    Args:
        archivo_indice (str): Ruta al archivo HTML del índice
        
    Returns:
        list: Lista de URLs absolutas
    """
    print(f"\n{'='*60}")
    print(f"EXTRAYENDO URLs DE: {archivo_indice}")
    print(f"{'='*60}\n")
    
    # Leer el archivo
    with open(archivo_indice, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Buscar todos los enlaces <a href="...">
    enlaces = soup.find_all('a', href=True)
    
    urls_html = []
    urls_pdf = []
    
    for enlace in enlaces:
        href = enlace['href']
        
        # Filtrar solo .html (ignorar PDFs, anchors, etc.)
        if href.endswith('.html'):
            # Convertir URL relativa a absoluta
            url_absoluta = urljoin(BASE_URL + '/docs/PXOM_2025/', href)
            
            if url_absoluta not in urls_html:
                urls_html.append(url_absoluta)
                print(f"✓ HTML: {url_absoluta}")
        
        elif href.endswith('.pdf'):
            if href not in urls_pdf:
                urls_pdf.append(href)
    
    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"  HTMLs encontrados: {len(urls_html)}")
    print(f"  PDFs encontrados: {len(urls_pdf)}")
    print(f"{'='*60}\n")
    
    return urls_html

def guardar_urls(urls, archivo_salida):
    """
    Guarda las URLs en un archivo de texto
    
    Args:
        urls (list): Lista de URLs
        archivo_salida (str): Ruta del archivo de salida
    """
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')
    
    print(f"✓ URLs guardadas en: {archivo_salida}")

def main():
    # Archivo de índice descargado
    archivo_indice = os.path.join(RAW_HTML_DIR, 'docs_PXOM_2025_REVISION_PXOM_INDICE_cas.html')
    
    if not os.path.exists(archivo_indice):
        print(f"✗ ERROR: No se encuentra el archivo {archivo_indice}")
        print("Ejecuta primero el crawler para descargar el índice.")
        return
    
    # Extraer URLs
    urls = extraer_urls_html(archivo_indice)
    
    # Guardar en archivo
    archivo_salida = 'urls_extraidas.txt'
    guardar_urls(urls, archivo_salida)
    
    print("\n" + "="*60)
    print("SIGUIENTE PASO:")
    print("="*60)
    print("1. Revisa el archivo 'urls_extraidas.txt'")
    print("2. Estas URLs probablemente son índices secundarios")
    print("3. Necesitaremos descargarlas para ver su contenido")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()