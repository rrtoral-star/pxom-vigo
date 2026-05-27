import sys
sys.path.insert(0, 'src')
from chunker_docling import ChunkerDocling

c = ChunkerDocling('data/raw/docling/cte_si_raw.md', fuente='cte-si')
arts = c._extraer_articulos()
print(f"Total: {len(arts)}")
for a in arts:
    print(f"  {a['numero']:15} | {a['titulo'][:60]}")