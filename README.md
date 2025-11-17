# Ruteo resiliente ante inundaciones urbanas — Fase 2

Repositorio que contiene scripts ETL, esquemas SQL y un sitio básico Next.js para visualizar
infraestructura, metadata y amenazas. Está preparado para ejecutarse en Docker y para conectar
con una instancia Supabase (Postgres + PostGIS + pgRouting).

Instrucciones rápidas:

1. Exporta las variables de entorno de Supabase necesarias (no subir credenciales al repo):

	- SUPABASE_URL
	- SUPABASE_DB_HOST
	- SUPABASE_DB_NAME
	- SUPABASE_DB_USER
	- SUPABASE_DB_PASSWORD

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
