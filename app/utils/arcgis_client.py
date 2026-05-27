"""
Cliente para consultas espaciales ArcGIS del Ayuntamiento de Vigo
"""

import requests
from typing import Optional, Dict
import sys
from pathlib import Path

# Añadir modules al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))
from coordinate_systems import wgs84_to_webmercator, validar_coordenadas_vigo

BASE_URL = "https://services9.arcgis.com/ss3qikvq575kYKRJ/ArcGIS/rest/services"

class ArcGISClient:
    """Cliente para consultas espaciales en servicios PXOM"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.timeout = 10
    
    def consultar_zona(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Consulta zona PXOM para coordenadas dadas
        
        Args:
            lat: Latitud WGS84
            lon: Longitud WGS84
        
        Returns:
            dict con información de zona o None
        """
        
        # Validar que está en Vigo
        if not validar_coordenadas_vigo(lat, lon):
            raise ValueError(f"Coordenadas fuera de Vigo: {lat}, {lon}")
        
        # Transformar a Web Mercator (sistema ArcGIS)
        x, y = wgs84_to_webmercator(lat, lon)
        
        # Intentar obtener clasificación primero
        clasificacion = self._query_clasificacion(x, y)
        
        if not clasificacion:
            return None
        
        # Si es suelo urbano, obtener ordenanza
        if clasificacion.get('clase') in ['UC', 'UNC', 'SU', 'SUC', 'SUNC']:
            ordenanza = self._query_ordenanza_urbana(x, y)
            if ordenanza:
                clasificacion.update(ordenanza)
        
        # Si es suelo rústico, obtener ordenanza
        elif clasificacion.get('clase') in ['SR', 'SNR']:
            ordenanza = self._query_ordenanza_rustica(x, y)
            if ordenanza:
                clasificacion.update(ordenanza)
        
        return clasificacion
    
    def _query_clasificacion(self, x: float, y: float) -> Optional[Dict]:
        """Consulta clasificación del suelo"""
        
        servicio = "36057_PXOM_202502_AD01_3CLAS_descri"
        url = f"{self.base_url}/{servicio}/FeatureServer/0/query"
        
        params = {
            'f': 'json',
            'geometry': f'{x},{y}',
            'geometryType': 'esriGeometryPoint',
            'inSR': '102100',  # Web Mercator
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'clase,clase_desc,cat,cat_desc,uso_global,nome',
            'returnGeometry': 'false'
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features'):
                    attrs = data['features'][0]['attributes']
                    return {
                        'clase': attrs.get('clase'),
                        'clase_desc': attrs.get('clase_desc'),
                        'categoria': attrs.get('cat'),
                        'uso_global': attrs.get('uso_global'),
                        'nombre': attrs.get('nome'),
                        'fuente': 'clasificacion'
                    }
            
            return None
            
        except Exception as e:
            print(f"Error consultando clasificación: {e}")
            return None
    
    def _query_ordenanza_urbana(self, x: float, y: float) -> Optional[Dict]:
        """Consulta ordenanza de suelo urbano"""
        
        servicio = "36057_PXOM_202502_AD01_4ORDSUC_nome"
        url = f"{self.base_url}/{servicio}/FeatureServer/0/query"
        
        params = {
            'f': 'json',
            'geometry': f'{x},{y}',
            'geometryType': 'esriGeometryPoint',
            'inSR': '102100',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'ordenanza,altura,nome,fondo',
            'returnGeometry': 'false'
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features'):
                    attrs = data['features'][0]['attributes']
                    return {
                        'ordenanza': attrs.get('ordenanza'),
                        'altura_arcgis': attrs.get('altura'),
                        'nombre_ordenanza': attrs.get('nome'),
                        'fondo': attrs.get('fondo')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error consultando ordenanza urbana: {e}")
            return None
    
    def _query_ordenanza_rustica(self, x: float, y: float) -> Optional[Dict]:
        """Consulta ordenanza de suelo rústico"""
        
        servicio = "36057_PXOM_202502_AD01_11ORDSNR"
        url = f"{self.base_url}/{servicio}/FeatureServer/0/query"
        
        params = {
            'f': 'json',
            'geometry': f'{x},{y}',
            'geometryType': 'esriGeometryPoint',
            'inSR': '102100',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'ordenanza,altura,nome',
            'returnGeometry': 'false'
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features'):
                    attrs = data['features'][0]['attributes']
                    return {
                        'ordenanza': attrs.get('ordenanza'),
                        'altura_arcgis': attrs.get('altura'),
                        'nombre_ordenanza': attrs.get('nome')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error consultando ordenanza rústica: {e}")
            return None


def test_arcgis():
    """Prueba consultas con puntos conocidos"""
    
    from coordinate_systems import PUNTOS_PRUEBA
    
    print("\n" + "="*70)
    print("TEST CONSULTAS ARCGIS")
    print("="*70)
    
    client = ArcGISClient()
    
    for key, punto in PUNTOS_PRUEBA.items():
        print(f"\n📍 {punto['nombre']}")
        print(f"   {punto['direccion']}")
        
        lat, lon = punto['wgs84']
        print(f"   WGS84: {lat:.6f}, {lon:.6f}")
        
        resultado = client.consultar_zona(lat, lon)
        
        if resultado:
            print(f"\n   ✓ Zona encontrada:")
            print(f"      Clasificación: {resultado.get('clase')} - {resultado.get('clase_desc')}")
            
            if resultado.get('ordenanza'):
                print(f"      Ordenanza: {resultado.get('ordenanza')}")
                print(f"      Nombre: {resultado.get('nombre_ordenanza')}")
                if resultado.get('altura_arcgis'):
                    print(f"      Altura: {resultado.get('altura_arcgis')}")
        else:
            print(f"\n   ⚠️  No se encontró zona (posible error)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    test_arcgis()