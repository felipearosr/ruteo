# Esquema del GeoJSON de infraestructura

El archivo generado por `infraestructura/osm_infra_etl.py` es `infraestructura/infraestructura.geojson`.
Es un GeoJSON FeatureCollection donde cada Feature representa una arista (way) de la red vial.

Estructura de cada Feature:

- type: "Feature"
- id: id del way en OSM (entero)
- geometry: LineString con coordenadas [lon, lat]
- properties: objeto con tags de OSM y metadatos, por ejemplo:
  - highway: tipo de vía (p. ej. residential, primary)
  - name: nombre de la vía (si existe)
  - maxspeed: límite de velocidad (si existe)
  - osm_id: id del way (redundante con `id`)

Ejemplo de Feature (simplificado):

{
  "type": "Feature",
  "id": 123456789,
  "geometry": {
    "type": "LineString",
    "coordinates": [[-70.65, -33.45], [-70.64, -33.46]]
  },
  "properties": {
    "highway": "residential",
    "name": "Calle Falsa",
    "osm_id": 123456789
  }
}

Notas:
- El loader SQL `infraestructura/load_infra.sql` espera este formato y debe convertir
  cada LineString en registros de `infra_aristas`, además de generar/insertar nodos en `infra_nodos`.
