"""
Chunker Docling v1.0 - Genera chunks desde markdown de Docling

Lee el markdown limpio (pxom_raw.md / nhv_raw.md) generado por Docling
y produce chunks compatibles con el pipeline existente (enricher, embeddings, indexer).

Cambios vs chunker.py:
- Lee markdown en vez de JSON
- Detecta artículos por cabeceras ## 
- Preserva tablas e imágenes asociadas al artículo
- Añade campos: wiki_path, imagen_urls, tiene_tablas, fuente
"""

import re
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class ChunkDocling:
    """Chunk enriquecido generado desde markdown de Docling"""

    # Identificación
    id: str = ""
    articulo_numero: str = ""
    parrafo_numero: int = 0

    # Contenido
    texto_original: str = ""
    texto_con_cabecera: str = ""
    cabecera: str = ""

    # Contexto jerárquico
    titulo_articulo: str = ""
    titulo_descriptivo: str = ""
    ordenanza: str = ""
    ordenanza_codigo: str = ""
    capitulo: str = ""
    seccion: str = ""
    titulo_normativa: str = ""

    # Flags semánticos
    define_altura: bool = False
    define_ocupacion: bool = False
    define_edificabilidad: bool = False
    define_retranqueos: bool = False
    define_parcela_minima: bool = False
    define_usos: bool = False
    ambito: str = ""

    # Enriquecimiento (se añade después)
    keywords: List[str] = field(default_factory=list)
    preguntas_sinteticas: List[str] = field(default_factory=list)
    resumen: str = ""

    # Referencias
    referencias: List[Dict] = field(default_factory=list)

    # Nuevo: Docling específico
    fuente: str = "pxom"           # pxom, nhv, cte...
    wiki_path: str = ""            # wiki/pxom/art-01.md
    imagen_urls: List[str] = field(default_factory=list)
    imagenes_raw: List[str] = field(default_factory=list)  # [IMAGEN_N] sin resolver
    tiene_tablas: bool = False
    tablas_md: List[str] = field(default_factory=list)    # tablas en markdown

    # Metadata
    longitud: int = 0
    tipo_chunk: str = "parrafo"

    def to_dict(self) -> dict:
        return asdict(self)

    def generar_id(self) -> str:
        base = f"{self.fuente}_art_{self.articulo_numero}_p{self.parrafo_numero}"
        return hashlib.md5(base.encode()).hexdigest()[:12]


class ChunkerDocling:
    """
    Genera chunks desde markdown limpio de Docling.

    Estrategia:
    - Detecta artículos por cabeceras ## Art. N.
    - Detecta secciones por cabeceras # TÍTULO / ## CAPÍTULO
    - Un chunk por párrafo dentro de cada artículo
    - Preserva tablas e imágenes asociadas al artículo
    """

    # Patrones
    PATRON_ARTICULO = re.compile(
        r'^##\s+Art(?:iculo|\.)\s*(\d+(?:\.\d+)?)[\.:]?\s*(.+?)\.?\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    PATRON_ORDENANZA = re.compile(
        r'\b[Oo]rdenanza\s+([UNR]\d+(?:\.\d+)?)\b'
    )
    PATRON_ORDENANZA_CABECERA = re.compile(
        r'^##\s+[Oo]rdenanza\s+([UNR]\d+(?:\.\d+)?)',
        re.MULTILINE
    )
    PATRON_CAPITULO = re.compile(
        r'^#{1,2}\s+(?:CAPÍTULO|Capítulo|CAPITULO|TÍTULO|Título|TITULO)\s+(.+?)$',
        re.MULTILINE | re.IGNORECASE
    )
    PATRON_IMAGEN = re.compile(r'\[IMAGEN_\d+\]')
    PATRON_TABLA = re.compile(r'(\|[^\n]+\|\n(?:\|[-:]+\|[-:\s|]*\n)?(?:\|[^\n]+\|\n)+)', re.MULTILINE)
    PATRON_ANEXO = re.compile(
        r'^##\s+ANEXO\s*(I{1,3}|II|III)(.*)$',
        re.MULTILINE | re.IGNORECASE
    )
    PATRON_SECCION_CTE = re.compile(
    r'^##\s+Secci[oó¾]n\s+([A-Z]{1,3}[\s\-]?\d+(?:\.\d+)?)\s+(.+?)$',
    re.MULTILINE | re.IGNORECASE
    )
    PATRON_SECCION_NUMERICA = re.compile(
    r'^##\s+(\d+(?:\.\d+)?)\s+([A-ZÁÉÍÓÚÑ][^#\n]{3,60})$',
    re.MULTILINE
    )
    # Flags semánticos
    TERMINOS_ALTURA = ['altura', 'plantas', 'pisos', 'niveles', 'rasante', 'cota', 'coronación']
    TERMINOS_OCUPACION = ['ocupación', 'ocupacion', 'superficie ocupada']
    TERMINOS_EDIFICABILIDAD = ['edificabilidad', 'aprovechamiento', 'm²/m²', 'm2/m2']
    TERMINOS_RETRANQUEOS = ['retranqueo', 'separación', 'lindero', 'medianera', 'fachada']
    TERMINOS_PARCELA = ['parcela mínima', 'solar mínimo', 'superficie mínima', 'frente mínimo']
    TERMINOS_USOS = ['uso', 'compatible', 'permitido', 'prohibido', 'autorizable']

    def __init__(self, md_path: str, fuente: str = "pxom",  
             imagen_urls_map: dict = None, max_frecuencia: int = 3):
        self.md_path = Path(md_path)
        self.fuente = fuente
        self.imagen_urls_map = imagen_urls_map or {}
        self.max_frecuencia = max_frecuencia
        self.md_content = ""
        from collections import Counter
        self.url_frecuencias = Counter(self.imagen_urls_map.values())
        self._cargar_markdown()

    def _cargar_markdown(self):
        with open(self.md_path, 'r', encoding='utf-8') as f:
            self.md_content = f.read()
        print(f"✓ Markdown cargado: {len(self.md_content)} chars")

        # Separar palabras unidas en cabeceras (problema NHV)
        self.md_content = re.sub(
            r'(#{1,3}\s+)([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+)([A-ZÁÉÍÓÚÑ])',
            lambda m: m.group(1) + m.group(2) + ' ' + m.group(3),
            self.md_content
        )
    def generar_chunks(self) -> List[ChunkDocling]:
        chunks = []
        articulos = self._extraer_articulos()
        print(f"✓ Artículos detectados: {len(articulos)}")

        for articulo in articulos:
            chunks_art = self._procesar_articulo(articulo)
            chunks.extend(chunks_art)

        print(f"✓ Chunks generados: {len(chunks)}")
        return chunks

    def _extraer_articulos(self) -> List[dict]:
        """Extrae bloques de texto por artículo.

        Estrategia por tipo de fuente:
        - PXOM / NHV : PATRON_ARTICULO + Anexos
        - CTE        : PATRON_SECCION_NUMERICA (ej: 13.1) + PATRON_SECCION_CTE (ej: HS 1)
        """
        es_cte = self.fuente.startswith("cte")

        # ── Rama CTE ──────────────────────────────────────────────────────────
        if es_cte:
            return self._extraer_secciones_cte()

        # ── Rama PXOM / NHV ───────────────────────────────────────────────────
        articulos = []
        matches = list(self.PATRON_ARTICULO.finditer(self.md_content))

        for i, match in enumerate(matches):
            numero = match.group(1)
            titulo = match.group(2).strip()
            inicio = match.end()
            fin = matches[i + 1].start() if i + 1 < len(matches) else len(self.md_content)
            texto_bloque = self.md_content[inicio:fin].strip()

            # Detectar contexto jerárquico antes del artículo
            contexto = self._extraer_contexto(match.start())

            articulos.append({
                'numero': numero,
                'titulo': titulo,
                'texto_bloque': texto_bloque,
                'contexto': contexto,
                'pos': match.start()
            })
 
        # Añadir Anexos como artículos especiales
        patron_anexo_simple = re.compile(r'^##\s+ANEXO\s*(II+|I)\b', re.MULTILINE)
        matches_anexo = list(patron_anexo_simple.finditer(self.md_content))
        vistos = set()

        for i, m in enumerate(matches_anexo):
            numero_romano = m.group(1).upper()
            if numero_romano in vistos:
                continue
            vistos.add(numero_romano)
            numero = f"Anexo-{numero_romano}"
            titulo = f"Anexo {numero_romano}"
            inicio = m.end()
            siguiente = matches_anexo[i + 1] if i + 1 < len(matches_anexo) else None
            # Saltar al siguiente anexo no visto
            while siguiente and siguiente.group(1).upper() in vistos:
                i += 1
                siguiente = matches_anexo[i + 1] if i + 1 < len(matches_anexo) else None
            fin = siguiente.start() if siguiente else len(self.md_content)
            texto_bloque = self.md_content[inicio:fin].strip()
            contexto = self._extraer_contexto(m.start())
            articulos.append({
                'numero': numero,
                'titulo': titulo,
                'texto_bloque': texto_bloque,
                'contexto': contexto,
                'pos': m.start()
            })
        return articulos

    # Patrón para secciones nivel 1 sin código (SE, HR, SE-AE...)
    PATRON_NIVEL1_CTE = re.compile(
        r'^##\s+(\d+)\s+([A-ZÁÉÍÓÚÑ][^#\n]{3,80})$',
        re.MULTILINE
    )
    # Patrón para anejos CTE
    PATRON_ANEJO_CTE = re.compile(
        r'^##\s+Anejo\s+([A-Z])\s+(.+?)$',
        re.MULTILINE | re.IGNORECASE
    )

    def _extraer_secciones_cte(self) -> List[dict]:
        """Extrae secciones principales de documentos CTE.

        Estrategia:
        - Si encuentra secciones con código (SI 1, HS 1...) → usa PATRON_SECCION_CTE
        - Si no → usa secciones nivel 1 (## 1, ## 2...) + Anejos (## Anejo A...)
        Las subsecciones quedan dentro del texto_bloque del padre.
        """
        articulos = []
        matches_cte = list(self.PATRON_SECCION_CTE.finditer(self.md_content))

        if matches_cte:
            # Documentos con código: SI, SUA, HS, HE
            matches = matches_cte
            for i, m in enumerate(matches):
                numero = m.group(1).strip()
                titulo = m.group(2).strip().lstrip('#').strip()
                inicio = m.end()
                fin = matches[i + 1].start() if i + 1 < len(matches) else len(self.md_content)
                texto_bloque = self.md_content[inicio:fin].strip()
                contexto = self._extraer_contexto(m.start())
                articulos.append({
                    'numero': numero,
                    'titulo': titulo,
                    'texto_bloque': texto_bloque,
                    'contexto': contexto,
                    'pos': m.start(),
                })
        else:
            # Documentos sin código: SE, HR, SE-AE, SE-A, SE-C, SE-F, SE-M
            # Secciones nivel 1 + Anejos
            todas = []
            for m in self.PATRON_NIVEL1_CTE.finditer(self.md_content):
                todas.append((m.start(), m.group(1).strip(), m.group(2).strip().lstrip('#').strip()))
            for m in self.PATRON_ANEJO_CTE.finditer(self.md_content):
                todas.append((m.start(), f"Anejo-{m.group(1).upper()}", m.group(2).strip().lstrip('#').strip()))

            todas.sort(key=lambda x: x[0])

            for i, (pos, numero, titulo) in enumerate(todas):
                inicio = self.md_content.index('\n', pos) + 1
                fin = todas[i + 1][0] if i + 1 < len(todas) else len(self.md_content)
                texto_bloque = self.md_content[inicio:fin].strip()
                contexto = self._extraer_contexto(pos)
                articulos.append({
                    'numero': numero,
                    'titulo': titulo,
                    'texto_bloque': texto_bloque,
                    'contexto': contexto,
                    'pos': pos,
                })

        # Deduplicar por número
        vistos = set()
        articulos_unicos = []
        for a in articulos:
            if a['numero'] not in vistos:
                vistos.add(a['numero'])
                articulos_unicos.append(a)

        return articulos_unicos

    def _extraer_contexto(self, pos: int) -> dict:
        """Extrae capítulo, sección y ordenanza antes de la posición"""
        texto_previo = self.md_content[:pos]

        # Ordenanza más cercana
        ordenanza = ""
        ordenanza_codigo = ""
        matches_ord = list(self.PATRON_ORDENANZA_CABECERA.finditer(texto_previo))
        if matches_ord:
            cod = matches_ord[-1].group(1)
            partes = cod.split('.')
            ordenanza = partes[0]
            ordenanza_codigo = cod

        # Capítulo más cercano
        capitulo = ""
        matches_cap = list(self.PATRON_CAPITULO.finditer(texto_previo))
        if matches_cap:
            capitulo = matches_cap[-1].group(1).strip()

        return {
            'ordenanza': ordenanza,
            'ordenanza_codigo': ordenanza_codigo,
            'capitulo': capitulo,
        }
    def _es_imagen_util(self, img_tag: str) -> bool:
        """Filtra imágenes decorativas por frecuencia de aparición"""
        key = img_tag.strip('[]')
        url = self.imagen_urls_map.get(key, '')
        if not url:
            return False
        return self.url_frecuencias[url] <= self.max_frecuencia
    
    def _procesar_articulo(self, articulo: dict) -> List[ChunkDocling]:
        chunks = []
        numero = articulo['numero']
        titulo = articulo['titulo']
        texto_bloque = articulo['texto_bloque']
        contexto = articulo['contexto']
        
        # Limpiar espacios dobles del PDF justificado
        texto_bloque = re.sub(r'  +', ' ', texto_bloque)
        texto_bloque = re.sub(r' \n', '\n', texto_bloque)
        contexto = articulo['contexto']
       
        # Extraer tablas del bloque
        tablas = self.PATRON_TABLA.findall(texto_bloque)
        texto_sin_tablas = self.PATRON_TABLA.sub('[TABLA]', texto_bloque)

        # Extraer imágenes
        imagenes = self.PATRON_IMAGEN.findall(texto_sin_tablas)
        texto_sin_imagenes = self.PATRON_IMAGEN.sub('', texto_sin_tablas)
        
        # Extraer imágenes
        imagenes = self.PATRON_IMAGEN.findall(texto_sin_tablas)
        imagenes_utiles = [img for img in imagenes if self._es_imagen_util(img)]
        imagen_urls_chunk = [self.imagen_urls_map.get(img.strip('[]'), '') 
                            for img in imagenes_utiles]
        texto_sin_imagenes = self.PATRON_IMAGEN.sub('', texto_sin_tablas)

        # Extraer ordenanza del texto si no está en contexto
        ordenanza = contexto.get('ordenanza', '')
        ordenanza_codigo = contexto.get('ordenanza_codigo', '')
        if not ordenanza:
            ordenanza, ordenanza_codigo = self._extraer_ordenanza(titulo + ' ' + texto_bloque)

        capitulo = contexto.get('capitulo', '')

        # Dividir en párrafos
        parrafos = [p.strip() for p in re.split(r'\n{2,}', texto_sin_imagenes) if p.strip() and p.strip() != '[TABLA]']

        if not parrafos:
            parrafos = [texto_sin_imagenes.strip()]

        for i, parrafo in enumerate(parrafos):
            if len(parrafo) < 20:
                continue

            flags = self._detectar_flags(parrafo)
            ambito = self._detectar_ambito(parrafo, capitulo)

            chunk = ChunkDocling(
                articulo_numero=numero,
                parrafo_numero=i,
                texto_original=parrafo,
                titulo_articulo=f"Art. {numero}. {titulo}",
                titulo_descriptivo=titulo,
                ordenanza=ordenanza,
                ordenanza_codigo=ordenanza_codigo,
                capitulo=capitulo,
                fuente=self.fuente,
                wiki_path=f"wiki/{self.fuente}/art-{numero.replace('.', '-')}.md",
                imagenes_raw=imagenes_utiles if i == 0 else [],
                imagen_urls=imagen_urls_chunk if i == 0 else [],
                tiene_tablas=len(tablas) > 0 and i == 0,
                tablas_md=tablas if i == 0 else [],
                ambito=ambito,
                longitud=len(parrafo),
                tipo_chunk="parrafo" if len(parrafos) > 1 else "articulo_completo",
                **flags
            )

            chunk.cabecera = self._generar_cabecera(chunk)
            chunk.texto_con_cabecera = f"{chunk.cabecera}\n\n{chunk.texto_original}"
            if tablas and i == 0:
                chunk.texto_con_cabecera += "\n\n" + "\n\n".join(tablas)
            chunk.id = chunk.generar_id()

            chunks.append(chunk)

        return chunks

    def _extraer_ordenanza(self, texto: str) -> tuple:
        match = self.PATRON_ORDENANZA.search(texto)
        if match:
            cod = match.group(1)
            partes = cod.split('.')
            return partes[0], cod
        return "", ""

    def _detectar_flags(self, texto: str) -> dict:
        texto_lower = texto.lower()
        return {
            'define_altura': any(t in texto_lower for t in self.TERMINOS_ALTURA),
            'define_ocupacion': any(t in texto_lower for t in self.TERMINOS_OCUPACION),
            'define_edificabilidad': any(t in texto_lower for t in self.TERMINOS_EDIFICABILIDAD),
            'define_retranqueos': any(t in texto_lower for t in self.TERMINOS_RETRANQUEOS),
            'define_parcela_minima': any(t in texto_lower for t in self.TERMINOS_PARCELA),
            'define_usos': any(t in texto_lower for t in self.TERMINOS_USOS),
        }

    def _detectar_ambito(self, texto: str, capitulo: str) -> str:
        texto_lower = texto.lower()
        cap_lower = capitulo.lower()
        if 'urbano consolidado' in texto_lower or 'urbano consolidado' in cap_lower:
            return 'urbano_consolidado'
        elif 'urbano no consolidado' in texto_lower:
            return 'urbano_no_consolidado'
        elif 'núcleo rural' in texto_lower or 'nucleo rural' in cap_lower:
            return 'nucleo_rural'
        elif 'rústico' in texto_lower or 'rustico' in cap_lower:
            return 'rustico'
        elif 'suelo urbano' in texto_lower or 'suelo urbano' in cap_lower:
            return 'urbano'
        return ''

    def _generar_cabecera(self, chunk: ChunkDocling) -> str:
        partes = []
        if chunk.ordenanza_codigo:
            partes.append(f"ORDENANZA {chunk.ordenanza_codigo}")
        elif chunk.ordenanza:
            partes.append(f"ORDENANZA {chunk.ordenanza}")
        if chunk.capitulo:
            cap_limpio = re.sub(r'\s+\d+$', '', chunk.capitulo)
            partes.append(cap_limpio)
        if chunk.articulo_numero:
            partes.append(f"Art. {chunk.articulo_numero}")
        if chunk.titulo_descriptivo:
            partes.append(chunk.titulo_descriptivo)
        conceptos = []
        if chunk.define_altura: conceptos.append("altura")
        if chunk.define_ocupacion: conceptos.append("ocupación")
        if chunk.define_edificabilidad: conceptos.append("edificabilidad")
        if chunk.define_retranqueos: conceptos.append("retranqueos")
        if chunk.define_parcela_minima: conceptos.append("parcela mínima")
        if chunk.define_usos: conceptos.append("usos")
        if conceptos:
            partes.append(f"[{', '.join(conceptos)}]")
        return " | ".join(partes)
    
if __name__ == "__main__":
    chunker = ChunkerDocling(
        md_path=r"C:\PROY\pxom-solo\data\raw\docling\pxom_raw.md",
        fuente="pxom"
    )
    chunks = chunker.generar_chunks()

    print("\n" + "="*70)
    print("EJEMPLOS")
    print("="*70)
    for chunk in chunks[:3]:
        print(f"\nID: {chunk.id}")
        print(f"Art: {chunk.articulo_numero} | Párrafo: {chunk.parrafo_numero}")
        print(f"Ordenanza: {chunk.ordenanza_codigo or chunk.ordenanza}")
        print(f"Cabecera: {chunk.cabecera}")
        print(f"Tablas: {chunk.tiene_tablas} | Imágenes: {len(chunk.imagenes_raw)}")
        print(f"Wiki: {chunk.wiki_path}")
        print(f"Texto: {chunk.texto_original[:150]}...")

    con_tablas = sum(1 for c in chunks if c.tiene_tablas)
    con_imagenes = sum(1 for c in chunks if c.imagenes_raw)
    con_ordenanza = sum(1 for c in chunks if c.ordenanza)
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Con ordenanza: {con_ordenanza}")
    print(f"Con tablas: {con_tablas}")
    print(f"Con imágenes: {con_imagenes}")