# Esquema del JSON de estaciones DGA

El archivo generado por `amenazas/dga_etl.py` es `amenazas/dga_estaciones.json`.

Contiene un array de objetos JSON donde cada objeto representa una estación de monitoreo de la DGA.

Campos:
- lon: longitud (float)
- lat: latitud (float)
- station_id: identificador único de la estación (string)
- parameter: objeto JSON con información del parámetro medido (type, unit)
- last_update: timestamp de última actualización en formato ISO 8601 (string)

Ejemplo:

[
  {
    "lon": -70.65,
    "lat": -33.45,
    "station_id": "DGA-001",
    "parameter": {
      "type": "caudal",
      "unit": "m3/s"
    },
    "last_update": "2025-11-16T20:00:00Z"
  }
]

El loader SQL `amenazas/load_dga.sql` insertará estos registros en la tabla `amenaza_dga`.
