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

**Diagrama de Base de Datos:**

Ver el diagrama completo del esquema en [`sql/diagram.svg`](sql/diagram.svg) (también disponible como [`diagram.png`](sql/diagram.png))

El diagrama muestra:
- Tablas de infraestructura: `infra_nodos`, `infra_aristas`
- Tablas de metadata: `meta_elevacion`, `meta_lluvia`, `meta_landcover`
- Tablas de amenazas: `amenaza_dga`, `amenaza_inundaciones_hist`, `amenaza_reportes_ciudadanos`
- Tipos de datos geoespaciales (GEOGRAPHY)
- Índices GIST para consultas espaciales eficientes

**Stack tecnológico:**

- **Backend:** Supabase (PostgreSQL + PostGIS + pgRouting)
- **ETL:** Python 3.11 con requests, geojson, shapely
- **Web Frontend:** Next.js 14, React 18, TypeScript
- **Mapa:** Leaflet 1.9.4 con react-leaflet
- **Estilos:** Tailwind CSS 3.3
- **Ruteo:** pgRouting (pgr_dijkstra) con algoritmo de Dijkstra
- **Datos:** OpenStreetMap (Overpass API) para infraestructura vial

## Ejecutar con Docker

Docker permite ejecutar todo el proyecto (ETL + servidor web) en un contenedor aislado.

### Requisitos previos

- Docker Engine 20.10+ instalado
- Docker Compose v2 instalado

### Pasos para ejecutar con Docker:

1. **Configurar variables de entorno:**

   Las variables de entorno se pueden configurar de dos formas:

   **Opción A:** Crear archivo `.env` en la raíz (recomendado)
   ```zsh
   cp .env.docker.example .env
   # Edita .env con tus credenciales de Supabase
   ```

   **Opción B:** Exportar variables en el shell
   ```zsh
   export SUPABASE_URL='https://tu-proyecto.supabase.co'
   export SUPABASE_ANON_KEY='tu_anon_key'
   export SUPABASE_DB_HOST='db.tu-proyecto.supabase.co'
   export SUPABASE_DB_PORT='6543'
   export SUPABASE_DB_USER='postgres.tu-proyecto'
   export SUPABASE_DB_PASSWORD='tu_password'
   ```

2. **Construir la imagen Docker:**

   ```zsh
   docker compose -f docker/docker-compose.yml build
   ```

   Esto creará una imagen con:
   - Python 3.11 + todas las dependencias ETL
   - Node.js 20 + dependencias de Next.js
   - Scripts de inicio automático

3. **Ejecutar el contenedor:**

   ```zsh
   docker compose -f docker/docker-compose.yml up
   ```

   El contenedor ejecutará automáticamente:
   1. **ETL:** Genera archivos JSON/GeoJSON (puede tardar si descarga datos de OSM)
   2. **Servidor web:** Inicia Next.js en http://localhost:3000

4. **Acceder a la aplicación:**

   Abre tu navegador en: http://localhost:3000

5. **Detener el contenedor:**

   ```zsh
   # Presiona Ctrl+C en la terminal donde está corriendo

   # O en otra terminal:
   docker compose -f docker/docker-compose.yml down
   ```

### Modo desarrollo con Docker

Si quieres modificar código y ver los cambios reflejados sin reconstruir:

```zsh
# El docker-compose.yml ya monta el código local en el contenedor
docker compose -f docker/docker-compose.yml up
```

Los cambios en archivos Python se reflejarán al reiniciar el contenedor.
Los cambios en archivos de Next.js se recargarán automáticamente (hot reload).

### Troubleshooting Docker

**Error: "Variables de entorno no configuradas"**
- Asegúrate de tener un archivo `.env` en la raíz del proyecto
- O exporta las variables antes de ejecutar `docker compose`

**Error: "504 Gateway Timeout" en ETL de OSM**
- La API de Overpass puede estar sobrecargada
- Esto es normal, el servidor web iniciará de todas formas
- Los datos de OSM ya están en el repositorio como archivos .geojson

**El puerto 3000 ya está en uso**
- Detén cualquier servidor Next.js local: `pkill -f "next dev"`
- O modifica el puerto en `docker-compose.yml`: `"3001:3000"`

Ver `copilot-instructions.md` para el resto de la especificación del proyecto.

