# check_collections.py — corregido
import os
from dotenv import load_dotenv
from pathlib import Path
from qdrant_client import QdrantClient

load_dotenv(dotenv_path=Path(".env"))  # desde la raíz del proyecto

url = os.getenv("QDRANT_CLOUD_URL")
key = os.getenv("QDRANT_CLOUD_API_KEY")
print(f"URL: {url}")
print(f"KEY: {'OK' if key else 'VACÍA'}")

client = QdrantClient(url=url, api_key=key)
for c in client.get_collections().collections:
    info = client.get_collection(c.name)
    print(f"{c.name}: {info.points_count} puntos")