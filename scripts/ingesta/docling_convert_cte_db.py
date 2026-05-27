import requests, time, json
from pathlib import Path

BASE_URL = "http://localhost:5001"
RAW_DIR = Path(r"C:\PROY\pxom-solo\data\raw")
OUTPUT_DIR = Path(r"C:\PROY\pxom-solo\data\raw\docling")

dbs = [
    ("cte-si.pdf",    "cte_si.json"),
    ("cte-sua.pdf",   "cte_sua.json"),
    ("cte-hs.pdf",    "cte_hs.json"),
    ("cte-se.pdf",    "cte_se.json"),
    ("cte-se-ae.pdf", "cte_se_ae.json"),
    ("cte-se-c.pdf",  "cte_se_c.json"),
    ("cte-se-a.pdf",  "cte_se_a.json"),
    ("cte-se-f.pdf",  "cte_se_f.json"),
    ("cte-se-m.pdf",  "cte_se_m.json"),
    ("cte-hr.pdf",    "cte_hr.json"),
    ("cte-he.pdf",    "cte_he.json"),
]

for pdf_name, json_name in dbs:
    pdf_path = RAW_DIR / pdf_name
    output = OUTPUT_DIR / json_name

    if output.exists():
        print(f"✓ {pdf_name} ya procesado, saltando...")
        continue

    print(f"\nProcesando {pdf_name}...")

    with open(pdf_path, 'rb') as f:
        r = requests.post(f"{BASE_URL}/v1/convert/file/async", files={'files': f})

    task_id = r.json()['task_id']
    print(f"Task ID: {task_id}")

    while True:
        try:
            status = requests.get(f"{BASE_URL}/v1/status/poll/{task_id}").json()
            print(f"Estado: {status['task_status']}")
            if status['task_status'] == 'success':
                break
            elif status['task_status'] == 'failure':
                print(f"ERROR en {pdf_name}")
                break
            time.sleep(10)
        except Exception as e:
            print(f"Conexión perdida: {e}")
            print("Esperando 30s...")
            time.sleep(30)
            continue

    if status['task_status'] == 'success':
        print(f"Descargando resultado...")
        result = requests.get(f"{BASE_URL}/v1/result/{task_id}").json()
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✓ Guardado {json_name}")

print("\n✅ Todos los DB procesados.")