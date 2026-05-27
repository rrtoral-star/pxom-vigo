"""
Extractor de PDFs del PXOM
Descarga y extrae texto estructurado de PDFs de normativa
"""

import os
import sys
import json
import requests
import pdfplumber
from datetime import datetime
import re

# Importar configuración
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import HEADERS, TIMEOUT, RAW_HTML_DIR, CLEANED_JSON_DIR, LOG_DIR


class PDFExtractor:
    """Extractor de contenido de PDFs del PXOM"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.crear_carpetas()
        self.log_file = os.path.join(LOG_DIR, f"pdf_extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.log("PDF Extractor inicializado")
    
    def crear_carpetas(self):
        """Crea carpetas necesarias"""
        for carpeta in [RAW_HTML_DIR, CLEANED_JSON_DIR, LOG_DIR]:
            os.makedirs(carpeta, exist_ok=True)
    
    def log(self, mensaje):
        """Registra mensaje en consola y archivo"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {mensaje}"
        print(log_msg)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def descargar_pdf(self, url):
        """
        Descarga un PDF y lo guarda localmente
        
        Args:
            url (str): URL del PDF
            
        Returns:
            str: Ruta local del PDF descargado o None si falla
        """
        try:
            self.log(f"Descargando PDF: {url}")
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            # Nombre del archivo
            filename = url.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            filepath = os.path.join(RAW_HTML_DIR, filename)
            
            # Guardar PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.log(f"✓ PDF descargado: {filename} ({len(response.content)/1024:.1f} KB)")
            return filepath
            
        except Exception as e:
            self.log(f"✗ ERROR descargando PDF: {str(e)}")
            return None
    
    def extraer_texto_pdf(self, pdf_path, pagina_inicio=7):
        """
        Extrae texto de un PDF desde una página específica
        
        Args:
            pdf_path (str): Ruta al archivo PDF
            pagina_inicio (int): Página desde donde empezar (1-indexed). Default: 7 para saltar índice
            
        Returns:
            str: Texto completo del PDF
        """
        try:
            self.log(f"Extrayendo texto de: {os.path.basename(pdf_path)}")
            self.log(f"  Saltando primeras {pagina_inicio-1} páginas (portada/índice)")
            
            texto_completo = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_paginas = len(pdf.pages)
                self.log(f"  Total de páginas: {total_paginas}")
                self.log(f"  Procesando desde página {pagina_inicio} hasta {total_paginas}")
                
                # Empezar desde pagina_inicio (convertir a índice 0-based)
                for i in range(pagina_inicio - 1, total_paginas):
                    numero_pagina = i + 1  # Mostrar número legible (1-based)
                    
                    if numero_pagina % 10 == 0:
                        self.log(f"  Procesando página {numero_pagina}/{total_paginas}...")
                    
                    texto = pdf.pages[i].extract_text()
                    if texto:
                        texto_completo.append(texto)
            
            texto_final = '\n'.join(texto_completo)
            self.log(f"✓ Texto extraído: {len(texto_final)} caracteres")
            
            return texto_final
            
        except Exception as e:
            self.log(f"✗ ERROR extrayendo texto: {str(e)}")
            return None
    
    def detectar_articulos(self, texto):
        """
        Detecta y extrae artículos del texto usando patrones mejorados
        
        Args:
            texto (str): Texto completo del PDF
            
        Returns:
            list: Lista de diccionarios con artículos estructurados
        """
        self.log("Detectando artículos en el texto...")
        
        articulos = []
        
        # Patrón mejorado: permite saltos de línea dentro del título
        patron_articulo = r'Art\.\s+(\d+[a-z]?)\.\s+((?:(?!\n\n)[^\.])+)\.'
        
        # Buscar todos los artículos
        matches = list(re.finditer(patron_articulo, texto, re.IGNORECASE | re.MULTILINE))
        
        self.log(f"  Encontrados {len(matches)} coincidencias de artículos")
        
        # Detectar contexto (Título y Capítulo actual)
        patron_titulo = r'TÍTULO\s+([IVX]+)\.\s+([^\n]+)'
        patron_capitulo = r'CAPÍTULO\s+([IVX]+)\.\s+([^\n]+)'
        patron_seccion = r'Sección\s+(\d+ª)\.\s+([^\n]+)'
        for i, match in enumerate(matches):
            # Número y título del artículo
            numero = match.group(1).strip()
            titulo_descriptivo = match.group(2).strip()
            
            # Limpiar saltos de línea dentro del título
            titulo_descriptivo = ' '.join(titulo_descriptivo.split())
            
            titulo_completo = f"Art. {numero}. {titulo_descriptivo}."
            
            # Posición inicial (justo después del título)
            inicio = match.end()
            
            # Posición final (hasta el siguiente artículo o final del texto)
            if i < len(matches) - 1:
                fin = matches[i + 1].start()
            else:
                fin = len(texto)
            
            # Contenido del artículo (todo el texto entre este y el siguiente)
            contenido_completo = texto[inicio:fin].strip()
            
            # Limpiar contenido: remover saltos de línea excesivos
            contenido_limpio = re.sub(r'\n{3,}', '\n\n', contenido_completo)
            
            # Limpiar texto de pie de página del PDF
            contenido_limpio = re.sub(r'REVISIÓN DEL.*?ataD', '', contenido_limpio, flags=re.DOTALL)
            contenido_limpio = re.sub(r'\d+ de \d+', '', contenido_limpio)  # "7 de 691"
            contenido_limpio = re.sub(r'OFICINA DE PLANEAMIENTO.*?2025', '', contenido_limpio, flags=re.DOTALL)
            contenido_limpio = re.sub(r'S\.E\.P\.I\.A\..*?\n', '', contenido_limpio)
            contenido_limpio = re.sub(r'onalletsac.*?\n', '', contenido_limpio)
            contenido_limpio = contenido_limpio.strip()
            
            # Detectar contexto (buscar hacia atrás)
            texto_previo = texto[:match.start()]
            
            # Buscar último TÍTULO antes de este artículo
            titulos = list(re.finditer(patron_titulo, texto_previo))
            titulo_contexto = None
            if titulos:
                ultimo_titulo = titulos[-1]
                titulo_contexto = {
                    'numero': ultimo_titulo.group(1),
                    'nombre': ultimo_titulo.group(2).strip()
                }
            
            # Buscar última Sección antes de este artículo
            secciones = list(re.finditer(patron_seccion, texto_previo))
            seccion_contexto = None
            if secciones:
                ultima_seccion = secciones[-1]
                seccion_contexto = {
                    'numero': ultima_seccion.group(1),
                    'nombre': ultima_seccion.group(2).strip()
                }
            
            # Buscar último CAPÍTULO antes de este artículo
            capitulos = list(re.finditer(patron_capitulo, texto_previo))
            capitulo_contexto = None
            if capitulos:
                ultimo_capitulo = capitulos[-1]
                capitulo_contexto = {
                    'numero': ultimo_capitulo.group(1),
                    'nombre': ultimo_capitulo.group(2).strip()
                }
            
            # Estructurar párrafos numerados
            contenido_estructurado = self.estructurar_parrafos(contenido_limpio)

            # Extraer referencias cruzadas
            referencias = self.extraer_referencias(contenido_limpio)


            # Crear estructura del artículo
            articulo = {
                'numero': numero,
                'titulo': titulo_completo,
                'titulo_descriptivo': titulo_descriptivo,
                'contenido': contenido_limpio,
                'contenido_estructurado': contenido_estructurado,
                'referencias': referencias,
                'longitud_caracteres': len(contenido_limpio),
                'contexto': {
                    'titulo': titulo_contexto,
                    'capitulo': capitulo_contexto,
                    'seccion': seccion_contexto
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Solo guardar si tiene contenido real (más de 100 caracteres)
            # Esto filtra entradas del índice
            if len(contenido_limpio) >= 100:
                articulos.append(articulo)
        
        # ELIMINAR DUPLICADOS (conservar el primero)
        articulos_unicos = []
        numeros_vistos = set()
        
        for articulo in articulos:
            numero = articulo['numero']
            if numero not in numeros_vistos:
                articulos_unicos.append(articulo)
                numeros_vistos.add(numero)
            else:
                self.log(f"  ⚠ Duplicado eliminado: Art. {numero}")
        
        self.log(f"✓ Detectados {len(articulos_unicos)} artículos únicos (eliminados {len(articulos) - len(articulos_unicos)} duplicados)")
        return articulos_unicos
    
    def estructurar_parrafos(self, contenido):
        """
        Detecta y estructura párrafos numerados dentro del contenido
        
        Args:
            contenido (str): Contenido del artículo
            
        Returns:
            dict: Contenido estructurado con párrafos
        """
        # Patrón para detectar párrafos numerados
        # Formatos: "1.", "1.-", "1)\", "a)", "a."
        patron_parrafo = r'^(\d+[a-z]?|[a-z])[.)\-]\s+(.+?)(?=^\d+[a-z]?[.)\-]\s+|^[a-z][.)\-]\s+|\Z)'
        
        matches = list(re.finditer(patron_parrafo, contenido, re.MULTILINE | re.DOTALL))
        
        if not matches or len(matches) < 2:
            # No hay estructura de párrafos numerados
            return {
                'tipo': 'simple',
                'texto_completo': contenido,
                'parrafos': []
            }
        
        # Extraer párrafos
        parrafos = []
        for match in matches:
            numero = match.group(1).strip()
            texto = match.group(2).strip()
            
            # Limpiar texto
            texto = re.sub(r'\n{2,}', '\n', texto)  # Reducir saltos múltiples
            texto = texto.strip()
            
            if texto:  # Solo añadir si tiene contenido
                parrafos.append({
                    'numero': numero,
                    'texto': texto
                })
        
        return {
            'tipo': 'numerado',
            'total_parrafos': len(parrafos),
            'texto_completo': contenido,
            'parrafos': parrafos
        }

    def extraer_referencias(self, contenido):
        """
        Detecta y extrae referencias a otros artículos y leyes en el contenido
        
        Args:
            contenido (str): Contenido del artículo
            
        Returns:
            list: Lista de referencias encontradas (sin duplicados, priorizando fuentes conocidas)
        """
        referencias_dict = {}  # {numero: {fuente, contexto}}
        
       # Patrones mejorados - del más específico al más general
        # IMPORTANTE: El orden importa - patrones más específicos primero
        patrones = [
            # Patrón 1: "art. 103 de esta Normativa", "art. 62.6 de estas", "art. 93 de las presentes Normas"
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+de\s+(?:la\s+presente\s+|esta\s+|estas\s+|las\s+presentes\s+)(Normativa|Normas)', 'normativa_interna'),
            
           # Patrón 2: "art. 18 de la "Ley 37/2015..." (captura solo número, no todo el nombre)
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+de\s+la\s+[\u201c\u201d"]L[eé]i?\s+(\d+/\d+)', 'ley_con_nombre'),
            
            # Patrón 3: "art. 46 de la Constitución"
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+de\s+la\s+(Constitución)', 'constitucion'),
            
            # Patrón 4: "art. 96 de su reglamento", "art. 43 de dicha Ley"
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+de\s+(?:su|dicho|dicha)\s+(reglamento|Ley)', 'documento_referido'),
            
            # Patrón 5: "art. 68 LSG", "artículo 42 de la LSG", "art. 42 del RLSG"
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+(?:de\s+la\s+|del\s+)?([A-Z]{2,10})\b', 'ley_especifica'),
            
            # Patrón 6: "en el art. 34 de la Ley X/YYYY" (leyes numeradas sin comillas)
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+de\s+la\s+Ley\s+(\d+/\d+)', 'ley_numerada'),
            
            # Patrón 7: "art. 42 del Real Decreto", "artículo 50 del Reglamento"
            (r'art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\s+del?\s+(Real\s+Decreto|Reglamento)', 'decreto_reglamento'),
            
            # Patrón 8: "conforme al art. 42", "según el artículo 50" (sin fuente explícita)
            (r'(?:conforme|según|establecido|previsto|atender[áa])\s+(?:al|en\s+el|a\s+lo\s+establecido\s+en\s+el)\s+art(?:ículo|\.)?\s+(\d+(?:\.\d+)?)\b', 'contexto'),
        ]
        
        for patron, tipo in patrones:
            matches = re.finditer(patron, contenido, re.IGNORECASE)
            
            for match in matches:
                numero = match.group(1)
                
               # Determinar la fuente según el tipo de patrón
                if tipo == 'normativa_interna':
                    fuente = 'esta Normativa'
                    prioridad = 1  # Máxima prioridad
                    
                elif tipo == 'ley_con_nombre':
                    # Extraer solo el número de la ley
                    ley_numero = match.group(2).split()[0]  # "4/2023 de..." → "4/2023"
                    fuente = f"Ley {ley_numero}"
                    prioridad = 1
                    
                elif tipo == 'constitucion':
                    fuente = match.group(2)  # "Constitución"
                    prioridad = 1
                    
                elif tipo == 'documento_referido':
                    fuente = match.group(2)  # "reglamento" o "Ley"
                    prioridad = 2
                    
                elif tipo == 'ley_especifica':
                    fuente = match.group(2).upper()
                    prioridad = 2
                    
                elif tipo == 'ley_numerada':
                    fuente = f"Ley {match.group(2)}"
                    prioridad = 2
                    
                elif tipo == 'decreto_reglamento':
                    fuente = match.group(2)
                    prioridad = 2
                    
                elif tipo == 'contexto':
                    fuente = 'no especificada'
                    prioridad = 3  # Baja prioridad
                
                else:
                    fuente = 'no especificada'
                    prioridad = 3
                
                # Guardar o actualizar referencia
                if numero not in referencias_dict:
                    referencias_dict[numero] = {
                        'fuente': fuente,
                        'prioridad': prioridad
                    }
                else:
                    # Si ya existe, mantener la de mayor prioridad (menor número)
                    if prioridad < referencias_dict[numero]['prioridad']:
                        referencias_dict[numero] = {
                            'fuente': fuente,
                            'prioridad': prioridad
                        }
        
        # Convertir a lista final (sin duplicados)
        referencias = []
        for numero, datos in referencias_dict.items():
            referencias.append({
                'tipo': 'articulo',
                'numero': numero,
                'fuente': datos['fuente']
            })
        
        # Ordenar por número de artículo
        try:
            referencias.sort(key=lambda x: float(x['numero'].replace('.', '')))
        except:
            pass
        # HARDCODE: Correcciones manuales para casos edge con comillas tipográficas
        # Art. 21 → Art. 18 de la Ley 37/2015
        # Art. 65 → Art. 2 de la Ley 37/2015  
        # Art. 104, 174 → Art. 44.6 de la Ley de Costas
        correcciones = {
            ('18', 'DE'): 'Ley 37/2015',
            ('2', 'DE'): 'Ley 37/2015',
            ('44.6', 'DE'): 'Ley de Costas',
        }
        
        # Aplicar correcciones
        for ref in referencias:
            clave = (ref['numero'], ref['fuente'])
            if clave in correcciones:
                ref['fuente'] = correcciones[clave]
        
        return referencias

    def extraer_numero_articulo(self, titulo):
        """Extrae el número del artículo del título"""
        match = re.search(r'(\d+[a-z]?)', titulo)
        return match.group(1) if match else "desconocido"
    
    def guardar_json(self, articulos, nombre_archivo):
        """
        Guarda artículos en formato JSON
        
        Args:
            articulos (list): Lista de artículos
            nombre_archivo (str): Nombre del archivo sin extensión
        """
        try:
            filepath = os.path.join(CLEANED_JSON_DIR, f"{nombre_archivo}.json")
            
            # Añadir metadata
            datos = {
                'metadata': {
                    'total_articulos': len(articulos),
                    'fecha_extraccion': datetime.now().isoformat(),
                    'fuente': 'PXOM Vigo 2025 - Normativa Urbanística'
                },
                'articulos': articulos
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            
            self.log(f"✓ JSON guardado: {nombre_archivo}.json")
            
            # Estadísticas
            self.mostrar_estadisticas(articulos)
            
        except Exception as e:
            self.log(f"✗ ERROR guardando JSON: {str(e)}")
    
    def mostrar_estadisticas(self, articulos):
        """Muestra estadísticas de los artículos extraídos"""
        if not articulos:
            return
        
        total_caracteres = sum(a['longitud_caracteres'] for a in articulos)
        promedio = total_caracteres / len(articulos)
        
        self.log("\n" + "="*60)
        self.log("ESTADÍSTICAS DE EXTRACCIÓN")
        self.log("="*60)
        self.log(f"  Total artículos: {len(articulos)}")
        self.log(f"  Total caracteres: {total_caracteres:,}")
        self.log(f"  Promedio por artículo: {promedio:.0f} caracteres")
        self.log(f"  Artículo más largo: {max(articulos, key=lambda x: x['longitud_caracteres'])['numero']}")
        self.log(f"  Artículo más corto: {min(articulos, key=lambda x: x['longitud_caracteres'])['numero']}")
        self.log("="*60 + "\n")
    
    def procesar_pdf_normativa(self, url):
        """
        Proceso completo: descargar PDF → extraer texto → detectar artículos → guardar JSON
        
        Args:
            url (str): URL del PDF de normativa
        """
        self.log("\n" + "="*60)
        self.log("PROCESANDO PDF DE NORMATIVA URBANÍSTICA")
        self.log("="*60 + "\n")
        
        # 1. Descargar PDF
        pdf_path = self.descargar_pdf(url)
        if not pdf_path:
            return
        
        # 2. Extraer texto
        texto = self.extraer_texto_pdf(pdf_path)
        if not texto:
            return
        
        # 3. Detectar artículos
        articulos = self.detectar_articulos(texto)
        
        # 4. Guardar JSON
        if articulos:
            self.guardar_json(articulos, 'normativa_urbanistica_pxom_2025')
        else:
            self.log("⚠ No se encontraron artículos")
        
        self.log("\n" + "="*60)
        self.log("PROCESO COMPLETADO")
        self.log(f"Revisa: {CLEANED_JSON_DIR}/normativa_urbanistica_pxom_2025.json")
        self.log("="*60 + "\n")


def main():
    # URL del PDF principal de normativa
    PDF_NORMATIVA_URL = "https://xmu.vigo.org/docs/PXOM_2025/PXOM_2025/07_NU/36057_PXOM_202502_AD01_NU_01NU_cas.pdf"
    
    extractor = PDFExtractor()
    extractor.procesar_pdf_normativa(PDF_NORMATIVA_URL)


if __name__ == "__main__":
    main()