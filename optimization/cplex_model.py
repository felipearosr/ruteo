"""
Modelo de Optimización con CPLEX para Ruteo Resiliente

Implementa un MILP usando docplex para encontrar la ruta óptima
considerando distancia y riesgo de falla.
"""

import os
import sys
import socket
import time
from collections import defaultdict, deque
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
    'host': os.getenv('SUPABASE_DB_HOST', 'aws-1-us-east-1.pooler.supabase.com'),
    'port': int(os.getenv('SUPABASE_DB_PORT', 6543)),
    'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
    'user': os.getenv('SUPABASE_DB_USER', 'postgres.eqjzlgbjgwbnvqzbomsn'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
    # Keep connections from hanging forever when the DB is unreachable.
    'connect_timeout': int(os.getenv('SUPABASE_DB_CONNECT_TIMEOUT', 10)),
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
        self.lambda_risk = float(os.getenv("CPLEX_LAMBDA_RISK", 5.0))
        # Límite de tiempo: por defecto 120s; 0 o negativo = sin límite explícito (dejar valor por defecto de CPLEX)
        env_time_limit = os.getenv("CPLEX_TIMELIMIT")
        if env_time_limit is None:
            self.max_time_limit = 120.0
        else:
            try:
                parsed = float(env_time_limit)
                self.max_time_limit = parsed if parsed > 0 else None
            except ValueError:
                self.max_time_limit = 120.0
        # Subgrafo compacto por defecto (~2 km)
        self.bbox_margin = float(os.getenv("CPLEX_BBOX_MARGIN", 0.02))
        self.threads = int(os.getenv("CPLEX_THREADS", os.cpu_count() or 1))
        # 0 = auto, 1 = oportunista (rápido), 2 = determinista (reproducible)
        self.parallel_mode = int(os.getenv("CPLEX_PARALLEL", 1))
        # Gap más laxo para priorizar velocidad
        self.mipgap = float(os.getenv("CPLEX_MIPGAP", 0.2))
        self.mip_display = int(os.getenv("CPLEX_MIPDISPLAY", 4))  # 4 = detalles de progreso
        self.mip_emphasis = int(os.getenv("CPLEX_MIPEMPHASIS", 1))
        self.log_output = os.getenv("CPLEX_LOG_OUTPUT", "1").lower() in {"1", "true", "yes", "on"}
        verbose_env = os.getenv("CPLEX_VERBOSE")
        self.verbose = (
            self.log_output
            if verbose_env is None
            else str(verbose_env).lower() in {"1", "true", "yes", "on"}
        )

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
        bbox_margin = self.bbox_margin if bbox_margin is None else bbox_margin
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT 
                ST_XMin(extent) as xmin, ST_YMin(extent) as ymin,
                ST_XMax(extent) as xmax, ST_YMax(extent) as ymax
            FROM (
                SELECT ST_Extent(geom) as extent
                FROM infra_nodos_cleaned
                WHERE id IN (%s, %s)
            ) AS bbox
            """,
            (source, target),
        )
        bbox = cur.fetchone()
        if (
            not bbox
            or bbox.get('xmin') is None
            or bbox.get('ymin') is None
            or bbox.get('xmax') is None
            or bbox.get('ymax') is None
        ):
            raise ValueError(f"No se encontraron los nodos {source} o {target} o no tienen geometría")

        xmin = bbox['xmin'] - bbox_margin
        ymin = bbox['ymin'] - bbox_margin
        xmax = bbox['xmax'] + bbox_margin
        ymax = bbox['ymax'] + bbox_margin
        bbox_width = xmax - xmin
        bbox_height = ymax - ymin
        self._log(
            f"[CPLEX] Bounding box | xmin={xmin:.6f} ymin={ymin:.6f} xmax={xmax:.6f} ymax={ymax:.6f} "
            f"width={bbox_width:.6f} height={bbox_height:.6f}"
        )

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
            FROM infra_aristas_cleaned a
            WHERE 
                a.length_m IS NOT NULL
                AND ST_Intersects(a.geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
                AND (%s = false OR coalesce(a.p_fallo_arista, 0.0) < %s)
            """,
            (xmin, ymin, xmax, ymax, avoid_flood_zones, flood_threshold),
        )
        raw_aristas = cur.fetchall()
        aristas = []
        for row in raw_aristas:
            length = row.get('length_m')
            p_fallo = row.get('p_fallo', 0.0)
            if length is None:
                continue
            try:
                row['length_m'] = float(length)
            except Exception:
                continue
            try:
                row['p_fallo'] = float(p_fallo if p_fallo is not None else 0.0)
            except Exception:
                row['p_fallo'] = 0.0
            aristas.append(row)

        cur.execute(
            """
            SELECT 
                id,
                ST_X(geom) as lon,
                ST_Y(geom) as lat,
                coalesce(p_fallo_nodo, 0.0) as p_fallo
            FROM infra_nodos_cleaned
            WHERE ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
            """,
            (xmin, ymin, xmax, ymax),
        )
        nodos = {}
        for row in cur.fetchall():
            row['lon'] = float(row['lon'])
            row['lat'] = float(row['lat'])
            row['p_fallo'] = float(row.get('p_fallo', 0.0) or 0.0)
            nodos[row['id']] = row

        # Aseguramos consistencia entre aristas y nodos: solo mantenemos aristas cuyos extremos
        # tienen geometría cargada en el bbox. Si no lo hacemos, CPLEX puede construir "rutas"
        # desconectadas porque faltan restricciones de flujo en nodos fuera del bbox.
        node_ids = set(nodos.keys())
        before = len(aristas)
        aristas = [a for a in aristas if a['source'] in node_ids and a['target'] in node_ids]
        removed = before - len(aristas)
        if removed > 0:
            self._log(f"[CPLEX] Aristas filtradas por bbox (sin nodos): removidas={removed}")

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
        bbox_margin: Optional[float] = None,
    ) -> Dict:
        if lambda_risk is not None:
            self.lambda_risk = lambda_risk

        self._log(
            f"[CPLEX] Iniciando solve | source={source} target={target} "
            f"lambda_risk={self.lambda_risk} max_risk={max_risk} max_distance={max_distance} "
            f"avoid_flood_zones={avoid_flood_zones}"
        )
        t0 = time.time()

        aristas, nodos = self.load_graph(
            source,
            target,
            bbox_margin=bbox_margin,
            avoid_flood_zones=avoid_flood_zones,
        )
        effective_margin = self.bbox_margin if bbox_margin is None else bbox_margin
        self._log(
            f"[CPLEX] Grafo cargado | nodos={len(nodos)} aristas={len(aristas)} bbox_margin={effective_margin}"
        )

        if source not in nodos or target not in nodos:
            raise ValueError(f"Los nodos {source} o {target} no están en el grafo cargado")

        m = Model(name="resilient_routing")
        if self.max_time_limit is not None:
            m.parameters.timelimit = self.max_time_limit
        m.parameters.threads = self.threads
        m.parameters.parallel = self.parallel_mode
        m.parameters.mip.tolerances.mipgap = self.mipgap
        m.parameters.mip.display = self.mip_display
        # emphasis vive en la rama general de emphasis (no en mip.* en versiones recientes de docplex)
        m.parameters.emphasis.mip = self.mip_emphasis
        time_limit_log = f"{self.max_time_limit}s" if self.max_time_limit is not None else "auto"
        self._log(
            "[CPLEX] Parámetros | "
            f"timelimit={time_limit_log} threads={self.threads} "
            f"parallel={self.parallel_mode} mipgap={self.mipgap} mip_display={self.mip_display} "
            f"mip_emphasis={self.mip_emphasis}"
        )

        # Tratamos las aristas como bidireccionales: creamos dos variables por arista
        # (u->v y v->u) y usamos restricción de flujo dirigida. Esto evita infeasibilidades
        # cuando el grafo base trae solo una orientación.
        directed_edges = []
        for a in aristas:
            cost = (a['length_m'] + self.lambda_risk * a['length_m'] * a['p_fallo'])
            var_fwd = m.binary_var(name=f"x_{a['id']}")
            var_bwd = m.binary_var(name=f"x_{a['id']}_rev")
            directed_edges.append((a['source'], a['target'], a, var_fwd, False, cost))
            directed_edges.append((a['target'], a['source'], a, var_bwd, True, cost))

        m.minimize(m.sum(cost * var for _, _, _, var, _, cost in directed_edges))

        out_edges = defaultdict(list)
        in_edges = defaultdict(list)
        for u, v, _, var, _, _ in directed_edges:
            out_edges[u].append(var)
            in_edges[v].append(var)

        self._log(f"[CPLEX] Armando restricciones de flujo para {len(nodos)} nodos...")
        t_flow = time.time()
        for nodo_id in nodos.keys():
            out_list = out_edges.get(nodo_id, [])
            in_list = in_edges.get(nodo_id, [])

            # Si el nodo no tiene aristas incidentes dentro del bbox y no es source/target,
            # omitir la restricción (previene filas triviales 0=0 que CPLEX puede marcar
            # como infactibles cuando todas las variables quedan fijadas).
            if nodo_id not in (source, target) and not out_list and not in_list:
                continue

            flow = m.sum(out_list) - m.sum(in_list)
            if nodo_id == source:
                m.add_constraint(flow == 1, ctname=f"flow_source_{nodo_id}")
            elif nodo_id == target:
                m.add_constraint(flow == -1, ctname=f"flow_target_{nodo_id}")
            else:
                m.add_constraint(flow == 0, ctname=f"flow_{nodo_id}")
        self._log(f"[CPLEX] Restricciones de flujo listas en {time.time() - t_flow:.2f}s")

        if max_risk is not None:
            m.add_constraint(m.sum(a['p_fallo'] * x[a['id']] for a in aristas) <= max_risk * len(aristas), "max_risk")
        if max_distance is not None:
            m.add_constraint(m.sum(a['length_m'] * x[a['id']] for a in aristas) <= max_distance, "max_distance")

        self._log("[CPLEX] Lanzando solve()...")
        solution = m.solve(log_output=self.log_output)
        self._log(
            f"[CPLEX] solve() terminado en {m.solve_details.time:.2f}s | "
            f"status={m.solve_details.status} gap={m.solve_details.mip_relative_gap}"
        )

        solve_time = m.solve_details.time

        result = {
            'status': solution.solve_status if solution else 'no_solution',
            'computation_time': solve_time if solution else 0.0,
            'route': [],
            'total_distance': 0.0,
            'total_risk': 0.0,
            'aristas_usadas': []
        }

        if solution is None:
            return result

        selected_edges = defaultdict(list)  # (u,v) -> list of (arista, is_reversed)
        selected_adj = defaultdict(list)    # directed adjacency using chosen orientation
        for u, v, a, var, is_reversed, _ in directed_edges:
            if var.solution_value > 0.5:
                selected_adj[u].append(v)
                selected_edges[(u, v)].append((a, is_reversed))

        if not selected_edges:
            self._log("[CPLEX] Sin aristas seleccionadas; posiblemente sin solución factible.")
            result['status'] = 'no_selected_edges'
            return result

        def bfs_path(start: int, goal: int):
            q = deque([start])
            parents = {start: None}
            while q:
                node = q.popleft()
                if node == goal:
                    break
                for nei in selected_adj.get(node, []):
                    if nei not in parents:
                        parents[nei] = node
                        q.append(nei)
            if goal not in parents:
                return None
            path = [goal]
            while path[-1] != start:
                path.append(parents[path[-1]])
            path.reverse()
            return path

        path_nodes = bfs_path(source, target)
        if not path_nodes:
            self._log("[CPLEX] No se pudo reconstruir ruta: target no alcanzable con aristas seleccionadas.")
            result['status'] = 'disconnected_route'
            return result

        for u, v in zip(path_nodes[:-1], path_nodes[1:]):
            edge_candidates = selected_edges.get((u, v), [])
            if not edge_candidates:
                self._log(f"[CPLEX] Falta arista para el segmento {u}->{v}; ruta incompleta.")
                result['status'] = 'reconstruction_error'
                break
            arista, is_reversed = edge_candidates[0]
            arista = arista.copy()
            arista['is_reversed'] = is_reversed
            result['route'].append(arista['id'])
            result['total_distance'] += arista['length_m']
            result['total_risk'] += arista['p_fallo']
            result['aristas_usadas'].append(arista)

        self._log(
            f"[CPLEX] Ruta recuperada en {time.time() - t0:.2f}s | "
            f"segmentos={len(result['route'])} distancia={result['total_distance']:.1f} "
            f"riesgo={result['total_risk']:.4f}"
        )

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

    def _log(self, message: str):
        if self.verbose:
            print(message, file=sys.stderr, flush=True)
