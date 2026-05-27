"""
03_migrar_a_cloud.py - Migra colecciones locales a Qdrant Cloud

Migra:
  - pxom_vigo_2025_v2        (1285 chunks)
  - habitabilidad_galicia_2010 (16 chunks)

Uso:
    python scripts/03_migrar_a_cloud.py

Requiere en .env:
    QDRANT_CLOUD_URL=https://xxxx.us-east4-0.gcp.cloud.qdrant.io
    QDRANT_CLOUD_API_KEY=tu_api_key
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

# ── Configuración ────────────────────────────────────────────
LOCAL_PATH   = "C:/PROY/pxom-solo/data/rag/qdrant_v2"
CLOUD_URL    = os.getenv("QDRANT_CLOUD_URL")
CLOUD_API_KEY = os.getenv("QDRANT_CLOUD_API_KEY")

COLECCIONES = [
    "pxom_vigo_2025_v2",
    "habitabilidad_galicia_2010",
    "habitabilidad_galicia_2023",
]

VECTOR_SIZE  = 1024
BATCH_SIZE   = 20   # Reducido para evitar timeout


def migrar_coleccion(local: QdrantClient, cloud: QdrantClient, nombre: str):
    print(f"\n{'='*60}")
    print(f"Migrando: {nombre}")
    print('='*60)

    # Contar puntos locales
    info = local.get_collection(nombre)
    total = info.points_count
    print(f"  Puntos locales: {total}")

    # Crear colección en cloud (recrear si existe)
    colecciones_cloud = [c.name for c in cloud.get_collections().collections]
    if nombre in colecciones_cloud:
        print(f"  ⚠ Colección ya existe en cloud, recreando...")
        cloud.delete_collection(nombre)

    cloud.create_collection(
        collection_name=nombre,
        vectors_config={
            "texto":    VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            "resumen":  VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            "preguntas": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        }
    )
    print(f"  ✓ Colección creada en cloud")

    # Migrar en batches
    offset = None
    migrados = 0

    while True:
        resultado = local.scroll(
            collection_name=nombre,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        puntos, next_offset = resultado

        if not puntos:
            break

        # Preparar puntos para cloud
        from qdrant_client.models import PointStruct

        puntos_cloud = []
        for p in puntos:
            # Los vectores vienen como dict {texto: [...], resumen: [...], preguntas: [...]}
            vectors = {}
            if isinstance(p.vector, dict):
                vectors = p.vector
            else:
                # Fallback si vienen como lista simple
                vectors = {"texto": p.vector}

            puntos_cloud.append(PointStruct(
                id=p.id,
                vector=vectors,
                payload=p.payload,
            ))

        cloud.upsert(
            collection_name=nombre,
            points=puntos_cloud,
        )

        migrados += len(puntos)
        print(f"  Migrados: {migrados}/{total}", end="\r")

        if next_offset is None:
            break
        offset = next_offset

    print(f"\n  ✓ Migración completada: {migrados} puntos")

    # Verificación
    info_cloud = cloud.get_collection(nombre)
    print(f"  ✓ Verificación cloud: {info_cloud.points_count} puntos")


def main():
    print("\n" + "="*60)
    print("MIGRACIÓN A QDRANT CLOUD")
    print("="*60)

    if not CLOUD_URL or not CLOUD_API_KEY:
        print("\n❌ Faltan variables de entorno:")
        print("   QDRANT_CLOUD_URL=https://xxxx.cloud.qdrant.io")
        print("   QDRANT_CLOUD_API_KEY=tu_api_key")
        print("\nAñádelas al fichero .env y vuelve a ejecutar.")
        sys.exit(1)

    print(f"\n  Local:  {LOCAL_PATH}")
    print(f"  Cloud:  {CLOUD_URL}")

    # Conectar
    local = QdrantClient(path=LOCAL_PATH)
    cloud = QdrantClient(url=CLOUD_URL, api_key=CLOUD_API_KEY, timeout=60)
    print("\n  ✓ Conexiones establecidas")

    # Migrar cada colección
    for nombre in COLECCIONES:
        migrar_coleccion(local, cloud, nombre)

    print(f"\n{'='*60}")
    print("MIGRACIÓN COMPLETADA")
    print("="*60)
    print("\nActualiza retriever.py con:")
    print(f'  "QDRANT_URL": "{CLOUD_URL}"')
    print(f'  "QDRANT_API_KEY": os.getenv("QDRANT_CLOUD_API_KEY")')
    print("="*60)


if __name__ == "__main__":
    main()
