/**
 * Componente: AddressInput
 * 
 * Input de dirección textual con autocomplete y geocodificación.
 * 
 * Features:
 * - Debounce de 500ms para evitar muchas llamadas a API
 * - Dropdown con sugerencias de Nominatim
 * - Selección que encuentra el nodo más cercano
 * - Loading states y manejo de errores
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Search, MapPin, Loader2, X } from 'lucide-react';

interface AddressResult {
  display_name: string;
  lat: number;
  lon: number;
  address: {
    road: string;
    house_number: string;
    suburb: string;
    city: string;
    region: string;
    country: string;
  };
}

interface AddressInputProps {
  onNodeSelected: (payload: {
    nodeId: number;
    address: string;
    distance: number;
    lat: number;
    lon: number;
  }) => void;
  placeholder?: string;
  label?: string;
}

export function AddressInput({ 
  onNodeSelected, 
  placeholder = "Ej: Av. Providencia 1234",
  label = "Buscar dirección"
}: AddressInputProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AddressResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isFindingNode, setIsFindingNode] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAddress, setSelectedAddress] = useState<string | null>(null);
  
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Debounced search
  const searchAddress = useCallback(async (searchQuery: string) => {
    if (searchQuery.trim().length < 3) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/geocode?q=${encodeURIComponent(searchQuery)}`
      );

      const data = await response.json();

      if (data.success) {
        setResults(data.results || []);
        setShowDropdown(data.results.length > 0);
      } else {
        setError(data.error || 'Error al buscar dirección');
        setResults([]);
        setShowDropdown(false);
      }
    } catch (err: any) {
      console.error('Error en búsqueda:', err);
      setError('Error de conexión');
      setResults([]);
      setShowDropdown(false);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Debounce effect
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (query.trim().length >= 3) {
      debounceTimer.current = setTimeout(() => {
        searchAddress(query);
      }, 500); // 500ms debounce
    } else {
      setResults([]);
      setShowDropdown(false);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, searchAddress]);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Seleccionar una dirección y encontrar nodo más cercano
  const handleSelectAddress = async (result: AddressResult) => {
    setIsFindingNode(true);
    setShowDropdown(false);
    setSelectedAddress(result.display_name);
    setQuery(result.display_name);

    try {
      // Llamar a find_nearest_node via API local
      const response = await fetch(`/api/node/nearest?lat=${result.lat}&lon=${result.lon}`);
      const apiResult = await response.json();

      if (!response.ok || !apiResult.success || !apiResult.data || apiResult.data.length === 0) {
        console.error('Error al buscar nodo cercano:', apiResult.error || 'Sin resultados');
        setIsFindingNode(false);
        return;
      }

      const nearestNode = apiResult.data[0];

      // Callback al padre con el nodo seleccionado
      onNodeSelected({
        nodeId: nearestNode.node_id,
        address: result.display_name,
        distance: nearestNode.distance_m,
        lat: nearestNode.node_lat ?? result.lat,
        lon: nearestNode.node_lon ?? result.lon
      });

      console.log(
        `Direccion encontrada: ${result.display_name}. ` +
        `Nodo: ${nearestNode.node_id}, Distancia: ${nearestNode.distance_m.toFixed(0)}m`
      );

    } catch (err: any) {
      console.error('Error al encontrar nodo:', err);
      alert(`❌ Error: ${err.message}`);
    } finally {
      setIsFindingNode(false);
    }
  };

  // Limpiar búsqueda
  const handleClear = () => {
    setQuery('');
    setResults([]);
    setShowDropdown(false);
    setSelectedAddress(null);
    setError(null);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isFindingNode}
            className="pr-8"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        
        <Button
          type="button"
          size="icon"
          variant="outline"
          disabled={isSearching || isFindingNode || query.trim().length < 3}
          onClick={() => searchAddress(query)}
        >
          {isSearching || isFindingNode ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Searching indicator */}
      {isSearching && (
        <div className="mt-1 text-sm text-gray-500">
          Buscando direcciones...
        </div>
      )}

      {/* Dropdown con resultados */}
      {showDropdown && results.length > 0 && (
        <Card className="absolute z-50 w-full mt-1 max-h-80 overflow-y-auto">
          <div className="divide-y">
            {results.map((result, index) => (
              <button
                key={index}
                onClick={() => handleSelectAddress(result)}
                className="w-full p-3 text-left hover:bg-gray-800 transition-colors"
                type="button"
              >
                <div className="flex items-start gap-2">
                  <MapPin className="h-4 w-4 mt-1 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">
                      {result.address.road} {result.address.house_number}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {result.address.suburb && `${result.address.suburb}, `}
                      {result.address.city}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {result.lat.toFixed(4)}, {result.lon.toFixed(4)}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* No results */}
      {showDropdown && results.length === 0 && !isSearching && query.length >= 3 && (
        <Card className="absolute z-50 w-full mt-1 p-3">
          <div className="text-sm text-gray-500 text-center">
            No se encontraron direcciones para "{query}"
          </div>
        </Card>
      )}
    </div>
  );
}
