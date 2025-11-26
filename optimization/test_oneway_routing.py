#!/usr/bin/env python3
"""
Test one-way street routing by finding a one-way street and testing routing through it
"""
import os
import sys
import socket
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Connection config
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': int(os.getenv('SUPABASE_DB_PORT', 6543)),
    'database': 'postgres',
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos."""
    host = DB_CONFIG['host']
    try:
        # Force IPv4 resolution
        host_ip = socket.gethostbyname(host)
    except Exception as e:
        host_ip = '18.213.155.45'
        
    params = DB_CONFIG.copy()
    params['host'] = host_ip
    return psycopg2.connect(**params)

conn = get_db_connection()
cur = conn.cursor(cursor_factory=RealDictCursor)

# Find a one-way street with both source and target nodes having other connections
print("Finding a suitable one-way street for testing...")
cur.execute("""
    WITH oneway_edges AS (
        SELECT 
            a.id,
            a.source,
            a.target,
            a.highway,
            a.tags->>'name' as street_name,
            ST_AsText(a.geom) as geom_wkt
        FROM infra_aristas a
        WHERE a.tags->>'oneway' = 'yes'
        AND a.highway IN ('residential', 'secondary', 'tertiary')
        LIMIT 100
    ),
    edges_with_connections AS (
        SELECT 
            oe.*,
            (SELECT COUNT(*) FROM infra_aristas WHERE source = oe.source OR target = oe.source) as source_connections,
            (SELECT COUNT(*) FROM infra_aristas WHERE source = oe.target OR target = oe.target) as target_connections
        FROM oneway_edges oe
    )
    SELECT *
    FROM edges_with_connections
    WHERE source_connections > 2 AND target_connections > 2
    LIMIT 5;
""")

print("\nOne-way streets suitable for testing:")
print("=" * 80)
for row in cur.fetchall():
    print(f"Edge ID: {row['id']}")
    print(f"  Street: {row['street_name'] or 'unnamed'}")
    print(f"  Highway type: {row['highway']}")
    print(f"  Source node: {row['source']} (connections: {row['source_connections']})")
    print(f"  Target node: {row['target']} (connections: {row['target_connections']})")
    print(f"  Direction: {row['source']} → {row['target']} (one-way)")
    print()

# Test pgr_dijkstra with directed routing
print("\nTesting pgr_dijkstra with directed routing on a one-way street:")
print("=" * 80)

cur.execute("""
    SELECT 
        a.id,
        a.source,
        a.target,
        a.tags->>'oneway' as oneway,
        a.tags->>'name' as street_name
    FROM infra_aristas a
    WHERE a.tags->>'oneway' = 'yes'
    AND a.highway IN ('residential', 'secondary', 'tertiary')
    LIMIT 1;
""")

test_edge = cur.fetchone()
if test_edge:
    print(f"Test edge: {test_edge['id']}")
    print(f"  Source: {test_edge['source']}, Target: {test_edge['target']}")
    print(f"  Oneway: {test_edge['oneway']}")
    print(f"  Street: {test_edge['street_name'] or 'unnamed'}")
    
    # Try routing in the allowed direction (source -> target)
    print(f"\nTest 1: Routing in ALLOWED direction ({test_edge['source']} → {test_edge['target']})")
    try:
        cur.execute("""
            SELECT COUNT(*) as path_length
            FROM pgr_dijkstra(
                'SELECT id, source, target, length_m as cost,
                 CASE 
                   WHEN tags->>''oneway'' = ''yes'' THEN -1
                   WHEN tags->>''oneway'' = ''-1'' THEN length_m
                   ELSE length_m
                 END as reverse_cost
                 FROM infra_aristas WHERE length_m IS NOT NULL',
                %s,
                %s,
                true
            );
        """, (test_edge['source'], test_edge['target']))
        result = cur.fetchone()
        print(f"  ✓ Route found with {result['path_length']} segments")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Try routing in the forbidden direction (target -> source)
    print(f"\nTest 2: Routing in FORBIDDEN direction ({test_edge['target']} → {test_edge['source']})")
    try:
        cur.execute("""
            SELECT COUNT(*) as path_length
            FROM pgr_dijkstra(
                'SELECT id, source, target, length_m as cost,
                 CASE 
                   WHEN tags->>''oneway'' = ''yes'' THEN -1
                   WHEN tags->>''oneway'' = ''-1'' THEN length_m
                   ELSE length_m
                 END as reverse_cost
                 FROM infra_aristas WHERE length_m IS NOT NULL',
                %s,
                %s,
                true
            );
        """, (test_edge['target'], test_edge['source']))
        result = cur.fetchone()
        if result['path_length'] > 0:
            print(f"  ✓ Route found with {result['path_length']} segments (takes alternate path)")
        else:
            print(f"  ✗ No route found (nodes may not be connected)")
    except Exception as e:
        print(f"  ✗ Error: {e}")

conn.close()
print("\n" + "=" * 80)
print("Testing complete!")
