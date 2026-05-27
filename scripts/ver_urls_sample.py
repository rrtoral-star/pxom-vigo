import json
from pathlib import Path

DOCLING = Path(r"C:\PROY\pxom-solo\data\raw\docling")

dbs = [
    "cte_si_imagen_urls.json",
    "cte_sua_imagen_urls.json",
    "cte_hs_imagen_urls.json",
    "cte_se_imagen_urls.json",
    "cte_se_ae_imagen_urls.json",
    "cte_se_c_imagen_urls.json",
    "cte_se_a_imagen_urls.json",
    "cte_se_f_imagen_urls.json",
    "cte_se_m_imagen_urls.json",
    "cte_hr_imagen_urls.json",
    "cte_he_imagen_urls.json",
]

for json_name in dbs:
    path = DOCLING / json_name
    with open(path) as f:
        urls = json.load(f)
    primera_url = list(urls.values())[0]
    print(f"\n{json_name}:")
    print(f"  {primera_url}")