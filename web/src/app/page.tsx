/**
 * Página principal (Next.js App Router)
 * 
 * Muestra un mapa de Leaflet con capas de infraestructura, metadata y amenazas.
 * Consume la API /api/route para mostrar rutas calculadas con pgr_dijkstra.
 */
'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Importar Leaflet de forma dinámica para evitar SSR issues
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });

export default function HomePage() {
  const [route, setRoute] = useState<any>(null);

  useEffect(() => {
    // Cargar la ruta desde la API
    fetch('/api/route')
      .then(res => res.json())
      .then(data => setRoute(data))
      .catch(err => console.error('Error cargando ruta:', err));
  }, []);

  return (
    <div className="w-full h-screen">
      <h1 className="absolute top-4 left-4 z-10 bg-white px-4 py-2 rounded shadow">
        Ruteo Resiliente - Fase 2
      </h1>
      <MapContainer
        center={[-33.45, -70.65]}
        zoom={13}
        className="w-full h-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {route && (
          <Marker position={[-33.45, -70.65]}>
            <Popup>
              Ruta calculada: {JSON.stringify(route)}
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
