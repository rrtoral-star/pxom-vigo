# inspect_chunker.py
import sys
sys.path.insert(0, "src")

from chunker_docling import ChunkerDocling

# Ver qué métodos tiene
print(dir(ChunkerDocling))
print("---")

# Ver el código fuente
import inspect
print(inspect.getsource(ChunkerDocling))