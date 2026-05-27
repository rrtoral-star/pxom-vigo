import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

articulos = data['articulos']

# Extraer todos los números
numeros = [a['numero'] for a in articulos]

# Detectar duplicados
from collections import Counter
contador = Counter(numeros)
duplicados = {num: count for num, count in contador.items() if count > 1}

print(f"\n📊 Total artículos en JSON: {len(articulos)}")
print(f"📊 Números únicos: {len(set(numeros))}")

if duplicados:
    print(f"\n⚠️ DUPLICADOS ENCONTRADOS:")
    for num, count in sorted(duplicados.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        print(f"   Art. {num}: aparece {count} veces")
        # Mostrar títulos
        for a in articulos:
            if a['numero'] == num:
                print(f"      - {a['titulo'][:70]}...")
else:
    print(f"\n✅ No hay duplicados")

print(f"\n📋 Rango de artículos:")
nums_int = [int(n) for n in numeros if n.isdigit()]
print(f"   Primero: {min(nums_int)}")
print(f"   Último: {max(nums_int)}")
print(f"   Artículos con letras: {len([n for n in numeros if not n.isdigit()])}")