# Ruteo resiliente ante inundaciones urbanas — Fase 2

Repositorio que contiene scripts ETL, esquemas SQL y un sitio básico Next.js para visualizar
infraestructura, metadata y amenazas. Está preparado para ejecutarse en Docker y para conectar
con una instancia Supabase (Postgres + PostGIS + pgRouting).

Instrucciones rápidas:

1. Configurar credenciales de Supabase:

   Copia el archivo `.env.example` a `.env` y completa con tus credenciales reales:

   ```zsh
   cp .env.example .env
   # Edita .env con tu editor favorito y completa las variables
   ```

   El archivo `.env` debe contener:
   - `SUPABASE_URL` — URL de tu proyecto Supabase
   - `SUPABASE_DB_HOST` — Host de la base de datos (ej: db.tu-proyecto.supabase.co)
   - `SUPABASE_DB_NAME` — Nombre de la BD (generalmente `postgres`)
   - `SUPABASE_DB_USER` — Usuario de la BD (generalmente `postgres`)
   - `SUPABASE_DB_PASSWORD` — Contraseña de la BD

   Alternativamente, exporta las variables en tu shell:

   ```zsh
   export SUPABASE_URL='https://tu-proyecto.supabase.co'
   export SUPABASE_DB_HOST='db.tu-proyecto.supabase.co'
   export SUPABASE_DB_NAME='postgres'
   export SUPABASE_DB_USER='postgres'
   export SUPABASE_DB_PASSWORD='tu-password'
   ```

2. Instalar dependencias de Python:

   ```zsh
   pip install -r requirements.txt
   ```

3. Crear el esquema de la base de datos en Supabase:

   **Opción A:** Usando psql (línea de comandos):
   ```zsh
   psql "postgresql://postgres:TU_PASSWORD@db.tu-proyecto.supabase.co:5432/postgres" -f sql/schema.sql
   ```

   **Opción B:** Desde el dashboard de Supabase:
   - Ve a **SQL Editor** en tu proyecto
   - Copia y pega el contenido de `sql/schema.sql`
   - Click en **Run**

4. Ejecutar los ETL para generar los datos:

   ```zsh
   python main.py
   ```

   Esto generará archivos JSON/GeoJSON en las carpetas `infraestructura/`, `metadata/` y `amenazas/`.

5. Cargar los datos a Supabase:

   ```zsh
   python load_to_supabase.py
   ```

   Este script carga automáticamente todos los archivos JSON/GeoJSON generados a las tablas de Supabase.

6. Configurar variables de entorno para la aplicación web:

   Copia el archivo de ejemplo en la carpeta `web/`:

   ```zsh
   cd web
   cp .env.local.example .env.local
   # Edita .env.local con tus credenciales de Supabase
   ```

   El archivo `.env.local` debe contener:
   - `NEXT_PUBLIC_SUPABASE_URL` — URL pública de Supabase (para el cliente)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Clave anónima de Supabase (para el cliente)
   - `SUPABASE_DB_HOST` — Host de la BD (para las API routes)
   - `SUPABASE_DB_PORT` — Puerto del pooler (6543)
   - `SUPABASE_DB_USER` — Usuario de la BD
   - `SUPABASE_DB_PASSWORD` — Contraseña de la BD

7. Iniciar el servidor web Next.js:

   ```zsh
   cd web  # si no estás ya en la carpeta web
   npm install
   npm run dev
   ```

   El sitio estará disponible en http://localhost:3000

## Funcionalidades de la aplicación web

La aplicación web implementada incluye:

- **Mapa interactivo** con OpenStreetMap centrado en Santiago, Chile
- **Capas de metadata:**
  - Elevación (puntos verdes)
  - Precipitación/Lluvia (puntos cyan)
  - Cobertura de suelo (puntos amarillos)
- **Capas de amenazas:**
  - Estaciones DGA (puntos azul oscuro)
  - Inundaciones históricas (puntos rojos)
  - Reportes ciudadanos (puntos naranjas)
- **Cálculo de rutas:**
  - Selección de nodos origen y destino
  - Botón para calcular ruta usando pgr_dijkstra
  - Visualización de la ruta calculada como línea azul en el mapa
  - Información de segmentos de la ruta
- **Controles de capas:**
  - Checkboxes para activar/desactivar cada capa
  - Popups informativos al hacer click en los marcadores

## Arquitectura técnica

- **Backend:** Supabase (PostgreSQL + PostGIS + pgRouting)
- **ETL:** Python 3.11 con requests, geojson, shapely
- **Web Frontend:** Next.js 14, React 18, TypeScript
- **Mapa:** Leaflet 1.9.4 con react-leaflet
- **Estilos:** Tailwind CSS 3.3
- **Ruteo:** pgRouting (pgr_dijkstra) con algoritmo de Dijkstra
- **Datos:** OpenStreetMap (Overpass API) para infraestructura vial

## Ejecutar con Docker

Alternativamente, puedes usar Docker:

```zsh
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

Ver `copilot-instructions.md` para el resto de la especificación del proyecto.

