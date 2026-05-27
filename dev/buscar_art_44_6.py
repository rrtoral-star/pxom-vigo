import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*60)
print("BUSCANDO REFERENCIAS AL ART. 44.6")
print("="*60)

total_encontradas = 0

for art in data['articulos']:
    refs_44_6 = [r for r in art.get('referencias', []) if r['numero'] == '44.6']
    
    if refs_44_6:
        total_encontradas += len(refs_44_6)
        print(f"\n📄 Art. {art['numero']}: {art['titulo_descriptivo'][:50]}...")
        
        for ref in refs_44_6:
            print(f"   → Art. 44.6 (fuente: {ref['fuente']})")

print(f"\n{'='*60}")
print(f"Total referencias al Art. 44.6: {total_encontradas}")
print("="*60)