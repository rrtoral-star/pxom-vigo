# scripts\check_payload_art84.py
import sys, os
sys.path.insert(0, 'src')
from dotenv import load_dotenv
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv(dotenv_path=Path(".env"))
client = QdrantClient(url=os.getenv("QDRANT_CLOUD_URL"), api_key=os.getenv("QDRANT_CLOUD_API_KEY"))

hits = client.scroll(
    "pxom_vigo_2026_v2",
    scroll_filter=Filter(must=[
        FieldCondition(key="articulo_numero", match=MatchValue(value="84"))
    ]),
    limit=10,
    with_payload=True
)[0]

for h in hits:
    print(f"fuente       : {h.payload.get('fuente')}")
    print(f"ordenanza    : {h.payload.get('ordenanza_codigo')}")
    print(f"titulo       : {h.payload.get('titulo_articulo')}")
    print()