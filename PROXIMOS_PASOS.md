# 🔜 Próximos Pasos - Guía de Implementación

**Para alcanzar el 90% de completitud**

---

## 1. Simulación de Fallas Dinámicas (10%)

### Descripción
Permitir activar/desactivar amenazas de forma aleatoria basándose en sus probabilidades, simulando un escenario de fallas reales.

### Implementación

#### Paso 1.1: Crear Endpoint de Simulación

Crear archivo: `web/src/app/api/simulate-failures/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const { seed } = await request.json();
    
    // Generar ID único para esta simulación
    const simulationId = uuidv4();
    
    // Si hay seed, usarlo para Math.random determinista
    // (implementar seeded random si es necesario)
    
    // Obtener nodos con probabilidad > 0
    const { data: nodos } = await supabase
      .from('infra_nodos')
      .select('id, p_fallo_nodo')
      .gt('p_fallo_nodo', 0);
    
    // Obtener aristas con probabilidad > 0
    const { data: aristas } = await supabase
      .from('infra_aristas')
      .select('id, p_fallo_arista')
      .gt('p_fallo_arista', 0);
    
    const simulaciones = [];
    
    // Simular fallas en nodos
    for (const nodo of nodos || []) {
      const randomValue = Math.random();
      const isFailed = randomValue < nodo.p_fallo_nodo;
      
      simulaciones.push({
        simulation_id: simulationId,
        entity_type: 'nodo',
        entity_id: nodo.id,
        p_fallo: nodo.p_fallo_nodo,
        random_value: randomValue,
        is_failed: isFailed
      });
    }
    
    // Simular fallas en aristas
    for (const arista of aristas || []) {
      const randomValue = Math.random();
      const isFailed = randomValue < arista.p_fallo_arista;
      
      simulaciones.push({
        simulation_id: simulationId,
        entity_type: 'arista',
        entity_id: arista.id,
        p_fallo: arista.p_fallo_arista,
        random_value: randomValue,
        is_failed: isFailed
      });
    }
    
    // Guardar en BD
    await supabase
      .from('sim_fallas_activas')
      .insert(simulaciones);
    
    // Contar fallas
    const nodosFailures = simulaciones.filter(s => s.entity_type === 'nodo' && s.is_failed).length;
    const aristasFailures = simulaciones.filter(s => s.entity_type === 'arista' && s.is_failed).length;
    
    return NextResponse.json({
      simulation_id: simulationId,
      total_nodos: nodos?.length || 0,
      nodos_failed: nodosFailures,
      total_aristas: aristas?.length || 0,
      aristas_failed: aristasFailures,
      timestamp: new Date().toISOString()
    });
    
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}

// Endpoint para limpiar simulaciones
export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const simulationId = searchParams.get('simulation_id');
  
  if (simulationId) {
    await supabase
      .from('sim_fallas_activas')
      .delete()
      .eq('simulation_id', simulationId);
  } else {
    // Limpiar todas
    await supabase
      .from('sim_fallas_activas')
      .delete()
      .neq('id', 0); // Truco para borrar todas
  }
  
  return NextResponse.json({ message: 'Simulación eliminada' });
}
```

#### Paso 1.2: Agregar UI en page.tsx

Agregar estado y botones:

```typescript
const [simulationActive, setSimulationActive] = useState(false);
const [simulationId, setSimulationId] = useState<string | null>(null);

const runSimulation = async () => {
  const response = await fetch('/api/simulate-failures', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ seed: null })
  });
  
  const data = await response.json();
  setSimulationId(data.simulation_id);
  setSimulationActive(true);
  
  // Mostrar resultados
  alert(`Simulación activada:\n${data.nodos_failed} nodos fallidos\n${data.aristas_failed} aristas fallidas`);
};

const clearSimulation = async () => {
  if (!simulationId) return;
  
  await fetch(`/api/simulate-failures?simulation_id=${simulationId}`, {
    method: 'DELETE'
  });
  
  setSimulationActive(false);
  setSimulationId(null);
};
```

Agregar botones en el panel lateral:

```tsx
<Card>
  <CardHeader>
    <CardTitle className="text-lg flex items-center gap-2">
      <Zap className="w-4 h-4" />
      Simulación
    </CardTitle>
  </CardHeader>
  <CardContent className="space-y-3">
    <Button 
      className="w-full" 
      onClick={runSimulation}
      disabled={simulationActive}
      variant={simulationActive ? "secondary" : "default"}
    >
      {simulationActive ? (
        <>
          <Check className="mr-2 h-4 w-4" />
          Simulación Activa
        </>
      ) : (
        <>
          <Zap className="mr-2 h-4 w-4" />
          Simular Fallas
        </>
      )}
    </Button>
    
    {simulationActive && (
      <Button 
        className="w-full" 
        onClick={clearSimulation}
        variant="destructive"
      >
        <X className="mr-2 h-4 w-4" />
        Limpiar Simulación
      </Button>
    )}
  </CardContent>
</Card>
```

**Tiempo estimado:** 2-3 horas

---

## 2. Geolocalización HTML5 (5%)

### Descripción
Detectar automáticamente la ubicación del usuario y usarla como punto de inicio.

### Implementación

#### Paso 2.1: Agregar Función de Geolocalización

En `page.tsx`:

```typescript
const [geolocating, setGeolocating] = useState(false);

const useMyLocation = () => {
  setGeolocating(true);
  
  if (!navigator.geolocation) {
    alert('Geolocalización no soportada por tu navegador');
    setGeolocating(false);
    return;
  }
  
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords;
      
      // Encontrar nodo más cercano
      const { data, error } = await supabase.rpc('find_nearest_node', {
        lat: latitude,
        lon: longitude
      });
      
      if (data && data.length > 0) {
        setSourceNode(data[0].id);
        alert(`Ubicación detectada: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}\nNodo más cercano: ${data[0].id}`);
      } else {
        alert('No se encontró un nodo cercano');
      }
      
      setGeolocating(false);
    },
    (error) => {
      alert(`Error: ${error.message}`);
      setGeolocating(false);
    }
  );
};
```

#### Paso 2.2: Crear Función PostgreSQL

En `sql/schema.sql`:

```sql
CREATE OR REPLACE FUNCTION find_nearest_node(lat DOUBLE PRECISION, lon DOUBLE PRECISION)
RETURNS TABLE (id BIGINT, distance_m DOUBLE PRECISION) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    n.id,
    ST_Distance(
      n.geom::geography,
      ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    ) AS distance_m
  FROM infra_nodos n
  ORDER BY distance_m
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;
```

#### Paso 2.3: Agregar Botón

```tsx
<div className="flex gap-2">
  <Input
    id="source"
    type="number"
    value={sourceNode}
    onChange={(e) => setSourceNode(parseInt(e.target.value) || 1)}
    className="flex-1"
  />
  <Button
    size="icon"
    variant="outline"
    onClick={useMyLocation}
    disabled={geolocating}
  >
    {geolocating ? (
      <Loader2 className="h-4 w-4 animate-spin" />
    ) : (
      <MapPin className="h-4 w-4" />
    )}
  </Button>
</div>
```

**Tiempo estimado:** 1-2 horas

---

## 3. Geocodificación con Nominatim (10%)

### Descripción
Permitir ingresar dirección textual y convertirla a coordenadas.

### Implementación

#### Paso 3.1: Crear Endpoint de Geocodificación

Crear archivo: `web/src/app/api/geocode/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const address = searchParams.get('address');
  
  if (!address) {
    return NextResponse.json(
      { error: 'address parameter required' },
      { status: 400 }
    );
  }
  
  try {
    // Nominatim API
    const url = `https://nominatim.openstreetmap.org/search?` +
      `q=${encodeURIComponent(address)}, Santiago, Chile&` +
      `format=json&` +
      `limit=5&` +
      `countrycodes=cl`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'RuteoResilienteApp/1.0'
      }
    });
    
    const data = await response.json();
    
    return NextResponse.json({
      results: data.map((item: any) => ({
        display_name: item.display_name,
        lat: parseFloat(item.lat),
        lon: parseFloat(item.lon),
        boundingbox: item.boundingbox
      }))
    });
    
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
```

#### Paso 3.2: Crear Componente AddressInput

Crear archivo: `web/src/components/AddressInput.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Search, Loader2 } from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

interface AddressInputProps {
  label: string;
  onNodeSelected: (nodeId: number) => void;
}

export function AddressInput({ label, onNodeSelected }: AddressInputProps) {
  const [address, setAddress] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  
  const searchAddress = async () => {
    if (!address) return;
    
    setSearching(true);
    
    try {
      // Geocodificar
      const response = await fetch(`/api/geocode?address=${encodeURIComponent(address)}`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        const result = data.results[0];
        
        // Encontrar nodo más cercano
        const { data: nodeData } = await supabase.rpc('find_nearest_node', {
          lat: result.lat,
          lon: result.lon
        });
        
        if (nodeData && nodeData.length > 0) {
          onNodeSelected(nodeData[0].id);
          alert(`Dirección encontrada:\n${result.display_name}\nNodo: ${nodeData[0].id}`);
        }
      } else {
        alert('No se encontraron resultados');
      }
    } catch (error) {
      alert('Error en geocodificación');
    } finally {
      setSearching(false);
    }
  };
  
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Ej: Providencia 1234"
          onKeyPress={(e) => e.key === 'Enter' && searchAddress()}
        />
        <Button
          size="icon"
          variant="outline"
          onClick={searchAddress}
          disabled={searching || !address}
        >
          {searching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
```

#### Paso 3.3: Integrar en page.tsx

```tsx
import { AddressInput } from '@/components/AddressInput';

// En el JSX
<AddressInput 
  label="Dirección de Origen"
  onNodeSelected={(id) => setSourceNode(id)}
/>

<AddressInput 
  label="Dirección de Destino"
  onNodeSelected={(id) => setTargetNode(id)}
/>
```

**Tiempo estimado:** 3-4 horas

---

## 4. Botón "Cargar Ejemplo" (2%)

### Descripción
Precargar el caso de ejemplo documentado con un solo click.

### Implementación

```typescript
const loadExample = () => {
  // Valores del caso de ejemplo
  setSourceNode(1);
  setTargetNode(100);
  setK(5.0);
  setLambdaRisk(5.0);
  setRiskWeight(3.0);
  
  // Auto-ejecutar
  setTimeout(() => {
    compareRoutes();
  }, 500);
};
```

Agregar botón:

```tsx
<Button 
  className="w-full" 
  variant="secondary"
  onClick={loadExample}
>
  <FileText className="mr-2 h-4 w-4" />
  Cargar Ejemplo
</Button>
```

**Tiempo estimado:** 30 minutos

---

## 5. Exportación de Rutas (2%)

### Descripción
Descargar rutas calculadas en formato GPX o GeoJSON.

### Implementación

```typescript
const exportRoute = (format: 'gpx' | 'geojson') => {
  if (!comparisonData) return;
  
  const route = comparisonData.baseline.route; // o cualquier otra
  
  if (format === 'geojson') {
    const blob = new Blob([JSON.stringify(route, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ruta_${Date.now()}.geojson`;
    a.click();
  } else {
    // Convertir a GPX (requiere librería gpx-builder o similar)
    alert('Formato GPX en desarrollo');
  }
};
```

Agregar botones:

```tsx
<div className="flex gap-2">
  <Button 
    size="sm" 
    variant="outline"
    onClick={() => exportRoute('geojson')}
  >
    <Download className="mr-2 h-4 w-4" />
    GeoJSON
  </Button>
  <Button 
    size="sm" 
    variant="outline"
    onClick={() => exportRoute('gpx')}
  >
    <Download className="mr-2 h-4 w-4" />
    GPX
  </Button>
</div>
```

**Tiempo estimado:** 1-2 horas

---

## 6. Dark Mode Toggle (1%)

### Descripción
Permitir cambiar entre tema claro y oscuro.

### Implementación

Crear archivo: `web/src/components/theme-toggle.tsx`

```typescript
'use client';

import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from './ui/button';

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  
  useEffect(() => {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (saved) {
      setTheme(saved);
      document.documentElement.classList.toggle('dark', saved === 'dark');
    }
  }, []);
  
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
    >
      {theme === 'light' ? (
        <Moon className="h-5 w-5" />
      ) : (
        <Sun className="h-5 w-5" />
      )}
    </Button>
  );
}
```

Agregar en `page.tsx`:

```tsx
import { ThemeToggle } from '@/components/theme-toggle';

// En el header
<div className="flex items-center justify-between">
  <h1>...</h1>
  <ThemeToggle />
</div>
```

**Tiempo estimado:** 30 minutos

---

## 🗓️ Plan de Implementación Sugerido

### Día 1 (4-6 horas)
- ✅ Simulación de fallas (endpoint + UI)
- ✅ Geolocalización HTML5

### Día 2 (4-6 horas)
- ✅ Geocodificación con Nominatim
- ✅ Botón cargar ejemplo

### Día 3 (2-4 horas)
- ✅ Exportación de rutas
- ✅ Dark mode toggle
- ✅ Testing manual exhaustivo

### Día 4 (opcional, 4-8 horas)
- ✅ Testing automatizado
- ✅ Documentación de funcionalidades nuevas
- ✅ Refactoring y optimizaciones

---

## ✅ Checklist de Validación

Después de implementar cada funcionalidad, verificar:

### Simulación de Fallas
- [ ] Endpoint POST funciona
- [ ] Endpoint DELETE funciona
- [ ] Se guardan registros en `sim_fallas_activas`
- [ ] Botón UI cambia de estado
- [ ] Alert muestra cantidad de fallas

### Geolocalización
- [ ] Solicita permiso de ubicación
- [ ] Encuentra nodo más cercano
- [ ] Actualiza input de origen
- [ ] Muestra error si no hay permisos

### Geocodificación
- [ ] Endpoint `/api/geocode` funciona
- [ ] Nominatim retorna resultados
- [ ] Encuentra nodo más cercano
- [ ] Componente AddressInput renderiza
- [ ] Enter ejecuta búsqueda

### Cargar Ejemplo
- [ ] Precarga valores correctos
- [ ] Auto-ejecuta comparación
- [ ] Funciona en primera carga

### Exportación
- [ ] GeoJSON descarga correctamente
- [ ] Archivo es válido JSON
- [ ] Incluye todas las features

### Dark Mode
- [ ] Toggle cambia clase 'dark'
- [ ] Persiste en localStorage
- [ ] CSS variables cambian
- [ ] Mapa se adapta

---

## 📚 Referencias

- **Nominatim API:** https://nominatim.org/release-docs/develop/api/Search/
- **Geolocation API:** https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API
- **shadcn/ui Docs:** https://ui.shadcn.com/
- **Next.js API Routes:** https://nextjs.org/docs/app/building-your-application/routing/route-handlers

---

**¡Buena suerte con la implementación!** 🚀

Si tienes dudas, consulta la documentación existente en `/docs/` o crea un issue en GitHub.
