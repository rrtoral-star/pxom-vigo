"""
enricher2.py - Enriquecimiento de chunks con Groq o Cerebras

Un chunk a la vez. Un solo proveedor sin fallback automático.
El pipeline decide qué proveedor usar.
Rate limit: espera el tiempo exacto que indica el error.
Límite diario: lanza RuntimeError("LIMITE_DIARIO")
"""

import re
import os
import time
from typing import List

try:
    import spacy
    NLP = spacy.load("es_core_news_md")
except:
    NLP = None

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False


TERMINOS_URBANISTICOS = {
    "altura", "plantas", "metros", "edificabilidad", "ocupación", "ocupacion",
    "retranqueo", "retranqueos", "parcela", "solar", "fachada", "alineación",
    "alineacion", "rasante", "cota", "volumen", "uso", "usos", "residencial",
    "comercial", "industrial", "dotacional", "equipamiento", "vivienda", "local",
    "sótano", "sotano", "bajo", "cubierta", "ático", "atico", "vuelo", "voladizo",
    "medianera", "lindero", "frente", "fondo", "separación", "separacion",
    "mínima", "minima", "máxima", "maxima", "consolidado", "urbanizable",
    "rústico", "rustico", "núcleo", "nucleo", "rural", "urbano"
}


def extraer_keywords(texto: str, top_n: int = 8) -> List[str]:
    keywords = set()
    texto_lower = texto.lower()

    for termino in TERMINOS_URBANISTICOS:
        if termino in texto_lower:
            keywords.add(termino)

    patrones = [
        r'(\d+(?:[,\.]\d+)?)\s*(m²|m2|metros cuadrados)',
        r'(\d+(?:[,\.]\d+)?)\s*(m\.?|metros?)\b',
        r'(\d+(?:[,\.]\d+)?)\s*(plantas?|pisos?)',
        r'(\d+(?:[,\.]\d+)?)\s*(%|por ciento)',
    ]
    for patron in patrones:
        for match in re.findall(patron, texto_lower):
            keywords.add(f"{match[0]} {match[1]}".strip())

    for cod in re.findall(r'\b([UNR]\d+(?:\.\d+)?)\b', texto.upper()):
        keywords.add(cod.lower())

    if NLP and len(texto) < 5000:
        doc = NLP(texto_lower[:3000])
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 3:
                if token.text in TERMINOS_URBANISTICOS:
                    keywords.add(token.text)

    return list(keywords)[:top_n]


class Enricher:
    """
    Enriquece chunks con un único proveedor LLM.
    Sin fallback. Sin batch. Un chunk a la vez.
    """

    def __init__(self, proveedor: str, model: str, api_key: str):
        self.proveedor = proveedor
        self.model = model
        self.client = None

        if proveedor == "groq" and GROQ_AVAILABLE:
            self.client = Groq(api_key=api_key, max_retries=0)
        elif proveedor == "cerebras" and CEREBRAS_AVAILABLE:
            self.client = Cerebras(api_key=api_key, max_retries=0)
        else:
            raise ValueError(f"Proveedor no disponible: {proveedor}")

        print(f"✓ Enricher: {proveedor} ({model})")

    def _llamar(self, prompt: str, max_tokens: int = 120, temperature: float = 0.7) -> str:
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    match = re.search(r'try again in ([\d\.]+)s', error_str)
                    if match:
                        wait = float(match.group(1)) + 0.5
                        if wait > 300:
                            print(f"  [{self.proveedor}] límite diario alcanzado")
                            raise RuntimeError("LIMITE_DIARIO")
                        print(f"  [{self.proveedor}] rate limit, esperando {wait:.1f}s...")
                        time.sleep(wait)
                    else:
                        print(f"  [{self.proveedor}] rate limit, esperando 5s...")
                        time.sleep(5.0)
                else:
                    print(f"  [{self.proveedor}] error: {error_str[:100]}")
                    return ""

    def generar_preguntas(self, texto: str, ordenanza: str = "", keywords: list = None) -> List[str]:
        keywords_str = ", ".join((keywords or [])[:5])
        prompt = f"""Normativa urbanística. Fragmento:
---
{texto[:600]}
---
Ordenanza: {ordenanza or "N/A"}
Conceptos: {keywords_str or "N/A"}

Escribe 2 preguntas cortas que haría un arquitecto para encontrar esto.
Una por línea, con signo de interrogación, sin numerar."""

        resp = self._llamar(prompt, max_tokens=120, temperature=0.7)
        if not resp:
            return []

        preguntas = []
        for p in resp.split('\n'):
            p = re.sub(r'^[\d\.\-\*]+\s*', '', p.strip())
            if len(p) > 10 and '?' in p:
                preguntas.append(p)
        return preguntas[:2]

    def generar_resumen(self, texto: str) -> str:
        prompt = f"""Resume en 1 frase este fragmento de normativa. Incluye valores numéricos si los hay.

{texto[:600]}

Resumen (1 frase, sin introducción):"""

        return self._llamar(prompt, max_tokens=60, temperature=0.3)

    def enriquecer_chunk(self, chunk) -> dict:
        """
        Enriquece un chunk y devuelve el resultado.
        No modifica el chunk directamente (thread-safe).
        """
        keywords = extraer_keywords(chunk.texto_original)
        preguntas = self.generar_preguntas(
            texto=chunk.texto_original,
            ordenanza=chunk.ordenanza_codigo or chunk.ordenanza,
            keywords=keywords
        )
        resumen = self.generar_resumen(chunk.texto_original)

        return {
            "keywords":            keywords,
            "preguntas_sinteticas": preguntas,
            "resumen":             resumen
        }