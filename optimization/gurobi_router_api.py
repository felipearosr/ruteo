#!/usr/bin/env python
"""
Script de API para ejecutar el router de GUROBI desde Next.js

Este script se ejecuta desde el endpoint /api/route/optimize y retorna
JSON con la ruta optimizada y métricas.

Uso:
    python gurobi_router_api.py --source X --target Y [--lambda-risk K] [--max-risk R] [--max-distance D]
"""

import sys
import json
import argparse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    from gurobi_model import ResilientRouter
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False


def main():
    parser = argparse.ArgumentParser(description='GUROBI Router API')
    parser.add_argument('--source', type=int, required=True, help='Nodo origen')
    parser.add_argument('--target', type=int, required=True, help='Nodo destino')
    parser.add_argument('--lambda-risk', type=float, default=5.0, help='Factor de penalización por riesgo')
    parser.add_argument('--max-risk', type=float, default=None, help='Riesgo máximo permitido')
    parser.add_argument('--max-distance', type=float, default=None, help='Distancia máxima permitida')
    parser.add_argument('--avoid-flood', action='store_true', help='Filtrar aristas con p_fallo >= 0.3')
    
    args = parser.parse_args()
    
    if not GUROBI_AVAILABLE:
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
                'method': 'gurobi',
                'status': 'unavailable'
            },
            'error': 'GUROBI no está instalado o no se encuentra la licencia',
            'gurobi_available': False
        }
        print(json.dumps(result))
        sys.exit(1)
    
    try:
        # Crear router y resolver
        router = ResilientRouter()
        solution = router.solve(
            source=args.source,
            target=args.target,
            max_risk=args.max_risk,
            max_distance=args.max_distance,
            lambda_risk=args.lambda_risk,
            avoid_flood_zones=args.avoid_flood
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
                'method': 'gurobi',
                'status': 'optimal' if solution['status'] == 2 else 'suboptimal',
                'parameters': {
                    'lambda_risk': args.lambda_risk,
                    'max_risk': args.max_risk,
                    'max_distance': args.max_distance
                }
            },
            'gurobi_available': True
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
                'method': 'gurobi',
                'status': 'error'
            },
            'error': str(e),
            'gurobi_available': True
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()
