#!/usr/bin/env python3
"""Get the latest simulation summary from the running API"""

import requests
import json

API_URL = "http://localhost:3000/api/simulate-failures"

print("Fetching simulations list...")
response = requests.get(API_URL)

if response.status_code != 200:
    print(f"Error: API returned {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

if not data.get('success'):
    print("Error: API reported failure")
    print(data)
    exit(1)

simulations = data.get('simulations', [])

if not simulations:
    print("No simulations found. Run a simulation first!")
    exit(1)

# Get the most recent simulation
latest_sim = simulations[0]
sim_id = latest_sim['simulation_id']

print(f"\nLatest Simulation ID: {sim_id}")
print(f"Created at: {latest_sim['created_at']}")

# Get full details
print("\nFetching full simulation details...")
detail_response = requests.get(f"{API_URL}?simulation_id={sim_id}")

if detail_response.status_code != 200:
    print(f"Error fetching details: {detail_response.status_code}")
    exit(1)

detail_data = detail_response.json()

if detail_data.get('success'):
    summary = detail_data.get('summary', {})
    
    print("\n" + "="*60)
    print("SIMULATION SUMMARY - WATER-LIKE PROPAGATION RESULTS")
    print("="*60)
    print(f"\nSimulation ID: {sim_id}")
    print(f"Created: {latest_sim['created_at']}")
    print(f"\nStatistics:")
    print(f"  Total Nodes Checked: {summary.get('total_nodos', 'N/A')}")
    print(f"  Failed Nodes: {summary.get('nodos_failed', 'N/A')}")
    print(f"  Total Edges Checked: {summary.get('total_aristas', 'N/A')}")
    print(f"  Failed Edges: {summary.get('aristas_failed', 'N/A')}")
    print(f"\nThis demonstrates how failures propagate through the network")
    print(f"like water, showing the critical need for resilient routing!")
    print("="*60)
    
    # Save to file
    output_file = '/home/faros/ruteo/latest_simulation_summary.json'
    with open(output_file, 'w') as f:
        json.dump(detail_data, f, indent=2)
    
    print(f"\n✓ Full data saved to: {output_file}")
    
    # Create a presentation-ready summary
    summary_file = '/home/faros/ruteo/SIMULATION_SHOWCASE.txt'
    with open(summary_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("WATER-LIKE FAILURE PROPAGATION - DEMONSTRATION RESULTS\n")
        f.write("="*70 + "\n\n")
        f.write(f"Simulation ID: {sim_id}\n")
        f.write(f"Timestamp: {latest_sim['created_at']}\n\n")
        f.write("KEY FINDINGS:\n")
        f.write("-" * 70 + "\n")
        f.write(f"• Network Nodes Analyzed: {summary.get('total_nodos', 'N/A')}\n")
        f.write(f"• Nodes That Failed: {summary.get('nodos_failed', 'N/A')}\n")
        f.write(f"• Network Edges Analyzed: {summary.get('total_aristas', 'N/A')}\n")
        f.write(f"• Edges That Failed: {summary.get('aristas_failed', 'N/A')}\n\n")
        
        if summary.get('nodos_failed') and summary.get('total_nodos'):
            failure_rate = (summary['nodos_failed'] / summary['total_nodos']) * 100
            f.write(f"• Node Failure Rate: {failure_rate:.1f}%\n\n")
        
        f.write("WHAT THIS DEMONSTRATES:\n")
        f.write("-" * 70 + "\n")
        f.write("This simulation showcases how infrastructure failures propagate\n")
        f.write("through a network like water spreading - when one component fails,\n")
        f.write("it increases the likelihood of neighboring components failing.\n\n")
        f.write("OUR SOLUTION:\n")
        f.write("-" * 70 + "\n")
        f.write("Our resilient routing system:\n")
        f.write("1. Identifies high-risk areas before failures occur\n")
        f.write("2. Routes traffic away from vulnerable zones\n")
        f.write("3. Adapts in real-time to changing threat conditions\n")
        f.write("4. Minimizes service disruption during cascading failures\n\n")
        f.write("="*70 + "\n")
    
    print(f"✓ Showcase summary saved to: {summary_file}")
    print("\nYou can use these files for your presentation!")

else:
    print("Error getting simulation details")
    print(detail_data)
