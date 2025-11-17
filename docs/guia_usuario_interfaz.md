# Guía de Usuario - Interfaz de Ruteo Resiliente

**Versión:** Fase 3  
**Última actualización:** Enero 2025

---

## Descripción General

La nueva interfaz permite comparar 4 métodos de ruteo resiliente simultáneamente, visualizando las rutas en un mapa interactivo con métricas detalladas.

---

## Métodos de Ruteo Disponibles

### 1. **Baseline (Azul)** 🔵
- **Algoritmo:** Dijkstra clásico
- **Objetivo:** Ruta más corta (distancia mínima)
- **Uso:** Referencia para comparar con otros métodos
- **Color en mapa:** Azul (#3b82f6)

### 2. **Resiliente (Naranja)** 🟠
- **Algoritmo:** Dijkstra con costos ajustados
- **Objetivo:** Balance entre distancia y riesgo
- **Parámetro:** `k` (factor de penalización, default: 5.0)
- **Fórmula:** `costo = distancia × (1 + k × probabilidad_fallo)`
- **Color en mapa:** Naranja (#f97316)

### 3. **GUROBI (Verde)** 🟢
- **Algoritmo:** Optimización MILP (Mixed Integer Linear Programming)
- **Objetivo:** Ruta óptima global (exacta)
- **Parámetro:** `λ` (lambda_risk, default: 5.0)
- **Características:**
  - Solución matemáticamente óptima
  - Puede tomar más tiempo (hasta 300s)
  - Requiere licencia GUROBI (académica, prueba o comunitaria)
  - Si no está disponible, muestra mensaje de error
- **Color en mapa:** Verde (#22c55e)

### 4. **A* (Púrpura)** 🟣
- **Algoritmo:** Metaheurística A* con heurística de riesgo
- **Objetivo:** Buena aproximación rápida
- **Parámetros:** `risk_weight` (peso del riesgo, default: 3.0)
- **Características:**
  - Más rápido que GUROBI
  - Solución cercana al óptimo
  - Explora menos nodos que Dijkstra
- **Color en mapa:** Púrpura (#a855f7)

---

## Componentes de la Interfaz

### Panel Lateral Izquierdo

#### 1. **Sección de Parámetros**

**Nodo Origen y Destino:**
- Campos numéricos para ID de nodos en la base de datos
- Ejemplo: `1` (Providencia) → `100` (Las Condes)
- Los nodos deben existir en la tabla `infra_nodos`

**Parámetros de Algoritmos:**
- **Factor k (Resiliente):** Penalización por riesgo (0.1 - 20.0)
  - Mayor k = mayor evitación de áreas riesgosas
  - Menor k = prioriza distancia sobre riesgo
  
- **λ (Lambda GUROBI):** Factor de riesgo en optimización (0.1 - 20.0)
  - Controla trade-off distancia vs. riesgo
  
- **Peso Riesgo (A*):** Peso del riesgo en heurística (0.1 - 10.0)
  - Afecta exploración del algoritmo

**Botón "Comparar Rutas":**
- Ejecuta las 4 rutas simultáneamente
- Muestra loading spinner durante cálculo
- Timeout: 5 minutos máximo

#### 2. **Control de Capas - Rutas**

Checkboxes para mostrar/ocultar cada ruta:
- ☑ Baseline (azul)
- ☑ Resiliente (naranja)
- ☑ GUROBI (verde)
- ☑ A* (púrpura)

**Uso:**
- Desmarcar para ocultar temporalmente una ruta
- Útil para comparar solo 2 o 3 rutas específicas

#### 3. **Control de Capas - Amenazas**

Checkboxes para capas de amenazas:
- ☑ **Zonas de Inundación:** Círculos rojos (inundaciones históricas)
- ☑ **Reportes Ciudadanos:** Círculos naranjas (reportes de usuarios)
- ☐ **Estaciones DGA:** Círculos azules (estaciones de nivel de agua)

**Popups informativos:**
- Click en cualquier amenaza para ver detalles
- Inundaciones: fecha, fuente
- Reportes: tipo, fecha de reporte
- DGA: código de estación, nivel de agua

#### 4. **Tabla Comparativa**

Muestra métricas de las 4 rutas:

| Método     | Distancia | Tiempo  | Riesgo |
|------------|-----------|---------|--------|
| Baseline   | 7.52 km   | 50 ms   | 65.0%  |
| Resiliente | 8.15 km   | 120 ms  | 22.0%  |
| GUROBI     | 8.34 km   | 2.5 s   | 18.0%  |
| A*         | 8.45 km   | 180 ms  | 25.0%  |

**Badges de resumen:**
- 🏆 **Distancia más corta:** Valor mínimo entre las 4 rutas
- 🛡️ **Menor riesgo:** Ruta más segura
- ⚡ **Más rápido:** Tiempo de cómputo menor

---

### Mapa Interactivo (Lado Derecho)

#### Visualización de Rutas

- **4 Polylines** superpuestas en el mapa
- **Colores distintos** para cada método
- **Grosor:** 4px con opacidad 0.7
- **Interactividad:** Zoom y pan con scroll y arrastre

#### Leyenda Visual

Ubicada en esquina inferior derecha:
```
━━ Baseline (más corta)
━━ Resiliente (ajustada)
━━ GUROBI (óptima)
━━ A* (metaheurística)
```

#### Mapa Base

- Tiles: OpenStreetMap
- Centro inicial: Santiago, Chile (-33.45, -70.65)
- Zoom inicial: 13

---

## Casos de Uso

### Caso 1: Comparación Rápida

**Objetivo:** Ver todas las rutas y elegir la mejor

**Pasos:**
1. Ingresar nodo origen (ej: 1)
2. Ingresar nodo destino (ej: 100)
3. Usar valores default de parámetros
4. Click en "Comparar Rutas"
5. Esperar 2-5 segundos
6. Revisar tabla comparativa
7. Identificar badges de resumen

**Resultado esperado:**
- GUROBI: Menor riesgo (óptimo) pero más lento
- Resiliente: Buen balance
- A*: Rápido con buen resultado
- Baseline: Más corto pero más riesgoso

---

### Caso 2: Ajuste de Parámetros

**Objetivo:** Personalizar nivel de aversión al riesgo

**Pasos:**
1. Configurar origen/destino
2. **Aumentar k a 10.0** (Resiliente muy conservador)
3. **Aumentar λ a 10.0** (GUROBI muy conservador)
4. Click en "Comparar Rutas"
5. Observar cómo las rutas evitan más las amenazas

**Resultado esperado:**
- Rutas más largas pero con riesgo significativamente menor
- Mayor diferencia con baseline

---

### Caso 3: Análisis de Amenazas

**Objetivo:** Entender por qué ciertas rutas evitan áreas específicas

**Pasos:**
1. Activar todas las capas de amenazas
2. Calcular rutas
3. Comparar rutas baseline vs. resiliente
4. Click en amenazas para ver detalles
5. Observar cómo las rutas las rodean

**Resultado esperado:**
- Baseline pasa cerca/a través de amenazas
- Resiliente/GUROBI/A* las evitan

---

### Caso 4: Evaluación de Performance

**Objetivo:** Comparar tiempos de cómputo

**Pasos:**
1. Configurar rutas largas (ej: nodo 1 → 500)
2. Click en "Comparar Rutas"
3. Observar tiempos en tabla:
   - Baseline: ~100ms (más rápido)
   - A*: ~200ms (rápido)
   - Resiliente: ~300ms (medio)
   - GUROBI: 2-10s (más lento pero óptimo)

**Conclusión:**
- Para aplicaciones en tiempo real: usar A* o Resiliente
- Para planificación offline: usar GUROBI

---

## Interpretación de Métricas

### Distancia (km)

- **Significado:** Longitud total de la ruta en kilómetros
- **Rango típico:** 5-15 km (depende de origen/destino)
- **Interpretación:**
  - Menor = más eficiente en combustible/tiempo
  - Mayor = posible desvío para evitar riesgo

### Tiempo de Cómputo (ms/s)

- **Significado:** Tiempo que tardó el algoritmo en calcular
- **Rango típico:**
  - Baseline: 50-200 ms
  - Resiliente: 100-500 ms
  - A*: 150-500 ms
  - GUROBI: 1-10 s
- **Interpretación:**
  - Importante para aplicaciones en tiempo real
  - GUROBI sacrifica tiempo por optimalidad

### Riesgo (%)

- **Significado:** Probabilidad acumulada de fallo en la ruta
- **Cálculo:** Suma de `p_fallo_arista` de todas las aristas
- **Rango típico:** 10-80%
- **Interpretación:**
  - 0-20%: Ruta muy segura
  - 20-40%: Ruta segura
  - 40-60%: Riesgo moderado
  - 60-80%: Riesgo alto
  - 80-100%: Ruta muy riesgosa

---

## Troubleshooting

### Problema: "GUROBI no disponible"

**Causa:** Licencia de GUROBI no configurada

**Solución:**
1. Obtener licencia académica/prueba en gurobi.com
2. Instalar gurobipy: `pip install gurobipy`
3. Activar licencia: `grbgetkey YOUR_LICENSE_KEY`
4. Reiniciar servidor

**Alternativa:** Usar solo Baseline, Resiliente y A*

---

### Problema: "No route found"

**Causa:** Nodos no conectados en el grafo

**Solución:**
1. Verificar que los nodos existan: `SELECT * FROM infra_nodos WHERE id IN (1, 100)`
2. Verificar conectividad: ejecutar Baseline primero
3. Si Baseline falla = problema de datos
4. Si solo GUROBI/A* falla = problema de restricciones

---

### Problema: Timeout (>5 minutos)

**Causa:** Rutas muy largas con muchos nodos

**Solución:**
1. Reducir distancia entre origen/destino
2. Reducir parámetros de penalización (k, λ)
3. Solo usar GUROBI para rutas cortas (<50 nodos)
4. Preferir A* para rutas largas

---

### Problema: Rutas idénticas

**Causa:** Probabilidades de fallo muy bajas o parámetros muy pequeños

**Solución:**
1. Verificar que las probabilidades estén calculadas:
   ```sql
   SELECT AVG(p_fallo_arista) FROM infra_aristas;
   -- Debería ser > 0.01
   ```
2. Ejecutar script de actualización:
   ```bash
   python model/actualizar_probabilidades.py
   ```
3. Aumentar parámetros (k, λ) a 10.0 o más

---

## Próximas Funcionalidades

### En desarrollo:

- 🔄 **Geolocalización:** Detectar ubicación del usuario automáticamente
- 🔄 **Geocodificación:** Ingresar dirección en vez de ID de nodo
- 🔄 **Simulación de fallas:** Activar/desactivar amenazas manualmente
- 🔄 **Caso de ejemplo:** Botón "Cargar Ejemplo" con datos precargados
- 🔄 **Exportación:** Descargar rutas en formato GPX/GeoJSON

---

## Soporte Técnico

**Documentación adicional:**
- `docs/caso_ejemplo_fase3.md` - Caso demostrativo completo
- `docs/instalacion_gurobi.md` - Guía de instalación de GUROBI
- `TODO_FASE3.md` - Checklist de funcionalidades

**Repositorio:** github.com/felipearosr/ruteo

---

**¡Importante!** Esta interfaz está optimizada para pantallas de escritorio (≥1280px). Para móviles, se recomienda usar en orientación horizontal.
