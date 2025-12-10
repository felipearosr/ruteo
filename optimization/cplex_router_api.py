#!/usr/bin/env python
"""
Script de API para ejecutar el router de CPLEX desde Next.js
"""

import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

try:
    from cplex_model import CplexResilientRouter, CPLEX_AVAILABLE
except ImportError:
    CPLEX_AVAILABLE = False


def main():
    parser = argparse.ArgumentParser(description='CPLEX Router API')
    parser.add_argument('--source', type=int, required=True, help='Nodo origen')
    parser.add_argument('--target', type=int, required=True, help='Nodo destino')
    parser.add_argument('--lambda-risk', type=float, default=5.0, help='Factor de penalización por riesgo')
    parser.add_argument('--max-risk', type=float, default=None, help='Riesgo máximo permitido')
    parser.add_argument('--max-distance', type=float, default=None, help='Distancia máxima permitida')
    parser.add_argument('--avoid-flood', action='store_true', help='Filtrar aristas con p_fallo >= 0.3')
    parser.add_argument('--bbox-margin', type=float, default=None, help='Margen (grados) alrededor de source/target')

    args = parser.parse_args()

    if not CPLEX_AVAILABLE:
        result = {
            'route': {'type': 'FeatureCollection', 'features': []},
            'metrics': {
                'distance_m': 0,
                'computation_time_ms': 0,
                'risk_score': 0,
                'num_segments': 0,
                'method': 'cplex',
                'status': 'unavailable'
            },
            'error': 'CPLEX/docplex no está instalado o no se encuentra la licencia',
            'cplex_available': False
        }
        print(json.dumps(result))
        sys.exit(1)

    try:
        router = CplexResilientRouter()
        solution = router.solve(
            source=args.source,
            target=args.target,
            max_risk=args.max_risk,
            max_distance=args.max_distance,
            lambda_risk=args.lambda_risk,
            avoid_flood_zones=args.avoid_flood,
            bbox_margin=args.bbox_margin,
        )

        geojson = router.solution_to_geojson(solution)

        result = {
            'route': geojson,
            'metrics': {
                'distance_m': solution['total_distance'],
                'travel_time_min': solution.get('travel_time_min', 0),
                'computation_time_ms': solution['computation_time'] * 1000,
                'risk_score': solution['total_risk'],
                'num_segments': len(solution['route']),
                'method': 'cplex',
                'status': str(solution.get('status')),
                'parameters': {
                    'lambda_risk': args.lambda_risk,
                    'max_risk': args.max_risk,
                    'max_distance': args.max_distance,
                    'avoid_flood': args.avoid_flood,
                    'bbox_margin': args.bbox_margin,
                }
            },
            'cplex_available': True
        }

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        result = {
            'route': {'type': 'FeatureCollection', 'features': []},
            'metrics': {
                'distance_m': 0,
                'computation_time_ms': 0,
                'risk_score': 0,
                'num_segments': 0,
                'method': 'cplex',
                'status': 'error'
            },
            'error': str(e),
            'cplex_available': True
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()
