import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../web/.env.local'))

def check_connectivity(source, target):
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_DB_HOST'),
        port=os.getenv('SUPABASE_DB_PORT'),
        database='postgres',
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD')
    )
    cur = conn.cursor()
    
    query = """
      SELECT * FROM pgr_dijkstra(
        'SELECT id, source, target, length_m as cost FROM infra_aristas WHERE length_m IS NOT NULL AND length_m > 0',
        %s::BIGINT,
        %s::BIGINT,
        false
      )
    """
    
    print(f"Checking connectivity from {source} to {target}...")
    try:
        cur.execute(query, (source, target))
        rows = cur.fetchall()
        if rows:
            print(f"✅ Path found! {len(rows)} segments.")
            for row in rows[:5]:
                print(row)
        else:
            print("❌ No path found.")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_connectivity(371620, 397280)
