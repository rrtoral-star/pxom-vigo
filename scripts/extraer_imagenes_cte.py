import json, re, base64, os, hashlib
from supabase import create_client
from dotenv import load_dotenv
from collections import Counter
from pathlib import Path

load_dotenv()

sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

DOCLING = Path(r"C:\PROY\pxom-solo\data\raw\docling")

dbs = [
    ("cte_si.json",    "cte-si"),
    ("cte_sua.json",   "cte-sua"),
    ("cte_hs.json",    "cte-hs"),
    ("cte_se.json",    "cte-se"),
    ("cte_se_ae.json", "cte-se-ae"),
    ("cte_se_c.json",  "cte-se-c"),
    ("cte_se_a.json",  "cte-se-a"),
    ("cte_se_f.json",  "cte-se-f"),
    ("cte_se_m.json",  "cte-se-m"),
    ("cte_hr.json",    "cte-hr"),
    ("cte_he.json",    "cte-he"),
]

for json_name, fuente in dbs:
    json_path = DOCLING / json_name
    output_path = DOCLING / f"{fuente.replace('-', '_')}_imagen_urls.json"

    if output_path.exists():
        print(f"✓ {fuente} ya procesado, saltando...")
        continue

    if not json_path.exists():
        print(f"⏭ {json_name} no existe, saltando...")
        continue

    print(f"\nProcesando {fuente}...")

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    md = data['document']['md_content']
    patron = r'!\[Image\]\(data:image/(png|jpeg|jpg);base64,([^)]+)\)'
    matches = list(re.finditer(patron, md))
    print(f"  Imágenes totales: {len(matches)}")

    urls = {}
    hashes_vistos = {}

    for i, m in enumerate(matches):
        ext = m.group(1)
        b64 = m.group(2)

        try:
            img_bytes = base64.b64decode(b64)
            img_hash = hashlib.md5(img_bytes).hexdigest()

            if img_hash in hashes_vistos:
                urls[f"IMAGEN_{i+1}"] = hashes_vistos[img_hash]
                continue

            nombre = f"{fuente}/imagen_{i+1}.{ext}"
            sb.storage.from_("pxom-imagenes").upload(
                nombre,
                img_bytes,
                {"content-type": f"image/{ext}"}
            )
            url = sb.storage.from_("pxom-imagenes").get_public_url(nombre)
            urls[f"IMAGEN_{i+1}"] = url
            hashes_vistos[img_hash] = url

        except Exception as e:
            print(f"  Error imagen {i+1}: {e}")

    with open(output_path, 'w') as f:
        json.dump(urls, f, indent=2)

    contador = Counter(urls.values())
    print(f"  Únicas: {len(hashes_vistos)} de {len(matches)}")
    print(f"  Guardado en {output_path.name}")

print("\n✅ Imágenes CTE procesadas.")