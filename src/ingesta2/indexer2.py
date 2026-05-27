"""
indexer2.py - Escritura en Qdrant en batch.

Sin lógica de negocio. Solo upsert.
Crea la colección si no existe.
"""

from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, PayloadSchemaType
)


class Indexer:

    def __init__(self, url: str, api_key: str, collection_name: str, vector_size: int = 1024):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(url=url, api_key=api_key)
        self._punto_id = 0
        print(f"✓ Indexer conectado a Qdrant")

    def crear_coleccion(self, recrear: bool = False):
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in collections:
            if recrear:
                print(f"  Eliminando colección: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            else:
                count = self.client.count(collection_name=self.collection_name)
                self._punto_id = count.count
                print(f"  Colección existente: {self.collection_name} ({count.count} puntos)")
                return

        print(f"  Creando colección: {self.collection_name}")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "texto":     VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "resumen":   VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "preguntas": VectorParams(size=self.vector_size, distance=Distance.COSINE),
            }
        )
        self._crear_indices()
        print(f"✓ Colección creada")

    def _crear_indices(self):
        indices = [
            ("ordenanza",          PayloadSchemaType.KEYWORD),
            ("ordenanza_codigo",   PayloadSchemaType.KEYWORD),
            ("articulo_numero",    PayloadSchemaType.KEYWORD),
            ("fuente",             PayloadSchemaType.KEYWORD),
            ("tiene_tablas",       PayloadSchemaType.BOOL),
            ("wiki_path",          PayloadSchemaType.KEYWORD),
            ("define_altura",      PayloadSchemaType.BOOL),
            ("define_ocupacion",   PayloadSchemaType.BOOL),
            ("define_edificabilidad", PayloadSchemaType.BOOL),
            ("define_retranqueos", PayloadSchemaType.BOOL),
            ("define_parcela_minima", PayloadSchemaType.BOOL),
            ("define_usos",        PayloadSchemaType.BOOL),
            ("ambito",             PayloadSchemaType.KEYWORD),
        ]
        for campo, tipo in indices:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=campo,
                    field_schema=tipo
                )
            except Exception:
                pass
        print("  ✓ Índices creados")

    def upsert_batch(self, chunks: list, vectors: List[Dict[str, List[float]]]):
        """Inserta chunks + vectores en Qdrant."""
        if not chunks:
            return

        points = []
        for chunk, vecs in zip(chunks, vectors):
            point = PointStruct(
                id=self._punto_id,
                vector={
                    "texto":     vecs["texto"],
                    "resumen":   vecs["resumen"],
                    "preguntas": vecs["preguntas"],
                },
                payload={
                    # Identificación
                    "chunk_id":          chunk.id,
                    "articulo_numero":   chunk.articulo_numero,
                    "parrafo_numero":    chunk.parrafo_numero,
                    # Contenido
                    "texto_original":    chunk.texto_original,
                    "texto_con_cabecera": chunk.texto_con_cabecera,
                    "cabecera":          chunk.cabecera,
                    "resumen":           chunk.resumen,
                    # Contexto
                    "titulo_articulo":   chunk.titulo_articulo,
                    "titulo_descriptivo": chunk.titulo_descriptivo,
                    "ordenanza":         chunk.ordenanza,
                    "ordenanza_codigo":  chunk.ordenanza_codigo,
                    "capitulo":          chunk.capitulo,
                    "seccion":           getattr(chunk, "seccion", ""),
                    "titulo_normativa":  getattr(chunk, "titulo_normativa", ""),
                    "ambito":            chunk.ambito,
                    # Flags
                    "define_altura":         chunk.define_altura,
                    "define_ocupacion":      chunk.define_ocupacion,
                    "define_edificabilidad": chunk.define_edificabilidad,
                    "define_retranqueos":    chunk.define_retranqueos,
                    "define_parcela_minima": chunk.define_parcela_minima,
                    "define_usos":           chunk.define_usos,
                    # Enriquecimiento
                    "keywords":              chunk.keywords,
                    "preguntas_sinteticas":  chunk.preguntas_sinteticas,
                    "referencias":           getattr(chunk, "referencias", []),
                    # Metadata
                    "longitud":              chunk.longitud,
                    "tipo_chunk":            chunk.tipo_chunk,
                    # Docling
                    "fuente":                chunk.fuente,
                    "wiki_path":             chunk.wiki_path,
                    "imagen_urls":           chunk.imagen_urls,
                    "tiene_tablas":          chunk.tiene_tablas,
                    "tablas_md":             chunk.tablas_md,
                }
            )
            points.append(point)
            self._punto_id += 1

        self.client.upsert(collection_name=self.collection_name, points=points)

    def total(self) -> int:
        return self.client.count(collection_name=self.collection_name).count