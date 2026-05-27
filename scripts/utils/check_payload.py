# check_payload.py
import os
from dotenv import load_dotenv
from pathlib import Path
from qdrant_client import QdrantClient

load_dotenv(dotenv_path=Path(".env"))
client = QdrantClient(url=os.getenv("QDRANT_CLOUD_URL"), api_key=os.getenv("QDRANT_CLOUD_API_KEY"))

hits = client.scroll("pxom_vigo_2026_v2", limit=3, with_payload=True)[0]
for h in hits:
    print(h.payload.keys())
    print(f"  fuente: {h.payload.get('fuente')}")
    print(f"  tipo:   {h.payload.get('tipo')}")
    print()