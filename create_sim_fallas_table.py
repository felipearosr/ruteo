import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Crear conexión a la base de datos Supabase."""
    # Intentar conectar al puerto 5432 directamente si 6543 falla
    port = 5432
    host = os.getenv('SUPABASE_DB_HOST')
    
    # Resolver a IPv4 explícitamente
    import socket
    try:
        host_ip = socket.gethostbyname(host)
        print(f"Resuelto {host} a {host_ip}")
        host = host_ip
    except Exception as e:
        print(f"No se pudo resolver {host}: {e}")
    
    print(f"Conectando a {host}:{port}...")
    
    return psycopg2.connect(
        host=host,
        database=os.getenv('SUPABASE_DB_NAME'),
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        port=port
    )

def create_tables():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Creando tabla sim_fallas_activas...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sim_fallas_activas (
            id bigserial primary key,
            simulation_id uuid not null,
            entity_type text not null check (entity_type in ('nodo', 'arista')),
            entity_id bigint not null,
            p_fallo double precision not null,
            random_value double precision not null,
            is_failed boolean not null,
            created_at timestamptz default now()
        );
        """)
        
        print("Creando índices...")
        cur.execute("CREATE INDEX IF NOT EXISTS sim_fallas_activas_sim_id_idx ON sim_fallas_activas (simulation_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS sim_fallas_activas_entity_idx ON sim_fallas_activas (entity_type, entity_id);")
        
        print("Verificando columnas de probabilidad en infra_nodos...")
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='infra_nodos' AND column_name='p_fallo_nodo') THEN
                ALTER TABLE infra_nodos ADD COLUMN p_fallo_nodo double precision default 0.0;
            END IF;
        END $$;
        """)
        
        print("Verificando columnas de probabilidad en infra_aristas...")
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='infra_aristas' AND column_name='p_fallo_arista') THEN
                ALTER TABLE infra_aristas ADD COLUMN p_fallo_arista double precision default 0.0;
            END IF;
        END $$;
        """)
        
        conn.commit()
        print("✓ Tablas y columnas verificadas/creadas exitosamente.")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()
