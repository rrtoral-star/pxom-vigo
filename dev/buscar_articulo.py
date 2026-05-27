import pdfplumber
import re

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'
articulo_buscar = "22"

print(f"\nBuscando Art. {articulo_buscar} en el PDF...\n")

with pdfplumber.open(pdf_path) as pdf:
    for i in range(6, len(pdf.pages)):  # Desde página 7
        texto = pdf.pages[i].extract_text()
        
        # Buscar diferentes formatos
        patrones = [
            f'Art. {articulo_buscar}.',
            f'Art.{articulo_buscar}.',
            f'Art {articulo_buscar}.',
            f'Artículo {articulo_buscar}.',
        ]
        
        for patron in patrones:
            if patron in texto:
                print(f"✓ Encontrado en página {i+1}")
                print(f"   Patrón: '{patron}'")
                
                # Extraer contexto (200 caracteres antes y después)
                pos = texto.find(patron)
                inicio = max(0, pos - 50)
                fin = min(len(texto), pos + 500)
                
                print(f"\nCONTEXTO:")
                print("="*60)
                print(texto[inicio:fin])
                print("="*60)
                exit()

print(f"✗ No encontrado Art. {articulo_buscar}")