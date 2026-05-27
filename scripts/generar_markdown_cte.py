"""
generar_markdown_cte.py - Convierte los JSON de Docling a markdown limpio
para todos los DB del CTE
"""

import json, re
from pathlib import Path

DOCLING_DIR = Path(r"C:\PROY\pxom-solo\data\raw\docling")

# Mapeo JSON → markdown
dbs = [
    ("cte_si.json",    "cte_si_raw.md"),
    ("cte_sua.json",   "cte_sua_raw.md"),
    ("cte_hs.json",    "cte_hs_raw.md"),
    ("cte_se.json",    "cte_se_raw.md"),
    ("cte_se_ae.json", "cte_se_ae_raw.md"),
    ("cte_se_c.json",  "cte_se_c_raw.md"),
    ("cte_se_a.json",  "cte_se_a_raw.md"),
    ("cte_se_f.json",  "cte_se_f_raw.md"),
    ("cte_se_m.json",  "cte_se_m_raw.md"),
    ("cte_hr.json",    "cte_hr_raw.md"),
    ("cte_he.json",    "cte_he_raw.md"),
]

for json_name, md_name in dbs:
    json_path = DOCLING_DIR / json_name
    md_path = DOCLING_DIR / md_name

    if not json_path.exists():
        print(f"⏭ {json_name} no existe aún, saltando...")
        continue

    if md_path.exists():
        print(f"✓ {md_name} ya existe, saltando...")
        continue

    print(f"Procesando {json_name}...")

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    md = data['document']['md_content']

    # Sustituir base64 por placeholder numerado
    counter = [0]
    def repl(m):
        counter[0] += 1
        return f'[IMAGEN_{counter[0]}]'

    md_limpio = re.sub(r'!\[Image\]\(data:image[^)]+\)', repl, md)

    # Limpiar espacios dobles
    md_limpio = re.sub(r'  +', ' ', md_limpio)
    md_limpio = re.sub(r' \n', '\n', md_limpio)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_limpio)

    print(f"✓ {md_name} ({len(md_limpio)//1024}KB, {counter[0]} imágenes)")

print("\n✅ Markdown generado para todos los DB disponibles.")