"""
Script de debug para ver la respuesta real de la API del Catastro
Ejecuta esto y pégame la salida completa
"""

import requests
import json

print("="*70)
print("DEBUG API CATASTRO - Respuestas RAW")
print("="*70)

# Coordenadas de prueba (zona residencial Vigo)
lat, lon = 42.2328, -8.7205

# ============================================================
# TEST 1: Endpoint JSON (WCF)
# ============================================================
print("\n[TEST 1] Endpoint JSON WCF")
print("-"*50)

url1 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/json/Consulta_RCCOOR"
params1 = {
    'SRS': 'EPSG:4326',
    'CoorX': lon,
    'CoorY': lat
}

print(f"URL: {url1}")
print(f"Params: {params1}")

try:
    r1 = requests.get(url1, params=params1, timeout=15)
    print(f"Status: {r1.status_code}")
    print(f"Content-Type: {r1.headers.get('Content-Type')}")
    print(f"\n>>> RESPUESTA COMPLETA:")
    print(r1.text)
    
    if r1.headers.get('Content-Type', '').startswith('application/json'):
        print(f"\n>>> JSON PARSEADO:")
        print(json.dumps(r1.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}")

# ============================================================
# TEST 2: Endpoint ASMX (legacy)
# ============================================================
print("\n" + "="*70)
print("[TEST 2] Endpoint ASMX Legacy")
print("-"*50)

url2 = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR"
params2 = {
    'SRS': 'EPSG:4326',
    'Coordenada_X': lon,
    'Coordenada_Y': lat
}

print(f"URL: {url2}")
print(f"Params: {params2}")

try:
    r2 = requests.get(url2, params=params2, timeout=15)
    print(f"Status: {r2.status_code}")
    print(f"Content-Type: {r2.headers.get('Content-Type')}")
    print(f"\n>>> RESPUESTA COMPLETA:")
    print(r2.text)
except Exception as e:
    print(f"ERROR: {e}")

# ============================================================
# TEST 3: Referencia catastral conocida
# ============================================================
print("\n" + "="*70)
print("[TEST 3] Consulta por Referencia Catastral")
print("-"*50)

url3 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"
params3 = {
    'RefCat': '36057A00100001'
}

print(f"URL: {url3}")
print(f"Params: {params3}")

try:
    r3 = requests.get(url3, params=params3, timeout=15)
    print(f"Status: {r3.status_code}")
    print(f"\n>>> RESPUESTA COMPLETA:")
    print(r3.text[:3000])  # Primeros 3000 chars
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*70)
print("FIN DEBUG - Copia toda esta salida y pégamela")
print("="*70)