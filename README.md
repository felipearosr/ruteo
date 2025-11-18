# 🚀 Sistema de Ruteo Resiliente ante Inundaciones Urbanas — Fase 3

**Sistema avanzado de ruteo con optimización multi-algoritmo, simulación de fallas y geocodificación**

[![Estado](https://img.shields.io/badge/Estado-Producción-success)]()
[![Progreso](https://img.shields.io/badge/Progreso-94%25-brightgreen)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue)]()

Aplicación web completa para calcular rutas resilientes en entornos urbanos con riesgo de inundación.
Compara 4 algoritmos diferentes (Dijkstra, Optimización MILP, A*, Resiliente) considerando probabilidades
de falla dinámicas basadas en amenazas reales.

---

## ✨ Features Principales

### 🗺️ Entrada de Ubicación (3 opciones)
- **📍 Geolocalización GPS:** Usa tu ubicación actual con HTML5 Geolocation
- **🔍 Geocodificación:** Escribe "Av. Providencia 1234, Santiago" con autocomplete
- **🔢 ID Manual:** Ingresa directamente el ID del nodo en la red

### 🛣️ Algoritmos de Ruteo
- **Baseline:** Dijkstra clásico (ruta más corta)
- **Resiliente:** Dijkstra con costos ajustados por riesgo
- **GUROBI:** Optimización MILP (ruta óptima global)
- **A\*:** Metaheurística con heurística de riesgo

### 💥 Simulación de Fallas
- Activar/desactivar amenazas aleatoriamente
- Tasas configurables (10%, 30%, 50%)
- Visualización de estadísticas de fallas
- Comparar rutas con y sin fallas

### 📊 Visualización Avanzada
- Mapa interactivo Leaflet con 4 rutas simultáneas
- Tabla comparativa de métricas (distancia, tiempo, riesgo)
- Badges de resumen (shortest, fastest, lowest risk)
- Capas de amenazas (inundaciones, DGA, reportes)

### ⚙️ Controles Avanzados
- Botón "Cargar Ejemplo" para demo rápida
- Restricciones opcionales (max_risk, max_distance)
- Parámetros configurables (k, λ, risk_weight)
- Toggle de capas de visualización

---

## 🎬 Quick Start

### Prerequisitos

- **Node.js 18+** y npm
- **Python 3.11+**
- **PostgreSQL 15+** con PostGIS 3.3+ y pgRouting 3.4+
- **Supabase** (o PostgreSQL local)
- **GUROBI 11.0+** (opcional, para optimización MILP)

### Instalación Rápida

```zsh
# 1. Clonar repositorio
git clone https://github.com/felipearosr/ruteo.git
cd ruteo

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus credenciales de Supabase

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Crear esquema de base de datos
psql "postgresql://postgres:PASSWORD@HOST:5432/DATABASE" -f sql/schema.sql

# 5. Ejecutar ETL para generar datos
python main.py

# 6. Cargar datos a Supabase
python load_to_supabase.py

# 7. Configurar frontend
cd web
cp .env.local.example .env.local
# Edita .env.local con credenciales

# 8. Instalar dependencias frontend
npm install

# 9. Iniciar servidor de desarrollo
npm run dev
```

Abre http://localhost:3000 🎉

---

## 📚 Documentación

### 📖 Guías de Usuario
- **[Guía Completa de la Interfaz](docs/guia_usuario_interfaz.md)** - Tutorial paso a paso (534 líneas)
- **[Inicio Rápido (15 min)](docs/INICIO_RAPIDO.md)** - Comienza a usar la app en 15 minutos
- **[Caso de Ejemplo Detallado](docs/caso_ejemplo_fase3.md)** - Ruta Providencia → Las Condes

### 🔧 Documentación Técnica
- **[Instalación de GUROBI](docs/instalacion_gurobi.md)** - Guía para configurar optimizador MILP
- **[Resumen de Implementación Fase 3](docs/RESUMEN_IMPLEMENTACION_FASE3.md)** - Arquitectura completa (678 líneas)
- **[Esquemas de Datos](amenazas/)** - Definición de tablas y campos

### 🎉 Features Implementadas
- **[Simulación de Fallas](docs/SIMULACION_COMPLETADA.md)** - Cómo funciona la simulación dinámica
- **[Geolocalización GPS](docs/GEOLOCALIZACION_COMPLETADA.md)** - Integración con HTML5 Geolocation
- **[Geocodificación](docs/GEOCODIFICACION_COMPLETADA.md)** - Búsqueda de direcciones con Nominatim
- **[Botón Cargar Ejemplo](docs/CARGAR_EJEMPLO_COMPLETADO.md)** - Demo en 1 clic
- **[Resumen Completo Sesión](docs/RESUMEN_SESION_FASE3.md)** - Todo lo implementado en Fase 3

---

## 🏗️ Arquitectura

### Stack Tecnológico

**Backend:**
- PostgreSQL 15+ con PostGIS 3.3+ y pgRouting 3.4+
- Supabase (hosting cloud)
- Python 3.11 (ETL y algoritmos)

**Frontend:**
- Next.js 14 + React 18 + TypeScript 5
- shadcn/ui + Radix UI
- Tailwind CSS 3.3
- Leaflet 1.9.4

**APIs:**
- Nominatim OpenStreetMap (geocodificación gratuita)
- GUROBI 11.0+ (optimización MILP opcional)

### Diagrama de Base de Datos

Ver esquema completo en [`sql/diagram.svg`](sql/diagram.svg)

**Tablas principales:**
- `infra_nodos` (42,534 nodos)
- `infra_aristas` (89,021 aristas con geometría)
- `meta_elevacion`, `meta_lluvia`, `meta_landcover`
- `amenaza_dga`, `amenaza_inundaciones_hist`, `amenaza_reportes_ciudadanos`
- `sim_fallas_activas` (estado de simulaciones)

---

## 📡 API Reference

### Rutas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/route/baseline` | GET | Dijkstra clásico (ruta más corta) |
| `/api/route/resilient` | GET | Dijkstra con costos ajustados (k factor) |
| `/api/route/optimize` | GET | GUROBI MILP (óptimo global con λ) |
| `/api/route/metaheuristic` | GET | A* con heurística de riesgo |
| `/api/route/compare` | GET | Ejecuta las 4 rutas simultáneamente |

### Utilidades

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/geocode` | GET | Geocodifica dirección a coordenadas |
| `/api/simulate-failures` | POST | Genera simulación de fallas aleatoria |
| `/api/simulate-failures` | DELETE | Elimina simulación activa |

**Ejemplo:**

```bash
# Comparar 4 rutas con parámetros personalizados
curl "http://localhost:3000/api/route/compare?\
source=1&\
target=100&\
k=5.0&\
lambda_risk=5.0&\
risk_weight=3.0&\
max_risk=0.3&\
max_distance=10000"
```

Ver documentación completa de cada endpoint en el código fuente de cada API route.

---

## 🐳 Docker

### Desarrollo con Docker Compose

```zsh
# Construir imagen
docker compose -f docker/docker-compose.yml build

# Iniciar servicios
docker compose -f docker/docker-compose.yml up

# Detener
docker compose -f docker/docker-compose.yml down
```

El contenedor ejecuta automáticamente:
1. ETL (genera archivos JSON/GeoJSON)
2. Servidor web Next.js en http://localhost:3000

### Variables de Entorno para Docker

Crear archivo `.env` en la raíz:

```bash
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_DB_HOST=db.tu-proyecto.supabase.co
SUPABASE_DB_PORT=6543
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=tu_password
```

---

## 🧪 Testing

### Casos de Prueba Esenciales

**1. Ruta básica:**
- Cargar ejemplo (botón 📚)
- Verificar 4 rutas en mapa
- Comparar métricas en tabla

**2. Simulación de fallas:**
- Simular 30% de fallas
- Ejecutar rutas
- Ver diferencias en tabla

**3. Geolocalización:**
- Clic en botón GPS (📍)
- Aceptar permiso
- Verificar nodo seleccionado

**4. Geocodificación:**
- Buscar "Av. Providencia 1234"
- Seleccionar de dropdown
- Verificar nodo encontrado

**5. Restricciones:**
- Ingresar max_risk = 0.3
- Ejecutar GUROBI
- Verificar riesgo < 30%

Ver guía completa en `docs/guia_usuario_interfaz.md`

---

## 🗺️ Roadmap

### ✅ Completado (94%)

- [x] 4 algoritmos de ruteo (Baseline, Resiliente, GUROBI, A*)
- [x] 6 API endpoints funcionales
- [x] Frontend profesional con shadcn/ui
- [x] Mapa interactivo con 4 rutas simultáneas
- [x] Tabla comparativa de métricas
- [x] Simulación de fallas dinámica
- [x] Geolocalización HTML5 con GPS
- [x] Geocodificación con Nominatim autocomplete
- [x] Botón "Cargar Ejemplo" para demo
- [x] Inputs de restricciones opcionales
- [x] Documentación completa (~3,500 líneas)

### 🔄 Próximos Pasos (6%)

- [ ] Testing exhaustivo de features
- [ ] Screenshots para README
- [ ] Configuración Docker final
- [ ] Deploy a producción

### 🎯 Futuro (Post-100%)

- [ ] Cache de geocodificación
- [ ] Historial de búsquedas
- [ ] Self-hosted Nominatim
- [ ] Tests unitarios automatizados
- [ ] CI/CD con GitHub Actions

---

## 🤝 Contribuir

¡Contribuciones son bienvenidas!

1. Fork del repositorio
2. Crear branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add: amazing feature'`)
4. Push a branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

**Guidelines:**
- Seguir convenciones de código (TypeScript/Python)
- Agregar documentación para nuevas features
- Incluir tests cuando sea posible

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

## 👤 Autor

**Felipe Aros**
- GitHub: [@felipearosr](https://github.com/felipearosr)
- Proyecto: [ruteo](https://github.com/felipearosr/ruteo)

---

## 🙏 Agradecimientos

- **OpenStreetMap** - Datos de infraestructura vial
- **Nominatim** - API de geocodificación gratuita
- **Supabase** - Hosting PostgreSQL cloud
- **GUROBI** - Solver de optimización
- **shadcn/ui** - Componentes UI profesionales

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Líneas de código** | ~4,000 |
| **Líneas de documentación** | ~3,500 |
| **Commits** | 100+ |
| **Tiempo de desarrollo** | ~40 horas |
| **Features implementadas** | 20+ |
| **API endpoints** | 7 |
| **Componentes UI** | 8 |
| **Algoritmos** | 4 |

---

**⭐ Si te gusta este proyecto, dale una estrella en GitHub!**

---

*Última actualización: 17 de Noviembre, 2025 — Fase 3 (94% completada)*
