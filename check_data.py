"""Script rápido para verificar cuántos datos hay en Supabase."""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Verificando datos en Supabase...")
print("="*60)

# Contar nodos
result = supabase.table('infra_nodos').select('id', count='exact').execute()
print(f"Nodos (infra_nodos): {result.count}")

# Contar aristas
result = supabase.table('infra_aristas').select('id', count='exact').execute()
print(f"Aristas (infra_aristas): {result.count}")

# Metadata
result = supabase.table('meta_elevacion').select('id', count='exact').execute()
print(f"Elevación: {result.count}")

result = supabase.table('meta_lluvia').select('id', count='exact').execute()
print(f"Lluvia: {result.count}")

result = supabase.table('meta_landcover').select('id', count='exact').execute()
print(f"Landcover: {result.count}")

# Amenazas
result = supabase.table('amenaza_dga').select('id', count='exact').execute()
print(f"DGA: {result.count}")

result = supabase.table('amenaza_inundaciones_hist').select('id', count='exact').execute()
print(f"Inundaciones históricas: {result.count}")

result = supabase.table('amenaza_reportes_ciudadanos').select('id', count='exact').execute()
print(f"Reportes ciudadanos: {result.count}")

print("="*60)
