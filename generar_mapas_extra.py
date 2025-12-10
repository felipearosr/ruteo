#!/usr/bin/env python3
"""
Genera mapas adicionales para el informe.
Variaciones y visualizaciones extra para tener mas opciones.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import contextily as ctx
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# Configuracion
QGIS_DIR = 'qgis_data'
OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEB_MERCATOR = 'EPSG:3857'

def load_geojson(filename):
    """Carga GeoJSON como GeoDataFrame."""
    filepath = os.path.join(QGIS_DIR, filename)
    if os.path.exists(filepath):
        return gpd.read_file(filepath)
    print(f"  [!] No encontrado: {filename}")
    return None

def add_basemap(ax, zoom=12, style='light'):
    """Agrega mapa base."""
    try:
        if style == 'light':
            ctx.add_basemap(ax, crs=WEB_MERCATOR, source=ctx.providers.CartoDB.Positron, zoom=zoom)
        elif style == 'dark':
            ctx.add_basemap(ax, crs=WEB_MERCATOR, source=ctx.providers.CartoDB.DarkMatter, zoom=zoom)
        elif style == 'osm':
            ctx.add_basemap(ax, crs=WEB_MERCATOR, source=ctx.providers.OpenStreetMap.Mapnik, zoom=zoom)
        elif style == 'satellite':
            ctx.add_basemap(ax, crs=WEB_MERCATOR, source=ctx.providers.Esri.WorldImagery, zoom=zoom)
    except Exception as e:
        print(f"  [!] No se pudo cargar mapa base: {e}")

print("=" * 60)
print("GENERANDO MAPAS ADICIONALES")
print("=" * 60)

# Cargar datos una vez
print("\nCargando datos...")
riesgo = load_geojson('aristas_riesgo.geojson')
alto_riesgo = load_geojson('aristas_alto_riesgo.geojson')
muy_alto = load_geojson('aristas_muy_alto_riesgo.geojson')
primarias = load_geojson('aristas_primarias.geojson')
dga = load_geojson('amenaza_dga.geojson')
pasos = load_geojson('amenaza_pasos_bajo_nivel.geojson')
reportes = load_geojson('amenaza_reportes.geojson')
clusters = load_geojson('zonas_criticas_centroid.geojson')
corredores = load_geojson('corredores_riesgo.geojson')

# Convertir a Web Mercator
if riesgo is not None:
    riesgo = riesgo.to_crs(WEB_MERCATOR)
if alto_riesgo is not None:
    alto_riesgo = alto_riesgo.to_crs(WEB_MERCATOR)
if muy_alto is not None:
    muy_alto = muy_alto.to_crs(WEB_MERCATOR)
if primarias is not None:
    primarias = primarias.to_crs(WEB_MERCATOR)
if dga is not None:
    dga = dga.to_crs(WEB_MERCATOR)
if pasos is not None:
    pasos = pasos.to_crs(WEB_MERCATOR)
if reportes is not None:
    reportes = reportes.to_crs(WEB_MERCATOR)
if clusters is not None:
    clusters = clusters.to_crs(WEB_MERCATOR)
if corredores is not None:
    corredores = corredores.to_crs(WEB_MERCATOR)

# ============================================================
# MAPA 1: Heatmap de Riesgo (gradiente continuo)
# ============================================================
print("\n[1/12] Generando: fig_heatmap_riesgo.png")

if riesgo is not None:
    fig, ax = plt.subplots(figsize=(14, 12))

    # Crear colormap personalizado
    colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#8e44ad']
    cmap = LinearSegmentedColormap.from_list('risk', colors)

    riesgo.plot(ax=ax, column='p_fallo_arista', cmap=cmap, linewidth=0.5,
                legend=True, legend_kwds={'label': 'Probabilidad de Falla', 'shrink': 0.6})

    add_basemap(ax, zoom=11)
    ax.set_title('Mapa de Calor: Probabilidad de Falla en Red Vial', fontsize=14, fontweight='bold')
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/fig_heatmap_riesgo.png', dpi=300, bbox_inches='tight')
    print(f"  [OK] {OUTPUT_DIR}/fig_heatmap_riesgo.png")
plt.close()

# ============================================================
# MAPA 2: Red Vial con Fondo Oscuro (estilo nocturno)
# ============================================================
print("\n[2/12] Generando: fig_red_vial_dark.png")

if primarias is not None:
    fig, ax = plt.subplots(figsize=(14, 12))

    colors = {
        'motorway': '#ff6b6b',
        'primary': '#feca57',
        'secondary': '#48dbfb',
        'tertiary': '#1dd1a1'
    }

    for highway_type in ['tertiary', 'secondary', 'primary', 'motorway']:
        subset = primarias[primarias['highway'] == highway_type]
        if len(subset) > 0:
            lw = {'motorway': 2.5, 'primary': 2.0, 'secondary': 1.5, 'tertiary': 1.0}
            subset.plot(ax=ax, color=colors.get(highway_type, 'white'),
                       linewidth=lw.get(highway_type, 1))

    add_basemap(ax, zoom=11, style='dark')

    legend_elements = [
        Line2D([0], [0], color='#ff6b6b', linewidth=2.5, label='Autopista'),
        Line2D([0], [0], color='#feca57', linewidth=2, label='Primaria'),
        Line2D([0], [0], color='#48dbfb', linewidth=1.5, label='Secundaria'),
        Line2D([0], [0], color='#1dd1a1', linewidth=1, label='Terciaria')
    ]
    ax.legend(handles=legend_elements, loc='upper right', title='Tipo de Via',
              facecolor='#2d3436', labelcolor='white', title_fontsize=10)

    ax.set_title('Red Vial Principal - Vista Nocturna', fontsize=14, fontweight='bold', color='white')
    ax.set_facecolor('#2d3436')
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/fig_red_vial_dark.png', dpi=300, bbox_inches='tight',
                facecolor='#2d3436')
    print(f"  [OK] {OUTPUT_DIR}/fig_red_vial_dark.png")
plt.close()

# ============================================================
# MAPA 3: Solo Amenazas con Etiquetas
# ============================================================
print("\n[3/12] Generando: fig_amenazas_etiquetado.png")

fig, ax = plt.subplots(figsize=(14, 12))

if dga is not None:
    dga.plot(ax=ax, color='#3498db', markersize=50, marker='o', edgecolor='white', linewidth=1)

if pasos is not None:
    pasos.plot(ax=ax, color='#e74c3c', markersize=100, marker='s', edgecolor='white', linewidth=1)
    for idx, row in pasos.iterrows():
        x, y = row.geometry.x, row.geometry.y
        nombre = row.get('nombre', str(idx))
        if nombre and len(str(nombre)) < 35:
            ax.annotate(nombre, xy=(x, y), xytext=(8, 8), textcoords='offset points',
                       fontsize=7, color='black', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

if reportes is not None:
    reportes.plot(ax=ax, color='#9b59b6', markersize=60, marker='^', edgecolor='white', linewidth=1)

add_basemap(ax, zoom=11)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=12, label='Estaciones DGA'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#e74c3c', markersize=12, label='Pasos Bajo Nivel'),
    Line2D([0], [0], marker='^', color='w', markerfacecolor='#9b59b6', markersize=12, label='Reportes Ciudadanos')
]
ax.legend(handles=legend_elements, loc='upper right', title='Fuentes de Amenaza')

ax.set_title('Ubicacion de Fuentes de Amenazas', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_amenazas_etiquetado.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_amenazas_etiquetado.png")
plt.close()

# ============================================================
# MAPA 4: Comparacion lado a lado (bajo vs alto riesgo)
# ============================================================
print("\n[4/12] Generando: fig_comparacion_riesgo_sidebyside.png")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

if riesgo is not None:
    # Panel izquierdo: bajo riesgo
    bajo = riesgo[riesgo['p_fallo_arista'] < 0.2]
    bajo.plot(ax=ax1, color='#2ecc71', linewidth=0.5)
    add_basemap(ax1, zoom=11)
    ax1.set_title('Aristas de Bajo Riesgo (p < 0.2)', fontsize=12, fontweight='bold')
    ax1.set_axis_off()

    # Panel derecho: alto riesgo
    alto = riesgo[riesgo['p_fallo_arista'] >= 0.3]
    alto.plot(ax=ax2, color='#e74c3c', linewidth=1.5)
    add_basemap(ax2, zoom=11)
    ax2.set_title('Aristas de Alto Riesgo (p >= 0.3)', fontsize=12, fontweight='bold')
    ax2.set_axis_off()

plt.suptitle('Comparacion: Zonas de Bajo vs Alto Riesgo', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_comparacion_riesgo_sidebyside.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_comparacion_riesgo_sidebyside.png")
plt.close()

# ============================================================
# MAPA 5: Zoom Zona Norte (Quilicura, Huechuraba, Conchali)
# ============================================================
print("\n[5/12] Generando: fig_zoom_zona_norte.png")

fig, ax = plt.subplots(figsize=(12, 10))

if riesgo is not None:
    riesgo['risk_cat'] = 'bajo'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.2, 'risk_cat'] = 'medio'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.3, 'risk_cat'] = 'alto'
    riesgo.loc[riesgo['p_fallo_arista'] >= 0.5, 'risk_cat'] = 'muy_alto'

    colors_risk = {'bajo': '#2ecc71', 'medio': '#f1c40f', 'alto': '#e67e22', 'muy_alto': '#e74c3c'}

    for cat in ['bajo', 'medio', 'alto', 'muy_alto']:
        subset = riesgo[riesgo['risk_cat'] == cat]
        if len(subset) > 0:
            lw = {'bajo': 0.3, 'medio': 0.6, 'alto': 1.2, 'muy_alto': 2.5}
            subset.plot(ax=ax, color=colors_risk[cat], linewidth=lw[cat])

# Zoom a zona norte
ax.set_xlim(-7878000, -7858000)
ax.set_ylim(-3952000, -3938000)

add_basemap(ax, zoom=13)

legend_elements = [
    Line2D([0], [0], color='#2ecc71', linewidth=1, label='Bajo'),
    Line2D([0], [0], color='#f1c40f', linewidth=1.5, label='Medio'),
    Line2D([0], [0], color='#e67e22', linewidth=2, label='Alto'),
    Line2D([0], [0], color='#e74c3c', linewidth=3, label='Muy Alto')
]
ax.legend(handles=legend_elements, loc='upper right', title='Nivel de Riesgo')

ax.set_title('Detalle Zona Norte: Quilicura - Huechuraba - Conchali', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_zoom_zona_norte.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_zoom_zona_norte.png")
plt.close()

# ============================================================
# MAPA 6: Zoom Zona Sur (La Florida, Puente Alto)
# ============================================================
print("\n[6/12] Generando: fig_zoom_zona_sur.png")

fig, ax = plt.subplots(figsize=(12, 10))

if riesgo is not None:
    for cat in ['bajo', 'medio', 'alto', 'muy_alto']:
        subset = riesgo[riesgo['risk_cat'] == cat]
        if len(subset) > 0:
            lw = {'bajo': 0.3, 'medio': 0.6, 'alto': 1.2, 'muy_alto': 2.5}
            colors_risk = {'bajo': '#2ecc71', 'medio': '#f1c40f', 'alto': '#e67e22', 'muy_alto': '#e74c3c'}
            subset.plot(ax=ax, color=colors_risk[cat], linewidth=lw[cat])

# Zoom a zona sur
ax.set_xlim(-7862000, -7842000)
ax.set_ylim(-3990000, -3970000)

add_basemap(ax, zoom=13)

ax.set_title('Detalle Zona Sur: La Florida - Puente Alto', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_zoom_zona_sur.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_zoom_zona_sur.png")
plt.close()

# ============================================================
# MAPA 7: Zoom Zona Poniente (Maipu, Pudahuel)
# ============================================================
print("\n[7/12] Generando: fig_zoom_zona_poniente.png")

fig, ax = plt.subplots(figsize=(12, 10))

if riesgo is not None:
    for cat in ['bajo', 'medio', 'alto', 'muy_alto']:
        subset = riesgo[riesgo['risk_cat'] == cat]
        if len(subset) > 0:
            lw = {'bajo': 0.3, 'medio': 0.6, 'alto': 1.2, 'muy_alto': 2.5}
            colors_risk = {'bajo': '#2ecc71', 'medio': '#f1c40f', 'alto': '#e67e22', 'muy_alto': '#e74c3c'}
            subset.plot(ax=ax, color=colors_risk[cat], linewidth=lw[cat])

# Zoom a zona poniente
ax.set_xlim(-7895000, -7870000)
ax.set_ylim(-3975000, -3955000)

add_basemap(ax, zoom=12)

ax.set_title('Detalle Zona Poniente: Maipu - Pudahuel', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_zoom_zona_poniente.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_zoom_zona_poniente.png")
plt.close()

# ============================================================
# MAPA 8: Red con Satelite de Fondo
# ============================================================
print("\n[8/12] Generando: fig_red_satelite.png")

fig, ax = plt.subplots(figsize=(14, 12))

if muy_alto is not None:
    muy_alto.plot(ax=ax, color='#ff0000', linewidth=3, alpha=0.9)

if alto_riesgo is not None:
    alto_riesgo.plot(ax=ax, color='#ff9500', linewidth=2, alpha=0.8)

add_basemap(ax, zoom=11, style='satellite')

legend_elements = [
    Line2D([0], [0], color='#ff9500', linewidth=2, label='Alto Riesgo'),
    Line2D([0], [0], color='#ff0000', linewidth=3, label='Muy Alto Riesgo')
]
ax.legend(handles=legend_elements, loc='upper right', title='Nivel de Riesgo',
          facecolor='white', framealpha=0.9)

ax.set_title('Zonas de Alto Riesgo sobre Imagen Satelital', fontsize=14, fontweight='bold', color='white')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_red_satelite.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_red_satelite.png")
plt.close()

# ============================================================
# MAPA 9: Densidad de Amenazas (cuadricula)
# ============================================================
print("\n[9/12] Generando: fig_densidad_amenazas.png")

fig, ax = plt.subplots(figsize=(14, 12))

# Combinar todas las amenazas
amenazas_all = []
if dga is not None:
    amenazas_all.append(dga)
if pasos is not None:
    amenazas_all.append(pasos)
if reportes is not None:
    amenazas_all.append(reportes)

if amenazas_all:
    import pandas as pd
    all_points = pd.concat(amenazas_all, ignore_index=True)

    # Extraer coordenadas
    x = [geom.x for geom in all_points.geometry]
    y = [geom.y for geom in all_points.geometry]

    # Crear heatmap
    hb = ax.hexbin(x, y, gridsize=30, cmap='YlOrRd', mincnt=1, alpha=0.7)
    plt.colorbar(hb, ax=ax, label='Numero de Amenazas', shrink=0.6)

add_basemap(ax, zoom=11)

ax.set_title('Densidad de Fuentes de Amenazas', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_densidad_amenazas.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_densidad_amenazas.png")
plt.close()

# ============================================================
# MAPA 10: Corredores Criticos Destacados
# ============================================================
print("\n[10/12] Generando: fig_corredores_criticos.png")

fig, ax = plt.subplots(figsize=(14, 12))

# Fondo: red completa en gris claro
if primarias is not None:
    primarias.plot(ax=ax, color='#bdc3c7', linewidth=0.3, alpha=0.5)

# Corredores de riesgo
if corredores is not None:
    corredores.plot(ax=ax, color='#e74c3c', linewidth=2.5, alpha=0.8)

# Clusters
if clusters is not None:
    sizes = clusters['num_aristas'].fillna(1) * 50
    clusters.plot(ax=ax, color='#9b59b6', markersize=sizes, alpha=0.6,
                  edgecolor='#8e44ad', linewidth=2)

add_basemap(ax, zoom=11)

legend_elements = [
    Line2D([0], [0], color='#bdc3c7', linewidth=1, label='Red Vial'),
    Line2D([0], [0], color='#e74c3c', linewidth=3, label='Corredores Criticos'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#9b59b6',
           markersize=12, alpha=0.6, label='Clusters de Riesgo')
]
ax.legend(handles=legend_elements, loc='upper right')

ax.set_title('Corredores Criticos y Clusters de Alto Riesgo', fontsize=14, fontweight='bold')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_corredores_criticos.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_corredores_criticos.png")
plt.close()

# ============================================================
# MAPA 11: Panel 2x2 de Zonas
# ============================================================
print("\n[11/12] Generando: fig_panel_zonas.png")

fig, axes = plt.subplots(2, 2, figsize=(16, 16))

zonas = [
    ('Norte', -7878000, -7858000, -3952000, -3938000),
    ('Oriente', -7858000, -7838000, -3968000, -3948000),
    ('Sur', -7868000, -7848000, -3988000, -3968000),
    ('Poniente', -7892000, -7868000, -3972000, -3952000)
]

colors_risk = {'bajo': '#2ecc71', 'medio': '#f1c40f', 'alto': '#e67e22', 'muy_alto': '#e74c3c'}

for ax, (nombre, xmin, xmax, ymin, ymax) in zip(axes.flat, zonas):
    if riesgo is not None:
        for cat in ['bajo', 'medio', 'alto', 'muy_alto']:
            subset = riesgo[riesgo['risk_cat'] == cat]
            if len(subset) > 0:
                lw = {'bajo': 0.3, 'medio': 0.6, 'alto': 1.2, 'muy_alto': 2.0}
                subset.plot(ax=ax, color=colors_risk[cat], linewidth=lw[cat])

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    add_basemap(ax, zoom=13)
    ax.set_title(f'Zona {nombre}', fontsize=12, fontweight='bold')
    ax.set_axis_off()

plt.suptitle('Detalle por Zonas de Santiago', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig_panel_zonas.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_panel_zonas.png")
plt.close()

# ============================================================
# MAPA 12: Infografia Resumen
# ============================================================
print("\n[12/12] Generando: fig_infografia_resumen.png")

fig = plt.figure(figsize=(20, 12))

# Panel principal: mapa de riesgo
ax_main = fig.add_axes([0.02, 0.1, 0.6, 0.85])

if riesgo is not None:
    colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#8e44ad']
    cmap = LinearSegmentedColormap.from_list('risk', colors)
    riesgo.plot(ax=ax_main, column='p_fallo_arista', cmap=cmap, linewidth=0.5)

add_basemap(ax_main, zoom=11)
ax_main.set_title('Mapa de Riesgo General', fontsize=14, fontweight='bold')
ax_main.set_axis_off()

# Panel superior derecho: histograma de riesgo
ax_hist = fig.add_axes([0.65, 0.55, 0.32, 0.35])
if riesgo is not None:
    ax_hist.hist(riesgo['p_fallo_arista'], bins=50, color='#3498db', edgecolor='white', alpha=0.7)
    ax_hist.axvline(x=0.3, color='#e74c3c', linestyle='--', linewidth=2, label='Umbral Alto Riesgo')
    ax_hist.set_xlabel('Probabilidad de Falla')
    ax_hist.set_ylabel('Numero de Aristas')
    ax_hist.set_title('Distribucion de Probabilidades', fontweight='bold')
    ax_hist.legend()

# Panel inferior derecho: estadisticas
ax_stats = fig.add_axes([0.65, 0.1, 0.32, 0.35])
ax_stats.axis('off')

if riesgo is not None:
    total = len(riesgo)
    bajo = len(riesgo[riesgo['p_fallo_arista'] < 0.2])
    medio = len(riesgo[(riesgo['p_fallo_arista'] >= 0.2) & (riesgo['p_fallo_arista'] < 0.3)])
    alto = len(riesgo[(riesgo['p_fallo_arista'] >= 0.3) & (riesgo['p_fallo_arista'] < 0.5)])
    muy_alto = len(riesgo[riesgo['p_fallo_arista'] >= 0.5])

    stats_text = f"""
    ESTADISTICAS DE LA RED VIAL

    Total de aristas: {total:,}

    Por nivel de riesgo:
    - Bajo (p < 0.2):      {bajo:,} ({100*bajo/total:.1f}%)
    - Medio (0.2-0.3):     {medio:,} ({100*medio/total:.1f}%)
    - Alto (0.3-0.5):      {alto:,} ({100*alto/total:.1f}%)
    - Muy Alto (p > 0.5):  {muy_alto:,} ({100*muy_alto/total:.1f}%)

    Amenazas integradas:
    - Estaciones DGA: {len(dga) if dga is not None else 0}
    - Pasos bajo nivel: {len(pasos) if pasos is not None else 0}
    - Reportes ciudadanos: {len(reportes) if reportes is not None else 0}
    """

    ax_stats.text(0.1, 0.9, stats_text, transform=ax_stats.transAxes, fontsize=11,
                  verticalalignment='top', fontfamily='monospace',
                  bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))

plt.savefig(f'{OUTPUT_DIR}/fig_infografia_resumen.png', dpi=300, bbox_inches='tight')
print(f"  [OK] {OUTPUT_DIR}/fig_infografia_resumen.png")
plt.close()

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 60)
print("MAPAS ADICIONALES GENERADOS")
print("=" * 60)

mapas = [
    'fig_heatmap_riesgo.png',
    'fig_red_vial_dark.png',
    'fig_amenazas_etiquetado.png',
    'fig_comparacion_riesgo_sidebyside.png',
    'fig_zoom_zona_norte.png',
    'fig_zoom_zona_sur.png',
    'fig_zoom_zona_poniente.png',
    'fig_red_satelite.png',
    'fig_densidad_amenazas.png',
    'fig_corredores_criticos.png',
    'fig_panel_zonas.png',
    'fig_infografia_resumen.png'
]

for m in mapas:
    filepath = os.path.join(OUTPUT_DIR, m)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / 1024
        print(f"  {m:40} ({size:>7.1f} KB)")

print(f"\nArchivos en: {os.path.abspath(OUTPUT_DIR)}/")
print("=" * 60)
