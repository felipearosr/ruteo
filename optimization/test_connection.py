import os
import socket
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../web/.env.local'))

def test_connection():
    host = os.getenv('SUPABASE_DB_HOST')
    print(f"Host: {host}")
    
    try:
        ip = socket.gethostbyname(host)
        print(f"Resolved IP: {ip}")
    except Exception as e:
        print(f"DNS Resolution failed: {e}")
        
    try:
        conn = psycopg2.connect(
            host=ip,
            port=os.getenv('SUPABASE_DB_PORT'),
            database='postgres',
            user=os.getenv('SUPABASE_DB_USER'),
            password=os.getenv('SUPABASE_DB_PASSWORD')
        )
        print("✅ Connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
