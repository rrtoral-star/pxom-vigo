"""
retriever.py - Pipeline de búsqueda RAG v2.6
Flujo: Query → BGE-M3 embed → Qdrant multi-vector → RRF fusion → BGE-Reranker → Top-K
Soporta búsqueda en múltiples colecciones (PXOM + Habitabilidad + futuras)
"""

import os
from typing import Optional
from dataclasses import dataclass, field

from pathlib import Path
from qdrant_client import QdrantClient
from FlagEmbedding import FlagModel, FlagReranker

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
# ============================================================
# CONFIGURACIÓN
# ============================================================
IS_CLOUD = os.getenv("STREAMLIT_CLOUD", "false").lower() == "true"

CONFIG = {
    "QDRANT_URL": os.getenv("QDRANT_CLOUD_URL", "https://22a6f68b-49cd-45d3-be74-dfbffe0d7f4e.eu-west-2-0.aws.cloud.qdrant.io"),
    "QDRANT_API_KEY": os.getenv("QDRANT_CLOUD_API_KEY"),
    "EMBED_MODEL": "BAAI/bge-m3",
    "RERANKER_MODEL": "BAAI/bge-reranker-v2-m3",
    "TOP_K_QDRANT": 20,
    "TOP_K_RERANK": 5,
    "SCORE_THRESHOLD": 0.3,
    "USE_RERANKER": os.getenv("USE_RERANKER", "false").lower() == "true",  # ← AÑADIR
}

# Colección activa — todos los documentos en una sola colección
COLECCION_ACTIVA = "pxom_vigo_2026_v2"
COLECCIONES = {
    COLECCION_ACTIVA: COLECCION_ACTIVA,
}

# Fuentes disponibles para filtrar por botón
FUENTES_VALIDAS = {
    "pxom":  {"fuente": "pxom"},
    "nhv":   {"fuente": "nhv"},
    "cte":   {"fuente_prefijo": "cte"},   # fuente starts with "cte"
}


# ============================================================
# DATACLASS RESULTADO
# ============================================================
@dataclass
class ChunkResult:
    id: str
    score: float
    articulo: int
    ordenanza: str
    cabecera: str
    texto: str
    coleccion: str = ""
    fuente: str = ""
    keywords: list = field(default_factory=list)
    rrf_score: float = 0.0
    rerank_score: float = 0.0


# ============================================================
# RETRIEVER PRINCIPAL
# ============================================================
class RAGRetriever:
    ALIAS_ORDENANZAS = {
    "U1.1": "U1",
    "U1.2": "U1",
}
    def __init__(self):
        print("Inicializando RAG Retriever...")

        qdrant_url = os.getenv("QDRANT_CLOUD_URL")
        qdrant_key = os.getenv("QDRANT_CLOUD_API_KEY")

        print(f"  URL: {qdrant_url[:40] if qdrant_url else 'NO URL'}")
        print(f"  KEY: {'OK' if qdrant_key else 'VACIA'}")

        if not qdrant_url or not qdrant_key:
            raise ValueError("QDRANT_CLOUD_URL y QDRANT_CLOUD_API_KEY son requeridas")

        self.client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        print(f"  ✔ Qdrant conectado ({len(COLECCIONES)} colecciones)")

        print(f"  Cargando {CONFIG['EMBED_MODEL']}...")
        self.embedder = FlagModel(
            CONFIG["EMBED_MODEL"],
            use_fp16=False,
            query_instruction_for_retrieval="Represent this sentence for searching relevant passages: "
        )
        print("  ✔ Embedder cargado")
        self._reranker = None
        print("✔ Retriever listo\n")

    @property
    def reranker(self):
        if not CONFIG["USE_RERANKER"]:
            return None
        if self._reranker is None:
            self._reranker = FlagReranker(CONFIG["RERANKER_MODEL"], use_fp16=False)
        return self._reranker

    # ----------------------------------------------------------
    # BÚSQUEDA PRINCIPAL
    # ----------------------------------------------------------
    def buscar(
        self,
        query: str,
        top_k: int = None,
        filtros: dict = None,
        colecciones: list = None,
        verbose: bool = True
    ) -> list[ChunkResult]:
        """
        Búsqueda completa: multi-vector → RRF → reranking

        Args:
            query: Pregunta en lenguaje natural
            top_k: Número de resultados finales
            filtros: Dict con filtros opcionales, ej: {"ordenanza_codigo": "U6"}
            colecciones: Lista de claves a buscar. None = todas.
            verbose: Mostrar pasos intermedios
        """

        top_k = top_k or CONFIG["TOP_K_RERANK"]
        colecciones_buscar = colecciones or list(COLECCIONES.keys())

        if verbose:
            print(f"\n🔍 Query: '{query}'")
            print(f"   Colecciones: {colecciones_buscar}")
            print("="*60)

        # 1. Embed query (con expansión de sinónimos)
        from query_expander import expandir_query, expandir_query_debug
        debug_info = expandir_query_debug(query)
        query_expandida = debug_info["query_expandida"]

        if verbose and debug_info["expandida"]:
            print(f"   Expansión: {debug_info['terminos_detectados']}")

        query_vector = self.embedder.encode_queries([query_expandida])[0].tolist()

        # 2. Búsqueda en cada colección y cada vector
        todos_texto, todos_resumen, todos_preguntas = [], [], []

        for clave in colecciones_buscar:
            nombre_col = COLECCIONES.get(clave)
            if not nombre_col:
                print(f"  ⚠ Colección '{clave}' no encontrada")
                continue
       
            # Alias de ordenanzas (U1.1 → U1 hasta reindexar)
            if filtros and "ordenanza_codigo" in filtros:
                ordenanza = filtros["ordenanza_codigo"]
                if ordenanza in self.ALIAS_ORDENANZAS:
                    filtros["ordenanza_codigo"] = self.ALIAS_ORDENANZAS[ordenanza]

            qdrant_filter = self._build_filter(filtros)
            todos_texto     += self._search_vector(query_vector, "texto",     qdrant_filter, nombre_col, clave)
            todos_resumen   += self._search_vector(query_vector, "resumen",   qdrant_filter, nombre_col, clave)
            todos_preguntas += self._search_vector(query_vector, "preguntas", qdrant_filter, nombre_col, clave)

        if verbose:
            print(f"  Candidatos: texto={len(todos_texto)}, "
                  f"resumen={len(todos_resumen)}, "
                  f"preguntas={len(todos_preguntas)}")

        # 3. Fusión RRF
        candidatos = self._rrf_fusion(todos_texto, todos_resumen, todos_preguntas)

        if verbose:
            print(f"  Tras RRF: {len(candidatos)} candidatos únicos")

        if not candidatos:
            print("  ⚠ Sin resultados")
            return []

        # 4. Re-ranking
        resultados_finales = self._rerank(query, candidatos, top_k)

        if verbose:
            print(f"  Tras reranking: {len(resultados_finales)} resultados finales")
            print()

        return resultados_finales

    # ----------------------------------------------------------
    # BÚSQUEDA EN UN VECTOR
    # ----------------------------------------------------------
    def _search_vector(self, query_vector, vector_name, qdrant_filter, collection_name, clave):
        try:
            hits = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                using=vector_name,
                limit=CONFIG["TOP_K_QDRANT"],
                query_filter=qdrant_filter,
                with_payload=True,
                score_threshold=CONFIG["SCORE_THRESHOLD"],
            ).points
            for hit in hits:
                hit.payload["_coleccion"] = clave
            return hits
        except Exception as e:
            print(f"  ⚠ Error en '{collection_name}'/'{vector_name}': {e}")
            return []

    # ----------------------------------------------------------
    # RRF FUSION
    # ----------------------------------------------------------
    def _rrf_fusion(self, *listas_resultados, k: int = 60) -> list[ChunkResult]:
        rrf_scores = {}
        payloads = {}

        for lista in listas_resultados:
            for rank, hit in enumerate(lista):
                clave_col = hit.payload.get("_coleccion", "")
                chunk_id = f"{clave_col}::{hit.payload.get('chunk_id', str(hit.id))}"
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)
                payloads[chunk_id] = hit.payload

        resultados = []
        for chunk_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: -x[1]):
            p = payloads[chunk_id]
            clave_col = p.get("_coleccion", "")
            # Fuente real desde el payload (pxom, nhv, cte-si, etc.)
            fuente_real = p.get("fuente", clave_col)
            resultados.append(ChunkResult(
                id=chunk_id,
                score=rrf_score,
                rrf_score=rrf_score,
                articulo=p.get("articulo_numero", 0),
                ordenanza=p.get("ordenanza_codigo") or p.get("ordenanza", ""),
                cabecera=p.get("cabecera", ""),
                texto=p.get("texto_con_cabecera") or p.get("texto_original", ""),
                keywords=p.get("keywords", []),
                coleccion=clave_col,
                fuente=fuente_real,
            ))

        return resultados

    # ----------------------------------------------------------
    # RE-RANKING
    # ----------------------------------------------------------
    def _rerank(self, query: str, candidatos: list[ChunkResult], top_k: int) -> list[ChunkResult]:
        if not candidatos:
           return []

        if not CONFIG["USE_RERANKER"]:
           # Sin reranker — devolver top_k por RRF score
           for chunk in candidatos:
               chunk.rerank_score = chunk.rrf_score
           return candidatos[:top_k]

        query_rerank = (
            f"Normativa urbanística PXOM Vigo uso residencial vivienda: {query}"
            if any(t in query.lower() for t in ["residencial", "vivienda", "altura", "retranqueo", "edificabilidad", "parcela"])
            else query
        )
        pares = [[query_rerank, c.texto.split("\n\n", 1)[-1] if "\n\n" in c.texto else c.texto]
                for c in candidatos]
        scores = self.reranker.compute_score(pares, normalize=True)

        if isinstance(scores, float):
            scores = [scores]

        for chunk, score in zip(candidatos, scores):
            chunk.rerank_score = float(score)

        candidatos.sort(key=lambda x: -x.rerank_score)
        return candidatos[:top_k]

    # ----------------------------------------------------------
    # FILTROS QDRANT
    # ----------------------------------------------------------
    def _build_filter(self, filtros: Optional[dict]):
        if not filtros:
            return None

        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

        FUENTES_CTE = [
            "cte-si", "cte-sua", "cte-hs", "cte-se", "cte-se-ae",
            "cte-se-a", "cte-se-c", "cte-se-f", "cte-se-m", "cte-hr", "cte-he"
        ]

        conditions = []
        for campo, valor in filtros.items():
            if campo == "fuente_prefijo":
                conditions.append(FieldCondition(key="fuente", match=MatchAny(any=FUENTES_CTE)))
            else:
                conditions.append(FieldCondition(key=campo, match=MatchValue(value=valor)))

        return Filter(must=conditions) if conditions else None

    # ----------------------------------------------------------
    # MOSTRAR RESULTADOS
    # ----------------------------------------------------------
    def mostrar_resultados(self, resultados: list[ChunkResult], max_texto: int = 300):
        if not resultados:
            print("Sin resultados.")
            return

        for i, r in enumerate(resultados, 1):
            print(f"{'='*60}")
            print(f"#{i} | Score: {r.rerank_score:.4f} (RRF: {r.rrf_score:.4f}) [{r.fuente}]")
            print(f"    Art.{r.articulo} | {r.ordenanza} | {r.cabecera[:80]}...")
            print(f"    Keywords: {', '.join(r.keywords[:5])}")
            print(f"    Texto: {r.texto[:max_texto]}{'...' if len(r.texto) > max_texto else ''}")
        print("="*60)

    # ----------------------------------------------------------
    # FORMATEAR CONTEXTO PARA LLM
    # ----------------------------------------------------------
    def formatear_contexto(self, resultados: list[ChunkResult]) -> str:
        partes = []
        for i, r in enumerate(resultados, 1):
            partes.append(
                f"[Fuente {i} - {r.fuente}] Artículo {r.articulo} - {r.ordenanza}\n"
                f"{r.cabecera}\n"
                f"{r.texto}"
            )
        return "\n\n---\n\n".join(partes)


# ============================================================
# TEST RÁPIDO
# ============================================================
if __name__ == "__main__":
    retriever = RAGRetriever()

    # Test multi-colección
    print("\n" + "="*60)
    print("TEST MULTI-COLECCIÓN (PXOM + Habitabilidad)")
    print("="*60)
    for query in [
        "¿puedo colocar un balcón en mi fachada?",
        "altura mínima de los techos en una vivienda",
        "requisitos para aparcamiento en edificios de viviendas",
    ]:
        resultados = retriever.buscar(query, top_k=3, verbose=True)
        retriever.mostrar_resultados(resultados)
        print()

    # Test solo habitabilidad
    print("\n" + "="*60)
    print("TEST SOLO HABITABILIDAD")
    print("="*60)
    resultados = retriever.buscar(
       "superficie mínima del cuarto de baño",
       colecciones=["habitabilidad_2010", "habitabilidad_2023"],  # ← cambiado
       top_k=3,
       verbose=True
   )
    retriever.mostrar_resultados(resultados)

    # Test solo PXOM con filtro
    print("\n" + "="*60)
    print("TEST SOLO PXOM CON FILTRO U3")
    print("="*60)
    resultados = retriever.buscar(
        "parámetros edificación",
        colecciones=["pxom"],
        filtros={"ordenanza_codigo": "U3"},
        top_k=3,
        verbose=True
    )
    retriever.mostrar_resultados(resultados)
