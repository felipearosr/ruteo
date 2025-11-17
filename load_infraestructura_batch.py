"""
Script para cargar infraestructura (red vial) a Supabase en lotes.

Procesa el archivo GeoJSON grande de infraestructura y lo carga en lotes pequeños
para evitar timeouts y problemas de memoria.

Prerrequisitos:
  - Haber ejecutado sql/schema.sql para crear las tablas
  - Tener las variables de entorno configuradas en .env
  - Haber ejecutado infraestructura/osm_infra_etl.py para generar el GeoJSON

Uso:
  python load_infraestructura_batch.py
"""
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()

# Configuración de lotes
BATCH_SIZE = 100  # Número de aristas por lote
MAX_FEATURES = 5000  # Máximo de features a procesar (para limitar en pruebas, None para todo)


def get_supabase_client():
    """Crear cliente de Supabase usando la API REST."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY deben estar configurados en .env")
    
    return create_client(url, key)


def load_infraestructura_batched(supabase: Client):
    """Cargar infraestructura en lotes."""
    print("\n" + "="*60)
    print("Cargando infraestructura (red vial) en lotes...")
    print("="*60)
    
    geojson_path = 'infraestructura/infraestructura.geojson'
    if not os.path.exists(geojson_path):
        print(f"ERROR: {geojson_path} no existe. Ejecuta main.py primero.")
        return
    
    print(f"Leyendo {geojson_path}...")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    total = len(features)
    
    if MAX_FEATURES and total > MAX_FEATURES:
        print(f"NOTA: Limitando a {MAX_FEATURES} features de {total} para prueba")
        features = features[:MAX_FEATURES]
        total = len(features)
    
    print(f"Total de aristas a procesar: {total}")
    print(f"Tamaño de lote: {BATCH_SIZE}")
    print(f"Número de lotes: {(total + BATCH_SIZE - 1) // BATCH_SIZE}")
    
    # Paso 1: Extraer y cargar nodos únicos
    print("\n--- Paso 1/3: Extrayendo nodos únicos ---")
    nodes_map = {}  # (lon, lat) -> temp_id
    node_id = 1
    
    for feat in features:
        coords = feat['geometry']['coordinates']
        for coord in coords:
            key = (round(coord[0], 7), round(coord[1], 7))
            if key not in nodes_map:
                nodes_map[key] = node_id
                node_id += 1
    
    print(f"Nodos únicos encontrados: {len(nodes_map)}")
    
    # Cargar nodos en lotes
    print("\n--- Paso 2/3: Cargando nodos a Supabase ---")
    nodes_list = list(nodes_map.keys())
    nodes_loaded = 0
    
    for i in range(0, len(nodes_list), BATCH_SIZE):
        batch = nodes_list[i:i + BATCH_SIZE]
        records = []
        
        for lon, lat in batch:
            records.append({
                'geom': f'POINT({lon} {lat})'
            })
        
        try:
            result = supabase.table('infra_nodos').insert(records).execute()
            nodes_loaded += len(records)
            print(f"  Nodos cargados: {nodes_loaded}/{len(nodes_list)}", end='\r')
            time.sleep(0.1)  # Pequeña pausa para no saturar la API
        except Exception as e:
            print(f"\n  ERROR en lote de nodos {i//BATCH_SIZE + 1}: {e}")
            # Continuar con el siguiente lote
    
    print(f"\n✓ Total nodos cargados: {nodes_loaded}")
    
    # Obtener los IDs reales de los nodos desde Supabase
    print("\n--- Obteniendo IDs de nodos desde Supabase ---")
    print("  Esto puede tardar unos segundos...")
    
    # Consultar nodos en lotes para evitar límites de API
    # Usar ST_AsGeoJSON para obtener coordenadas en formato JSON
    supabase_nodes = []
    offset = 0
    limit = 1000
    
    while True:
        # Solicitar id y las coordenadas extraídas con ST_X y ST_Y
        result = supabase.table('infra_nodos').select('id,geom').range(offset, offset + limit - 1).execute()
        if not result.data:
            break
        supabase_nodes.extend(result.data)
        offset += limit
        print(f"  Obtenidos: {len(supabase_nodes)} nodos", end='\r')
        if len(result.data) < limit:
            break
    
    print(f"\n✓ Total nodos obtenidos: {len(supabase_nodes)}")
    
    # DEBUG: Mostrar formato de la primera geometría
    if supabase_nodes:
        print(f"  Formato de geometría ejemplo: {type(supabase_nodes[0].get('geom'))} = {supabase_nodes[0].get('geom')}")

    
    # Crear mapeo de coordenadas a IDs reales
    # NOTA: Supabase devuelve geometrías en formato GeoJSON por defecto
    coord_to_id = {}
    for node in supabase_nodes:
        node_id = node.get('id')
        geom = node.get('geom')
        
        # Intentar diferentes formatos
        if isinstance(geom, dict) and 'coordinates' in geom:
            # Formato GeoJSON
            lon, lat = geom['coordinates']
            key = (round(lon, 7), round(lat, 7))
            coord_to_id[key] = node_id
        elif isinstance(geom, str):
            # Formato WKT: POINT(lon lat)
            if 'POINT' in geom:
                coords_part = geom.split('(')[1].split(')')[0]
                lon, lat = map(float, coords_part.split())
                key = (round(lon, 7), round(lat, 7))
                coord_to_id[key] = node_id
    
    print(f"Mapeo creado: {len(coord_to_id)} coordenadas -> IDs")
    
    if len(coord_to_id) == 0:
        print("\nERROR: No se pudo crear el mapeo de coordenadas a IDs")
        print("Ejemplo de geometría recibida:", supabase_nodes[0].get('geom') if supabase_nodes else "N/A")
        return

    
    # Paso 3: Cargar aristas en lotes
    print("\n--- Paso 3/3: Cargando aristas a Supabase ---")
    aristas_loaded = 0
    aristas_skipped = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = features[i:i + BATCH_SIZE]
        records = []
        
        for feat in batch:
            coords = feat['geometry']['coordinates']
            if len(coords) < 2:
                aristas_skipped += 1
                continue
            
            # Primer y último punto
            first = (round(coords[0][0], 7), round(coords[0][1], 7))
            last = (round(coords[-1][0], 7), round(coords[-1][1], 7))
            
            source_id = coord_to_id.get(first)
            target_id = coord_to_id.get(last)
            
            if not source_id or not target_id:
                aristas_skipped += 1
                continue
            
            # Crear LineString WKT
            line_coords = ','.join([f'{c[0]} {c[1]}' for c in coords])
            line_wkt = f'LINESTRING({line_coords})'
            
            props = feat.get('properties', {})
            
            records.append({
                'source': source_id,
                'target': target_id,
                'geom': line_wkt,
                'highway': props.get('highway', 'unclassified'),
                'maxspeed': props.get('maxspeed'),
                'tags': props
            })
        
        if records:
            try:
                result = supabase.table('infra_aristas').insert(records).execute()
                aristas_loaded += len(records)
                print(f"  Aristas cargadas: {aristas_loaded}/{total} (omitidas: {aristas_skipped})", end='\r')
                time.sleep(0.1)  # Pequeña pausa
            except Exception as e:
                print(f"\n  ERROR en lote de aristas {i//BATCH_SIZE + 1}: {e}")
                # Continuar con el siguiente lote
    
    print(f"\n✓ Total aristas cargadas: {aristas_loaded}")
    print(f"  Aristas omitidas (sin nodos válidos): {aristas_skipped}")
    
    # Calcular longitudes y costos
    print("\n--- Calculando longitudes y costos ---")
    try:
        # Usar la función RPC de Supabase para ejecutar la función SQL
        result = supabase.rpc('infra_calcular_longitudes_costs', {}).execute()
        print("✓ Longitudes y costos calculados")
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo ejecutar la función de cálculo: {e}")
        print("Puedes ejecutarla manualmente desde el SQL Editor:")
        print("  SELECT infra_calcular_longitudes_costs();")


def main():
    print("="*60)
    print("CARGA DE INFRAESTRUCTURA EN LOTES")
    print("="*60)
    
    if MAX_FEATURES:
        print(f"\nMODO PRUEBA: Se cargarán máximo {MAX_FEATURES} features")
        print("Para cargar todo, edita MAX_FEATURES = None en este script\n")
    
    print("Conectando a Supabase via API REST...")
    try:
        supabase = get_supabase_client()
        print("✓ Cliente creado exitosamente\n")
    except Exception as e:
        print(f"ERROR: No se pudo crear el cliente de Supabase: {e}")
        return
    
    try:
        load_infraestructura_batched(supabase)
        
        print("\n" + "="*60)
        print("✓ INFRAESTRUCTURA CARGADA EXITOSAMENTE")
        print("="*60)
        print("\nPuedes verificar los datos en:")
        print("  - Table Editor > infra_nodos")
        print("  - Table Editor > infra_aristas")
        
    except Exception as e:
        print(f"\nERROR durante la carga: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
