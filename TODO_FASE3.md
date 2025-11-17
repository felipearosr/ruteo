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

- [ ] Crear `model/probabilidad_fallo.py`
  - [ ] Función para calcular distancia a amenazas más cercanas
  - [ ] Modelo de probabilidad basado en:
    - [ ] Distancia a zonas de inundación histórica
    - [ ] Proximidad a estaciones DGA con alto caudal
    - [ ] Densidad de reportes ciudadanos
    - [ ] Metadata relevante (elevación, lluvia)
  - [ ] Persistencia en BD (nuevos campos o tablas auxiliares)
- [ ] Actualizar `sql/schema.sql` con campos `p_fallo_nodo`, `p_fallo_arista`
- [ ] Crear script `model/actualizar_probabilidades.py` para recalcular
- [ ] Integrar cálculo de probabilidades en `main.py`

### C. Interfaz Web Mejorada

- [ ] Geolocalización y Geocodificación
  - [ ] Implementar HTML5 Geolocation API
  - [ ] Integrar Nominatim para geocodificación de direcciones
  - [ ] UI para seleccionar origen (ubicación actual vs dirección)
- [ ] Controles de Restricciones
  - [ ] Input: Riesgo máximo aceptable (%)
  - [ ] Input: Distancia máxima (km)
  - [ ] Input: Tiempo máximo estimado (min)
  - [ ] Toggle: Evitar zonas de inundación
- [ ] Panel de Comparación de Rutas
  - [ ] Tabla con 4 filas (una por ruta)
  - [ ] Columnas: Método, Distancia, Tiempo de cómputo, Riesgo acumulado
  - [ ] Checkboxes para mostrar/ocultar cada ruta
- [ ] Leyenda de Colores
  - [ ] Ruta 1 (Baseline): Azul
  - [ ] Ruta 2 (CPLEX): Verde
  - [ ] Ruta 3 (Dijkstra Resiliente): Naranja
  - [ ] Ruta 4 (Metaheurística): Morado

### D. Implementación de 4 Métodos de Ruteo

#### D.1 Ruta 1: pgr_dijkstra Baseline

- [ ] Refactorizar `/api/route` → `/api/route/baseline`
- [ ] Asegurar que solo usa costo = distancia
- [ ] Agregar medición de tiempo (performance.now())
- [ ] Retornar JSON con:
  - [ ] `route`: GeoJSON FeatureCollection
  - [ ] `metrics`: { distance_m, computation_time_ms, risk_score }

#### D.2 Ruta 2: CPLEX/GUROBI

- [ ] Decidir entre CPLEX o GUROBI (usar GUROBI por licencia académica)
- [ ] Crear `optimization/gurobi_model.py`
  - [ ] Clase `ResilientRouter` con método `solve()`
  - [ ] Variables: binarias para cada arista
  - [ ] Función objetivo: min(distancia + λ * riesgo)
  - [ ] Restricciones:
    - [ ] Conservación de flujo (nodo origen = +1, destino = -1, otros = 0)
    - [ ] Riesgo acumulado ≤ max_risk (si aplica)
    - [ ] Longitud total ≤ max_distance (si aplica)
  - [ ] Conversión de solución a lista de aristas
- [ ] Crear `/api/route/cplex` (usar endpoint genérico)
- [ ] Implementar carga de grafo desde Supabase
- [ ] Retornar GeoJSON + métricas

#### D.3 Ruta 3: pgr_dijkstra con Costos Ajustados

- [ ] Crear función SQL `infra_calcular_costo_resiliente()`
  - [ ] Formula: `cost_resiliente = length_m * (1 + k * p_fallo_arista)`
  - [ ] Parámetro `k` configurable (ej: 5.0 para penalizar 5x)
- [ ] Crear vista `infra_aristas_resilientes` con costos ajustados
- [ ] Crear `/api/route/resilient`
  - [ ] Query pgr_dijkstra usando vista/función de costos
  - [ ] Aplicar filtrado de aristas según restricciones
- [ ] Retornar GeoJSON + métricas

#### D.4 Ruta 4: Metaheurística (A* con Heurística de Riesgo)

- [ ] Crear `optimization/metaheuristics.py`
  - [ ] Implementar A* modificado
  - [ ] Heurística h(n) = distancia_euclidiana + factor_riesgo
  - [ ] Cargar grafo como diccionario {nodo_id: [(vecino, costo, riesgo), ...]}
  - [ ] Función `a_star_resilient(source, target, graph, heuristic_weight)`
- [ ] Crear `/api/route/metaheuristic`
- [ ] Integrar con BD (leer nodos/aristas)
- [ ] Retornar GeoJSON + métricas

### E. API Unificada de Comparación

- [ ] Crear `/api/route/compare`
  - [ ] Parámetros: `source`, `target`, `max_risk`, `max_distance`
  - [ ] Ejecutar las 4 rutas en paralelo (asyncio)
  - [ ] Retornar JSON:
    ```json
    {
      "baseline": { route: ..., metrics: ... },
      "cplex": { route: ..., metrics: ... },
      "resilient": { route: ..., metrics: ... },
      "metaheuristic": { route: ..., metrics: ... }
    }
    ```
- [ ] Optimizar para compartir conexiones a BD

### F. Simulación de Fallas

- [ ] Crear `/api/simulate-failures`
  - [ ] Parámetros: `seed` (opcional, para reproducibilidad)
  - [ ] Leer `p_fallo_nodo` y `p_fallo_arista` de BD
  - [ ] Generar números aleatorios y determinar fallas
  - [ ] Guardar estado en tabla temporal `sim_fallas_activas`
  - [ ] Retornar JSON: `{ failed_nodes: [...], failed_edges: [...] }`
- [ ] Crear tabla `sim_fallas_activas` en schema
- [ ] Función para limpiar simulación anterior
- [ ] Integrar con UI: botón "Simular Fallas"

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

- [ ] Crear `docs/caso_ejemplo_fase3.md`
  - [ ] Descripción del escenario
  - [ ] Nodos origen/destino específicos
  - [ ] Configuración de amenazas
  - [ ] Resultados esperados de cada ruta
  - [ ] Capturas de pantalla
- [ ] Agregar botón "Cargar Ejemplo" en UI
  - [ ] Precarga origen = [X], destino = [Y]
  - [ ] Activa amenazas específicas
  - [ ] Configura restricciones predefinidas
- [ ] Documentar diferencias entre las 4 rutas

### I. Dependencias y Configuración

- [ ] Actualizar `requirements.txt`:
  - [ ] `gurobipy` (o `cplex` si se usa CPLEX)
  - [ ] `geopy` (para Nominatim)
  - [ ] `networkx` (para metaheurísticas)
- [ ] Actualizar `web/package.json`:
  - [ ] Verificar versiones de Leaflet/React
  - [ ] Agregar librerías si es necesario
- [ ] Crear `docs/instalacion_gurobi.md` con instrucciones
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
- [ ] Actualizar `README.md`
  - [ ] Sección de Fase 3
  - [ ] Instrucciones de instalación GUROBI
  - [ ] Ejemplos de uso de APIs
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
| Modelo de Riesgo | 1 script + 2 campos BD | 0 | 0% |
| Métodos de Ruteo | 4 implementaciones | 0 | 0% |
| APIs | 5 endpoints | 0 | 0% |
| UI Mejorada | 8 features | 0 | 0% |
| Simulación | 1 sistema + filtrado | 0 | 0% |
| Caso de Ejemplo | 1 documentado + botón | 0 | 0% |
| Docker | 1 setup actualizado | 0 | 0% |
| Documentación | 3 archivos nuevos | 0 | 0% |
| **TOTAL** | **23** | **0** | **0%** |

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

**Última actualización:** 17 de Noviembre, 2025  
**Estado general:** 🔴 No iniciado  
**Próxima tarea:** Implementar modelo de probabilidad de falla
