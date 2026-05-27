from dbfread import DBF
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

tabla = DBF(r'C:\PROY\pxom-solo\data\inspire\urbana\54057uA 54007 VIGO\CARVIA\Carvia.DBF', encoding='latin1')
df = pd.DataFrame(iter(tabla))
df.columns = [c.lower() for c in df.columns]

registros = df[['via','ttggss','denomina','fechaalta','fechabaja']].to_dict('records')
client.table('catastro_carvia').insert(registros).execute()
print(f'✅ {len(registros)} vías cargadas')
