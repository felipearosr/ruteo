import os
import psycopg2
from dotenv import load_dotenv
import random

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../web/.env.local'))

def find_distant_connected_nodes():
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_DB_HOST'),
        port=os.getenv('SUPABASE_DB_PORT'),
        database='postgres',
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD')
    )
    cur = conn.cursor()
    
    print("Searching for distant connected nodes...")
    
    # Get min/max coordinates to understand the bounding box
    cur.execute("SELECT ST_XMin(ST_Extent(geom)), ST_YMin(ST_Extent(geom)), ST_XMax(ST_Extent(geom)), ST_YMax(ST_Extent(geom)) FROM infra_nodos")
    bbox = cur.fetchone()
    print(f"BBox: {bbox}")
    
    # Try to find nodes that are at least 0.05 degrees apart (approx 5km)
    # We'll pick a random start node and look for a far end node
    
    for _ in range(20): # Try 20 source nodes
        # Get a random node
        cur.execute("SELECT id, geom FROM infra_nodos ORDER BY RANDOM() LIMIT 1")
        start_node = cur.fetchone()
        if not start_node:
            continue
            
        start_id = start_node[0]
        
        # Find 50 nodes far away
        query = """
            SELECT id, ST_Distance(geom, %s::geometry) as dist 
            FROM infra_nodos 
            WHERE ST_Distance(geom, %s::geometry) > 0.03
            ORDER BY RANDOM() 
            LIMIT 50
        """
        cur.execute(query, (start_node[1], start_node[1]))
        targets = cur.fetchall()
        
        if not targets:
            continue
            
        target_ids = [t[0] for t in targets]
        print(f"Testing source {start_id} against {len(target_ids)} targets...")
        
        # Check connectivity to ANY of the targets
        check_query = """
          SELECT * FROM pgr_dijkstra(
            'SELECT id, source, target, length_m as cost FROM infra_aristas WHERE length_m IS NOT NULL AND length_m > 0',
            %s::BIGINT,
            %s::BIGINT[],
            false
          )
          ORDER BY cost DESC
          LIMIT 1
        """
        try:
            cur.execute(check_query, (start_id, target_ids))
            result = cur.fetchone()
            if result:
                # result is (seq, path_seq, node, edge, cost, agg_cost)
                # But pgr_dijkstra with array targets returns (seq, path_seq, end_vid, node, edge, cost, agg_cost)
                # Actually, let's check the columns returned or just use the node from the last row
                
                # Wait, pgr_dijkstra(sql, source, targets_array) returns (seq, path_seq, end_vid, node, edge, cost, agg_cost)
                # We want the end_vid of the path found.
                
                # Let's just get the target that was reached.
                # The query returns the path. The last row for a path has edge = -1.
                # But we are ordering by cost DESC, so we might get the longest path found?
                
                # Let's simplify: just get one path.
                end_vid = result['end_vid'] if isinstance(result, dict) else result[2] 
                # We need to be careful with the return structure.
                
                print(f"✅ Found connected pair! {start_id} -> {end_vid}")
                conn.close()
                return start_id, end_vid
            else:
                print("❌ No paths found to any target")
        except Exception as e:
            print(f"Error checking connectivity: {e}")
            conn.rollback()
            
    print("Could not find a good pair after attempts.")
    conn.close()
    return None, None

if __name__ == "__main__":
    find_distant_connected_nodes()
