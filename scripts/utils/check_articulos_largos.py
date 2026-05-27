# check_articulos_largos.py
import re
from pathlib import Path

content = Path("data/raw/docling/pxom_raw.md").read_text(encoding="utf-8")

PATRON = re.compile(
    r'^##\s+Art(?:iculo|\.)\s*(\d+(?:\.\d+)?)[\.:]?\s*(.+?)\.?\s*$',
    re.MULTILINE | re.IGNORECASE
)
matches = list(PATRON.finditer(content))

largos = []
for i, match in enumerate(matches):
    numero = match.group(1)
    titulo = match.group(2).strip()
    inicio = match.end()
    fin    = matches[i+1].start() if i+1 < len(matches) else len(content)
    texto  = content[inicio:fin].strip()
    if len(texto) > 4000:
        largos.append((numero, titulo, len(texto)))

print(f"Total artículos  : {len(matches)}")
print(f"Superan 4000 chars: {len(largos)}")
print()
for n, t, l in sorted(largos, key=lambda x: -x[2]):
    print(f"  Art. {n:6} | {l:6} chars | {t[:50]}")