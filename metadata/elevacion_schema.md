# Esquema del JSON de elevación

El archivo generado por `metadata/elevacion_etl.py` es `metadata/elevacion.json`.

Contiene un array de objetos JSON donde cada objeto representa un punto con elevación.

Campos:
- lon: longitud (float)
- lat: latitud (float)
- elev_m: elevación en metros sobre el nivel del mar (float)
- source: fuente de la información (string, p. ej. "SRTM")

Ejemplo:

[
  {
    "lon": -70.65,
    "lat": -33.45,
    "elev_m": 520.0,
    "source": "SRTM"
  }
]

El loader SQL `metadata/load_elevacion.sql` insertará estos registros en la tabla `meta_elevacion`.
