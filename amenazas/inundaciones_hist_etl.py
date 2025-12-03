"""
ETL para amenazas de inundaciones historicas.

Genera zonas de inundacion basadas en:
1. Cursos de agua principales de Santiago (Rio Mapocho, Zanjon de la Aguada)
2. Quebradas precordilleranas conocidas por aluviones (Lo Canas, Macul, San Ramon)
3. Datos historicos de inundaciones documentadas

Fuentes de referencia:
- SERNAGEOMIN: Peligro de Remociones en Masa e Inundacion, Cuenca de Santiago
- Estudios municipales de zonas de riesgo
- Registro historico de eventos de inundacion (ONEMI/SENAPRED)

Salida:
  - amenazas/inundaciones_hist.json

Uso:
  python amenazas/inundaciones_hist_etl.py
"""
import os
import json
from typing import List, Dict

# Zonas de inundacion conocidas en Santiago
# Basado en datos de SERNAGEOMIN y registros historicos
FLOOD_ZONES = [
    # Rio Mapocho - Sector Providencia/Las Condes
    {
        "name": "Rio Mapocho - Providencia",
        "source": "SERNAGEOMIN/Registro historico",
        "severity": "alta",
        "event_date": {"lower": "1982-06-01", "upper": "1982-06-30"},
        "description": "Zona de desborde historico del Rio Mapocho",
        "coordinates": [
            [-70.6100, -33.4200],
            [-70.5900, -33.4200],
            [-70.5900, -33.4350],
            [-70.6100, -33.4350],
            [-70.6100, -33.4200]
        ]
    },
    # Rio Mapocho - Sector Centro
    {
        "name": "Rio Mapocho - Santiago Centro",
        "source": "SERNAGEOMIN/Registro historico",
        "severity": "alta",
        "event_date": {"lower": "1997-06-01", "upper": "1997-06-30"},
        "description": "Zona de inundacion sector Parque Forestal",
        "coordinates": [
            [-70.6500, -33.4300],
            [-70.6300, -33.4300],
            [-70.6300, -33.4400],
            [-70.6500, -33.4400],
            [-70.6500, -33.4300]
        ]
    },
    # Rio Mapocho - Sector Pudahuel
    {
        "name": "Rio Mapocho - Pudahuel",
        "source": "Registro municipal",
        "severity": "media",
        "event_date": {"lower": "2016-04-01", "upper": "2016-04-30"},
        "description": "Zona de desborde sector poniente",
        "coordinates": [
            [-70.7600, -33.4400],
            [-70.7400, -33.4400],
            [-70.7400, -33.4550],
            [-70.7600, -33.4550],
            [-70.7600, -33.4400]
        ]
    },
    # Zanjon de la Aguada - Sector San Miguel
    {
        "name": "Zanjon de la Aguada - San Miguel",
        "source": "SERNAGEOMIN/Registro historico",
        "severity": "alta",
        "event_date": {"lower": "1993-05-01", "upper": "1993-05-31"},
        "description": "Desborde historico del Zanjon de la Aguada",
        "coordinates": [
            [-70.6500, -33.4900],
            [-70.6300, -33.4900],
            [-70.6300, -33.5050],
            [-70.6500, -33.5050],
            [-70.6500, -33.4900]
        ]
    },
    # Zanjon de la Aguada - Sector Pedro Aguirre Cerda
    {
        "name": "Zanjon de la Aguada - PAC",
        "source": "Registro municipal",
        "severity": "media",
        "event_date": {"lower": "2005-07-01", "upper": "2005-07-31"},
        "description": "Zona de anegamiento recurrente",
        "coordinates": [
            [-70.6700, -33.4850],
            [-70.6550, -33.4850],
            [-70.6550, -33.4950],
            [-70.6700, -33.4950],
            [-70.6700, -33.4850]
        ]
    },
    # Quebrada de Macul - La Florida
    {
        "name": "Quebrada de Macul - La Florida",
        "source": "SERNAGEOMIN",
        "severity": "muy_alta",
        "event_date": {"lower": "1993-05-03", "upper": "1993-05-03"},
        "description": "Aluvion historico de la Quebrada de Macul - 26 fallecidos",
        "coordinates": [
            [-70.5300, -33.4900],
            [-70.5100, -33.4900],
            [-70.5100, -33.5100],
            [-70.5300, -33.5100],
            [-70.5300, -33.4900]
        ]
    },
    # Quebrada Lo Canas - La Florida
    {
        "name": "Quebrada Lo Canas - La Florida",
        "source": "SERNAGEOMIN",
        "severity": "alta",
        "event_date": {"lower": "1993-05-03", "upper": "1993-05-03"},
        "description": "Zona de riesgo de aluvion quebrada Lo Canas",
        "coordinates": [
            [-70.5200, -33.5200],
            [-70.5000, -33.5200],
            [-70.5000, -33.5400],
            [-70.5200, -33.5400],
            [-70.5200, -33.5200]
        ]
    },
    # Quebrada de Ramon - La Reina/Penalolen
    {
        "name": "Quebrada de Ramon - La Reina",
        "source": "SERNAGEOMIN",
        "severity": "alta",
        "event_date": {"lower": "1987-02-01", "upper": "1987-02-28"},
        "description": "Zona de riesgo de aluvion Quebrada de Ramon",
        "coordinates": [
            [-70.5100, -33.4500],
            [-70.4900, -33.4500],
            [-70.4900, -33.4700],
            [-70.5100, -33.4700],
            [-70.5100, -33.4500]
        ]
    },
    # Estero Lampa - Lampa
    {
        "name": "Estero Lampa - Lampa",
        "source": "Registro municipal",
        "severity": "media",
        "event_date": {"lower": "2017-05-01", "upper": "2017-05-31"},
        "description": "Zona de desborde Estero Lampa",
        "coordinates": [
            [-70.8800, -33.2900],
            [-70.8600, -33.2900],
            [-70.8600, -33.3100],
            [-70.8800, -33.3100],
            [-70.8800, -33.2900]
        ]
    },
    # Estero Colina - Colina
    {
        "name": "Estero Colina - Colina",
        "source": "Registro municipal",
        "severity": "media",
        "event_date": {"lower": "2015-08-01", "upper": "2015-08-31"},
        "description": "Zona de anegamiento Estero Colina",
        "coordinates": [
            [-70.6700, -33.2000],
            [-70.6500, -33.2000],
            [-70.6500, -33.2200],
            [-70.6700, -33.2200],
            [-70.6700, -33.2000]
        ]
    },
    # Rio Maipo - Sector El Monte
    {
        "name": "Rio Maipo - El Monte",
        "source": "DGA/Registro historico",
        "severity": "alta",
        "event_date": {"lower": "2008-05-01", "upper": "2008-05-31"},
        "description": "Zona de desborde Rio Maipo sector rural",
        "coordinates": [
            [-70.9500, -33.6800],
            [-70.9300, -33.6800],
            [-70.9300, -33.7000],
            [-70.9500, -33.7000],
            [-70.9500, -33.6800]
        ]
    },
    # Rio Maipo - Puente Alto
    {
        "name": "Rio Maipo - Puente Alto",
        "source": "Registro municipal",
        "severity": "media",
        "event_date": {"lower": "2013-06-01", "upper": "2013-06-30"},
        "description": "Zona de riesgo ribera norte Rio Maipo",
        "coordinates": [
            [-70.5700, -33.5900],
            [-70.5500, -33.5900],
            [-70.5500, -33.6100],
            [-70.5700, -33.6100],
            [-70.5700, -33.5900]
        ]
    },
    # Canal San Carlos - Nunoa/La Reina
    {
        "name": "Canal San Carlos - Nunoa",
        "source": "Registro municipal",
        "severity": "baja",
        "event_date": {"lower": "2019-06-01", "upper": "2019-06-30"},
        "description": "Zona de desborde Canal San Carlos",
        "coordinates": [
            [-70.5800, -33.4550],
            [-70.5650, -33.4550],
            [-70.5650, -33.4650],
            [-70.5800, -33.4650],
            [-70.5800, -33.4550]
        ]
    },
    # Sector Lo Barnechea - Alto
    {
        "name": "Quebradas Lo Barnechea",
        "source": "SERNAGEOMIN",
        "severity": "alta",
        "event_date": {"lower": "2017-02-25", "upper": "2017-02-26"},
        "description": "Zona de riesgo de aluvion sector cordillerano",
        "coordinates": [
            [-70.4800, -33.3500],
            [-70.4600, -33.3500],
            [-70.4600, -33.3700],
            [-70.4800, -33.3700],
            [-70.4800, -33.3500]
        ]
    },
    # Vitacura - Sector El Golf
    {
        "name": "Vitacura - El Golf",
        "source": "Registro municipal",
        "severity": "baja",
        "event_date": {"lower": "2020-06-01", "upper": "2020-06-30"},
        "description": "Zona de anegamiento por drenaje insuficiente",
        "coordinates": [
            [-70.5900, -33.4050],
            [-70.5750, -33.4050],
            [-70.5750, -33.4150],
            [-70.5900, -33.4150],
            [-70.5900, -33.4050]
        ]
    }
]


def generate_flood_zones() -> List[Dict]:
    """Genera las zonas de inundacion en formato GeoJSON-like."""
    zones = []

    for zone in FLOOD_ZONES:
        zones.append({
            "geometry": {
                "type": "Polygon",
                "coordinates": [zone["coordinates"]]
            },
            "source": zone["source"],
            "event_date": zone["event_date"],
            "severity": zone["severity"],
            "name": zone["name"],
            "description": zone.get("description", "")
        })

    return zones


def main():
    zones = generate_flood_zones()

    outdir = os.path.dirname(__file__)
    outpath = os.path.join(outdir, 'inundaciones_hist.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(zones, f, ensure_ascii=False, indent=2)

    print(f"Archivo generado: {outpath} ({len(zones)} zonas)")

    # Resumen por severidad
    severidades = {}
    for z in zones:
        s = z['severity']
        severidades[s] = severidades.get(s, 0) + 1

    print("\nResumen por severidad:")
    for s, c in sorted(severidades.items()):
        print(f"  {s}: {c}")

    # Resumen por fuente
    fuentes = {}
    for z in zones:
        src = z['source'].split('/')[0]
        fuentes[src] = fuentes.get(src, 0) + 1

    print("\nResumen por fuente:")
    for f, c in sorted(fuentes.items(), key=lambda x: -x[1]):
        print(f"  {f}: {c}")


if __name__ == '__main__':
    main()
