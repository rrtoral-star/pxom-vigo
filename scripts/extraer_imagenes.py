import json, re, base64, os, hashlib
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("Cargando JSON...")
with open(r'C:\PROY\pxom-solo\data\raw\docling\pxom_test.json', encoding='utf-8') as f:
    data = json.load(f)

md = data['document']['md_content']

patron = r'!\[Image\]\(data:image/(png|jpeg|jpg);base64,([^)]+)\)'
matches = list(re.finditer(patron, md))
print(f"Imágenes totales: {len(matches)}")

urls = {}
hashes_vistos = {}

for i, m in enumerate(matches):
    ext = m.group(1)
    b64 = m.group(2)
    
    try:
        img_bytes = base64.b64decode(b64)
        img_hash = hashlib.md5(img_bytes).hexdigest()
        
        # Si ya existe esta imagen, reutiliza la URL
        if img_hash in hashes_vistos:
            urls[f"IMAGEN_{i+1}"] = hashes_vistos[img_hash]
            continue
        
        # Solo sube imágenes únicas
        nombre = f"pxom/imagen_{i+1}.{ext}"
        sb.storage.from_("pxom-imagenes").upload(
            nombre,
            img_bytes,
            {"content-type": f"image/{ext}"}
        )
        url = sb.storage.from_("pxom-imagenes").get_public_url(nombre)
        urls[f"IMAGEN_{i+1}"] = url
        hashes_vistos[img_hash] = url
        
        if len(hashes_vistos) % 10 == 0:
            print(f"  Únicas subidas: {len(hashes_vistos)} / Procesadas: {i+1}")
            
    except Exception as e:
        print(f"  Error imagen {i+1}: {e}")

with open(r'C:\PROY\pxom-solo\data\raw\docling\pxom_imagen_urls.json', 'w') as f:
    json.dump(urls, f, indent=2)

print(f"Total únicas: {len(hashes_vistos)} de {len(matches)}")
print(f"URLs guardadas: {len(urls)}")