# Dockerfile para la aplicación (ETL Python + Next.js)
# - Incluye Python 3.11 para ejecutar los scripts ETL (main.py y *_etl.py)
# - Incluye Node.js 20 para construir/ejecutar la parte Next.js en `web/`
# - Instala dependencias si existen `requirements.txt` y `web/package.json`
# - Entry point por defecto: ejecutar `main.py`

FROM python:3.11-slim

# Evitar prompts interactivos durante apt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       gnupg \
       build-essential \
       git \
       locales \
    && rm -rf /var/lib/apt/lists/*

# Instalar Node.js 20 desde NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /app

# Ruta recomendada de licencia GUROBI (puede montarse vía volumen)
ENV GUROBI_LICENSE_FILE=/opt/gurobi/gurobi.lic
ENV GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic

# Copiar todo el repositorio al contenedor
# (se asume que el contexto de build es la raíz del repositorio)
COPY . /app

# Actualizar pip y, si existe, instalar requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Instalar dependencias de Node/Next.js si existe package.json en /app/web
RUN if [ -f web/package.json ]; then npm --prefix web ci --prefer-offline --no-audit --progress=false; fi

# Variables de entorno recomendadas (pueden sobrescribirse en docker-compose o entorno de ejecución)
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Puerto por defecto (Next.js suele usar 3000)
EXPOSE 3000

# Copiar script de inicio
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Variables de entorno recomendadas (pueden sobrescribirse en docker-compose o entorno de ejecución)
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Puerto por defecto (Next.js suele usar 3000)
EXPOSE 3000

# Punto de entrada: ejecutar script de inicio
ENTRYPOINT ["/usr/local/bin/start.sh"]
