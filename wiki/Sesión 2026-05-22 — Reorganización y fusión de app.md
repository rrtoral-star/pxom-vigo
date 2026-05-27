##  Reorganización y fusión de app

- Reorganización completa de carpetas: docs/, tests/, scripts/ingesta|catastro|utils, data/cache, data/processed
- app.py (raíz, nueva UI oscura) fusionado con funcionalidad de catastro
- Entrypoint: app/streamlit_app.py (Railway apunta aquí, sin cambios)
- Página catastro existente (app/pages/) integrada con sección RAG (pendiente depuración)
- Sidebar expanded para que aparezca menú de páginas Streamlit
- Bug corregido en catastro_client.py: eliminado `from transformers import data`
- Cache path actualizado a data/cache/
- Commit: "refactor: reorganización carpetas + app fusionada + catastro con RAG (pendiente)"
- PXOM 2025 descargado (12GB) — decisión de ingesta pendiente