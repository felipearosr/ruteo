#!/usr/bin/env python
"""
Script de API para ejecutar A* desde Next.js

Este script se ejecuta desde el endpoint /api/route/metaheuristic y retorna
JSON con la ruta calculada por A* y métricas.

Uso:
    python astar_router_api.py --source X --target Y [--risk-weight W] [--heuristic-weight H]
"""

import sys
import json
import argparse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from metaheuristics import AStarResilientRouter


def main():
    parser = argparse.ArgumentParser(description='A* Router API')
    parser.add_argument('--source', type=int, required=True, help='Nodo origen')
    parser.add_argument('--target', type=int, required=True, help='Nodo destino')
    parser.add_argument('--risk-weight', type=float, default=3.0, help='Peso del riesgo en el costo')
    parser.add_argument('--heuristic-weight', type=float, default=1.0, help='Peso de la heurística')
    
    args = parser.parse_args()
    
    try:
        # Crear router y resolver
        router = AStarResilientRouter()
        solution = router.solve(
            source=args.source,
            target=args.target,
            risk_weight=args.risk_weight,
            heuristic_weight=args.heuristic_weight
        )
        
        # Convertir a GeoJSON
        geojson = router.solution_to_geojson(solution)
        
        # Preparar resultado
        result = {
            'route': geojson,
            'metrics': {
                'distance_m': solution['total_distance'],
                'computation_time_ms': solution['computation_time'] * 1000,  # s to ms
                'risk_score': solution['total_risk'],
                'num_segments': len(solution['route']),
                'nodes_explored': solution['nodes_explored'],
                'method': 'astar',
                'parameters': {
                    'risk_weight': args.risk_weight,
                    'heuristic_weight': args.heuristic_weight
                }
            }
        }
        
        # Imprimir JSON para que Next.js lo capture
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        result = {
            'route': {
                'type': 'FeatureCollection',
                'features': []
            },
            'metrics': {
                'distance_m': 0,
                'computation_time_ms': 0,
                'risk_score': 0,
                'num_segments': 0,
                'nodes_explored': 0,
                'method': 'astar'
            },
            'error': str(e)
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()
