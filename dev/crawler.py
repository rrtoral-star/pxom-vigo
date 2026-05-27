"""
Crawler PXOM Solo - Extracción de Normativa Urbanística
Fase 1: Descarga y limpieza de HTML
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

# Importar configuración
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import *


class PXOMCrawler:
    """Crawler para extraer normativa PXOM de Vigo"""
    
    def __init__(self):
        """Inicializar crawler y crear carpetas necesarias"""
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.crear_carpetas()
        self.log_file = os.path.join(LOG_DIR, f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.log("Crawler inicializado")
    
    def crear_carpetas(self):
        """Crea las carpetas de datos si no existen"""
        for carpeta in [RAW_HTML_DIR, CLEANED_JSON_DIR, LOG_DIR]:
            os.makedirs(carpeta, exist_ok=True)
    
    def log(self, mensaje):
        """Registra mensaje en consola y archivo"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {mensaje}"
        print(log_msg)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def descargar_pagina(self, url):
        """
        Descarga una página web y devuelve el contenido HTML
        
        Args:
            url (str): URL a descargar
            
        Returns:
            str: Contenido HTML o None si falla
        """
        try:
            self.log(f"Descargando: {url}")
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding  # Detectar encoding correcto
            
            # Guardar HTML original
            filename = self.url_to_filename(url)
            filepath = os.path.join(RAW_HTML_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.log(f"✓ Descargado: {filename}")
            return response.text
            
        except requests.exceptions.Timeout:
            self.log(f"✗ ERROR: Timeout en {url}")
            return None
        except requests.exceptions.RequestException as e:
            self.log(f"✗ ERROR descargando {url}: {str(e)}")
            return None
    
    def url_to_filename(self, url):
        """Convierte una URL en un nombre de archivo seguro"""
        parsed = urlparse(url)
        filename = parsed.path.replace('/', '_').replace('\\', '_')
        if not filename or filename == '_':
            filename = 'index'
        if not filename.endswith('.html'):
            filename += '.html'
        return filename.lstrip('_')
    
    def limpiar_html(self, html):
        """
        Elimina tags innecesarios del HTML
        
        Args:
            html (str): HTML original
            
        Returns:
            BeautifulSoup: Objeto soup limpio
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Eliminar tags no deseados
            for tag_name in TAGS_TO_REMOVE:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
            
            # Eliminar comentarios HTML
            for comment in soup.find_all(string=lambda text: isinstance(text, type(soup))):
                comment.extract()
            
            return soup
            
        except Exception as e:
            self.log(f"✗ ERROR limpiando HTML: {str(e)}")
            return None
    
    def extraer_articulos(self, soup, url_origen):
        """
        Extrae artículos de la normativa del HTML limpio
        
        Args:
            soup (BeautifulSoup): HTML parseado
            url_origen (str): URL de donde vienen los datos
            
        Returns:
            list: Lista de diccionarios con artículos
        """
        articulos = []
        
        try:
            # Buscar todos los bloques de texto
            # NOTA: Esta lógica es GENÉRICA, deberás ajustarla según la estructura real
            
            # Estrategia 1: Buscar headers (h1, h2, h3) que contengan palabras clave
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div'])
            
            articulo_actual = None
            
            for elemento in headers:
                texto = elemento.get_text(strip=True).lower()
                
                # Detectar si es un título de artículo/sección
                es_titulo = any(keyword in texto for keyword in ARTICLE_KEYWORDS)
                
                if es_titulo:
                    # Guardar artículo anterior si existe
                    if articulo_actual:
                        articulos.append(articulo_actual)
                    
                    # Iniciar nuevo artículo
                    articulo_actual = {
                        'titulo': elemento.get_text(strip=True),
                        'tipo_tag': elemento.name,
                        'contenido': [],
                        'url_origen': url_origen,
                        'timestamp': datetime.now().isoformat()
                    }
                
                elif articulo_actual:
                    # Agregar contenido al artículo actual
                    contenido = elemento.get_text(strip=True)
                    if contenido and len(contenido) > 10:  # Ignorar textos muy cortos
                        articulo_actual['contenido'].append(contenido)
            
            # Agregar último artículo
            if articulo_actual:
                articulos.append(articulo_actual)
            
            self.log(f"✓ Extraídos {len(articulos)} artículos de {url_origen}")
            
        except Exception as e:
            self.log(f"✗ ERROR extrayendo artículos: {str(e)}")
        
        return articulos
    
    def guardar_json(self, articulos, nombre_archivo):
        """
        Guarda artículos en formato JSON
        
        Args:
            articulos (list): Lista de artículos
            nombre_archivo (str): Nombre del archivo sin extensión
        """
        try:
            filepath = os.path.join(CLEANED_JSON_DIR, f"{nombre_archivo}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articulos, f, ensure_ascii=False, indent=2)
            
            self.log(f"✓ Guardado JSON: {nombre_archivo}.json ({len(articulos)} artículos)")
            
        except Exception as e:
            self.log(f"✗ ERROR guardando JSON: {str(e)}")
    
    def procesar_url(self, url):
        """
        Proceso completo: descargar → limpiar → extraer → guardar
        
        Args:
            url (str): URL a procesar
        """
        self.log(f"\n{'='*60}")
        self.log(f"PROCESANDO: {url}")
        self.log(f"{'='*60}")
        
        # 1. Descargar
        html = self.descargar_pagina(url)
        if not html:
            return
        
        # 2. Limpiar
        soup = self.limpiar_html(html)
        if not soup:
            return
        
        # 3. Extraer
        articulos = self.extraer_articulos(soup, url)
        
        # 4. Guardar
        if articulos:
            nombre = self.url_to_filename(url).replace('.html', '')
            self.guardar_json(articulos, nombre)
        else:
            self.log("⚠ No se encontraron artículos en esta página")
        
        # Pausa para no sobrecargar el servidor
        time.sleep(1)
    
    def ejecutar(self):
        """Ejecuta el crawler en todas las URLs configuradas"""
        self.log("\n" + "="*60)
        self.log("INICIANDO CRAWLER PXOM SOLO")
        self.log("="*60 + "\n")
        
        for url in START_URLS:
            self.procesar_url(url)
        
        self.log("\n" + "="*60)
        self.log("CRAWLER FINALIZADO")
        self.log(f"Revisa los resultados en: {CLEANED_JSON_DIR}")
        self.log("="*60)


# PUNTO DE ENTRADA
if __name__ == "__main__":
    crawler = PXOMCrawler()
    crawler.ejecutar()