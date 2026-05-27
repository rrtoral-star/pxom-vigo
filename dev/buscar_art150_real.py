import pdfplumber

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'

print("\nBuscando Art. 150 DESPUÉS del índice (desde pág. 25)...\n")

with pdfplumber.open(pdf_path) as pdf:
    for i in range(24, len(pdf.pages)):  # Desde página 25
        texto = pdf.pages[i].extract_text()
        
        if 'Art. 150.' in texto:
            print(f"✓ Encontrado en página {i+1}")
            
            # Extraer contexto amplio
            pos = texto.find('Art. 150.')
            inicio = max(0, pos - 100)
            fin = min(len(texto), pos + 800)
            
            print(f"\nCONTEXTO:")
            print("="*60)
            print(texto[inicio:fin])
            print("="*60)
            
            # Ver si el contenido es suficiente
            import re
            siguiente = re.search(r'Art\.\s+151\.', texto[pos:])
            if siguiente:
                contenido = texto[pos:pos+siguiente.start()]
                print(f"\nLongitud contenido hasta Art. 151: {len(contenido)} chars")
            
            break
    else:
        print("✗ Art. 150 NO encontrado después del índice")