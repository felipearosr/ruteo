# Esquema del JSON de lluvia

El archivo generado por `metadata/lluvia_etl.py` es `metadata/lluvia.json`.

Contiene un array de objetos JSON donde cada objeto representa un punto de medición de precipitación.

Campos:
- lon: longitud (float)
- lat: latitud (float)
- precip_mm: precipitación en milímetros (float)
- observed_at: timestamp de la observación en formato ISO 8601 (string)
- source: fuente de la información (string, p. ej. "Estación Meteo A")

Ejemplo:

[
  {
    "lon": -70.65,
    "lat": -33.45,
    "precip_mm": 12.5,
    "observed_at": "2025-11-16T22:00:00Z",
    "source": "Estación Meteo A"
  }
]

El loader SQL `metadata/load_lluvia.sql` insertará estos registros en la tabla `meta_lluvia`.
