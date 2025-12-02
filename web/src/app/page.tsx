/**
 * Página principal - Fase 3: Ruteo Resiliente con Comparación
 * 
 * Muestra mapa interactivo con 2 rutas calculadas simultáneamente:
 * - Baseline (Dijkstra simple)
 * - Resiliente (Dijkstra con costos ajustados)
 */
'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { useMapEvents } from 'react-leaflet';
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
const Circle = dynamic(() => import('react-leaflet').then(mod => mod.Circle), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });
const Tooltip = dynamic(() => import('react-leaflet').then(mod => mod.Tooltip), { ssr: false });

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

interface NodeAdjustment {
  requested: number;
  resolved: number;
  exists: boolean;
  degree: number | null;
  snapped: boolean;
  nearestDistanceM: number | null;
  requestedLat: number | null;
  requestedLon: number | null;
  resolvedLat: number | null;
  resolvedLon: number | null;
}

interface ComparisonResult {
  baseline: RouteResult;
  resilient: RouteResult;
  cplex?: RouteResult;
  astar: RouteResult;
  node_adjustments?: {
    source: NodeAdjustment;
    target: NodeAdjustment;
    adjustedSource: number;
    adjustedTarget: number;
  };
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
  const mapRef = useRef<any>(null);
  const [mapReady, setMapReady] = useState(false);
  const [leafletLib, setLeafletLib] = useState<typeof import('leaflet') | null>(null);
  const [lastMouseLatLng, setLastMouseLatLng] = useState<{ lat: number; lon: number } | null>(null);
  const [showNodes, setShowNodes] = useState(false);
  const [visibleNodes, setVisibleNodes] = useState<{ id: number; lat: number; lon: number }[]>([]);
  const [isLoadingNodes, setIsLoadingNodes] = useState(false);
  const emptyNodesWarned = useRef(false);
  const [currentZoom, setCurrentZoom] = useState<number>(13);
  const [nodesInfo, setNodesInfo] = useState<string | null>(null);
  const [shouldFitBounds, setShouldFitBounds] = useState(true);
  const [showConnections, setShowConnections] = useState(false);
  const [visibleConnections, setVisibleConnections] = useState<{ id: number; coords: [number, number][] }[]>([]);
  const [isLoadingConnections, setIsLoadingConnections] = useState(false);

  // Estado para rutas
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Controles de visualización de capas
  const [showInundaciones, setShowInundaciones] = useState(true);
  const [showReportes, setShowReportes] = useState(true);
  const [showDgaStations, setShowDgaStations] = useState(true);

  // Controles de visualización de rutas
  const [showBaseline, setShowBaseline] = useState(true);
  const [showResilient, setShowResilient] = useState(true);
  const [showAstar, setShowAstar] = useState(true);
  const [showCplex, setShowCplex] = useState(true);



  // Parámetros de ruteo
  // Nodos de ejemplo (se dejan vacíos al cargar; usar o seleccionar)
  const [sourceNode, setSourceNode] = useState<string>('');
  const [targetNode, setTargetNode] = useState<string>('');
  const [k, setK] = useState(5.0);
  const [maxRisk, setMaxRisk] = useState<number | null>(null);
  const [maxDistance, setMaxDistance] = useState<number | null>(null);
  const [maxTimeMinutes, setMaxTimeMinutes] = useState<number | null>(null);
  const [avoidFloodZones, setAvoidFloodZones] = useState(false);

  // Estado para simulación de fallas
  const [simulationActive, setSimulationActive] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [simulationData, setSimulationData] = useState<any>(null);
  const [simulationEntities, setSimulationEntities] = useState<any[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [onlySimulatedThreats, setOnlySimulatedThreats] = useState(false);
  const [geolocating, setGeolocating] = useState(false);
  const [sourceMarker, setSourceMarker] = useState<{ lat: number; lon: number; label?: string; distance?: number } | null>(null);
  const [targetMarker, setTargetMarker] = useState<{ lat: number; lon: number; label?: string; distance?: number } | null>(null);
  const markerUpdateTimeout = useRef<NodeJS.Timeout | null>(null);

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

  // Cargar Leaflet solo en cliente para evitar errores de window en SSR
  useEffect(() => {
    let mounted = true;
    if (typeof window !== 'undefined') {
      import('leaflet').then((mod) => {
        if (mounted) setLeafletLib(mod);
      });
    }
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    // Cargar amenazas al montar el componente
    loadInundaciones();
    loadReportes();
    loadDgaStations();
  }, []);



  // Modo rápido: Shift + D fija el destino en la posición actual del cursor sobre el mapa
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.shiftKey && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        if (lastMouseLatLng) {
          setDestinationFromPosition(lastMouseLatLng.lat, lastMouseLatLng.lon, 'Destino (Shift+D)');
        } else {
          toast.warning('Mueve el mouse sobre el mapa y vuelve a intentarlo');
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [lastMouseLatLng]);

  const compareRoutes = async () => {
    const src = parseInt(sourceNode, 10);
    const tgt = parseInt(targetNode, 10);
    if (Number.isNaN(src) || Number.isNaN(tgt)) {
      toast.warning('Ingresa nodo origen y destino antes de calcular');
      return;
    }

    // Asegurar que las capas estén visibles al recalcular
    setShowBaseline(true);
    setShowResilient(true);
    setShowAstar(true);
    setShowCplex(true);

    setIsLoading(true);

    console.log('🚀 Starting route comparison:', { sourceNode, targetNode });

    try {
      const AVERAGE_SPEED_M_PER_MIN = 500; // ~30 km/h as rough estimate
      const timeBasedDistance = maxTimeMinutes ? maxTimeMinutes * AVERAGE_SPEED_M_PER_MIN : null;
      const effectiveMaxDistance = (() => {
        if (timeBasedDistance !== null && maxDistance !== null) {
          return Math.min(timeBasedDistance, maxDistance);
        }
        if (timeBasedDistance !== null) return timeBasedDistance;
        if (maxDistance !== null) return maxDistance;
        return null;
      })();

      const params = new URLSearchParams({
        source: src.toString(),
        target: tgt.toString(),
        k: k.toString(),
        ...(maxRisk && { max_risk: maxRisk.toString() }),
        ...(effectiveMaxDistance && { max_distance: effectiveMaxDistance.toString() }),
        ...(maxTimeMinutes && { max_time_min: maxTimeMinutes.toString() }),
        ...(avoidFloodZones && { avoid_flood_zones: 'true' }),
        ...(simulationActive && simulationId && { simulation_id: simulationId })
      });

      const response = await fetch(`/api/route/compare?${params}`);
      const data = await response.json();

      console.log('✅ Routes received:', {
        baseline: data.baseline?.route?.features?.length || 0,
        resilient: data.resilient?.route?.features?.length || 0,
        astar: data.astar?.route?.features?.length || 0,
        cplex: data.cplex?.route?.features?.length || 0
      });

      setComparisonData(data);
      setShouldFitBounds(true);
      const adjustments = data.node_adjustments;
      if (adjustments?.source?.resolvedLat != null && adjustments?.source?.resolvedLon != null) {
        setSourceMarker({
          lat: adjustments.source.resolvedLat,
          lon: adjustments.source.resolvedLon,
          label: adjustments.source.snapped
            ? `Snapped → ${adjustments.source.resolved} (desde ${adjustments.source.requested})`
            : `Nodo ${adjustments.source.resolved}`,
          distance: adjustments.source.nearestDistanceM ?? undefined
        });
      }
      if (adjustments?.target?.resolvedLat != null && adjustments?.target?.resolvedLon != null) {
        setTargetMarker({
          lat: adjustments.target.resolvedLat,
          lon: adjustments.target.resolvedLon,
          label: adjustments.target.snapped
            ? `Snapped → ${adjustments.target.resolved} (desde ${adjustments.target.requested})`
            : `Nodo ${adjustments.target.resolved}`,
          distance: adjustments.target.nearestDistanceM ?? undefined
        });
      }
      const noRoutes =
        (!data?.baseline?.route?.features || data.baseline.route.features.length === 0) &&
        (!data?.resilient?.route?.features || data.resilient.route.features.length === 0) &&
        (!data?.astar?.route?.features || data.astar.route.features.length === 0) &&
        (!data?.cplex?.route?.features || data.cplex.route.features.length === 0);
      if (noRoutes) {
        toast.warning('No se encontraron rutas para estos nodos', {
          description: 'Verifica origen/destino o intenta con otro par de nodos.'
        });
      }
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
            setSourceNode(nearestNode.node_id.toString());
            setSourceMarker({
              lat: nearestNode.node_lat ?? latitude,
              lon: nearestNode.node_lon ?? longitude,
              label: 'Ubicacion detectada',
              distance: nearestNode.distance_m
            });
            clearRoutes();

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
    // Configurar parámetros del caso de ejemplo (nodos cercanos válidos)
    setSourceNode('81615');
    setTargetNode('79672');
    setK(5.0);



    // Habilitar todas las rutas para comparación
    setShowBaseline(true);
    setShowResilient(true);
    setShowCplex(true);
    setShowAstar(true);

    // Ejecutar comparación después de actualizar estados
    setTimeout(() => {
      compareRoutes();
    }, 300);

    toast.info('Ejemplo cargado', {
      description: 'Origen: Nodo 81615, Destino: Nodo 79672. Ejecutando comparacion de rutas...',
      duration: 3000,
    });
  };

  // Extraer coordenadas de geometría GeoJSON
  const extractCoords = (geom: any): [number, number][] => {
    if (!geom) return [];

    const handleCoords = (coords: any): [number, number][] => {
      if (!Array.isArray(coords)) return [];
      // Handles [lon, lat] pairs
      if (coords.length === 2 && typeof coords[0] === 'number' && typeof coords[1] === 'number') {
        return [[coords[1], coords[0]]];
      }
      // Handles nested arrays (LineString / MultiLineString parts)
      return coords.flatMap((c: any) => handleCoords(c));
    };

    if (typeof geom === 'object' && geom.type && geom.coordinates) {
      if (geom.type === 'LineString' || geom.type === 'MultiLineString') {
        return handleCoords(geom.coordinates);
      }
      if (geom.type === 'Point') {
        return [[geom.coordinates[1], geom.coordinates[0]]];
      }
      if (geom.type === 'GeometryCollection' && Array.isArray(geom.geometries)) {
        return geom.geometries.flatMap((g: any) => extractCoords(g));
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

  const baselineCoords = useMemo(() => getRouteCoords(comparisonData?.baseline), [comparisonData?.baseline]);
  const resilientCoords = useMemo(() => getRouteCoords(comparisonData?.resilient), [comparisonData?.resilient]);
  const astarCoords = useMemo(() => getRouteCoords(comparisonData?.astar), [comparisonData?.astar]);
  const cplexCoords = useMemo(() => getRouteCoords(comparisonData?.cplex), [comparisonData?.cplex]);
  const sourceLatLng = sourceMarker ? [sourceMarker.lat, sourceMarker.lon] : (baselineCoords[0] ?? null);
  const targetLatLng = targetMarker ? [targetMarker.lat, targetMarker.lon] : (baselineCoords.length ? baselineCoords[baselineCoords.length - 1] : null);

  // Ajustar vista del mapa al conjunto de rutas o marcadores disponibles
  useEffect(() => {
    if (!mapRef.current || !leafletLib) return;
    if (!shouldFitBounds) return;

    const routeCoords: [number, number][] = [
      ...baselineCoords,
      ...resilientCoords,
      ...astarCoords,
      ...cplexCoords
    ];

    if (routeCoords.length > 0) {
      const bounds = leafletLib.latLngBounds(routeCoords);
      mapRef.current.fitBounds(bounds, { padding: [80, 80] });
      setShouldFitBounds(false);
      return;
    }

    const markerCoords: [number, number][] = [];
    if (sourceLatLng) markerCoords.push(sourceLatLng as [number, number]);
    if (targetLatLng) markerCoords.push(targetLatLng as [number, number]);

    if (markerCoords.length > 0) {
      mapRef.current.fitBounds(leafletLib.latLngBounds(markerCoords), { padding: [80, 80] });
      setShouldFitBounds(false);
    }
  }, [baselineCoords, resilientCoords, astarCoords, cplexCoords, sourceLatLng, targetLatLng, leafletLib, shouldFitBounds]);

const clearRoutes = () => {
    // Preservar posición actual antes de limpiar resultados
    if (!sourceMarker && baselineCoords.length > 0) {
      setSourceMarker({
        lat: baselineCoords[0][0],
        lon: baselineCoords[0][1],
        label: `Nodo origen ${sourceNode}`
      });
    }
    if (!targetMarker && baselineCoords.length > 0) {
      const last = baselineCoords[baselineCoords.length - 1];
      setTargetMarker({
        lat: last[0],
        lon: last[1],
        label: `Nodo destino ${targetNode}`
      });
    }
    setComparisonData(null);
};

// Componente ligero para escuchar eventos del mapa sin depender de whenCreated
function MapEventBridge({
  onMoveEnd,
  onZoomChange,
  onUserAdjustView,
  mapRef
}: {
  onMoveEnd: () => void;
  onZoomChange: (zoom: number) => void;
  onUserAdjustView: () => void;
  mapRef: React.MutableRefObject<any>;
}) {
  const map = useMapEvents({
    movestart: () => {
      onUserAdjustView();
    },
    zoomstart: () => {
      onUserAdjustView();
    },
    moveend: () => {
      mapRef.current = map;
      onZoomChange(map.getZoom());
      onMoveEnd();
    },
    zoomend: () => {
      mapRef.current = map;
      onZoomChange(map.getZoom());
    }
  });

  useEffect(() => {
    mapRef.current = map;
    onZoomChange(map.getZoom());
  }, [map, onZoomChange]);

  return null;
}


  // Formatear métricas
  const formatDistance = (m: number) => (m / 1000).toFixed(2) + ' km';
  const formatTime = (ms: number) => ms < 1000 ? ms.toFixed(0) + 'ms' : (ms / 1000).toFixed(2) + 's';
  const formatRisk = (r: number) => (r * 100).toFixed(1) + '%';
  const fitToData = () => setShouldFitBounds(true);

  const refreshNodesInView = async () => {
    if (!showNodes || !mapRef.current) return;

    const zoom = mapRef.current.getZoom?.() ?? 0;
    setCurrentZoom(zoom);
    if (zoom < 13) {
      setVisibleNodes([]);
      return;
    }

    const bounds = mapRef.current.getBounds?.();
    if (!bounds) return;

    const south = bounds.getSouth();
    const west = bounds.getWest();
    const north = bounds.getNorth();
    const east = bounds.getEast();
    setNodesInfo(`bbox=${south.toFixed(4)},${west.toFixed(4)},${north.toFixed(4)},${east.toFixed(4)} zoom=${zoom}`);

    setIsLoadingNodes(true);
    try {
      const res = await fetch(`/api/nodes?bbox=${south},${west},${north},${east}&limit=1500`);
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(data?.error || 'Error al obtener nodos');
      }
      if (data?.nodes) {
        setVisibleNodes(data.nodes);
        if (data.nodes.length === 0 && !emptyNodesWarned.current) {
          emptyNodesWarned.current = true;
          toast.info('No hay nodos en esta vista', {
            description: 'Mueve el mapa hacia Santiago (lon -70.83 a -70.46, lat -33.63 a -33.37)',
            duration: 4000
          });
        }
        if (data.nodes.length > 0) {
          emptyNodesWarned.current = false;
        }
      } else {
        setVisibleNodes([]);
        setNodesInfo((prev) => prev ? `${prev} | sin datos` : 'sin datos');
      }
    } catch (err) {
      console.error('Error loading nodes bbox', err);
      toast.error(err instanceof Error ? err.message : 'No se pudieron cargar nodos en vista');
      setVisibleNodes([]);
      setNodesInfo((prev) => prev ? `${prev} | error` : 'error');
    } finally {
      setIsLoadingNodes(false);
    }
  };

  const refreshConnectionsInView = async () => {
    if (!showConnections || !mapRef.current) return;

    const zoom = mapRef.current.getZoom?.() ?? 0;
    if (zoom < 13) {
      setVisibleConnections([]);
      return;
    }

    const bounds = mapRef.current.getBounds?.();
    if (!bounds) return;

    const south = bounds.getSouth();
    const west = bounds.getWest();
    const north = bounds.getNorth();
    const east = bounds.getEast();

    setIsLoadingConnections(true);
    try {
      const res = await fetch(`/api/connections?bbox=${south},${west},${north},${east}&limit=2000`);
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(data?.error || 'Error al obtener conexiones');
      }
      const conns = (data?.connections || []).map((c: any) => ({
        id: c.id,
        coords: extractCoords(c.geom)
      })).filter((c: any) => c.coords.length > 0);
      setVisibleConnections(conns);
    } catch (err) {
      console.error('Error loading connections bbox', err);
      toast.error(err instanceof Error ? err.message : 'No se pudieron cargar conexiones en vista');
      setVisibleConnections([]);
    } finally {
      setIsLoadingConnections(false);
    }
  };

  const refreshLayersInView = async () => {
    await Promise.all([
      refreshNodesInView(),
      refreshConnectionsInView()
    ]);
  };

  // Mantener marcadores de origen/destino siempre visibles al cambiar IDs
  useEffect(() => {
    const src = parseInt(sourceNode, 10);
    const tgt = parseInt(targetNode, 10);
    if (Number.isNaN(src) || Number.isNaN(tgt)) return;
    // Debounce para evitar demasiadas peticiones mientras se escribe
    if (markerUpdateTimeout.current) clearTimeout(markerUpdateTimeout.current);
    markerUpdateTimeout.current = setTimeout(async () => {
      try {
        const params = new URLSearchParams({
          source: src.toString(),
          target: tgt.toString()
        });
        const resp = await fetch(`/api/node/resolve?${params.toString()}`);
        if (!resp.ok) return;
        const data = await resp.json();
        const adjustments = data?.node_adjustments;
        if (adjustments?.source?.resolvedLat != null && adjustments?.source?.resolvedLon != null) {
          setSourceMarker({
            lat: adjustments.source.resolvedLat,
            lon: adjustments.source.resolvedLon,
            label: adjustments.source.snapped
              ? `Snapped → ${adjustments.source.resolved} (desde ${adjustments.source.requested})`
              : `Nodo ${adjustments.source.resolved}`,
            distance: adjustments.source.nearestDistanceM ?? undefined
          });
        }
        if (adjustments?.target?.resolvedLat != null && adjustments?.target?.resolvedLon != null) {
          setTargetMarker({
            lat: adjustments.target.resolvedLat,
            lon: adjustments.target.resolvedLon,
            label: adjustments.target.snapped
              ? `Snapped → ${adjustments.target.resolved} (desde ${adjustments.target.requested})`
              : `Nodo ${adjustments.target.resolved}`,
            distance: adjustments.target.nearestDistanceM ?? undefined
          });
        }
      } catch (err) {
        console.error('No se pudo resolver nodos para marcadores:', err);
      }
    }, 300);
    return () => {
      if (markerUpdateTimeout.current) clearTimeout(markerUpdateTimeout.current);
    };
  }, [sourceNode, targetNode]);

  // Actualizar conexiones cuando el toggle cambia
  useEffect(() => {
    if (showConnections) {
      refreshConnectionsInView();
    } else {
      setVisibleConnections([]);
    }
  }, [showConnections]);

  const setDestinationFromPosition = async (lat: number, lon: number, label?: string) => {
    try {
      const { data, error } = await supabase.rpc('find_nearest_node', {
        p_lat: lat,
        p_lon: lon
      });
      if (error) throw error;
      if (data && data.length > 0) {
        const nearest = data[0];
        setTargetNode(nearest.node_id.toString());
        setTargetMarker({
          lat: nearest.node_lat ?? lat,
          lon: nearest.node_lon ?? lon,
          label: label || 'Destino fijado',
          distance: nearest.distance_m
        });
        clearRoutes();
        toast.success('Destino actualizado', {
          description: `Nodo ${nearest.node_id} a ${nearest.distance_m.toFixed(0)} m`
        });
      } else {
        toast.warning('No se encontró nodo conectado cerca de ese punto');
      }
    } catch (err: any) {
      console.error('Error fijando destino desde mapa:', err);
      toast.error('No se pudo fijar destino', { description: err.message });
    }
  };

  // Recargar nodos al cambiar la vista o al activar la capa
  useEffect(() => {
    if (!showNodes) {
      setVisibleNodes([]);
      return;
    }
    if (!mapReady || !mapRef.current) return;
    refreshNodesInView();
  }, [showNodes, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;
    const map = mapRef.current;
    const updateZoom = () => setCurrentZoom(map.getZoom?.() ?? null);
    updateZoom();
    map.on?.('zoomend', updateZoom);
    return () => {
      map.off?.('zoomend', updateZoom);
    };
  }, [mapReady]);

  return (
    <div className="w-full h-screen flex dark bg-background text-foreground">
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
                      onChange={(e) => setSourceNode(e.target.value)}
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
                    onChange={(e) => setTargetNode(e.target.value)}
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
                    onNodeSelected={({ nodeId, address, distance, lat, lon }) => {
                      setSourceNode(nodeId.toString());
                      setSourceMarker({ lat, lon, label: address, distance });
                      clearRoutes();
                    }}
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-sm text-gray-600">
                    O buscar destino por dirección:
                  </Label>
                  <AddressInput
                    placeholder="Ej: Mall Parque Arauco, Las Condes"
                    onNodeSelected={({ nodeId, address, distance, lat, lon }) => {
                      setTargetNode(nodeId.toString());
                      setTargetMarker({ lat, lon, label: address, distance });
                      clearRoutes();
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

                <div className="space-y-2">
                  <Label htmlFor="maxtime" className="text-sm">
                    Tiempo máximo estimado (min)
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="maxtime"
                      type="number"
                      step="1"
                      min="0"
                      placeholder="Ej: 30"
                      value={maxTimeMinutes ?? ''}
                      onChange={(e) => setMaxTimeMinutes(e.target.value ? parseFloat(e.target.value) : null)}
                      className="flex-1"
                    />
                    {maxTimeMinutes !== null && (
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setMaxTimeMinutes(null)}
                      >
                        ✕
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    Se convierte a distancia usando ~30 km/h. Si también defines distancia, usamos el menor límite.
                  </p>
                </div>

                <div className="flex items-start gap-3 pt-1">
                  <Checkbox
                    id="avoidflood"
                    checked={avoidFloodZones}
                    onCheckedChange={(checked) => setAvoidFloodZones(checked as boolean)}
                  />
                  <div className="space-y-1">
                    <Label htmlFor="avoidflood" className="text-sm">
                      Evitar zonas de inundación
                    </Label>
                    <p className="text-xs text-gray-500">
                      Filtra aristas con p_fallo &gt;= 0.30 para rutas calculadas.
                    </p>
                  </div>
                </div>
              </div>

              <Button
                className="w-full"
                onClick={compareRoutes}
                disabled={isLoading || !sourceNode || !targetNode}
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
                  id="cplex"
                  checked={showCplex}
                  onCheckedChange={(checked) => setShowCplex(checked as boolean)}
                />
                <Label htmlFor="cplex" className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-emerald-500"></div>
                  MILP (CPLEX)
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
                  A* Resiliente
                </Label>
              </div>


            </CardContent>
          </Card>

          {/* Nodos en vista */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Nodos</CardTitle>
              <CardDescription>Mostrar nodos visibles (zoom ≥ 13)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="shownodes"
                  checked={showNodes}
                  onCheckedChange={(checked) => setShowNodes(!!checked)}
                />
                <Label htmlFor="shownodes" className="flex-1">
                  Mostrar nodos en la vista actual
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Se limita a 1500 nodos por vista. Acerca el zoom para ver IDs.
              </p>
              <p className="text-xs text-muted-foreground">
                Cobertura actual de datos: Santiago (lon -70.83 a -70.46, lat -33.63 a -33.37).
              </p>
              <p className="text-xs text-muted-foreground">
                Zoom actual: {currentZoom} (mínimo 13 para mostrar nodos).
              </p>
              {nodesInfo && (
                <p className="text-[10px] text-muted-foreground">
                  Última consulta: {nodesInfo}
                </p>
              )}
              {showNodes && (
                <div className="text-xs text-muted-foreground">
                  {isLoadingNodes ? 'Cargando nodos...' : `Mostrando ${visibleNodes.length} nodos`}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Conexiones en vista */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Conexiones</CardTitle>
              <CardDescription>Mostrar aristas en la vista (zoom ≥ 13)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="showconnections"
                  checked={showConnections}
                  onCheckedChange={(checked) => setShowConnections(!!checked)}
                />
                <Label htmlFor="showconnections" className="flex-1">
                  Mostrar conexiones (límite 2000)
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Útil para ver la conectividad de la red en el área actual.
              </p>
              {showConnections && (
                <div className="text-xs text-muted-foreground">
                  {isLoadingConnections ? 'Cargando conexiones...' : `Mostrando ${visibleConnections.length} conexiones`}
                </div>
              )}
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
                <div className="w-2 h-2 rounded-full bg-blue-500" />
                <Label className="text-sm">
                  Zonas de Inundación
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                <Label className="text-sm">
                  Reportes Ciudadanos
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-cyan-500" />
                <Label className="text-sm">
                  Estaciones DGA
                </Label>
              </div>

              {simulationActive && (
                <div className="flex items-start space-x-3 pt-2 border-t">
                  <Checkbox
                    id="onlySimulated"
                    checked={onlySimulatedThreats}
                    onCheckedChange={(checked) => setOnlySimulatedThreats(checked as boolean)}
                  />
                  <div className="space-y-1">
                    <Label htmlFor="onlySimulated" className="text-sm">
                      Mostrar solo amenazas simuladas
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Oculta capas base y muestra fallas activas de la simulación.
                    </p>
                  </div>
                </div>
              )}
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
                  {/* Statistics removed as requested */}
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
                      <TableCell className="font-medium">MILP (CPLEX)</TableCell>
                      <TableCell>{formatDistance(comparisonData.cplex?.metrics?.distance_m || 0)}</TableCell>
                      <TableCell>{formatTime(comparisonData.cplex?.metrics?.computation_time_ms || 0)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.cplex?.metrics?.risk_score || 0)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">A* (Metaheurística)</TableCell>
                      <TableCell>{formatDistance(comparisonData.astar?.metrics?.distance_m || 0)}</TableCell>
                      <TableCell>{formatTime(comparisonData.astar?.metrics?.computation_time_ms || 0)}</TableCell>
                      <TableCell>{formatRisk(comparisonData.astar?.metrics?.risk_score || 0)}</TableCell>
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
          whenCreated={(mapInstance) => {
            mapRef.current = mapInstance;
            setMapReady(true);
            setCurrentZoom(mapInstance.getZoom?.() ?? null);
            mapInstance.on('mousemove', (e: any) => {
              setLastMouseLatLng({ lat: e.latlng.lat, lon: e.latlng.lng });
            });
          }}
        >
          {/* Bridge to listen map events reliably */}
          <MapEventBridge
            onMoveEnd={refreshLayersInView}
            onZoomChange={setCurrentZoom}
            onUserAdjustView={() => setShouldFitBounds(false)}
            mapRef={mapRef}
          />
          <TileLayer
            className="filter brightness-[1.2] contrast-[0.9]"
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
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

          {showCplex && cplexCoords.length > 0 && (
            <Polyline
              positions={cplexCoords}
              pathOptions={{ color: '#10b981', weight: 4, opacity: 0.7 }}
            />
          )}

          {showAstar && astarCoords.length > 0 && (
            <Polyline
              positions={astarCoords}
              pathOptions={{ color: '#a855f7', weight: 4, opacity: 0.7 }}
            />
          )}

          {/* Conexiones de la red */}
          {showConnections && visibleConnections.map((conn) => (
            <Polyline
              key={`conn-${conn.id}`}
              positions={conn.coords}
              pathOptions={{ color: '#6b7280', weight: 2, opacity: 0.4 }}
            />
          ))}

          {/* Nodos visibles en la vista */}
          {showNodes && visibleNodes.map((n) => (
            <CircleMarker
              key={`node-${n.id}`}
              center={[n.lat, n.lon]}
              radius={4}
              pathOptions={{ color: '#38bdf8', fillColor: '#38bdf8', fillOpacity: 0.8, weight: 1 }}
            >
              <Tooltip direction="top" offset={[0, -4]} opacity={0.95} className="text-xs">
                {n.id}
              </Tooltip>
            </CircleMarker>
          ))}



          {/* Inundaciones históricas */}
          {showInundaciones && !onlySimulatedThreats && inundaciones.map((item, idx) => {
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
          {showReportes && !onlySimulatedThreats && reportes.map((item, idx) => {
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
          {showDgaStations && !onlySimulatedThreats && dgaStations.map((station: any, idx) => {
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



          {/* Visualización de Fallas Simuladas */}
          {/* Zona inundada (buffer alrededor de nodos fallidos) */}
          {simulationActive && simulationEntities.map((entity, idx) => {
            if (!entity.is_failed || !entity.geom || entity.entity_type !== 'nodo') return null;

            const coords = extractCoords(entity.geom);
            if (coords.length === 0) return null;

            return (
              <Circle
                key={`flood-zone-${idx}`}
                center={coords[0]}
                radius={150} // 150 metros de radio para la zona inundada
                pathOptions={{
                  color: '#ff6b6b',
                  fillColor: '#ff6b6b',
                  fillOpacity: 0.15,
                  weight: 1,
                  opacity: 0.3
                }}
              />
            );
          })}

          {/* Nodos y aristas fallidos */}
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
          {sourceLatLng && (
            <CircleMarker
              center={sourceLatLng as [number, number]}
              radius={15}
              pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.8, weight: 3 }}
            >
              <Popup>
                <b>🟢 Nodo Origen</b><br />
                ID: {sourceNode}<br />
                {sourceMarker?.label && <>Dir: {sourceMarker.label}<br /></>}
                {sourceMarker?.distance !== undefined && <>Dist: {sourceMarker.distance.toFixed(0)} m<br /></>}
              </Popup>
            </CircleMarker>
          )}

          {/* Marcador de nodo destino */}
          {targetLatLng && (
            <CircleMarker
              center={targetLatLng as [number, number]}
              radius={15}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.8, weight: 3 }}
            >
              <Popup>
                <b>🔴 Nodo Destino</b><br />
                ID: {targetNode}<br />
                {targetMarker?.label && <>Dir: {targetMarker.label}<br /></>}
                {targetMarker?.distance !== undefined && <>Dist: {targetMarker.distance.toFixed(0)} m<br /></>}
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>

        <div className="absolute top-4 right-4 z-[1000] flex gap-2">
          <Button size="sm" variant="secondary" onClick={fitToData}>
            Ajustar vista
          </Button>
        </div>

        {/* Leyenda en el mapa */}
        <div className="absolute bottom-4 right-4 z-[1000] bg-background p-4 rounded-lg shadow-lg border border-border">
          <h3 className="font-semibold mb-2 text-sm text-foreground">Leyenda de Rutas</h3>
          <div className="space-y-1 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-blue-500"></div>
              <span>Baseline (más corta)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-orange-500"></div>
              <span>Resiliente (ajustada)</span>
            </div>


          </div>
        </div>
      </div>

    </div>
  );
}
