from qdrant_client import QdrantClient

client = QdrantClient(path="data/rag/qdrant_storage")

result = client.scroll(
    collection_name="pxom_vigo_2025",
    limit=1,
    with_payload=True,
    with_vectors=False
)

import json
print(json.dumps(result[0][0].payload, indent=2, ensure_ascii=False))

# También cuántos chunks hay
print(f"\nTotal chunks: {client.count('pxom_vigo_2025')}")