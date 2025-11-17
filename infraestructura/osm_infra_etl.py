"""
ETL para infraestructura (red vial) desde Overpass API.

Este script consulta la Overpass API para extraer ways etiquetados como `highway`
en un bounding box configurable y genera un archivo GeoJSON con las aristas (LineString)
y sus propiedades.

Salida:
  - infraestructura/infraestructura.geojson

Uso:
  python infraestructura/osm_infra_etl.py

Variables opcionales (entorno):
  - OVERPASS_BBOX (min_lon,min_lat,max_lon,max_lat) por defecto cubre una zona de ejemplo

Comentarios:
  - Este script no carga a la base de datos; solo genera el GeoJSON que luego será
	procesado por el loader SQL `infraestructura/load_infra.sql`.
"""
import os
import json
import requests
from geojson import Feature, FeatureCollection, LineString


def get_bbox():
	# Bounding box como 'min_lon,min_lat,max_lon,max_lat'
	bbox_env = os.getenv('OVERPASS_BBOX')
	if bbox_env:
		parts = [p.strip() for p in bbox_env.split(',')]
		if len(parts) == 4:
			return parts
	# Coordenadas por defecto (pequeña área de ejemplo)
	# Aquí se usa un bbox centrado en Santiago, Chile (ejemplo)
	return ['-70.8','-33.6','-70.5','-33.4']


def build_overpass_query(bbox):
	# Consulta Overpass: obtener ways con tag highway y los nodos asociados
	# bbox: min_lon, min_lat, max_lon, max_lat
	min_lon, min_lat, max_lon, max_lat = bbox
	query = f"""
	[out:json][timeout:25];
	(
	  way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
	);
	(._;>;);
	out body;
	"""
	return query


def run_overpass(query):
	url = 'https://overpass-api.de/api/interpreter'
	resp = requests.post(url, data={'data': query}, timeout=60)
	resp.raise_for_status()
	return resp.json()


def parse_overpass_to_geojson(data):
	# Index nodes by id
	nodes = {str(n['id']): n for n in data.get('elements', []) if n['type'] == 'node'}

	features = []
	for el in data.get('elements', []):
		if el['type'] == 'way':
			coords = []
			for nid in el.get('nodes', []):
				node = nodes.get(str(nid))
				if node:
					coords.append([node['lon'], node['lat']])
			if len(coords) >= 2:
				props = el.get('tags', {})
				props.update({'osm_id': el.get('id')})
				feat = Feature(geometry=LineString(coords), properties=props, id=el.get('id'))
				features.append(feat)

	return FeatureCollection(features)


def save_geojson(fc, path):
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(fc, f, ensure_ascii=False, indent=2)


def main():
	bbox = get_bbox()
	print(f"Usando bbox: {bbox}")
	query = build_overpass_query(bbox)
	print("Consultando Overpass API...")
	data = run_overpass(query)
	print("Parseando a GeoJSON...")
	fc = parse_overpass_to_geojson(data)
	outdir = os.path.join(os.path.dirname(__file__), '.')
	outpath = os.path.join(outdir, 'infraestructura.geojson')
	save_geojson(fc, outpath)
	print(f"GeoJSON guardado en: {outpath} (features: {len(fc['features'])})")


if __name__ == '__main__':
	main()

