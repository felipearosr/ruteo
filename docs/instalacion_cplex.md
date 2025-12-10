# Instalación de IBM CPLEX

## ¿Qué es CPLEX?

IBM CPLEX es un solver de optimización de alto rendimiento para programación lineal (LP), programación lineal entera mixta (MILP), programación cuadrática (QP) y más. En este proyecto lo usamos para resolver el problema de ruteo resiliente como un modelo MILP.

---

## Opciones de Instalación

### Opción 1: Licencia Académica Gratuita (Recomendada)

IBM ofrece licencias académicas gratuitas para estudiantes, profesores e investigadores.

#### Requisitos

- Email institucional (.edu, .ac, etc.)
- Ser estudiante o profesor universitario

#### Pasos

1. **Registrarse en IBM Academic Initiative:**
   - Visitar https://www.ibm.com/academic
   - Crear cuenta con email institucional
   - Buscar "CPLEX Optimization Studio"

2. **Descargar CPLEX:**
   - Descargar la versión más reciente (22.1.1 o superior)
   - Disponible para Linux, Mac y Windows

3. **Instalar CPLEX:**

   ```bash
   # Linux
   chmod +x cplex_studio2211.linux_x86_64.bin
   ./cplex_studio2211.linux_x86_64.bin
   # Directorio recomendado: /opt/ibm/ILOG/CPLEX_Studio221

   # Mac
   # Montar el DMG y seguir el instalador

   # Windows
   # Ejecutar el instalador .exe
   ```

4. **Instalar docplex (API Python):**

   ```bash
   pip install docplex
   ```

5. **Verificar instalación:**

   ```bash
   python -c "from docplex.mp.model import Model; print('CPLEX OK')"
   ```

---

### Opción 2: Versión Community (Limitada)

CPLEX ofrece una versión gratuita con límites de tamaño.

**Límites:**
- Variables: 1,000
- Restricciones: 1,000

**Para nuestro proyecto:** Puede ser insuficiente para rutas largas.

#### Instalación

```bash
pip install cplex docplex
```

---

## Configuración de Variables de Entorno

### Linux/Mac

Agregar a `~/.bashrc` o `~/.zshrc`:

```bash
export CPLEX_STUDIO_DIR=/opt/ibm/ILOG/CPLEX_Studio221
export PATH=$CPLEX_STUDIO_DIR/cplex/bin/x86-64_linux:$PATH
export LD_LIBRARY_PATH=$CPLEX_STUDIO_DIR/cplex/bin/x86-64_linux:$LD_LIBRARY_PATH
export PYTHONPATH=$CPLEX_STUDIO_DIR/cplex/python/3.11/x86-64_linux:$PYTHONPATH
```

### Windows

Agregar a las variables de entorno del sistema:
- `CPLEX_STUDIO_DIR`: `C:\Program Files\IBM\ILOG\CPLEX_Studio221`
- Agregar al `PATH`: `%CPLEX_STUDIO_DIR%\cplex\bin\x64_win64`

---

## Probar la Instalación

```python
from docplex.mp.model import Model

# Crear modelo simple
m = Model(name='test')

# Variables
x = m.continuous_var(name='x')
y = m.continuous_var(name='y')

# Restricciones
m.add_constraint(x + 2*y <= 4)
m.add_constraint(x >= 0)
m.add_constraint(y >= 0)

# Función objetivo
m.maximize(x + y)

# Resolver
solution = m.solve()

# Resultado
if solution:
    print(f"CPLEX funciona correctamente!")
    print(f"Solución: x={solution.get_value(x):.2f}, y={solution.get_value(y):.2f}")
    print(f"Objetivo: {solution.objective_value:.2f}")
else:
    print("Error al resolver el modelo")
```

---

## Solución de Problemas

### Error: "CPLEX not found"

1. Verificar que `CPLEX_STUDIO_DIR` está configurado
2. Verificar que docplex está instalado: `pip show docplex`
3. Reiniciar terminal después de configurar variables

### Error: "License not found"

1. Verificar que la licencia académica está activa
2. La licencia se valida online; verificar conexión a internet
3. Contactar soporte IBM si el problema persiste

### Rendimiento Lento

Para redes grandes, configurar timeout:

```python
m.parameters.timelimit = 60  # 60 segundos máximo
m.parameters.mip.tolerances.mipgap = 0.01  # Gap de 1%
```

---

## Alternativas si No Tienes CPLEX

Si no puedes obtener CPLEX, el sistema ofrece alternativas:

1. **Dijkstra Resiliente**: Rápido y efectivo, no requiere solver
2. **A* Resiliente**: Buen balance entre velocidad y calidad
3. **PuLP + CBC**: Solver open source

```bash
pip install pulp
```

---

## Referencias

- [Documentación oficial de CPLEX](https://www.ibm.com/docs/en/icos)
- [API docplex](https://ibmdecisionoptimization.github.io/docplex-doc/)
- [IBM Academic Initiative](https://www.ibm.com/academic)
