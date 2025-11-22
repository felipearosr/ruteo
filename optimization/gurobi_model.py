"""
Modelo de Optimización con GUROBI para Ruteo Resiliente

Este módulo implementa un modelo de programación lineal entera mixta (MILP)
para encontrar la ruta óptima considerando distancia y riesgo de falla.

Autor: Felipe Aros
Fecha: Noviembre 2025
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    print("⚠️  GUROBI no está instalado. El modelo de optimización no estará disponible.")


import socket

# Configuración de conexión a Supabase
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': int(os.getenv('SUPABASE_DB_PORT', 6543)),
    'database': 'postgres',
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos."""
    host = DB_CONFIG['host']
    try:
        # Force IPv4 resolution
        host_ip = socket.gethostbyname(host)
    except:
        host_ip = '18.213.155.45'
        
    params = DB_CONFIG.copy()
    params['host'] = host_ip
    return psycopg2.connect(**params)


class ResilientRouter:
    """Router resiliente usando optimización MILP con GUROBI"""
    
    def __init__(self, connection_params: Dict = None):
        """
        Inicializar el router
        
        Args:
            connection_params: Parámetros de conexión a PostgreSQL
        """
        if not GUROBI_AVAILABLE:
            raise ImportError("GUROBI no está disponible. Instala gurobipy primero.")
        
        self.conn_params = connection_params or DB_CONFIG
        self.conn = None
        
        # Parámetros del modelo
        self.lambda_risk = 5.0  # Factor de penalización por riesgo
        self.max_time_limit = 300  # Límite de tiempo en segundos
        
    def connect(self):
        """Establecer conexión a la base de datos"""
        if not self.conn or self.conn.closed:
            self.conn = get_db_connection()
        return self.conn
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def load_graph(self, source: int, target: int, bbox_margin: float = 0.05) -> Tuple[List, Dict]:
        """
        Cargar el grafo desde la base de datos
        
        Args:
            source: ID del nodo origen
            target: ID del nodo destino
            bbox_margin: Margen adicional para el bounding box (en grados)
            
        Returns:
            Tupla de (aristas, nodos_dict)
        """
        self.connect()
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener coordenadas de origen y destino para definir bbox
        cur.execute("""
            SELECT 
                ST_XMin(extent) as xmin, ST_YMin(extent) as ymin,
                ST_XMax(extent) as xmax, ST_YMax(extent) as ymax
            FROM (
                SELECT ST_Extent(geom) as extent
                FROM infra_nodos
                WHERE id IN (%s, %s)
            ) AS bbox
        """, (source, target))
        bbox = cur.fetchone()
        
        if not bbox:
            raise ValueError(f"No se encontraron los nodos {source} o {target}")
        
        # Expandir bbox
        xmin = bbox['xmin'] - bbox_margin
        ymin = bbox['ymin'] - bbox_margin
        xmax = bbox['xmax'] + bbox_margin
        ymax = bbox['ymax'] + bbox_margin
        
        # Cargar aristas dentro del bbox
        cur.execute("""
            SELECT 
                a.id,
                a.source,
                a.target,
                a.length_m,
                0.0 as p_fallo,
                a.highway,
                ST_AsText(a.geom) as geom_wkt
            FROM infra_aristas a
            JOIN infra_nodos n1 ON a.source = n1.id
            JOIN infra_nodos n2 ON a.target = n2.id
            WHERE 
                a.length_m IS NOT NULL AND
                ST_Intersects(
                    a.geom,
                    ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                )
        """, (xmin, ymin, xmax, ymax))
        
        aristas = cur.fetchall()
        
        # Cargar nodos
        cur.execute("""
            SELECT 
                id,
                ST_X(geom) as lon,
                ST_Y(geom) as lat,
                0.0 as p_fallo
            FROM infra_nodos
            WHERE ST_Intersects(
                geom,
                ST_MakeEnvelope(%s, %s, %s, %s, 4326)
            )
        """, (xmin, ymin, xmax, ymax))
        
        nodos = {}
        for row in cur.fetchall():
            row['lon'] = float(row['lon'])
            row['lat'] = float(row['lat'])
            nodos[row['id']] = row
            
        # Convertir aristas a float
        for arista in aristas:
            arista['length_m'] = float(arista['length_m'])
            arista['p_fallo'] = float(arista['p_fallo'])
        
        cur.close()
        
        print(f"📊 Grafo cargado: {len(nodos)} nodos, {len(aristas)} aristas")
        
        return aristas, nodos
    
    def solve(self, source: int, target: int, 
              max_risk: Optional[float] = None,
              max_distance: Optional[float] = None,
              lambda_risk: Optional[float] = None) -> Dict:
        """
        Resolver el problema de ruteo óptimo
        
        Args:
            source: ID del nodo origen
            target: ID del nodo destino
            max_risk: Riesgo máximo acumulado permitido (0-1)
            max_distance: Distancia máxima permitida en metros
            lambda_risk: Factor de penalización por riesgo (override)
            
        Returns:
            Diccionario con la solución:
            {
                'route': lista de IDs de aristas,
                'total_distance': distancia total en metros,
                'total_risk': riesgo acumulado,
                'computation_time': tiempo de cómputo en segundos,
                'status': estado de la solución
            }
        """
        if lambda_risk is not None:
            self.lambda_risk = lambda_risk
        
        print(f"🔍 Resolviendo ruta de {source} a {target}...")
        
        # Cargar grafo
        aristas, nodos = self.load_graph(source, target)
        
        if source not in nodos or target not in nodos:
            raise ValueError(f"Los nodos {source} o {target} no están en el grafo cargado")
        
        # Crear modelo
        model = gp.Model("resilient_routing")
        model.setParam('OutputFlag', 0)  # Silenciar output
        model.setParam('TimeLimit', self.max_time_limit)
        
        # Variables: x[arista_id] = 1 si la arista se usa, 0 si no
        x = {}
        for arista in aristas:
            x[arista['id']] = model.addVar(vtype=GRB.BINARY, name=f"x_{arista['id']}")
        
        # Función objetivo: minimizar distancia + lambda * riesgo
        objective = gp.LinExpr()
        for arista in aristas:
            cost = float(arista['length_m']) + self.lambda_risk * float(arista['length_m']) * arista['p_fallo']
            objective += cost * x[arista['id']]
        
        model.setObjective(objective, GRB.MINIMIZE)
        
        # Restricciones de conservación de flujo
        for nodo_id in nodos.keys():
            # Flujo saliente - flujo entrante
            flow = gp.LinExpr()
            
            for arista in aristas:
                if arista['source'] == nodo_id:
                    flow += x[arista['id']]
                if arista['target'] == nodo_id:
                    flow -= x[arista['id']]
            
            # Nodo origen: flujo neto = +1
            if nodo_id == source:
                model.addConstr(flow == 1, f"flow_source_{nodo_id}")
            # Nodo destino: flujo neto = -1
            elif nodo_id == target:
                model.addConstr(flow == -1, f"flow_target_{nodo_id}")
            # Otros nodos: flujo neto = 0
            else:
                model.addConstr(flow == 0, f"flow_{nodo_id}")
        
        # Restricción de riesgo máximo (si se especifica)
        if max_risk is not None:
            risk_expr = gp.LinExpr()
            for arista in aristas:
                risk_expr += arista['p_fallo'] * x[arista['id']]
            model.addConstr(risk_expr <= max_risk * len(aristas), "max_risk")
        
        # Restricción de distancia máxima (si se especifica)
        if max_distance is not None:
            distance_expr = gp.LinExpr()
            for arista in aristas:
                distance_expr += arista['length_m'] * x[arista['id']]
            model.addConstr(distance_expr <= max_distance, "max_distance")
        
        # Resolver
        print("⚙️  Resolviendo modelo MILP...")
        model.optimize()
        
        # Extraer solución
        result = {
            'status': model.status,
            'computation_time': model.Runtime,
            'route': [],
            'total_distance': 0.0,
            'total_risk': 0.0,
            'aristas_usadas': []
        }
        
        if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
            # Construir lista de adyacencia de aristas seleccionadas
            selected_adj = {}
            selected_edges = {}
            
            for arista in aristas:
                if x[arista['id']].X > 0.5:  # Variable binaria = 1
                    u, v = arista['source'], arista['target']
                    if u not in selected_adj: selected_adj[u] = []
                    if v not in selected_adj: selected_adj[v] = []
                    selected_adj[u].append(v)
                    selected_adj[v].append(u)
                    
                    # Guardar info de arista (clave ordenada para no duplicar en no dirigido)
                    key = tuple(sorted((u, v)))
                    selected_edges[key] = arista

            # Reconstruir camino desde source
            curr = source
            visited_edges = set()
            
            # Limite de seguridad para evitar bucles infinitos
            max_steps = len(selected_edges) + 10
            steps = 0
            
            while curr != target and steps < max_steps:
                steps += 1
                if curr not in selected_adj:
                    print(f"⚠️ Camino roto en nodo {curr}")
                    break
                
                # Encontrar siguiente nodo
                next_node = None
                for neighbor in selected_adj[curr]:
                    edge_key = tuple(sorted((curr, neighbor)))
                    if edge_key not in visited_edges:
                        next_node = neighbor
                        visited_edges.add(edge_key)
                        break
                
                if next_node is None:
                     print(f"⚠️ Sin salida o ciclo en nodo {curr}")
                     break
                
                # Agregar a resultado
                edge_key = tuple(sorted((curr, next_node)))
                arista = selected_edges[edge_key].copy()
                
                # Verificar dirección
                if arista['source'] == curr and arista['target'] == next_node:
                    arista['is_reversed'] = False
                else:
                    arista['is_reversed'] = True
                
                result['route'].append(arista['id'])
                result['total_distance'] += arista['length_m']
                result['total_risk'] += arista['p_fallo']
                result['aristas_usadas'].append(arista)
                
                curr = next_node
            
            print(f"✅ Solución encontrada:")
            print(f"   Distancia total: {result['total_distance']:.2f}m")
            print(f"   Riesgo acumulado: {result['total_risk']:.4f}")
            print(f"   Tiempo de cómputo: {result['computation_time']:.3f}s")
            print(f"   Aristas en ruta: {len(result['route'])}")
        else:
            print(f"❌ No se encontró solución óptima (status: {model.status})")
        
        self.close()
        return result
    
    def solution_to_geojson(self, solution: Dict) -> Dict:
        """
        Convertir solución a formato GeoJSON
        
        Args:
            solution: Solución del modelo
            
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        for i, arista in enumerate(solution['aristas_usadas']):
            geom = self._wkt_to_geojson(arista['geom_wkt'])
            
            # Reverse geometry if needed
            if arista.get('is_reversed', False) and geom['type'] == 'LineString':
                geom['coordinates'].reverse()
            
            feature = {
                'type': 'Feature',
                'geometry': geom,
                'properties': {
                    'seq': i + 1,
                    'edge_id': arista['id'],
                    'length_m': arista['length_m'],
                    'p_fallo': arista['p_fallo'],
                    'highway': arista['highway']
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'total_distance_m': solution['total_distance'],
                'total_risk': solution['total_risk'],
                'computation_time_s': solution['computation_time'],
                'num_segments': len(features)
            }
        }
    
    def _wkt_to_geojson(self, wkt: str) -> Dict:
        """
        Convertir WKT a geometría GeoJSON
        
        Args:
            wkt: Geometría en formato WKT
            
        Returns:
            Geometría GeoJSON
        """
        # Parsear WKT simple (solo LineString por ahora)
        if wkt.startswith('LINESTRING'):
            coords_str = wkt.replace('LINESTRING(', '').replace(')', '')
            coords = []
            for pair in coords_str.split(','):
                lon, lat = pair.strip().split()
                coords.append([float(lon), float(lat)])
            
            return {
                'type': 'LineString',
                'coordinates': coords
            }
        
        return {'type': 'Point', 'coordinates': [0, 0]}


def main():
    """Función de prueba"""
    if not GUROBI_AVAILABLE:
        print("❌ GUROBI no está disponible")
        sys.exit(1)
    
    router = ResilientRouter()
    
    # Ejemplo de uso
    try:
        solution = router.solve(
            source=1,
            target=100,
            max_risk=0.5,
            lambda_risk=5.0
        )
        
        if solution['route']:
            geojson = router.solution_to_geojson(solution)
            print("\n📄 GeoJSON generado:")
            print(f"   Features: {len(geojson['features'])}")
            print(f"   Metadata: {geojson['metadata']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
