from qdrant_client import QdrantClient

client = QdrantClient(path="C:/PROY/pxom-solo/data/rag/qdrant_v2")

# Scroll por todos los puntos y contar los que tienen preguntas
total = 0
con_preguntas = 0
offset = None

while True:
    resultados, offset = client.scroll(
        collection_name="pxom_vigo_2025_v2",
        limit=100,
        offset=offset,
        with_payload=["preguntas_sinteticas", "resumen"]
    )
    for r in resultados:
        total += 1
        p = r.payload.get("preguntas_sinteticas", [])
        if p and len(p) > 0:
            con_preguntas += 1
    if offset is None:
        break

print(f"Total chunks: {total}")
print(f"Con preguntas sintéticas: {con_preguntas}")
print(f"Sin preguntas: {total - con_preguntas}")