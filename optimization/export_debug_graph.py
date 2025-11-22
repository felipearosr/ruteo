import os
import json
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import socket

# Load env vars
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../web/.env.local'))

# DB Config
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': 5432,
    'database': 'postgres',
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}

def get_db_connection():
    host = DB_CONFIG['host']
    try:
        host_ip = socket.gethostbyname(host)
    except:
        host_ip = '18.213.155.45' # Fallback
        
    params = DB_CONFIG.copy()
    params['host'] = host_ip
    params['port'] = 6543
    params['options'] = '-c prepare_threshold=0'
    return psycopg2.connect(**params)

def export_graph(bbox, output_file):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    xmin, ymin, xmax, ymax = bbox
    print(f"Exporting graph for bbox: {bbox}")
    
    # Fetch Nodes
    cur.execute("""
        SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat
        FROM infra_nodos
        WHERE ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
    """, (xmin, ymin, xmax, ymax))
    nodes = cur.fetchall()
    print(f"Found {len(nodes)} nodes")
    
    # Fetch Edges
    cur.execute("""
        SELECT id, source, target, ST_AsGeoJSON(geom) as geom_json, length_m
        FROM infra_aristas
        WHERE ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
    """, (xmin, ymin, xmax, ymax))
    edges = cur.fetchall()
    print(f"Found {len(edges)} edges")
    
    features = []
    
    # Add Nodes
    for node in nodes:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [node['lon'], node['lat']]
            },
            "properties": {
                "type": "node",
                "id": node['id']
            }
        })
        
    # Add Edges
    for edge in edges:
        features.append({
            "type": "Feature",
            "geometry": json.loads(edge['geom_json']),
            "properties": {
                "type": "edge",
                "id": edge['id'],
                "source": edge['source'],
                "target": edge['target'],
                "length": edge['length_m']
            }
        })
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f)
        
    print(f"Exported to {output_file}")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export graph to GeoJSON')
    # Default to Santiago Centro approx
    parser.add_argument('--bbox', type=float, nargs=4, default=[-70.66, -33.45, -70.64, -33.43],
                        help='Bounding box: xmin ymin xmax ymax')
    parser.add_argument('--output', type=str, default='../web/public/debug_graph.json',
                        help='Output file path')
    
    args = parser.parse_args()
    export_graph(args.bbox, args.output)
