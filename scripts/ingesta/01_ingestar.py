"""
Script de Ingesta PXOM v2.5

Pipeline completo:
1. Cargar JSON del PXOM
2. Generar chunks con cabecera estructural
3. Enriquecer con keywords, preguntas, resumen (Groq)
4. Generar embeddings multi-vector (BGE-M3)
5. Indexar en Qdrant

Uso:
    python 01_ingestar.py
    python 01_ingestar.py --sin-llm  # Sin Groq, solo keywords locales
    python 01_ingestar.py --test     # Solo 10 chunks para probar
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingesta.chunker import ChunkerPXOM
from ingesta.enricher import ChunkEnricher
from ingesta.embeddings import EmbeddingService
from ingesta.indexer import QdrantIndexer

from dotenv import load_dotenv
load_dotenv()

# === CONFIGURACIÓN ===
CONFIG = {
    # Paths
    "PXOM_JSON": "C:/PROY/pxom-solo/data/cleaned/normativa_urbanistica_pxom_2025.json",
    "QDRANT_PATH": "C:/PROY/pxom-solo/data/rag/qdrant_v2",
    
    # Qdrant
    "COLLECTION_NAME": "pxom_vigo_2025_v2",
    "VECTOR_SIZE": 1024,
    
    # Embeddings
    "EMBEDDING_DEVICE": "cpu",  # Cambiar de "cuda" a "cpu"
    "BATCH_SIZE_EMBED": 16,
    
    # Indexación
    "BATCH_SIZE_INDEX": 100,
}


def main(args):
    """Pipeline principal de ingesta"""
    
    print("\n" + "="*70)
    print("INGESTA PXOM v2.5")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # === 1. CHUNKING ===
    print("\n[1/5] GENERANDO CHUNKS...")
    print("-"*50)
    
    chunker = ChunkerPXOM(CONFIG["PXOM_JSON"])
    chunks = chunker.generar_chunks()
    
    # Limitar para test
    if args.test:
        chunks = chunks[:10]
        print(f"  ⚠ Modo test: limitado a {len(chunks)} chunks")
    
    # === 2. ENRIQUECIMIENTO ===
    print("\n[2/5] ENRIQUECIENDO CHUNKS...")
    print("-"*50)
    
    enricher = ChunkEnricher(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        use_llm=not args.sin_llm
    )
    
    enricher.enriquecer_batch(chunks, verbose=True, batch_size=20)
    
    # === 3. EMBEDDINGS ===
    print("\n[3/5] GENERANDO EMBEDDINGS...")
    print("-"*50)
    
    embedding_service = EmbeddingService(
        device=CONFIG["EMBEDDING_DEVICE"]
    )
    
    vectors_list = embedding_service.embed_chunks_batch(
        chunks,
        batch_size=CONFIG["BATCH_SIZE_EMBED"],
        verbose=True
    )
    
    # === 4. INDEXACIÓN ===
    print("\n[4/5] INDEXANDO EN QDRANT...")
    print("-"*50)
    
    indexer = QdrantIndexer(
        path=CONFIG["QDRANT_PATH"],
        collection_name=CONFIG["COLLECTION_NAME"],
        vector_size=CONFIG["VECTOR_SIZE"]
    )
    
    indexer.crear_coleccion(recrear=True)
    
    indexer.indexar_batch(
        chunks,
        vectors_list,
        batch_size=CONFIG["BATCH_SIZE_INDEX"],
        verbose=True
    )
    
    # === 5. VERIFICACIÓN ===
    print("\n[5/5] VERIFICACIÓN...")
    print("-"*50)
    
    stats = indexer.get_stats()
    
    print(f"\n{'='*70}")
    print("INGESTA COMPLETADA")
    print("="*70)
    print(f"  Colección: {stats['nombre']}")
    print(f"  Total chunks: {stats['total_puntos']}")
    print(f"  Vectores por chunk: {len(stats['vectores'])} ({', '.join(stats['vectores'])})")
    print(f"  Dimensiones: {stats['vector_size']}")
    print(f"  Path: {CONFIG['QDRANT_PATH']}")
    print("="*70)
    
    # Mostrar ejemplo
    print("\nEJEMPLO DE CHUNK INDEXADO:")
    print("-"*50)
    
    result = indexer.client.scroll(
        collection_name=CONFIG["COLLECTION_NAME"],
        limit=1,
        with_payload=True,
        with_vectors=False
    )
    
    if result[0]:
        payload = result[0][0].payload
        print(f"  ID: {payload['chunk_id']}")
        print(f"  Artículo: {payload['articulo_numero']}")
        print(f"  Ordenanza: {payload['ordenanza_codigo'] or payload['ordenanza']}")
        print(f"  Cabecera: {payload['cabecera'][:80]}...")
        print(f"  Keywords: {payload['keywords'][:5]}")
        if payload.get('preguntas_sinteticas'):
            print(f"  Preguntas: {payload['preguntas_sinteticas'][0][:60]}...")
    
    indexer.close()
    
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta PXOM v2.5")
    parser.add_argument("--sin-llm", action="store_true", help="Sin Groq (solo keywords locales)")
    parser.add_argument("--test", action="store_true", help="Modo test (10 chunks)")
    
    args = parser.parse_args()
    
    sys.exit(main(args))
