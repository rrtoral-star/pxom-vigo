import requests
from xml.etree import ElementTree as ET

NS = {"atom": "http://www.w3.org/2005/Atom"}

# Feed de municipios de Pontevedra
URL_36 = "http://www.catastro.hacienda.gob.es/INSPIRE/CadastralParcels/36/ES.SDGC.CP.atom_36.xml"

r = requests.get(URL_36, timeout=30)
root = ET.fromstring(r.content)

# Listar todos los municipios para ver el formato exacto
for entry in root.findall("atom:entry", NS):
    title = entry.find("atom:title", NS).text
    links = [lnk.get("href") for lnk in entry.findall("atom:link", NS)]
    print(f"{title}")
    for l in links:
        print(f"  → {l}")