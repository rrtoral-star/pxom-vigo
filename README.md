# RAG PXOM Vigo v2.5

Sistema RAG experto para normativa urbanística del Plan Xeral de Ordenación Municipal de Vigo.

## Características v2.5

- **Multi-vector**: 3 embeddings por chunk (texto, resumen, preguntas)
- **BGE-M3**: Embeddings normalizados con prefijo de retrieval
- **Enriquecimiento**: Keywords (TF-IDF) + preguntas sintéticas (Groq)
- **Filtros dinámicos**: Por ordenanza, conceptos, ámbito
- **Cabecera estructural**: Contexto prepended para mejor embedding

## Estructura

```
v2.5/
├── src/
│   ├── config.py              # Configuración
│   └── ingesta/
│       ├── chunker.py         # Genera chunks del PXOM
│       ├── enricher.py        # Keywords + preguntas (Groq)
│       ├── embeddings.py      # BGE-M3 multi-vector
│       └── indexer.py         # Indexa en Qdrant
│
├── scripts/
│   └── 01_ingestar.py         # Script de ingesta
│
└── requirements_v2.5.txt
```

## Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements_v2.5.txt

# 2. Descargar modelo spaCy
python -m spacy download es_core_news_md

# 3. Configurar API keys
export GROQ_API_KEY="tu_key"
# o crear archivo .env
```

## Uso

### Ingesta completa

```bash
cd C:\PROY\pxom-solo

# Ingesta completa con Groq
python scripts/v2.5/01_ingestar.py

# Sin LLM (solo keywords locales, más rápido)
python scripts/v2.5/01_ingestar.py --sin-llm

# Test con 10 chunks
python scripts/v2.5/01_ingestar.py --test
```

### Verificar colección

```python
from qdrant_client import QdrantClient

client = QdrantClient(path="data/rag/qdrant_v2")

# Ver estadísticas
print(client.get_collection("pxom_vigo_2025_v2"))
print(client.count("pxom_vigo_2025_v2"))

# Ver un chunk
result = client.scroll("pxom_vigo_2025_v2", limit=1, with_payload=True)
print(result[0][0].payload)
```

## Estructura de Chunk

Cada chunk indexado tiene:

```python
{
    # Identificación
    "chunk_id": "abc123",
    "articulo_numero": "145",
    "parrafo_numero": 1,
    
    # Contenido
    "texto_original": "...",
    "texto_con_cabecera": "ORDENANZA U3 | Art. 145 | ...",
    "cabecera": "ORDENANZA U3 | Art. 145 | [altura, ocupación]",
    "resumen": "Define altura máxima de 7m...",
    
    # Contexto
    "ordenanza": "U3",
    "ordenanza_codigo": "U3.2",
    "capitulo": "...",
    "ambito": "urbano_consolidado",
    
    # Flags semánticos
    "define_altura": true,
    "define_ocupacion": true,
    "define_edificabilidad": false,
    ...
    
    # Enriquecimiento
    "keywords": ["altura", "7 metros", "plantas"],
    "preguntas_sinteticas": ["¿Cuál es la altura máxima en U3?", ...]
}
```

## Próximos pasos

1. ✅ Ingesta multi-vector
2. ⬜ Pipeline de búsqueda con filtros
3. ⬜ Re-ranking con BGE-Reranker
4. ⬜ Integración con informe urbanístico
5. ⬜ Frontend con mapa interactivo

## Configuración

Editar `scripts/01_ingestar.py`:

```python
CONFIG = {
    "PXOM_JSON": "ruta/al/json",
    "QDRANT_PATH": "ruta/qdrant",
    "EMBEDDING_DEVICE": "cuda",  # o "cpu"
    ...
}
```
