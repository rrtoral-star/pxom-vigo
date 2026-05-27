"""
Carga shapefiles del Catastro a Supabase via REST API (batch mode)
"""
import geopandas as gpd
import json
import os
from shapely.geometry import MultiPolygon, MultiLineString
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

BASE = r"C:\PROY\pxom-solo\data\inspire\urbana\54057uA 54007 VIGO"
BATCH_SIZE = 100

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

def limpiar_valor(val):
    if val is None:
        return None
    if hasattr(val, '__float__') and str(val) == 'nan':
        return None
    if hasattr(val, 'item'):
        return val.item()
    return val

def geom_to_geojson(geom):
    return json.dumps(geom.__geo_interface__)

def cargar_capa(tabla, config, skip=True):
    """
    skip=True: salta la capa si ya tiene datos
    """
    print(f"\nCargando {tabla}...")

    # Verificar si ya tiene datos
    if skip:
        count = client.table(tabla).select('id', count='exact').execute()
        if count.count and count.count > 0:
            print(f"  ⏭️  Ya tiene {count.count} registros, saltando.")
            return

    gdf = gpd.read_file(config["path"])
    gdf = gdf.to_crs(epsg=4326)

    # Convertir a Multi
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
    batch = []

    for _, row in gdf.iterrows():
        registro = {}
        for campo in config["campos"]:
            registro[campo] = limpiar_valor(row.get(campo))
        registro["geom"] = geom_to_geojson(row.geometry)
        batch.append(registro)

        if len(batch) >= BATCH_SIZE:
            try:
                client.table(tabla).insert(batch).execute()
                insertadas += len(batch)
                print(f"  {insertadas}/{total}...", end='\r')
            except Exception as e:
                errores += len(batch)
                print(f"\n  ⚠️  Error batch: {e}")
            batch = []

    # Último batch
    if batch:
        try:
            client.table(tabla).insert(batch).execute()
            insertadas += len(batch)
        except Exception as e:
            errores += len(batch)

    print(f"  ✅ {tabla}: {insertadas}/{total} insertadas, {errores} errores")

print("="*60)
print("CARGA CATASTRO → SUPABASE (batch mode)")
print("="*60)

# Forzar recarga de catastro_constru
cargar_capa("catastro_constru", CAPAS["catastro_constru"], skip=False)

#for tabla, config in CAPAS.items(): 
#    cargar_capa(tabla, config)

print("\n✅ Carga completada.")