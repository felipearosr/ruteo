"""
Script para cargar datos generados por ETL a Supabase.

Lee los archivos JSON/GeoJSON generados y los inserta en las tablas correspondientes
usando psycopg2 para conexión directa a PostgreSQL.

Prerrequisitos:
  - Ejecutar sql/schema.sql primero para crear las tablas
  - Tener las variables de entorno configuradas en .env
  - Haber ejecutado main.py para generar los archivos JSON/GeoJSON

Uso:
  python load_to_supabase.py
"""
import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_db_connection():
    """Crear conexión a la base de datos Supabase."""
    # Intentar usar puerto del pooler (6543) si está configurado, sino usar 5432
    port = os.getenv('SUPABASE_DB_PORT', '6543')
    host = os.getenv('SUPABASE_DB_HOST')
    
    print(f"Intentando conectar a {host}:{port}...")
    
    return psycopg2.connect(
        host=host,
        database=os.getenv('SUPABASE_DB_NAME'),
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        port=int(port)
    )



def load_infraestructura(conn):
    """Cargar datos de infraestructura (red vial) desde GeoJSON."""
    print("\n" + "="*60)
    print("Cargando infraestructura (red vial)...")
    print("="*60)
    
    geojson_path = 'infraestructura/infraestructura.geojson'
    if not os.path.exists(geojson_path):
        print(f"ADVERTENCIA: {geojson_path} no existe. Ejecuta main.py primero.")
        return
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"Procesando {len(features)} aristas...")
    
    cur = conn.cursor()
    
    # Primero, extraer y cargar nodos únicos
    print("Extrayendo nodos únicos...")
    nodes_set = set()
    for feat in features:
        coords = feat['geometry']['coordinates']
        for coord in coords:
            nodes_set.add((coord[0], coord[1]))
    
    print(f"Insertando {len(nodes_set)} nodos...")
    node_values = [(f'SRID=4326;POINT({lon} {lat})',) for lon, lat in nodes_set]
    execute_values(
        cur,
        "INSERT INTO infra_nodos (geom) VALUES %s ON CONFLICT DO NOTHING",
        node_values
    )
    conn.commit()
    
    # Crear índice temporal de coordenadas a IDs de nodos
    print("Creando índice de nodos...")
    cur.execute("""
        SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat 
        FROM infra_nodos
    """)
    node_map = {(round(row[1], 7), round(row[2], 7)): row[0] for row in cur.fetchall()}
    
    # Insertar aristas
    print("Insertando aristas...")
    aristas_values = []
    for feat in features:
        coords = feat['geometry']['coordinates']
        if len(coords) < 2:
            continue
        
        # Primer y último punto
        first = (round(coords[0][0], 7), round(coords[0][1], 7))
        last = (round(coords[-1][0], 7), round(coords[-1][1], 7))
        
        source_id = node_map.get(first)
        target_id = node_map.get(last)
        
        if not source_id or not target_id:
            continue
        
        # Crear LineString WKT
        line_wkt = 'SRID=4326;LINESTRING(' + ','.join([f'{c[0]} {c[1]}' for c in coords]) + ')'
        
        props = feat.get('properties', {})
        highway = props.get('highway', 'unclassified')
        maxspeed = props.get('maxspeed')
        tags = json.dumps(props)
        
        aristas_values.append((source_id, target_id, line_wkt, highway, maxspeed, tags))
    
    print(f"Insertando {len(aristas_values)} aristas...")
    execute_values(
        cur,
        """
        INSERT INTO infra_aristas (source, target, geom, highway, maxspeed, tags)
        VALUES %s
        """,
        aristas_values
    )
    conn.commit()
    
    # Calcular longitudes y costos
    print("Calculando longitudes y costos...")
    cur.execute("SELECT infra_calcular_longitudes_costs()")
    conn.commit()
    
    cur.close()
    print("✓ Infraestructura cargada exitosamente")


def load_metadata_elevacion(conn):
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
    
    cur = conn.cursor()
    values = [
        (f"SRID=4326;POINT({item['lon']} {item['lat']})",
         item['elev_m'],
         item.get('source'),
         json.dumps(item))
        for item in data
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO meta_elevacion (geom, elev_m, source, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} registros de elevación cargados")


def load_metadata_lluvia(conn):
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
    
    cur = conn.cursor()
    values = [
        (f"SRID=4326;POINT({item['lon']} {item['lat']})",
         item.get('precip_mm'),
         item.get('observed_at'),
         item.get('source'),
         json.dumps(item))
        for item in data
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO meta_lluvia (geom, precip_mm, observed_at, source, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} registros de lluvia cargados")


def load_metadata_landcover(conn):
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
    
    cur = conn.cursor()
    values = []
    for item in data:
        geom = item['geometry']
        if geom['type'] == 'Point':
            geom_wkt = f"SRID=4326;POINT({geom['coordinates'][0]} {geom['coordinates'][1]})"
        else:
            geom_wkt = f"SRID=4326;{geom['type'].upper()}(...)"  # Simplificado
        
        values.append((
            geom_wkt,
            item.get('class'),
            item.get('confidence'),
            item.get('source'),
            json.dumps(item)
        ))
    
    execute_values(
        cur,
        """
        INSERT INTO meta_landcover (geom, class, confidence, source, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} registros de landcover cargados")


def load_amenaza_dga(conn):
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
    
    cur = conn.cursor()
    values = [
        (f"SRID=4326;POINT({item['lon']} {item['lat']})",
         item.get('station_id'),
         json.dumps(item.get('parameter')),
         item.get('last_update'),
         json.dumps(item))
        for item in data
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO amenaza_dga (geom, station_id, parameter, last_update, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} estaciones DGA cargadas")


def load_amenaza_inundaciones(conn):
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
    
    cur = conn.cursor()
    values = []
    for item in data:
        geom = item['geometry']
        if geom['type'] == 'Polygon':
            coords_str = ','.join([f"{c[0]} {c[1]}" for c in geom['coordinates'][0]])
            geom_wkt = f"SRID=4326;POLYGON(({coords_str}))"
        else:
            geom_wkt = f"SRID=4326;POINT(0 0)"  # Fallback
        
        event_date = item.get('event_date', {})
        values.append((
            geom_wkt,
            item.get('source'),
            f"[{event_date.get('lower')},{event_date.get('upper')}]",
            item.get('severity'),
            json.dumps(item)
        ))
    
    execute_values(
        cur,
        """
        INSERT INTO amenaza_inundaciones_hist (geom, source, event_date, severity, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} zonas de inundación cargadas")


def load_amenaza_reportes(conn):
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
    
    cur = conn.cursor()
    values = [
        (f"SRID=4326;POINT({item['lon']} {item['lat']})",
         item.get('reported_at'),
         item.get('reporter'),
         item.get('description'),
         json.dumps(item.get('media')),
         json.dumps(item))
        for item in data
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO amenaza_reportes_ciudadanos (geom, reported_at, reporter, description, media, properties)
        VALUES %s
        """,
        values
    )
    conn.commit()
    cur.close()
    print(f"✓ {len(data)} reportes ciudadanos cargados")


def main():
    print("Conectando a Supabase...")
    try:
        conn = get_db_connection()
        print("✓ Conexión exitosa")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a Supabase: {e}")
        print("\nVerifica que:")
        print("  1. El archivo .env tenga las credenciales correctas")
        print("  2. Hayas ejecutado sql/schema.sql para crear las tablas")
        return
    
    try:
        # Cargar datos en orden
        load_infraestructura(conn)
        load_metadata_elevacion(conn)
        load_metadata_lluvia(conn)
        load_metadata_landcover(conn)
        load_amenaza_dga(conn)
        load_amenaza_inundaciones(conn)
        load_amenaza_reportes(conn)
        
        print("\n" + "="*60)
        print("✓ TODOS LOS DATOS CARGADOS EXITOSAMENTE")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR durante la carga: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
