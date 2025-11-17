"""
Script para cargar datos generados por ETL a Supabase usando la API REST.

Alternativa a load_to_supabase.py cuando la conexión directa PostgreSQL no funciona
(problemas con IPv6, firewall, etc).

Prerrequisitos:
  - Ejecutar sql/schema.sql primero para crear las tablas (desde el dashboard web)
  - Tener las variables de entorno configuradas en .env
  - Haber ejecutado main.py para generar los archivos JSON/GeoJSON

Uso:
  python load_to_supabase_api.py
"""
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_supabase_client():
    """Crear cliente de Supabase usando la API REST."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY deben estar configurados en .env")
    
    return create_client(url, key)


def load_metadata_elevacion(supabase: Client):
    """Cargar datos de elevación."""
    print("\n" + "="*60)
    print("Cargando metadata: elevación...")
    print("="*60)
    
    json_path = 'metadata/elevacion.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            'geom': f'POINT({item["lon"]} {item["lat"]})',
            'elev_m': item['elev_m'],
            'source': item.get('source'),
            'properties': item
        })
    
    # Insertar en lotes
    result = supabase.table('meta_elevacion').insert(records).execute()
    print(f"✓ {len(records)} registros de elevación cargados")


def load_metadata_lluvia(supabase: Client):
    """Cargar datos de lluvia."""
    print("\n" + "="*60)
    print("Cargando metadata: lluvia...")
    print("="*60)
    
    json_path = 'metadata/lluvia.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            'geom': f'POINT({item["lon"]} {item["lat"]})',
            'precip_mm': item.get('precip_mm'),
            'observed_at': item.get('observed_at'),
            'source': item.get('source'),
            'properties': item
        })
    
    result = supabase.table('meta_lluvia').insert(records).execute()
    print(f"✓ {len(records)} registros de lluvia cargados")


def load_metadata_landcover(supabase: Client):
    """Cargar datos de landcover."""
    print("\n" + "="*60)
    print("Cargando metadata: landcover...")
    print("="*60)
    
    json_path = 'metadata/landcover.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        geom = item['geometry']
        if geom['type'] == 'Point':
            geom_wkt = f"POINT({geom['coordinates'][0]} {geom['coordinates'][1]})"
        else:
            geom_wkt = f"POINT(0 0)"  # Fallback
        
        records.append({
            'geom': geom_wkt,
            'class': item.get('class'),
            'confidence': item.get('confidence'),
            'source': item.get('source'),
            'properties': item
        })
    
    result = supabase.table('meta_landcover').insert(records).execute()
    print(f"✓ {len(records)} registros de landcover cargados")


def load_amenaza_dga(supabase: Client):
    """Cargar datos de estaciones DGA."""
    print("\n" + "="*60)
    print("Cargando amenazas: estaciones DGA...")
    print("="*60)
    
    json_path = 'amenazas/dga_estaciones.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            'geom': f'POINT({item["lon"]} {item["lat"]})',
            'station_id': item.get('station_id'),
            'parameter': item.get('parameter'),
            'last_update': item.get('last_update'),
            'properties': item
        })
    
    result = supabase.table('amenaza_dga').insert(records).execute()
    print(f"✓ {len(records)} estaciones DGA cargadas")


def load_amenaza_inundaciones(supabase: Client):
    """Cargar datos de inundaciones históricas."""
    print("\n" + "="*60)
    print("Cargando amenazas: inundaciones históricas...")
    print("="*60)
    
    json_path = 'amenazas/inundaciones_hist.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        geom = item['geometry']
        if geom['type'] == 'Polygon':
            coords_str = ','.join([f"{c[0]} {c[1]}" for c in geom['coordinates'][0]])
            geom_wkt = f"POLYGON(({coords_str}))"
        else:
            geom_wkt = f"POINT(0 0)"
        
        event_date = item.get('event_date', {})
        records.append({
            'geom': geom_wkt,
            'source': item.get('source'),
            'event_date': f"[{event_date.get('lower')},{event_date.get('upper')}]",
            'severity': item.get('severity'),
            'properties': item
        })
    
    result = supabase.table('amenaza_inundaciones_hist').insert(records).execute()
    print(f"✓ {len(records)} zonas de inundación cargadas")


def load_amenaza_reportes(supabase: Client):
    """Cargar datos de reportes ciudadanos."""
    print("\n" + "="*60)
    print("Cargando amenazas: reportes ciudadanos...")
    print("="*60)
    
    json_path = 'amenazas/reportes_ciudadanos.json'
    if not os.path.exists(json_path):
        print(f"ADVERTENCIA: {json_path} no existe.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            'geom': f'POINT({item["lon"]} {item["lat"]})',
            'reported_at': item.get('reported_at'),
            'reporter': item.get('reporter'),
            'description': item.get('description'),
            'media': item.get('media'),
            'properties': item
        })
    
    result = supabase.table('amenaza_reportes_ciudadanos').insert(records).execute()
    print(f"✓ {len(records)} reportes ciudadanos cargados")


def main():
    print("Conectando a Supabase via API REST...")
    try:
        supabase = get_supabase_client()
        print("✓ Cliente creado exitosamente")
    except Exception as e:
        print(f"ERROR: No se pudo crear el cliente de Supabase: {e}")
        print("\nVerifica que:")
        print("  1. El archivo .env tenga SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY correctos")
        print("  2. Hayas ejecutado sql/schema.sql para crear las tablas (desde el dashboard web)")
        return
    
    try:
        # Cargar datos (sin infraestructura por ahora, es muy pesado para la API REST)
        print("\nNOTA: Este script carga metadata y amenazas.")
        print("La infraestructura (red vial) es muy grande y debe cargarse vía PostgreSQL directo")
        print("o desde el dashboard de Supabase.\n")
        
        load_metadata_elevacion(supabase)
        load_metadata_lluvia(supabase)
        load_metadata_landcover(supabase)
        load_amenaza_dga(supabase)
        load_amenaza_inundaciones(supabase)
        load_amenaza_reportes(supabase)
        
        print("\n" + "="*60)
        print("✓ DATOS DE METADATA Y AMENAZAS CARGADOS")
        print("="*60)
        print("\nPara cargar la infraestructura (red vial):")
        print("  1. Ve al SQL Editor en Supabase Dashboard")
        print("  2. Usa la función de importación de datos o ejecuta load_infra.sql")
        
    except Exception as e:
        print(f"\nERROR durante la carga: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
