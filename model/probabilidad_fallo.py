"""
Modelo de Probabilidad de Falla para Infraestructura Vial

Este módulo calcula la probabilidad de falla para nodos y aristas de la red vial
basándose en la proximidad a amenazas y condiciones de metadata ambiental.

Autor: Felipe Aros
Fecha: Noviembre 2025
"""

import os
import sys
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values
import math

# Configuración de conexión a Supabase
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': int(os.getenv('SUPABASE_DB_PORT', 6543)),
    'database': 'postgres',
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}


class ProbabilidadFalloCalculator:
    """Calculador de probabilidades de fallo para infraestructura vial"""
    
    def __init__(self, connection_params: Dict = None):
        """
        Inicializar el calculador
        
        Args:
            connection_params: Parámetros de conexión a PostgreSQL
        """
        self.conn_params = connection_params or DB_CONFIG
        self.conn = None
        
        # Parámetros del modelo (ajustables)
        self.PESO_INUNDACION = 0.4
        self.PESO_DGA = 0.3
        self.PESO_REPORTES = 0.2
        self.PESO_LLUVIA = 0.1
        
        # Radios de influencia (en metros)
        self.RADIO_INUNDACION = 500  # 500m de zona de inundación
        self.RADIO_DGA = 1000         # 1km de estación DGA
        self.RADIO_REPORTES = 200     # 200m de reporte ciudadano
        
    def connect(self):
        """Establecer conexión a la base de datos"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.conn_params)
        return self.conn
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def calcular_distancia_minima_amenaza(self, geom_wkt: str, tabla_amenaza: str) -> float:
        """
        Calcular la distancia mínima desde una geometría a la amenaza más cercana
        
        Args:
            geom_wkt: Geometría en formato WKT
            tabla_amenaza: Nombre de la tabla de amenazas
            
        Returns:
            Distancia en metros a la amenaza más cercana (o infinito si no hay amenazas)
        """
        cur = self.conn.cursor()
        
        query = f"""
        SELECT MIN(ST_Distance(
            ST_Transform(ST_GeomFromText(%s, 4326), 3857),
            ST_Transform(geom, 3857)
        )) as min_dist
        FROM {tabla_amenaza}
        WHERE geom IS NOT NULL;
        """
        
        cur.execute(query, (geom_wkt,))
        result = cur.fetchone()
        cur.close()
        
        return result[0] if result[0] is not None else float('inf')
    
    def calcular_factor_amenaza(self, distancia: float, radio_influencia: float) -> float:
        """
        Calcular factor de amenaza basado en distancia
        
        Usa función exponencial decreciente: factor = exp(-distancia/radio)
        
        Args:
            distancia: Distancia a la amenaza en metros
            radio_influencia: Radio de influencia en metros
            
        Returns:
            Factor entre 0 (muy lejos) y 1 (muy cerca)
        """
        if distancia == float('inf'):
            return 0.0
        
        # Función exponencial decreciente
        factor = math.exp(-distancia / radio_influencia)
        return min(max(factor, 0.0), 1.0)
    
    def calcular_probabilidad_nodo(self, nodo_id: int) -> float:
        """
        Calcular probabilidad de falla para un nodo específico
        
        Args:
            nodo_id: ID del nodo en infra_nodos
            
        Returns:
            Probabilidad de falla entre 0.0 y 1.0
        """
        cur = self.conn.cursor()
        
        # Obtener geometría del nodo
        cur.execute("SELECT ST_AsText(geom) FROM infra_nodos WHERE id = %s", (nodo_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            return 0.0
        
        geom_wkt = result[0]
        
        # Calcular distancias a amenazas
        dist_inundacion = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_inundaciones_hist')
        dist_dga = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_dga')
        dist_reportes = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_reportes_ciudadanos')
        
        # Calcular factores de amenaza
        factor_inundacion = self.calcular_factor_amenaza(dist_inundacion, self.RADIO_INUNDACION)
        factor_dga = self.calcular_factor_amenaza(dist_dga, self.RADIO_DGA)
        factor_reportes = self.calcular_factor_amenaza(dist_reportes, self.RADIO_REPORTES)
        
        # Calcular factor de lluvia (si hay datos de meta_lluvia cercanos)
        cur.execute("""
            SELECT AVG(precip_mm) 
            FROM meta_lluvia 
            WHERE ST_DWithin(
                ST_Transform(geom, 3857),
                ST_Transform(ST_GeomFromText(%s, 4326), 3857),
                1000
            )
        """, (geom_wkt,))
        result = cur.fetchone()
        lluvia_avg = result[0] if result[0] else 0.0
        factor_lluvia = min(lluvia_avg / 50.0, 1.0)  # Normalizar: 50mm+ = factor 1.0
        
        cur.close()
        
        # Combinar factores con pesos
        p_fallo = (
            self.PESO_INUNDACION * factor_inundacion +
            self.PESO_DGA * factor_dga +
            self.PESO_REPORTES * factor_reportes +
            self.PESO_LLUVIA * factor_lluvia
        )
        
        return min(max(p_fallo, 0.0), 1.0)
    
    def calcular_probabilidad_arista(self, arista_id: int) -> float:
        """
        Calcular probabilidad de falla para una arista específica
        
        Para aristas, usamos el punto medio de la LineString
        
        Args:
            arista_id: ID de la arista en infra_aristas
            
        Returns:
            Probabilidad de falla entre 0.0 y 1.0
        """
        cur = self.conn.cursor()
        
        # Obtener punto medio de la arista
        cur.execute("""
            SELECT ST_AsText(ST_LineInterpolatePoint(geom, 0.5))
            FROM infra_aristas 
            WHERE id = %s
        """, (arista_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            return 0.0
        
        geom_wkt = result[0]
        
        # Reutilizar lógica de nodos (podría refinarse)
        # Calcular distancias a amenazas
        dist_inundacion = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_inundaciones_hist')
        dist_dga = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_dga')
        dist_reportes = self.calcular_distancia_minima_amenaza(geom_wkt, 'amenaza_reportes_ciudadanos')
        
        # Calcular factores de amenaza
        factor_inundacion = self.calcular_factor_amenaza(dist_inundacion, self.RADIO_INUNDACION)
        factor_dga = self.calcular_factor_amenaza(dist_dga, self.RADIO_DGA)
        factor_reportes = self.calcular_factor_amenaza(dist_reportes, self.RADIO_REPORTES)
        
        # Calcular factor de lluvia
        cur.execute("""
            SELECT AVG(precip_mm) 
            FROM meta_lluvia 
            WHERE ST_DWithin(
                ST_Transform(geom, 3857),
                ST_Transform(ST_GeomFromText(%s, 4326), 3857),
                1000
            )
        """, (geom_wkt,))
        result = cur.fetchone()
        lluvia_avg = result[0] if result[0] else 0.0
        factor_lluvia = min(lluvia_avg / 50.0, 1.0)
        
        cur.close()
        
        # Combinar factores con pesos
        p_fallo = (
            self.PESO_INUNDACION * factor_inundacion +
            self.PESO_DGA * factor_dga +
            self.PESO_REPORTES * factor_reportes +
            self.PESO_LLUVIA * factor_lluvia
        )
        
        return min(max(p_fallo, 0.0), 1.0)
    
    def actualizar_todas_probabilidades(self, batch_size: int = 1000):
        """
        Actualizar probabilidades de falla para todos los nodos y aristas
        
        Args:
            batch_size: Tamaño de lote para actualizaciones
        """
        print("🔄 Iniciando cálculo de probabilidades de falla...")
        
        self.connect()
        cur = self.conn.cursor()
        
        # Actualizar nodos
        print("\n📍 Actualizando probabilidades de nodos...")
        cur.execute("SELECT COUNT(*) FROM infra_nodos")
        total_nodos = cur.fetchone()[0]
        print(f"   Total de nodos: {total_nodos}")
        
        cur.execute("SELECT id FROM infra_nodos ORDER BY id")
        nodo_ids = [row[0] for row in cur.fetchall()]
        
        updates_nodos = []
        for i, nodo_id in enumerate(nodo_ids):
            p_fallo = self.calcular_probabilidad_nodo(nodo_id)
            updates_nodos.append((p_fallo, nodo_id))
            
            if (i + 1) % 100 == 0:
                print(f"   Procesados {i + 1}/{total_nodos} nodos ({(i+1)/total_nodos*100:.1f}%)")
            
            # Actualizar en lotes
            if len(updates_nodos) >= batch_size:
                cur.executemany(
                    "UPDATE infra_nodos SET p_fallo_nodo = %s WHERE id = %s",
                    updates_nodos
                )
                self.conn.commit()
                updates_nodos = []
        
        # Actualizar nodos restantes
        if updates_nodos:
            cur.executemany(
                "UPDATE infra_nodos SET p_fallo_nodo = %s WHERE id = %s",
                updates_nodos
            )
            self.conn.commit()
        
        print(f"✅ Nodos actualizados: {total_nodos}")
        
        # Actualizar aristas
        print("\n🛣️  Actualizando probabilidades de aristas...")
        cur.execute("SELECT COUNT(*) FROM infra_aristas")
        total_aristas = cur.fetchone()[0]
        print(f"   Total de aristas: {total_aristas}")
        
        cur.execute("SELECT id FROM infra_aristas ORDER BY id")
        arista_ids = [row[0] for row in cur.fetchall()]
        
        updates_aristas = []
        for i, arista_id in enumerate(arista_ids):
            p_fallo = self.calcular_probabilidad_arista(arista_id)
            updates_aristas.append((p_fallo, arista_id))
            
            if (i + 1) % 100 == 0:
                print(f"   Procesadas {i + 1}/{total_aristas} aristas ({(i+1)/total_aristas*100:.1f}%)")
            
            # Actualizar en lotes
            if len(updates_aristas) >= batch_size:
                cur.executemany(
                    "UPDATE infra_aristas SET p_fallo_arista = %s WHERE id = %s",
                    updates_aristas
                )
                self.conn.commit()
                updates_aristas = []
        
        # Actualizar aristas restantes
        if updates_aristas:
            cur.executemany(
                "UPDATE infra_aristas SET p_fallo_arista = %s WHERE id = %s",
                updates_aristas
            )
            self.conn.commit()
        
        print(f"✅ Aristas actualizadas: {total_aristas}")
        
        cur.close()
        self.close()
        
        print("\n✅ ¡Cálculo de probabilidades completado!")


def main():
    """Función principal para ejecutar desde línea de comandos"""
    calculator = ProbabilidadFalloCalculator()
    
    try:
        calculator.actualizar_todas_probabilidades(batch_size=1000)
    except Exception as e:
        print(f"❌ Error al calcular probabilidades: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
