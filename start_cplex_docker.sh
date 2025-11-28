#!/bin/bash
set -euo pipefail

# Configuración y arranque de Docker con CPLEX montado

CPLEX_DIR="${CPLEX_DIR:-/home/faros/CPLEX_Studio2211}"
# Permitir licencia por archivo o por servidor (ILOG_LICENSE_FILE=puerto@host).
user_license="${LICENSE_FILE:-${ILOG_LICENSE_FILE:-}}"
candidate_licenses=(
  "$user_license"
  "$CPLEX_DIR/license/access.ilm"
  "$CPLEX_DIR/licenses/access.ilm"
  "$CPLEX_DIR/access.ilm"
  "$HOME/access.ilm"
)

license_file=""
for candidate in "${candidate_licenses[@]}"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then
    license_file="$candidate"
    break
  fi
done
license_hint="$user_license"

if [ ! -d "$CPLEX_DIR" ]; then
  echo "CPLEX_DIR no existe: $CPLEX_DIR" >&2
  exit 1
fi
license_mode="none"
compose_files=(-f docker/docker-compose.yml)
unset ILOG_LICENSE_FILE
unset CPLEX_LICENSE_FILE

if [ -n "$license_file" ]; then
  license_mode="file"
  export ILOG_LICENSE_FILE="$license_file"
  export CPLEX_LICENSE_FILE="$license_file"
  compose_files+=(-f docker/docker-compose.license.yml)
elif [ -n "$license_hint" ]; then
  license_mode="server"
  export ILOG_LICENSE_FILE="$license_hint"
fi

if [ "$license_mode" = "none" ]; then
  cat >&2 <<'EOF'
No se encontró archivo de licencia access.ilm ni variable LICENSE_FILE/ILOG_LICENSE_FILE.
Se intentará arrancar el contenedor sin montar licencia (usará la licencia por defecto que tenga CPLEX o fallará si no hay).
- Coloca access.ilm en /home/faros/CPLEX_Studio2211/license/access.ilm (o ajusta CPLEX_DIR).
- O exporta LICENSE_FILE=/ruta/al/access.ilm (o ILOG_LICENSE_FILE=puerto@servidor) antes de ejecutar este script.
EOF
fi

export CPLEX_STUDIO_DIR2211="$CPLEX_DIR"
export PATH="$CPLEX_STUDIO_DIR2211/cplex/bin/x86-64_linux:$PATH"
export LD_LIBRARY_PATH="$CPLEX_STUDIO_DIR2211/cplex/bin/x86-64_linux:$CPLEX_STUDIO_DIR2211/cplex/lib/x86-64_linux:${LD_LIBRARY_PATH:-}"

# Variables para docker-compose (usadas para montar host->contenedor)
export CPLEX_HOST_DIR="$CPLEX_STUDIO_DIR2211"

echo "CPLEX_STUDIO_DIR2211=$CPLEX_STUDIO_DIR2211"
echo "ILOG_LICENSE_FILE=${ILOG_LICENSE_FILE:-<no definido>}"
echo "Modo licencia: $license_mode (archivo montado: ${license_file:-no})"
echo "Iniciando docker-compose con CPLEX montado..."

docker compose "${compose_files[@]}" up "$@"
