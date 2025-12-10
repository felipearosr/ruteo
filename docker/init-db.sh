#!/bin/bash
# Script para inicializar la base de datos local
# Uso: ./init-db.sh

set -e

echo "=== Inicializando base de datos local ==="

# Esperar a que la base de datos este lista
echo "Esperando a que PostgreSQL este listo..."
until docker exec ruteo_db pg_isready -U postgres -d ruteo > /dev/null 2>&1; do
    sleep 2
done
echo "PostgreSQL listo!"

# Instalar pgRouting
echo "Instalando pgRouting..."
docker exec ruteo_db bash -c "apt-get update && apt-get install -y postgresql-17-pgrouting" > /dev/null 2>&1
echo "pgRouting instalado!"

# Restaurar datos
echo "Restaurando datos desde backup..."
docker exec ruteo_db pg_restore -U postgres -d ruteo --no-owner --no-acl --clean --if-exists /backup.dump 2>/dev/null || true
echo "Datos restaurados!"

# Habilitar pgRouting
echo "Habilitando extension pgrouting..."
docker exec ruteo_db psql -U postgres -d ruteo -c "CREATE EXTENSION IF NOT EXISTS pgrouting;" 2>/dev/null || true

# Copiar probabilidades de fallo a tablas cleaned (necesario para simulacion)
echo "Sincronizando probabilidades de fallo a tablas cleaned..."
docker exec ruteo_db psql -U postgres -d ruteo -c "
UPDATE infra_nodos_cleaned nc
SET p_fallo_nodo = (
  SELECT n.p_fallo_nodo
  FROM infra_nodos n
  WHERE ST_DWithin(nc.geom, n.geom, 0.0001)
  ORDER BY ST_Distance(nc.geom, n.geom)
  LIMIT 1
)
WHERE EXISTS (
  SELECT 1 FROM infra_nodos n
  WHERE ST_DWithin(nc.geom, n.geom, 0.0001)
);
" 2>/dev/null || true
echo "Nodos sincronizados!"

docker exec ruteo_db psql -U postgres -d ruteo -c "
UPDATE infra_aristas_cleaned ac
SET p_fallo_arista = (
  SELECT a.p_fallo_arista
  FROM infra_aristas a
  WHERE ST_DWithin(ST_Centroid(ac.geom), ST_Centroid(a.geom), 0.0001)
  ORDER BY ST_Distance(ST_Centroid(ac.geom), ST_Centroid(a.geom))
  LIMIT 1
)
WHERE EXISTS (
  SELECT 1 FROM infra_aristas a
  WHERE ST_DWithin(ST_Centroid(ac.geom), ST_Centroid(a.geom), 0.0001)
);
" 2>/dev/null || true
echo "Aristas sincronizadas!"

# Verificar
echo ""
echo "=== Verificacion ==="
docker exec ruteo_db psql -U postgres -d ruteo -c "SELECT 'infra_nodos' as tabla, COUNT(*) as registros FROM infra_nodos UNION ALL SELECT 'infra_aristas', COUNT(*) FROM infra_aristas UNION ALL SELECT 'infra_aristas_cleaned', COUNT(*) FROM infra_aristas_cleaned;"

echo ""
echo "=== Base de datos inicializada correctamente ==="
echo "La aplicacion web esta disponible en: http://localhost:3000"
