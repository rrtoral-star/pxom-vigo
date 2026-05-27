import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*60)
print("ARTÍCULOS CON REFERENCIAS 'DE'")
print("="*60)

for art in data['articulos']:
    refs_de = [r for r in art.get('referencias', []) if r['fuente'] == 'DE']
    
    if refs_de:
        print(f"\n📄 Art. {art['numero']}: {art['titulo_descriptivo'][:50]}...")
        print(f"   Referencias 'DE': {len(refs_de)}")
        
        for ref in refs_de:
            print(f"     → Art. {ref['numero']} (fuente: DE)")
        
        # Buscar en el contenido el contexto
        contenido = art['contenido']
        for ref in refs_de:
            # Buscar el artículo en el texto
            import re
            patron = rf'art(?:ículo|\.)?\s+{ref["numero"]}\b.{{0,50}}'
            matches = re.findall(patron, contenido, re.IGNORECASE)
            
            if matches:
                print(f"\n   Contextos encontrados para Art. {ref['numero']}:")
                for i, match in enumerate(matches[:3], 1):  # Máximo 3
                    print(f"     {i}. ...{match}...")

print("\n" + "="*60)