# Instalación de GUROBI para Fase 3

## ¿Qué es GUROBI?

GUROBI es un solver de optimización comercial de alto rendimiento para programación lineal (LP), programación lineal entera mixta (MILP), programación cuadrática (QP) y más. En este proyecto lo usamos para resolver el problema de ruteo resiliente como un modelo MILP.

---

## 📦 Opciones de Instalación

### Opción 1: Licencia Académica Gratuita (Recomendada)

GUROBI ofrece licencias académicas gratuitas para estudiantes, profesores e investigadores.

#### Requisitos

- Email institucional (.edu, .ac.uk, etc.)
- Ser estudiante o profesor universitario

#### Pasos

1. **Registrarse en GUROBI:**
   - Visitar https://www.gurobi.com/academia/academic-program-and-licenses/
   - Click en "Request Free Academic License"
   - Crear cuenta con email institucional

2. **Instalar GUROBI:**

   ```bash
   # Con pip
   pip install gurobipy
   ```

3. **Obtener licencia académica:**
   - Iniciar sesión en https://portal.gurobi.com/
   - Click en "Licenses" → "Request Academic License"
   - Copiar el comando de activación (ejemplo):
     ```bash
     grbgetkey abc12345-6789-def0-1234-56789abcdef0
     ```
   - Ejecutar el comando en terminal
   - La licencia se guardará en `~/gurobi.lic` (Linux/Mac) o `C:\gurobi\gurobi.lic` (Windows)

4. **Verificar instalación:**

   ```bash
   python -c "import gurobipy as gp; print(gp.gurobi.version())"
   # Debería mostrar: (11, 0, 0)
   ```

---

### Opción 2: Licencia de Prueba Gratuita (30 días)

Si no tienes email académico, puedes usar una licencia de evaluación.

#### Pasos

1. Registrarse en https://www.gurobi.com/downloads/
2. Descargar GUROBI Optimizer (incluye licencia de 30 días)
3. Instalar siguiendo las instrucciones del instalador
4. La licencia de prueba se activa automáticamente

---

### Opción 3: Versión Comunitaria (Limitada)

GUROBI ofrece una versión gratuita con límites de tamaño de problema.

**Límites:**
- Variables: 2,000
- Restricciones: 2,000

**Para nuestro proyecto:** Puede ser insuficiente para grafos grandes (>2,000 aristas).

#### Instalación

```bash
pip install gurobipy
# No requiere licencia adicional para problemas pequeños
```

---

## 🐳 Configuración en Docker

### Opción A: Licencia Local (Bind Mount)

Si ya tienes la licencia en tu máquina local:

```dockerfile
# En Dockerfile.app
COPY gurobi.lic /opt/gurobi/gurobi.lic
ENV GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic
```

```yaml
# En docker-compose.yml
volumes:
  - ./gurobi.lic:/opt/gurobi/gurobi.lic:ro
environment:
  - GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic
```

### Opción B: Licencia Cloud (Académica)

GUROBI académico permite licencias cloud que funcionan sin archivo local:

```yaml
# En docker-compose.yml
environment:
  - GRB_LICENSEID=your_license_id
  - GUROBI_HOME=/usr/local/lib/python3.11/site-packages/gurobipy
```

### Opción C: Sin GUROBI (Desarrollo)

Si no tienes licencia, el sistema puede funcionar sin GUROBI (se omitirá la Ruta 2):

```yaml
# En docker-compose.yml
environment:
  - USE_GUROBI=false
```

---

## 🧪 Probar la Instalación

### Test Básico

```python
import gurobipy as gp
from gurobipy import GRB

# Crear modelo simple
m = gp.Model("test")

# Variables
x = m.addVar(name="x")
y = m.addVar(name="y")

# Restricciones
m.addConstr(x + 2*y <= 4, "c1")
m.addConstr(x >= 0, "c2")
m.addConstr(y >= 0, "c3")

# Función objetivo
m.setObjective(x + y, GRB.MAXIMIZE)

# Resolver
m.optimize()

# Resultado
if m.status == GRB.OPTIMAL:
    print(f"✅ GUROBI funciona correctamente!")
    print(f"   Solución: x={x.X:.2f}, y={y.X:.2f}")
    print(f"   Objetivo: {m.ObjVal:.2f}")
else:
    print(f"❌ Error: status = {m.status}")
```

### Test del Proyecto

```bash
cd /home/faros/ruteo
python optimization/gurobi_model.py
```

---

## 🔧 Solución de Problemas

### Error: "No se encuentra la licencia"

```
GurobiError: No license for Gurobi found
```

**Solución:**
1. Verificar que existe `~/gurobi.lic` (Linux/Mac)
2. Si no existe, ejecutar `grbgetkey` con tu código de licencia
3. Verificar variable de entorno:
   ```bash
   echo $GRB_LICENSE_FILE
   # Debería mostrar: /home/usuario/gurobi.lic
   ```

### Error: "Licencia expirada"

```
GurobiError: License has expired
```

**Solución:**
- Licencia académica: Renovar cada año en el portal
- Licencia de prueba: Expiró después de 30 días
- Solicitar nueva licencia

### Error: "Modelo demasiado grande"

```
GurobiError: Model too large for size-limited license
```

**Solución:**
- Estás usando versión comunitaria con límites
- Opciones:
  1. Reducir área de búsqueda (bbox más pequeño)
  2. Obtener licencia académica completa
  3. Usar Dijkstra Resiliente o A* en su lugar

### Error en Docker: "Cannot find license file"

```
GurobiError: Cannot find license file
```

**Solución:**
1. Verificar que el archivo está montado:
   ```bash
   docker compose exec app ls -la /opt/gurobi/
   ```
2. Verificar permisos del archivo:
   ```bash
   chmod 644 gurobi.lic
   ```
3. Verificar variable de entorno en contenedor:
   ```bash
   docker compose exec app env | grep GRB
   ```

---

## 📚 Recursos Adicionales

- **Documentación oficial:** https://www.gurobi.com/documentation/
- **Python API:** https://www.gurobi.com/documentation/current/refman/py_python_api_overview.html
- **Ejemplos:** https://www.gurobi.com/documentation/current/examples/
- **Foro de soporte:** https://support.gurobi.com/hc/
- **Tutoriales académicos:** https://www.gurobi.com/academia/

---

## 💡 Alternativas si No Tienes GUROBI

Si no puedes obtener GUROBI, estas alternativas funcionan:

### 1. PuLP + CBC (Open Source)

```bash
pip install pulp
# CBC viene incluido
```

Reemplazar GUROBI en `gurobi_model.py` con PuLP.

### 2. Google OR-Tools (Open Source)

```bash
pip install ortools
```

Solver gratuito de Google, muy potente.

### 3. Solo Dijkstra Resiliente + A*

Las Rutas 3 y 4 no requieren solver comercial y dan resultados muy buenos.

---

## ⚖️ Comparación de Solvers

| Solver | Licencia | Velocidad | Calidad | Fácil Instalación |
|--------|----------|-----------|---------|-------------------|
| **GUROBI** | Académica gratis / Comercial | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **CPLEX** | Académica gratis / Comercial | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **CBC (PuLP)** | Open Source | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **OR-Tools** | Open Source (Google) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **SCIP** | Academic Free / Comercial | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recomendación para este proyecto:** GUROBI Académico (mejor balance)

---

**Última actualización:** 17 de Noviembre, 2025  
**Autor:** Felipe Aros
