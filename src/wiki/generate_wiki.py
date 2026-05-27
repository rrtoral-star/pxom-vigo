"""
generate_wiki.py — Generador de Wiki PXOM-Solo
Uso:  python src/wiki/generate_wiki.py --fuente pxom
      python src/wiki/generate_wiki.py --fuente nhv
      python src/wiki/generate_wiki.py --fuente cte-si
      python src/wiki/generate_wiki.py --all
      python src/wiki/generate_wiki.py --all --dry-run
"""

import sys, json, re, argparse, time
from pathlib import Path
from datetime import datetime

# ── Rutas ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
SRC  = ROOT / "src"
sys.path.insert(0, str(SRC))

from chunker_docling import ChunkerDocling

import requests

# ── Config fuentes ─────────────────────────────────────────────────────────────
#   tipo    → agrupa en frontmatter y adapta el prompt
#   subtipo → DB-SI, DB-SUA… o el propio nombre si es único
#   wiki    → carpeta destino (CTE agrupado bajo wiki/cte/)

FUENTES = {
    "pxom": {
        "md":      "data/raw/docling/pxom_raw.md",
        "imgs":    "data/raw/docling/pxom_imagen_urls.json",
        "wiki":    "wiki/pxom",
        "tipo":    "PXOM",
        "subtipo": "PXOM",
        "label":   "Plan Xeral de Ordenación Municipal de Vigo",
    },
    "nhv": {
        "md":      "data/raw/docling/nhv_raw.md",
        "imgs":    "data/raw/docling/nhv_imagen_urls.json",
        "wiki":    "wiki/nhv",
        "tipo":    "NHV",
        "subtipo": "NHV",
        "label":   "Normativa de Habitabilidade de Vivenda (Galicia)",
    },
    "cte-si": {
        "md":      "data/raw/docling/cte_si_raw.md",
        "imgs":    "data/raw/docling/cte_si_imagen_urls.json",
        "wiki":    "wiki/cte/si",
        "tipo":    "CTE",
        "subtipo": "DB-SI",
        "label":   "CTE DB-SI — Seguridad en caso de Incendio",
    },
    "cte-sua": {
        "md":      "data/raw/docling/cte_sua_raw.md",
        "imgs":    "data/raw/docling/cte_sua_imagen_urls.json",
        "wiki":    "wiki/cte/sua",
        "tipo":    "CTE",
        "subtipo": "DB-SUA",
        "label":   "CTE DB-SUA — Seguridad de Utilización y Accesibilidad",
    },
    "cte-hs": {
        "md":      "data/raw/docling/cte_hs_raw.md",
        "imgs":    "data/raw/docling/cte_hs_imagen_urls.json",
        "wiki":    "wiki/cte/hs",
        "tipo":    "CTE",
        "subtipo": "DB-HS",
        "label":   "CTE DB-HS — Salubridad",
    },
    "cte-se": {
        "md":      "data/raw/docling/cte_se_raw.md",
        "imgs":    "data/raw/docling/cte_se_imagen_urls.json",
        "wiki":    "wiki/cte/se",
        "tipo":    "CTE",
        "subtipo": "DB-SE",
        "label":   "CTE DB-SE — Seguridad Estructural (General)",
    },
    "cte-se-ae": {
        "md":      "data/raw/docling/cte_se_ae_raw.md",
        "imgs":    "data/raw/docling/cte_se_ae_imagen_urls.json",
        "wiki":    "wiki/cte/se-ae",
        "tipo":    "CTE",
        "subtipo": "DB-SE-AE",
        "label":   "CTE DB-SE-AE — Acciones en la Edificación",
    },
    "cte-se-a": {
        "md":      "data/raw/docling/cte_se_a_raw.md",
        "imgs":    "data/raw/docling/cte_se_a_imagen_urls.json",
        "wiki":    "wiki/cte/se-a",
        "tipo":    "CTE",
        "subtipo": "DB-SE-A",
        "label":   "CTE DB-SE-A — Estructuras de Acero",
    },
    "cte-se-c": {
        "md":      "data/raw/docling/cte_se_c_raw.md",
        "imgs":    "data/raw/docling/cte_se_c_imagen_urls.json",
        "wiki":    "wiki/cte/se-c",
        "tipo":    "CTE",
        "subtipo": "DB-SE-C",
        "label":   "CTE DB-SE-C — Cimientos",
    },
    "cte-se-f": {
        "md":      "data/raw/docling/cte_se_f_raw.md",
        "imgs":    "data/raw/docling/cte_se_f_imagen_urls.json",
        "wiki":    "wiki/cte/se-f",
        "tipo":    "CTE",
        "subtipo": "DB-SE-F",
        "label":   "CTE DB-SE-F — Estructuras de Fábrica",
    },
    "cte-se-m": {
        "md":      "data/raw/docling/cte_se_m_raw.md",
        "imgs":    "data/raw/docling/cte_se_m_imagen_urls.json",
        "wiki":    "wiki/cte/se-m",
        "tipo":    "CTE",
        "subtipo": "DB-SE-M",
        "label":   "CTE DB-SE-M — Estructuras de Madera",
    },
    "cte-hr": {
        "md":      "data/raw/docling/cte_hr_raw.md",
        "imgs":    "data/raw/docling/cte_hr_imagen_urls.json",
        "wiki":    "wiki/cte/hr",
        "tipo":    "CTE",
        "subtipo": "DB-HR",
        "label":   "CTE DB-HR — Protección frente al Ruido",
    },
    "cte-he": {
        "md":      "data/raw/docling/cte_he_raw.md",
        "imgs":    "data/raw/docling/cte_he_imagen_urls.json",
        "wiki":    "wiki/cte/he",
        "tipo":    "CTE",
        "subtipo": "DB-HE",
        "label":   "CTE DB-HE — Ahorro de Energía",
    },
}

# ── Ollama ─────────────────────────────────────────────────────────────────────
OLLAMA_URL     = "http://localhost:11434/api/chat"
MODELO_WIKI    = "qwen3:14b"
TIMEOUT_SEG    = 300   # segundos por intento
MAX_REINTENTOS = 3     # reintentos antes de saltar
BACKOFF_SEG    = 10    # espera entre reintentos


# ── Checkpoint ─────────────────────────────────────────────────────────────────
def cargar_checkpoint(wiki_dir: Path) -> set:
    cp = wiki_dir / ".checkpoint.json"
    if cp.exists():
        return set(json.loads(cp.read_text(encoding="utf-8")))
    return set()

def guardar_checkpoint(wiki_dir: Path, procesados: set):
    cp = wiki_dir / ".checkpoint.json"
    cp.write_text(json.dumps(sorted(procesados), indent=2, ensure_ascii=False),
                  encoding="utf-8")


# ── Conversor de wikilinks ────────────────────────────────────────────────────
# Convierte referencias textuales a wikilinks de Obsidian:
#   "Art. 45"   → [[art-45]]
#   "Art. 3.1"  → [[art-3-1]]
#   "Sección A" → texto sin cambio (no hay slug definido)

_RE_ARTICULO = re.compile(
    r'\bArt(?:ículo|iculo|\.)?\s*\.?\s*(\d+(?:\.\d+)?)\b',
    re.IGNORECASE
)

def construir_slugs_validos(articulos: list[dict]) -> set:
    """Genera el conjunto de slugs reales de una fuente."""
    return {f"art-{a['numero'].replace('.', '-')}" for a in articulos}

def convertir_wikilinks(refs: list[str], fuente_actual: str,
                        slugs_validos: set = None) -> list[str]:
    """
    Convierte referencias textuales a wikilinks Obsidian.
    Si slugs_validos esta presente, elimina referencias a articulos
    que no existen realmente (evita alucinaciones del LLM).
    """
    resultado = []
    for ref in refs:
        wikilinks_en_ref = []

        def reemplazar(m):
            numero = m.group(1)
            slug   = f"art-{numero.replace('.', '-')}"
            valido = (slugs_validos is None) or (slug in slugs_validos)
            wikilinks_en_ref.append(valido)
            return f"[[{slug}]]" if valido else f"__INVALIDO_{slug}__"

        ref_convertida = _RE_ARTICULO.sub(reemplazar, ref)

        # Descartar referencias con cualquier slug inexistente
        if "__INVALIDO_" not in ref_convertida:
            resultado.append(ref_convertida)

    return resultado


# ── Prompts por tipo ───────────────────────────────────────────────────────────
CONTEXTO_TIPO = {
    "PXOM": (
        "normativa urbanística municipal (PXOM). "
        "El lector es un arquitecto o técnico municipal que necesita entender "
        "qué regula el artículo, qué usos, alturas, edificabilidades y retranqueos fija, "
        "y cómo se relaciona con otras ordenanzas del PXOM."
    ),
    "NHV": (
        "normativa de habitabilidad de vivienda de Galicia (NHV). "
        "El lector es un arquitecto técnico que necesita aplicar estas condiciones "
        "mínimas en proyectos de vivienda: superficies, alturas libres, iluminación, "
        "ventilación y accesibilidad."
    ),
    "CTE": (
        "Código Técnico de la Edificación (CTE). "
        "El lector es un arquitecto o ingeniero que necesita aplicar este documento "
        "básico en proyecto: exigencias técnicas, valores límite, métodos de cálculo "
        "y relación con otras secciones del CTE."
    ),
}

def construir_prompt(articulo: dict, config: dict) -> str:
    numero    = articulo["numero"]
    titulo    = articulo["titulo"]
    texto_completo = articulo["texto_bloque"]
    limite         = 8000
    es_parcial     = len(texto_completo) > limite
    texto          = texto_completo[:limite]
    ctx       = articulo.get("contexto", {})
    capitulo  = ctx.get("capitulo", "")
    ordenanza = ctx.get("ordenanza_codigo", "") or ctx.get("ordenanza", "")
    tipo      = config["tipo"]
    subtipo   = config["subtipo"]
    label     = config["label"]

    contexto_tipo = CONTEXTO_TIPO.get(tipo, "normativa técnica de edificación.")

    contexto_str = f"Documento: {label}\n"
    if ordenanza:
        contexto_str += f"Ordenanza: {ordenanza}\n"
    if capitulo:
        contexto_str += f"Capítulo: {capitulo}\n"

    aviso_parcial = (
        "\nNOTA: El artículo es extenso. Solo se muestra la primera parte. "
        "Indica en notas_interpretacion que el resumen es parcial y cubre solo la introducción."
        if es_parcial else ""
    )

    return f"""Eres un experto en {contexto_tipo}

Analiza el siguiente artículo y responde ÚNICAMENTE con un objeto JSON válido.
Sin texto adicional, sin bloques markdown, sin ```json.

{contexto_str}{aviso_parcial}
Artículo: {subtipo} — Art. {numero}. {titulo}
Texto:
{texto}

El JSON debe tener EXACTAMENTE estas claves:
{{
  "resumen": "2-3 frases claras sobre qué regula, qué exige y por qué importa.",
  "notas_interpretacion": ["nota práctica 1", "nota práctica 2", "caso límite o excepción"],
  "referencias_cruzadas": ["Art. X / Sección Y — motivo de la relación"],
  "tags": ["tag1", "tag2", "tag3"]
}}

Criterios:
- resumen: directo, sin jerga innecesaria, orientado a aplicación práctica.
- notas_interpretacion: advertencias reales, excepciones, casos frecuentes en proyecto.
- referencias_cruzadas: SOLO artículos mencionados explícitamente en el texto proporcionado. No inventes referencias ni cites documentos externos que no aparezcan en el texto.
- tags: conceptos técnicos clave (altura, retranqueo, resistencia al fuego, etc.).

Solo JSON."""


# ── Llamada Ollama ─────────────────────────────────────────────────────────────
def llamar_ollama(prompt: str) -> dict:
    payload = {
        "model": MODELO_WIKI,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    import time as _time
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEG)
            r.raise_for_status()
            contenido = r.json()["message"]["content"].strip()
            contenido = re.sub(r"^```(?:json)?\s*", "", contenido)
            contenido = re.sub(r"\s*```$", "", contenido)
            contenido = re.sub(r"<think>.*?</think>", "", contenido, flags=re.DOTALL).strip()
            return json.loads(contenido)
        except json.JSONDecodeError as e:
            print(f"    ⚠ JSON inválido (intento {intento}): {e}")
            if intento < MAX_REINTENTOS:
                _time.sleep(BACKOFF_SEG)
            else:
                return {"resumen": contenido, "notas_interpretacion": [],
                        "referencias_cruzadas": [], "tags": []}
        except Exception as e:
            print(f"    ⚠ Error Ollama (intento {intento}/{MAX_REINTENTOS}): {e}")
            if intento < MAX_REINTENTOS:
                _time.sleep(BACKOFF_SEG)
            else:
                return {}
    return {}


# ── Renderizar página wiki ──────────────────────────────────────────────────────
def renderizar_pagina(articulo: dict, meta: dict, config: dict,
                      slugs_validos: set = None,
                      imagen_urls: list = None) -> str:
    numero    = articulo["numero"]
    titulo    = articulo["titulo"]
    texto     = articulo["texto_bloque"]
    ctx       = articulo.get("contexto", {})
    capitulo  = ctx.get("capitulo", "—")
    ordenanza = ctx.get("ordenanza_codigo", "") or ctx.get("ordenanza", "—")
    fecha     = datetime.now().strftime("%Y-%m-%d")

    tipo    = config["tipo"]
    subtipo = config["subtipo"]
    label   = config["label"]

    resumen  = meta.get("resumen", "")
    notas    = meta.get("notas_interpretacion", [])
    refs     = convertir_wikilinks(meta.get("referencias_cruzadas", []), config["subtipo"], slugs_validos)
    tags     = meta.get("tags", [])
    tags_str = " ".join(f"#{t.replace(' ', '_')}" for t in tags)
    es_parcial = len(articulo["texto_bloque"]) > 8000

    notas_md = "\n".join(f"- {n}" for n in notas) if notas else "_Sin notas._"
    refs_md  = "\n".join(f"- {r}" for r in refs)  if refs  else "_Sin referencias identificadas._"
    aviso_md = (
        "\n> ⚠ **Resumen parcial** — Este artículo es extenso ({:,} chars). "
        "El resumen y las notas cubren solo la primera parte.\n".format(len(articulo["texto_bloque"]))
        if es_parcial else ""
    )
    imgs_utiles = [u for u in (imagen_urls or []) if u]
    if imgs_utiles:
        imagenes_md = "## Im\u00e1genes\n\n" + "\n\n".join(f"![]({u})" for u in imgs_utiles) + "\n\n"
    else:
        imagenes_md = ""

    return f"""---
articulo: "{numero}"
titulo: "{titulo}"
tipo_doc: "{tipo}"
subtipo: "{subtipo}"
documento: "{label}"
ordenanza: "{ordenanza}"
capitulo: "{capitulo}"
generado: "{fecha}"
tags: [{", ".join(f'"{t}"' for t in tags)}]
---

# {subtipo} — Art. {numero}. {titulo}

> **Tipo:** `{tipo}` | **Documento:** {subtipo} | **Capítulo:** {capitulo} | **Ordenanza:** {ordenanza}

## Resumen
{aviso_md}
{resumen}

---

## Texto Original

{texto}

{imagenes_md}---

## Notas de Interpretación

{notas_md}

## Referencias Cruzadas

{refs_md}

---

{tags_str}
*Generado el {fecha} con `{MODELO_WIKI}`*
"""


# ── Procesar una fuente ────────────────────────────────────────────────────────
def procesar_fuente(nombre: str, config: dict, dry_run: bool = False):
    md_path  = ROOT / config["md"]
    wiki_dir = ROOT / config["wiki"]

    if not md_path.exists():
        print(f"  ⚠ No encontrado: {md_path} — saltando")
        return

    wiki_dir.mkdir(parents=True, exist_ok=True)
    procesados = cargar_checkpoint(wiki_dir)

    print(f"\n{'='*60}")
    print(f"  Fuente  : {nombre}  ({config['tipo']} / {config['subtipo']})")
    print(f"  Origen  : {md_path.name}")
    print(f"  Destino : {wiki_dir}")

    imagen_urls_map = {}
    imgs_path = ROOT / config.get("imgs", "")
    if imgs_path.exists():
        imagen_urls_map = json.loads(imgs_path.read_text(encoding="utf-8"))
        print(f"  Imágenes: {len(imagen_urls_map)} entradas")

    chunker   = ChunkerDocling(str(md_path), fuente=nombre, imagen_urls_map=imagen_urls_map)
    articulos = chunker._extraer_articulos()

    slugs_validos = construir_slugs_validos(articulos)
    pendientes = [a for a in articulos if a["numero"] not in procesados]
    print(f"  Artículos total : {len(articulos)}")
    print(f"  Ya procesados   : {len(procesados)}")
    print(f"  Pendientes      : {len(pendientes)}")

    if dry_run:
        print("  [dry-run] Sin cambios.")
        return

    for i, art in enumerate(pendientes, 1):
        numero = art["numero"]
        titulo = art["titulo"]
        slug   = numero.replace(".", "-")
        out_path = wiki_dir / f"art-{slug}.md"

        print(f"  [{i:3}/{len(pendientes)}] Art. {numero} — {titulo[:50]}", end=" ", flush=True)

        # Extraer imágenes útiles del artículo
        chunks_art = chunker._procesar_articulo(art)
        imgs = chunks_art[0].imagen_urls if chunks_art else []

        t0     = time.time()
        prompt = construir_prompt(art, config)
        meta   = llamar_ollama(prompt)
        t1     = time.time()

        if not meta:
            print(f"✗ ({t1-t0:.1f}s)")
            continue

        pagina = renderizar_pagina(art, meta, config, slugs_validos, imgs)
        out_path.write_text(pagina, encoding="utf-8")

        procesados.add(numero)
        guardar_checkpoint(wiki_dir, procesados)
        print(f"✓ ({t1-t0:.1f}s)")

    print(f"\n  ✓ {len(procesados)} artículos en {wiki_dir}")


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Genera wiki desde markdown fuente")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fuente", choices=FUENTES.keys(),
                       help="Procesar una sola fuente")
    group.add_argument("--all", action="store_true",
                       help="Procesar todas las fuentes")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar plan sin generar nada")
    args = parser.parse_args()

    fuentes_a_procesar = FUENTES if args.all else {args.fuente: FUENTES[args.fuente]}

    for nombre, config in fuentes_a_procesar.items():
        procesar_fuente(nombre, config, dry_run=args.dry_run)

    print("\n✅ Wiki generada.")


if __name__ == "__main__":
    main()
