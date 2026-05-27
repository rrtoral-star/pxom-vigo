## Docling v2 — cambios de API

- `PipelineOptions` → ahora es `PdfPipelineOptions`
- `do_ocr=False` necesario para PDFs nativos (evita descarga modelos OCR)
- HuggingFace bloqueado en entornos sandbox; modelos deben estar cacheados localmente
- Los documentos ORDET de Vigo son texto nativo (no escaneado) → extracción limpia

## Estructura ORDET
- Cada sector tiene su propia normativa en 04.NU (7-15 págs típico)
- Las tablas de parámetros urbanísticos están siempre en el artículo de "Ordenanza de Edificación"
- Los diagramas con cotas están en 03.PORD/05.xSECC (planos de sección)