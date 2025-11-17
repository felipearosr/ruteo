/**
 * Página principal - Fase 3: Ruteo Resiliente con Comparación
 * 
 * Muestra mapa interactivo con 4 rutas calculadas simultáneamente:
 * - Baseline (Dijkstra simple)
 * - Resiliente (Dijkstra con costos ajustados)
 * - GUROBI (Optimización MILP)
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
  AlertTriangle
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
  gurobi: RouteResult;
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
  const [showInundaciones, setShowInundaciones] = useState(true);
  const [showReportes, setShowReportes] = useState(true);
  const [showDGA, setShowDGA] = useState(false);
  
  // Controles de visualización de rutas
  const [showBaseline, setShowBaseline] = useState(true);
  const [showResilient, setShowResilient] = useState(true);
  const [showGurobi, setShowGurobi] = useState(true);
  const [showAstar, setShowAstar] = useState(true);
  
  // Parámetros de ruteo
  const [sourceNode, setSourceNode] = useState(1);
  const [targetNode, setTargetNode] = useState(100);
  const [k, setK] = useState(5.0);
  const [lambdaRisk, setLambdaRisk] = useState(5.0);
  const [riskWeight, setRiskWeight] = useState(3.0);
  const [maxRisk, setMaxRisk] = useState<number | null>(null);
  const [maxDistance, setMaxDistance] = useState<number | null>(null);

  useEffect(() => {
    // Cargar datos de amenazas
    supabase.from('amenaza_inundaciones_hist').select('*').then(({ data }) => {
      if (data) setInundaciones(data);
    });

    supabase.from('amenaza_reportes_ciudadanos').select('*').then(({ data }) => {
      if (data) setReportes(data);
    });

    supabase.from('amenaza_dga').select('*').then(({ data }) => {
      if (data) setDgaStations(data);
    });
  }, []);

  const compareRoutes = async () => {
    setIsLoading(true);
    
    try {
      const params = new URLSearchParams({
        source: sourceNode.toString(),
        target: targetNode.toString(),
        k: k.toString(),
        lambda_risk: lambdaRisk.toString(),
        risk_weight: riskWeight.toString(),
        ...(maxRisk && { max_risk: maxRisk.toString() }),
        ...(maxDistance && { max_distance: maxDistance.toString() })
      });

      const response = await fetch(`/api/route/compare?${params}`);
      const data = await response.json();
      
      setComparisonData(data);
    } catch (err) {
      console.error('Error al comparar rutas:', err);
    } finally {
      setIsLoading(false);
    }
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
  const gurobiCoords = getRouteCoords(comparisonData?.gurobi);
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
                  <Input
                    id="source"
                    type="number"
                    value={sourceNode}
                    onChange={(e) => setSourceNode(parseInt(e.target.value) || 1)}
                  />
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
                <Label htmlFor="lambda">λ (GUROBI)</Label>
                <Input
                  id="lambda"
                  type="number"
                  step="0.1"
                  value={lambdaRisk}
                  onChange={(e) => setLambdaRisk(parseFloat(e.target.value) || 5.0)}
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
                  id="gurobi"
                  checked={showGurobi}
                  onCheckedChange={(checked) => setShowGurobi(checked as boolean)}
                />
                <Label htmlFor="gurobi" className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-green-500"></div>
                  GUROBI
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
                  checked={showDGA}
                  onCheckedChange={(checked) => setShowDGA(checked as boolean)}
                />
                <Label htmlFor="dga" className="text-sm">
                  Estaciones DGA
                </Label>
              </div>
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
                      <TableCell className="font-medium">GUROBI</TableCell>
                      <TableCell>{formatDistance(comparisonData.gurobi.metrics.distance_m)}</TableCell>
                      <TableCell>{formatTime(comparisonData.gurobi.metrics.computation_time_ms)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.gurobi.metrics.risk_score)}</TableCell>
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

          {showGurobi && gurobiCoords.length > 0 && (
            <Polyline 
              positions={gurobiCoords}
              pathOptions={{ color: '#22c55e', weight: 4, opacity: 0.7 }}
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
                  <b>Inundación Histórica</b><br/>
                  Fecha: {item.fecha || 'N/A'}<br/>
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
                  <b>Reporte Ciudadano</b><br/>
                  Tipo: {item.tipo || 'N/A'}<br/>
                  Fecha: {item.fecha_reporte || 'N/A'}
                </Popup>
              </CircleMarker>
            );
          })}

          {/* Estaciones DGA */}
          {showDGA && dgaStations.map((item, idx) => {
            const coords = extractCoords(item.geom);
            if (coords.length === 0) return null;
            return (
              <CircleMarker 
                key={`dga-${idx}`}
                center={coords[0]}
                radius={7}
                pathOptions={{ color: 'darkblue', fillColor: 'lightblue', fillOpacity: 0.7 }}
              >
                <Popup>
                  <b>Estación DGA</b><br/>
                  Código: {item.codigo_estacion || 'N/A'}<br/>
                  Nivel: {item.nivel_agua_m || 'N/A'}m
                </Popup>
              </CircleMarker>
            );
          })}
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
              <div className="w-6 h-1 bg-green-500"></div>
              <span>GUROBI (óptima)</span>
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
