# Pipeline Ingesta v2 — Diseño

*Fecha: 2026-05-08*

---

## Objetivo

Reescritura completa del pipeline de ingesta con arquitectura multihilo.
Sin parches, desde cero, bien diseñado.

---

## Estructura de directorios

```
src/ingesta2/
├── config.py        # Configuración centralizada
├── checkpoint.py    # Guarda/carga chunks completos enriquecidos
├── enricher2.py     # Enriquecimiento Groq / Cerebras (un chunk a la vez)
├── embedder.py      # BGE-M3, cargado una vez, compartido
├── indexer2.py      # Escritura en Qdrant en batch
└── pipeline.py      # Orquestador principal, hilos, colas
```

---

## Orden de ejecución

```
1. pipeline.py arranca
2. config.py carga configuración
3. embedder.py carga BGE-M3 en memoria (una sola vez)
4. checkpoint.py carga estado actual
5. Se crean las colas:
   - cola_docs: documentos pendientes
   - buffer: chunks enriquecidos esperando embed
6. Se lanzan 3 hilos:

   Hilo Groq             Hilo Cerebras          Writer
   ─────────────────     ─────────────────      ──────────────────
   coge doc de cola      coge doc de cola       espera buffer
   chunker → chunks      chunker → chunks       cuando tiene 50+:
   por cada chunk:       por cada chunk:          embed batch
     si en checkpoint      si en checkpoint       indexer.upsert()
       skip                  skip                 checkpoint.save()
     enricher(groq)        enricher(cerebras)
     → buffer              → buffer
   coge siguiente        coge siguiente

7. Cola vacía → hilos terminan → Writer vacía buffer → FIN
```

---

## Módulos

### config.py
- Lista de documentos (fuente, md, img_urls, img_freq)
- Parámetros: EMBED_BATCH_SIZE=50, WRITER_BUFFER_SIZE=50
- Modelos: GROQ_MODEL, CEREBRAS_MODEL, EMBED_MODEL
- Colección: pxom_vigo_2026_v2

### checkpoint.py
- Guarda chunk completo enriquecido (keywords, preguntas, resumen)
- Carga chunks ya procesados
- Identifica qué chunks faltan
- Un archivo por documento: checkpoints_v2/pxom.json

### enricher2.py
- Un chunk a la vez (sin batch)
- Groq O Cerebras (sin fallback automático, el pipeline decide)
- Manejo de rate limit: espera exacta según el error
- Sin dependencias del pipeline

### embedder.py
- BGE-M3 cargado una vez en __init__
- embed_batch(chunks) → vectores
- Batch size configurable

### indexer2.py
- upsert_batch(chunks, vectors) → Qdrant
- Sin lógica de negocio

### pipeline.py
- Orquestador principal
- Gestiona cola de documentos (thread-safe)
- Lanza hilo Groq, hilo Cerebras, Writer
- Writer: buffer → embedder → indexer → checkpoint

---

## Decisiones de diseño

- BGE-M3 solo lo usa el Writer, nunca los hilos de enriquecimiento
- Groq y Cerebras nunca procesan el mismo documento
- El checkpoint guarda chunks completos, no solo IDs
- Rate limit: cada enricher espera el tiempo exacto que indica el error
- Colección nueva pxom_vigo_2026_v2 (limpia, sin basura de pruebas)

---

## Estado

- [x] config.py — escrito
- [ ] checkpoint.py
- [ ] enricher2.py
- [ ] embedder.py
- [ ] indexer2.py
- [ ] pipeline.py
- [ ] test completo
