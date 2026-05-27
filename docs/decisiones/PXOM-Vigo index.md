# PXOM-Vigo

## Estado
- **Fase:** En producción
- **Urgencia:** 🔴 Deuda técnica activa
- **Última actualización:** Abril 2026

## Qué es
Asistente de IA para arquitectos que permite consultar en lenguaje
natural la normativa urbanística de Vigo (PXOM), cruzada con datos
reales del Catastro. Ahorra horas de búsqueda manual y cita los
artículos aplicables a una parcela concreta.

## Reto activo
Extraer tablas e imágenes de la normativa de habitabilidad aún no
vinculadas a las respuestas del sistema.

## Objetivo final
Producto SaaS de suscripción para arquitectos y estudios. Escalable
a otros municipios.

## Stack
Python 3.10+, Llama 3.3 (Groq), BGE-M3, Qdrant Cloud,
Supabase + PostGIS, Streamlit, Railway

## Decisiones tomadas
- 2025 — Deploy en Railway
- 2025 — Embeddings con BGE-M3
- 2025 — Base vectorial en Qdrant Cloud

## Aprendizajes
- (pendiente)

## Conexiones
- [[Concepts/fastapi-groq]]
- [[Concepts/qdrant-busqueda-semantica]]
- [[practicas-ia/index]]

## Límites
- No tramita licencias ni gestiona expedientes
- No reemplaza al arquitecto ni toma decisiones legales
- Solo cubre Vigo en esta fase
- No es app BIM ni de diseño 3D