"""
ingestar_db.py - Ingesta de un DB específico con proveedor elegido.

Uso:
  python scripts/ingestar_db.py --fuente cte-hs --proveedor groq
  python scripts/ingestar_db.py --fuente cte-si --proveedor cerebras
"""

import os, json, sys, ctypes, argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Anti-suspensión
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

ROOT = Path(r"C:\PROY\pxom-solo")
DOCLING = ROOT / "data/raw/docling"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ingesta"))

from chunker_docling import ChunkerDocling
from enricher import ChunkEnricher
from embeddings import EmbeddingService
from indexer_docling import QdrantIndexerDocling

# Mapa de documentos
DOCUMENTOS = {
    "nhv":       {"md": "nhv_raw.md",        "urls": "nhv_imagen_urls.json",        "freq": 1},
    "cte-si":    {"md": "cte_si_raw.md",     "urls": "cte_si_imagen_urls.json",     "freq": 1},
    "cte-sua":   {"md": "cte_sua_raw.md",    "urls": "cte_sua_imagen_urls.json",    "freq": 1},
    "cte-hs":    {"md": "cte_hs_raw.md",     "urls": "cte_hs_imagen_urls.json",     "freq": 1},
    "cte-se":    {"md": "cte_se_raw.md",     "urls": "cte_se_imagen_urls.json",     "freq": 1},
    "cte-se-ae": {"md": "cte_se_ae_raw.md",  "urls": "cte_se_ae_imagen_urls.json",  "freq": 1},
    "cte-se-c":  {"md": "cte_se_c_raw.md",   "urls": "cte_se_c_imagen_urls.json",   "freq": 1},
    "cte-se-a":  {"md": "cte_se_a_raw.md",   "urls": "cte_se_a_imagen_urls.json",   "freq": 1},
    "cte-se-f":  {"md": "cte_se_f_raw.md",   "urls": "cte_se_f_imagen_urls.json",   "freq": 1},
    "cte-se-m":  {"md": "cte_se_m_raw.md",   "urls": "cte_se_m_imagen_urls.json",   "freq": 1},
    "cte-hr":    {"md": "cte_hr_raw.md",     "urls": "cte_hr_imagen_urls.json",     "freq": 1},
    "cte-he":    {"md": "cte_he_raw.md",     "urls": "cte_he_imagen_urls.json",     "freq": 1},
}


def ingestar_con_checkpoint(chunks, enricher, embedder, indexer, checkpoint_path, batch_size=15):
    checkpoint = Path(checkpoint_path)
    procesados = set()
    if checkpoint.exists():
        with open(checkpoint) as f:
            procesados = set(json.load(f))
        print(f"Checkpoint: {len(procesados)} chunks ya procesados")

    chunks_pendientes = [c for c in chunks if c.id not in procesados]
    print(f"Pendientes: {len(chunks_pendientes)} chunks")

    for i in range(0, len(chunks_pendientes), batch_size):
        batch = chunks_pendientes[i:i + batch_size]
        enricher.enriquecer_batch(batch, verbose=False)
        vectors = embedder.embed_chunks_batch(batch, verbose=False)
        indexer.indexar_batch(batch, vectors, verbose=False)
        procesados.update(c.id for c in batch)
        with open(checkpoint, 'w') as f:
            json.dump(list(procesados), f)
        print(f"Progreso: {len(procesados)}/{len(chunks)} chunks")

    print("Completado")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fuente', required=True, choices=DOCUMENTOS.keys())
    parser.add_argument('--proveedor', required=True, choices=['groq', 'cerebras'])
    args = parser.parse_args()

    doc = DOCUMENTOS[args.fuente]
    print(f"\n{'='*60}")
    print(f"INGESTA — {args.fuente.upper()} ({args.proveedor.upper()})")
    print(f"{'='*60}")

    # Cargar URLs de imágenes
    imagen_urls_map = {}
    urls_path = DOCLING / doc["urls"]
    if urls_path.exists():
        with open(urls_path) as f:
            imagen_urls_map = json.load(f)
        print(f"URLs imágenes: {len(imagen_urls_map)}")

    # Chunker
    chunker = ChunkerDocling(
        md_path=str(DOCLING / doc["md"]),
        fuente=args.fuente,
        imagen_urls_map=imagen_urls_map,
        max_frecuencia=doc["freq"]
    )
    chunks = chunker.generar_chunks()
    print(f"Chunks: {len(chunks)}")

    # Enricher con proveedor fijo sin fallback
    if args.proveedor == 'groq':
        enricher = ChunkEnricher(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            cerebras_api_key=None,
            use_llm=True
        )
    else:
        enricher = ChunkEnricher(
            groq_api_key=None,
            cerebras_api_key=os.getenv("CEREBRAS_API_KEY"),
            use_llm=True
        )

    # Embeddings
    embedder = EmbeddingService()

    # Indexer
    indexer = QdrantIndexerDocling(
        url=os.getenv("QDRANT_CLOUD_URL"),
        api_key=os.getenv("QDRANT_CLOUD_API_KEY"),
        collection_name="pxom_vigo_2026_v1"
    )
    indexer.crear_coleccion(recrear=False)

    # Checkpoint
    checkpoint_path = DOCLING / f"checkpoint_{args.fuente.replace('-', '_')}.json"
    ingestar_con_checkpoint(chunks, embedder=embedder, enricher=enricher,
                            indexer=indexer, checkpoint_path=checkpoint_path)

    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print("\nIngesta completada.")