## Wiki PXOM-Solo — Sesión 2026-05-11

### Generador wiki (local)
- Script: `src/wiki/generate_wiki.py`
- Motor: Qwen3:14b via Ollama (local)
- 880 artículos en 13 fuentes — dry-run OK
- Frontmatter: tipo_doc, subtipo, documento, ordenanza, capitulo, tags
- Prompts adaptados por tipo: PXOM / NHV / CTE
- Wikilinks automáticos: Art. 45 → [[art-45]]
- Estructura carpetas: wiki/pxom/, wiki/nhv/, wiki/cte/{si,sua,hs,...}/

### Arquitectura Oracle
- Generación: local (Qwen) → git push → Oracle git pull
- Frontend: Streamlit (piloto) — navegar wiki + RAG query
- RAG queries: Groq/Cerebras → Qdrant Cloud (pxom_vigo_2026_v2)
- Notas usuarios avanzados: escritas en Oracle, ingestadas con BGE-M3
- Sync notas: Oracle git push → local git pull → reconstruir wikilinks → git push → Oracle pull
- Wikilink rebuilder: corre en local, no en Oracle

### Pendiente
- [ ] Lanzar generate_wiki.py --fuente pxom (validar primer .md)
- [ ] Setup Oracle: git, venv, estructura carpetas
- [ ] Streamlit frontend (próxima sesión)
- [ ] Notes pipeline BGE-M3 (Oracle)
- [ ] Wikilink rebuilder
- [ ] Actualizar retriever: pxom_vigo_2025_v2 → pxom_vigo_2026_v2