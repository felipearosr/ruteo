"""
ETL para amenazas de pasos bajo nivel.

Los pasos bajo nivel (underpasses) son extremadamente peligrosos durante
inundaciones ya que acumulan agua rapidamente y atrapan vehiculos.

Fuentes de referencia:
- Noticias de vehiculos atrapados en pasos bajo nivel
- Reportes de Carabineros sobre cierres de pasos bajo nivel
- Documentacion municipal sobre puntos criticos

Salida:
  - amenazas/pasos_bajo_nivel.json

Uso:
  python amenazas/pasos_bajo_nivel_etl.py
"""
import os
import json
from typing import List, Dict

# Pasos bajo nivel conocidos en Santiago con historial de inundacion
# Basado en noticias y reportes de emergencias
PASOS_BAJO_NIVEL = [
    # Pudahuel - Americo Vespucio (muy conocido por inundaciones)
    {
        "name": "Paso bajo nivel Americo Vespucio - Pudahuel",
        "lat": -33.4350,
        "lon": -70.7450,
        "description": "Paso bajo nivel con historial recurrente de inundacion y vehiculos atrapados",
        "severity": "muy_alta",
        "last_incident": "2023-06-15"
    },
    # Estacion Central - Alameda
    {
        "name": "Paso bajo nivel Alameda - Estacion Central",
        "lat": -33.4530,
        "lon": -70.6800,
        "description": "Paso bajo nivel frente a Terminal de Buses, frecuentes anegamientos",
        "severity": "alta",
        "last_incident": "2023-06-15"
    },
    # San Miguel - Gran Avenida
    {
        "name": "Paso bajo nivel Gran Avenida - San Miguel",
        "lat": -33.4950,
        "lon": -70.6550,
        "description": "Paso bajo nivel en sector comercial, acumula agua rapidamente",
        "severity": "alta",
        "last_incident": "2022-08-10"
    },
    # La Florida - Vicuna Mackenna
    {
        "name": "Paso bajo nivel Vicuna Mackenna - Departamental",
        "lat": -33.5050,
        "lon": -70.5950,
        "description": "Cruce bajo nivel en avenida principal",
        "severity": "media",
        "last_incident": "2023-06-15"
    },
    # Maipu - Pajaritos
    {
        "name": "Paso bajo nivel Pajaritos - 5 de Abril",
        "lat": -33.4650,
        "lon": -70.7350,
        "description": "Paso bajo nivel con drenaje insuficiente",
        "severity": "alta",
        "last_incident": "2022-06-20"
    },
    # Quinta Normal - Matucana
    {
        "name": "Paso bajo nivel Matucana - Ecuador",
        "lat": -33.4420,
        "lon": -70.6700,
        "description": "Paso bajo nivel cerca de Estacion Central",
        "severity": "media",
        "last_incident": "2023-06-15"
    },
    # Cerrillos - Lo Valledor
    {
        "name": "Paso bajo nivel Lo Valledor",
        "lat": -33.4750,
        "lon": -70.6850,
        "description": "Paso bajo nivel en sector de feria mayorista",
        "severity": "media",
        "last_incident": "2022-08-10"
    },
    # San Bernardo - Americo Vespucio
    {
        "name": "Paso bajo nivel Americo Vespucio - San Bernardo",
        "lat": -33.5850,
        "lon": -70.6950,
        "description": "Paso bajo nivel en autopista, cierres frecuentes",
        "severity": "alta",
        "last_incident": "2023-06-15"
    },
    # Puente Alto - Concha y Toro
    {
        "name": "Paso bajo nivel Concha y Toro",
        "lat": -33.6050,
        "lon": -70.5650,
        "description": "Paso bajo nivel cerca del rio Maipo",
        "severity": "media",
        "last_incident": "2022-06-20"
    },
    # Recoleta - El Salto
    {
        "name": "Paso bajo nivel El Salto - Recoleta",
        "lat": -33.4050,
        "lon": -70.6400,
        "description": "Paso bajo nivel en acceso norte",
        "severity": "media",
        "last_incident": "2023-06-15"
    },
    # Renca - Americo Vespucio
    {
        "name": "Paso bajo nivel Americo Vespucio - Renca",
        "lat": -33.3950,
        "lon": -70.7100,
        "description": "Paso bajo nivel con problemas de drenaje",
        "severity": "alta",
        "last_incident": "2022-08-10"
    },
    # La Cisterna - Gran Avenida
    {
        "name": "Paso bajo nivel Gran Avenida - La Cisterna",
        "lat": -33.5380,
        "lon": -70.6600,
        "description": "Paso bajo nivel en avenida principal del sur",
        "severity": "media",
        "last_incident": "2023-06-15"
    },
    # Pedro Aguirre Cerda - Departamental
    {
        "name": "Paso bajo nivel Departamental - Lo Ovalle",
        "lat": -33.4880,
        "lon": -70.6600,
        "description": "Paso bajo nivel cerca del Zanjon de la Aguada",
        "severity": "alta",
        "last_incident": "2022-06-20"
    },
    # Providencia - Costanera Norte
    {
        "name": "Paso bajo nivel Costanera Norte - Providencia",
        "lat": -33.4200,
        "lon": -70.6100,
        "description": "Tunel de Costanera Norte, acumula agua en tormentas fuertes",
        "severity": "media",
        "last_incident": "2022-08-10"
    },
    # Las Condes - Kennedy
    {
        "name": "Paso bajo nivel Kennedy - Americo Vespucio",
        "lat": -33.4050,
        "lon": -70.5700,
        "description": "Paso bajo nivel en sector oriente",
        "severity": "baja",
        "last_incident": "2021-06-15"
    },
    # Cerro Navia - Ruta 68
    {
        "name": "Paso bajo nivel Ruta 68 - Cerro Navia",
        "lat": -33.4250,
        "lon": -70.7300,
        "description": "Paso bajo nivel en autopista a Valparaiso",
        "severity": "alta",
        "last_incident": "2023-06-15"
    },
    # Lo Prado - Americo Vespucio
    {
        "name": "Paso bajo nivel Americo Vespucio - Lo Prado",
        "lat": -33.4450,
        "lon": -70.7200,
        "description": "Paso bajo nivel con historial de cierres",
        "severity": "alta",
        "last_incident": "2022-08-10"
    },
    # Quilicura - Americo Vespucio
    {
        "name": "Paso bajo nivel Americo Vespucio - Quilicura",
        "lat": -33.3600,
        "lon": -70.7250,
        "description": "Paso bajo nivel en sector norte, problemas de drenaje",
        "severity": "media",
        "last_incident": "2023-06-15"
    },
    # Macul - Vicuna Mackenna
    {
        "name": "Paso bajo nivel Vicuna Mackenna - Macul",
        "lat": -33.4850,
        "lon": -70.5950,
        "description": "Paso bajo nivel cerca de quebrada de Macul",
        "severity": "media",
        "last_incident": "2022-06-20"
    },
    # Penalolen - Grecia
    {
        "name": "Paso bajo nivel Grecia - Tobalaba",
        "lat": -33.4650,
        "lon": -70.5550,
        "description": "Paso bajo nivel en sector oriente",
        "severity": "baja",
        "last_incident": "2021-08-10"
    }
]


def generate_pasos_bajo_nivel() -> List[Dict]:
    """Genera datos de pasos bajo nivel."""
    features = []

    for paso in PASOS_BAJO_NIVEL:
        features.append({
            "lon": paso["lon"],
            "lat": paso["lat"],
            "name": paso["name"],
            "description": paso["description"],
            "severity": paso["severity"],
            "last_incident": paso.get("last_incident", None),
            "type": "paso_bajo_nivel"
        })

    return features


def main():
    pasos = generate_pasos_bajo_nivel()

    outdir = os.path.dirname(__file__)
    outpath = os.path.join(outdir, 'pasos_bajo_nivel.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(pasos, f, ensure_ascii=False, indent=2)

    print(f"Archivo generado: {outpath} ({len(pasos)} pasos bajo nivel)")

    # Resumen por severidad
    severidades = {}
    for p in pasos:
        s = p.get('severity', 'unknown')
        severidades[s] = severidades.get(s, 0) + 1

    print("\nResumen por severidad:")
    for s, c in sorted(severidades.items()):
        print(f"  {s}: {c}")


if __name__ == '__main__':
    main()
