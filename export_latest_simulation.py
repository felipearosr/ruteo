#!/usr/bin/env python3
"""Export the latest simulation results to a JSON file"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/faros/ruteo/.env')

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not url or not key:
    print("Error: Environment variables not set")
    exit(1)

supabase = create_client(url, key)

# Get the most recent simulation
print("Fetching latest simulation...")
result = supabase.table('sim_fallas_activas').select('simulation_id, created_at').order('created_at', desc=True).limit(1).execute()

if not result.data or len(result.data) == 0:
    print("No simulations found in database")
    exit(1)

latest_sim_id = result.data[0]['simulation_id']
created_at = result.data[0]['created_at']

print(f"Latest simulation ID: {latest_sim_id}")
print(f"Created at: {created_at}")

# Get all entities for this simulation
print("\nFetching simulation entities...")
entities = supabase.table('sim_fallas_activas').select('*').eq('simulation_id', latest_sim_id).execute()

# Count statistics
total_entities = len(entities.data)
failed_nodes = [e for e in entities.data if e['entity_type'] == 'nodo' and e['is_failed']]
failed_edges = [e for e in entities.data if e['entity_type'] == 'arista' and e['is_failed']]

print(f"\nSimulation Statistics:")
print(f"  Total entities: {total_entities}")
print(f"  Failed nodes: {len(failed_nodes)}")
print(f"  Failed edges: {len(failed_edges)}")

# Get geometries for failed nodes
print("\nFetching node geometries...")
failed_node_ids = [n['entity_id'] for n in failed_nodes]
if failed_node_ids:
    nodes_with_geom = supabase.table('infra_nodos').select('id, geom').in_('id', failed_node_ids).execute()
    node_geom_map = {n['id']: n['geom'] for n in nodes_with_geom.data}
else:
    node_geom_map = {}

# Get geometries for failed edges
print("Fetching edge geometries...")
failed_edge_ids = [e['entity_id'] for e in failed_edges]
if failed_edge_ids:
    edges_with_geom = supabase.table('infra_aristas').select('id, geom').in_('id', failed_edge_ids).execute()
    edge_geom_map = {e['id']: e['geom'] for e in edges_with_geom.data}
else:
    edge_geom_map = {}

# Build export data
export_data = {
    'simulation_id': latest_sim_id,
    'created_at': created_at,
    'summary': {
        'total_entities': total_entities,
        'failed_nodes': len(failed_nodes),
        'failed_edges': len(failed_edges)
    },
    'failed_nodes': [
        {
            'id': n['entity_id'],
            'p_fallo': n['p_fallo'],
            'random_value': n['random_value'],
            'geom': node_geom_map.get(n['entity_id'])
        }
        for n in failed_nodes
    ],
    'failed_edges': [
        {
            'id': e['entity_id'],
            'p_fallo': e['p_fallo'],
            'random_value': e['random_value'],
            'geom': edge_geom_map.get(e['entity_id'])
        }
        for e in failed_edges
    ]
}

# Save to file
output_file = '/home/faros/ruteo/latest_simulation_export.json'
with open(output_file, 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"\n✓ Simulation data exported to: {output_file}")

# Also create a summary file
summary_file = '/home/faros/ruteo/simulation_summary.txt'
with open(summary_file, 'w') as f:
    f.write(f"Latest Simulation Summary\n")
    f.write(f"========================\n\n")
    f.write(f"Simulation ID: {latest_sim_id}\n")
    f.write(f"Created at: {created_at}\n\n")
    f.write(f"Statistics:\n")
    f.write(f"  - Total entities: {total_entities}\n")
    f.write(f"  - Failed nodes: {len(failed_nodes)}\n")
    f.write(f"  - Failed edges: {len(failed_edges)}\n\n")
    f.write(f"This demonstrates the water-like propagation effect where failures\n")
    f.write(f"spread through the network, showcasing the importance of resilient routing.\n")

print(f"✓ Summary saved to: {summary_file}")
