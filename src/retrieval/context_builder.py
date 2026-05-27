import os
from supabase import create_client
from src.retrieval.search import buscar_chunks_qdrant  # ajusta al nombre real

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def obtener_datos_gis(rc: str) -> dict:
    """Llama a info_urbanistica(rc) en Supabase."""
    response = supabase.rpc("info_urbanistica", {"rc": rc}).execute()
    
    if response.data:
        return response.data
    return {"error": f"RC no encontrada: {rc}"}


def construir_contexto(rc: str, pregunta: str) -> dict:
    """
    Orquesta GIS + Qdrant y devuelve contexto unificado para el prompt.
    """
    # 1. Datos espaciales
    datos_gis = obtener_datos_gis(rc)
    
    # 2. Ordenanza para filtrar búsqueda RAG
    ordenanza = (
        datos_gis.get("zona_pxom", {}).get("ordenanza", "")
    )
    
    # 3. Chunks normativa desde Qdrant
    # Busca combinando la pregunta + la ordenanza detectada
    query_enriquecida = f"{pregunta} ordenanza {ordenanza}".strip()
    chunks = buscar_chunks_qdrant(query=query_enriquecida, top_k=5)
    
    return {
        "rc":               rc,
        "datos_gis":        datos_gis,
        "ordenanza":        ordenanza,
        "chunks_normativa": chunks,
    }