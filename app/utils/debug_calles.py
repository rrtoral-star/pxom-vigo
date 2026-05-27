"""
Debug: Ver respuesta XML de búsqueda de calles
"""
import requests

url = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/ConsultaVia"

params = {
    'Provincia': 'PONTEVEDRA',
    'Municipio': 'VIGO',
    'TipoVia': '',
    'NombreVia': 'URZAIZ'
}

print("=== DEBUG BÚSQUEDA CALLES ===")
print(f"URL: {url}")
print(f"Params: {params}")

response = requests.get(url, params=params, timeout=15)
print(f"Status: {response.status_code}")
print(f"\n=== RESPUESTA XML ===")
print(response.text[:3000])