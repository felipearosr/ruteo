import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../web/.env.local'))

def analyze_components():
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_DB_HOST'),
        port=os.getenv('SUPABASE_DB_PORT'),
        database='postgres',
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD')
    )
    cur = conn.cursor()
    
    print("Analyzing connected components...")
    
    # Check if pgr_connectedComponents is available
    try:
        cur.execute("SELECT pgr_version()")
        print(f"pgRouting version: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"Error checking pgRouting version: {e}")
        return

    # Run pgr_connectedComponents
    # This might take a while for large graphs
    query = """
        SELECT component, count(*) as count
        FROM pgr_connectedComponents(
            'SELECT id, source, target, length_m as cost, length_m as reverse_cost FROM infra_aristas WHERE length_m IS NOT NULL'
        )
        GROUP BY component
        ORDER BY count DESC
        LIMIT 10
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
        
        print("\nTop 10 Components by Size:")
        total_nodes = 0
        for row in rows:
            print(f"Component {row[0]}: {row[1]} nodes")
            total_nodes += row[1]
            
        if rows:
            lcc_id = rows[0][0]
            lcc_size = rows[0][1]
            print(f"\nLargest Connected Component (LCC) ID: {lcc_id}")
            print(f"LCC Size: {lcc_size} nodes")
            
            # Calculate percentage
            cur.execute("SELECT count(*) FROM infra_nodos")
            total_db_nodes = cur.fetchone()[0]
            print(f"Total nodes in DB: {total_db_nodes}")
            print(f"LCC Coverage: {lcc_size / total_db_nodes * 100:.2f}%")
            
    except Exception as e:
        print(f"Error analyzing components: {e}")
        
    conn.close()

if __name__ == "__main__":
    analyze_components()
