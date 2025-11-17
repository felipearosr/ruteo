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

## ⚠️ 7. Carpeta Sitio Web con Leaflet

**Estado:** PARCIALMENTE COMPLETADO

Archivos existentes:
- [x] `web/package.json` - Dependencias de Next.js, React, Leaflet, Supabase
- [x] `web/src/app/page.tsx` - Página principal con mapa de Leaflet (STUB)
- [x] `web/src/app/api/route/index.ts` - Endpoint API para rutas (STUB)
- [x] `web/next.config.mjs` - Configuración de Next.js
- [x] `web/tailwind.config.ts` - Configuración de Tailwind CSS

**PENDIENTE:**
- [ ] Completar `page.tsx` para cargar y visualizar infraestructura desde Supabase
- [ ] Completar `page.tsx` para mostrar capas de metadata (elevación, lluvia, landcover)
- [ ] Completar `page.tsx` para mostrar capas de amenazas (DGA, inundaciones, reportes)
- [ ] Agregar controles de capas (checkboxes) para activar/desactivar visualizaciones
- [ ] Configurar variables de entorno para el cliente web (`.env.local`)

---

## ⚠️ 8. Ruta con pgr_dijkstra

**Estado:** STUB CREADO

- [x] Endpoint API creado en `web/src/app/api/route/index.ts` (retorna datos de ejemplo)
- [ ] **PENDIENTE:** Implementar consulta real a Supabase con `pgr_dijkstra`
  - Conectar al backend de Supabase usando credenciales
  - Ejecutar consulta SQL con `pgr_dijkstra` usando `length_m` como costo
  - Seleccionar nodos origen/destino representativos del problema
  - Devolver GeoJSON con la geometría de la ruta calculada
- [ ] **PENDIENTE:** Mostrar la ruta en el mapa de Leaflet
  - Dibujar polilínea con la ruta
  - Marcar origen y destino
  - Mostrar información de la ruta (distancia, número de segmentos)

**Ejemplo de consulta SQL a implementar:**
```sql
SELECT 
  a.geom,
  a.length_m,
  r.seq,
  r.node,
  r.edge,
  r.cost
FROM pgr_dijkstra(
  'SELECT id, source, target, cost FROM infra_aristas WHERE cost IS NOT NULL',
  <source_node_id>,
  <target_node_id>,
  directed := false
) r
JOIN infra_aristas a ON r.edge = a.id
ORDER BY r.seq;
```

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
| 7 | Sitio Web Leaflet | ⚠️ Stub creado, falta implementación |
| 8 | Ruta pgr_dijkstra | ⚠️ API stub, falta implementación real |
| 9 | main.py orquestador | ✅ Completo |
| 10 | Docker | ⚠️ Archivos creados, falta probar |

---

## 🚀 Próximos pasos prioritarios

### Críticos para completar la Fase 2:

1. **Crear diagrama de la base de datos** (`sql/diagram.png`)
   - Usar herramienta online como dbdiagram.io
   - Mostrar tablas, relaciones, tipos de datos

2. **Implementar visualización web completa** (`web/src/app/page.tsx`)
   - Cargar infraestructura desde Supabase
   - Mostrar capas de metadata y amenazas
   - Agregar controles de capas

3. **Implementar endpoint de ruteo real** (`web/src/app/api/route/index.ts`)
   - Conectar a Supabase
   - Ejecutar consulta con `pgr_dijkstra`
   - Devolver GeoJSON de la ruta

4. **Mostrar ruta en el mapa**
   - Dibujar polilínea en Leaflet
   - Agregar marcadores de origen/destino
   - Mostrar información de la ruta

5. **Probar contenedores Docker**
   - Verificar build
   - Verificar ejecución de ETL
   - Verificar acceso al sitio web

6. **Documentar ejecución Docker** en README
   - Instrucciones paso a paso
   - Variables de entorno necesarias
   - Comandos de build y run

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

**Última actualización:** 2025-11-17
