#!/usr/bin/env python3
"""
Check for one-way street data in the database
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

# Check columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'infra_aristas' 
    ORDER BY ordinal_position;
""")
print('Columns in infra_aristas:')
for row in cur.fetchall():
    print(f'  {row["column_name"]}: {row["data_type"]}')

# Check for oneway data in tags
cur.execute("""
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN tags->>'oneway' IS NOT NULL THEN 1 END) as with_oneway,
           COUNT(CASE WHEN tags->>'oneway' = 'yes' THEN 1 END) as oneway_yes,
           COUNT(CASE WHEN tags->>'oneway' = '-1' THEN 1 END) as oneway_reverse
    FROM infra_aristas;
""")
print('\nOne-way street statistics:')
row = cur.fetchone()
print(f'  Total edges: {row["total"]}')
print(f'  With oneway tag: {row["with_oneway"]}')
print(f'  Oneway=yes: {row["oneway_yes"]}')
print(f'  Oneway=-1 (reverse): {row["oneway_reverse"]}')

# Sample some oneway tags
cur.execute("""
    SELECT id, source, target, tags->>'oneway' as oneway, tags->>'highway' as highway, reverse_cost
    FROM infra_aristas
    WHERE tags->>'oneway' IS NOT NULL
    LIMIT 10;
""")
print('\nSample one-way edges:')
for row in cur.fetchall():
    print(f'  ID {row["id"]}: source={row["source"]}, target={row["target"]}, oneway={row["oneway"]}, highway={row["highway"]}, reverse_cost={row["reverse_cost"]}')

conn.close()
