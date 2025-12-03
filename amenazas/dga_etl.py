"""
ETL para amenazas DGA (estaciones de monitoreo de la Dirección General de Aguas, Chile).

Descarga el GeoJSON oficial desde el portal de Datos Abiertos del MMA y filtra
estaciones dentro del bounding box de Santiago.

Fuente: https://lineasdebasepublicas.mma.gob.cl/datos_abiertos/dataset/hidrosfera

Salida:
  - amenazas/dga_estaciones.json

Uso:
  python amenazas/dga_etl.py
"""
import os
import json
import zipfile
import tempfile
import urllib.request
from typing import List, Dict

# URL del GeoJSON oficial de estaciones DGA
DGA_GEOJSON_URL = (
    "https://lineasdebasepublicas.mma.gob.cl/datos_abiertos/dataset/"
    "bdc95936-1ea3-4625-985b-8885a10812d6/resource/"
    "d18e82ca-85c2-4ef6-ad4d-a91c9cbc7b57/download/"
    "estacion-de-red-hidrometrica-dga_geojson.zip"
)

# Bounding box de Santiago (lat, lon)
SANTIAGO_BBOX = {
    "lat_min": -33.8,
    "lat_max": -33.2,
    "lon_min": -70.9,
    "lon_max": -70.4
}


def download_and_extract_geojson() -> Dict:
    """Descarga y extrae el GeoJSON de estaciones DGA."""
    print("Descargando GeoJSON de estaciones DGA...")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "dga.zip")

        # Descargar
        urllib.request.urlretrieve(DGA_GEOJSON_URL, zip_path)

        # Extraer
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Buscar archivo GeoJSON
        for fname in os.listdir(tmpdir):
            if fname.endswith('.geojson'):
                geojson_path = os.path.join(tmpdir, fname)
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

    raise FileNotFoundError("No se encontró archivo GeoJSON en el zip")


def filter_santiago_stations(geojson: Dict) -> List[Dict]:
    """Filtra estaciones dentro del bounding box de Santiago."""
    stations = []

    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])

        if len(coords) < 2:
            continue

        lon, lat = coords[0], coords[1]

        # Filtrar por bounding box
        if not (SANTIAGO_BBOX['lat_min'] <= lat <= SANTIAGO_BBOX['lat_max'] and
                SANTIAGO_BBOX['lon_min'] <= lon <= SANTIAGO_BBOX['lon_max']):
            continue

        # Convertir a formato esperado por la aplicacion
        station = {
            "lon": lon,
            "lat": lat,
            "station_id": props.get('cod_estacion', 'unknown'),
            "nombre": props.get('nombre', ''),
            "parameter": {
                "type": props.get('tipo_estacion', 'unknown'),
                "altitud": props.get('altitud'),
                "comuna": props.get('comuna', ''),
                "lugar": props.get('lugar', '')
            },
            "last_update": None  # No disponible en datos estaticos
        }
        stations.append(station)

    return stations


def load_cached_geojson() -> Dict:
    """Intenta cargar GeoJSON desde cache local."""
    cache_path = os.path.join(os.path.dirname(__file__),
                              'Estación de Red Hidrométrica DGA.geojson')
    if os.path.exists(cache_path):
        print(f"Usando cache local: {cache_path}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def main():
    # Intentar usar cache local primero
    geojson = load_cached_geojson()

    if not geojson:
        geojson = download_and_extract_geojson()

    print(f"Total estaciones en dataset: {len(geojson.get('features', []))}")

    # Filtrar para Santiago
    stations = filter_santiago_stations(geojson)
    print(f"Estaciones en Santiago: {len(stations)}")

    # Guardar resultado
    outdir = os.path.dirname(__file__)
    outpath = os.path.join(outdir, 'dga_estaciones.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(stations, f, ensure_ascii=False, indent=2)

    print(f"Archivo generado: {outpath} ({len(stations)} registros)")

    # Mostrar resumen por tipo
    tipos = {}
    for s in stations:
        t = s['parameter']['type']
        tipos[t] = tipos.get(t, 0) + 1
    print("\nResumen por tipo:")
    for t, c in sorted(tipos.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")


if __name__ == '__main__':
    main()
