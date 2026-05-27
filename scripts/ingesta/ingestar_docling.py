"""
ingestar_docling.py - Pipeline completo de ingesta con Docling

Flujo:
1. ChunkerDocling → chunks desde markdown
2. ChunkEnricher → keywords + resumen + preguntas (Groq)
3. EmbeddingService → BGE-M3, 3 vectores
4. QdrantIndexerDocling → indexar en Qdrant Cloud

Soporta checkpoint para reanudar si se interrumpe.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(r"C:\PROY\pxom-solo")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ingesta"))

from chunker_docling import ChunkerDocling
from enricher import ChunkEnricher
from embeddings import EmbeddingService
from indexer_docling import QdrantIndexerDocling


def ingestar_con_checkpoint(
    chunks,
    enricher,
    embedder,
    indexer,
    checkpoint_path: str,
    batch_size: int = 50,
    verbose: bool = True
):
    """Ingesta con checkpoint para poder reanudar"""
    checkpoint = Path(checkpoint_path)

    # Cargar checkpoint si existe
    procesados = set()
    if checkpoint.exists():
        with open(checkpoint) as f:
            procesados = set(json.load(f))
        print(f"✓ Checkpoint cargado: {len(procesados)} chunks ya procesados")

    chunks_pendientes = [c for c in chunks if c.id not in procesados]
    print(f"  Pendientes: {len(chunks_pendientes)} chunks")

    for i in range(0, len(chunks_pendientes), batch_size):
        batch = chunks_pendientes[i:i + batch_size]

        # Enricher
        enricher.enriquecer_batch(batch, verbose=False)

        # Embeddings
        vectors = embedder.embed_chunks_batch(batch, verbose=False)

        # Indexar
        indexer.indexar_batch(batch, vectors, verbose=False)

        # Guardar checkpoint
        procesados.update(c.id for c in batch)
        with open(checkpoint, 'w') as f:
            json.dump(list(procesados), f)

        print(f"  Progreso: {len(procesados)}/{len(chunks)} chunks")

    print(f"✓ Ingesta completada")


def ingestar(
    md_path: str,
    fuente: str,
    imagen_urls_path: str = None,
    collection_name: str = "pxom_vigo_2026_v1",
    max_frecuencia_imagen: int = 0,
    recrear_coleccion: bool = False,
    batch_size: int = 50,
    verbose: bool = True
):
    print(f"\n{'='*60}")
    print(f"INGESTA DOCLING — {fuente.upper()}")
    print(f"{'='*60}")

    # 1. Cargar mapa de imágenes si existe
    imagen_urls_map = {}
    if imagen_urls_path and Path(imagen_urls_path).exists():
        with open(imagen_urls_path, encoding='utf-8') as f:
            imagen_urls_map = json.load(f)
        print(f"✓ URLs de imágenes cargadas: {len(imagen_urls_map)}")

    # 2. Chunker
    print(f"\n[1/4] Chunking...")
    chunker = ChunkerDocling(
        md_path=md_path,
        fuente=fuente,
        imagen_urls_map=imagen_urls_map,
        max_frecuencia=max_frecuencia_imagen
    )
    chunks = chunker.generar_chunks()
    print(f"✓ Chunks generados: {len(chunks)}")

    # 3. Enricher
    print(f"\n[2/4] Inicializando enricher...")
    enricher = ChunkEnricher(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        use_llm=True
    )

    # 4. Embeddings
    print(f"\n[3/4] Cargando BGE-M3...")
    embedder = EmbeddingService()

    # 5. Indexer
    print(f"\n[4/4] Conectando a Qdrant Cloud...")
    indexer = QdrantIndexerDocling(
        url=os.getenv("QDRANT_CLOUD_URL"),
        api_key=os.getenv("QDRANT_CLOUD_API_KEY"),
        collection_name=collection_name
    )
    indexer.crear_coleccion(recrear=recrear_coleccion)

    # 6. Ingesta con checkpoint
    checkpoint_path = str(ROOT / f"data/raw/docling/checkpoint_{fuente}.json")
    print(f"\nIngesta con checkpoint: {checkpoint_path}")
    ingestar_con_checkpoint(
        chunks=chunks,
        enricher=enricher,
        embedder=embedder,
        indexer=indexer,
        checkpoint_path=checkpoint_path,
        batch_size=batch_size,
        verbose=verbose
    )

    stats = indexer.get_stats()
    print(f"\n{'='*60}")
    print(f"INGESTA COMPLETADA")
    print(f"  Colección: {stats['nombre']}")
    print(f"  Total puntos: {stats['total_puntos']}")
    print(f"{'='*60}")


if __name__ == '__main__':
    # PXOM
    ingestar(
        md_path=str(ROOT / "data/raw/docling/pxom_raw.md"),
        fuente="pxom",
        imagen_urls_path=str(ROOT / "data/raw/docling/pxom_imagen_urls.json"),
        collection_name="pxom_vigo_2026_v1",
        max_frecuencia_imagen=0,
        recrear_coleccion=True,
        batch_size=50,
        verbose=True
    )

    # NHV (descomentar cuando esté listo)
    # ingestar(
    #     md_path=str(ROOT / "data/raw/docling/nhv_raw.md"),
    #     fuente="nhv",
    #     imagen_urls_path=None,
    #     collection_name="pxom_vigo_2026_v1",
    #     max_frecuencia_imagen=3,
    #     recrear_coleccion=False,
    #     batch_size=50,
    #     verbose=True
    # )