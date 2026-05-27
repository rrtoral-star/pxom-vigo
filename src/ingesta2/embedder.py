"""
embedder.py - BGE-M3 cargado una vez, compartido entre hilos.

Solo lo usa el Writer thread.
Genera 3 vectores por chunk: texto, resumen, preguntas.
"""

from typing import List, Dict
from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.vector_size = 1024

        print(f"Cargando {model_name}...")
        try:
            self.model = SentenceTransformer(model_name, device=device)
            print(f"✓ BGE-M3 cargado en {device}")
        except Exception:
            print("⚠ Error con device, usando CPU...")
            self.model = SentenceTransformer(model_name, device="cpu")
            print("✓ BGE-M3 cargado en CPU")

    def embed_batch(self, chunks: list, batch_size: int = 50) -> List[Dict[str, List[float]]]:
        """
        Genera 3 vectores por chunk en batch.
        Devuelve lista de dicts: [{"texto": [...], "resumen": [...], "preguntas": [...]}, ...]
        """
        if not chunks:
            return []

        textos     = [c.texto_con_cabecera for c in chunks]
        resumenes  = [c.resumen if c.resumen else c.texto_original[:500] for c in chunks]
        preguntas  = [
            " | ".join(c.preguntas_sinteticas) if c.preguntas_sinteticas
            else c.cabecera + " " + " ".join(c.keywords or [])
            for c in chunks
        ]

        vecs_texto    = self.model.encode(textos,    batch_size=batch_size,
                                          normalize_embeddings=True,
                                          convert_to_numpy=True,
                                          show_progress_bar=False)

        vecs_resumen  = self.model.encode(resumenes, batch_size=batch_size,
                                          normalize_embeddings=True,
                                          convert_to_numpy=True,
                                          show_progress_bar=False)

        vecs_preguntas = self.model.encode(preguntas, batch_size=batch_size,
                                           normalize_embeddings=True,
                                           convert_to_numpy=True,
                                           show_progress_bar=False)

        return [
            {
                "texto":     vecs_texto[i].tolist(),
                "resumen":   vecs_resumen[i].tolist(),
                "preguntas": vecs_preguntas[i].tolist(),
            }
            for i in range(len(chunks))
        ]