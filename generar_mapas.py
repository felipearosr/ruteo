#!/usr/bin/env python3
"""
Genera mapas PNG para el informe usando matplotlib y geopandas.
No requiere QGIS.

Uso:
    python generar_mapas.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import contextily as ctx
import os
import warnings
warnings.filterwarnings('ignore')

# Configuracion
QGIS_DIR = 'qgis_data'
OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CRS para visualizacion con tiles
WEB_MERCATOR = 'EPSG:3857'
WGS84 = 'EPSG:4326'

def load_geojson(filename):
    """Carga GeoJSON como GeoDataFrame."""
    filepath = os.path.join(QGIS_DIR, filename)
    if os.path.exists(filepath):
        gdf = gpd.read_file(filepath)
        return gdf
    print(f"  [!] No encontrado: {filename}")
    return None

def add_basemap(ax, zoom=12):
    """Agrega mapa base de OpenStreetMap."""
    try:
        ctx.add_basemap(ax, crs=WEB_MERCATOR, source=ctx.providers.CartoDB.Positron, zoom=zoom)
    except Exception as e:
        print(f"  [!] No se pudo cargar mapa base: {e}")

print("=" * 60)
print("GENERANDO MAPAS PARA EL INFORME")
print("=" * 60)

# ============================================================
# MAPA 1: Red Vial Principal
# ============================================================
print("\n[1/6] Generando: fig_red_vial_santiago.png")

fig, ax = plt.subplots(figsize=(12, 10))

primarias = load_geojson('aristas_primarias.geojson')
if primarias is not None:
    primarias = primarias.to_crs(WEB_MERCATOR)

    # Colores por tipo de via
    colors = {
        'motorway': '#e74c3c',
        'primary': '#e67e22',
        'secondary': '#f1c40f',
        'tertiary': '#3498db'
    }
    linewidths = {
        'motorway': 2.0,
        'primary': 1.5,
        'secondary': 1.2,
        'tertiary': 0.8
    }

    for highway_type in ['tertiary', 'secondary', 'primary', 'motorway']:
        subset = primarias[primarias['highway'] == highway_type]
        if len(subset) > 0:
            subset.plot(ax=ax, color=colors.get(highway_type, 'gray'),
                       linewidth=linewidths.get(highway_type, 1), label=highway_type)

    add_basemap(ax, zoom=11)

    # Leyenda
    legend_elements = [
        Line2D([0], [0], color='#e74c3c', linewidth=2, label='Motorway'),
        Line2D([0], [0], color='#e67e22', linewidth=1.5, label='Primary'),
        Line2D([0], [0], color='#f1c40f', linewidth=1.2, label='Secondary'),
        Line2D([0], [0], color='#3498db', linewidth=0.8, label='Tertiary')
    ]
    ax.legend(handles=legend_elements, loc='upper right', title='Tipo de Via')

    ax.set_title('Red Vial Principal - Santiago de Chile', fontsize=14, fontweight='bold')
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/fig_red_vial_santiago.png', dpi=300, bbox_inches='tight')
    print(f"  [OK] {OUTPUT_DIR}/fig_red_vial_santiago.png")
plt.close()

# ============================================================
# MAPA 2: Distribucion de Riesgo
# ============================================================
print("\n[2/6] Generando: fig_distribucion_riesgo.png")

fig, ax = plt.subplots(figsize=(12, 10))

riesgo = load_geojson('aristas_riesgo.geojson')
if riesgo is not None:
    riesgo = riesgo.to_crs(WEB_MERCATOR)

    # Clasificar por riesgo
    riesgo['risk_cat'] = 'bajo'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.2, 'risk_cat'] = 'medio'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.3, 'risk_cat'] = 'alto'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.5, 'risk_cat'] = 'muy_alto'

    colors_risk = {
        'bajo': '#2ecc71',
        'medio': '#f1c40f',
        'alto': '#e67e22',
        'muy_alto': '#e74c3c'
    }

    for cat in ['bajo', 'medio', 'alto', 'muy_alto']:
        subset = riesgo[riesgo['risk_cat'] == cat]
        if len(subset) > 0:
            lw = 0.3 if cat == 'bajo' else (0.5 if cat == 'medio' else (1.0 if cat == 'alto' else 2.0))
            subset.plot(ax=ax, color=colors_risk[cat], linewidth=lw)

    add_basemap(ax, zoom=11)

    legend_elements = [
        Line2D([0], [0], color='#2ecc71', linewidth=1, label='Bajo (< 0.2)'),
        Line2D([0], [0], color='#f1c40f', linewidth=1.5, label='Medio (0.2 - 0.3)'),
        Line2D([0], [0], color='#e67e22', linewidth=2, label='Alto (0.3 - 0.5)'),
        Line2D([0], [0], color='#e74c3c', linewidth=3, label='Muy Alto (> 0.5)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', title='Probabilidad de Falla')

    ax.set_title('Distribucion de Riesgo en la Red Vial', fontsize=14, fontweight='bold')
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/fig_distribucion_riesgo.png', dpi=300, bbox_inches='tight')
    print(f"  [OK] {OUTPUT_DIR}/fig_distribucion_riesgo.png")
plt.close()

# ============================================================
# MAPA 3: Zonas de Alto Riesgo
# ============================================================
print("\n[3/6] Generando: fig_zonas_alto_riesgo.png")

fig, ax = plt.subplots(figsize=(12, 10))

alto = load_geojson('aristas_alto_riesgo.geojson')
muy_alto = load_geojson('aristas_muy_alto_riesgo.geojson')

if alto is not None:
    alto = alto.to_crs(WEB_MERCATOR)
    alto.plot(ax=ax, color='#e67e22', linewidth=1.5, label='Alto (0.3-0.5)')

if muy_alto is not None:
    muy_alto = muy_alto.to_crs(WEB_MERCATOR)
    muy_alto.plot(ax=ax, color='#e74c3c', linewidth=2.5, label='Muy Alto (>0.5)')

add_basemap(ax, zoom=11)

legend_elements = [
    Line2D([0], [0], color='#e67e22', linewidth=2, label='Alto (0.3 - 0.5)'),
    Line2D([0], [0], color='#e74c3c', linewidth=3, label='Muy Alto (> 0.5)')
]
ax.legend(handles=legend_elements, loc='upper right', title='Nivel de Riesgo')

ax.set_title('Aristas de Alto y Muy Alto Riesgo', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_zonas_alto_riesgo.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_zonas_alto_riesgo.png")
plt.close()

# ============================================================
# MAPA 4: Amenazas y Buffers
# ============================================================
print("\n[4/6] Generando: fig_amenazas_santiago.png")

fig, ax = plt.subplots(figsize=(12, 10))

# Cargar buffers
buffer_dga = load_geojson('buffer_dga_1000m.geojson')
buffer_pasos = load_geojson('buffer_pasos_500m.geojson')
buffer_reportes = load_geojson('buffer_reportes_200m.geojson')

# Cargar puntos
dga = load_geojson('amenaza_dga.geojson')
pasos = load_geojson('amenaza_pasos_bajo_nivel.geojson')
reportes = load_geojson('amenaza_reportes.geojson')

# Plotear buffers (primero, como fondo)
if buffer_dga is not None:
    buffer_dga = buffer_dga.to_crs(WEB_MERCATOR)
    buffer_dga.plot(ax=ax, color='#3498db', alpha=0.2, edgecolor='#2980b9', linewidth=0.5)

if buffer_pasos is not None:
    buffer_pasos = buffer_pasos.to_crs(WEB_MERCATOR)
    buffer_pasos.plot(ax=ax, color='#e74c3c', alpha=0.25, edgecolor='#c0392b', linewidth=0.5)

if buffer_reportes is not None:
    buffer_reportes = buffer_reportes.to_crs(WEB_MERCATOR)
    buffer_reportes.plot(ax=ax, color='#9b59b6', alpha=0.25, edgecolor='#8e44ad', linewidth=0.5)

# Plotear puntos
if dga is not None:
    dga = dga.to_crs(WEB_MERCATOR)
    dga.plot(ax=ax, color='#3498db', markersize=30, marker='o', edgecolor='white', linewidth=0.5)

if reportes is not None:
    reportes = reportes.to_crs(WEB_MERCATOR)
    reportes.plot(ax=ax, color='#9b59b6', markersize=40, marker='^', edgecolor='white', linewidth=0.5)

if pasos is not None:
    pasos = pasos.to_crs(WEB_MERCATOR)
    pasos.plot(ax=ax, color='#e74c3c', markersize=60, marker='s', edgecolor='white', linewidth=0.5)

add_basemap(ax, zoom=11)

legend_elements = [
    mpatches.Patch(facecolor='#3498db', alpha=0.3, edgecolor='#2980b9', label='Buffer DGA (1000m)'),
    mpatches.Patch(facecolor='#e74c3c', alpha=0.3, edgecolor='#c0392b', label='Buffer Pasos BN (500m)'),
    mpatches.Patch(facecolor='#9b59b6', alpha=0.3, edgecolor='#8e44ad', label='Buffer Reportes (200m)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=8, label='Estaciones DGA (94)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#e74c3c', markersize=8, label='Pasos Bajo Nivel (20)'),
    Line2D([0], [0], marker='^', color='w', markerfacecolor='#9b59b6', markersize=8, label='Reportes Ciudadanos (25)')
]
ax.legend(handles=legend_elements, loc='upper right', title='Fuentes de Amenazas')

ax.set_title('Amenazas y Radios de Influencia', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_amenazas_santiago.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_amenazas_santiago.png")
plt.close()

# ============================================================
# MAPA 5: Detalle Zona Critica
# ============================================================
print("\n[5/6] Generando: fig_detalle_zona_critica.png")

fig, ax = plt.subplots(figsize=(12, 10))

if muy_alto is not None:
    muy_alto.plot(ax=ax, color='#e74c3c', linewidth=3)

if pasos is not None:
    pasos.plot(ax=ax, color='#e74c3c', markersize=150, marker='s', edgecolor='black', linewidth=1)
    # Agregar etiquetas
    for idx, row in pasos.iterrows():
        x, y = row.geometry.x, row.geometry.y
        nombre = row.get('nombre', '')
        if nombre and len(nombre) < 40:
            ax.annotate(nombre, xy=(x, y), xytext=(5, 5), textcoords='offset points',
                       fontsize=7, color='black', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

# Zoom a zona critica (Estacion Central area)
# Coordenadas en Web Mercator aproximadas
ax.set_xlim(-7875000, -7860000)
ax.set_ylim(-3970000, -3955000)

add_basemap(ax, zoom=14)

legend_elements = [
    Line2D([0], [0], color='#e74c3c', linewidth=3, label='Aristas Muy Alto Riesgo'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#e74c3c',
           markersize=10, markeredgecolor='black', label='Pasos Bajo Nivel')
]
ax.legend(handles=legend_elements, loc='upper right')

ax.set_title('Detalle: Zona Critica - Santiago Centro', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_detalle_zona_critica.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_detalle_zona_critica.png")
plt.close()

# ============================================================
# MAPA 6: Clusters de Riesgo
# ============================================================
print("\n[6/6] Generando: fig_clusters_riesgo.png")

fig, ax = plt.subplots(figsize=(12, 10))

corredores = load_geojson('corredores_riesgo.geojson')
clusters = load_geojson('zonas_criticas_centroid.geojson')

if corredores is not None:
    corredores = corredores.to_crs(WEB_MERCATOR)
    corredores.plot(ax=ax, color='#e74c3c', linewidth=1.5, alpha=0.7)

if clusters is not None:
    clusters = clusters.to_crs(WEB_MERCATOR)
    # Tamano proporcional al numero de aristas
    sizes = clusters['num_aristas'].fillna(1) * 30
    clusters.plot(ax=ax, color='#e74c3c', markersize=sizes, alpha=0.5,
                  edgecolor='#c0392b', linewidth=2)

add_basemap(ax, zoom=11)

legend_elements = [
    Line2D([0], [0], color='#e74c3c', linewidth=2, alpha=0.7, label='Corredores de Riesgo'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c',
           markersize=12, alpha=0.5, markeredgecolor='#c0392b', label='Clusters de Riesgo')
]
ax.legend(handles=legend_elements, loc='upper right', title='Zonas Criticas')

ax.set_title('Clusters y Corredores de Alto Riesgo', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_clusters_riesgo.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_clusters_riesgo.png")
plt.close()

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 60)
print("MAPAS GENERADOS")
print("=" * 60)

mapas_generados = [
    ('fig_red_vial_santiago.png', 'Red vial principal categorizada'),
    ('fig_distribucion_riesgo.png', 'Distribucion de probabilidad de falla'),
    ('fig_zonas_alto_riesgo.png', 'Aristas de alto y muy alto riesgo'),
    ('fig_amenazas_santiago.png', 'Fuentes de amenazas con buffers'),
    ('fig_detalle_zona_critica.png', 'Detalle zona centro-poniente'),
    ('fig_clusters_riesgo.png', 'Clusters y corredores de riesgo')
]

for filename, desc in mapas_generados:
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / 1024
        print(f"  {filename:35} ({size:>6.1f} KB)")
    else:
        print(f"  {filename:35} [ERROR]")

print(f"\nArchivos guardados en: {os.path.abspath(OUTPUT_DIR)}/")
print("=" * 60)
