# RESUMEN FASE 3 - Progreso Inicial

**Proyecto:** Sistema de Ruteo Inteligente con Visualización Geoespacial  
**Fase:** 3 de 3 - Ruteo Resiliente Avanzado  
**Fecha de Inicio:** 17 de Noviembre, 2025  
**Estado Actual:** � Desarrollo Avanzado (70% completado)

---

## ✅ COMPLETADO HASTA AHORA

### 1. Estructura del Proyecto

Se crearon las siguientes carpetas y archivos:

```
ruteo/
├── model/                           # ✅ NUEVO
│   ├── probabilidad_fallo.py        # Calculador de probabilidades
│   └── actualizar_probabilidades.py # Script de actualización
│
├── optimization/                    # ✅ NUEVO
│   ├── gurobi_model.py             # Optimización MILP con GUROBI
│   └── metaheuristics.py           # A* con heurística de riesgo
│
├── docs/                           # ✅ NUEVO
│   ├── caso_ejemplo_fase3.md       # Caso demostrativo documentado
│   └── instalacion_gurobi.md       # Guía de instalación GUROBI
│
├── TODO_FASE3.md                   # ✅ NUEVO - Checklist detallado
├── sql/schema.sql                  # ✅ ACTUALIZADO - Nuevos campos
└── requirements.txt                # ✅ ACTUALIZADO - Nuevas dependencias
```

---

### 2. Modelo de Probabilidad de Falla

**Archivo:** `model/probabilidad_fallo.py`

**Características implementadas:**
- ✅ Cálculo de probabilidad basado en distancia a amenazas
- ✅ Factores considerados:
  - Inundaciones históricas (peso: 40%, radio: 500m)
  - Estaciones DGA (peso: 30%, radio: 1000m)
  - Reportes ciudadanos (peso: 20%, radio: 200m)
  - Precipitación (peso: 10%)
- ✅ Función exponencial decreciente: `exp(-distancia/radio)`
- ✅ Actualización en lotes (batch_size=1000)
- ✅ Progress tracking con prints
- ✅ Soporte para nodos y aristas

**Script de actualización:** `model/actualizar_probabilidades.py`
- ✅ Verificación de variables de entorno
- ✅ Ejecución independiente
- ✅ Manejo de errores robusto

---

### 3. Schema de Base de Datos Actualizado

**Archivo:** `sql/schema.sql`

**Nuevos campos agregados:**

```sql
-- En infra_nodos
p_fallo_nodo double precision default 0.0

-- En infra_aristas  
p_fallo_arista double precision default 0.0
```

**Nuevas funciones SQL:**

```sql
-- Función para calcular costos resilientes
infra_calcular_costo_resiliente(k double precision)
-- Retorna aristas con cost = length_m * (1 + k * p_fallo_arista)
```

**Nueva tabla:**

```sql
-- Tabla para simulaciones de fallas
sim_fallas_activas (
    id, simulation_id, entity_type, entity_id,
    p_fallo, random_value, is_failed, created_at
)
```

---

### 4. Optimización con GUROBI

**Archivo:** `optimization/gurobi_model.py`

**Características implementadas:**
- ✅ Clase `ResilientRouter` con método `solve()`
- ✅ Modelo MILP:
  - Variables binarias `x[arista]` (1 si se usa, 0 si no)
  - Función objetivo: `min(distancia + λ * distancia * riesgo)`
  - Restricciones de conservación de flujo
  - Restricción de riesgo máximo (opcional)
  - Restricción de distancia máxima (opcional)
- ✅ Carga eficiente de grafo (con bounding box)
- ✅ Conversión de solución a GeoJSON
- ✅ Métricas: distancia total, riesgo acumulado, tiempo de cómputo
- ✅ Timeout configurable (default: 300s)
- ✅ Manejo de casos sin licencia GUROBI

**Parámetros configurables:**
- `source`, `target`: Nodos origen/destino
- `max_risk`: Riesgo acumulado máximo permitido
- `max_distance`: Distancia máxima permitida
- `lambda_risk`: Factor de penalización por riesgo (default: 5.0)

---

### 5. Metaheurística A*

**Archivo:** `optimization/metaheuristics.py`

**Características implementadas:**
- ✅ Clase `AStarResilientRouter`
- ✅ Algoritmo A* con:
  - Heurística: distancia euclidiana + factor de riesgo
  - Costo: `distancia * (1 + risk_weight * p_fallo)`
  - Priority queue con heap
  - Conjunto de nodos explorados
- ✅ Grafo como diccionario de adyacencia
- ✅ Reconstrucción de camino con `came_from`
- ✅ Métricas: nodos explorados, tiempo, distancia, riesgo
- ✅ Conversión a GeoJSON

**Parámetros configurables:**
- `source`, `target`: Nodos origen/destino
- `risk_weight`: Peso del riesgo en el costo (default: 3.0)
- `heuristic_weight`: Peso de la heurística (default: 1.0)

**Ventajas sobre Dijkstra:**
- Explora menos nodos (búsqueda dirigida)
- Más rápido para grafos grandes
- Resultados cercanos al óptimo

---

### 6. Documentación

#### `docs/caso_ejemplo_fase3.md`

Caso de ejemplo completo documentado:
- ✅ Escenario: Providencia → Las Condes
- ✅ Amenazas configuradas (zona inundación, estación DGA, reportes)
- ✅ Restricciones del usuario
- ✅ Resultados esperados de las 4 rutas:
  - Baseline: 7,520m, riesgo 0.65, 50ms
  - GUROBI: 8,340m, riesgo 0.18, 2,500ms (ÓPTIMO)
  - Dijkstra Resiliente: 8,150m, riesgo 0.22, 120ms
  - A*: 8,450m, riesgo 0.25, 180ms
- ✅ Tabla comparativa
- ✅ Código de colores para visualización
- ✅ Análisis y conclusiones
- ✅ Instrucciones de carga

#### `docs/instalacion_gurobi.md`

Guía completa de instalación:
- ✅ 3 opciones de licencia (académica, prueba, comunitaria)
- ✅ Pasos detallados de instalación
- ✅ Configuración en Docker (3 opciones)
- ✅ Tests de verificación
- ✅ Solución de problemas comunes
- ✅ Alternativas open source (PuLP, OR-Tools)
- ✅ Comparación de solvers

#### `TODO_FASE3.md`

Checklist exhaustivo:
- ✅ 13 secciones (A-M)
- ✅ 80+ tareas individuales
- ✅ Criterios de completitud
- ✅ Hitos por semana
- ✅ Decisiones técnicas
- ✅ Riesgos y mitigaciones

---

### 7. Dependencias Actualizadas

**`requirements.txt`:**

```
# Existentes
requests>=2.28
geojson>=2.5
shapely>=2.0
psycopg2-binary>=2.9
python-dotenv>=1.0
supabase>=2.0
tqdm>=4.65

# Nuevas para Fase 3
gurobipy>=11.0       # Optimización MILP
geopy>=2.4           # Geocodificación con Nominatim
```

---

## 🔄 PENDIENTE DE IMPLEMENTAR (30% restante)

### ✅ APIs Backend (Endpoints Next.js) - COMPLETADO 100%

1. ✅ **`/api/route/baseline`** - Dijkstra clásico (shortest path)
2. ✅ **`/api/route/optimize`** - GUROBI (MILP optimization)
3. ✅ **`/api/route/resilient`** - Dijkstra con costos ajustados
4. ✅ **`/api/route/metaheuristic`** - A* con heurística de riesgo
5. ✅ **`/api/route/compare`** - Comparación unificada de las 4 rutas
6. 🔄 **`/api/simulate-failures`** - Simulación de fallas (PENDIENTE)

### ✅ Frontend con shadcn/ui - COMPLETADO 100%

**Componentes UI implementados:**
- ✅ Button, Checkbox, Label, Input
- ✅ Card (Header, Title, Description, Content)
- ✅ Badge, Table (Header, Body, Row, Cell)
- ✅ Configuración de Tailwind con tema shadcn
- ✅ Utilidad `cn()` para className merging

**Interfaz principal (`page.tsx`) refactorizada:**

1. ✅ **Panel lateral izquierdo con controles:**
   - ✅ Inputs para nodo origen/destino
   - ✅ Inputs para parámetros (k, λ, risk_weight)
   - ✅ Botón "Comparar Rutas" con loading state
   - ✅ Checkboxes para toggle de 4 rutas (baseline, resilient, GUROBI, A*)
   - ✅ Checkboxes para amenazas (inundaciones, reportes, DGA)
   - ✅ Tabla comparativa de métricas (distancia, tiempo, riesgo)
   - ✅ Badges con resúmenes (shortest, lowest risk, fastest)

2. ✅ **Mapa Leaflet con visualización:**
   - ✅ 4 Polylines con colores distintos:
     - Baseline: Azul (#3b82f6)
     - Resiliente: Naranja (#f97316)
     - GUROBI: Verde (#22c55e)
     - A*: Púrpura (#a855f7)
   - ✅ CircleMarkers para amenazas (inundaciones, reportes, DGA)
   - ✅ Popups informativos con detalles
   - ✅ Leyenda visual en esquina inferior derecha
   - ✅ Responsive layout (panel lateral + mapa)

3. 🔄 **Funcionalidades pendientes:**
   - 🔄 Geolocalización HTML5 (detectar ubicación del usuario)
   - 🔄 Geocodificación con Nominatim (input de dirección textual)
   - Inputs de restricciones (max_risk, max_distance)
   
2. **Visualización de 4 rutas:**
   - 4 Polylines con colores distintos
   - Checkboxes para mostrar/ocultar
   - Leyenda de colores

3. **Panel de comparación:**
   - Tabla con métricas de cada ruta
   - Distancia, tiempo, riesgo
   - Highlighting de la mejor opción

4. **Simulación de fallas:**
   - Botón "Simular Fallas"
   - Checkbox "Mostrar solo amenazas activas"
   - Indicador de simulación activa

5. **Caso de ejemplo:**
   - Botón "Cargar Ejemplo"
   - Precarga de origen/destino
   - Amenazas predefinidas

### Docker

1. **Actualizar `Dockerfile.app`:**
   - Instalar GUROBI
   - Copiar archivos de licencia

2. **Actualizar `start.sh`:**
   - Ejecutar `actualizar_probabilidades.py`
   - Verificar GUROBI disponible

3. **Actualizar `docker-compose.yml`:**
   - Variables de entorno GUROBI
   - Volúmenes para licencia

---

## 📊 PROGRESO GENERAL

| Categoría | Tareas Totales | Completadas | % |
|-----------|----------------|-------------|---|
| Estructura | 3 | 3 | 100% |
| Modelo de Riesgo | 4 | 4 | 100% |
| Schema BD | 3 | 3 | 100% |
| Backend Python | 4 | 4 | 100% |
| APIs Next.js | 6 | 0 | 0% |
| Frontend React | 8 | 0 | 0% |
| Docker | 3 | 0 | 0% |
| Documentación | 3 | 3 | 100% |
| Testing | 5 | 0 | 0% |
| **TOTAL** | **39** | **17** | **44%** |

---

## 🎯 PRÓXIMOS PASOS

### Prioridad Alta (Esta Semana)

1. **Implementar endpoints de API:**
   - Crear `/api/route/baseline` (refactorizar existente)
   - Crear `/api/route/optimize` (GUROBI)
   - Crear `/api/route/resilient` (Dijkstra ajustado)
   - Crear `/api/route/metaheuristic` (A*)
   - Crear `/api/route/compare` (unificado)

2. **Extender interfaz web:**
   - Agregar controles de restricciones
   - Panel de comparación de rutas
   - Visualización de 4 rutas con colores

3. **Probar integración:**
   - Ejecutar scripts Python standalone
   - Verificar que APIs retornan GeoJSON correcto
   - Validar tiempos de cómputo

### Prioridad Media (Próxima Semana)

4. **Simulación de fallas:**
   - Endpoint `/api/simulate-failures`
   - Integración con frontend
   - Filtrado visual de amenazas

5. **Geolocalización y geocodificación:**
   - HTML5 Geolocation API
   - Integración con Nominatim
   - Fallback a input manual

6. **Docker:**
   - Actualizar configuración
   - Probar build completo
   - Documentar deployment

### Prioridad Baja (Pulido Final)

7. **Testing y validación:**
   - Casos de prueba
   - Manejo de errores edge cases
   - Performance optimization

8. **Documentación final:**
   - `docs/fase3_resumen.md` completo
   - Actualizar `README.md`
   - Screenshots y ejemplos

---

## 💡 NOTAS TÉCNICAS

### Decisiones de Diseño

1. **GUROBI vs CPLEX:** Elegimos GUROBI por disponibilidad de licencia académica gratuita

2. **A* vs GRASP:** A* es más simple de implementar y dar resultados óptimos para este caso

3. **Nominatim vs Google Maps API:** Nominatim es gratuito y no requiere API key

4. **Tabla temporal vs estado en memoria:** Tabla `sim_fallas_activas` permite consultas SQL

### Validaciones Pendientes

- [ ] Verificar que todas las rutas usan solo geometrías de `infra_aristas`
- [ ] Confirmar que no se dibujan líneas rectas que crucen zonas sin caminos
- [ ] Validar que las 4 rutas dan resultados diferentes en el caso de ejemplo
- [ ] Probar con grafos de diferentes tamaños (100 nodos, 1000 nodos, 10000 nodos)

---

## 📞 SOPORTE

Si tienes preguntas o problemas:

1. **Revisa la documentación:** `docs/` tiene guías detalladas
2. **Consulta el TODO:** `TODO_FASE3.md` tiene el checklist completo
3. **Revisa el código:** Todos los módulos Python tienen docstrings
4. **Ejecuta los tests:** Scripts Python tienen función `main()` para pruebas

---

**Última actualización:** 17 de Noviembre, 2025  
**Autor:** Felipe Aros  
**Estado:** 🟡 En desarrollo activo  
**Próxima revisión:** Después de implementar APIs backend
