import pdfplumber

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print("\n" + "="*60)
    print("ANÁLISIS DEL PDF - PRIMERAS PÁGINAS")
    print("="*60)
    
    # Página 1 (probablemente portada)
    print("\n=== PÁGINA 1 (Portada) ===")
    print(pdf.pages[0].extract_text()[:500])
    
    # Página 10 (probablemente índice)
    print("\n=== PÁGINA 10 (Índice?) ===")
    print(pdf.pages[9].extract_text()[:800])
    
    # Página 30 (probablemente contenido)
    print("\n=== PÁGINA 30 (Contenido?) ===")
    print(pdf.pages[29].extract_text()[:1000])
    
    # Página 50
    print("\n=== PÁGINA 50 ===")
    print(pdf.pages[49].extract_text()[:1000])
    
    print("\n" + "="*60)