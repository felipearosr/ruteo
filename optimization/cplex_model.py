"""
Modelo de Optimización con CPLEX para Ruteo Resiliente

Implementa un MILP usando docplex para encontrar la ruta óptima
considerando distancia y riesgo de falla.
"""

import os
import sys
import socket
from typing import Dict, List, Tuple, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    from docplex.mp.model import Model
    CPLEX_AVAILABLE = True
except ImportError:
    CPLEX_AVAILABLE = False
    print("⚠️  CPLEX/docplex no está instalado. El modelo de optimización no estará disponible.", file=sys.stderr)


DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': int(os.getenv('SUPABASE_DB_PORT', 6543)),
    'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}


def get_db_connection():
    host = DB_CONFIG['host']
    try:
        host_ip = socket.gethostbyname(host)
    except Exception:
        host_ip = host
    params = DB_CONFIG.copy()
    params['host'] = host_ip
    return psycopg2.connect(**params)


class CplexResilientRouter:
    """Router resiliente usando MILP con CPLEX (docplex)"""

    def __init__(self, connection_params: Dict = None):
        if not CPLEX_AVAILABLE:
            raise ImportError("CPLEX/docplex no está disponible. Instala docplex y CPLEX primero.")
        self.conn_params = connection_params or DB_CONFIG
        self.conn = None
        self.lambda_risk = 5.0
        self.max_time_limit = 300  # segundos

    def connect(self):
        if not self.conn or self.conn.closed:
            self.conn = get_db_connection()
        return self.conn

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def load_graph(
        self,
        source: int,
        target: int,
        bbox_margin: float = 0.05,
        avoid_flood_zones: bool = False,
        flood_threshold: float = 0.3,
    ) -> Tuple[List[Dict], Dict]:
        self.connect()
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT 
                ST_XMin(extent) as xmin, ST_YMin(extent) as ymin,
                ST_XMax(extent) as xmax, ST_YMax(extent) as ymax
            FROM (
                SELECT ST_Extent(geom) as extent
                FROM infra_nodos
                WHERE id IN (%s, %s)
            ) AS bbox
            """,
            (source, target),
        )
        bbox = cur.fetchone()
        if not bbox:
            raise ValueError(f"No se encontraron los nodos {source} o {target}")

        xmin = bbox['xmin'] - bbox_margin
        ymin = bbox['ymin'] - bbox_margin
        xmax = bbox['xmax'] + bbox_margin
        ymax = bbox['ymax'] + bbox_margin

        cur.execute(
            """
            SELECT 
                a.id,
                a.source,
                a.target,
                a.length_m,
                coalesce(a.p_fallo_arista, 0.0) as p_fallo,
                a.highway,
                ST_AsText(a.geom) as geom_wkt
            FROM infra_aristas a
            WHERE 
                a.length_m IS NOT NULL
                AND ST_Intersects(a.geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
                AND (%s = false OR coalesce(a.p_fallo_arista, 0.0) < %s)
            """,
            (xmin, ymin, xmax, ymax, avoid_flood_zones, flood_threshold),
        )
        aristas = cur.fetchall()

        cur.execute(
            """
            SELECT 
                id,
                ST_X(geom) as lon,
                ST_Y(geom) as lat,
                coalesce(p_fallo_nodo, 0.0) as p_fallo
            FROM infra_nodos
            WHERE ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
            """,
            (xmin, ymin, xmax, ymax),
        )
        nodos = {}
        for row in cur.fetchall():
            row['lon'] = float(row['lon'])
            row['lat'] = float(row['lat'])
            nodos[row['id']] = row

        for arista in aristas:
            arista['length_m'] = float(arista['length_m'])
            arista['p_fallo'] = float(arista['p_fallo'])

        cur.close()
        return aristas, nodos

    def solve(
        self,
        source: int,
        target: int,
        max_risk: Optional[float] = None,
        max_distance: Optional[float] = None,
        lambda_risk: Optional[float] = None,
        avoid_flood_zones: bool = False,
    ) -> Dict:
        if lambda_risk is not None:
            self.lambda_risk = lambda_risk

        aristas, nodos = self.load_graph(source, target, avoid_flood_zones=avoid_flood_zones)
        if source not in nodos or target not in nodos:
            raise ValueError(f"Los nodos {source} o {target} no están en el grafo cargado")

        m = Model(name="resilient_routing")
        m.parameters.timelimit = self.max_time_limit

        x = {a['id']: m.binary_var(name=f"x_{a['id']}") for a in aristas}

        m.minimize(
            m.sum((a['length_m'] + self.lambda_risk * a['length_m'] * a['p_fallo']) * x[a['id']] for a in aristas)
        )

        for nodo_id in nodos.keys():
            flow = m.sum(x[a['id']] for a in aristas if a['source'] == nodo_id) - m.sum(
                x[a['id']] for a in aristas if a['target'] == nodo_id
            )
            if nodo_id == source:
                m.add_constraint(flow == 1, ctname=f"flow_source_{nodo_id}")
            elif nodo_id == target:
                m.add_constraint(flow == -1, ctname=f"flow_target_{nodo_id}")
            else:
                m.add_constraint(flow == 0, ctname=f"flow_{nodo_id}")

        if max_risk is not None:
            m.add_constraint(m.sum(a['p_fallo'] * x[a['id']] for a in aristas) <= max_risk * len(aristas), "max_risk")
        if max_distance is not None:
            m.add_constraint(m.sum(a['length_m'] * x[a['id']] for a in aristas) <= max_distance, "max_distance")

        solution = m.solve(log_output=False)

        result = {
            'status': solution.solve_status if solution else 'no_solution',
            'computation_time': solution.solve_time if solution else 0.0,
            'route': [],
            'total_distance': 0.0,
            'total_risk': 0.0,
            'aristas_usadas': []
        }

        if solution is None:
            return result

        selected_edges = {}
        selected_adj = {}
        for a in aristas:
            if x[a['id']].solution_value > 0.5:
                u, v = a['source'], a['target']
                selected_adj.setdefault(u, []).append(v)
                selected_adj.setdefault(v, []).append(u)
                key = tuple(sorted((u, v)))
                selected_edges[key] = a

        curr = source
        visited_edges = set()
        steps = 0
        max_steps = len(selected_edges) + 10
        while curr != target and steps < max_steps:
            steps += 1
            neighbors = selected_adj.get(curr, [])
            next_node = None
            for neighbor in neighbors:
                edge_key = tuple(sorted((curr, neighbor)))
                if edge_key not in visited_edges:
                    next_node = neighbor
                    visited_edges.add(edge_key)
                    break
            if next_node is None:
                break

            edge_key = tuple(sorted((curr, next_node)))
            arista = selected_edges[edge_key].copy()
            arista['is_reversed'] = not (arista['source'] == curr and arista['target'] == next_node)
            result['route'].append(arista['id'])
            result['total_distance'] += arista['length_m']
            result['total_risk'] += arista['p_fallo']
            result['aristas_usadas'].append(arista)
            curr = next_node

        return result

    def solution_to_geojson(self, solution: Dict) -> Dict:
        features = []
        for i, arista in enumerate(solution.get('aristas_usadas', [])):
            geom = self._wkt_to_geojson(arista['geom_wkt'])
            if arista.get('is_reversed', False) and geom['type'] == 'LineString':
                geom['coordinates'].reverse()
            features.append({
                'type': 'Feature',
                'geometry': geom,
                'properties': {
                    'seq': i + 1,
                    'edge_id': arista['id'],
                    'length_m': arista['length_m'],
                    'p_fallo': arista['p_fallo'],
                    'highway': arista['highway']
                }
            })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'total_distance_m': solution.get('total_distance', 0.0),
                'total_risk': solution.get('total_risk', 0.0),
                'computation_time_s': solution.get('computation_time', 0.0),
                'num_segments': len(features)
            }
        }

    def _wkt_to_geojson(self, wkt: str) -> Dict:
        wkt = wkt.strip()
        if wkt.upper().startswith("LINESTRING"):
            coords_str = wkt[wkt.find("(") + 1: wkt.rfind(")")].split(",")
            coords = []
            for c in coords_str:
                parts = c.strip().split()
                if len(parts) == 2:
                    x, y = map(float, parts)
                    coords.append([x, y])
            return {'type': 'LineString', 'coordinates': coords}
        return {'type': 'GeometryCollection', 'geometries': []}
