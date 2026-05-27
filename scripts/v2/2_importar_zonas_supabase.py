"""
Script 2: Importar zonas PXOM desde ArcGIS a Supabase
Objetivo: Exportar geometrías y metadatos de zonas al PostGIS
"""

import requests
import sys
from pathlib import Path
from typing import List, Dict
import json

# Añadir modules y utils al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app" / "utils"))

from coordinate_systems import webmercator_to_wgs84
from supabase_zoning import ZoningDB

BASE_URL = "https://services9.arcgis.com/ss3qikvq575kYKRJ/ArcGIS/rest/services"

def exportar_geometrias_arcgis(servicio: str, layer_id: int = 0) -> List[Dict]:
    """
    Exporta todas las features de una capa ArcGIS
    
    Args:
        servicio: Nombre del servicio
        layer_id: ID de la capa (default 0)
    
    Returns:
        Lista de features con geometrías y atributos
    """
    
    url = f"{BASE_URL}/{servicio}/FeatureServer/{layer_id}/query"
    
    features_totales = []
    offset = 0
    batch_size = 1000  # Máximo permitido por ArcGIS
    
    print(f"\n📥 Exportando {servicio}...")
    
    while True:
        params = {
            'f': 'json',
            'where': '1=1',  # Todos los registros
            'outFields': '*',
            'returnGeometry': 'true',
            'resultOffset': offset,
            'resultRecordCount': batch_size
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Error HTTP {response.status_code}")
                break
            
            data = response.json()
            
            if 'error' in data:
                print(f"   ❌ Error ArcGIS: {data['error']}")
                break
            
            features = data.get('features', [])
            
            if not features:
                break  # No hay más datos
            
            features_totales.extend(features)
            offset += len(features)
            
            print(f"   ✓ {offset} features exportadas...", end='\r')
            
            # Si recibimos menos del batch_size, ya terminamos
            if len(features) < batch_size:
                break
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            break
    
    print(f"\n   ✅ Total exportadas: {len(features_totales)}")
    return features_totales


def convertir_geometria_a_wgs84(geometria_arcgis: Dict) -> Dict:
    """
    Convierte geometría de Web Mercator (ArcGIS) a WGS84 (PostGIS)
    """
    
    # DEBUG: Ver estructura
    if not hasattr(convertir_geometria_a_wgs84, '_debug_shown'):
        print(f"\n   [DEBUG] Estructura geometría ArcGIS:")
        print(f"   {json.dumps(geometria_arcgis, indent=2)[:300]}...")
        convertir_geometria_a_wgs84._debug_shown = True
    
    # ArcGIS geometry puede no tener 'type', tiene 'rings' directamente
    if 'rings' in geometria_arcgis:
        rings_wgs84 = []
        
        for ring in geometria_arcgis['rings']:
            ring_wgs84 = []
            for punto in ring:
                x, y = punto[0], punto[1]
                lat, lon = webmercator_to_wgs84(x, y)
                ring_wgs84.append([lon, lat])  # GeoJSON usa [lon, lat]
            rings_wgs84.append(ring_wgs84)
        
        # Formato GeoJSON MultiPolygon (PostGIS requiere Multi)
        return {
            'type': 'MultiPolygon',
            'coordinates': [rings_wgs84]  # Array de polígonos
        }
    
    else:
        raise ValueError(f"Geometría sin 'rings': {list(geometria_arcgis.keys())}")


def procesar_ordenanzas_urbanas(features: List[Dict]) -> List[Dict]:
    """Procesa features de ordenanzas urbanas (U1-U9)"""
    
    zonas_procesadas = []
    contadores = {}  # Contador por ordenanza
    
    for feature in features:
        attrs = feature['attributes']
        geom = feature.get('geometry')
        
        if not geom:
            continue
        
        try:
            # Convertir geometría a WGS84
            geom_wgs84 = convertir_geometria_a_wgs84(geom)
            
            ordenanza = attrs.get('ordenanza', 'DESCONOCIDO')
            
            # Generar código único con contador
            if ordenanza not in contadores:
                contadores[ordenanza] = 0
            contadores[ordenanza] += 1
            
            codigo_unico = f"{ordenanza}-{contadores[ordenanza]:04d}"  # U1.1-0001, U1.1-0002...
            
            # Preparar datos para Supabase
            zona = {
                'codigo': codigo_unico,  # Código único
                'ordenanza': ordenanza,   # Ordenanza original (U1.1)
                'nombre': attrs.get('nome', ''),
                'clasificacion': 'Suelo Urbano',
                'geom': json.dumps(geom_wgs84),
                'altura_maxima': None,
                'edificabilidad': None,
                'ocupacion_maxima': None
            }
            
            zonas_procesadas.append(zona)
            
        except Exception as e:
            print(f"   ⚠️  Error procesando feature: {e}")
            continue
    
    return zonas_procesadas


def procesar_clasificacion(features: List[Dict]) -> List[Dict]:
    """Procesa features de clasificación general del suelo"""
    
    zonas_procesadas = []
    
    for feature in features:
        attrs = feature['attributes']
        geom = feature.get('geometry')
        
        if not geom:
            continue
        
        try:
            geom_wgs84 = convertir_geometria_a_wgs84(geom)
            
            clase = attrs.get('clase', '')
            codigo = attrs.get('cod', attrs.get('clase', 'DESCONOCIDO'))
            
            zona = {
                'codigo': codigo,
                'ordenanza': None,  # Se llenará con ordenanzas específicas
                'nombre': attrs.get('clase_desc', ''),
                'clasificacion': attrs.get('clase_desc', clase),
                'geom': json.dumps(geom_wgs84)
            }
            
            zonas_procesadas.append(zona)
            
        except Exception as e:
            print(f"   ⚠️  Error procesando feature: {e}")
            continue
    
    return zonas_procesadas


def main():
    """Ejecuta importación completa"""
    
    print("\n" + "="*70)
    print("IMPORTACIÓN ZONAS PXOM → SUPABASE")
    print("="*70)
    
    # Conectar a Supabase
    print("\n1. Conectando a Supabase...")
    try:
        db = ZoningDB()
        print("   ✓ Conectado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Limpiar tabla (opcional - comentar si quieres preservar datos)
    print("\n2. Limpiando tabla existente...")
    try:
        db.client.table('zonas_pxom').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("   ✓ Tabla limpiada")
    except:
        print("   ⚠️  No se pudo limpiar (puede estar vacía)")
    
    # Exportar y procesar ordenanzas urbanas
    print("\n3. Exportando ordenanzas urbanas (U1-U9)...")
    features_urbanas = exportar_geometrias_arcgis("36057_PXOM_202502_AD01_4ORDSUC_nome")
    
    if features_urbanas:
        zonas_urbanas = procesar_ordenanzas_urbanas(features_urbanas)
        print(f"   ✓ {len(zonas_urbanas)} zonas urbanas procesadas")
        
        # Insertar en Supabase
        print("\n4. Insertando zonas urbanas en Supabase...")
        insertadas = 0
        errores = 0
        
        for zona in zonas_urbanas:
            try:
                db.client.table('zonas_pxom').insert(zona).execute()
                insertadas += 1
                print(f"   ✓ {insertadas}/{len(zonas_urbanas)} insertadas...", end='\r')
            except Exception as e:
                errores += 1
                if errores <= 3:  # Mostrar solo primeros 3 errores
                    print(f"\n   ⚠️  Error insertando {zona['codigo']}: {e}")
        
        print(f"\n   ✅ {insertadas} zonas insertadas, {errores} errores")
    
    # Verificar resultado
    print("\n5. Verificando base de datos...")
    total = db.contar_zonas()
    print(f"   ✓ Total zonas en BD: {total}")
    
    # Probar consulta espacial
    print("\n6. Prueba de consulta espacial...")
    lat, lon = 42.2315, -8.7138  # Corte Inglés
    zona_test = db.consultar_zona(lat, lon)
    
    if zona_test:
        print(f"   ✅ Consulta exitosa!")
        print(f"      Punto: Corte Inglés ({lat}, {lon})")
        print(f"      Zona: {zona_test.get('codigo')}")
        print(f"      Clasificación: {zona_test.get('clasificacion')}")
    else:
        print(f"   ⚠️  No se encontró zona (puede ser gap en datos)")
    
    print("\n" + "="*70)
    print("IMPORTACIÓN COMPLETADA")
    print(f"Total zonas: {total}")
    print("Próximo paso: Enriquecer chunks con zonas")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()