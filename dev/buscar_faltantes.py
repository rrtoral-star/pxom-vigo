import pdfplumber
import re

pdf_path = 'data/raw/36057_PXOM_202502_AD01_NU_01NU_cas.pdf'
faltantes = ["52", "53", "150"]

print("\n" + "="*60)
print("BUSCANDO ARTÍCULOS FALTANTES")
print("="*60)

with pdfplumber.open(pdf_path) as pdf:
    for art_num in faltantes:
        print(f"\n{'='*60}")
        print(f"ARTÍCULO {art_num}")
        print(f"{'='*60}")
        
        encontrado = False
        for i in range(6, len(pdf.pages)):
            texto = pdf.pages[i].extract_text()
            
            # Buscar diferentes formatos
            patrones = [
                f'Art. {art_num}.',
                f'Art.{art_num}.',
                f'Art {art_num}.',
            ]
            
            for patron in patrones:
                if patron in texto:
                    print(f"✓ Encontrado en página {i+1}")
                    print(f"   Patrón: '{patron}'")
                    
                    # Extraer contexto (500 caracteres después)
                    pos = texto.find(patron)
                    fin = min(len(texto), pos + 600)
                    
                    print(f"\nCONTEXTO:")
                    print("-"*60)
                    print(texto[pos:fin])
                    print("-"*60)
                    
                    # Verificar longitud del contenido
                    # Buscar hasta el siguiente artículo
                    siguiente = re.search(r'Art\.\s+\d+\.', texto[pos+20:])
                    if siguiente:
                        contenido = texto[pos:pos+20+siguiente.start()]
                    else:
                        contenido = texto[pos:fin]
                    
                    print(f"\nLongitud del contenido: {len(contenido)} caracteres")
                    print(f"¿Pasa filtro de 100 chars?: {'✓ SÍ' if len(contenido) > 100 else '✗ NO'}")
                    
                    encontrado = True
                    break
            
            if encontrado:
                break
        
        if not encontrado:
            print(f"✗ NO ENCONTRADO en el PDF")

print("\n" + "="*60)