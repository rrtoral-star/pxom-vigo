# PXOM-Vigo — Backlog
*Última actualización: 2026-04-27*

---

## Estado actual

| Componente | Estado |
|---|---|
| Chat RAG en producción (Railway) | ✅ |
| Qdrant Cloud (1285 chunks) | ✅ |
| BGE-M3 + Reranker | ✅ |
| Módulo Catastro + PostGIS | ✅ |
| Alias U1.1 → U1 en retriever | ✅ |
| Temperatura 0.1 + modelo actualizado | ✅ |
| Prints DEBUG eliminados | ✅ |
| RAM Railway 4GB | ✅ (pendiente verificar) |
| Docker: postgres + qdrant + n8n + docling | ✅ |

---

## Deuda técnica pendiente

- [ ] Verificar RAM Railway 4GB en dashboard
- [ ] Reindexar U1.1 correctamente en Qdrant (al hacer Bloque 4)
- [ ] Edge cases catastro: tipos de vía ESTRADA, CAMIÑO, etc.
- [ ] Formulario búsqueda avanzada (portal + piso + letra)

---

## Bloque 3 — Calculadora de viviendas

- [ ] Extraer zonas PXOM desde Qdrant → poblar pxom_vigo_params.json
- [ ] Decidir integración Streamlit:
  - Opción A: tab independiente
  - Opción B: sección automática tras consulta catastro

---

## Bloque 4 — Docling + Wiki + Reindexado

*Decisiones tomadas 2026-04-27:*
- Docling corre en Docker (puerto 5001), no en el venv
- Sustituye pdf_extractor.py como parser
- La IA (Qwen local o Groq) genera el contenido del wiki, no solo lo extrae
- Artículos con flags define_altura/ocupacion/edificabilidad → requieren validación técnica antes de publicar
- Tablas e imágenes quedan asociadas al artículo correspondiente via Docling

*Estructura de directorios a añadir:*
```
wiki/
  pxom/
  nhv/
data/raw/docling/
```

### Fase 1 — Docling operativo
- [x] Añadir docling al docker-compose.yml
- [ ] Crear carpetas wiki/ y data/raw/docling/
- [ ] Probar Docling con un artículo del PXOM (POST a localhost:5001)
- [ ] Verificar extracción de tablas e imágenes

### Fase 2 — Pipeline nuevo
- [ ] Sustituir pdf_extractor.py por cliente Docling
- [ ] Adaptar chunker.py para leer markdown en vez de JSON
- [ ] Añadir paso: chunk enriquecido → guardar wiki/pxom/U6-art45.md
- [ ] Asociar imagen_url[] y tablas[] al payload de cada chunk en Qdrant
- [ ] Subir imágenes a Supabase Storage

### Fase 3 — Wiki generado por IA
- [ ] Qwen (local) o Groq genera interpretación de cada artículo
- [ ] Marcar artículos numéricos como "requiere validación técnica"
- [ ] Script de lint: detectar artículos sin validar, contradicciones

### Fase 4 — Streamlit tipo wiki
- [ ] Vista artículo: texto oficial + tablas + imágenes
- [ ] Navegación: parcela → ordenanza → artículos aplicables
- [ ] Chat RAG como capa de consulta libre encima del wiki
- [ ] Renderizar anotaciones de técnicos junto al artículo

---

## Bloque 5 — Anotaciones de técnicos municipales

*Redefinido 2026-04-27: técnicos municipales como fuente de verdad.*

- [ ] Crear tabla en Supabase:
  ```sql
  anotaciones_articulos (
    id, ordenanza_codigo, articulo_numero,
    texto_anotacion, autor_id, fecha,
    validada bool,
    tipo: interpretacion | excepcion | jurisprudencia
  )
  ```
- [ ] Panel técnico municipal en Streamlit: añadir / editar anotaciones
- [ ] Badge "Interpretación oficial" visible en la vista artículo
- [ ] RAG incorpora anotaciones validadas como contexto prioritario

---

## Bloque 6 — Mapa interactivo

- [ ] Folium + streamlit-folium sobre OSM
- [ ] Capa WMS Catastro
- [ ] Capa zonas_pxom desde Supabase → GeoJSON
- [ ] Click en parcela → preview datos + zona PXOM
- [ ] Botón → informe RAG completo

---

## Setup local confirmado

| Herramienta | Uso |
|---|---|
| VS Code + Continue | Asistente de código (Qwen 2.5 Coder 7B via Ollama) |
| Ollama | Modelos locales para desarrollo |
| Docker | postgres + qdrant + n8n + docling |
| Railway | Deploy producción Streamlit |
| Qdrant Cloud | Vectores en producción |
| Supabase | PostGIS + Storage |
| Groq API | Enricher + RAG en producción |

---

## Orden de prioridad

1. Verificar Docling funcionando (curl health + prueba PDF)
2. Bloque 4 Fase 1 y 2: pipeline nuevo con Docling
3. Bloque 4 Fase 3: wiki generado por IA
4. Bloque 5: anotaciones técnicos municipales
5. Bloque 4 Fase 4: Streamlit tipo wiki
6. Bloque 3: calculadora viviendas
7. Bloque 6: mapa interactivo
