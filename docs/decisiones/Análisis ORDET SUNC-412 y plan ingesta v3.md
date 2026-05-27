## 2026-05-23 — Análisis ORDET SUNC-412 y plan ingesta v3

### Decisiones
- Colección nueva `pxom_vigo_2026_v3` en paralelo (v2 sigue activa en producción)
- 11.ORDET tiene un solo sector (SUNC-412). El grueso de normativa está en 07.NU
- ORDET y 07.NU son complementarios: específico vs general

### Documentos a indexar por sector ORDET
- `04.NU` — Normativa urbanística (7 págs, texto nativo, 1 tabla de edificabilidad)
- `01.MX/01INF` — Memoria informativa (42 págs)
- `03.PORD/05.1-05.2SECC` — Diagramas sección → pipeline Vision

### Descartados
- 02.PINF (cartografía), 06.EE, 07.AAE, 05.CAT

### Ajustes chunker pendientes
- Añadir `PATRON_SECCION_ORDET` para secciones numeradas tipo "1. NORMAS XERAIS"
- Añadir campos `sector` y `sector_nombre` al payload ChunkDocling
- Fix patrón IMAGEN para variantes con espacio: `\[IMAGEN[_\s]\d+\]`

### Próximo paso
- Correr `scripts/ingesta/docling_ordet.py` en local
- Pegar primeras 100 líneas del markdown para verificar estructura y tabla