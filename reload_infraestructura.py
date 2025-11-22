"""
Script para recargar TODA la infraestructura a Supabase.
Limpia las tablas existentes y carga las 133,905 calles del GeoJSON.
"""
import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Crear conexión a la base de datos Supabase."""
    port = '5432'  # Session pooler para pgRouting
    host = '18.213.155.45'  # IP directa que funciona
    
    print(f"Conectando a {host}:{port}...")
    
    return psycopg2.connect(
        host=host,
        database='postgres',
        user='postgres.eqjzlgbjgwbnvqzbomsn',
        password='femaarroD4rK',
        port=int(port)
    )

def reload_infraestructura():
    """Recargar toda la infraestructura."""
    print("="*70)
    print("RECARGA COMPLETA DE INFRAESTRUCTURA")
    print("="*70)
    
    geojson_path = 'infraestructura/infraestructura.geojson'
    if not os.path.exists(geojson_path):
        print(f"ERROR: {geojson_path} no existe")
        return
    
    print(f"\nCargando {geojson_path}...")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"✓ {len(features):,} features en el archivo")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # PASO 1: Limpiar tablas existentes
        print("\nPASO 1/4: Limpiando tablas existentes...")
        cur.execute("TRUNCATE TABLE infra_aristas CASCADE")
        cur.execute("TRUNCATE TABLE infra_nodos CASCADE")
        conn.commit()
        print("✓ Tablas limpiadas")
        
        # PASO 2: Extraer nodos únicos
        print("\nPASO 2/4: Extrayendo nodos únicos...")
        nodes_set = set()
        for i, feat in enumerate(features):
            if i % 10000 == 0:
                print(f"  Procesando feature {i:,}/{len(features):,}")
            coords = feat['geometry']['coordinates']
            for coord in coords:
                # Redondear a 7 decimales para evitar duplicados por precision
                lon = round(coord[0], 7)
                lat = round(coord[1], 7)
                nodes_set.add((lon, lat))
        
        print(f"✓ {len(nodes_set):,} nodos únicos encontrados")
        
        # PASO 3: Insertar nodos
        print("\nPASO 3/4: Insertando nodos en la base de datos...")
        node_values = [(f'SRID=4326;POINT({lon} {lat})',) for lon, lat in nodes_set]
        
        # Insertar en batches de 1000
        batch_size = 1000
        for i in range(0, len(node_values), batch_size):
            batch = node_values[i:i+batch_size]
            execute_values(
                cur,
                "INSERT INTO infra_nodos (geom) VALUES %s",
                batch
            )
            if i % 10000 == 0:
                print(f"  Insertados {i:,}/{len(node_values):,} nodos")
        conn.commit()
        print(f"✓ {len(node_values):,} nodos insertados")
        
        # PASO 4: Crear índice de nodos
        print("\nPASO 4/4: Creando índice de coordenadas a IDs...")
        cur.execute("""
            SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat 
            FROM infra_nodos
        """)
        node_map = {(round(row[1], 7), round(row[2], 7)): row[0] for row in cur.fetchall()}
        print(f"✓ Índice creado con {len(node_map):,} nodos")
        
        # PASO 5: Insertar aristas
        print("\nPASO 5/5: Insertando aristas...")
        aristas_batch = []
        batch_size = 1000
        inserted = 0
        skipped = 0
        
        for i, feat in enumerate(features):
            if i % 10000 == 0:
                print(f"  Procesando arista {i:,}/{len(features):,} (insertadas: {inserted:,}, omitidas: {skipped:,})")
            
            coords = feat['geometry']['coordinates']
            if len(coords) < 2:
                skipped += 1
                continue
            
            # Primer y último punto (source y target)
            first = (round(coords[0][0], 7), round(coords[0][1], 7))
            last = (round(coords[-1][0], 7), round(coords[-1][1], 7))
            
            source_id = node_map.get(first)
            target_id = node_map.get(last)
            
            if not source_id or not target_id:
                skipped += 1
                continue
            
            # Crear LineString WKT
            line_wkt = 'SRID=4326;LINESTRING(' + ','.join([f'{c[0]} {c[1]}' for c in coords]) + ')'
            
            props = feat.get('properties', {})
            highway = props.get('highway', 'unclassified')
            maxspeed = props.get('maxspeed')
            tags = json.dumps(props)
            
            aristas_batch.append((source_id, target_id, line_wkt, highway, maxspeed, tags))
            
            # Insertar en batches
            if len(aristas_batch) >= batch_size:
                execute_values(
                    cur,
                    """
                    INSERT INTO infra_aristas (source, target, geom, highway, maxspeed, tags)
                    VALUES %s
                    """,
                    aristas_batch
                )
                inserted += len(aristas_batch)
                aristas_batch = []
        
        # Insertar último batch
        if aristas_batch:
            execute_values(
                cur,
                """
                INSERT INTO infra_aristas (source, target, geom, highway, maxspeed, tags)
                VALUES %s
                """,
                aristas_batch
            )
            inserted += len(aristas_batch)
        
        conn.commit()
        print(f"✓ {inserted:,} aristas insertadas ({skipped:,} omitidas)")
        
        # PASO 6: Calcular longitudes y costos
        print("\nPASO 6/6: Calculando longitudes y costos...")
        cur.execute("SELECT infra_calcular_longitudes_costs()")
        conn.commit()
        print("✓ Longitudes calculadas")
        
        # Mostrar estadísticas finales
        print("\n" + "="*70)
        print("ESTADÍSTICAS FINALES")
        print("="*70)
        
        cur.execute("SELECT COUNT(*) FROM infra_nodos")
        total_nodes = cur.fetchone()[0]
        print(f"Nodos totales: {total_nodes:,}")
        
        cur.execute("SELECT COUNT(*) FROM infra_aristas")
        total_edges = cur.fetchone()[0]
        print(f"Aristas totales: {total_edges:,}")
        
        cur.execute("SELECT COUNT(*) FROM infra_aristas WHERE length_m IS NOT NULL")
        edges_with_length = cur.fetchone()[0]
        print(f"Aristas con longitud: {edges_with_length:,}")
        
        cur.execute("""
            SELECT COUNT(DISTINCT source) 
            FROM infra_aristas 
            WHERE length_m IS NOT NULL AND length_m > 0
        """)
        connected_nodes = cur.fetchone()[0]
        print(f"Nodos conectados: {connected_nodes:,}")
        
        print("\n" + "="*70)
        print("✓ RECARGA COMPLETADA EXITOSAMENTE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    reload_infraestructura()
