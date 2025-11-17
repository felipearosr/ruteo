# Esquema del JSON de inundaciones históricas

El archivo generado por `amenazas/inundaciones_hist_etl.py` es `amenazas/inundaciones_hist.json`.

Contiene un array de objetos JSON donde cada objeto representa una zona con historial de inundaciones.

Campos:
- geometry: objeto GeoJSON geometry (típicamente Polygon o MultiPolygon)
- source: fuente de la información (string)
- event_date: objeto con lower y upper (fechas en formato ISO 8601 o YYYY-MM-DD) representando el rango de fechas del evento
- severity: nivel de severidad (string, p. ej. "alta", "media", "baja")

Ejemplo:

[
  {
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [-70.65, -33.45],
        [-70.64, -33.45],
        [-70.64, -33.46],
        [-70.65, -33.46],
        [-70.65, -33.45]
      ]]
    },
    "source": "Registro municipal",
    "event_date": {
      "lower": "2023-06-15",
      "upper": "2023-06-20"
    },
    "severity": "alta"
  }
]

El loader SQL `amenazas/load_inundaciones_hist.sql` insertará estos registros en la tabla `amenaza_inundaciones_hist`.
