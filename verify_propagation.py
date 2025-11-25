import requests
import json
import os
from dotenv import load_dotenv

# Load env to get URL if needed, but we'll assume localhost:3000
load_dotenv('/home/faros/ruteo/web/.env')

API_URL = "http://localhost:3000/api/simulate-failures"

def verify_propagation():
    print("Starting verification...")
    
    # Payload with high propagation probability
    payload = {
        "seed": 12345,
        "min_probability": 0.01,
        "propagation_probability": 0.9, # Very high to ensure spread
        "max_propagation_steps": 10
    }
    
    try:
        print(f"Sending POST request to {API_URL}...")
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            print(f"Error: API returned {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        
        if not data.get('success'):
            print("Error: API reported failure")
            print(data.get('error'))
            return
            
        summary = data.get('summary', {})
        print("\nSimulation Summary:")
        print(json.dumps(summary, indent=2))
        
        initial_seeds = summary.get('initial_seeds', 0)
        propagated_nodes = summary.get('propagated_nodes', 0)
        total_failed = summary.get('total_nodes_failed', 0)
        
        print(f"\nInitial Seeds: {initial_seeds}")
        print(f"Propagated Nodes: {propagated_nodes}")
        print(f"Total Failed: {total_failed}")
        
        if propagated_nodes > 0:
            print("\nSUCCESS: Propagation occurred!")
        else:
            print("\nWARNING: No propagation occurred. Check if graph is connected or probabilities are too low.")
            
    except Exception as e:
        print(f"Exception during verification: {e}")

if __name__ == "__main__":
    verify_propagation()
