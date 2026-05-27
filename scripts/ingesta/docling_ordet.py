# scripts/ingesta/docling_ordet.py
import json
import requests
from pathlib import Path

API = "http://localhost:5001"

PDF = Path(r"C:\Users\User\Desktop\VIGO_REVISION_PXOM_26.05.2025\36057_PXOM_202502_AD01_01PDF_DIL\11.ORDET\36057_PXOM_202502_AD01_ORDET_SUNC412_01PDF\04.NU\36057_PXOM_202502_AD01_ORDET_SUNC412_NU.pdf")

OUT = Path(r"C:\PROY\pxom-solo\data\raw\docling\ordet")
OUT.mkdir(parents=True, exist_ok=True)

print(f"Enviando: {PDF.name}")

with open(PDF, "rb") as f:
    response = requests.post(
        f"{API}/v1/convert/file",
        files={"files": (PDF.name, f, "application/pdf")},
        data={
            "do_table_structure": "true",
            "do_ocr": "false",
            "table_structure_options.mode": "accurate",
        },
        timeout=120
    )

if response.status_code != 200:
    print(f"Error {response.status_code}: {response.text[:500]}")
else:
    data = response.json()
    # Guardar JSON completo
    json_path = OUT / "sunc412_nu_raw.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Extraer markdown
    md = data.get("document", {}).get("md_content") or \
         data.get("output", {}).get("markdown") or \
         data.get("markdown") or \
         str(data)[:2000]

    md_path = OUT / "sunc412_nu_raw.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"Chars markdown: {len(md)}")
    print(f"JSON guardado: {json_path}")
    print("\n--- PRIMERAS 100 LÍNEAS ---")
    for i, line in enumerate(md.splitlines()[:100], 1):
        print(f"{i:3}: {line}")