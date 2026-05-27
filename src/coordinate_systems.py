"""
Módulo para transformación de sistemas de coordenadas
Convierte entre WGS84, Web Mercator y UTM 29N
"""

from pyproj import Transformer
from typing import Tuple

# Sistemas de coordenadas
EPSG_WGS84 = 4326          # Lat/Lon grados decimales (Catastro, Nominatim)
EPSG_WEB_MERCATOR = 102100  # Web Mercator (ArcGIS Ayuntamiento)
EPSG_UTM29N = 25829        # UTM Zone 29N (Posible alternativa)

# Crear transformadores (cachear para performance)
_transformers = {}

def get_transformer(from_epsg: int, to_epsg: int) -> Transformer:
    """Obtiene transformador con caché"""
    key = (from_epsg, to_epsg)
    
    if key not in _transformers:
        # Web Mercator usa código especial en pyproj
        from_crs = f"EPSG:{from_epsg}" if from_epsg != 102100 else "EPSG:3857"
        to_crs = f"EPSG:{to_epsg}" if to_epsg != 102100 else "EPSG:3857"
        
        _transformers[key] = Transformer.from_crs(
            from_crs,
            to_crs,
            always_xy=True  # Siempre (lon, lat) o (x, y)
        )
    
    return _transformers[key]


def wgs84_to_webmercator(lat: float, lon: float) -> Tuple[float, float]:
    """
    Convierte WGS84 (Catastro/Nominatim) → Web Mercator (ArcGIS)
    
    Args:
        lat: Latitud WGS84 (42.2406)
        lon: Longitud WGS84 (-8.7207)
    
    Returns:
        (x, y) en metros Web Mercator
    """
    transformer = get_transformer(EPSG_WGS84, EPSG_WEB_MERCATOR)
    x, y = transformer.transform(lon, lat)  # Nota: lon, lat (no lat, lon)
    return x, y


def webmercator_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """
    Convierte Web Mercator (ArcGIS) → WGS84
    
    Args:
        x: Coordenada X en metros
        y: Coordenada Y en metros
    
    Returns:
        (lat, lon) WGS84
    """
    transformer = get_transformer(EPSG_WEB_MERCATOR, EPSG_WGS84)
    lon, lat = transformer.transform(x, y)
    return lat, lon


def validar_coordenadas_vigo(lat: float, lon: float) -> bool:
    """
    Verifica que coordenadas están dentro de Vigo
    
    Args:
        lat: Latitud WGS84
        lon: Longitud WGS84
    
    Returns:
        True si está en el área de Vigo
    """
    # Bounding box aproximado de Vigo
    # Lat: 42.13 - 42.30
    # Lon: -8.79 - -8.61
    
    return (42.13 <= lat <= 42.30) and (-8.79 <= lon <= -8.61)


def calcular_distancia(coords1: Tuple[float, float], 
                       coords2: Tuple[float, float]) -> float:
    """
    Calcula distancia entre dos puntos WGS84
    
    Args:
        coords1: (lat1, lon1)
        coords2: (lat2, lon2)
    
    Returns:
        Distancia en metros
    """
    from geopy.distance import geodesic
    return geodesic(coords1, coords2).meters


# Puntos de prueba conocidos en Vigo
PUNTOS_PRUEBA = {
    'concello': {
        'nombre': 'Concello de Vigo',
        'wgs84': (42.2406, -8.7207),
        'direccion': 'Praza do Concello 1'
    },
    'corte_ingles': {
        'nombre': 'El Corte Inglés',
        'wgs84': (42.2315, -8.7138),
        'direccion': 'Gran Vía 25-27'
    },
    'urzaiz': {
        'nombre': 'Estación de Urzáiz',
        'wgs84': (42.2405, -8.7298),
        'direccion': 'Praza da Estación'
    },
    'samil': {
        'nombre': 'Playa de Samil',
        'wgs84': (42.2095, -8.7896),
        'direccion': 'Praia de Samil'
    }
}


def test_transformaciones():
    """Prueba transformaciones con puntos conocidos"""
    
    print("\n" + "="*70)
    print("TEST TRANSFORMACIONES COORDENADAS")
    print("="*70)
    
    for key, punto in PUNTOS_PRUEBA.items():
        print(f"\n📍 {punto['nombre']}")
        print(f"   Dirección: {punto['direccion']}")
        
        lat, lon = punto['wgs84']
        print(f"   WGS84: {lat:.6f}, {lon:.6f}")
        
        # Transformar a Web Mercator
        x, y = wgs84_to_webmercator(lat, lon)
        print(f"   Web Mercator: {x:.2f}, {y:.2f}")
        
        # Transformar de vuelta
        lat_back, lon_back = webmercator_to_wgs84(x, y)
        print(f"   WGS84 (vuelta): {lat_back:.6f}, {lon_back:.6f}")
        
        # Verificar precisión
        distancia = calcular_distancia((lat, lon), (lat_back, lon_back))
        print(f"   Error: {distancia:.6f} metros")
        
        if distancia < 0.001:
            print(f"   ✓ Precisión excelente")
        elif distancia < 1:
            print(f"   ✓ Precisión aceptable")
        else:
            print(f"   ⚠️  Error significativo")
        
        # Validar que está en Vigo
        if validar_coordenadas_vigo(lat, lon):
            print(f"   ✓ Coordenadas dentro de Vigo")
        else:
            print(f"   ⚠️  Coordenadas fuera de Vigo")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    test_transformaciones()