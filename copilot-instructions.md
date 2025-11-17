# Instrucciones de proyecto para Copilot — Fase 2 (Ruteo resiliente inundaciones urbanas)

Contexto:
Este repositorio implementa la Fase 2 de un proyecto universitario sobre ruteo resiliente ante inundaciones urbanas. 
El objetivo es construir el proceso ETL (Extract, Transform, Load), el esquema de base de datos, y un sitio web básico con Leaflet, 
cumpliendo una rúbrica específica. Todo el código debe estar preparado para correr dentro de contenedores Docker.

## Stack técnico

- Base de datos: Supabase (PostgreSQL gestionado) con:
  - Extensión `postgis` para tipos geográficos.
  - Extensión `pgrouting` para algoritmos de ruteo (`pgr_dijkstra` con longitud como costo).
- Lenguajes:
  - Python para scripts ETL (infraestructura, metadata, amenazas).
  - SQL para crear esquema de BD y funciones de carga.
  - TypeScript + Next.js para el sitio web.
  - Tailwind CSS para estilos.
- Todo debe ser compatible con contenedores Docker.

## Reglas generales

- No usar emojis en código, comentarios, commits, ni documentación.
- Idioma por defecto para comentarios, documentación y nombres de archivos: español neutro.
- Mantener funciones pequeñas y claras, separando ETL, carga a BD y front-end.
- Mantener consistencia en nombres:
  - Tablas: `infra_nodos`, `infra_aristas`, `meta_elevacion`, `meta_lluvia`, `meta_landcover`, `amenaza_dga`, etc.
  - Scripts ETL: `*_etl.py`.
  - Cargadores: `load_*.sql`.
- Siempre asumir que la BD es Supabase:
  - No crear contenedor local de Postgres; conectar vía URL/KEY usando variables de entorno.

## Estructura de repositorio esperada

Cuando te pida crear o modificar archivos, respeta y usa esta estructura:

- `sql/schema.sql`:
  - Crear extensiones `postgis` y `pgrouting` si no existen.
  - Crear tablas de nodos y aristas de infraestructura.
  - Crear tablas para metadata (elevación, lluvia, landcover).
  - Crear tablas para amenazas (estaciones DGA, inundaciones históricas, reportes ciudadanos).
  - Incluir índices geoespaciales donde corresponda (`GIST` sobre geometrías).

- `infraestructura/osm_infra_etl.py`:
  - Script Python que:
    - Extrae red vial desde Overpass API para el bounding box definido.
    - Normaliza nodos (id, lat, lon) y aristas (id, source, target, longitud, tipo de vía).
    - Exporta un archivo `infraestructura/infraestructura.json` o `infraestructura/infraestructura.geojson`.
  - No realizar la carga a la BD aquí, solo generación del JSON/GeoJSON.

- `infraestructura/infra_schema.md`:
  - Explicar la estructura del JSON/GeoJSON generado:
    - Campos de nodos.
    - Campos de aristas.
    - Ejemplo de registro.

- `infraestructura/load_infra.sql`:
  - SQL que, a partir de un JSON/GeoJSON importado a una tabla staging o usando `jsonb_populate_record`, inserte datos en `infra_nodos` e `infra_aristas`.
  - Asumir que el JSON será cargado mediante herramientas como `psql` o funciones de Supabase.

- Carpeta `metadata/`:
  - Tres scripts ETL:
    - `elevacion_etl.py` → `metadata/elevacion.json`
    - `lluvia_etl.py` → `metadata/lluvia.json`
    - `landcover_etl.py` → `metadata/landcover.json`
  - Cada script:
    - Extrae datos de una API/BD definida.
    - Transforma a un JSON normalizado alineado con el esquema de la BD.
  - Cada JSON debe tener su documentación:
    - `elevacion_schema.md`, `lluvia_schema.md`, `landcover_schema.md`.
  - Cada JSON debe tener su loader SQL:
    - `load_elevacion.sql`, `load_lluvia.sql`, `load_landcover.sql`.

- Carpeta `amenazas/`:
  - Tres scripts ETL:
    - `dga_etl.py` → descarga GeoJSON de estaciones DGA, filtra bounding box, genera `dga_estaciones.json`.
    - `inundaciones_hist_etl.py` → genera `inundaciones_hist.json` (zonas de inundación históricas).
    - `reportes_ciudadanos_etl.py` → `reportes_ciudadanos.json` (estructura simulada o basada en Twitter).
  - Documentación: `dga_schema.md`, `inundaciones_hist_schema.md`, `reportes_ciudadanos_schema.md`.
  - Loaders: `load_dga.sql`, `load_inundaciones_hist.sql`, `load_reportes_ciudadanos.sql`.

- Carpeta `web/`:
  - Proyecto Next.js con TypeScript y Tailwind.
  - Usar Leaflet para:
    - Mostrar la infraestructura (red vial).
    - Mostrar capas de metadata.
    - Mostrar amenazas como capas activables (checkboxes).
  - Incluir una ruta calculada con `pgr_dijkstra`:
    - Crear un endpoint API en Next.js (`/api/route`) que:
      - Reciba origen y destino (por ahora se pueden fijar).
      - Llame a Supabase (con `supabase-js` o `pg`/`node-postgres`) y ejecute una consulta SQL que use `pgr_dijkstra` sobre la tabla de aristas.
      - Devuelva los segmentos de la ruta como GeoJSON o lista de coordenadas.
  - En `page.tsx`, mostrar en el mapa:
    - Capas de infraestructura.
    - Capas de metadata y amenazas.
    - La ruta resultante como polilínea.

- `main.py` en la raíz:
  - Orquestar la ejecución completa en este orden:
    1. Ejecutar ETL de infraestructura.
    2. Ejecutar ETL de metadata (los 3 scripts).
    3. Ejecutar ETL de amenazas (los 3 scripts).
    4. Llamar a los loaders SQL para cargar cada JSON/GeoJSON a la BD Supabase.
    5. Opcional: lanzar comandos para inicializar o levantar el servidor de Next.js.
  - Documentar claramente cómo se leen variables de entorno:
    - `SUPABASE_DB_URL`, `SUPABASE_DB_PASSWORD`, etc.

- Carpeta `docker/`:
  - `Dockerfile.app`:
    - Imagen base: una que tenga Python + Node (o instalar ambos).
    - Instalar dependencias de Python (requirements.txt).
    - Instalar dependencias de Node (para Next.js).
    - Definir entrypoints para ejecutar `main.py` y/o `npm run dev` / `npm run start` en `/web`.
  - `docker-compose.yml`:
    - Servicio `app` que ejecute ETL y/o web.
    - Variables de entorno para conectar con Supabase.

## Comportamiento esperado de Copilot

- Cuando el usuario pida:
  - “Genera `sql/schema.sql`”:
    - Crear SQL con `create extension if not exists postgis;` y `create extension if not exists pgrouting;`
    - Crear tablas para infraestructura, metadata y amenazas, con claves primarias y tipos `geometry` donde corresponda.
  - “Genera `infraestructura/osm_infra_etl.py`”:
    - Escribir un script Python que haga:
      - Petición a Overpass API.
      - Parseo de `ways` y `nodes`.
      - Cálculo de longitud usando geodesia simple o directamente la geometría LineString.
      - Guardar un archivo JSON/GeoJSON en disco.
  - “Genera `web/src/app/page.tsx`”:
    - Crear un componente con un mapa de Leaflet centrado en el área de estudio.
    - Cargar infraestructura y mostrarla.
    - Consumir la API interna `/api/route` para pintar la ruta pgr_dijkstra.

- Siempre comentar el código en español, explicando brevemente:
  - Qué hace cada script.
  - Qué formato tiene el JSON que se genera.
  - Cómo se relaciona con las tablas de la BD.

## Estilo y restricciones

- No usar emojis.
- No asumir credenciales; usar variables de entorno.
- Evitar lógica excesivamente compleja:
  - Hacer scripts ETL modulares, con funciones claras.
- Mantener la alineación con la rúbrica de la Fase 2:
  - Todos los puntos 0 al 9 deben estar soportados por archivos reales en el repositorio.
