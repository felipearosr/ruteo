#!/bin/bash
set -e

echo "=== Ruteo Resiliente - Docker Container ==="
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
