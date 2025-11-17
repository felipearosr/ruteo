# Esquema del JSON de reportes ciudadanos

El archivo generado por `amenazas/reportes_ciudadanos_etl.py` es `amenazas/reportes_ciudadanos.json`.

Contiene un array de objetos JSON donde cada objeto representa un reporte ciudadano de una posible amenaza (p. ej. inundación).

Campos:
- lon: longitud (float)
- lat: latitud (float)
- reported_at: timestamp del reporte en formato ISO 8601 (string)
- reporter: identificador del usuario que reportó (string)
- description: descripción del reporte (string)
- media: objeto JSON con medios asociados (p. ej. imágenes)

Ejemplo:

[
  {
    "lon": -70.65,
    "lat": -33.45,
    "reported_at": "2025-11-16T19:00:00Z",
    "reporter": "@usuario1",
    "description": "Inundación en calle principal",
    "media": {
      "images": ["http://example.com/img1.jpg"]
    }
  }
]

El loader SQL `amenazas/load_reportes_ciudadanos.sql` insertará estos registros en la tabla `amenaza_reportes_ciudadanos`.
