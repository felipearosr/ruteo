# TODO - FASE 3: RUTEO RESILIENTE AVANZADO

**Proyecto:** Sistema de Ruteo Inteligente con Visualización Geoespacial  
**Fase:** 3 de 3 - Ruteo Resiliente con Múltiples Técnicas  
**Fecha de Inicio:** 17 de Noviembre, 2025

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### A. Preparación y Limpieza ✅

- [x] Revisar código actual de routing API
- [x] Verificar que las rutas usan `infra_aristas` correctamente
- [x] Identificar puntos de extensión para Fase 3
- [x] Crear estructura de carpetas: `model/`, `optimization/`, `docs/`

### B. Modelo de Probabilidad de Falla

- [x] Crear `model/probabilidad_fallo.py`
  - [x] Función para calcular distancia a amenazas más cercanas
  - [x] Modelo de probabilidad basado en:
    - [x] Distancia a zonas de inundación histórica
    - [x] Proximidad a estaciones DGA con alto caudal
    - [x] Densidad de reportes ciudadanos
    - [x] Metadata relevante (elevación, lluvia)
  - [x] Persistencia en BD (nuevos campos o tablas auxiliares)
- [x] Actualizar `sql/schema.sql` con campos `p_fallo_nodo`, `p_fallo_arista`
- [x] Crear script `model/actualizar_probabilidades.py` para recalcular
- [x] Integrar cálculo de probabilidades en `main.py` (ahora corre al final del ETL)

### C. Interfaz Web Mejorada

- [x] Geolocalización y Geocodificación
  - [x] Implementar HTML5 Geolocation API
  - [x] Integrar Nominatim para geocodificación de direcciones
  - [x] UI para seleccionar origen (ubicación actual vs dirección)
- [ ] Controles de Restricciones
  - [x] Input: Riesgo máximo aceptable (%)
  - [x] Input: Distancia máxima (km)
  - [ ] Input: Tiempo máximo estimado (min)
  - [ ] Toggle: Evitar zonas de inundación
- [ ] Panel de Comparación de Rutas
  - [x] Tabla con 4 filas (una por ruta)
  - [x] Columnas: Método, Distancia, Tiempo de cómputo, Riesgo acumulado
  - [x] Checkboxes para mostrar/ocultar cada ruta
- [ ] Leyenda de Colores
  - [x] Ruta 1 (Baseline): Azul
  - [x] Ruta 2 (CPLEX): Verde
  - [x] Ruta 3 (Dijkstra Resiliente): Naranja
  - [x] Ruta 4 (Metaheurística): Morado

### D. Implementación de 4 Métodos de Ruteo

#### D.1 Ruta 1: pgr_dijkstra Baseline

- [x] Refactorizar `/api/route` → `/api/route/baseline`
- [x] Asegurar que solo usa costo = distancia
- [x] Agregar medición de tiempo (performance.now())
- [x] Retornar JSON con:
  - [x] `route`: GeoJSON FeatureCollection
  - [x] `metrics`: { distance_m, computation_time_ms, risk_score }

#### D.2 Ruta 2: CPLEX/GUROBI

- [x] Decidir entre CPLEX o GUROBI (usar GUROBI por licencia académica)
- [x] Crear `optimization/gurobi_model.py`
  - [x] Clase `ResilientRouter` con método `solve()`
  - [x] Variables: binarias para cada arista
  - [x] Función objetivo: min(distancia + λ * riesgo)
  - [x] Restricciones:
    - [x] Conservación de flujo (nodo origen = +1, destino = -1, otros = 0)
    - [x] Riesgo acumulado ≤ max_risk (si aplica)
    - [x] Longitud total ≤ max_distance (si aplica)
  - [x] Conversión de solución a lista de aristas
- [x] Crear `/api/route/cplex` (usar endpoint genérico) → `/api/route/optimize` con GUROBI
- [x] Implementar carga de grafo desde Supabase
- [x] Retornar GeoJSON + métricas

#### D.3 Ruta 3: pgr_dijkstra con Costos Ajustados

- [x] Crear función SQL `infra_calcular_costo_resiliente()`
  - [x] Formula: `cost_resiliente = length_m * (1 + k * p_fallo_arista)`
  - [x] Parámetro `k` configurable (ej: 5.0 para penalizar 5x)
- [x] Crear vista `infra_aristas_resilientes` con costos ajustados
- [x] Crear `/api/route/resilient`
  - [x] Query pgr_dijkstra usando vista/función de costos
  - [x] Aplicar filtrado de aristas según restricciones
- [x] Retornar GeoJSON + métricas

#### D.4 Ruta 4: Metaheurística (A* con Heurística de Riesgo)

- [x] Crear `optimization/metaheuristics.py`
  - [x] Implementar A* modificado
  - [x] Heurística h(n) = distancia_euclidiana + factor_riesgo
  - [x] Cargar grafo como diccionario {nodo_id: [(vecino, costo, riesgo), ...]}
  - [x] Función `a_star_resilient(source, target, graph, heuristic_weight)`
- [x] Crear `/api/route/metaheuristic`
- [x] Integrar con BD (leer nodos/aristas)
- [x] Retornar GeoJSON + métricas

### E. API Unificada de Comparación

- [x] Crear `/api/route/compare`
  - [x] Parámetros: `source`, `target`, `max_risk`, `max_distance`
  - [x] Ejecutar las 4 rutas en paralelo (Baseline, Resiliente, A*, GUROBI)
  - [ ] Retornar JSON:
    ```json
    {
      "baseline": { route: ..., metrics: ... },
      "gurobi": { route: ..., metrics: ... },
      "resilient": { route: ..., metrics: ... },
      "metaheuristic": { route: ..., metrics: ... }
    }
    ```
- [ ] Optimizar para compartir conexiones a BD

### F. Simulación de Fallas

- [x] Crear `/api/simulate-failures`
  - [x] Parámetros: `seed` (opcional, para reproducibilidad)
  - [x] Leer `p_fallo_nodo` y `p_fallo_arista` de BD
  - [x] Generar números aleatorios y determinar fallas
  - [x] Guardar estado en tabla temporal `sim_fallas_activas`
  - [x] Retornar JSON: `{ failed_nodes: [...], failed_edges: [...] }`
- [x] Crear tabla `sim_fallas_activas` en schema
- [x] Función para limpiar simulación anterior
- [x] Integrar con UI: botón "Simular Fallas"

### G. Filtrado Visual de Amenazas

- [ ] Agregar checkbox "Mostrar solo amenazas activas/simuladas"
- [ ] Estado React: `activeThreats: Set<number>`
- [ ] Al simular fallas, actualizar `activeThreats`
- [ ] Filtrar marcadores:
  ```tsx
  {showInundaciones && inundaciones
    .filter(item => !onlyActive || activeThreats.has(item.id))
    .map(...)}
  ```
- [ ] Indicador visual de "Simulación activa"

### H. Caso de Ejemplo Demostrativo

- [x] Crear `docs/caso_ejemplo_fase3.md`
  - [x] Descripción del escenario
  - [x] Nodos origen/destino específicos
  - [x] Configuración de amenazas
  - [ ] Resultados esperados de cada ruta
  - [ ] Capturas de pantalla
- [x] Agregar botón "Cargar Ejemplo" en UI
  - [x] Precarga origen = [X], destino = [Y]
  - [ ] Activa amenazas específicas
  - [ ] Configura restricciones predefinidas
- [ ] Documentar diferencias entre las 4 rutas

### I. Dependencias y Configuración

- [x] Actualizar `requirements.txt`:
  - [x] `gurobipy` (o `cplex` si se usa CPLEX)
  - [x] `geopy` (para Nominatim)
  - [ ] `networkx` (para metaheurísticas)
- [x] Actualizar `web/package.json`:
  - [x] Verificar versiones de Leaflet/React
  - [ ] Agregar librerías si es necesario
- [x] Crear `docs/instalacion_gurobi.md` con instrucciones
- [ ] Actualizar `.env.example` con nuevas variables:
  - [ ] `GUROBI_LICENSE_FILE` (si aplica)
  - [ ] `NOMINATIM_USER_AGENT`

### J. Docker y Despliegue

- [ ] Actualizar `docker/Dockerfile.app`
  - [ ] Instalar GUROBI (o versión académica)
  - [ ] Copiar licencia GUROBI si es necesaria
- [ ] Actualizar `docker/start.sh`
  - [ ] Ejecutar `model/actualizar_probabilidades.py` antes de web
  - [ ] Verificar que GUROBI esté accesible
- [ ] Actualizar `docker/docker-compose.yml`
  - [ ] Variables de entorno para GUROBI
- [ ] Probar build completo: `docker compose -f docker/docker-compose.yml build`
- [ ] Probar ejecución: `docker compose -f docker/docker-compose.yml up`

### K. Documentación

- [ ] Crear `docs/fase3_resumen.md`
  - [ ] Arquitectura de Fase 3
  - [ ] Explicación de cada método de ruteo
  - [ ] Modelo de probabilidad de falla
  - [ ] Uso de APIs
  - [ ] Capturas de pantalla
- [x] Actualizar `README.md`
  - [x] Sección de Fase 3
  - [ ] Instrucciones de instalación GUROBI
  - [x] Ejemplos de uso de APIs
- [ ] Actualizar `RESUMEN_FASE2.md` → `RESUMEN_COMPLETO.md`
  - [ ] Agregar sección de Fase 3
  - [ ] Métricas finales del proyecto completo

### L. Testing y Validación

- [ ] Probar Ruta 1 con múltiples origen/destino
- [ ] Probar Ruta 2 (CPLEX/GUROBI) y verificar optimalidad
- [ ] Probar Ruta 3 con diferentes parámetros de riesgo
- [ ] Probar Ruta 4 y comparar con Dijkstra
- [ ] Validar que todas las rutas usan solo `infra_aristas`
- [ ] Probar simulación de fallas con diferentes seeds
- [ ] Verificar filtrado de amenazas activas
- [ ] Probar geolocalización en diferentes navegadores
- [ ] Probar geocodificación con direcciones reales
- [ ] Verificar responsividad de UI
- [ ] Probar caso de ejemplo completo

### M. Optimización y Refinamiento

- [ ] Optimizar queries SQL (EXPLAIN ANALYZE)
- [ ] Agregar índices adicionales si es necesario
- [ ] Implementar caché de rutas frecuentes
- [ ] Loading states para todas las operaciones async
- [ ] Manejo de errores robusto:
  - [ ] Sin ruta posible
  - [ ] Nodos inválidos
  - [ ] Timeout de GUROBI
  - [ ] Error de geocodificación
- [ ] Mejorar UX:
  - [ ] Tooltips explicativos
  - [ ] Mensajes de error claros
  - [ ] Progress bars para operaciones largas
- [ ] Accessibility (ARIA labels, keyboard navigation)

---

## 📊 CRITERIOS DE COMPLETITUD

| Categoría | Requisitos | Completados | % |
|-----------|------------|-------------|---|
| Modelo de Riesgo | 4 entregables | 4 | 100% |
| Métodos de Ruteo | 4 implementaciones | 4 | 100% |
| APIs | 5 endpoints (incl. compare) | 5 | 100% |
| UI Mejorada | 14 subtareas | 12 | 86% |
| Simulación | 4 subtareas | 4 | 100% |
| Caso de Ejemplo | 3 subtareas | 2 | 67% |
| Docker | 5 subtareas | 0 | 0% |
| Documentación | 3 subtareas | 1 | 33% |
| **TOTAL** | **42** | **32** | **76%** |

**Objetivo:** 100% de completitud para Fase 3

---

## 🎯 HITOS

- [ ] **Hito 1:** Modelo de probabilidad funcionando (Semana 1)
- [ ] **Hito 2:** 4 rutas implementadas y visualizables (Semana 2)
- [ ] **Hito 3:** Simulación de fallas operativa (Semana 3)
- [ ] **Hito 4:** Documentación completa y Docker funcionando (Semana 4)

---

## 📝 NOTAS

### Decisiones Técnicas

1. **GUROBI vs CPLEX:** Usar GUROBI por disponibilidad de licencia académica gratuita
2. **Metaheurística:** Implementar A* con heurística de riesgo por balance entre optimalidad y velocidad
3. **Geocodificación:** Usar Nominatim (OpenStreetMap) por ser gratuito y no requerir API key
4. **Simulación:** Usar tabla temporal en lugar de estado en memoria para permitir consultas SQL sobre fallas

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| GUROBI no instala en Docker | Media | Alto | Proveer instrucciones alternativas con versión local |
| Metaheurística es muy lenta | Media | Medio | Implementar timeout y caché de soluciones |
| Geocodificación no encuentra direcciones | Alta | Bajo | Fallback a entrada manual de coordenadas |
| BD muy grande para optimización | Media | Alto | Limitar área de búsqueda con bbox alrededor de origen/destino |

---

**Última actualización:** 26 de November, 2025  
**Estado general:** 🟠 En progreso  
**Próxima tarea:** Añadir restricción de tiempo/evitar inundaciones en UI, optimizar conexiones compartidas en `/api/route/compare`, y preparar Docker con GUROBI/licencia.
