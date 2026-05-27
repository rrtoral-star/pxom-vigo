import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

total = len(data['articulos'])
numerados = 0
simples = 0
total_parrafos = 0

articulos_numerados = []

for art in data['articulos']:
    est = art['contenido_estructurado']
    if est['tipo'] == 'numerado':
        numerados += 1
        total_parrafos += est['total_parrafos']
        articulos_numerados.append({
            'numero': art['numero'],
            'titulo': art['titulo_descriptivo'][:50],
            'parrafos': est['total_parrafos']
        })
    else:
        simples += 1

print("\n" + "="*60)
print("ESTADÍSTICAS DE ESTRUCTURACIÓN DE PÁRRAFOS")
print("="*60)
print(f"\n📊 Total artículos: {total}")
print(f"📝 Artículos numerados: {numerados} ({numerados/total*100:.1f}%)")
print(f"📄 Artículos simples: {simples} ({simples/total*100:.1f}%)")
print(f"📑 Total párrafos extraídos: {total_parrafos}")
print(f"📈 Promedio párrafos/artículo: {total_parrafos/numerados:.1f}")

print(f"\n📚 TOP 10 artículos con más párrafos:")
top10 = sorted(articulos_numerados, key=lambda x: x['parrafos'], reverse=True)[:10]
for art in top10:
    print(f"   Art. {art['numero']:>3}: {art['parrafos']:>2} párrafos - {art['titulo']}...")

print("\n" + "="*60)