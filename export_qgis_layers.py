#!/usr/bin/env python3
"""
Script para exportar capas de datos a GeoJSON para visualizacion en QGIS.
Genera multiples capas con datos del sistema de ruteo resiliente.

Uso:
    python export_qgis_layers.py

Salida:
    qgis_data/
        - aristas_riesgo.geojson          (red vial con probabilidad de falla)
        - aristas_alto_riesgo.geojson     (solo aristas con p >= 0.3)
        - aristas_muy_alto_riesgo.geojson (solo aristas con p >= 0.5)
        - nodos.geojson                   (nodos de la red)
        - amenaza_dga.geojson             (estaciones DGA)
        - amenaza_pasos_bajo_nivel.geojson
        - amenaza_reportes.geojson
        - buffer_dga_1000m.geojson        (buffers de amenazas)
        - buffer_pasos_500m.geojson
        - buffer_reportes_200m.geojson
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuracion de conexion
DB_URL = os.getenv('SUPABASE_DB_URL',
    'postgresql://postgres.eqjzlgbjgwbnvqzbomsn:femaarroD4rK@aws-1-us-east-1.pooler.supabase.com:6543/postgres')

# Directorio de salida
OUTPUT_DIR = 'qgis_data'

def get_connection():
    """Obtiene conexion a la base de datos."""
    return psycopg2.connect(DB_URL)

def export_geojson(cursor, query, filename, description):
    """Ejecuta query y exporta resultado como GeoJSON."""
    print(f"Exportando: {description}...")

    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        print(f"  [!] Sin datos para {filename}")
        return 0

    features = []
    for row in rows:
        # Parsear geometria GeoJSON
        geom = json.loads(row['geom'])

        # Crear propiedades (todo excepto geom), convertir datetime a string
        properties = {}
        for k, v in row.items():
            if k != 'geom':
                if hasattr(v, 'isoformat'):  # datetime/date
                    properties[k] = v.isoformat()
                else:
                    properties[k] = v

        feature = {
            "type": "Feature",
            "geometry": geom,
            "properties": properties
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "name": filename.replace('.geojson', ''),
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)

    print(f"  [OK] {len(features)} features -> {filepath}")
    return len(features)

def main():
    """Funcion principal de exportacion."""

    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("EXPORTACION DE CAPAS PARA QGIS")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    queries = [
        # 1. Red vial completa con riesgo
        {
            "filename": "aristas_riesgo.geojson",
            "description": "Red vial completa con probabilidad de falla",
            "query": """
                SELECT
                    id,
                    source,
                    target,
                    highway,
                    length_m,
                    p_fallo_arista,
                    CASE
                        WHEN p_fallo_arista < 0.1 THEN 'bajo'
                        WHEN p_fallo_arista < 0.3 THEN 'medio'
                        WHEN p_fallo_arista < 0.5 THEN 'alto'
                        ELSE 'muy_alto'
                    END as categoria_riesgo,
                    ST_AsGeoJSON(geom) as geom
                FROM infra_aristas
                WHERE highway NOT IN ('footway', 'steps', 'pedestrian', 'path')
                LIMIT 50000
            """
        },

        # 2. Solo aristas de alto riesgo
        {
            "filename": "aristas_alto_riesgo.geojson",
            "description": "Aristas con riesgo >= 0.3",
            "query": """
                SELECT
                    id,
                    highway,
                    length_m,
                    p_fallo_arista,
                    ST_AsGeoJSON(geom) as geom
                FROM infra_aristas
                WHERE p_fallo_arista >= 0.3
            """
        },

        # 3. Solo aristas de muy alto riesgo
        {
            "filename": "aristas_muy_alto_riesgo.geojson",
            "description": "Aristas con riesgo >= 0.5",
            "query": """
                SELECT
                    id,
                    highway,
                    length_m,
                    p_fallo_arista,
                    ST_AsGeoJSON(geom) as geom
                FROM infra_aristas
                WHERE p_fallo_arista >= 0.5
            """
        },

        # 4. Aristas por tipo de via principal
        {
            "filename": "aristas_primarias.geojson",
            "description": "Vias primarias y secundarias",
            "query": """
                SELECT
                    id,
                    highway,
                    length_m,
                    p_fallo_arista,
                    ST_AsGeoJSON(geom) as geom
                FROM infra_aristas
                WHERE highway IN ('primary', 'secondary', 'tertiary', 'motorway')
            """
        },

        # 5. Estaciones DGA
        {
            "filename": "amenaza_dga.geojson",
            "description": "Estaciones de monitoreo DGA",
            "query": """
                SELECT
                    id,
                    station_id,
                    properties->>'nombre' as nombre,
                    properties->>'tipo' as tipo,
                    properties->>'cuenca' as cuenca,
                    ST_AsGeoJSON(geom) as geom
                FROM amenaza_dga
            """
        },

        # 6. Pasos bajo nivel
        {
            "filename": "amenaza_pasos_bajo_nivel.geojson",
            "description": "Pasos bajo nivel vulnerables",
            "query": """
                SELECT
                    id,
                    name as nombre,
                    description as descripcion,
                    severity as severidad,
                    ST_AsGeoJSON(geom) as geom
                FROM amenaza_pasos_bajo_nivel
            """
        },

        # 7. Reportes ciudadanos
        {
            "filename": "amenaza_reportes.geojson",
            "description": "Reportes ciudadanos de inundacion",
            "query": """
                SELECT
                    id,
                    description as descripcion,
                    reported_at as fecha,
                    ST_AsGeoJSON(geom) as geom
                FROM amenaza_reportes_ciudadanos
            """
        },

        # 8. Buffer DGA 1000m
        {
            "filename": "buffer_dga_1000m.geojson",
            "description": "Buffer de influencia DGA (1000m)",
            "query": """
                SELECT
                    id,
                    station_id,
                    properties->>'nombre' as nombre,
                    1000 as radio_m,
                    ST_AsGeoJSON(ST_Buffer(geom::geography, 1000)::geometry) as geom
                FROM amenaza_dga
            """
        },

        # 9. Buffer pasos bajo nivel 500m
        {
            "filename": "buffer_pasos_500m.geojson",
            "description": "Buffer de influencia pasos bajo nivel (500m)",
            "query": """
                SELECT
                    id,
                    name as nombre,
                    500 as radio_m,
                    ST_AsGeoJSON(ST_Buffer(geom::geography, 500)::geometry) as geom
                FROM amenaza_pasos_bajo_nivel
            """
        },

        # 10. Buffer reportes 200m
        {
            "filename": "buffer_reportes_200m.geojson",
            "description": "Buffer de influencia reportes (200m)",
            "query": """
                SELECT
                    id,
                    description as descripcion,
                    200 as radio_m,
                    ST_AsGeoJSON(ST_Buffer(geom::geography, 200)::geometry) as geom
                FROM amenaza_reportes_ciudadanos
            """
        },

        # 11. Nodos de alta conectividad (grado > 3)
        {
            "filename": "nodos_intersecciones.geojson",
            "description": "Intersecciones principales (grado > 3)",
            "query": """
                WITH node_degree AS (
                    SELECT
                        n.id,
                        n.geom,
                        COUNT(DISTINCT a.id) as grado
                    FROM infra_nodos n
                    JOIN infra_aristas a ON (a.source = n.id OR a.target = n.id)
                    GROUP BY n.id, n.geom
                    HAVING COUNT(DISTINCT a.id) > 3
                )
                SELECT
                    id,
                    grado,
                    ST_AsGeoJSON(geom) as geom
                FROM node_degree
                LIMIT 10000
            """
        },

        # 12. Cluster de alto riesgo (centroide de zonas criticas)
        {
            "filename": "zonas_criticas_centroid.geojson",
            "description": "Centroides de zonas de alto riesgo",
            "query": """
                WITH high_risk_clusters AS (
                    SELECT
                        ST_ClusterKMeans(geom, 20) OVER() as cluster_id,
                        geom,
                        p_fallo_arista
                    FROM infra_aristas
                    WHERE p_fallo_arista >= 0.4
                )
                SELECT
                    cluster_id,
                    COUNT(*) as num_aristas,
                    AVG(p_fallo_arista) as riesgo_promedio,
                    ST_AsGeoJSON(ST_Centroid(ST_Collect(geom))) as geom
                FROM high_risk_clusters
                GROUP BY cluster_id
            """
        },

        # 13. Corredores de riesgo (aristas conectadas de alto riesgo)
        {
            "filename": "corredores_riesgo.geojson",
            "description": "Corredores de vias de alto riesgo conectadas",
            "query": """
                SELECT
                    id,
                    highway,
                    length_m,
                    p_fallo_arista,
                    source,
                    target,
                    ST_AsGeoJSON(geom) as geom
                FROM infra_aristas
                WHERE p_fallo_arista >= 0.35
                AND highway IN ('primary', 'secondary', 'tertiary', 'residential', 'living_street')
            """
        }
    ]

    total_features = 0

    for q in queries:
        try:
            count = export_geojson(
                cursor,
                q['query'],
                q['filename'],
                q['description']
            )
            total_features += count
        except Exception as e:
            print(f"  [ERROR] {q['filename']}: {e}")

    cursor.close()
    conn.close()

    print("=" * 60)
    print(f"Exportacion completada: {total_features} features totales")
    print(f"Archivos en: {os.path.abspath(OUTPUT_DIR)}/")
    print("=" * 60)

    # Crear archivo de instrucciones para QGIS
    create_qgis_instructions()

def create_qgis_instructions():
    """Crea archivo con instrucciones para QGIS."""

    instructions = """# Instrucciones para QGIS

## Cargar capas

1. Abrir QGIS
2. Arrastrar archivos .geojson a la ventana de capas
3. O usar: Capa > Anadir capa > Anadir capa vectorial

## Orden de capas recomendado (de arriba a abajo)

1. amenaza_pasos_bajo_nivel (puntos rojos)
2. amenaza_reportes (puntos morados)
3. amenaza_dga (puntos azules)
4. aristas_muy_alto_riesgo (lineas rojas gruesas)
5. aristas_alto_riesgo (lineas naranjas)
6. aristas_primarias (lineas grises)
7. buffer_pasos_500m (poligonos rojos transparentes)
8. buffer_reportes_200m (poligonos morados transparentes)
9. buffer_dga_1000m (poligonos azules transparentes)
10. OpenStreetMap (base)

## Estilos recomendados

### Aristas por riesgo (aristas_riesgo.geojson)
- Estilo: Categorizado
- Columna: categoria_riesgo
- Valores:
  - bajo: #2ecc71 (verde), ancho 0.5
  - medio: #f1c40f (amarillo), ancho 0.8
  - alto: #e67e22 (naranja), ancho 1.2
  - muy_alto: #e74c3c (rojo), ancho 2.0

### Aristas alto riesgo (graduado por p_fallo)
- Estilo: Graduado
- Columna: p_fallo_arista
- Metodo: Quantile, 5 clases
- Rampa: RdYlGn invertida
- Ancho: 1.5 - 3.0

### Buffers de amenazas
- Relleno: color con 20% opacidad
- Borde: color solido, 0.5px
- DGA: #3498db
- Pasos: #e74c3c
- Reportes: #9b59b6

### Puntos de amenazas
- Marcador simple
- Tamano: 8-12 puntos
- Con etiqueta del nombre

## Mapas sugeridos para el informe

1. **Mapa general de la red**
   - Capas: aristas_primarias + base OSM
   - Escala: 1:150,000
   - Mostrar extension de la red

2. **Mapa de distribucion de riesgo**
   - Capas: aristas_riesgo (categorizado)
   - Escala: 1:100,000
   - Leyenda con categorias

3. **Mapa de zonas criticas**
   - Capas: aristas_muy_alto_riesgo + zonas_criticas_centroid
   - Escala: 1:50,000
   - Zoom a zona con mas riesgo

4. **Mapa de amenazas y buffers**
   - Capas: todos los buffers + puntos de amenazas
   - Escala: 1:100,000
   - Mostrar superposicion de amenazas

5. **Mapa de detalle: zona centro**
   - Capas: aristas_alto_riesgo + amenazas
   - Extent: -70.68, -33.47 a -70.62, -33.43
   - Escala: 1:25,000

6. **Mapa de corredores de riesgo**
   - Capas: corredores_riesgo + intersecciones
   - Identificar rutas criticas

## Exportar mapas

1. Proyecto > Nuevo diseno de impresion
2. Agregar mapa, leyenda, escala, norte
3. Exportar como imagen (300 DPI para informe)

## Composicion de mapa para IEEE

- Tamano: 3.5" x 3" (columna simple) o 7" x 5" (doble columna)
- DPI: 300
- Formato: PNG o TIFF
- Incluir: escala grafica, leyenda compacta, norte
"""

    filepath = os.path.join(OUTPUT_DIR, 'INSTRUCCIONES_QGIS.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(instructions)

    print(f"\nInstrucciones guardadas en: {filepath}")

if __name__ == '__main__':
    main()
