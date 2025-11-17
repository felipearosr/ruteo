"""
Script para actualizar las probabilidades de falla en la base de datos

Este script debe ejecutarse después de cargar los datos de amenazas y metadata
para calcular las probabilidades de falla de nodos y aristas.

Uso:
    python model/actualizar_probabilidades.py
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar el calculador
from probabilidad_fallo import ProbabilidadFalloCalculator


def main():
    print("=" * 60)
    print("ACTUALIZACIÓN DE PROBABILIDADES DE FALLA")
    print("=" * 60)
    print()
    
    # Verificar variables de entorno
    required_vars = [
        'SUPABASE_DB_HOST',
        'SUPABASE_DB_PORT',
        'SUPABASE_DB_USER',
        'SUPABASE_DB_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Error: Faltan variables de entorno: {', '.join(missing_vars)}")
        print("   Asegúrate de tener un archivo .env con las credenciales de Supabase")
        sys.exit(1)
    
    print("✅ Variables de entorno verificadas")
    print()
    
    # Crear calculador y ejecutar
    calculator = ProbabilidadFalloCalculator()
    
    try:
        calculator.actualizar_todas_probabilidades(batch_size=1000)
        print()
        print("=" * 60)
        print("✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR AL ACTUALIZAR PROBABILIDADES")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
