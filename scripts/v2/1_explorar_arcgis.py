"""
Script 1: Explorar servicios ArcGIS del Ayuntamiento de Vigo
Objetivo: Identificar capas de zonificación PXOM y sistema coordenadas
"""

import requests
import json
from pathlib import Path

# URLs base
BASE_URL = "https://services9.arcgis.com/ss3qikvq575kYKRJ/ArcGIS/rest/services"

# Servicios PXOM más relevantes
SERVICIOS_PXOM = [
    "36057_PXOM_202502_AD01_3CLAS_descri",      # Clasificación suelo
    "36057_PXOM_202502_AD01_4ORDSUC_nome",      # Ordenanzas SUC
    "36057_PXOM_202502_AD01_11ORDSNR",          # Ordenanzas SNR
    "36057_PXOM_202502_AD01_O_SNR",             # Ordenanzas generales
    "iop_v5_clasificacion_lab2"                  # Clasificación con labels
]

def explorar_servicio(nombre_servicio):
    """Explora un servicio ArcGIS y retorna metadata"""
    
    url = f"{BASE_URL}/{nombre_servicio}/FeatureServer?f=pjson"
    
    print(f"\n{'='*70}")
    print(f"SERVICIO: {nombre_servicio}")
    print(f"{'='*70}")
    print(f"URL: {url}\n")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        # Información general
        print(f"📊 Capas disponibles: {len(data.get('layers', []))}")
        
        # Sistema de coordenadas CRÍTICO
        if 'spatialReference' in data:
            sr = data['spatialReference']
            wkid = sr.get('wkid', 'N/A')
            print(f"🗺️  SISTEMA COORDENADAS: EPSG:{wkid}")
            
            # Identificar sistema
            if wkid == 4326:
                print(f"   ✓ WGS84 (Lat/Lon en grados decimales)")
            elif wkid == 25829:
                print(f"   ✓ ETRS89 / UTM Zone 29N (metros)")
            elif wkid == 3857:
                print(f"   ✓ Web Mercator (metros)")
            else:
                print(f"   ⚠️  Sistema no estándar")
        
        # Listar capas
        print(f"\n📋 Capas:")
        for layer in data.get('layers', [])[:5]:  # Primeras 5
            print(f"   {layer.get('id')}: {layer.get('name')}")
            print(f"      Tipo: {layer.get('geometryType', 'N/A')}")
        
        # Explorar primera capa en detalle
        if data.get('layers'):
            layer_id = data['layers'][0]['id']
            explorar_capa(nombre_servicio, layer_id)
        
        return data
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout (servidor lento)")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def explorar_capa(nombre_servicio, layer_id):
    """Explora campos de una capa específica"""
    
    url = f"{BASE_URL}/{nombre_servicio}/FeatureServer/{layer_id}?f=pjson"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            layer_data = response.json()
            
            print(f"\n   📝 Campos de la capa {layer_id}:")
            
            # Campos relevantes para zonificación
            campos_clave = []
            for field in layer_data.get('fields', []):
                nombre = field.get('name')
                tipo = field.get('type')
                
                # Identificar campos importantes
                if any(k in nombre.lower() for k in ['zona', 'ordenanza', 'codigo', 'clas', 'edif', 'altura']):
                    campos_clave.append(f"      ⭐ {nombre}: {tipo}")
                else:
                    campos_clave.append(f"         {nombre}: {tipo}")
            
            # Mostrar solo primeros 15 campos
            for campo in campos_clave[:15]:
                print(campo)
            
            if len(campos_clave) > 15:
                print(f"      ... y {len(campos_clave) - 15} campos más")
            
            # Información de extensión geográfica
            if 'extent' in layer_data:
                extent = layer_data['extent']
                print(f"\n   🌍 Extensión geográfica:")
                print(f"      Min: ({extent.get('xmin')}, {extent.get('ymin')})")
                print(f"      Max: ({extent.get('xmax')}, {extent.get('ymax')})")
            
    except Exception as e:
        print(f"   ❌ Error explorando capa: {e}")


def consultar_punto_prueba(nombre_servicio, layer_id, x, y):
    """Prueba consulta espacial con punto conocido"""
    
    # Punto de prueba: Concello de Vigo (aprox)
    # WGS84: 42.2406, -8.7207
    # Si ArcGIS usa UTM29N: necesitamos transformar
    
    url = f"{BASE_URL}/{nombre_servicio}/FeatureServer/{layer_id}/query"
    
    params = {
        'f': 'json',
        'geometry': f'{x},{y}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('features'):
                print(f"\n✅ Consulta espacial exitosa!")
                print(f"   Encontrados: {len(data['features'])} registros")
                
                # Mostrar primer resultado
                if data['features']:
                    attrs = data['features'][0]['attributes']
                    print(f"\n   Primer resultado:")
                    for key, value in list(attrs.items())[:10]:
                        print(f"      {key}: {value}")
            else:
                print(f"\n⚠️  Consulta OK pero sin resultados (punto fuera de zona?)")
        else:
            print(f"\n❌ Error en consulta: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error en consulta espacial: {e}")


def main():
    """Ejecuta exploración completa"""
    
    print("\n" + "="*70)
    print("EXPLORACIÓN SERVICIOS ARCGIS - AYUNTAMIENTO DE VIGO")
    print("="*70)
    
    resultados = {}
    
    for servicio in SERVICIOS_PXOM:
        data = explorar_servicio(servicio)
        if data:
            resultados[servicio] = {
                'capas': len(data.get('layers', [])),
                'sistema_coordenadas': data.get('spatialReference', {}).get('wkid'),
                'url': f"{BASE_URL}/{servicio}/FeatureServer"
            }
    
    # Guardar resultados
    output_path = Path("data/v2/zonas/arcgis_metadata.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"RESUMEN")
    print(f"{'='*70}")
    print(f"✓ Servicios explorados: {len(resultados)}")
    print(f"✓ Metadata guardada en: {output_path}")
    
    # Sistema coordenadas predominante
    sistemas = [r['sistema_coordenadas'] for r in resultados.values() if r['sistema_coordenadas']]
    if sistemas:
        sistema_comun = max(set(sistemas), key=sistemas.count)
        print(f"✓ Sistema coordenadas más común: EPSG:{sistema_comun}")
        
        if sistema_comun == 4326:
            print(f"  → Perfecto: WGS84 (mismo que Catastro)")
        elif sistema_comun == 25829:
            print(f"  → Necesitaremos transformar de/a WGS84")
    
    print("\n" + "="*70)
    print("PRÓXIMO PASO:")
    print("  1. Verificar sistema coordenadas identificado")
    print("  2. Crear módulo de transformación (coordinate_systems.py)")
    print("  3. Probar consulta espacial con punto conocido")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()