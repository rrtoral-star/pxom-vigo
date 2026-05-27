import requests, time, json

print('Enviando PDF a Docling...')
with open(r'C:\PROY\pxom-solo\data\raw\BOE-424_Codigo_Tecnico_de_la_Edificacion_CTE.pdf', 'rb') as f:
    r = requests.post('http://localhost:5001/v1/convert/file/async', files={'files': f})

print('Respuesta:', r.status_code, r.text[:200])
task_id = r.json()['task_id']
print(f'Task ID: {task_id}')

while True:
    status = requests.get(f'http://localhost:5001/v1/status/poll/{task_id}').json()
    print(f'Estado: {status["task_status"]}')
    if status['task_status'] in ['success', 'failure']:
        break
    time.sleep(10)
print('Descargando resultado...')  # ← añade esto
result = requests.get(f'http://localhost:5001/v1/result/{task_id}').json()
print('Guardando archivo...')      # ← y esto
with open(r'C:\PROY\pxom-solo\data\raw\docling\cte_test.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print('Guardado en cte_test.json')