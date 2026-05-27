"""
ingestar_todo.py - Ingesta completa: NHV + 11 DB del CTE
Con protección anti-suspensión para portátil.
"""

import os, json, sys, ctypes
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Evitar suspensión del sistema
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
print("✓ Modo anti-suspensión activado")

ROOT = Path(r"C:\PROY\pxom-solo")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ingesta"))

from chunker_docling import ChunkerDocling
from enricher import ChunkEnricher
from embeddings import EmbeddingService
from indexer_docling import QdrantIndexerDocling


def ingestar_con_checkpoint(chunks, enricher, embedder, indexer, checkpoint_path, batch_size=50):
    checkpoint = Path(checkpoint_path)
    procesados = set()
    if checkpoint.exists():
        with open(checkpoint) as f:
            procesados = set(json.load(f))
        print(f"✓ Checkpoint: {len(procesados)} chunks ya procesados")

    chunks_pendientes = [c for c in chunks if c.id not in procesados]
    print(f"  Pendientes: {len(chunks_pendientes)} chunks")

    for i in range(0, len(chunks_pendientes), batch_size):
        batch = chunks_pendientes[i:i + batch_size]
        enricher.enriquecer_batch(batch, verbose=False)
        vectors = embedder.embed_chunks_batch(batch, verbose=False)
        indexer.indexar_batch(batch, vectors, verbose=False)
        procesados.update(c.id for c in batch)
        with open(checkpoint, 'w') as f:
            json.dump(list(procesados), f)
        print(f"  Progreso: {len(procesados)}/{len(chunks)} chunks")

    print(f"✓ Completado")


def ingestar(md_path, fuente, collection_name="pxom_vigo_2026_v1",
             imagen_urls_path=None, max_frecuencia_imagen=0,
             recrear_coleccion=False, batch_size=50):

    print(f"\n{'='*60}")
    print(f"INGESTA — {fuente.upper()}")
    print(f"{'='*60}")

    imagen_urls_map = {}
    if imagen_urls_path and Path(imagen_urls_path).exists():
        with open(imagen_urls_path, encoding='utf-8') as f:
            imagen_urls_map = json.load(f)

    chunker = ChunkerDocling(
        md_path=md_path,
        fuente=fuente,
        imagen_urls_map=imagen_urls_map,
        max_frecuencia=max_frecuencia_imagen
    )
    chunks = chunker.generar_chunks()
    print(f"✓ Chunks: {len(chunks)}")

    enricher = ChunkEnricher(groq_api_key=os.getenv("GROQ_API_KEY"), use_llm=True)
    embedder = EmbeddingService()

    indexer = QdrantIndexerDocling(
        url=os.getenv("QDRANT_CLOUD_URL"),
        api_key=os.getenv("QDRANT_CLOUD_API_KEY"),
        collection_name=collection_name
    )
    indexer.crear_coleccion(recrear=recrear_coleccion)

    checkpoint_path = ROOT / f"data/raw/docling/checkpoint_{fuente.replace('-', '_')}.json"
    ingestar_con_checkpoint(chunks, enricher, embedder, indexer, checkpoint_path, batch_size)

    stats = indexer.get_stats()
    print(f"✓ Total en Qdrant: {stats['total_puntos']} puntos")


if __name__ == '__main__':

    DOCLING = ROOT / "data/raw/docling"
    COL = "pxom_vigo_2026_v1"

    documentos = [
        # NHV
 
        {"md_path": DOCLING / "nhv_raw.md", "fuente": "nhv",
         "imagen_urls_path": str(DOCLING / "nhv_imagen_urls.json"),
         "max_frecuencia_imagen": 1},
        # CTE por DB
        {"md_path": DOCLING / "cte_si_raw.md",     "fuente": "cte-si"},
        {"md_path": DOCLING / "cte_sua_raw.md",    "fuente": "cte-sua"},
        {"md_path": DOCLING / "cte_hs_raw.md",     "fuente": "cte-hs"},
        {"md_path": DOCLING / "cte_se_raw.md",     "fuente": "cte-se"},
        {"md_path": DOCLING / "cte_se_ae_raw.md",  "fuente": "cte-se-ae"},
        {"md_path": DOCLING / "cte_se_c_raw.md",   "fuente": "cte-se-c"},
        {"md_path": DOCLING / "cte_se_a_raw.md",   "fuente": "cte-se-a"},
        {"md_path": DOCLING / "cte_se_f_raw.md",   "fuente": "cte-se-f"},
        {"md_path": DOCLING / "cte_se_m_raw.md",   "fuente": "cte-se-m"},
        {"md_path": DOCLING / "cte_hr_raw.md",     "fuente": "cte-hr"},
        {"md_path": DOCLING / "cte_he_raw.md",     "fuente": "cte-he"},
    ]

    for doc in documentos:
        ingestar(
            md_path=str(doc["md_path"]),
            fuente=doc["fuente"],
            collection_name=COL,
            imagen_urls_path=doc.get("imagen_urls_path"),
            max_frecuencia_imagen=doc.get("max_frecuencia_imagen", 0),
            recrear_coleccion=False,
            batch_size=50
        )

    # Restaurar comportamiento normal
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print("\n✅ Ingesta completa. Anti-suspensión desactivado.")