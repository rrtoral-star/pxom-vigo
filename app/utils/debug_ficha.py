"""
Debug: Ver todos los datos disponibles en la ficha catastral
"""
import requests
import json

# RC de ejemplo (Urzaiz 1, Vigo)
ref_catastral = "3362013NG2736S0001RB"

print("="*70)
print(f"FICHA CATASTRAL COMPLETA: {ref_catastral}")
print("="*70)

# Endpoint de datos no protegidos
url = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"

params = {'RefCat': ref_catastral}

response = requests.get(url, params=params, timeout=15)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n=== RESPUESTA JSON COMPLETA ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))