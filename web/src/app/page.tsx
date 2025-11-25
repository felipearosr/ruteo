/**
 * Página principal - Fase 3: Ruteo Resiliente con Comparación
 * 
 * Muestra mapa interactivo con 3 rutas calculadas simultáneamente:
 * - Baseline (Dijkstra simple)
 * - Resiliente (Dijkstra con costos ajustados)
 * - A* (Metaheurística)
 */
'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { createClient } from '@supabase/supabase-js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AddressInput } from '@/components/AddressInput';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import {
  MapPin,
  Route as RouteIcon,
  Zap,
  TrendingUp,
  Loader2,
  Check,
  X,
  AlertTriangle,
  BookOpen
} from 'lucide-react';

// Importar Leaflet de forma dinámica
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const Polyline = dynamic(() => import('react-leaflet').then(mod => mod.Polyline), { ssr: false });
const CircleMarker = dynamic(() => import('react-leaflet').then(mod => mod.CircleMarker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });

// Cliente de Supabase
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Tipos de datos
interface RouteMetrics {
  distance_m: number;
  computation_time_ms: number;
  risk_score: number;
  num_segments: number;
  method: string;
  nodes_explored?: number;
  status?: string;
}

interface RouteResult {
  route: any; // GeoJSON
  metrics: RouteMetrics;
  error?: string;
}

interface ComparisonResult {
  baseline: RouteResult;
  resilient: RouteResult;
  astar: RouteResult;
  comparison: {
    total_time_ms: number;
    summary: {
      shortest_distance: number;
      lowest_risk: number;
      fastest_computation: number;
    };
  };
}

export default function HomePage() {
  // Estado para amenazas
  const [inundaciones, setInundaciones] = useState<any[]>([]);
  const [reportes, setReportes] = useState<any[]>([]);
  const [dgaStations, setDgaStations] = useState<any[]>([]);

  // Estado para rutas
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Controles de visualización de capas
  const [showInundaciones, setShowInundaciones] = useState(false);
  const [showReportes, setShowReportes] = useState(false);
  const [showDgaStations, setShowDgaStations] = useState(false);
  const [showDebugGraph, setShowDebugGraph] = useState(false);
  const [debugGraphData, setDebugGraphData] = useState<any>(null);

  // Controles de visualización de rutas
  const [showBaseline, setShowBaseline] = useState(true);
  const [showResilient, setShowResilient] = useState(true);

  const [showAstar, setShowAstar] = useState(true);

  // Parámetros de ruteo
  const [sourceNode, setSourceNode] = useState(640514);
  const [targetNode, setTargetNode] = useState(723678);
  const [k, setK] = useState(5.0);

  const [riskWeight, setRiskWeight] = useState(3.0);
  const [maxRisk, setMaxRisk] = useState<number | null>(null);
  const [maxDistance, setMaxDistance] = useState<number | null>(null);

  // Estado para simulación de fallas
  const [simulationActive, setSimulationActive] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [simulationData, setSimulationData] = useState<any>(null);
  const [simulationEntities, setSimulationEntities] = useState<any[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [geolocating, setGeolocating] = useState(false);

  // Funciones para cargar datos de amenazas
  const loadInundaciones = async () => {
    const { data } = await supabase.from('amenaza_inundaciones_hist').select('*');
    if (data) setInundaciones(data);
  };

  const loadReportes = async () => {
    const { data } = await supabase.from('amenaza_reportes_ciudadanos').select('*');
    if (data) setReportes(data);
  };

  const loadDgaStations = async () => {
    const { data } = await supabase.from('amenaza_dga').select('*');
    if (data) setDgaStations(data);
  };

  useEffect(() => {
    // Cargar amenazas al montar el componente
    loadInundaciones();
    loadReportes();
    loadDgaStations();
  }, []);

  // Load debug graph data when toggled
  useEffect(() => {
    if (showDebugGraph && !debugGraphData) {
      fetch('/debug_graph.json')
        .then(res => res.json())
        .then(data => setDebugGraphData(data))
        .catch(err => console.error('Error loading debug graph:', err));
    }
  }, [showDebugGraph, debugGraphData]); // Added debugGraphData to dependencies to prevent re-fetching if already loaded

  // Cargar ruta de ejemplo al inicio (desde cache)
  useEffect(() => {
    // Cargar ejemplo pre-calculado desde archivo estático
    fetch('/example_route.json')
      .then(res => res.json())
      .then(data => {
        setComparisonData(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error loading cached example:', err);
        // Fallback: calcular en vivo si falla la carga del cache
        setTimeout(() => {
          compareRoutes();
        }, 500);
      });
  }, []);

  const compareRoutes = async () => {
    setIsLoading(true);

    console.log('🚀 Starting route comparison:', { sourceNode, targetNode });

    try {
      const params = new URLSearchParams({
        source: sourceNode.toString(),
        target: targetNode.toString(),
        k: k.toString(),

        risk_weight: riskWeight.toString(),
        ...(maxRisk && { max_risk: maxRisk.toString() }),
        ...(maxDistance && { max_distance: maxDistance.toString() }),
        ...(simulationActive && simulationId && { simulation_id: simulationId })
      });

      const response = await fetch(`/api/route/compare?${params}`);
      const data = await response.json();

      console.log('✅ Routes received:', {
        baseline: data.baseline?.route?.features?.length || 0,
        resilient: data.resilient?.route?.features?.length || 0,
        astar: data.astar?.route?.features?.length || 0
      });

      setComparisonData(data);
    } catch (err) {
      console.error('Error al comparar rutas:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Funciones de simulación de fallas
  const runSimulation = async () => {
    setIsSimulating(true);

    try {
      const response = await fetch('/api/simulate-failures', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          seed: null, // null para random, o número para reproducibilidad
          min_probability: 0.01
        })
      });

      const data = await response.json();

      if (data.success) {
        setSimulationId(data.simulation_id);
        setSimulationData(data.summary);
        setSimulationActive(true);

        // Fetch detailed entities with geometry
        const detailsResponse = await fetch(`/api/simulate-failures?simulation_id=${data.simulation_id}`);
        const detailsData = await detailsResponse.json();

        if (detailsData.success && detailsData.entities) {
          setSimulationEntities(detailsData.entities);
        }

        toast.success('Simulacion activada', {
          description: `${data.summary.total_failed} fallas generadas de ${data.summary.total_entities} entidades. Nodos: ${data.summary.nodos_failed}/${data.summary.total_nodos}, Aristas: ${data.summary.aristas_failed}/${data.summary.total_aristas}`,
          duration: 5000,
        });
      } else {
        toast.error('Error en simulacion', {
          description: data.error,
        });
      }
    } catch (error: any) {
      console.error('Error en simulacion:', error);
      toast.error('Error al simular fallas', {
        description: error.message,
      });
    } finally {
      setIsSimulating(false);
    }
  };

  const clearSimulation = async () => {
    if (!simulationId) return;

    setIsSimulating(true);

    try {
      const response = await fetch(`/api/simulate-failures?simulation_id=${simulationId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.success) {
        setSimulationActive(false);
        setSimulationId(null);
        setSimulationData(null);
        setSimulationEntities([]);
        toast.success('Simulacion eliminada correctamente');
      } else {
        toast.error('Error al limpiar simulacion', {
          description: data.error,
        });
      }
    } catch (error: any) {
      console.error('Error al limpiar simulacion:', error);
      toast.error('Error al limpiar simulacion', {
        description: error.message,
      });
    } finally {
      setIsSimulating(false);
    }
  };

  // Función de geolocalización HTML5
  const useMyLocation = () => {
    setGeolocating(true);

    if (!navigator.geolocation) {
      toast.error('Geolocalizacion no soportada por tu navegador');
      setGeolocating(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        try {
          // Encontrar nodo más cercano usando función de Supabase
          const { data, error } = await supabase.rpc('find_nearest_node', {
            p_lat: latitude,
            p_lon: longitude
          });

          if (error) {
            throw new Error(error.message);
          }

          if (data && data.length > 0) {
            const nearestNode = data[0];
            setSourceNode(nearestNode.node_id);

            toast.success('Ubicacion detectada', {
              description: `Nodo mas cercano: ${nearestNode.node_id} (${nearestNode.distance_m.toFixed(0)} metros)`,
              duration: 4000,
            });
          } else {
            toast.warning('No se encontro ningun nodo cercano a tu ubicacion');
          }
        } catch (error: any) {
          console.error('Error al buscar nodo cercano:', error);
          toast.error('Error al buscar nodo cercano', {
            description: error.message,
          });
        } finally {
          setGeolocating(false);
        }
      },
      (error) => {
        let errorMessage = 'Error desconocido';

        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Permiso denegado. Habilita el acceso a la ubicacion en tu navegador.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Informacion de ubicacion no disponible.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Tiempo de espera agotado.';
            break;
        }

        toast.error('Error de geolocalizacion', {
          description: errorMessage,
        });
        setGeolocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };


  // Cargar caso de ejemplo predefinido
  const loadExample = () => {
    // Configurar parámetros del caso de ejemplo (usando nodos válidos conocidos)
    setSourceNode(640514);
    setTargetNode(723678);
    setK(5.0);

    setRiskWeight(3.0);

    // Habilitar todas las rutas para comparación
    setShowBaseline(true);
    setShowResilient(true);
    setShowAstar(true);

    // Ejecutar comparación después de actualizar estados
    setTimeout(() => {
      compareRoutes();
    }, 300);

    toast.info('Ejemplo cargado', {
      description: 'Origen: Nodo 640514, Destino: Nodo 723678. Ejecutando comparacion de rutas...',
      duration: 3000,
    });
  };

  // Extraer coordenadas de geometría GeoJSON
  const extractCoords = (geom: any): [number, number][] => {
    if (!geom) return [];

    if (typeof geom === 'object' && geom.coordinates) {
      if (geom.type === 'LineString') {
        return geom.coordinates.map((c: number[]) => [c[1], c[0]]);
      }
      if (geom.type === 'Point') {
        return [[geom.coordinates[1], geom.coordinates[0]]];
      }
    }

    return [];
  };

  // Convertir rutas a coordenadas
  const getRouteCoords = (routeData: RouteResult | undefined) => {
    if (!routeData || !routeData.route || !routeData.route.features) return [];
    return routeData.route.features
      .map((f: any) => extractCoords(f.geometry))
      .flat()
      .filter((c: any) => c.length === 2);
  };

  const baselineCoords = getRouteCoords(comparisonData?.baseline);
  const resilientCoords = getRouteCoords(comparisonData?.resilient);
  const astarCoords = getRouteCoords(comparisonData?.astar);

  // Formatear métricas
  const formatDistance = (m: number) => (m / 1000).toFixed(2) + ' km';
  const formatTime = (ms: number) => ms < 1000 ? ms.toFixed(0) + 'ms' : (ms / 1000).toFixed(2) + 's';
  const formatRisk = (r: number) => (r * 100).toFixed(1) + '%';

  return (
    <div className="w-full h-screen flex">
      {/* Panel lateral izquierdo */}
      <div className="w-96 h-full overflow-y-auto bg-background border-r shadow-lg z-10">
        <div className="p-6 space-y-6">
          {/* Encabezado */}
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <RouteIcon className="w-6 h-6" />
              Ruteo Resiliente
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Fase 3 - Comparación de Técnicas
            </p>
          </div>

          {/* Parámetros de Ruteo */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Parámetros</CardTitle>
              <CardDescription>Configurar nodos y restricciones</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="source">Nodo Origen</Label>
                  <div className="flex gap-2">
                    <Input
                      id="source"
                      type="number"
                      value={sourceNode}
                      onChange={(e) => setSourceNode(parseInt(e.target.value) || 1)}
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      size="icon"
                      variant="outline"
                      onClick={useMyLocation}
                      disabled={geolocating}
                      title="Usar mi ubicación actual"
                    >
                      {geolocating ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <MapPin className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target">Nodo Destino</Label>
                  <Input
                    id="target"
                    type="number"
                    value={targetNode}
                    onChange={(e) => setTargetNode(parseInt(e.target.value) || 100)}
                  />
                </div>
              </div>

              {/* Buscar por dirección */}
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label className="text-sm text-gray-600">
                    O buscar origen por dirección:
                  </Label>
                  <AddressInput
                    placeholder="Ej: Av. Providencia 1234, Santiago"
                    onNodeSelected={(nodeId, address, distance) => {
                      setSourceNode(nodeId);
                    }}
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-sm text-gray-600">
                    O buscar destino por dirección:
                  </Label>
                  <AddressInput
                    placeholder="Ej: Mall Parque Arauco, Las Condes"
                    onNodeSelected={(nodeId, address, distance) => {
                      setTargetNode(nodeId);
                    }}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="k">Factor k (Resiliente)</Label>
                <Input
                  id="k"
                  type="number"
                  step="0.1"
                  value={k}
                  onChange={(e) => setK(parseFloat(e.target.value) || 5.0)}
                />
              </div>


              <div className="space-y-2">
                <Label htmlFor="riskweight">Peso Riesgo (A*)</Label>
                <Input
                  id="riskweight"
                  type="number"
                  step="0.1"
                  value={riskWeight}
                  onChange={(e) => setRiskWeight(parseFloat(e.target.value) || 3.0)}
                />
              </div>

              {/* Restricciones opcionales */}
              <div className="pt-3 border-t space-y-2">
                <Label className="text-xs text-gray-500 uppercase">Restricciones (Opcional)</Label>

                <div className="space-y-2">
                  <Label htmlFor="maxrisk" className="text-sm">
                    Riesgo máximo acumulado
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="maxrisk"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      placeholder="Ej: 0.3 (30%)"
                      value={maxRisk || ''}
                      onChange={(e) => setMaxRisk(e.target.value ? parseFloat(e.target.value) : null)}
                      className="flex-1"
                    />
                    {maxRisk !== null && (
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setMaxRisk(null)}
                      >
                        ✕
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    Riesgo total máximo permitido (0.0-1.0). Dejar vacío para sin límite.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxdistance" className="text-sm">
                    Distancia máxima (metros)
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="maxdistance"
                      type="number"
                      step="100"
                      min="0"
                      placeholder="Ej: 10000 (10km)"
                      value={maxDistance || ''}
                      onChange={(e) => setMaxDistance(e.target.value ? parseFloat(e.target.value) : null)}
                      className="flex-1"
                    />
                    {maxDistance !== null && (
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setMaxDistance(null)}
                      >
                        ✕
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    Longitud máxima de ruta permitida. Dejar vacío para sin límite.
                  </p>
                </div>
              </div>

              <Button
                className="w-full"
                onClick={compareRoutes}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Calculando...
                  </>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Comparar Rutas
                  </>
                )}
              </Button>

              <Button
                className="w-full mt-2"
                variant="secondary"
                onClick={loadExample}
                disabled={isLoading}
              >
                <BookOpen className="mr-2 h-4 w-4" />
                Cargar Ejemplo
              </Button>
            </CardContent>
          </Card>

          {/* Control de Capas - Rutas */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Rutas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="baseline"
                  checked={showBaseline}
                  onCheckedChange={(checked) => setShowBaseline(checked as boolean)}
                />
                <Label htmlFor="baseline" className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-blue-500"></div>
                  Baseline
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="resilient"
                  checked={showResilient}
                  onCheckedChange={(checked) => setShowResilient(checked as boolean)}
                />
                <Label htmlFor="resilient" className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-orange-500"></div>
                  Resiliente
                </Label>
              </div>


              <div className="flex items-center space-x-2">
                <Checkbox
                  id="astar"
                  checked={showAstar}
                  onCheckedChange={(checked) => setShowAstar(checked as boolean)}
                />
                <Label htmlFor="astar" className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-purple-500"></div>
                  A*
                </Label>
              </div>
            </CardContent>
          </Card>

          {/* Control de Capas - Amenazas */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Amenazas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="inundaciones"
                  checked={showInundaciones}
                  onCheckedChange={(checked) => setShowInundaciones(checked as boolean)}
                />
                <Label htmlFor="inundaciones" className="text-sm">
                  Zonas de Inundación
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="reportes"
                  checked={showReportes}
                  onCheckedChange={(checked) => setShowReportes(checked as boolean)}
                />
                <Label htmlFor="reportes" className="text-sm">
                  Reportes Ciudadanos
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="dga"
                  checked={showDgaStations}
                  onCheckedChange={(checked) => setShowDgaStations(checked as boolean)}
                />
                <Label htmlFor="dga" className="text-sm">
                  Estaciones DGA
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="debug-graph"
                  checked={showDebugGraph}
                  onCheckedChange={(checked) => setShowDebugGraph(checked as boolean)}
                />
                <Label htmlFor="debug-graph" className="text-sm">
                  🔍 Debug: Grafo (Nodos y Aristas)
                </Label>
              </div>
            </CardContent>
          </Card>

          {/* Simulación de Fallas */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Simulación de Fallas
              </CardTitle>
              <CardDescription>
                Generar fallas aleatorias basadas en probabilidades
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                className="w-full"
                onClick={runSimulation}
                disabled={simulationActive || isSimulating}
                variant={simulationActive ? "secondary" : "default"}
              >
                {isSimulating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Simulando...
                  </>
                ) : simulationActive ? (
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

              {simulationActive && simulationData && (
                <div className="p-3 bg-muted rounded-md text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Nodos fallidos:</span>
                    <Badge variant="destructive">
                      {simulationData.nodos_failed}/{simulationData.total_nodos}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Aristas fallidas:</span>
                    <Badge variant="destructive">
                      {simulationData.aristas_failed}/{simulationData.total_aristas}
                    </Badge>
                  </div>
                  <div className="flex justify-between font-semibold">
                    <span>Total fallas:</span>
                    <span className="text-destructive">{simulationData.total_failed}</span>
                  </div>
                </div>
              )}

              {simulationActive && (
                <Button
                  className="w-full"
                  onClick={clearSimulation}
                  disabled={isSimulating}
                  variant="destructive"
                >
                  {isSimulating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Limpiando...
                    </>
                  ) : (
                    <>
                      <X className="mr-2 h-4 w-4" />
                      Limpiar Simulación
                    </>
                  )}
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Tabla de Comparación */}
          {comparisonData && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Comparación
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Método</TableHead>
                      <TableHead>Distancia</TableHead>
                      <TableHead>Tiempo</TableHead>
                      <TableHead>Riesgo</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Baseline</TableCell>
                      <TableCell>{formatDistance(comparisonData.baseline.metrics.distance_m)}</TableCell>
                      <TableCell>{formatTime(comparisonData.baseline.metrics.computation_time_ms)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.baseline.metrics.risk_score)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Resiliente</TableCell>
                      <TableCell>{formatDistance(comparisonData.resilient.metrics.distance_m)}</TableCell>
                      <TableCell>{formatTime(comparisonData.resilient.metrics.computation_time_ms)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.resilient.metrics.risk_score)}</TableCell>
                    </TableRow>

                    <TableRow>
                      <TableCell className="font-medium">A*</TableCell>
                      <TableCell>{formatDistance(comparisonData.astar.metrics.distance_m)}</TableCell>
                      <TableCell>{formatTime(comparisonData.astar.metrics.computation_time_ms)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.astar.metrics.risk_score)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Distancia más corta:</span>
                    <Badge variant="secondary">
                      {formatDistance(comparisonData.comparison.summary.shortest_distance)}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Menor riesgo:</span>
                    <Badge variant="secondary">
                      {formatRisk(comparisonData.comparison.summary.lowest_risk)}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Más rápido:</span>
                    <Badge variant="secondary">
                      {formatTime(comparisonData.comparison.summary.fastest_computation)}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Mapa */}
      <div className="flex-1 relative">
        <MapContainer
          center={[-33.45, -70.65]}
          zoom={13}
          className="w-full h-full"
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />

          {/* Rutas */}
          {showBaseline && baselineCoords.length > 0 && (
            <Polyline
              positions={baselineCoords}
              pathOptions={{ color: '#3b82f6', weight: 4, opacity: 0.7 }}
            />
          )}

          {showResilient && resilientCoords.length > 0 && (
            <Polyline
              positions={resilientCoords}
              pathOptions={{ color: '#f97316', weight: 4, opacity: 0.7 }}
            />
          )}


          {showAstar && astarCoords.length > 0 && (
            <Polyline
              positions={astarCoords}
              pathOptions={{ color: '#a855f7', weight: 4, opacity: 0.7 }}
            />
          )}

          {/* Inundaciones históricas */}
          {showInundaciones && inundaciones.map((item, idx) => {
            const coords = extractCoords(item.geom);
            if (coords.length === 0) return null;
            return (
              <CircleMarker
                key={`inund-${idx}`}
                center={coords[0]}
                radius={8}
                pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.5 }}
              >
                <Popup>
                  <b>Inundación Histórica</b><br />
                  Fecha: {item.fecha || 'N/A'}<br />
                  Fuente: {item.fuente || 'N/A'}
                </Popup>
              </CircleMarker>
            );
          })}

          {/* Reportes ciudadanos */}
          {showReportes && reportes.map((item, idx) => {
            const coords = extractCoords(item.geom);
            if (coords.length === 0) return null;
            return (
              <CircleMarker
                key={`rep-${idx}`}
                center={coords[0]}
                radius={6}
                pathOptions={{ color: 'orange', fillColor: 'orange', fillOpacity: 0.6 }}
              >
                <Popup>
                  <b>Reporte Ciudadano</b><br />
                  Tipo: {item.tipo || 'N/A'}<br />
                  Fecha: {item.fecha_reporte || 'N/A'}
                </Popup>
              </CircleMarker>
            );
          })}

          {/* Estaciones DGA */}
          {showDgaStations && dgaStations.map((station: any, idx) => {
            const coords = extractCoords(station.geom);
            if (coords.length === 0) return null;
            return (
              <CircleMarker
                key={`dga-${idx}`}
                center={coords[0]}
                radius={7}
                pathOptions={{ color: 'darkblue', fillColor: 'lightblue', fillOpacity: 0.7 }}
              >
                <Popup>
                  <b>Estación DGA</b><br />
                  Nombre: {station.nombre_estacion || 'N/A'}<br />
                  Código: {station.codigo_estacion || 'N/A'}<br />
                  Nivel: {station.nivel_agua_m || 'N/A'}m
                </Popup>
              </CircleMarker>
            );
          })}

          {/* Debug Graph Layer - Nodes and Edges */}
          {showDebugGraph && debugGraphData && debugGraphData.features && debugGraphData.features.map((feature: any, idx: number) => {
            if (feature.properties.type === 'node') {
              const coords = extractCoords(feature.geometry);
              if (coords.length === 0) return null;
              return (
                <CircleMarker
                  key={`debug-node-${idx}`}
                  center={coords[0]}
                  radius={2}
                  pathOptions={{ color: 'gray', fillColor: 'gray', fillOpacity: 0.3, weight: 1 }}
                >
                  <Popup>
                    <b>🔍 Nodo</b><br />
                    ID: {feature.properties.id}
                  </Popup>
                </CircleMarker>
              );
            } else if (feature.properties.type === 'edge') {
              const coords = extractCoords(feature.geometry);
              if (coords.length === 0) return null;
              return (
                <Polyline
                  key={`debug-edge-${idx}`}
                  positions={coords}
                  pathOptions={{ color: 'lightgray', weight: 1, opacity: 0.4 }}
                >
                  <Popup>
                    <b>🔍 Arista</b><br />
                    ID: {feature.properties.id}<br />
                    Source: {feature.properties.source}<br />
                    Target: {feature.properties.target}<br />
                    Length: {feature.properties.length?.toFixed(2)}m
                  </Popup>
                </Polyline>
              );
            }
            return null;
          })}

          {/* Visualización de Fallas Simuladas */}
          {simulationActive && simulationEntities.map((entity, idx) => {
            if (!entity.is_failed || !entity.geom) return null;

            const coords = extractCoords(entity.geom);
            if (coords.length === 0) return null;

            if (entity.entity_type === 'nodo') {
              return (
                <CircleMarker
                  key={`fail-node-${idx}`}
                  center={coords[0]}
                  radius={6}
                  pathOptions={{ color: 'red', fillColor: 'darkred', fillOpacity: 0.9, weight: 2 }}
                >
                  <Popup>
                    <b>❌ Nodo Fallido</b><br />
                    ID: {entity.entity_id}<br />
                    Probabilidad: {(entity.p_fallo * 100).toFixed(1)}%
                  </Popup>
                </CircleMarker>
              );
            } else if (entity.entity_type === 'arista') {
              return (
                <Polyline
                  key={`fail-edge-${idx}`}
                  positions={coords}
                  pathOptions={{ color: 'red', weight: 6, opacity: 0.9 }}
                >
                  <Popup>
                    <b>❌ Arista Fallida</b><br />
                    ID: {entity.entity_id}<br />
                    Probabilidad: {(entity.p_fallo * 100).toFixed(1)}%
                  </Popup>
                </Polyline>
              );
            }
            return null;
          })}

          {/* Marcador de nodo origen */}
          {sourceNode && baselineCoords.length > 0 && (
            <CircleMarker
              center={baselineCoords[0]}
              radius={15}
              pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.8, weight: 3 }}
            >
              <Popup>
                <b>🟢 Nodo Origen</b><br />
                ID: {sourceNode}
              </Popup>
            </CircleMarker>
          )}

          {/* Marcador de nodo destino */}
          {targetNode && baselineCoords.length > 0 && (
            <CircleMarker
              center={baselineCoords[baselineCoords.length - 1]}
              radius={15}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.8, weight: 3 }}
            >
              <Popup>
                <b>🔴 Nodo Destino</b><br />
                ID: {targetNode}
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>

        {/* Leyenda en el mapa */}
        <div className="absolute bottom-4 right-4 z-[1000] bg-white p-4 rounded-lg shadow-lg border">
          <h3 className="font-semibold mb-2 text-sm">Leyenda de Rutas</h3>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-blue-500"></div>
              <span>Baseline (más corta)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-orange-500"></div>
              <span>Resiliente (ajustada)</span>
            </div>

            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-purple-500"></div>
              <span>A* (metaheurística)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
