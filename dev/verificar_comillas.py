import json

with open('data/cleaned/normativa_urbanistica_pxom_2025.json', encoding='utf-8') as f:
    data = json.load(f)

# Art. 21 tiene una referencia problemática
art_21 = next(a for a in data['articulos'] if a['numero'] == '21')

# Buscar "Ley 37/2015" en el contenido
import re
matches = re.finditer(r'.{0,80}Ley 37/2015.{0,80}', art_21['contenido'])

print("\n" + "="*60)
print("CONTEXTO COMPLETO - Art. 21, Ley 37/2015")
print("="*60)

for i, match in enumerate(matches, 1):
    texto = match.group()
    print(f"\n{i}. {texto}")
    print(f"\n   Caracteres especiales:")
    for char in texto:
        if ord(char) > 127 or char in ['"', '"', '"', "'", "'"]:
            print(f"     '{char}' → código: {ord(char)}")

print("\n" + "="*60)