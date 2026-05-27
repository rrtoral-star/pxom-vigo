## Próxima sesión — Catastro en Streamlit

Integrar funciones PostGIS/Supabase en app.py:
- Caja de entrada: dirección o refcat
- Flujo: dirección → API Catastro → refcat → PostGIS → parámetros urbanísticos
- Funciones a integrar:
  - zona_pxom(refcat)
  - edificabilidad_real(refcat)
  - ocupacion_parcela(refcat)
  - altura_estimada(refcat)
  - parametros_urbanisticos(refcat)
  - es_parcela_pasante(refcat)
- Mostrar resultado junto a la consulta RAG normativa
- Oracle: pospuesto hasta tener el piloto local completo