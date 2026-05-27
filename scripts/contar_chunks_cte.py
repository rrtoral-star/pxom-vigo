import sys
sys.path.insert(0, r'C:\PROY\pxom-solo\src')
from chunker_docling import ChunkerDocling
from pathlib import Path

DOCLING = Path(r"C:\PROY\pxom-solo\data\raw\docling")

dbs = [
    ("cte_si_raw.md",    "cte-si"),
    ("cte_sua_raw.md",   "cte-sua"),
    ("cte_hs_raw.md",    "cte-hs"),
    ("cte_se_raw.md",    "cte-se"),
    ("cte_se_ae_raw.md", "cte-se-ae"),
    ("cte_se_c_raw.md",  "cte-se-c"),
    ("cte_se_a_raw.md",  "cte-se-a"),
    ("cte_se_f_raw.md",  "cte-se-f"),
    ("cte_se_m_raw.md",  "cte-se-m"),
    ("cte_hr_raw.md",    "cte-hr"),
    ("cte_he_raw.md",    "cte-he"),
]

total = 0
for md_name, fuente in dbs:
    c = ChunkerDocling(str(DOCLING / md_name), fuente=fuente)
    chunks = c.generar_chunks()
    print(f"{fuente}: {len(chunks)} chunks")
    total += len(chunks)

print(f"\nTotal CTE: {total} chunks")