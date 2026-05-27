## PEPRIs Vigo — deuda técnica

### Documentos pendientes
- PEPRI Casco Vello — aprobado 12.04.2007 (DOG 06.06.2007), API-101
- PEPRI Bouzas — aprobado junto al anterior
- Fuente: https://hoxe.vigo.org/movemonos/urbanismo_pxom.php?lang=es
  → sección "Planeamientos incorporados al PGOM (APIs) incluídos PEPRI Casco Vello e Bouzas"

### Pipeline cuando se obtengan los PDFs
1. Procesar con Docling → pepri_casco_vello_raw.md / pepri_bouzas_raw.md
2. Añadir entradas en generate_wiki.py (tipo: PEPRI)
3. Indexar en pxom_vigo_2026_v2 con fuente: "pepri-casco-vello" / "pepri-bouzas"
4. Añadir botón PEPRI en Streamlit
5. Añadir sinónimos en query_expander.py:
   "casco vello" → ["casco histórico", "conjunto histórico", "PEPRI", "API-101"]
   "casco viejo" → ["casco histórico", "conjunto histórico", "PEPRI"]
   "bouzas"      → ["PEPRI Bouzas", "barrio histórico Bouzas"]

### Nota
El PXOM remite al PEPRI — sin estos documentos las consultas
sobre Casco Vello y Bouzas devuelven vacío o contexto insuficiente.