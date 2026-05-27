"""
checkpoint.py - Gestión de checkpoints por documento

Guarda chunks completos enriquecidos (no solo IDs).
Incluye campo indexado para evitar duplicados en Qdrant.
Un archivo por documento en CHECKPOINT_DIR.
"""

import json
from pathlib import Path
from typing import Optional


class Checkpoint:

    def __init__(self, fuente: str, checkpoint_dir: Path):
        self.fuente = fuente
        self.path = checkpoint_dir / f"{fuente.replace('-', '_')}.json"
        self._data: dict = {}
        self._cargar()

    def _cargar(self):
        if self.path.exists():
            with open(self.path, encoding='utf-8') as f:
                self._data = json.load(f)
            print(f"  Checkpoint {self.fuente}: {len(self._data)} chunks cargados")
        else:
            self._data = {}

    def guardar_chunk(self, chunk_id: str, keywords: list, preguntas: list, resumen: str):
        self._data[chunk_id] = {
            "keywords": keywords,
            "preguntas_sinteticas": preguntas,
            "resumen": resumen,
            "indexado": False
        }
        self._flush()

    def marcar_indexado(self, chunk_id: str):
        if chunk_id in self._data:
            self._data[chunk_id]["indexado"] = True
            self._flush()

    def marcar_batch_indexado(self, chunk_ids: list):
        for chunk_id in chunk_ids:
            if chunk_id in self._data:
                self._data[chunk_id]["indexado"] = True
        self._flush()

    def esta_indexado(self, chunk_id: str) -> bool:
        return self._data.get(chunk_id, {}).get("indexado", False)

    def cargar_enriquecimiento(self, chunk_id: str) -> Optional[dict]:
        return self._data.get(chunk_id)

    def esta_procesado(self, chunk_id: str) -> bool:
        return chunk_id in self._data

    def pendientes(self, chunks: list) -> list:
        return [c for c in chunks if not self.esta_procesado(c.id)]

    def pendientes_indexar(self, chunks: list) -> list:
        """Chunks enriquecidos pero no indexados en Qdrant."""
        return [c for c in chunks
                if self.esta_procesado(c.id) and not self.esta_indexado(c.id)]

    def aplicar_a_chunks(self, chunks: list) -> int:
        aplicados = 0
        for chunk in chunks:
            datos = self.cargar_enriquecimiento(chunk.id)
            if datos:
                chunk.keywords             = datos["keywords"]
                chunk.preguntas_sinteticas = datos["preguntas_sinteticas"]
                chunk.resumen              = datos["resumen"]
                aplicados += 1
        return aplicados

    def _flush(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False)

    def total(self) -> int:
        return len(self._data)

    def total_indexados(self) -> int:
        return sum(1 for v in self._data.values() if v.get("indexado", False))

    def __repr__(self):
        return f"Checkpoint({self.fuente}, {len(self._data)} chunks)"