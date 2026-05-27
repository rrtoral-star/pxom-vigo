import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

numeros = set(int(a['numero']) for a in data['articulos'] if a['numero'].isdigit())

todos = set(range(1, 183))  # 1 a 182
faltantes = sorted(todos - numeros)

print(f"\n📊 Artículos presentes: {len(numeros)}")
print(f"📊 Artículos faltantes: {len(faltantes)}")

if faltantes:
    print(f"\n⚠️ FALTANTES:")
    for num in faltantes:
        print(f"   Art. {num}")
else:
    print(f"\n✅ No faltan artículos (rango completo 1-182)")