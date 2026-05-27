import json
from collections import Counter

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

total_articulos = len(data['articulos'])
articulos_con_refs = 0
total_referencias = 0
referencias_por_fuente = Counter()
articulos_mas_referenciados = Counter()

# TOP artículos con más referencias
top_refs = []

for art in data['articulos']:
    refs = art.get('referencias', [])
    
    if refs:
        articulos_con_refs += 1
        total_referencias += len(refs)
        
        top_refs.append({
            'numero': art['numero'],
            'titulo': art['titulo_descriptivo'][:50],
            'total_refs': len(refs)
        })
        
        for ref in refs:
            referencias_por_fuente[ref['fuente']] += 1
            articulos_mas_referenciados[ref['numero']] += 1

print("\n" + "="*60)
print("ANÁLISIS DE REFERENCIAS CRUZADAS")
print("="*60)

print(f"\n📊 Estadísticas Generales:")
print(f"   Total artículos: {total_articulos}")
print(f"   Artículos con referencias: {articulos_con_refs} ({articulos_con_refs/total_articulos*100:.1f}%)")
print(f"   Total referencias encontradas: {total_referencias}")
print(f"   Promedio referencias/artículo: {total_referencias/articulos_con_refs:.1f}")

print(f"\n📚 Referencias por Fuente:")
for fuente, count in referencias_por_fuente.most_common(10):
    print(f"   {fuente}: {count} referencias")

print(f"\n🔗 Artículos Más Referenciados (TOP 10):")
for numero, count in articulos_mas_referenciados.most_common(10):
    print(f"   Art. {numero}: {count} veces")

print(f"\n📖 TOP 10 Artículos con Más Referencias:")
top_10 = sorted(top_refs, key=lambda x: x['total_refs'], reverse=True)[:10]
for art in top_10:
    print(f"   Art. {art['numero']:>3}: {art['total_refs']:>2} refs - {art['titulo']}...")

print("\n" + "="*60)