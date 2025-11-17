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

6. Iniciar el servidor web Next.js:

   ```zsh
   cd web
   npm install
   npm run dev
   ```

   El sitio estará disponible en http://localhost:3000

## Ejecutar con Docker

Alternativamente, puedes usar Docker:

```zsh
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

Ver `copilot-instructions.md` para el resto de la especificación del proyecto.

