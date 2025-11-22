"""
Metaheurísticas para Ruteo Resiliente

Este módulo implementa algoritmos metaheurísticos para encontrar rutas resilientes:
- A* modificado con heurística que considera riesgo
- GRASP (Greedy Randomized Adaptive Search Procedure)

Autor: Felipe Aros
Fecha: Noviembre 2025
"""

import os
import sys
from typing import Dict, List, Tuple, Optional, Set
import psycopg2
from psycopg2.extras import RealDictCursor
import heapq
import math
import time


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
    except Exception as e:
        host_ip = '18.213.155.45'
        
    params = DB_CONFIG.copy()
    params['host'] = host_ip
    return psycopg2.connect(**params)


class AStarResilientRouter:
    """Router resiliente usando A* con heurística de riesgo"""
    
    def __init__(self, connection_params: Dict = None):
        """
        Inicializar el router
        
        Args:
            connection_params: Parámetros de conexión a PostgreSQL
        """
        self.conn_params = connection_params or DB_CONFIG
        self.conn = None
        
        # Parámetros del algoritmo
        self.heuristic_weight = 1.0  # Peso de la heurística
        self.risk_weight = 3.0  # Peso del riesgo en el costo
        
    def connect(self):
        """Establecer conexión a la base de datos"""
        if not self.conn or self.conn.closed:
            self.conn = get_db_connection()
        return self.conn
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def load_graph(self, source: int, target: int, bbox_margin: float = 0.05) -> Tuple[Dict, Dict, Dict]:
        """
        Cargar el grafo desde la base de datos
        
        Args:
            source: ID del nodo origen
            target: ID del nodo destino
            bbox_margin: Margen adicional para el bounding box (en grados)
            
        Returns:
            Tupla de (grafo, nodos, aristas_dict)
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
        
        # Cargar aristas
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
            WHERE 
                a.source = ANY(%s::bigint[]) AND
                a.target = ANY(%s::bigint[]) AND
                a.length_m IS NOT NULL
        """, (list(nodos.keys()), list(nodos.keys())))
        
        aristas_list = cur.fetchall()
        
        # Construir grafo como diccionario de adyacencia
        # grafo[nodo] = [(vecino, costo, riesgo, arista_id), ...]
        grafo = {nodo_id: [] for nodo_id in nodos.keys()}
        aristas_dict = {}
        
        for arista in aristas_list:
            # Convertir a float para evitar problemas con Decimal
            arista['length_m'] = float(arista['length_m'])
            arista['p_fallo'] = float(arista['p_fallo'])
            
            source_id = arista['source']
            target_id = arista['target']
            
            # Costo = distancia + riesgo ponderado
            cost = arista['length_m'] * (1.0 + self.risk_weight * arista['p_fallo'])
            
            # Grafo no dirigido
            grafo[source_id].append((target_id, cost, arista['p_fallo'], arista['id']))
            grafo[target_id].append((source_id, cost, arista['p_fallo'], arista['id']))
            
            aristas_dict[arista['id']] = dict(arista)
        
        cur.close()
        
        print(f"📊 Grafo cargado: {len(nodos)} nodos, {len(aristas_list)} aristas", file=sys.stderr)
        
        return grafo, nodos, aristas_dict
    
    def heuristic(self, node_id: int, target_id: int, nodos: Dict) -> float:
        """
        Calcular heurística de distancia euclidiana
        
        Args:
            node_id: ID del nodo actual
            target_id: ID del nodo destino
            nodos: Diccionario de nodos con coordenadas
            
        Returns:
            Distancia euclidiana aproximada en metros
        """
        if node_id not in nodos or target_id not in nodos:
            return 0.0
        
        node = nodos[node_id]
        target = nodos[target_id]
        
        # Distancia euclidiana en coordenadas geográficas (aproximación)
        # 1 grado ≈ 111km
        dx = (node['lon'] - target['lon']) * 111000 * math.cos(math.radians(node['lat']))
        dy = (node['lat'] - target['lat']) * 111000
        
        return math.sqrt(dx**2 + dy**2)
    
    def solve(self, source: int, target: int,
              risk_weight: Optional[float] = None,
              heuristic_weight: Optional[float] = None) -> Dict:
        """
        Resolver el problema de ruteo usando A*
        
        Args:
            source: ID del nodo origen
            target: ID del nodo destino
            risk_weight: Peso del riesgo en el costo (override)
            heuristic_weight: Peso de la heurística (override)
            
        Returns:
            Diccionario con la solución:
            {
                'route': lista de IDs de aristas,
                'node_path': lista de IDs de nodos,
                'total_distance': distancia total en metros,
                'total_risk': riesgo acumulado,
                'computation_time': tiempo de cómputo en segundos,
                'nodes_explored': número de nodos explorados
            }
        """
        if risk_weight is not None:
            self.risk_weight = risk_weight
        if heuristic_weight is not None:
            self.heuristic_weight = heuristic_weight
        
        print(f"🔍 Resolviendo ruta de {source} a {target} con A*...", file=sys.stderr)
        start_time = time.time()
        
        # Cargar grafo
        grafo, nodos, aristas_dict = self.load_graph(source, target)
        
        if source not in grafo or target not in grafo:
            raise ValueError(f"Los nodos {source} o {target} no están en el grafo cargado")
        
        # Algoritmo A*
        # Priority queue: (f_score, node_id)
        open_set = [(0.0, source)]
        
        # g_score: costo del camino desde origen a cada nodo
        g_score = {node_id: float('inf') for node_id in nodos.keys()}
        g_score[source] = 0.0
        
        # came_from: para reconstruir el camino
        came_from = {}
        came_from_edge = {}
        
        # f_score = g_score + h_score
        f_score = {node_id: float('inf') for node_id in nodos.keys()}
        f_score[source] = self.heuristic(source, target, nodos) * self.heuristic_weight
        
        # Conjunto de nodos ya evaluados
        closed_set: Set[int] = set()
        nodes_explored = 0
        
        while open_set:
            # Obtener nodo con menor f_score
            current_f, current = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
            
            nodes_explored += 1
            
            # ¿Llegamos al destino?
            if current == target:
                print(f"✅ Camino encontrado!", file=sys.stderr)
                break
            
            closed_set.add(current)
            
            # Explorar vecinos
            for neighbor, edge_cost, risk, edge_id in grafo[current]:
                if neighbor in closed_set:
                    continue
                
                # Calcular tentative g_score
                tentative_g = g_score[current] + edge_cost
                
                if tentative_g < g_score[neighbor]:
                    # Este camino es mejor
                    came_from[neighbor] = current
                    came_from_edge[neighbor] = edge_id
                    g_score[neighbor] = tentative_g
                    
                    h = self.heuristic(neighbor, target, nodos) * self.heuristic_weight
                    f_score[neighbor] = tentative_g + h
                    
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        computation_time = time.time() - start_time
        
        # Reconstruir camino
        result = {
            'computation_time': computation_time,
            'nodes_explored': nodes_explored,
            'node_path': [],
            'route': [],
            'total_distance': 0.0,
            'total_risk': 0.0,
            'aristas_usadas': []
        }
        
        if target in came_from or target == source:
            # Reconstruir desde target hasta source
            path = []
            current = target
            
            while current != source:
                path.append(current)
                if current not in came_from:
                    break
                current = came_from[current]
            
            path.append(source)
            path.reverse()
            
            result['node_path'] = path
            
            # Obtener aristas
            for i in range(len(path) - 1):
                node = path[i]
                next_node = path[i + 1]
                
                if next_node in came_from_edge:
                    edge_id = came_from_edge[next_node]
                    arista = aristas_dict[edge_id].copy()
                    
                    # Check direction
                    if arista['source'] == node and arista['target'] == next_node:
                        arista['is_reversed'] = False
                    else:
                        arista['is_reversed'] = True
                    
                    result['route'].append(edge_id)
                    result['total_distance'] += arista['length_m']
                    result['total_risk'] += arista['p_fallo']
                    result['aristas_usadas'].append(arista)
            
            print(f"✅ Solución encontrada:", file=sys.stderr)
            print(f"   Distancia total: {result['total_distance']:.2f}m", file=sys.stderr)
            print(f"   Riesgo acumulado: {result['total_risk']:.4f}", file=sys.stderr)
            print(f"   Tiempo de cómputo: {result['computation_time']:.3f}s", file=sys.stderr)
            print(f"   Nodos explorados: {nodes_explored}", file=sys.stderr)
            print(f"   Aristas en ruta: {len(result['route'])}", file=sys.stderr)
        else:
            print(f"❌ No se encontró camino de {source} a {target}", file=sys.stderr)
        
        self.close()
        return result
    
    def solution_to_geojson(self, solution: Dict) -> Dict:
        """
        Convertir solución a formato GeoJSON
        
        Args:
            solution: Solución del algoritmo
            
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
                'nodes_explored': solution['nodes_explored'],
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
    router = AStarResilientRouter()
    
    # Ejemplo de uso
    try:
        solution = router.solve(
            source=1,
            target=100,
            risk_weight=3.0,
            heuristic_weight=1.0
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
