import re
with open(r'C:\PROY\pxom-solo\data\raw\docling\cte_se_raw.md', encoding='utf-8') as f:
    md = f.read()
cabeceras = re.findall(r'^#{1,3}.{0,80}$', md, re.MULTILINE)
print(f'Cabeceras: {len(cabeceras)}')
for c in cabeceras[:25]:
    print(c)
    