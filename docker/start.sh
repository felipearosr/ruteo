#!/bin/bash
set -e

echo "=== Ruteo Resiliente - Docker Container ==="
echo ""

# Chequeo liviano de CPLEX/docplex para informar estado en tiempo de arranque
echo "=== Verificando CPLEX/docplex ==="
python - <<'PY' || true
import os
import pathlib

root = os.getenv("CPLEX_STUDIO_DIR2211")
license_file = os.getenv("ILOG_LICENSE_FILE")
print(f"CPLEX_STUDIO_DIR2211: {root or 'no configurado'}")
if root:
    print(f"  - Ruta existe: {pathlib.Path(root).exists()}")
print(f"ILOG_LICENSE_FILE: {license_file or 'no configurado'}")
if license_file:
    print(f"  - Licencia existe: {pathlib.Path(license_file).exists()}")

try:
    from docplex.mp.model import Model  # type: ignore
    print("docplex: OK (import exitoso)")
except Exception as e:
    print(f"docplex: NO DISPONIBLE ({e})")
PY
echo ""

# Verificar si existen las variables de entorno necesarias
if [ -z "$SUPABASE_DB_HOST" ]; then
    echo "⚠️  ADVERTENCIA: Variables de entorno de Supabase no configuradas"
    echo "   Los ETL no podrán cargar datos a la base de datos"
    echo ""
fi

echo "=== Ejecutando ETL (main.py) ==="
echo "Generando archivos JSON/GeoJSON de infraestructura, metadata y amenazas..."
echo ""

cd /app
python main.py || echo "⚠️  ETL completado con errores o sin conexión a APIs externas"

echo ""
echo "=== ETL completado ==="
echo ""
echo "=== Iniciando servidor Next.js en modo desarrollo ==="
echo "El sitio web estará disponible en http://localhost:3000"
echo ""

cd /app/web
exec npm run dev
