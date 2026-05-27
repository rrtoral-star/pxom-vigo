"""
Configuración RAG PXOM Vigo v2.5
"""
import os
from pathlib import Path
from dataclasses import dataclass

# Base del proyecto
BASE_DIR = Path(__file__).parent.parent

@dataclass
class Config:
    """Configuración centralizada"""
    
    # === PATHS ===
    DATA_DIR: Path = BASE_DIR / "data"
    PXOM_JSON: Path = DATA_DIR / "cleaned" / "normativa_urbanistica_pxom_2025.json"
    QDRANT_PATH: Path = DATA_DIR / "rag" / "qdrant_v2"
    CACHE_DIR: Path = DATA_DIR / "cache"
    
    # === QDRANT ===
    COLLECTION_NAME: str = "pxom_vigo_2026_v2"
    VECTOR_SIZE: int = 1024  # BGE-M3
    
    # === EMBEDDINGS ===
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    NORMALIZE_EMBEDDINGS: bool = True
    RETRIEVAL_PREFIX: str = "Represent this sentence for searching relevant passages: "
    
    # === BÚSQUEDA ===
    TOP_K_INICIAL: int = 30
    TOP_K_RERANK: int = 10
    TOP_K_FINAL: int = 5
    MIN_SCORE: float = 0.5
    
    # === LLM (Groq) ===
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    # === SUPABASE ===
    TABLA_ZONAS: str = "zonas_pxom"
    
    def __post_init__(self):
        """Crear directorios si no existen"""
        self.QDRANT_PATH.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)


# Singleton
config = Config()


# === API KEYS (desde .env o variables de entorno) ===
def get_groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")

def get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "")

def get_supabase_key() -> str:
    return os.getenv("SUPABASE_KEY", "")
