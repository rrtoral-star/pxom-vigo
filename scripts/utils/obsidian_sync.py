"""
obsidian_sync.py — Sincroniza notas Obsidian desde bloques Claude

Uso:
    1. Copia los bloques Obsidian que genera Claude al portapapeles
    2. Ejecuta desde la carpeta del proyecto:
       python scripts/utils/obsidian_sync.py
    3. Detecta el proyecto por la ruta actual automaticamente

Flags:
    --proyecto    Fuerza un proyecto concreto (override del auto-detect)
    --global      Atajo para --proyecto global
    --file        Leer desde archivo en vez del portapapeles
    --dry-run     Muestra que haria sin escribir nada
    --debug       Muestra el contenido bruto del portapapeles
    --init        Crea carpetas base si no existen
    --list        Lista los proyectos disponibles
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── CONFIGURACION ────────────────────────────────────────────────
VAULT_BASE = Path(r"C:\PROY")

PROYECTOS = {
    "global":          VAULT_BASE / "_global",
    "pxom-solo":       VAULT_BASE / "pxom-solo"       / "docs",
    "agente-mercados": VAULT_BASE / "agente-mercados"  / "docs",
    "paper-gap":       VAULT_BASE / "paper-gap"        / "docs",
    "practicas-ia":    VAULT_BASE / "practicas-ia"     / "docs",
    "synthgen":        VAULT_BASE / "synthgen"         / "docs",
}

CARPETAS_BASE = {
    "global":  ["stack-compartido", "aprendizajes", "herramientas", "decisiones"],
    "default": ["decisiones", "aprendizajes", "referencias", "deuda-tecnica"],
}
# ─────────────────────────────────────────────────────────────────


def detectar_proyecto() -> str | None:
    """Detecta el proyecto activo por la ruta de trabajo actual."""
    cwd = Path.cwd().resolve()

    # Si estamos en la raiz del vault → global
    try:
        if cwd == VAULT_BASE.resolve():
            return "global"
    except Exception:
        pass

    # Buscar coincidencia con alguna carpeta de proyecto
    for nombre in PROYECTOS:
        if nombre == "global":
            continue
        carpeta = VAULT_BASE / nombre
        try:
            cwd.relative_to(carpeta.resolve())
            return nombre
        except ValueError:
            continue

    return None


def normalizar(texto: str) -> str:
    return texto.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")


def parsear_bloques(texto: str, debug: bool = False) -> list[dict]:
    texto = normalizar(texto)

    if debug:
        print("\n── DEBUG: primeros 500 chars ──")
        print(repr(texto[:500]))
        print("───────────────────────────────\n")

    PATRON = re.compile(
        r'^📁\s+`?([^`\n]+?\.md)`?'
        r'(?:\s*→\s*\[?([^\]\n]*?)\]?)?'
        r'\s*$',
        re.MULTILINE
    )

    lineas = texto.split("\n")
    indices = []
    for i, linea in enumerate(lineas):
        if PATRON.match(linea.strip()):
            indices.append(i)

    if debug:
        print(f"── DEBUG: cabeceras en lineas {indices} ──")
        for idx in indices:
            print(f"  [{idx}] {repr(lineas[idx])}")
        print()

    bloques = []
    for n, idx in enumerate(indices):
        m = PATRON.match(lineas[idx].strip())
        if not m:
            continue
        ruta = m.group(1).strip()
        seccion = (m.group(2) or "contenido").strip()
        fin = indices[n + 1] if n + 1 < len(indices) else len(lineas)
        cuerpo = "\n".join(lineas[idx + 1:fin]).strip()
        cuerpo = re.sub(r'^```(?:markdown|md)?\n?', '', cuerpo)
        cuerpo = re.sub(r'\n?```\s*$', '', cuerpo).strip()
        if cuerpo:
            bloques.append({"ruta": ruta, "seccion": seccion, "contenido": cuerpo})

    return bloques


def aplicar_bloque(docs: Path, bloque: dict, dry_run: bool = False) -> str:
    ruta_rel = bloque["ruta"].lstrip("/\\")
    archivo = docs / ruta_rel
    contenido_nuevo = bloque["contenido"]

    if dry_run:
        accion = "CREAR" if not archivo.exists() else "ACTUALIZAR"
        return f"  [dry] {accion}: {ruta_rel}"

    archivo.parent.mkdir(parents=True, exist_ok=True)

    if not archivo.exists():
        archivo.write_text(contenido_nuevo + "\n", encoding="utf-8")
        return f"  CREADO:      {ruta_rel}"

    actual = archivo.read_text(encoding="utf-8")
    if contenido_nuevo[:80] in actual:
        return f"  SIN CAMBIOS: {ruta_rel}"

    separador = f"\n\n---\n*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    archivo.write_text(actual.rstrip() + separador + contenido_nuevo + "\n", encoding="utf-8")
    return f"  ACTUALIZADO: {ruta_rel}"


def init_estructura(proyecto: str, docs: Path):
    docs.mkdir(parents=True, exist_ok=True)
    carpetas = CARPETAS_BASE.get(proyecto, CARPETAS_BASE["default"])
    for carpeta in carpetas:
        (docs / carpeta).mkdir(exist_ok=True)
        print(f"  OK: {carpeta}/")
    print(f"Vault '{proyecto}' listo en {docs}")


def obtener_clipboard() -> str:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        texto = root.clipboard_get()
        root.destroy()
        return texto or ""
    except Exception:
        pass
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception:
        pass
    print("No se pudo leer el portapapeles.")
    print("Usa: python obsidian_sync.py --file notas.txt")
    return ""


def main():
    parser = argparse.ArgumentParser(description="Sincroniza notas Obsidian desde bloques Claude")
    parser.add_argument("--proyecto", default=None, help=f"Proyecto destino: {', '.join(PROYECTOS.keys())}")
    parser.add_argument("--global", dest="forzar_global", action="store_true", help="Atajo para --proyecto global")
    parser.add_argument("--file", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        print("\nProyectos disponibles:")
        for nombre, ruta in PROYECTOS.items():
            existe = "OK" if ruta.exists() else "XX"
            print(f"  [{existe}] {nombre:20} -> {ruta}")
        detectado = detectar_proyecto()
        print(f"\nProyecto detectado desde ruta actual: {detectado or '(ninguno)'}")
        return

    # Resolver proyecto
    if args.forzar_global:
        proyecto = "global"
    elif args.proyecto:
        proyecto = args.proyecto
    else:
        proyecto = detectar_proyecto()

    if proyecto is None:
        print("No se pudo detectar el proyecto desde la ruta actual.")
        print(f"Usa --proyecto [nombre]. Disponibles: {', '.join(PROYECTOS.keys())}")
        sys.exit(1)

    if proyecto not in PROYECTOS:
        print(f"Proyecto '{proyecto}' no reconocido.")
        print(f"Disponibles: {', '.join(PROYECTOS.keys())}")
        sys.exit(1)

    docs = PROYECTOS[proyecto]
    print(f"Proyecto: {proyecto}")
    print(f"Vault:    {docs}\n")

    if args.init:
        init_estructura(proyecto, docs)
        return

    texto = args.file.read_text(encoding="utf-8") if args.file else obtener_clipboard()

    if not texto or not texto.strip():
        print("Sin contenido. Copia el bloque 'Actualizacion Obsidian' e intentalo de nuevo.")
        return

    bloques = parsear_bloques(texto, debug=args.debug)

    if not bloques:
        print("No se encontraron bloques.")
        print("Formato esperado:")
        print("  📁 `decisiones/2026-05-24.md` -> [etiqueta]")
        print("  contenido...")
        print("\nPrueba con --debug para ver el portapapeles.")
        return

    print(f"Bloques detectados: {len(bloques)}\n")
    for bloque in bloques:
        print(aplicar_bloque(docs, bloque, dry_run=args.dry_run))

    print(f"\n{'Listo.' if not args.dry_run else 'Dry run - nada escrito.'}")


if __name__ == "__main__":
    main()
