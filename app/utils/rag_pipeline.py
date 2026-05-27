from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from groq import Groq

class RAGArquitectos:
    def __init__(self, groq_api_key):
        self.groq_client = Groq(api_key=groq_api_key)
        self.embed_model = SentenceTransformer('BAAI/bge-m3', device='cpu')
        self.qdrant = QdrantClient(path='data/rag/qdrant_storage')
        self.collection_name = 'pxom_vigo_2025'
    
    def buscar_contexto(self, query, top_k=5):
        query_embedding = self.embed_model.encode([query])[0].tolist()
        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k
        ).points
        return results
    
    def formatear_contexto(self, results):
        contexto = ''
        for i, hit in enumerate(results, 1):
            art_num = hit.payload.get('articulo_numero', 'N/A')
            titulo = hit.payload.get('articulo_titulo', '')
            texto = hit.payload.get('text', '')
            ordenanza = hit.payload.get('ordenanza', '')
            contexto += f'Fragmento {i} - Art. {art_num}\n'
            if ordenanza:
                contexto += f'Ordenanza: {ordenanza}\n'
            contexto += f'{titulo}\n{texto}\n\n'
        return contexto
    
    def generar_respuesta(self, pregunta, results, modelo):
        contexto = self.formatear_contexto(results)
        system_prompt = 'Eres experto en PXOM Vigo. Responde solo con info de fragmentos. Cita articulos. Si pregunta en gallego, responde en gallego.'
        user_prompt = f'Pregunta: {pregunta}\n\nFragmentos:\n{contexto}'
        chat = self.groq_client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            model=modelo,
            temperature=0.1,
            max_tokens=1024
        )
        return chat.choices[0].message.content
