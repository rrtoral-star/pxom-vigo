"""
crear_indices_cloud.py - Crea índices de payload en Qdrant Cloud
necesarios para filtros por ordenanza, ámbito, etc.

Uso:
    python scripts/crear_indices_cloud.py
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

load_dotenv()

CLOUD_URL     = os.getenv("QDRANT_CLOUD_URL")
CLOUD_API_KEY = os.getenv("QDRANT_CLOUD_API_KEY")

INDICES = {
    "pxom_vigo_2025_v2": [
        "ordenanza_codigo",
        "ambito",
        "articulo_numero",
    ],
    "habitabilidad_galicia_2010": [
        "articulo_numero",
    ],
    "habitabilidad_galicia_2023": [
        "articulo_numero",
    ],
}

def main():
    print("\n" + "="*60)
    print("CREANDO ÍNDICES EN QDRANT CLOUD")
    print("="*60)

    cloud = QdrantClient(url=CLOUD_URL, api_key=CLOUD_API_KEY, timeout=60)

    for coleccion, campos in INDICES.items():
        print(f"\n  Colección: {coleccion}")
        for campo in campos:
            try:
                cloud.create_payload_index(
                    collection_name=coleccion,
                    field_name=campo,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                print(f"    ✓ {campo}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"    · {campo} (ya existía)")
                else:
                    print(f"    ✗ {campo}: {e}")

    print(f"\n{'='*60}")
    print("✓ Índices creados")
    print("="*60)

if __name__ == "__main__":
    main()