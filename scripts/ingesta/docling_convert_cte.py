import requests, time, json
from pathlib import Path

BASE_URL = "http://localhost:5001"
PARTES_DIR = Path(r"C:\PROY\pxom-solo\data\raw\cte_partes")
OUTPUT_DIR = Path(r"C:\PROY\pxom-solo\data\raw\docling")

partes = sorted(PARTES_DIR.glob("cte_parte_*.pdf"))
print(f"Partes encontradas: {len(partes)}")

for parte in partes:
    output = OUTPUT_DIR / parte.name.replace(".pdf", ".json")
    
    if output.exists():
        print(f"✓ {parte.name} ya procesada, saltando...")
        continue
    
    print(f"\nProcesando {parte.name}...")
    
    with open(parte, 'rb') as f:
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
                print(f"ERROR en {parte.name}")
                break
            time.sleep(10)
        except Exception as e:
            print(f"Conexión perdida: {e}")
            print("Esperando 30s y reintentando...")
            time.sleep(30)
            continue
    
    if status['task_status'] == 'success':
        print(f"Descargando resultado...")
        result = requests.get(f"{BASE_URL}/v1/result/{task_id}").json()
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✓ Guardado en {output.name}")

print("\n✅ Todas las partes procesadas.")