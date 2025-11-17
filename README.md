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

2. Construir y levantar el contenedor (desde la carpeta `docker/`):

```zsh
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
```

3. Para ejecutar localmente los ETL sin Docker:

```zsh
python infraestructura/osm_infra_etl.py
python metadata/elevacion_etl.py
python metadata/lluvia_etl.py
python metadata/landcover_etl.py
python amenazas/dga_etl.py
python amenazas/inundaciones_hist_etl.py
python amenazas/reportes_ciudadanos_etl.py
```

4. Cargar los archivos JSON/GeoJSON a la base de datos Supabase usando los archivos `sql/*.sql` y
	los loaders en `infraestructura/` y `metadata/`.

Ver `copilot-instructions.md` para el resto de la especificación del proyecto.
