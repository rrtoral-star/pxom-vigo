"""Test rápido del pipeline con 5 chunks"""
import os, json, sys
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

if __name__ == '__main__':

    # 1. Chunker - solo 5 chunks
    print("[1/4] Chunking...")
    chunker = ChunkerDocling(
        md_path=str(ROOT / "data/raw/docling/pxom_raw.md"),
        fuente="pxom"
    )
    chunks = chunker.generar_chunks()[:5]
    print(f"✓ Usando {len(chunks)} chunks para test")

    # 2. Enricher
    print("[2/4] Enriqueciendo...")
    enricher = ChunkEnricher(groq_api_key=os.getenv("GROQ_API_KEY"), use_llm=True)
    enricher.enriquecer_batch(chunks, verbose=True)

    # 3. Embeddings
    print("[3/4] Embeddings...")
    embedder = EmbeddingService()
    vectors_list = embedder.embed_chunks_batch(chunks, verbose=True)

    # 4. Indexar en memoria (test sin tocar Qdrant Cloud)
    print("[4/4] Indexando en memoria...")
    indexer = QdrantIndexerDocling(collection_name="test_pipeline")
    indexer.crear_coleccion(recrear=True)
    indexer.indexar_batch(chunks, vectors_list, verbose=True)

    stats = indexer.get_stats()
    print(f"\n✓ Test completado: {stats['total_puntos']} puntos indexados")