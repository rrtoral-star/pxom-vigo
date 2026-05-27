import json, sys
sys.path.insert(0, r'C:\PROY\pxom-solo\src')
from chunker_docling import ChunkerDocling

with open(r'C:\PROY\pxom-solo\data\raw\docling\pxom_imagen_urls.json') as f:
    urls = json.load(f)

chunker = ChunkerDocling(
    md_path=r'C:\PROY\pxom-solo\data\raw\docling\pxom_raw.md',
    fuente='pxom',
    imagen_urls_map=urls,
    max_frecuencia=3
)
chunks = chunker.generar_chunks()

con_imagenes = [c for c in chunks if c.imagen_urls]
print(f'Chunks con imagenes utiles: {len(con_imagenes)}')
for c in con_imagenes:
    print(f'Art. {c.articulo_numero} | {c.titulo_descriptivo}')
    for url in c.imagen_urls:
        nombre = url.split('/')[-1]
        print(f'  {nombre}')