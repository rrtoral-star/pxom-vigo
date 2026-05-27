"""
config.py - Configuración centralizada del pipeline de ingesta v2
"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(r"C:\PROY\pxom-solo")  # ← primero ROOT
load_dotenv(ROOT / ".env")          # ← luego load_dotenv

# ─── Rutas ────────────────────────────────────────────────
ROOT           = Path(r"C:\PROY\pxom-solo")
DOCLING_DIR    = ROOT / "data/raw/docling"
CHECKPOINT_DIR = DOCLING_DIR / "checkpoints_v2"
CHECKPOINT_DIR.mkdir(exist_ok=True)

# ─── Qdrant ───────────────────────────────────────────────
QDRANT_URL      = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_CLOUD_API_KEY")
COLLECTION_NAME = "pxom_vigo_2026_v2"
VECTOR_SIZE     = 1024

# ─── Modelos ──────────────────────────────────────────────
EMBED_MODEL    = "BAAI/bge-m3"
GROQ_MODEL     = "llama-3.1-8b-instant"
CEREBRAS_MODEL = "llama3.1-8b"

# ─── APIs ─────────────────────────────────────────────────
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# ─── Batch sizes ──────────────────────────────────────────
EMBED_BATCH_SIZE   = 10
WRITER_BUFFER_SIZE = 10

# ─── Documentos ───────────────────────────────────────────
DOCUMENTOS = [
    {
        "fuente":   "cte-hr",
        "md":       DOCLING_DIR / "cte_hr_raw.md",
        "img_urls": DOCLING_DIR / "cte_hr_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-he",
        "md":       DOCLING_DIR / "cte_he_raw.md",
        "img_urls": DOCLING_DIR / "cte_he_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "pxom",
        "md":       DOCLING_DIR / "pxom_raw.md",
        "img_urls": DOCLING_DIR / "pxom_imagen_urls.json",
        "img_freq": 0,
    },
    {
        "fuente":   "nhv",
        "md":       DOCLING_DIR / "nhv_raw.md",
        "img_urls": DOCLING_DIR / "nhv_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-si",
        "md":       DOCLING_DIR / "cte_si_raw.md",
        "img_urls": DOCLING_DIR / "cte_si_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-sua",
        "md":       DOCLING_DIR / "cte_sua_raw.md",
        "img_urls": DOCLING_DIR / "cte_sua_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-hs",
        "md":       DOCLING_DIR / "cte_hs_raw.md",
        "img_urls": DOCLING_DIR / "cte_hs_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se",
        "md":       DOCLING_DIR / "cte_se_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se-ae",
        "md":       DOCLING_DIR / "cte_se_ae_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_ae_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se-c",
        "md":       DOCLING_DIR / "cte_se_c_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_c_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se-a",
        "md":       DOCLING_DIR / "cte_se_a_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_a_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se-f",
        "md":       DOCLING_DIR / "cte_se_f_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_f_imagen_urls.json",
        "img_freq": 1,
    },
    {
        "fuente":   "cte-se-m",
        "md":       DOCLING_DIR / "cte_se_m_raw.md",
        "img_urls": DOCLING_DIR / "cte_se_m_imagen_urls.json",
        "img_freq": 1,
    },
]