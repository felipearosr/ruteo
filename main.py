"""
Orquestador principal del proyecto (ETL completo).

Este script ejecuta todos los scripts ETL en el orden especificado por copilot-instructions.md:
  1. Infraestructura
  2. Metadata (elevacion, lluvia, landcover)
  3. Amenazas (dga, inundaciones_hist, reportes_ciudadanos)

Después de ejecutar los ETL, muestra instrucciones para cargar los datos a Supabase usando los
archivos SQL de loader.

Uso:
  python main.py
"""
import os
import subprocess
import sys


def run_script(script_path):
    """Ejecuta un script Python y reporta el resultado."""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script_path}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode != 0:
        print(f"ERROR: El script {script_path} falló con código {result.returncode}")
        sys.exit(1)
    print(f"OK: {script_path} completado exitosamente.\n")


def main():
    print("Iniciando proceso ETL completo...")
    
    # Paso 1: Infraestructura
    run_script('infraestructura/osm_infra_etl.py')
    
    # Paso 2: Metadata
    run_script('metadata/elevacion_etl.py')
    run_script('metadata/lluvia_etl.py')
    run_script('metadata/landcover_etl.py')
    
    # Paso 3: Amenazas
    run_script('amenazas/dga_etl.py')
    run_script('amenazas/inundaciones_hist_etl.py')
    run_script('amenazas/reportes_ciudadanos_etl.py')
    
    print("\n" + "="*60)
    print("ETL completo finalizado con éxito.")
    print("="*60)
    print("\nPróximos pasos:")
    print("  1. Asegúrate de tener configuradas las variables de entorno para Supabase:")
    print("     - SUPABASE_DB_HOST")
    print("     - SUPABASE_DB_NAME")
    print("     - SUPABASE_DB_USER")
    print("     - SUPABASE_DB_PASSWORD")
    print("\n  2. Ejecuta el esquema SQL principal en Supabase:")
    print("     psql -h $SUPABASE_DB_HOST -U $SUPABASE_DB_USER -d $SUPABASE_DB_NAME -f sql/schema.sql")
    print("\n  3. Carga los datos generados usando los loaders SQL:")
    print("     - infraestructura/load_infra.sql")
    print("     - metadata/load_elevacion.sql, load_lluvia.sql, load_landcover.sql")
    print("     - amenazas/load_dga.sql, load_inundaciones_hist.sql, load_reportes_ciudadanos.sql")
    print("\n  4. Para iniciar el servidor Next.js:")
    print("     cd web && npm install && npm run dev")
    print("\n¡Todo listo!")


if __name__ == '__main__':
    main()
