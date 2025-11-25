#!/usr/bin/env python3
"""Deploy the simulate_propagation SQL function to Supabase"""

import os
from supabase import create_client

# Read the SQL file
with open('/home/faros/ruteo/sql/simulate_propagation.sql', 'r') as f:
    sql = f.read()

# Get credentials from environment
url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not url or not key:
    print("Error: NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    exit(1)

# Create client
supabase = create_client(url, key)

# Execute the SQL
try:
    result = supabase.rpc('exec_sql', {'sql': sql}).execute()
    print("✓ Function deployed successfully!")
except Exception as e:
    # If exec_sql doesn't exist, try direct execution via postgrest
    print(f"Note: {e}")
    print("Attempting alternative deployment method...")
    
    # Alternative: use the SQL editor endpoint if available
    # For now, we'll just print instructions
    print("\nPlease run this SQL in the Supabase SQL Editor:")
    print("=" * 60)
    print(sql)
    print("=" * 60)
