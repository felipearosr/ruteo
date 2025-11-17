# Esquema del JSON de landcover

El archivo generado por `metadata/landcover_etl.py` es `metadata/landcover.json`.

Contiene un array de objetos JSON donde cada objeto representa una geometría clasificada por tipo de cobertura de suelo.

Campos:
- geometry: objeto GeoJSON geometry (puede ser Point, Polygon, etc.)
- class: tipo de cobertura (string, p. ej. "urban", "vegetation", "water")
- confidence: nivel de confianza de la clasificación (float entre 0 y 1)
- source: fuente de la información (string, p. ej. "Sentinel-2")

Ejemplo:

[
  {
    "geometry": {
      "type": "Point",
      "coordinates": [-70.65, -33.45]
    },
    "class": "urban",
    "confidence": 0.95,
    "source": "Sentinel-2"
  }
]

El loader SQL `metadata/load_landcover.sql` insertará estos registros en la tabla `meta_landcover`.
