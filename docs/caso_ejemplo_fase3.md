# Caso de Ejemplo - Fase 3: Ruteo Resiliente

## 📍 Escenario

Este caso de ejemplo demuestra cómo las diferentes técnicas de ruteo producen rutas distintas cuando se enfrentan a amenazas de inundación en Santiago, Chile.

### Ubicación: Barrio Providencia - Las Condes

**Origen:** Plaza Italia / Baquedano  
- **Coordenadas:** -33.437, -70.635  
- **Nodo ID:** 15432 (ajustar según datos reales)  
- **Descripción:** Punto de partida en zona central de Santiago

**Destino:** Mall Parque Arauco  
- **Coordenadas:** -33.404, -70.575  
- **Nodo ID:** 28901 (ajustar según datos reales)  
- **Descripción:** Centro comercial en Las Condes

**Distancia directa:** ~7.5 km  
**Rutas principales:** Av. Providencia, Av. Apoquindo, Av. Las Condes

---

## 🌊 Amenazas Configuradas

### 1. Zona de Inundación Histórica

**Ubicación:** Cruce de Av. Providencia con Av. Tobalaba  
- **Coordenadas centrales:** -33.424, -70.605  
- **Radio de influencia:** 500m  
- **Probabilidad de falla:** 0.7 (70%)  
- **Fuente:** Registros de inundación 2020-2023  
- **Descripción:** Zona con drenaje deficiente, se inunda con lluvia >30mm/día

### 2. Estación DGA con Alerta

**Ubicación:** Canal San Carlos  
- **Coordenadas:** -33.420, -70.600  
- **Radio de influencia:** 1000m  
- **Nivel de agua:** 2.3m (alto)  
- **Código estación:** DGA-RM-015  
- **Estado:** ⚠️ Alerta amarilla

### 3. Reportes Ciudadanos Activos

**Reporte 1:** Anegamiento en Av. Providencia altura 2000  
- **Coordenadas:** -33.425, -70.607  
- **Fecha:** 2025-11-17 08:30  
- **Severidad:** Media  
- **Descripción:** "Calzada con 20cm de agua, tráfico lento"

**Reporte 2:** Árbol caído en Av. Pedro de Valdivia  
- **Coordenadas:** -33.422, -70.612  
- **Fecha:** 2025-11-17 09:15  
- **Severidad:** Alta  
- **Descripción:** "Árbol bloqueando dos pistas"

---

## 🎯 Restricciones del Usuario

### Configuración del Caso de Ejemplo

```javascript
{
  "max_risk": 0.3,           // Riesgo acumulado máximo: 30%
  "max_distance": 10000,     // Distancia máxima: 10 km
  "avoid_flooding": true,    // Evitar zonas de inundación
  "lambda_risk": 5.0         // Factor de penalización por riesgo
}
```

---

## 📊 Resultados Esperados de las 4 Rutas

### Ruta 1: Baseline (pgr_dijkstra simple)

**Descripción:** Ruta más corta sin considerar amenazas

**Ruta esperada:**
```
Plaza Italia → Av. Providencia → Av. Tobalaba → Av. Apoquindo → Parque Arauco
```

**Métricas:**
- **Distancia:** 7,520 m
- **Tiempo de cómputo:** ~50 ms
- **Riesgo acumulado:** 0.65 (⚠️ ALTO - atraviesa zona de inundación)
- **Segmentos:** 42 aristas
- **Color en mapa:** 🔵 Azul

**⚠️ Problema:** Esta ruta pasa directamente por la zona de inundación en Providencia x Tobalaba

---

### Ruta 2: GUROBI (Optimización MILP)

**Descripción:** Ruta óptima que minimiza distancia + λ*riesgo

**Ruta esperada:**
```
Plaza Italia → Av. Costanera → Av. Kennedy → Av. Las Condes → Parque Arauco
```

**Métricas:**
- **Distancia:** 8,340 m (+11% vs baseline)
- **Tiempo de cómputo:** ~2,500 ms
- **Riesgo acumulado:** 0.18 (✅ BAJO)
- **Segmentos:** 48 aristas
- **Color en mapa:** 🟢 Verde
- **Estado GUROBI:** OPTIMAL

**✅ Ventaja:** Ruta matemáticamente óptima que balancea distancia y riesgo. Evita completamente la zona de inundación.

---

### Ruta 3: Dijkstra Resiliente (Costos Ajustados)

**Descripción:** Dijkstra con costo = distancia * (1 + k * p_fallo)

**Ruta esperada:**
```
Plaza Italia → Av. Bilbao → Av. Manquehue → Av. Las Condes → Parque Arauco
```

**Métricas:**
- **Distancia:** 8,150 m (+8% vs baseline)
- **Tiempo de cómputo:** ~120 ms
- **Riesgo acumulado:** 0.22 (✅ BAJO)
- **Segmentos:** 45 aristas
- **Color en mapa:** 🟠 Naranja
- **Factor k:** 5.0

**✅ Ventaja:** Mucho más rápido que GUROBI, resultados similares. Buen balance entre optimalidad y velocidad.

---

### Ruta 4: A* con Heurística de Riesgo

**Descripción:** A* que considera distancia euclidiana + riesgo en la heurística

**Ruta esperada:**
```
Plaza Italia → Av. Nueva Providencia → Av. Manquehue → Av. Apoquindo → Parque Arauco
```

**Métricas:**
- **Distancia:** 8,450 m (+12% vs baseline)
- **Tiempo de cómputo:** ~180 ms
- **Riesgo acumulado:** 0.25 (✅ MODERADO)
- **Segmentos:** 46 aristas
- **Nodos explorados:** 1,234
- **Color en mapa:** 🟣 Morado

**✅ Ventaja:** Explora menos nodos que Dijkstra completo. Encuentra ruta razonable rápidamente.

---

## 📈 Tabla Comparativa

| Método | Distancia (m) | Δ vs Baseline | Riesgo | Tiempo (ms) | Ventaja Principal |
|--------|--------------|---------------|---------|-------------|-------------------|
| **Baseline** | 7,520 | - | 0.65 ⚠️ | 50 | Más corta |
| **GUROBI** | 8,340 | +11% | 0.18 ✅ | 2,500 | Óptimo matemático |
| **Dijkstra Resiliente** | 8,150 | +8% | 0.22 ✅ | 120 | Balance optimalidad/velocidad |
| **A*** | 8,450 | +12% | 0.25 ✅ | 180 | Búsqueda dirigida |

---

## 🎨 Visualización en el Mapa

### Código de Colores

```css
/* Rutas */
.ruta-baseline      { color: #0066FF; weight: 4; }  /* Azul */
.ruta-gurobi        { color: #00CC44; weight: 4; }  /* Verde */
.ruta-resiliente    { color: #FF6600; weight: 4; }  /* Naranja */
.ruta-astar         { color: #9933FF; weight: 4; }  /* Morado */

/* Amenazas */
.zona-inundacion    { color: #FF0000; opacity: 0.3; }  /* Rojo */
.estacion-dga       { color: #0044AA; }                /* Azul oscuro */
.reporte-ciudadano  { color: #FF9900; }                /* Naranja */
```

### Capas Habilitadas

- ✅ Ruta Baseline (azul)
- ✅ Ruta GUROBI (verde)  
- ✅ Ruta Resiliente (naranja)
- ✅ Ruta A* (morado)
- ✅ Zona de Inundación (rojo)
- ✅ Estación DGA (azul oscuro)
- ✅ Reportes Ciudadanos (naranja)
- ⬜ Elevación
- ⬜ Lluvia
- ⬜ Landcover

---

## 💡 Análisis y Conclusiones

### ¿Qué Demuestra Este Caso?

1. **La ruta más corta NO es siempre la mejor:**
   - Baseline atraviesa zona de alto riesgo (p=0.65)
   - Puede resultar en retrasos o peligro durante eventos de lluvia

2. **Trade-off entre distancia y seguridad:**
   - Rutas resilientes son 8-12% más largas
   - Pero reducen riesgo en 65-72%
   - Beneficio: mayor confiabilidad durante emergencias

3. **GUROBI encuentra el óptimo global:**
   - Pero es 20x más lento que Dijkstra Resiliente
   - Para uso interactivo, Dijkstra Resiliente es preferible

4. **A* es eficiente para búsquedas dirigidas:**
   - Explora menos nodos que Dijkstra completo
   - Buen balance entre calidad y velocidad

### Recomendaciones de Uso

| Escenario | Método Recomendado | Razón |
|-----------|-------------------|--------|
| Emergencias en tiempo real | **A*** | Respuesta rápida (<200ms) |
| Planificación de rutas | **Dijkstra Resiliente** | Balance óptimo |
| Análisis offline | **GUROBI** | Solución óptima garantizada |
| Navegación estándar | **Baseline** | Cuando no hay amenazas activas |

---

## 🔧 Cómo Cargar Este Ejemplo

### Desde la Interfaz Web

1. Click en botón **"Cargar Ejemplo"** en el panel de control
2. Se precargarán:
   - Origen: Nodo 15432
   - Destino: Nodo 28901
   - Restricciones: max_risk=0.3, max_distance=10000
   - Amenazas activas marcadas
3. Click en **"Comparar Rutas"**
4. Visualizar las 4 rutas simultáneamente

### Desde la API

```bash
# Comparar todas las rutas
curl "http://localhost:3000/api/route/compare?\
source=15432&\
target=28901&\
max_risk=0.3&\
max_distance=10000&\
lambda_risk=5.0"
```

### Respuesta Esperada

```json
{
  "baseline": {
    "route": { "type": "FeatureCollection", "features": [...] },
    "metrics": {
      "distance_m": 7520,
      "computation_time_ms": 50,
      "risk_score": 0.65,
      "num_segments": 42
    }
  },
  "gurobi": {
    "route": { "type": "FeatureCollection", "features": [...] },
    "metrics": {
      "distance_m": 8340,
      "computation_time_ms": 2500,
      "risk_score": 0.18,
      "num_segments": 48,
      "status": "OPTIMAL"
    }
  },
  "resilient": {
    "route": { "type": "FeatureCollection", "features": [...] },
    "metrics": {
      "distance_m": 8150,
      "computation_time_ms": 120,
      "risk_score": 0.22,
      "num_segments": 45
    }
  },
  "astar": {
    "route": { "type": "FeatureCollection", "features": [...] },
    "metrics": {
      "distance_m": 8450,
      "computation_time_ms": 180,
      "risk_score": 0.25,
      "num_segments": 46,
      "nodes_explored": 1234
    }
  }
}
```

---

## 📸 Capturas de Pantalla

*(Agregar capturas una vez implementado)*

1. **Mapa con las 4 rutas superpuestas**
2. **Panel de comparación con métricas**
3. **Zona de inundación resaltada**
4. **Simulación de fallas activa**

---

**Última actualización:** 17 de Noviembre, 2025  
**Autor:** Felipe Aros  
**Versión:** 1.0
