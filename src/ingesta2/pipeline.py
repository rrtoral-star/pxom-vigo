"""
pipeline.py - Orquestador principal del pipeline de ingesta v2.

Arquitectura:
- Fase 1 (main): Pre-carga chunks enriquecidos pero NO indexados al buffer
- Writer arranca solo y vacía el buffer del checkpoint
- Cuando el buffer está vacío, arrancan los enrichers
- Fase 2 (hilos): Groq y Cerebras enriquecen pendientes en paralelo

BGE-M3 se carga una vez y solo lo usa el Writer.
Sincronización con evento para evitar competencia CPU.
"""

import sys
import json
import ctypes
import threading
import queue
import traceback
from pathlib import Path

ES_CONTINUOUS      = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

ROOT = Path(r"C:\PROY\pxom-solo")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ingesta2"))

from config import (
    DOCUMENTOS, CHECKPOINT_DIR,
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, VECTOR_SIZE,
    EMBED_MODEL, EMBED_BATCH_SIZE, WRITER_BUFFER_SIZE,
    GROQ_MODEL, CEREBRAS_MODEL,
    GROQ_API_KEY, CEREBRAS_API_KEY,
)
from chunker_docling import ChunkerDocling
from checkpoint import Checkpoint
from enricher2 import Enricher
from embedder import Embedder
from indexer2 import Indexer

_FIN = None


def precargar_checkpoints(documentos: list, buffer: queue.Queue) -> dict:
    """
    Fase 1 (main thread):
    Carga chunks enriquecidos pero NO indexados al buffer.
    Devuelve docs con chunks pendientes de enriquecer.
    """
    print("\n[Fase 1] Pre-cargando checkpoints...")
    docs_pendientes = {}
    total_precargados = 0

    for doc in documentos:
        fuente = doc["fuente"]

        imagen_urls_map = {}
        if doc.get("img_urls") and Path(doc["img_urls"]).exists():
            with open(doc["img_urls"], encoding="utf-8") as f:
                imagen_urls_map = json.load(f)

        chunker = ChunkerDocling(
            md_path=str(doc["md"]),
            fuente=fuente,
            imagen_urls_map=imagen_urls_map,
            max_frecuencia=doc.get("img_freq", 0)
        )
        chunks = chunker.generar_chunks()
        ckpt = Checkpoint(fuente, CHECKPOINT_DIR)
        ckpt.aplicar_a_chunks(chunks)

        # Solo chunks enriquecidos pero NO indexados
        a_indexar = ckpt.pendientes_indexar(chunks)
        for chunk in a_indexar:
            buffer.put((chunk, ckpt))
        total_precargados += len(a_indexar)

        pendientes = ckpt.pendientes(chunks)
        print(f"  {fuente}: {len(a_indexar)} a indexar, {len(pendientes)} a enriquecer")

        if pendientes:
            docs_pendientes[fuente] = {
                "doc": doc,
                "chunks": chunks,
                "pendientes": pendientes,
                "ckpt": ckpt
            }

    print(f"[Fase 1] Total a indexar: {total_precargados} chunks\n")
    return docs_pendientes


def hilo_enricher(nombre: str, enricher: Enricher,
                  cola_docs: queue.Queue, buffer: queue.Queue):
    try:
        print(f"[{nombre}] Arrancando...")

        while True:
            item = cola_docs.get()
            if item is _FIN:
                cola_docs.put(_FIN)
                break

            fuente = item["doc"]["fuente"]
            chunks = item["chunks"]
            pendientes = item["pendientes"]
            ckpt = item["ckpt"]

            print(f"[{nombre}] Enriqueciendo {fuente} ({len(pendientes)} pendientes)...")

            limite_diario = False
            for chunk in pendientes:
                try:
                    resultado = enricher.enriquecer_chunk(chunk)
                except RuntimeError as e:
                    if str(e) == "LIMITE_DIARIO":
                        print(f"[{nombre}] Límite diario alcanzado, terminando hilo")
                        limite_diario = True
                        break
                    raise

                chunk.keywords             = resultado["keywords"]
                chunk.preguntas_sinteticas = resultado["preguntas_sinteticas"]
                chunk.resumen              = resultado["resumen"]
                ckpt.guardar_chunk(chunk.id, chunk.keywords,
                                   chunk.preguntas_sinteticas, chunk.resumen)
                buffer.put((chunk, ckpt))

            if limite_diario:
                break

            print(f"[{nombre}] {fuente} completado")
            cola_docs.task_done()

    except Exception as e:
        print(f"[{nombre}] ERROR FATAL: {e}")
        traceback.print_exc()

    finally:
        print(f"[{nombre}] Terminado")
        buffer.put(_FIN)


def hilo_writer(buffer: queue.Queue, embedder: Embedder,
                indexer: Indexer, n_hilos_enricher: int,
                checkpoint_vaciado: threading.Event):
    try:
        print("[Writer] Arrancando...")
        fins_recibidos = 0
        acumulados = []
        ckpts_acumulados = []
        total_indexados = 0
        checkpoint_procesado = False

        while True:
            try:
                item = buffer.get(timeout=1)
            except queue.Empty:
                # Procesar lo que quede acumulado
                if acumulados:
                    _procesar_batch(acumulados, ckpts_acumulados, embedder, indexer)
                    total_indexados += len(acumulados)
                    print(f"[Writer] Indexados: {total_indexados}")
                    acumulados = []
                    ckpts_acumulados = []

                # Señalar que el checkpoint está vaciado
                if not checkpoint_procesado and not checkpoint_vaciado.is_set():
                    checkpoint_vaciado.set()
                    checkpoint_procesado = True
                    print(f"[Writer] Checkpoint vaciado ({total_indexados} indexados). Enrichers pueden arrancar.")

                continue

            if item is _FIN:
                fins_recibidos += 1
                if fins_recibidos >= n_hilos_enricher:
                    if acumulados:
                        _procesar_batch(acumulados, ckpts_acumulados, embedder, indexer)
                        total_indexados += len(acumulados)
                    print(f"[Writer] Terminado. Total indexados: {total_indexados}")
                    break
                continue

            chunk, ckpt = item
            acumulados.append(chunk)
            ckpts_acumulados.append(ckpt)

            if len(acumulados) >= WRITER_BUFFER_SIZE:
                _procesar_batch(acumulados, ckpts_acumulados, embedder, indexer)
                total_indexados += len(acumulados)
                print(f"[Writer] Indexados: {total_indexados}")
                acumulados = []
                ckpts_acumulados = []

    except Exception as e:
        print(f"[Writer] ERROR FATAL: {e}")
        traceback.print_exc()
        # Señalar aunque haya error para no bloquear los enrichers
        if not checkpoint_vaciado.is_set():
            checkpoint_vaciado.set()


def _procesar_batch(chunks: list, ckpts: list, embedder: Embedder, indexer: Indexer):
    try:
        vectors = embedder.embed_batch(chunks, batch_size=EMBED_BATCH_SIZE)
        indexer.upsert_batch(chunks, vectors)
        for chunk, ckpt in zip(chunks, ckpts):
            ckpt.marcar_indexado(chunk.id)
    except Exception as e:
        print(f"[Writer] ERROR en batch: {e}")
        traceback.print_exc()


def main():
    print("=" * 60)
    print("PIPELINE INGESTA v2")
    print("=" * 60)

    # Cargar BGE-M3
    embedder = Embedder(model_name=EMBED_MODEL)

    # Conectar Qdrant
    indexer = Indexer(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
        vector_size=VECTOR_SIZE
    )
    indexer.crear_coleccion(recrear=False)

    # Buffer compartido
    buffer = queue.Queue()

    # FASE 1: Pre-cargar checkpoints al buffer
    docs_pendientes = precargar_checkpoints(DOCUMENTOS, buffer)

    # Evento de sincronización
    checkpoint_vaciado = threading.Event()

    # Arrancar Writer solo primero
    t_writer = threading.Thread(
        target=hilo_writer,
        args=(buffer, embedder, indexer, 2, checkpoint_vaciado)
    )
    t_writer.start()

    # Esperar a que el Writer vacíe el checkpoint
    print("[Main] Esperando a que el Writer vacíe el checkpoint...")
    checkpoint_vaciado.wait()
    print("[Main] Arrancando enrichers...")

    # Arrancar enrichers
    enricher_groq = Enricher(
        proveedor="groq",
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY
    )
    enricher_cerebras = Enricher(
        proveedor="cerebras",
        model=CEREBRAS_MODEL,
        api_key=CEREBRAS_API_KEY
    )

    cola_docs = queue.Queue()
    for fuente, item in docs_pendientes.items():
        cola_docs.put(item)
    cola_docs.put(_FIN)

    t_groq = threading.Thread(
        target=hilo_enricher,
        args=("Groq", enricher_groq, cola_docs, buffer)
    )
    t_cerebras = threading.Thread(
        target=hilo_enricher,
        args=("Cerebras", enricher_cerebras, cola_docs, buffer)
    )

    t_groq.start()
    t_cerebras.start()

    t_groq.join()
    t_cerebras.join()
    t_writer.join()

    print("\n" + "=" * 60)
    print(f"INGESTA COMPLETADA")
    print(f"Total en Qdrant: {indexer.total()} puntos")
    print("=" * 60)

    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


if __name__ == "__main__":
    main()