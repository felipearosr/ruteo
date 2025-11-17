/**
 * Página principal (Next.js App Router)
 * 
 * Muestra un mapa de Leaflet con capas de infraestructura, metadata y amenazas.
 * Consume la API /api/route para mostrar rutas calculadas con pgr_dijkstra.
 */
'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { createClient } from '@supabase/supabase-js';

// Importar Leaflet de forma dinámica para evitar SSR issues
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const GeoJSON = dynamic(() => import('react-leaflet').then(mod => mod.GeoJSON), { ssr: false });
const Polyline = dynamic(() => import('react-leaflet').then(mod => mod.Polyline), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });
const CircleMarker = dynamic(() => import('react-leaflet').then(mod => mod.CircleMarker), { ssr: false });

// Cliente de Supabase para el navegador
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default function HomePage() {
  // Estado para capas y datos
  const [route, setRoute] = useState<any>(null);
  const [elevacion, setElevacion] = useState<any[]>([]);
  const [lluvia, setLluvia] = useState<any[]>([]);
  const [landcover, setLandcover] = useState<any[]>([]);
  const [dgaStations, setDgaStations] = useState<any[]>([]);
  const [inundaciones, setInundaciones] = useState<any[]>([]);
  const [reportes, setReportes] = useState<any[]>([]);
  
  // Estado para controles de capas
  const [showElevacion, setShowElevacion] = useState(false);
  const [showLluvia, setShowLluvia] = useState(false);
  const [showLandcover, setShowLandcover] = useState(false);
  const [showDGA, setShowDGA] = useState(false);
  const [showInundaciones, setShowInundaciones] = useState(true);
  const [showReportes, setShowReportes] = useState(true);
  const [showRoute, setShowRoute] = useState(true);

  // Nodos de origen/destino para routing (configurables)
  const [sourceNode, setSourceNode] = useState(1);
  const [targetNode, setTargetNode] = useState(100);

  useEffect(() => {
    // Cargar datos de metadata
    supabase.from('meta_elevacion').select('*').then(({ data }) => {
      if (data) setElevacion(data);
    });

    supabase.from('meta_lluvia').select('*').then(({ data }) => {
      if (data) setLluvia(data);
    });

    supabase.from('meta_landcover').select('*').then(({ data }) => {
      if (data) setLandcover(data);
    });

    // Cargar datos de amenazas
    supabase.from('amenaza_dga').select('*').then(({ data }) => {
      if (data) setDgaStations(data);
    });

    supabase.from('amenaza_inundaciones_hist').select('*').then(({ data }) => {
      if (data) setInundaciones(data);
    });

    supabase.from('amenaza_reportes_ciudadanos').select('*').then(({ data }) => {
      if (data) setReportes(data);
    });
  }, []);

  // Función para calcular ruta
  const calculateRoute = () => {
    fetch(`/api/route?source=${sourceNode}&target=${targetNode}`)
      .then(res => res.json())
      .then(data => {
        setRoute(data);
        console.log('Ruta calculada:', data);
      })
      .catch(err => console.error('Error calculando ruta:', err));
  };

  useEffect(() => {
    calculateRoute();
  }, [sourceNode, targetNode]);

  // Extraer coordenadas de geometría GeoJSON
  const extractCoords = (geom: any): [number, number][] => {
    if (!geom) return [];
    
    // Si es objeto con coordinates
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

  // Convertir ruta a coordenadas
  const routeCoords = route?.features
    ?.map((f: any) => extractCoords(f.geometry))
    .flat()
    .filter((c: any) => c.length === 2) || [];

  return (
    <div className="w-full h-screen relative">
      {/* Título */}
      <div className="absolute top-4 left-4 z-[1000] bg-white px-4 py-2 rounded shadow-lg">
        <h1 className="text-xl font-bold">Ruteo Resiliente - Fase 2</h1>
        <p className="text-sm text-gray-600">Santiago, Chile</p>
      </div>

      {/* Panel de control */}
      <div className="absolute top-4 right-4 z-[1000] bg-white p-4 rounded shadow-lg max-w-xs">
        <h2 className="font-bold mb-2">Capas</h2>
        
        <div className="space-y-1 mb-4">
          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showRoute} 
              onChange={(e) => setShowRoute(e.target.checked)}
              className="mr-2"
            />
            <span className="text-blue-600 font-semibold">● Ruta Calculada</span>
          </label>
          
          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showInundaciones} 
              onChange={(e) => setShowInundaciones(e.target.checked)}
              className="mr-2"
            />
            <span className="text-red-600">■ Inundaciones Históricas</span>
          </label>
          
          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showReportes} 
              onChange={(e) => setShowReportes(e.target.checked)}
              className="mr-2"
            />
            <span className="text-orange-600">▲ Reportes Ciudadanos</span>
          </label>

          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showDGA} 
              onChange={(e) => setShowDGA(e.target.checked)}
              className="mr-2"
            />
            <span className="text-blue-800">● Estaciones DGA</span>
          </label>

          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showElevacion} 
              onChange={(e) => setShowElevacion(e.target.checked)}
              className="mr-2"
            />
            <span className="text-green-600">● Elevación</span>
          </label>

          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showLluvia} 
              onChange={(e) => setShowLluvia(e.target.checked)}
              className="mr-2"
            />
            <span className="text-cyan-600">● Lluvia</span>
          </label>

          <label className="flex items-center text-sm">
            <input 
              type="checkbox" 
              checked={showLandcover} 
              onChange={(e) => setShowLandcover(e.target.checked)}
              className="mr-2"
            />
            <span className="text-yellow-600">● Cobertura Suelo</span>
          </label>
        </div>

        <div className="border-t pt-3">
          <h3 className="font-bold mb-2 text-sm">Calcular Ruta</h3>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-gray-600">Nodo Origen</label>
              <input 
                type="number" 
                value={sourceNode}
                onChange={(e) => setSourceNode(parseInt(e.target.value) || 1)}
                className="w-full px-2 py-1 border rounded text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600">Nodo Destino</label>
              <input 
                type="number" 
                value={targetNode}
                onChange={(e) => setTargetNode(parseInt(e.target.value) || 100)}
                className="w-full px-2 py-1 border rounded text-sm"
              />
            </div>
            <button 
              onClick={calculateRoute}
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm"
            >
              Calcular Ruta
            </button>
          </div>
          
          {route && route.features && route.features.length > 0 && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
              <p>✓ Ruta encontrada</p>
              <p>Segmentos: {route.features.length}</p>
            </div>
          )}
        </div>
      </div>

      {/* Mapa */}
      <MapContainer
        center={[-33.45, -70.65]}
        zoom={13}
        className="w-full h-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* Ruta calculada */}
        {showRoute && routeCoords.length > 0 && (
          <Polyline 
            positions={routeCoords}
            pathOptions={{ color: 'blue', weight: 4, opacity: 0.7 }}
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

        {/* Elevación */}
        {showElevacion && elevacion.map((item, idx) => {
          const coords = extractCoords(item.geom);
          if (coords.length === 0) return null;
          return (
            <CircleMarker 
              key={`elev-${idx}`}
              center={coords[0]}
              radius={5}
              pathOptions={{ color: 'green', fillColor: 'lightgreen', fillOpacity: 0.5 }}
            >
              <Popup>
                <b>Elevación</b><br/>
                Altura: {item.elevation_m || 'N/A'}m
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Lluvia */}
        {showLluvia && lluvia.map((item, idx) => {
          const coords = extractCoords(item.geom);
          if (coords.length === 0) return null;
          return (
            <CircleMarker 
              key={`lluv-${idx}`}
              center={coords[0]}
              radius={5}
              pathOptions={{ color: 'cyan', fillColor: 'lightcyan', fillOpacity: 0.5 }}
            >
              <Popup>
                <b>Precipitación</b><br/>
                Lluvia: {item.rainfall_mm || 'N/A'}mm
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Landcover */}
        {showLandcover && landcover.map((item, idx) => {
          const coords = extractCoords(item.geom);
          if (coords.length === 0) return null;
          return (
            <CircleMarker 
              key={`land-${idx}`}
              center={coords[0]}
              radius={5}
              pathOptions={{ color: 'yellow', fillColor: 'lightyellow', fillOpacity: 0.5 }}
            >
              <Popup>
                <b>Cobertura de Suelo</b><br/>
                Tipo: {item.landcover_type || 'N/A'}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
