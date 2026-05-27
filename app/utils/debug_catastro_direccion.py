"""
Debug Catastro - Prueba con dirección real
"""

import requests
import json

print("="*70)
print("DEBUG CATASTRO - Calle Colón 23, Vigo")
print("="*70)

# ============================================================
# TEST 1: Buscar por dirección (DNPLOC)
# ============================================================
print("\n[TEST 1] Buscar por dirección")
print("-"*50)

url1 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPLOC"
params1 = {
    'Provincia': 'PONTEVEDRA',
    'Municipio': 'VIGO',
    'Sigla': 'CL',       # CL = Calle
    'Calle': 'COLON',
    'Numero': '23'
}

print(f"URL: {url1}")
print(f"Params: {params1}")

try:
    r1 = requests.get(url1, params=params1, timeout=15)
    print(f"Status: {r1.status_code}")
    print(f"\n>>> RESPUESTA:")
    print(json.dumps(r1.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}")

# ============================================================
# TEST 2: Buscar calle en callejero
# ============================================================
print("\n" + "="*70)
print("[TEST 2] Buscar calle en callejero")
print("-"*50)

url2 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/ConsultaVia"
params2 = {
    'Provincia': 'PONTEVEDRA',
    'Municipio': 'VIGO',
    'TipoVia': 'CL',
    'NombreVia': 'COLON'
}

print(f"URL: {url2}")

try:
    r2 = requests.get(url2, params=params2, timeout=15)
    print(f"Status: {r2.status_code}")
    print(f"\n>>> RESPUESTA:")
    print(json.dumps(r2.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}")

# ============================================================
# TEST 3: Coordenadas del gist que SÍ funcionan (Pontevedra)
# ============================================================
print("\n" + "="*70)
print("[TEST 3] Coordenadas de referencia (Pontevedra)")
print("-"*50)

url3 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/json/Consulta_RCCOOR"
params3 = {
    'SRS': 'EPSG:4326',
    'CoorX': -8.588562011718752,
    'CoorY': 42.28137302193453
}

print(f"URL: {url3}")
print(f"Params: {params3}")

try:
    r3 = requests.get(url3, params=params3, timeout=15)
    print(f"Status: {r3.status_code}")
    print(f"\n>>> RESPUESTA:")
    print(json.dumps(r3.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}")

# ============================================================
# TEST 4: Si encontramos RC, consultar datos completos
# ============================================================
print("\n" + "="*70)
print("[TEST 4] Datos por RC (si test 1 o 3 devuelven RC)")
print("-"*50)

# Probar con una RC conocida de Vigo urbano
url4 = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"

# RC de ejemplo urbano Vigo (puedes cambiarla por la que encuentres)
params4 = {
    'RefCat': '5832501NG2753S'  # Formato urbano típico
}

print(f"Probando RC urbana: {params4['RefCat']}")

try:
    r4 = requests.get(url4, params=params4, timeout=15)
    print(f"Status: {r4.status_code}")
    resp = r4.json()
    print(f"\n>>> RESPUESTA:")
    print(json.dumps(resp, indent=2, ensure_ascii=False)[:2000])
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*70)
print("FIN DEBUG")
print("="*70)