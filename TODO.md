# TODO - Sistema de Ruteo Resiliente

Estado actual del proyecto: **94% completado**

## Tareas Pendientes Principales

### Alta Prioridad

- [ ] **Testing exhaustivo de features**
  - [ ] Probar todos los endpoints API con diferentes parametros
  - [ ] Verificar casos borde (nodos desconectados, rutas muy largas)
  - [ ] Probar simulacion de fallas con diferentes tasas
  - [ ] Validar geocodificacion con direcciones ambiguas

- [ ] **Screenshots para documentacion**
  - [ ] Captura de pantalla del mapa con 4 rutas
  - [ ] Captura de la tabla comparativa
  - [ ] Captura del panel de capas
  - [ ] Captura de simulacion de fallas activa

- [ ] **Configuracion Docker final**
  - [ ] Verificar que docker-compose.yml funcione correctamente
  - [ ] Probar build completo desde cero
  - [ ] Documentar variables de entorno requeridas
  - [ ] Agregar health checks a los servicios

### Prioridad Media

- [ ] **Documentacion de esquema JSON**
  - [ ] Crear README para cada archivo JSON en /amenazas
  - [ ] Documentar estructura de infraestructura.geojson
  - [ ] Documentar estructura de metadata/*.json

- [ ] **Mejoras de ETL**
  - [ ] Agregar manejo de errores mas robusto en osm_infra_etl.py
  - [ ] Implementar retry logic para APIs externas
  - [ ] Agregar logging estructurado

- [ ] **Video demostrativo (Fase 3)**
  - [ ] Grabar demostracion de carga del sitio web
  - [ ] Mostrar seleccion de origen/destino con geolocalizacion
  - [ ] Mostrar comparacion de 4 algoritmos
  - [ ] Mostrar simulacion de fallas
  - [ ] Exportar video a menos de 50MB

### Baja Prioridad (Post-100%)

- [ ] **Cache de geocodificacion**
  - [ ] Implementar cache local para Nominatim
  - [ ] Agregar TTL configurable

- [ ] **Historial de busquedas**
  - [ ] Almacenar ultimas 10 busquedas en localStorage
  - [ ] Agregar UI para acceder al historial

- [ ] **Self-hosted Nominatim**
  - [ ] Configurar contenedor Docker de Nominatim
  - [ ] Cargar datos de Chile

- [ ] **Tests unitarios automatizados**
  - [ ] Tests para modelo de probabilidad de falla
  - [ ] Tests para algoritmos de ruteo
  - [ ] Tests para endpoints API

- [ ] **CI/CD con GitHub Actions**
  - [ ] Workflow para ejecutar tests
  - [ ] Workflow para build de Docker
  - [ ] Workflow para deploy automatico

## Requisitos del Paper IEEE (Fase 4)

El paper debe tener exactamente 14 paginas e incluir:

- [x] Introduccion con referencias
- [x] Estado del arte
- [x] Problematica (con n estudios)
- [x] Hipotesis
- [x] Objetivo general y especificos
- [x] Metodologia
- [x] Desarrollo y resultados
- [x] Conclusiones y trabajo futuro
- [x] Bibliografia APA

**Nota**: El archivo `informes/fase4_paper_ieee.tex` contiene el borrador del paper.

## Verificacion de Entregables por Fase

### Fase 1 (Presentacion)
- [x] Problematica identificada con estudios
- [x] Hipotesis
- [x] Objetivos
- [x] Infraestructura definida (OSM)
- [x] Metadata definida (3 fuentes)
- [x] Amenazas definidas (3 fuentes)

### Fase 2 (Implementacion ETL)
- [x] Diagrama de BD (sql/schema.sql)
- [x] Carpeta Infraestructura con ETL
- [x] Carpeta Metadata con 3 ETLs
- [x] Carpeta Amenazas con 3 ETLs
- [ ] Archivos README para cada JSON
- [x] Scripts de carga a BD
- [x] Sitio web con Leaflet
- [x] Ruta con pgr_dijkstra
- [x] main.py orquestador
- [x] Docker configurado

### Fase 3 (Algoritmos y Demo)
- [x] Rutas realistas (no lineas rectas)
- [x] Parametros de consulta del usuario
- [x] Geolocalizacion automatica (GPS)
- [x] Geocodificacion alternativa
- [x] Visualizacion de metadata y amenazas
- [x] Panel de control con checkboxes
- [x] Modelo de probabilidad de falla
- [x] pgr_dijkstra (baseline)
- [x] CPLEX MILP (optimize)
- [x] pgr_dijkstra resiliente
- [x] A* metaheuristica
- [x] Toggle de rutas en UI
- [x] Tiempo de computo mostrado
- [x] Simulacion de fallas (random 0-100)
- [x] Checkbox para amenazas activas
- [x] Caso de ejemplo funcional

## Comandos Utiles

```bash
# Ejecutar ETL completo
python main.py

# Cargar datos a Supabase
python load_to_supabase.py

# Iniciar servidor de desarrollo
cd web && npm run dev

# Build de produccion
cd web && npm run build

# Docker
docker compose -f docker/docker-compose.yml up
```

## Contacto

- Autor: Felipe Aros
- GitHub: https://github.com/felipearosr/ruteo
