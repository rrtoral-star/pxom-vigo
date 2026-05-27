# scripts/cargar_postgis.py
import geopandas as gpd
import pandas as pd
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

load_dotenv()

#DB_URL = os.getenv("SUPABASE_DB_URL")
#print(f"DB_URL: {DB_URL}")  # ← debug

BASE = r"C:\PROY\pxom-solo\data\inspire\urbana\54057uA 54007 VIGO"

capas = {
    "catastro_parcela":  f"{BASE}\\PARCELA\\PARCELA.SHP",
    "catastro_constru":  f"{BASE}\\CONSTRU\\CONSTRU.SHP",
    "catastro_masa":     f"{BASE}\\MASA\\MASA.SHP",
    "catastro_subparce": f"{BASE}\\SUBPARCE\\SUBPARCE.SHP",
    "catastro_ejes":     f"{BASE}\\EJES\\EJES.SHP",
}

connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres.uwytwgasxooqswhyivfn",
    password=os.getenv("SUPABASE_DB_PASSWORD"),  # solo la contraseña
    host="aws-1-eu-west-2.pooler.supabase.com",
    port=5432,
    database="postgres"
)

engine = create_engine(connection_url)

# Verificar conexión
with engine.connect() as con:
    result = con.execute(text("SELECT PostGIS_Version()"))
    print(f"✅ Conectado a Supabase — PostGIS {result.fetchone()[0]}")

for tabla, path in capas.items():
    print(f"\nCargando {tabla}...")
    gdf = gpd.read_file(path)

    # Reproyectar a EPSG:4326 (estándar para Supabase)
    gdf = gdf.to_crs(epsg=4326)

    # Limpiar nombres de columnas a minúsculas
    gdf.columns = [c.lower() for c in gdf.columns]

    # Cargar a Supabase (reemplaza si ya existe)
    gdf.to_postgis(
        name=tabla,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
    )
    print(f"  ✅ {tabla}: {len(gdf)} registros cargados")

print("\n✅ Carga completada.")