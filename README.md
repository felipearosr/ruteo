# Sistema de Ruteo Resiliente ante Inundaciones Urbanas

**Sistema de navegación inteligente que calcula rutas seguras considerando riesgos de inundación en Santiago de Chile**

[![Estado](https://img.shields.io/badge/Estado-Producción-success)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue)]()
[![Next.js](https://img.shields.io/badge/Next.js-14-black)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)]()

## Video Demo - Tarea 3

[![Video Demo Tarea 3](https://img.youtube.com/vi/jiYTzVdZzk0/maxresdefault.jpg)](https://youtu.be/jiYTzVdZzk0)

---

## Descripción

Este proyecto implementa un sistema de ruteo vehicular que integra datos de amenazas hidrometeorológicas para calcular rutas que minimicen simultáneamente la distancia recorrida y la exposición a zonas de riesgo de inundación.

El sistema compara **4 algoritmos de ruteo**:
- **Dijkstra Baseline**: Ruta más corta tradicional
- **Dijkstra Resiliente**: Considera probabilidades de falla
- **CPLEX MILP**: Optimización global con programación lineal
- **A* Resiliente**: Metaheurística con heurística de riesgo

### Características Principales

- Integración de datos de OpenStreetMap, DGA, SERNAGEOMIN
- Modelo de probabilidad de falla basado en proximidad a amenazas
- Simulación de escenarios de falla dinámica
- Interfaz web interactiva con mapas Leaflet
- API REST para integración con otros sistemas
- Geocodificación de direcciones con Nominatim

---

## Inicio Rapido con Docker

La forma mas sencilla de ejecutar el proyecto es usando Docker. Solo necesitas tener Docker instalado.

### Prerequisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/felipearosr/ruteo.git
cd ruteo

# 2. Iniciar servicios (base de datos + aplicacion web)
cd docker
docker compose -f docker-compose.full.yml up -d

# 3. Esperar ~30 segundos a que la base de datos inicie, luego inicializar
./init-db.sh
```

**Listo!** Abrir http://localhost:3000

### Comandos Utiles

```bash
# Ver logs de la aplicacion
docker logs -f ruteo_web

# Detener servicios
docker compose -f docker-compose.full.yml down

# Detener y eliminar datos (reinicio completo)
docker compose -f docker-compose.full.yml down -v
```

---

## Instalacion Manual (Alternativa)

Si prefieres no usar Docker, puedes instalar manualmente:

### Prerequisitos

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ con PostGIS 3.3+ y pgRouting 3.4+
- IBM CPLEX (opcional, para optimizacion MILP)

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/felipearosr/ruteo.git
cd ruteo

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales de base de datos

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Crear esquema de base de datos
psql "$SUPABASE_DB_URL" -f sql/schema.sql

# 5. Ejecutar pipeline ETL
python main.py

# 6. Cargar datos a la base de datos
python load_to_supabase.py

# 7. Calcular probabilidades de falla
psql "$SUPABASE_DB_URL" -f sql/setup_and_calculate_probabilities.sql

# 8. Configurar e iniciar frontend
cd web
npm install
npm run dev
```

Abrir http://localhost:3000

---

## Arquitectura

### Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | PostgreSQL 15, PostGIS 3.3, pgRouting 3.4 |
| **Base de Datos** | Supabase (PostgreSQL gestionado) |
| **Optimización** | IBM CPLEX con docplex |
| **ETL** | Python 3.11, GeoPandas, Shapely |

### Estructura del Proyecto

```
ruteo/
├── web/                    # Aplicación Next.js
│   ├── src/
│   │   ├── app/           # Páginas y API routes
│   │   │   ├── api/       # Endpoints REST
│   │   │   │   ├── route/
│   │   │   │   │   ├── baseline/
│   │   │   │   │   ├── resilient/
│   │   │   │   │   ├── optimize/
│   │   │   │   │   ├── metaheuristic/
│   │   │   │   │   └── compare/
│   │   │   │   ├── geocode/
│   │   │   │   └── simulate-failures/
│   │   │   └── page.tsx   # Interfaz principal
│   │   ├── components/    # Componentes React
│   │   └── lib/           # Utilidades
│   └── package.json
├── sql/                    # Scripts SQL
│   ├── schema.sql         # Esquema de base de datos
│   └── setup_and_calculate_probabilities.sql
├── infraestructura/        # ETL de red vial
│   └── osm_infra_etl.py
├── amenazas/               # ETL de amenazas
│   ├── dga_etl.py
│   ├── inundaciones_hist_etl.py
│   └── reportes_ciudadanos_etl.py
├── metadata/               # ETL de metadatos
│   ├── elevacion_etl.py
│   ├── lluvia_etl.py
│   └── landcover_etl.py
├── optimization/           # Algoritmos de optimización
│   └── cplex_model.py
├── model/                  # Modelo de probabilidad
│   └── actualizar_probabilidades.py
├── docker/                 # Configuración Docker
├── docs/                   # Documentación adicional
├── main.py                 # Orquestador ETL
├── load_to_supabase.py     # Carga de datos
└── requirements.txt        # Dependencias Python
```

---

## Base de Datos

### Esquema Principal

#### Tablas de Infraestructura

| Tabla | Descripción | Registros |
|-------|-------------|-----------|
| `infra_nodos` | Nodos de la red vial (intersecciones) | ~28,000 |
| `infra_aristas` | Aristas con geometría y probabilidad de falla | ~34,000 |

#### Tablas de Amenazas

| Tabla | Descripción | Registros |
|-------|-------------|-----------|
| `amenaza_dga` | Estaciones de monitoreo hidrológico | 94 |
| `amenaza_rios` | Zonas de inundación histórica (buffer 150m) | 58 |
| `amenaza_pasos_bajo_nivel` | Pasos bajo nivel vulnerables | 20 |
| `amenaza_reportes_ciudadanos` | Reportes de inundación geolocalizados | 25 |

#### Tablas de Metadatos

| Tabla | Descripción |
|-------|-------------|
| `meta_elevacion` | Datos de elevación SRTM |
| `meta_lluvia` | Datos de precipitación CHIRPS |
| `meta_landcover` | Cobertura de suelo |

### Modelo de Probabilidad de Falla

La probabilidad de falla de cada arista se calcula como:

```
p_fallo = Σ (w_i × exp(-d_i / r_i))
```

Donde:
- `w_i`: Peso del factor (inundación: 0.4, DGA: 0.3, reportes: 0.2, lluvia: 0.1)
- `d_i`: Distancia a la amenaza más cercana de tipo i
- `r_i`: Radio de influencia del factor i

---

## API Reference

### Endpoints de Ruteo

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/route/baseline` | GET | Dijkstra clásico (ruta más corta) |
| `/api/route/resilient` | GET | Dijkstra con costos ajustados por riesgo |
| `/api/route/optimize` | GET | CPLEX MILP (óptimo global) |
| `/api/route/metaheuristic` | GET | A* con heurística de riesgo |
| `/api/route/compare` | GET | Ejecuta los 4 algoritmos simultáneamente |

### Parámetros de Ruteo

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `source` | number | ID del nodo origen | requerido |
| `target` | number | ID del nodo destino | requerido |
| `k` | number | Factor de penalización (Dijkstra resiliente) | 5.0 |
| `lambda_risk` | number | Factor de riesgo (CPLEX) | 5.0 |
| `risk_weight` | number | Peso de riesgo (A*) | 3.0 |
| `max_risk` | number | Restricción de riesgo máximo (0-1) | null |
| `max_distance` | number | Restricción de distancia máxima (metros) | null |

### Endpoints Auxiliares

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/geocode` | GET | Geocodifica dirección a coordenadas |
| `/api/simulate-failures` | POST | Genera simulación de fallas |
| `/api/simulate-failures` | DELETE | Elimina simulación activa |

### Ejemplo de Uso

```bash
# Comparar 4 rutas entre dos puntos
curl "http://localhost:3000/api/route/compare?source=1&target=100&k=5.0"

# Geocodificar una dirección
curl "http://localhost:3000/api/geocode?address=Av.%20Providencia%201234,%20Santiago"

# Simular 30% de fallas
curl -X POST "http://localhost:3000/api/simulate-failures?rate=0.3"
```

---

## Docker

El proyecto incluye configuracion Docker para desarrollo local con base de datos incluida.

### Archivos Docker

| Archivo | Descripcion |
|---------|-------------|
| `docker/docker-compose.full.yml` | Stack completo (DB + Web) - **Recomendado** |
| `docker/docker-compose.local-db.yml` | Solo base de datos |
| `docker/init-db.sh` | Script de inicializacion de datos |
| `backup_supabase.dump` | Dump de la base de datos con todos los datos |

### Iniciar Stack Completo

```bash
cd docker

# Iniciar base de datos y aplicacion web
docker compose -f docker-compose.full.yml up -d

# Inicializar datos (primera vez)
./init-db.sh

# Ver logs
docker logs -f ruteo_web

# Detener
docker compose -f docker-compose.full.yml down
```

### Solo Base de Datos (para desarrollo local)

```bash
# 1. Iniciar PostgreSQL con pgRouting
docker compose -f docker/docker-compose.local-db.yml up -d

# 2. Esperar ~10 segundos, luego restaurar datos
docker exec ruteo_local_db pg_restore -U postgres -d ruteo --no-owner --no-acl /backup.dump

# 3. Habilitar extension pgRouting
docker exec ruteo_local_db psql -U postgres -d ruteo -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"

# 4. Configurar variables de entorno para la app web
cd web
cat > .env.local << EOF
SUPABASE_DB_HOST=localhost
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=ruteo
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=postgres
EOF

# 5. Instalar dependencias e iniciar
npm install
npm run dev
```

Abrir http://localhost:3000

### Conexion a la Base de Datos Local

```
Host: localhost
Puerto: 5432
Base de datos: ruteo
Usuario: postgres
Password: postgres
```

---

## Algoritmos Implementados

### 1. Dijkstra Baseline

Algoritmo clásico de camino más corto. Utiliza `pgr_dijkstra` de pgRouting.

```sql
SELECT * FROM pgr_dijkstra(
    'SELECT id, source, target, length_m AS cost FROM infra_aristas',
    origen, destino, directed := false
);
```

### 2. Dijkstra Resiliente

Modifica el costo incorporando la probabilidad de falla:

```
cost = length × (1 + k × p_fallo)
```

Donde `k` es el factor de penalización (default: 5.0).

### 3. CPLEX MILP

Formulación como problema de programación lineal entera mixta:

**Función objetivo:**
```
min Σ x_e × (length_e + λ × length_e × p_e)
```

**Restricciones de flujo:**
```
Σ x_out - Σ x_in = b_v  ∀v ∈ V
```

Donde b_v = 1 (origen), -1 (destino), 0 (otros).

### 4. A* Resiliente

Extiende Dijkstra con heurística euclidiana:

```
f(n) = g(n) + h(n)
g(n) = costo acumulado con penalización de riesgo
h(n) = distancia euclidiana al destino
```

---

## Resultados Experimentales

### Comparación de Algoritmos

| Algoritmo | Red. Riesgo | Aum. Distancia | Tiempo Cómputo |
|-----------|-------------|----------------|----------------|
| Baseline | - | - | ~50 ms |
| Resiliente | 50.8% | 8.1% | ~50 ms |
| CPLEX | 58.3% | 5.2% | ~8,000 ms |
| A* | 49.2% | 6.9% | ~500 ms |

### Disponibilidad bajo Fallas (30% tasa de falla)

| Algoritmo | Disponibilidad |
|-----------|----------------|
| Baseline | 67% |
| Resiliente | 86% |
| CPLEX | 90% |
| A* | 85% |

---

## Documentación Adicional

- [Guía de Usuario de la Interfaz](docs/guia_usuario_interfaz.md)
- [Configuración de CPLEX](docs/cplex_config.md)
- [Implementación de Simulación de Fallas](docs/implementacion_simulacion_fallas.md)
- [Caso de Ejemplo Detallado](docs/caso_ejemplo_fase3.md)

---

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork del repositorio
2. Crear branch para la feature (`git checkout -b feature/nueva-feature`)
3. Commit de cambios (`git commit -m 'Agregar nueva feature'`)
4. Push al branch (`git push origin feature/nueva-feature`)
5. Abrir Pull Request

### Guías de Estilo

- **Python**: PEP 8, comentarios en español
- **TypeScript**: ESLint configurado en el proyecto
- **Commits**: Mensajes descriptivos en español

---

## Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## Autor

**Felipe Aros**
- GitHub: [@felipearosr](https://github.com/felipearosr)
- Email: felipe.aros1@mail.udp.cl
- Universidad Diego Portales, Santiago, Chile

---

## Agradecimientos

- **OpenStreetMap** - Datos de infraestructura vial
- **Supabase** - Hosting de base de datos PostgreSQL
- **IBM** - Licencia académica de CPLEX
- **DGA Chile** - Datos de estaciones hidrológicas
- **SERNAGEOMIN** - Datos de zonas de inundación
- **Nominatim** - API de geocodificación

---

## Citar este Proyecto

```bibtex
@software{aros2024ruteo,
  author = {Aros, Felipe},
  title = {Sistema de Ruteo Resiliente ante Inundaciones Urbanas},
  year = {2024},
  url = {https://github.com/felipearosr/ruteo}
}
```

---

*Desarrollado como proyecto de investigación en la Universidad Diego Portales, Santiago de Chile.*
