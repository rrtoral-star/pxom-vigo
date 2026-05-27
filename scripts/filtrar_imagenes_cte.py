import json
from pathlib import Path

DOCLING = Path(r"C:\PROY\pxom-solo\data\raw\docling")

decorativas = {
    "cte_he_imagen_urls.json":     {"IMAGEN_1"},
    "cte_hr_imagen_urls.json":     {"IMAGEN_1"},
    "cte_hs_imagen_urls.json":     {"IMAGEN_1"},
    "cte_se_a_imagen_urls.json":   set(),
    "cte_se_ae_imagen_urls.json":  set(),
    "cte_se_c_imagen_urls.json":   {"IMAGEN_1"},
    "cte_se_f_imagen_urls.json":   {"IMAGEN_1"},
    "cte_se_m_imagen_urls.json":   {"IMAGEN_1"},
    "cte_se_imagen_urls.json":     {"IMAGEN_1", "IMAGEN_2"},
    "cte_si_imagen_urls.json":     {"IMAGEN_1", "IMAGEN_2"},
    "cte_sua_imagen_urls.json":    {"IMAGEN_1"},
}

for json_name, excluir in decorativas.items():
    path = DOCLING / json_name
    if not path.exists():
        print(f"⏭ {json_name} no existe")
        continue

    with open(path) as f:
        urls = json.load(f)

    antes = len(urls)
    urls_filtrado = {k: v for k, v in urls.items() if k not in excluir}
    despues = len(urls_filtrado)

    with open(path, 'w') as f:
        json.dump(urls_filtrado, f, indent=2)

    print(f"✓ {json_name}: {antes} → {despues} URLs")

print("\n✅ Filtrado completado.")