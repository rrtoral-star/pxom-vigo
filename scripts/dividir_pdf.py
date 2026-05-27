from pypdf import PdfReader, PdfWriter
from pathlib import Path

pdf_path = r"C:\PROY\pxom-solo\data\raw\BOE-424_Codigo_Tecnico_de_la_Edificacion_CTE.pdf"
output_dir = Path(r"C:\PROY\pxom-solo\data\raw\cte_partes")
output_dir.mkdir(exist_ok=True)

reader = PdfReader(pdf_path)
total = len(reader.pages)
parte_size = 300
print(f"Total páginas: {total}")

for i in range(0, total, parte_size):
    writer = PdfWriter()
    fin = min(i + parte_size, total)
    for p in range(i, fin):
        writer.add_page(reader.pages[p])
    nombre = output_dir / f"cte_parte_{i//parte_size + 1}.pdf"
    with open(nombre, "wb") as f:
        writer.write(f)
    print(f"✓ {nombre.name}: páginas {i+1}-{fin}")

print("Listo.")