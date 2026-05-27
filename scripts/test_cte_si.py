import sys
sys.path.insert(0, r'C:\PROY\pxom-solo\src')
from chunker_docling import ChunkerDocling

c = ChunkerDocling(r'C:\PROY\pxom-solo\data\raw\docling\cte_si_raw.md', fuente='cte-si')
chunks = c.generar_chunks()
articulos = c._extraer_articulos()
print(f'Secciones: {len(articulos)}')
print(f'Chunks: {len(chunks)}')
for a in articulos[:10]:
    print(f"  {a['numero']} | {a['titulo'][:50]}")