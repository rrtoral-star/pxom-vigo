"""
Cliente de Geocoding para convertir direcciones a coordenadas
Usa Nominatim (OpenStreetMap) - gratuito y sin API key
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from typing import Optional, Dict
import json
from pathlib import Path
import re
import sys

# Añadir módulos al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))
from coordinate_systems import validar_coordenadas_vigo


class GeocodingClient:
    """Cliente para geocodificación de direcciones en Vigo"""
    
    def __init__(self, cache_dir: str = "data/v2/cache"):
        self.geolocator = Nominatim(
            user_agent="pxom-vigo-app/2.0",
            timeout=10
        )
        
        # Cache local
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "geocoding_cache.json"
        self._load_cache()
        
        # Límites de Vigo para validación
        self.vigo_bounds = {
            'lat_min': 42.13,
            'lat_max': 42.29,
            'lon_min': -8.82,
            'lon_max': -8.60
        }
    
    def _load_cache(self):
        """Carga cache desde disco"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Guarda cache a disco"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error guardando cache: {e}")
    
    def geocode(self, direccion: str) -> Optional[Dict]:
        """
        Convierte dirección a coordenadas
        Prueba múltiples variantes automáticamente
        
        Args:
            direccion: Dirección completa o parcial
        
        Returns:
            dict con lat, lon, direccion_completa o None
        """
        
        # Normalizar dirección
        direccion_norm = direccion.strip()
        
        # Cache key
        cache_key = f"geo_{direccion_norm.lower()}"
        
        if cache_key in self.cache:
            print(f"   ✓ Geocoding (cache): {direccion_norm[:40]}...")
            return self.cache[cache_key]
        
        # Generar variantes de la dirección
        variantes = self._generar_variantes(direccion_norm)
        
        print(f"   → Geocodificando: {direccion_norm[:60]}...")
        
        # Probar cada variante
        for i, variante in enumerate(variantes):
            if i > 0:
                print(f"   → Variante {i+1}: {variante[:60]}...")
            
            try:
                time.sleep(1)  # Rate limiting
                
                # Añadir Vigo si no está
                if "vigo" not in variante.lower():
                    direccion_buscar = f"{variante}, Vigo, Pontevedra, España"
                else:
                    direccion_buscar = variante
                
                location = self.geolocator.geocode(
                    direccion_buscar,
                    exactly_one=True,
                    addressdetails=True
                )
                
                if not location:
                    continue  # Probar siguiente variante
                
                lat = location.latitude
                lon = location.longitude
                
                # Validar que esté en Vigo
                if not self._validar_en_vigo(lat, lon):
                    print(f"   ⚠️  Fuera de Vigo: {location.address[:50]}")
                    continue  # Probar siguiente variante
                
                resultado = {
                    'lat': lat,
                    'lon': lon,
                    'direccion_completa': location.address,
                    'direccion_original': direccion_norm,
                    'variante_usada': variante
                }
                
                print(f"   ✓ Encontrado: {lat:.6f}, {lon:.6f}")
                print(f"   ✓ {location.address}")
                
                # Guardar en cache
                self.cache[cache_key] = resultado
                self._save_cache()
                
                return resultado
                
            except GeocoderTimedOut:
                continue
            except Exception:
                # Intentar siguiente variante
                continue
        
        # Si llegamos aquí, ninguna variante funcionó
        print(f"   ⚠️  No se encontró (probadas {len(variantes)} variantes)")
        return None
    
    def _generar_variantes(self, direccion: str) -> list:
        """
        Genera variantes de una dirección para búsqueda
        
        Returns:
            Lista de variantes ordenadas por probabilidad
        """
        
        variantes = []
        direccion_lower = direccion.lower().strip()
        
        # Variante original
        variantes.append(direccion)
        
        # Detectar y extraer número si existe
        match_numero = re.search(r'\s+(\d+)\s*$', direccion)
        numero = match_numero.group(1) if match_numero else ""
        base_sin_numero = direccion[:match_numero.start()] if match_numero else direccion
        
        # Tipos de vía comunes en Vigo
        prefijos = [
            'calle ', 'c/', 'c\\',
            'avenida ', 'av.', 'av ',
            'plaza ', 'praza ', 'pza.',
            'paseo ',
            'rua ', 'rúa ', 'rúa de ',
            'camiño ', 'camino ',
            'estrada ', 'carretera ', 'ctra.',
            'travesía ', 'travesia ',
            'lugar ',
        ]
        
        # Detectar tipo de vía
        tipo_detectado = None
        nombre_via = base_sin_numero.strip()
        
        for prefijo in prefijos:
            if direccion_lower.startswith(prefijo):
                tipo_detectado = prefijo
                nombre_via = base_sin_numero[len(prefijo):].strip()
                break
        
        # Generar variantes
        if tipo_detectado or nombre_via != base_sin_numero:
            # Si tiene tipo de vía, probar variantes con los tipos más comunes en Vigo
            for tipo in ['rúa', 'avenida', 'camiño', 'estrada', 'praza', 'rúa de']:
                v = f"{tipo} {nombre_via}"
                if numero:
                    v += f" {numero}"
                if v.lower() != direccion_lower:
                    variantes.append(v)

            # Sin tipo de vía
            v_sin_tipo = nombre_via
            if numero:
                v_sin_tipo += f" {numero}"
            if v_sin_tipo.lower() != direccion_lower:
                variantes.append(v_sin_tipo)

        else:
            # Si NO tiene tipo de vía, añadir tipos comunes
            for tipo in ['rúa', 'avenida', 'camiño', 'estrada', 'rúa de', 'praza']:
                v = f"{tipo} {nombre_via}"
                if numero:
                    v += f" {numero}"
                variantes.append(v)
        
        # Eliminar duplicados manteniendo orden
        variantes_unicas = []
        for v in variantes:
            v_clean = v.strip()
            if v_clean and v_clean.lower() not in [x.lower() for x in variantes_unicas]:
                variantes_unicas.append(v_clean)
        
        return variantes_unicas
    
    def _validar_en_vigo(self, lat: float, lon: float) -> bool:
        """Valida que coordenadas estén en el área de Vigo"""
        
        # Validación amplia (incluye zonas periféricas)
        if not (self.vigo_bounds['lat_min'] <= lat <= self.vigo_bounds['lat_max']):
            return False
        
        if not (self.vigo_bounds['lon_min'] <= lon <= self.vigo_bounds['lon_max']):
            return False
        
        # Validación adicional usando módulo coordinate_systems
        try:
            return validar_coordenadas_vigo(lat, lon)
        except:
            # Si falla, usar validación básica
            return True
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Convierte coordenadas a dirección
        
        Args:
            lat: Latitud
            lon: Longitud
        
        Returns:
            dict con dirección o None
        """
        
        # Cache key
        cache_key = f"rev_{lat:.6f}_{lon:.6f}"
        
        if cache_key in self.cache:
            print(f"   ✓ Reverse geocoding (cache)")
            return self.cache[cache_key]
        
        try:
            print(f"   → Reverse geocoding: {lat:.6f}, {lon:.6f}")
            time.sleep(1)
            
            location = self.geolocator.reverse(
                f"{lat}, {lon}",
                exactly_one=True,
                addressdetails=True
            )
            
            if not location:
                print(f"   ⚠️  No se encontró dirección")
                return None
            
            resultado = {
                'direccion': location.address,
                'lat': lat,
                'lon': lon
            }
            
            print(f"   ✓ {location.address}")
            
            # Guardar en cache
            self.cache[cache_key] = resultado
            self._save_cache()
            
            return resultado
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None


def test_geocoding():
    """Prueba cliente Geocoding"""
    
    print("\n" + "="*70)
    print("TEST CLIENTE GEOCODING (CON VARIANTES AUTOMÁTICAS)")
    print("="*70)
    
    client = GeocodingClient()
    
    # Test 1: García Barbón (puede ser Calle o Avenida)
    print("\n1. Geocodificación - Calle García Barbón 15:")
    resultado = client.geocode("Calle García Barbón 15")
    
    if resultado:
        print(f"\n   ✅ Coordenadas:")
        print(f"      Lat: {resultado['lat']:.6f}")
        print(f"      Lon: {resultado['lon']:.6f}")
        print(f"      Variante: {resultado['variante_usada']}")
    
    # Test 2: Urzaiz (puede ser "Rúa Urzaiz" o "Rúa de Urzaiz")
    print("\n2. Geocodificación - Calle Urzaiz 1:")
    resultado2 = client.geocode("Calle Urzaiz 1")
    
    if resultado2:
        print(f"\n   ✅ Encontrado:")
        print(f"      Coords: {resultado2['lat']:.6f}, {resultado2['lon']:.6f}")
        print(f"      Variante: {resultado2['variante_usada']}")
    
    # Test 3: Landmark
    print("\n3. Geocodificación - Concello de Vigo:")
    resultado3 = client.geocode("Concello de Vigo")
    
    if resultado3:
        print(f"\n   ✅ Landmark encontrado:")
        print(f"      Coords: {resultado3['lat']:.6f}, {resultado3['lon']:.6f}")
    
    # Test 4: Reverse geocoding
    if resultado3:
        print("\n4. Reverse Geocoding:")
        reverse = client.reverse_geocode(resultado3['lat'], resultado3['lon'])
        
        if reverse:
            print(f"\n   ✅ Dirección desde coords:")
            print(f"      {reverse['direccion'][:70]}")
    
    # Test 5: Cache
    print("\n5. Test de cache:")
    resultado_cache = client.geocode("Calle García Barbón 15")
    
    if resultado_cache:
        print(f"   ✅ Cache funcionando")
    
    print("\n" + "="*70)
    print("CLIENTE GEOCODING LISTO")
    print(f"Cache: {client.cache_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_geocoding()