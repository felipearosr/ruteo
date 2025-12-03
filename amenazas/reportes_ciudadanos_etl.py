"""
ETL para amenazas de reportes ciudadanos.

Genera reportes ciudadanos basados en:
1. Puntos criticos conocidos de inundacion en Santiago
2. Noticias recientes de eventos de inundacion
3. Comunas historicamente afectadas (Pudahuel, Quilicura, Lo Espejo, etc.)

Fuentes de referencia:
- Noticias La Tercera, BioBioChile sobre inundaciones recientes
- Reportes municipales de puntos criticos
- Datos de SENAPRED sobre emergencias

Salida:
  - amenazas/reportes_ciudadanos.json

Uso:
  python amenazas/reportes_ciudadanos_etl.py
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
import random

# Puntos criticos de inundacion conocidos en Santiago
# Basado en noticias y reportes municipales
CRITICAL_POINTS = [
    # Quilicura - Estero Las Cruces
    {
        "location": "Estero Las Cruces, Quilicura",
        "lat": -33.3550,
        "lon": -70.7300,
        "description": "Desborde de Estero Las Cruces afecta viviendas",
        "severity": "alta"
    },
    # Conchali - Calle Huechuraba
    {
        "location": "Calle Huechuraba con Calle G, Conchali",
        "lat": -33.3880,
        "lon": -70.6600,
        "description": "Anegamiento en cruce peatonal",
        "severity": "media"
    },
    # Recoleta - Colector Independencia
    {
        "location": "Colector Independencia, Recoleta",
        "lat": -33.4100,
        "lon": -70.6450,
        "description": "Colapso de colector genera inundacion",
        "severity": "alta"
    },
    # La Cisterna - Gran Avenida
    {
        "location": "Gran Avenida con Lo Ovalle, La Cisterna",
        "lat": -33.5380,
        "lon": -70.6600,
        "description": "Anegamiento en avenida principal",
        "severity": "media"
    },
    # Maipu - Canal Lo Espejo
    {
        "location": "Canal Lo Espejo y Ruta 78, Maipu",
        "lat": -33.5100,
        "lon": -70.7800,
        "description": "Desborde de canal afecta autopista",
        "severity": "alta"
    },
    # Pudahuel - Bajo puente
    {
        "location": "Bajo puente Americo Vespucio, Pudahuel",
        "lat": -33.4350,
        "lon": -70.7450,
        "description": "Vehiculos atrapados en paso bajo nivel inundado",
        "severity": "muy_alta"
    },
    # Lo Espejo - Sector residencial
    {
        "location": "Poblacion Lo Sierra, Lo Espejo",
        "lat": -33.5200,
        "lon": -70.6900,
        "description": "Agua ingresa a viviendas",
        "severity": "alta"
    },
    # Cerro Navia - Canal
    {
        "location": "Canal Ortuzano, Cerro Navia",
        "lat": -33.4250,
        "lon": -70.7200,
        "description": "Desborde de canal menor",
        "severity": "media"
    },
    # Penalolen - Sector quebrada
    {
        "location": "Av. Grecia con Las Torres, Penalolen",
        "lat": -33.4850,
        "lon": -70.5200,
        "description": "Escurrimiento desde cerros causa anegamiento",
        "severity": "media"
    },
    # La Florida - Sector quebrada Macul
    {
        "location": "Av. Vicuna Mackenna, La Florida",
        "lat": -33.5050,
        "lon": -70.5900,
        "description": "Acumulacion de agua en avenida",
        "severity": "media"
    },
    # Puente Alto - Sector Rio Maipo
    {
        "location": "Calle Concha y Toro, Puente Alto",
        "lat": -33.6050,
        "lon": -70.5700,
        "description": "Crecida de Rio Maipo genera alerta",
        "severity": "alta"
    },
    # San Bernardo - Sector industrial
    {
        "location": "Av. Portales, San Bernardo",
        "lat": -33.5950,
        "lon": -70.7000,
        "description": "Anegamiento en zona industrial",
        "severity": "baja"
    },
    # El Bosque - Poblacion
    {
        "location": "Gran Avenida, El Bosque",
        "lat": -33.5650,
        "lon": -70.6700,
        "description": "Calles anegadas dificultan transito",
        "severity": "media"
    },
    # Renca - Canal Zapata
    {
        "location": "Canal Zapata, Renca",
        "lat": -33.3950,
        "lon": -70.7150,
        "description": "Desborde de canal Zapata",
        "severity": "alta"
    },
    # Huechuraba - Ciudad Empresarial
    {
        "location": "Ciudad Empresarial, Huechuraba",
        "lat": -33.3750,
        "lon": -70.6500,
        "description": "Anegamiento en estacionamientos subterraneos",
        "severity": "media"
    },
    # Lampa - Centro
    {
        "location": "Centro de Lampa",
        "lat": -33.2850,
        "lon": -70.8750,
        "description": "Desborde de estero afecta comercio",
        "severity": "alta"
    },
    # Colina - Chicureo
    {
        "location": "Av. Chicureo, Colina",
        "lat": -33.2500,
        "lon": -70.5800,
        "description": "Escurrimiento desde cerros",
        "severity": "baja"
    },
    # Santiago Centro - Metro
    {
        "location": "Estacion Metro U. de Chile, Santiago",
        "lat": -33.4420,
        "lon": -70.6500,
        "description": "Filtraciones de agua en estacion metro",
        "severity": "media"
    },
    # Providencia - Canal San Carlos
    {
        "location": "Canal San Carlos con Eliodoro Yanez, Providencia",
        "lat": -33.4300,
        "lon": -70.6050,
        "description": "Canal San Carlos presenta alto caudal",
        "severity": "baja"
    },
    # Nunoa - Sector Irarrazaval
    {
        "location": "Av. Irarrazaval con Suecia, Nunoa",
        "lat": -33.4520,
        "lon": -70.6000,
        "description": "Acumulacion de agua por drenaje tapado",
        "severity": "baja"
    },
    # La Reina - Sector alto
    {
        "location": "Av. Larrain, La Reina",
        "lat": -33.4450,
        "lon": -70.5400,
        "description": "Escurrimiento desde quebrada Ramon",
        "severity": "media"
    },
    # Las Condes - Sector El Golf
    {
        "location": "Av. Apoquindo con El Golf, Las Condes",
        "lat": -33.4150,
        "lon": -70.5850,
        "description": "Anegamiento puntual en cruce",
        "severity": "baja"
    },
    # Estacion Central - Sector Alameda
    {
        "location": "Terminal de Buses, Estacion Central",
        "lat": -33.4530,
        "lon": -70.6800,
        "description": "Paso bajo nivel inundado",
        "severity": "alta"
    },
    # Pedro Aguirre Cerda - Zanjon
    {
        "location": "Zanjon de la Aguada, PAC",
        "lat": -33.4880,
        "lon": -70.6650,
        "description": "Alto nivel de agua en Zanjon",
        "severity": "alta"
    },
    # San Miguel - Club Hipico
    {
        "location": "Av. Club Hipico, San Miguel",
        "lat": -33.4950,
        "lon": -70.6550,
        "description": "Anegamiento en sector comercial",
        "severity": "media"
    }
]


def generate_citizen_reports() -> List[Dict]:
    """Genera reportes ciudadanos simulados basados en puntos criticos reales."""
    reports = []
    now = datetime.utcnow()

    # Generar reportes para cada punto critico
    # Variamos las fechas para simular reportes recientes
    for i, point in enumerate(CRITICAL_POINTS):
        # Variar la fecha (ultimos 7 dias)
        hours_ago = random.randint(1, 168)  # 1 hora a 7 dias
        report_time = now - timedelta(hours=hours_ago)

        # Generar nombre de usuario ficticio
        usernames = [
            "@vecino_alerta", "@ciudadano_rm", "@reporte_stgo",
            "@alertas_chile", "@trafico_rm", "@emergencias_cl",
            "@info_santiago", "@reportero_urbano", "@alerta_lluvia",
            "@vecinos_unidos", "@santiago_informa", "@metro_alerta"
        ]
        reporter = random.choice(usernames)

        reports.append({
            "lon": point["lon"],
            "lat": point["lat"],
            "reported_at": report_time.isoformat() + 'Z',
            "reporter": reporter,
            "description": f"{point['description']} - {point['location']}",
            "severity": point["severity"],
            "media": {
                "images": []  # En produccion, estos serian URLs de imagenes
            }
        })

    return reports


def main():
    random.seed(42)  # Para reproducibilidad
    reports = generate_citizen_reports()

    outdir = os.path.dirname(__file__)
    outpath = os.path.join(outdir, 'reportes_ciudadanos.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

    print(f"Archivo generado: {outpath} ({len(reports)} reportes)")

    # Resumen por severidad
    severidades = {}
    for r in reports:
        s = r.get('severity', 'unknown')
        severidades[s] = severidades.get(s, 0) + 1

    print("\nResumen por severidad:")
    for s, c in sorted(severidades.items()):
        print(f"  {s}: {c}")


if __name__ == '__main__':
    main()
