import os
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv('/home/faros/ruteo/.env')

# Configuration
SIMULATION_ID = '5bfd6d01-22fc-4f06-8706-69eeefc67dbb'
DB_HOST = os.getenv('SUPABASE_DB_HOST')
DB_PORT = os.getenv('SUPABASE_DB_PORT', '5432')
DB_NAME = os.getenv('SUPABASE_DB_NAME')
DB_USER = os.getenv('SUPABASE_DB_USER')
DB_PASS = os.getenv('SUPABASE_DB_PASSWORD')

def get_connection():
    import socket
    try:
        host_ip = socket.gethostbyname(DB_HOST)
        print(f"Resolved {DB_HOST} to {host_ip}")
    except Exception as e:
        print(f"Could not resolve {DB_HOST}: {e}")
        # Fallback to known IPv4 from other scripts
        host_ip = '18.213.155.45'
    
    return psycopg2.connect(
        host=host_ip,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def test_query(query_type, query_sql):
    print(f"\nTesting {query_type} query...")
    conn = get_connection()
    cur = conn.cursor()
    
    start_time = time.time()
    try:
        # We wrap it in EXPLAIN ANALYZE to get execution details without fetching all data
        # But for pgr_dijkstra we might just run it? 
        # Actually, let's just run the inner query which is likely the bottleneck
        # The inner query is the one generating the cost
        
        cur.execute(f"EXPLAIN ANALYZE {query_sql}")
        rows = cur.fetchall()
        for row in rows:
            print(row[0])
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.4f} seconds")
        cur.close()
        conn.close()

# Pre-calculation strategy test
# 1. Find all edges close to failures and calculate penalty
precalc_query = f"""
WITH active_failures AS (
    SELECT 
      CASE 
        WHEN entity_type = 'nodo' THEN (SELECT geom FROM infra_nodos WHERE id = entity_id)
        WHEN entity_type = 'arista' THEN (SELECT geom FROM infra_aristas WHERE id = entity_id)
      END as geom_sim
    FROM sim_fallas_activas 
    WHERE simulation_id = '{SIMULATION_ID}' AND is_failed = true
)
SELECT 
    a.id,
    SUM(5.0 / (ST_Distance(a.geom::geography, f.geom_sim::geography) + 1.0)) as penalty
FROM infra_aristas a
JOIN active_failures f ON ST_DWithin(a.geom, f.geom_sim, 0.001) -- Use index!
GROUP BY a.id
"""

if __name__ == "__main__":
    print("Testing PRE-CALCULATION query...")
    conn = get_connection()
    cur = conn.cursor()
    start_time = time.time()
    try:
        cur.execute(precalc_query)
        rows = cur.fetchall()
        print(f"Found {len(rows)} affected edges.")
        if len(rows) > 0:
            print(f"Sample: {rows[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.4f} seconds")
        cur.close()
        conn.close()
