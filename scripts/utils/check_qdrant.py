from qdrant_client import QdrantClient
from FlagEmbedding import FlagModel
import os
from dotenv import load_dotenv
load_dotenv()

c = QdrantClient(url=os.getenv('QDRANT_CLOUD_URL'), api_key=os.getenv('QDRANT_CLOUD_API_KEY'))

print("Cargando embedder...")
embedder = FlagModel(
    'BAAI/bge-m3',
    use_fp16=False,
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages: "
)
print("Embedder listo")

query = "altura máxima edificación"
vector = embedder.encode_queries([query])[0].tolist()
print(f"Vector generado: dimensiones={len(vector)}, primeros 5={vector[:5]}")

# Buscar sin threshold
hits = c.query_points(
    collection_name="pxom_vigo_2025_v2",
    query=vector,
    using="texto",
    limit=5,
    with_payload=True,
).points

print(f"\nResultados sin threshold: {len(hits)}")
for h in hits:
    print(f"  score={h.score:.4f} | art={h.payload.get('articulo_numero')} | {h.payload.get('cabecera','')[:60]}")