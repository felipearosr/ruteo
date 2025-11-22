import os
import subprocess
import socket
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('SUPABASE_DB_HOST')
user = os.getenv('SUPABASE_DB_USER')
password = os.getenv('SUPABASE_DB_PASSWORD')
dbname = os.getenv('SUPABASE_DB_NAME')
port = '5432'

# Try to resolve to IPv4
try:
    host_ip = socket.gethostbyname(host)
    print(f"Resolved {host} to {host_ip}")
    host = host_ip
except:
    print(f"Could not resolve {host}, using hostname")

# Construct connection string
# postgresql://user:password@host:port/dbname
conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

print(f"Connecting to {host}:{port}...")

# Run psql
cmd = ['psql', conn_str, '-f', 'create_table.sql']

# Mask password in print
print(f"Running: psql postgresql://{user}:***@{host}:{port}/{dbname} -f create_table.sql")

try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    if result.returncode == 0:
        print("Success!")
    else:
        print("Failed with return code", result.returncode)
except Exception as e:
    print(f"Error running psql: {e}")
