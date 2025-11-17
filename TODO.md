# TODO - Fase 2: Ruteo Resiliente ante Inundaciones Urbanas

Estado del proyecto según la rúbrica de evaluación.

---

## ✅ 0. Diagrama de BD y schema.sql

**Estado:** COMPLETADO

- [x] `sql/schema.sql` - Esquema completo de la base de datos con PostGIS y pgRouting
  - Extensiones habilitadas: `postgis`, `pgrouting`
  - Tablas de infraestructura: `infra_nodos`, `infra_aristas`
  - Tablas de metadata: `meta_elevacion`, `meta_lluvia`, `meta_landcover`
  - Tablas de amenazas: `amenaza_dga`, `amenaza_inundaciones_hist`, `amenaza_reportes_ciudadanos`
  - Índices GIST en todas las geometrías
  - Función `infra_calcular_longitudes_costs()` para calcular costos

- [ ] `sql/diagram.png` - Imagen del diagrama de la base de datos
  - **PENDIENTE:** Crear diagrama visual de las tablas y relaciones
  - Herramientas sugeridas: dbdiagram.io, draw.io, DBeaver

**Datos cargados en Supabase:**
- 602,652 nodos
- 138,905 aristas
- Metadata y amenazas completas

---

## ✅ 1. Carpeta Infraestructura

**Estado:** COMPLETADO

- [x] `infraestructura/osm_infra_etl.py` - ETL que consulta Overpass API
  - Extrae red vial (ways con tag highway)
  - Genera `infraestructura/infraestructura.geojson` (133,905 features)
  - Configurable por bounding box vía variable de entorno

---

## ✅ 2. Carpeta Metadata

**Estado:** COMPLETADO

Scripts ETL:
- [x] `metadata/elevacion_etl.py` → `metadata/elevacion.json`
- [x] `metadata/lluvia_etl.py` → `metadata/lluvia.json`
- [x] `metadata/landcover_etl.py` → `metadata/landcover.json`

Todos funcionan con datos de ejemplo (simulados). En producción se conectarían a APIs reales.

---

## ✅ 3. Carpeta Amenazas

**Estado:** COMPLETADO

Scripts ETL:
- [x] `amenazas/dga_etl.py` → `amenazas/dga_estaciones.json`
- [x] `amenazas/inundaciones_hist_etl.py` → `amenazas/inundaciones_hist.json`
- [x] `amenazas/reportes_ciudadanos_etl.py` → `amenazas/reportes_ciudadanos.json`

Todos funcionan con datos de ejemplo (simulados). En producción se conectarían a APIs/BDs reales.

---

## ✅ 4. Documentación de archivos JSON/GeoJSON

**Estado:** COMPLETADO

Schemas creados:
- [x] `infraestructura/infra_schema.md` - Estructura del GeoJSON de red vial
- [x] `metadata/elevacion_schema.md` - Estructura del JSON de elevación
- [x] `metadata/lluvia_schema.md` - Estructura del JSON de lluvia
- [x] `metadata/landcover_schema.md` - Estructura del JSON de landcover
- [x] `amenazas/dga_schema.md` - Estructura del JSON de estaciones DGA
- [x] `amenazas/inundaciones_hist_schema.md` - Estructura del JSON de inundaciones
- [x] `amenazas/reportes_ciudadanos_schema.md` - Estructura del JSON de reportes

Cada archivo explica campos, tipos de datos y formato con ejemplos.

---

## ⚠️ 5. (Punto omitido en la rúbrica)

No existe el punto 5 en la rúbrica proporcionada.

---

## ✅ 6. Loaders SQL para cada JSON

**Estado:** COMPLETADO

Loaders creados:
- [x] `infraestructura/load_infra.sql` - Carga nodos y aristas desde GeoJSON
- [x] `metadata/load_elevacion.sql` - Carga datos de elevación
- [x] `metadata/load_lluvia.sql` - Carga datos de lluvia
- [x] `metadata/load_landcover.sql` - Carga datos de landcover
- [x] `amenazas/load_dga.sql` - Carga estaciones DGA
- [x] `amenazas/load_inundaciones_hist.sql` - Carga zonas de inundación
- [x] `amenazas/load_reportes_ciudadanos.sql` - Carga reportes ciudadanos

**Nota:** Además se crearon scripts Python alternativos para facilitar la carga:
- `load_to_supabase.py` - Carga vía conexión directa PostgreSQL (requiere IPv6)
- `load_to_supabase_api.py` - Carga vía API REST (metadata y amenazas)
- `load_infraestructura_batch.py` - Carga infraestructura en lotes vía API REST (USADO)

---

## ✅ 7. Carpeta Sitio Web con Leaflet

**Estado:** COMPLETADO

Archivos implementados:
- [x] `web/package.json` - Dependencias actualizadas: Next.js, React, Leaflet, Supabase, pg
- [x] `web/tsconfig.json` - Configuración TypeScript para Next.js 14
- [x] `web/postcss.config.js` - Configuración de PostCSS con Tailwind
- [x] `web/src/app/layout.tsx` - Layout raíz con imports de CSS global y Leaflet
- [x] `web/src/app/globals.css` - Estilos globales con Tailwind
- [x] `web/src/app/page.tsx` - Página principal completa con:
  - Mapa Leaflet centrado en Santiago
  - Carga de todas las capas desde Supabase
  - Visualización de metadata (elevación, lluvia, landcover)
  - Visualización de amenazas (DGA, inundaciones, reportes)
  - Controles de capas con checkboxes
  - Panel de control para calcular rutas
  - Inputs para nodo origen/destino
  - Visualización de ruta como Polyline azul
  - Popups informativos para cada capa
- [x] `web/src/app/api/route/index.ts` - Endpoint API implementado (ver punto 8)
- [x] `web/next.config.mjs` - Configuración de Next.js
- [x] `web/tailwind.config.ts` - Configuración de Tailwind CSS
- [x] `web/.env.local` - Variables de entorno configuradas
- [x] `web/.env.local.example` - Plantilla de variables de entorno

**Características implementadas:**
- ✅ Mapas interactivo con OpenStreetMap
- ✅ Capas activables/desactivables con controles
- ✅ Colores diferenciados por tipo de capa
- ✅ Popups con información detallada
- ✅ Diseño responsive con Tailwind CSS
- ✅ Servidor Next.js funcional en puerto 3000

---

## ✅ 8. Ruta con pgr_dijkstra

**Estado:** COMPLETADO

- [x] Endpoint API implementado en `web/src/app/api/route/index.ts`
  - Conexión directa a PostgreSQL usando librería `pg`
  - Consulta SQL con `pgr_dijkstra` usando campo `cost` de aristas
  - Parámetros configurables vía query params: `?source=1&target=100`
  - Retorna GeoJSON FeatureCollection con geometrías LineString
  - Manejo de errores con mensajes descriptivos
  - Incluye metadata de cada segmento (seq, edge_id, cost, length_m, highway)

- [x] Visualización en el mapa de Leaflet
  - Dibuja ruta como Polyline azul con peso 4 y opacidad 0.7
  - Panel de control con inputs para nodos origen/destino
  - Botón "Calcular Ruta" para actualizar en tiempo real
  - Muestra cantidad de segmentos en la ruta
  - Checkbox para activar/desactivar visualización de ruta

**Consulta SQL implementada:**
```sql
SELECT 
  json_build_object(
    'type', 'FeatureCollection',
    'features', COALESCE(json_agg(
      json_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(a.geom)::json,
        'properties', json_build_object(
          'seq', r.seq,
          'edge_id', r.edge,
          'cost', r.cost,
          'length_m', a.length_m,
          'highway', a.highway
        )
      ) ORDER BY r.seq
    ), '[]'::json)
  ) as route
FROM pgr_dijkstra(
  'SELECT id, source, target, cost FROM infra_aristas WHERE cost IS NOT NULL',
  $1,  -- source node
  $2,  -- target node
  directed := false
) r
JOIN infra_aristas a ON r.edge = a.id;
```

**Variables de entorno configuradas:**
- `SUPABASE_DB_HOST`: db.eqjzlgbjgwbnvqzbomsn.supabase.co
- `SUPABASE_DB_PORT`: 6543 (pooler)
- `SUPABASE_DB_USER`: postgres.eqjzlgbjgwbnvqzbomsn
- `SUPABASE_DB_PASSWORD`: [configurado en .env.local]

---

## ✅ 9. Archivo main.py en la raíz

**Estado:** COMPLETADO

- [x] `main.py` - Orquestador que ejecuta todos los ETL en orden
  - Ejecuta `infraestructura/osm_infra_etl.py`
  - Ejecuta los 3 ETL de metadata
  - Ejecuta los 3 ETL de amenazas
  - Muestra instrucciones para cargar datos a Supabase y lanzar web

**PENDIENTE (opcional):**
- [ ] Integrar la carga a Supabase dentro de `main.py` (actualmente son scripts separados)
- [ ] Agregar paso para lanzar el servidor Next.js automáticamente

---

## ⚠️ 10. Contenedores Docker

**Estado:** PARCIALMENTE COMPLETADO

Archivos creados:
- [x] `docker/Dockerfile.app` - Imagen con Python 3.11 + Node.js 20
  - Instala dependencias de `requirements.txt`
  - Instala dependencias de `web/package.json`
  - ENTRYPOINT: `python main.py`
- [x] `docker/docker-compose.yml` - Servicio `app` con variables de entorno
  - Monta el repositorio en `/app`
  - Expone puerto 3000
  - Declara variables para Supabase

**PENDIENTE:**
- [ ] Probar que el contenedor construye correctamente
  ```bash
  docker compose -f docker/docker-compose.yml build
  ```
- [ ] Probar que el contenedor ejecuta `main.py` sin errores
  ```bash
  docker compose -f docker/docker-compose.yml up
  ```
- [ ] Verificar que el sitio web Next.js es accesible en el contenedor
- [ ] Documentar en README cómo ejecutar todo el proyecto con Docker

---

## 📝 Archivos de soporte creados

Adicionales no requeridos pero útiles:
- [x] `.gitignore` - Ignora archivos generados, secrets, node_modules
- [x] `requirements.txt` - Dependencias de Python
- [x] `.env.example` - Plantilla de variables de entorno
- [x] `README.md` - Instrucciones de uso del proyecto
- [x] `check_data.py` - Script para verificar datos cargados en Supabase
- [x] Scripts de carga alternativos (API REST en lugar de PostgreSQL directo)

---

## 🎯 Resumen de estado general

| Punto | Descripción | Estado |
|-------|-------------|--------|
| 0 | Diagrama BD + schema.sql | ⚠️ Falta diagrama visual |
| 1 | ETL Infraestructura | ✅ Completo |
| 2 | ETL Metadata | ✅ Completo |
| 3 | ETL Amenazas | ✅ Completo |
| 4 | Schemas JSON documentados | ✅ Completo |
| 6 | Loaders SQL | ✅ Completo |
| 7 | Sitio Web Leaflet | ✅ Completo |
| 8 | Ruta pgr_dijkstra | ✅ Completo |
| 9 | main.py orquestador | ✅ Completo |
| 10 | Docker | ⚠️ Archivos creados, falta probar |

**Progreso: 8/10 puntos completos (80%)**

---

## 🚀 Próximos pasos prioritarios

### Críticos para completar la Fase 2:

1. **Crear diagrama de la base de datos** (`sql/diagram.png`)
   - Usar herramienta online como dbdiagram.io
   - Mostrar tablas, relaciones, tipos de datos

2. **Probar contenedores Docker**
   - Verificar build
   - Verificar ejecución de ETL
   - Verificar acceso al sitio web

3. **Documentar ejecución Docker** en README
   - Instrucciones paso a paso
   - Variables de entorno necesarias
   - Comandos de build y run

### Opcionales para mejorar el proyecto:

4. **Optimizar carga de infraestructura en el mapa**
   - La red vial tiene 138K aristas, muy pesado para cargar todas
   - Implementar viewport-based loading (solo aristas visibles)
   - O usar tiles vectoriales

5. **Agregar marcadores de origen/destino en el mapa**
   - Permitir seleccionar nodos haciendo click en el mapa
   - Mostrar coordenadas de los nodos seleccionados

6. **Implementar búsqueda de nodos más cercanos**
   - Dado un click en el mapa, encontrar el nodo más cercano
   - Usar PostGIS ST_Distance o KNN

7. **Agregar métricas de la ruta**
   - Distancia total
   - Costo total
   - Tipos de vías utilizadas
   - Zonas de riesgo atravesadas

---

## 📊 Datos actuales en Supabase

- Nodos: 602,652
- Aristas: 138,905
- Elevación: 3 puntos
- Lluvia: 2 puntos
- Landcover: 2 registros
- DGA: 2 estaciones
- Inundaciones: 1 zona
- Reportes: 2 reportes

**Base de datos lista para pruebas de ruteo.**

---

## 🔗 Enlaces útiles

- Repositorio GitHub: https://github.com/felipearosr/ruteo
- Dashboard Supabase: https://supabase.com/dashboard/project/eqjzlgbjgwbnvqzbomsn
- SQL Editor: https://supabase.com/dashboard/project/eqjzlgbjgwbnvqzbomsn/sql/new

---

**Última actualización:** 2025-01-17 - Web completa implementada con visualización de capas y routing con pgr_dijkstra
