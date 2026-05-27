from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Conectar a Qdrant (en memoria)
client = QdrantClient(":memory:")

# Cargar modelo
print("Cargando modelo...")
model = SentenceTransformer('BAAI/bge-m3')

# Test queries
queries = [
    "¿Cuál es la altura máxima en ordenanza U6?",
    "retranqueo mínimo vivienda unifamiliar",
    "edificabilidad suelo urbanizable"
]

print("\nPrueba de búsqueda:")
for query in queries:
    print(f"\nQuery: '{query}'")
    
    # Generar embedding
    query_embedding = model.encode([query])[0].tolist()
    
    # Buscar
    try:
        results = client.query_points(
            collection_name="pxom_vigo_2025",
            query=query_embedding,
            limit=3
        ).points
        
        print(f"Top 3 resultados:")
        for i, hit in enumerate(results, 1):
            art = hit.payload.get('articulo_numero', 'N/A')
            titulo = hit.payload.get('articulo_titulo', 'N/A')
            score = hit.score
            print(f"   {i}. Art. {art} ({score:.3f}): {titulo[:50]}...")
    except Exception as e:
        print(f"Error: {e}")