"""
Cliente Supabase para consultas de zonificación
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ZoningDB:
    """Cliente para consultas de zonas PXOM en Supabase"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL y SUPABASE_KEY deben estar configuradas en .env"
            )
        
        self.client: Client = create_client(url, key)
    
    def consultar_zona(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Consulta zona PXOM para coordenadas dadas
        
        Args:
            lat: Latitud WGS84
            lon: Longitud WGS84
        
        Returns:
            dict con datos de zona o None
        """
        try:
            # Llamar función PostGIS
            result = self.client.rpc(
                'get_zona_by_point',
                {'lat': lat, 'lon': lon}
            ).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error consultando Supabase: {e}")
            return None
    
    def insertar_zona(self, zona_data: dict) -> bool:
        """Inserta nueva zona en la base de datos"""
        try:
            self.client.table('zonas_pxom').insert(zona_data).execute()
            return True
        except Exception as e:
            print(f"Error insertando zona: {e}")
            return False
    
    def contar_zonas(self) -> int:
        """Retorna número total de zonas en la BD"""
        try:
            result = self.client.table('zonas_pxom')\
                .select('*', count='exact')\
                .execute()
            return result.count
        except Exception as e:
            print(f"Error contando zonas: {e}")
            return 0

    def consultar_zona_por_rc(self, rc: str) -> dict | None:
        """
        Consulta zona PXOM usando la RC real (más preciso que coordenadas).
        Llama a info_urbanistica(rc) en Supabase.
        """
        try:
            result = self.client.rpc(
                "info_urbanistica", {"rc": rc}
            ).execute()
            return result.data if result.data else None
        except Exception as e:
            print(f"Error consultando info_urbanistica: {e}")
            return None
        
def test_supabase():
    """Prueba conexión a Supabase"""
    
    print("\n" + "="*70)
    print("TEST CONEXIÓN SUPABASE")
    print("="*70)
    
    try:
        db = ZoningDB()
        print("✓ Conexión establecida")
        
        # Contar zonas
        num_zonas = db.contar_zonas()
        print(f"✓ Zonas en BD: {num_zonas}")
        
        # Probar consulta (aunque esté vacía)
        lat, lon = 42.2406, -8.7207  # Concello Vigo
        zona = db.consultar_zona(lat, lon)
        
        if zona:
            print(f"\n✓ Zona encontrada:")
            print(f"   Código: {zona.get('codigo')}")
            print(f"   Ordenanza: {zona.get('ordenanza')}")
        else:
            print(f"\n⚠️  No hay zonas aún (BD vacía - normal)")
            print(f"   Próximo paso: importar zonas de ArcGIS")
        
        print("\n" + "="*70)
        print("PRÓXIMO PASO:")
        print("  Script para importar zonas de ArcGIS → Supabase")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nVerifica:")
        print("  1. Archivo .env existe y tiene las credenciales")
        print("  2. SUPABASE_URL y SUPABASE_KEY están correctas")


if __name__ == "__main__":
    test_supabase()