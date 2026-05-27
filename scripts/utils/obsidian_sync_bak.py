"""
obsidian_sync.py — Sincroniza notas Obsidian desde bloques Claude

Uso:
    1. Copia los bloques Obsidian que genera Claude al portapapeles
    2. Ejecuta: python obsidian_sync.py
    3. Los archivos se crean/actualizan solos

También acepta un archivo de texto:
    python obsidian_sync.py --file mis_notas.txt

Flags:
    --dry-run     Muestra qué haría sin escribir nada
    --init        Crea carpetas base si no existen
    --debug       Muestra el contenido bruto del portapapeles y los bloques detectados
    --proyecto    Cambia el proyecto activo (default: pxom-solo)
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── CONFIGURACIÓN ────────────────────────────────────────────────
VAULT_BASE = Path(r"C:\PROY")

PROYECTOS = {
    "pxom-solo": VAULT_BASE / "pxom-solo" / "docs",
    # Añade aquí proyectos futuros:
    # "otro-proyecto": VAULT_BASE / "otro-proyecto" / "docs",
}

PROYECTO_DEFAULT = "pxom-solo"
CARPETAS_BASE = ["decisiones", "aprendizajes", "referencias"]
# ─────────────────────────────────────────────────────────────────


def normalizar(texto: str) -> str:
    """Normaliza saltos de línea y espacios invisibles de Windows."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    # Eliminar BOM si existe
    texto = texto.lstrip("\ufeff")
    return texto


def parsear_bloques(texto: str, debug: bool = False) -> list[dict]:
    texto = normalizar(texto)

    if debug:
        print("\n── DEBUG: primeros 500 chars del texto ──")
        print(repr(texto[:500]))
        print("─────────────────────────────────────────\n")

    bloques = []

    # Separar por líneas que empiezan con el emoji 📁
    # Soporta: con y sin backticks, con y sin →, con y sin [sección]
    PATRON_CABECERA = re.compile(
        r'^📁\s+'            # emoji + espacio
        r'`?'               # backtick opcional
        r'([^`\n]+?\.md)'   # nombre archivo (captura 1)
        r'`?'               # backtick opcional
        r'(?:\s*→\s*'       # flecha opcional
        r'\[?([^\]\n]*?)\]?'  # sección opcional (captura 2)
        r')?'
        r'\s*$',            # fin de línea
        re.MULTILINE
    )

    lineas = texto.split("\n")
    indices_cabecera = []

    for i, linea in enumerate(lineas):
        if PATRON_CABECERA.match(linea.strip()):
            indices_cabecera.append(i)

    if debug:
        print(f"── DEBUG: cabeceras encontradas en líneas: {indices_cabecera} ──")
        for idx in indices_cabecera:
            print(f"  [{idx}] {repr(lineas[idx])}")
        print()

    for n, idx in enumerate(indices_cabecera):
        linea_cab = lineas[idx].strip()
        m = PATRON_CABECERA.match(linea_cab)
        if not m:
            continue

        ruta = m.group(1).strip()
        seccion = (m.group(2) or "contenido").strip()

        # Contenido: desde la línea siguiente hasta la próxima cabecera
        fin = indices_cabecera[n + 1] if n + 1 < len(indices_cabecera) else len(lineas)
        cuerpo = "\n".join(lineas[idx + 1:fin]).strip()

        # Quitar envoltorio de code block si lo hay
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
        return f"  ✅ CREADO:      {ruta_rel}"

    actual = archivo.read_text(encoding="utf-8")

    if contenido_nuevo[:80] in actual:
        return f"  ⏭  SIN CAMBIOS: {ruta_rel}"

    separador = f"\n\n---\n*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    archivo.write_text(actual.rstrip() + separador + contenido_nuevo + "\n", encoding="utf-8")
    return f"  🔄 ACTUALIZADO: {ruta_rel}"


def init_estructura(docs: Path):
    docs.mkdir(parents=True, exist_ok=True)
    for carpeta in CARPETAS_BASE:
        (docs / carpeta).mkdir(exist_ok=True)
        print(f"  ✅ {carpeta}/")
    print("Estructura lista.")


def obtener_clipboard() -> str:
    # Método 1: tkinter (viene con Python, preserva Unicode/emojis)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        texto = root.clipboard_get()
        root.destroy()
        return texto or ""
    except Exception:
        pass

    # Método 2: pyperclip (si está instalado)
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception:
        pass

    print("⚠️  No se pudo leer el portapapeles.")
    print("   Usa: python obsidian_sync.py --file notas.txt")
    return ""


def main():
    parser = argparse.ArgumentParser(description="Sincroniza notas Obsidian desde bloques Claude")
    parser.add_argument("--proyecto", default=PROYECTO_DEFAULT)
    parser.add_argument("--file", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Muestra el contenido bruto del portapapeles")
    args = parser.parse_args()

    if args.proyecto not in PROYECTOS:
        print(f"❌ Proyecto '{args.proyecto}' no reconocido.")
        print(f"   Disponibles: {', '.join(PROYECTOS.keys())}")
        sys.exit(1)

    docs = PROYECTOS[args.proyecto]
    print(f"📂 {docs}")
    print(f"📋 Proyecto: {args.proyecto}\n")

    if args.init:
        init_estructura(docs)
        return

    texto = args.file.read_text(encoding="utf-8") if args.file else obtener_clipboard()

    if not texto or not texto.strip():
        print("⚠️  Sin contenido. Copia el bloque 'Actualización Obsidian' e inténtalo de nuevo.")
        return

    bloques = parsear_bloques(texto, debug=args.debug)

    if not bloques:
        print("⚠️  No se encontraron bloques.")
        print("   Formato esperado:")
        print("   📁 `decisiones/2026-05-24.md` → [sección]")
        print("   contenido aquí...")
        print()
        print("   Prueba con --debug para ver qué hay en el portapapeles.")
        return

    print(f"Bloques detectados: {len(bloques)}\n")
    for bloque in bloques:
        print(aplicar_bloque(docs, bloque, dry_run=args.dry_run))

    print(f"\n{'✅ Listo.' if not args.dry_run else '🔍 Dry run — nada escrito.'}")


if __name__ == "__main__":
    main()
