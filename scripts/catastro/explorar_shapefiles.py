# scripts/explorar_shapefiles.py
import geopandas as gpd
import pandas as pd

BASE = r"C:\PROY\pxom-solo\data\inspire\urbana\54057uA 54007 VIGO"

capas = {
    "PARCELA":  f"{BASE}\\PARCELA\\PARCELA.SHP",
    "CONSTRU":  f"{BASE}\\CONSTRU\\CONSTRU.SHP",
    "MASA":     f"{BASE}\\MASA\\MASA.SHP",
    "SUBPARCE": f"{BASE}\\SUBPARCE\\SUBPARCE.SHP",
    "EJES":     f"{BASE}\\EJES\\EJES.SHP",
}

for nombre, path in capas.items():
    print(f"\n{'='*50}")
    print(f"  {nombre}")
    print(f"{'='*50}")
    gdf = gpd.read_file(path)
    print(f"  Registros : {len(gdf)}")
    print(f"  CRS       : {gdf.crs}")
    print(f"  Geometría : {gdf.geom_type.unique()}")
    print(f"  Columnas  : {list(gdf.columns)}")
    print(gdf.head(2).to_string())

# CARVIA sin geometría
print(f"\n{'='*50}")
print(f"  CARVIA (tabla sin geometría)")
print(f"{'='*50}")
df = pd.read_csv(f"{BASE}\\CARVIA\\Carvia.DBF", encoding="latin-1", on_bad_lines="skip")
print(df.head(5).to_string())