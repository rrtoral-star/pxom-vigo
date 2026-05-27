"""
Carga shapefiles del Catastro a Supabase via REST API
"""
import geopandas as gpd
import json
import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Conexión Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

BASE = r"C:\PROY\pxom-solo\data\inspire\urbana\54057uA 54007 VIGO"

CAPAS = {
    "catastro_parcela": {
        "path": f"{BASE}\\PARCELA\\PARCELA.SHP",
        "campos": ["refcat", "via", "numero", "area", "fechaalta", "fechabaja", "masa"],
    },
    "catastro_constru": {
        "path": f"{BASE}\\CONSTRU\\CONSTRU.SHP",
        "campos": ["refcat", "constru", "area", "fechaalta", "fechabaja", "masa"],
    },
    "catastro_masa": {
        "path": f"{BASE}\\MASA\\MASA.SHP",
        "campos": ["refcat", "masa", "area"],
    },
    "catastro_ejes": {
        "path": f"{BASE}\\EJES\\EJES.SHP",
        "campos": ["via", "ttggss"],
    },
}

def geom_to_geojson(geom):
    """Convierte geometría GeoPandas a GeoJSON string"""
    return json.dumps(geom.__geo_interface__)

def cargar_capa(tabla, config):
    print(f"\nCargando {tabla}...")
    gdf = gpd.read_file(config["path"])
    gdf = gdf.to_crs(epsg=4326)
    
    # Convertir Polygon a MultiPolygon
    from shapely.geometry import MultiPolygon, MultiLineString
    if tabla == "catastro_ejes":
        gdf["geometry"] = gdf["geometry"].apply(
            lambda g: MultiLineString([g]) if g.geom_type == "LineString" else g
        )
    else:
        gdf["geometry"] = gdf["geometry"].apply(
            lambda g: MultiPolygon([g]) if g.geom_type == "Polygon" else g
        )
    gdf.columns = [c.lower() for c in gdf.columns]

    total = len(gdf)
    insertadas = 0
    errores = 0

    for _, row in gdf.iterrows():
        try:
            registro = {}
            for campo in config["campos"]:
                val = row.get(campo)
                # Convertir NaN y tipos numpy a Python nativo
                if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'float' and str(val) == 'nan'):
                    registro[campo] = None
                elif hasattr(val, 'item'):
                    registro[campo] = val.item()
                else:
                    registro[campo] = val

            registro["geom"] = geom_to_geojson(row.geometry)

            client.table(tabla).insert(registro).execute()
            insertadas += 1

            if insertadas % 500 == 0:
                print(f"  {insertadas}/{total}...", end='\r')

        except Exception as e:
            errores += 1
            if errores <= 3:
                print(f"\n  ⚠️  Error en fila {insertadas}: {e}")

    print(f"  ✅ {tabla}: {insertadas}/{total} insertadas, {errores} errores")

# Ejecutar
print("="*60)
print("CARGA CATASTRO → SUPABASE")
print("="*60)

for tabla, config in CAPAS.items():
    cargar_capa(tabla, config)

print("\n✅ Carga completada.")