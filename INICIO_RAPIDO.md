# 🚀 Inicio Rápido - Fase 3

**Tiempo estimado:** 10-15 minutos

---

## Prerrequisitos

✅ Node.js 18+ instalado  
✅ Python 3.11+ instalado  
✅ PostgreSQL 15+ con PostGIS y pgRouting  
✅ Supabase configurado (Fases 1-2 completadas)

---

## Paso 1: Actualizar Base de Datos (5 min)

### 1.1 Agregar Campos de Probabilidad

```sql
-- Conectar a Supabase
psql postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

-- Ejecutar
ALTER TABLE infra_nodos 
ADD COLUMN IF NOT EXISTS p_fallo_nodo DOUBLE PRECISION DEFAULT 0.0;

ALTER TABLE infra_aristas 
ADD COLUMN IF NOT EXISTS p_fallo_arista DOUBLE PRECISION DEFAULT 0.0;
```

### 1.2 Crear Función de Costo Resiliente

```sql
CREATE OR REPLACE FUNCTION infra_calcular_costo_resiliente(k DOUBLE PRECISION)
RETURNS TABLE (
  id BIGINT,
  costo_resiliente DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    a.id,
    a.length_m * (1.0 + k * COALESCE(a.p_fallo_arista, 0.0)) AS costo_resiliente
  FROM infra_aristas a;
END;
$$ LANGUAGE plpgsql;
```

### 1.3 Crear Tabla de Simulación

```sql
CREATE TABLE IF NOT EXISTS sim_fallas_activas (
  id SERIAL PRIMARY KEY,
  simulation_id UUID NOT NULL,
  entity_type VARCHAR(10) NOT NULL,
  entity_id BIGINT NOT NULL,
  p_fallo DOUBLE PRECISION NOT NULL,
  random_value DOUBLE PRECISION NOT NULL,
  is_failed BOOLEAN NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sim_fallas_simulation ON sim_fallas_activas(simulation_id);
```

---

## Paso 2: Configurar Python (3 min)

### 2.1 Instalar Dependencias

```bash
cd /home/faros/ruteo
pip install -r requirements.txt
```

**Nota:** Si no tienes licencia de GUROBI, las rutas Baseline, Resiliente y A* funcionarán igual. Solo la ruta GUROBI fallará con error 503.

### 2.2 Configurar Variables de Entorno

Verificar que `.env` tiene:

```bash
# Supabase
SUPABASE_URL=https://eqjzlgbjgwbnvqzbomsn.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# PostgreSQL
DATABASE_URL=postgres://postgres:[PASSWORD]@db.eqjzlgbjgwbnvqzbomsn.supabase.co:5432/postgres
```

### 2.3 Calcular Probabilidades de Fallo

```bash
python model/actualizar_probabilidades.py
```

**Salida esperada:**
```
Conectando a base de datos...
Calculando probabilidades para nodos...
Progress: 1234/1234 (100%)
Calculando probabilidades para aristas...
Progress: 5678/5678 (100%)
✅ Actualización completada en 12.34s
```

**Tiempo:** ~10-30 segundos (depende del tamaño de datos)

---

## Paso 3: Configurar Frontend (2 min)

### 3.1 Instalar Dependencias de Node

```bash
cd web
npm install
```

**Nota:** Ya están instaladas desde sesiones anteriores. Este comando verificará que todo esté actualizado (228 paquetes).

### 3.2 Verificar Variables de Entorno

Archivo `web/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://eqjzlgbjgwbnvqzbomsn.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## Paso 4: Iniciar Aplicación (1 min)

```bash
cd /home/faros/ruteo/web
npm run dev
```

**Salida esperada:**
```
   ▲ Next.js 14.0.4
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.10:3000

 ✓ Ready in 2.1s
```

---

## Paso 5: Probar en Navegador (5 min)

### 5.1 Abrir Aplicación

Navegar a: **http://localhost:3000**

### 5.2 Verificar Interfaz

Deberías ver:
- ✅ Panel lateral izquierdo con controles
- ✅ Mapa en el lado derecho
- ✅ Amenazas cargadas (círculos rojos/naranjas)

### 5.3 Ejecutar Primera Comparación

**Configuración de prueba:**
1. Nodo Origen: **1**
2. Nodo Destino: **100**
3. Factor k: **5.0**
4. λ (Lambda): **5.0**
5. Peso Riesgo: **3.0**

**Acción:** Click en **"Comparar Rutas"**

### 5.4 Resultados Esperados

**Tiempo de ejecución:** 2-5 segundos

**Mapa:**
- 🔵 Ruta Baseline (azul)
- 🟠 Ruta Resiliente (naranja)
- 🟢 Ruta GUROBI (verde) - o error 503 si no hay licencia
- 🟣 Ruta A* (púrpura)

**Tabla Comparativa:**

| Método     | Distancia | Tiempo  | Riesgo |
|------------|-----------|---------|--------|
| Baseline   | ~7.5 km   | ~100ms  | ~65%   |
| Resiliente | ~8.2 km   | ~200ms  | ~22%   |
| GUROBI     | ~8.3 km   | ~2s     | ~18%   |
| A*         | ~8.4 km   | ~300ms  | ~25%   |

**Badges:**
- 🏆 Distancia más corta: 7.52 km
- 🛡️ Menor riesgo: 18.0%
- ⚡ Más rápido: 100ms

---

## 🎯 Pruebas Sugeridas

### Prueba 1: Comparar Visualización

**Objetivo:** Ver diferencias entre rutas

1. Asegúrate de que todas las rutas estén visibles (checkboxes marcados)
2. Observa cómo la ruta baseline (azul) pasa cerca de amenazas
3. Observa cómo las otras rutas las evitan

**Tip:** Haz click en los checkboxes para mostrar/ocultar rutas individuales

---

### Prueba 2: Ajustar Parámetros

**Objetivo:** Probar sensibilidad a parámetros

**Configuración 1 - Conservador:**
- k: **10.0**
- λ: **10.0**
- risk_weight: **5.0**

**Resultado esperado:** Rutas más largas pero mucho más seguras (riesgo ~10-15%)

**Configuración 2 - Agresivo:**
- k: **1.0**
- λ: **1.0**
- risk_weight: **1.0**

**Resultado esperado:** Rutas más cortas, similar a baseline (riesgo ~50-60%)

---

### Prueba 3: Toggle de Capas

**Objetivo:** Ver amenazas y entender su influencia

1. Desmarcar todas las rutas
2. Marcar solo **Resiliente** y **Baseline**
3. Activar capa de **Inundaciones**
4. Hacer click en círculos rojos para ver detalles
5. Observar cómo Resiliente evita esas zonas

---

### Prueba 4: Verificar Métricas

**Objetivo:** Entender trade-offs

**Pregunta 1:** ¿Cuál es la ruta más rápida de calcular?
**Respuesta esperada:** Baseline (~50-200ms)

**Pregunta 2:** ¿Cuál tiene el menor riesgo?
**Respuesta esperada:** GUROBI (~15-20%) - óptimo matemático

**Pregunta 3:** ¿Cuál es el mejor balance?
**Respuesta esperada:** Resiliente o A* (riesgo ~20-25%, tiempo ~200-300ms)

---

## 🐛 Troubleshooting

### Problema: "No routes found"

**Causa:** Nodos no conectados o no existen

**Solución:**
```sql
-- Verificar nodos
SELECT id, geom FROM infra_nodos WHERE id IN (1, 100);

-- Si están vacíos, usar nodos existentes
SELECT id FROM infra_nodos LIMIT 10;
```

---

### Problema: "GUROBI not available (503)"

**Causa:** Licencia de GUROBI no instalada

**Solución 1 - Ignorar:**
- Las otras 3 rutas funcionarán perfectamente
- GUROBI es opcional

**Solución 2 - Instalar licencia:**
Ver `docs/instalacion_gurobi.md`

---

### Problema: "TypeError: Cannot read property 'features'"

**Causa:** API retornó error pero frontend esperaba GeoJSON

**Solución:**
```bash
# Verificar logs del servidor
# Terminal donde corre npm run dev

# Ver respuesta de API
curl http://localhost:3000/api/route/baseline?source=1&target=100
```

---

### Problema: "p_fallo_arista is null"

**Causa:** No se ejecutó `actualizar_probabilidades.py`

**Solución:**
```bash
python model/actualizar_probabilidades.py
```

---

### Problema: Rutas idénticas

**Causa:** Probabilidades muy bajas

**Solución:**
```sql
-- Verificar promedio de probabilidades
SELECT 
  AVG(p_fallo_nodo) as avg_nodo,
  AVG(p_fallo_arista) as avg_arista
FROM infra_nodos, infra_aristas;

-- Debería ser > 0.01
-- Si es 0, ejecutar actualizar_probabilidades.py
```

---

### Problema: Mapa no carga

**Causa:** Leaflet no se importó correctamente

**Solución:**
1. Verificar que no haya errores en consola del navegador (F12)
2. Limpiar caché: `rm -rf .next && npm run dev`

---

## ✅ Checklist de Verificación

Antes de continuar, verifica:

- [ ] Base de datos tiene campos `p_fallo_nodo` y `p_fallo_arista`
- [ ] Función `infra_calcular_costo_resiliente` existe
- [ ] Script `actualizar_probabilidades.py` se ejecutó exitosamente
- [ ] Valores de `p_fallo_arista` son > 0 (verificar con SQL)
- [ ] Frontend carga sin errores (npm run dev)
- [ ] Al menos 3 rutas (Baseline, Resiliente, A*) funcionan
- [ ] Mapa muestra amenazas correctamente
- [ ] Tabla comparativa muestra métricas
- [ ] Checkboxes de toggle funcionan

---

## 📚 Siguientes Pasos

Una vez que todo funcione:

1. **Leer documentación:**
   - `docs/guia_usuario_interfaz.md` - Guía completa de uso
   - `docs/caso_ejemplo_fase3.md` - Caso de ejemplo detallado
   - `RESUMEN_IMPLEMENTACION_FASE3.md` - Visión completa del proyecto

2. **Probar casos avanzados:**
   - Rutas largas (>50 nodos)
   - Restricciones (max_risk, max_distance)
   - Diferentes valores de parámetros

3. **Próximas funcionalidades:**
   - Geolocalización HTML5
   - Geocodificación con Nominatim
   - Simulación de fallas
   - Exportación de rutas

---

## 🎉 ¡Listo!

Si llegaste hasta aquí y todo funciona, **¡felicidades!** 🎊

Tienes un sistema de ruteo resiliente completamente funcional con:
- ✅ 4 algoritmos diferentes
- ✅ Comparación visual simultánea
- ✅ Interfaz profesional con shadcn/ui
- ✅ Modelo probabilístico de riesgos
- ✅ Métricas detalladas

---

**Tiempo total:** ~15 minutos  
**Siguiente paso:** Probar el caso de ejemplo en `docs/caso_ejemplo_fase3.md`
