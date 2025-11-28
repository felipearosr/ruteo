# Configuración de CPLEX (docplex) para Fase 3

Ruta local informada: `/home/faros/CPLEX_Studio2211`

## 1) Variables de entorno (sesión local o shell)
Exporta antes de correr scripts Python o Next.js:

```bash
export CPLEX_STUDIO_DIR2211=/home/faros/CPLEX_Studio2211
export PATH=$CPLEX_STUDIO_DIR2211/cplex/bin/x86-64_linux:$PATH
export LD_LIBRARY_PATH=$CPLEX_STUDIO_DIR2211/cplex/bin/x86-64_linux:$CPLEX_STUDIO_DIR2211/cplex/lib/x86-64_linux:${LD_LIBRARY_PATH:-}
export ILOG_LICENSE_FILE=/home/faros/CPLEX_Studio2211/licenses/access.ilm
```

`docplex` ya está en `requirements.txt`; instala dependencias con `pip install -r requirements.txt`.

### Ajustes de rendimiento (CPU)
- Hilos: `export CPLEX_THREADS=$(nproc)` para usar todos los núcleos (o fija un entero).
- Paralelismo: `export CPLEX_PARALLEL=1` (oportunista, más rápido) o `2` (determinista/reproducible). `0` deja que CPLEX decida.
- Gap: `export CPLEX_MIPGAP=0.1` (10% por defecto actual) si quieres soluciones buenas rápido; baja el número para más precisión.

## 2) Prueba rápida en local
```bash
python - <<'PY'
import os, pathlib
from docplex.mp.model import Model
print("CPLEX_STUDIO_DIR2211", os.getenv("CPLEX_STUDIO_DIR2211"))
print("ILOG_LICENSE_FILE", os.getenv("ILOG_LICENSE_FILE"))
print("Dir existe:", pathlib.Path(os.getenv("CPLEX_STUDIO_DIR2211", "")).exists())
print("Lic existe:", pathlib.Path(os.getenv("ILOG_LICENSE_FILE", "")).exists())
Model(name="probe")  # debe crear modelo sin lanzar excepción
print("OK: docplex funcional")
PY

# Luego, prueba el router
python optimization/cplex_router_api.py --source 1 --target 2
```

## 3) Docker (usa tu instalación montada)
En `docker/docker-compose.yml` ya se montan rutas por defecto apuntando a `/home/faros/CPLEX_Studio2211`:
- `CPLEX_HOST_DIR` → `/opt/ibm/ILOG/CPLEX_Studio2211` (en el contenedor)
- `CPLEX_LICENSE_FILE` → `/licenses/ilm.lic` (en el contenedor)

Si tus rutas son las dadas, no necesitas cambiar nada. Si cambian, ajusta variables en tu `.env` o en el comando `docker compose`:
```bash
export CPLEX_HOST_DIR=/home/faros/CPLEX_Studio2211
export CPLEX_LICENSE_FILE=/home/faros/CPLEX_Studio2211/licenses/access.ilm
docker compose -f docker/docker-compose.yml up
```

El contenedor ahora imprime un chequeo de CPLEX/docplex al inicio (`docker/start.sh`) para confirmar que paths y licencia son visibles.
