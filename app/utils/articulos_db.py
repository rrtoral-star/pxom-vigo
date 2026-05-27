import json
import re

class ArticulosDB:
    def __init__(self):
        with open("data/cleaned/normativa_urbanistica_pxom_2025.json", encoding="utf-8") as f:
            data = json.load(f)
        self.articulos = {art["numero"]: art for art in data["articulos"]}
    
    def obtener_articulo(self, numero):
        return self.articulos.get(str(numero))
    
    def formatear_articulo(self, art):
        if not art:
            return None
        
        texto = f"## Articulo {art['numero']}: {art['titulo_descriptivo']}\n\n"
        
        contexto = art.get("contexto", {})
        if contexto:
            texto += "**Contexto:**\n"
            if contexto.get("titulo"):
                texto += f"- Titulo {contexto['titulo'].get('numero', '')}: {contexto['titulo'].get('nombre', '')}\n"
            if contexto.get("capitulo"):
                texto += f"- Capitulo {contexto['capitulo'].get('numero', '')}: {contexto['capitulo'].get('nombre', '')}\n"
            if contexto.get("seccion"):
                texto += f"- Seccion {contexto['seccion'].get('numero', '')}: {contexto['seccion'].get('nombre', '')}\n"
            texto += "\n"
        
        texto += "**Contenido:**\n\n"
        
        contenido_est = art.get("contenido_estructurado", {})
        if contenido_est.get("tipo") == "numerado":
            for parrafo in contenido_est.get("parrafos", []):
                texto += f"**{parrafo['numero']}.** {parrafo['texto']}\n\n"
        else:
            texto += art["contenido"] + "\n\n"
        
        referencias = art.get("referencias", [])
        if referencias:
            texto += "**Referencias:**\n"
            refs_texto = ", ".join([f"Art. {r['numero']}" for r in referencias[:10]])
            texto += refs_texto + "\n"
        
        return texto

def detectar_solicitud_articulo(pregunta):
    pregunta_lower = pregunta.lower()
    patrones = [
        r"(?:art(?:iculo)?\.?\s+|artigo\s+)(\d+)",
        r"(?:ver|muestra|mostrar|dame|consulta|busca)\s+(?:el\s+)?(?:art(?:iculo)?\.?\s+|artigo\s+)?(\d+)",
        r"^(\d+)$",
    ]
    for patron in patrones:
        match = re.search(patron, pregunta_lower)
        if match:
            return match.group(1)
    return None
