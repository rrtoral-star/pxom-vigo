import sys
sys.path.insert(0, r'C:\PROY\pxom-solo\src')
from chunker_docling import ChunkerDocling

c = ChunkerDocling(r'C:\PROY\pxom-solo\data\raw\docling\nhv_raw.md', fuente='nhv')
articulos = c._extraer_articulos()
for a in articulos:
    print(f"Art. {a['numero']} | {a['titulo']}")