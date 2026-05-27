import pdfplumber

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'

print("\nBuscando 'Art. 1. Ámbito' en el PDF...\n")

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        texto = page.extract_text()
        if 'Art. 1. Ámbito' in texto or 'Art. 1.\nÁmbito' in texto:
            print(f"✓ Encontrado en página {i+1}")
            print(f"\nTexto de la página {i+1}:")
            print("="*60)
            print(texto[:1000])
            print("="*60)
            break