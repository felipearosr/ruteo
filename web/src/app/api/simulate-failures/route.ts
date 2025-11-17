/**
 * API Endpoint: Simulación de Fallas Dinámicas
 * 
 * POST: Genera fallas aleatorias basadas en probabilidades
 * DELETE: Limpia simulaciones activas
 * GET: Obtiene estado de simulación activa
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * POST - Generar nueva simulación de fallas
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { seed, min_probability = 0.01 } = body;
    
    // Generar ID único para esta simulación
    const simulationId = uuidv4();
    
    // Implementar random con seed si se proporciona
    let random = Math.random;
    if (seed !== undefined && seed !== null) {
      // Seeded random usando algoritmo simple
      let seedValue = seed;
      random = () => {
        seedValue = (seedValue * 9301 + 49297) % 233280;
        return seedValue / 233280;
      };
    }
    
    // Obtener nodos con probabilidad > umbral
    const { data: nodos, error: nodosError } = await supabase
      .from('infra_nodos')
      .select('id, p_fallo_nodo')
      .gt('p_fallo_nodo', min_probability);
    
    if (nodosError) {
      throw new Error(`Error al obtener nodos: ${nodosError.message}`);
    }
    
    // Obtener aristas con probabilidad > umbral
    const { data: aristas, error: aristasError } = await supabase
      .from('infra_aristas')
      .select('id, p_fallo_arista')
      .gt('p_fallo_arista', min_probability);
    
    if (aristasError) {
      throw new Error(`Error al obtener aristas: ${aristasError.message}`);
    }
    
    const simulaciones = [];
    
    // Simular fallas en nodos
    let nodosFailedCount = 0;
    for (const nodo of nodos || []) {
      const randomValue = random();
      const isFailed = randomValue < nodo.p_fallo_nodo;
      
      if (isFailed) nodosFailedCount++;
      
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
    let aristasFailedCount = 0;
    for (const arista of aristas || []) {
      const randomValue = random();
      const isFailed = randomValue < arista.p_fallo_arista;
      
      if (isFailed) aristasFailedCount++;
      
      simulaciones.push({
        simulation_id: simulationId,
        entity_type: 'arista',
        entity_id: arista.id,
        p_fallo: arista.p_fallo_arista,
        random_value: randomValue,
        is_failed: isFailed
      });
    }
    
    // Guardar en BD (en lotes de 1000)
    const batchSize = 1000;
    for (let i = 0; i < simulaciones.length; i += batchSize) {
      const batch = simulaciones.slice(i, i + batchSize);
      const { error: insertError } = await supabase
        .from('sim_fallas_activas')
        .insert(batch);
      
      if (insertError) {
        throw new Error(`Error al insertar simulaciones: ${insertError.message}`);
      }
    }
    
    return NextResponse.json({
      success: true,
      simulation_id: simulationId,
      summary: {
        total_nodos: nodos?.length || 0,
        nodos_failed: nodosFailedCount,
        nodos_failure_rate: nodos?.length ? (nodosFailedCount / nodos.length * 100).toFixed(1) : '0',
        total_aristas: aristas?.length || 0,
        aristas_failed: aristasFailedCount,
        aristas_failure_rate: aristas?.length ? (aristasFailedCount / aristas.length * 100).toFixed(1) : '0',
        total_entities: (nodos?.length || 0) + (aristas?.length || 0),
        total_failed: nodosFailedCount + aristasFailedCount
      },
      timestamp: new Date().toISOString(),
      seed: seed
    });
    
  } catch (error: any) {
    console.error('Error en simulación:', error);
    return NextResponse.json(
      { 
        success: false,
        error: error.message 
      },
      { status: 500 }
    );
  }
}

/**
 * DELETE - Limpiar simulaciones
 */
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const simulationId = searchParams.get('simulation_id');
    
    if (simulationId) {
      // Eliminar simulación específica
      const { error } = await supabase
        .from('sim_fallas_activas')
        .delete()
        .eq('simulation_id', simulationId);
      
      if (error) {
        throw new Error(`Error al eliminar simulación: ${error.message}`);
      }
      
      return NextResponse.json({ 
        success: true,
        message: `Simulación ${simulationId} eliminada` 
      });
    } else {
      // Eliminar todas las simulaciones
      const { error } = await supabase
        .from('sim_fallas_activas')
        .delete()
        .neq('id', 0); // Truco para borrar todas las filas
      
      if (error) {
        throw new Error(`Error al limpiar simulaciones: ${error.message}`);
      }
      
      return NextResponse.json({ 
        success: true,
        message: 'Todas las simulaciones eliminadas' 
      });
    }
    
  } catch (error: any) {
    console.error('Error al eliminar simulación:', error);
    return NextResponse.json(
      { 
        success: false,
        error: error.message 
      },
      { status: 500 }
    );
  }
}

/**
 * GET - Obtener estado de simulaciones activas
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const simulationId = searchParams.get('simulation_id');
    
    if (simulationId) {
      // Obtener simulación específica
      const { data, error } = await supabase
        .from('sim_fallas_activas')
        .select('*')
        .eq('simulation_id', simulationId);
      
      if (error) {
        throw new Error(`Error al obtener simulación: ${error.message}`);
      }
      
      const nodosData = data?.filter(s => s.entity_type === 'nodo') || [];
      const aristasData = data?.filter(s => s.entity_type === 'arista') || [];
      
      return NextResponse.json({
        success: true,
        simulation_id: simulationId,
        summary: {
          total_nodos: nodosData.length,
          nodos_failed: nodosData.filter(n => n.is_failed).length,
          total_aristas: aristasData.length,
          aristas_failed: aristasData.filter(a => a.is_failed).length
        },
        entities: data
      });
    } else {
      // Listar todas las simulaciones (solo IDs únicos)
      const { data, error } = await supabase
        .from('sim_fallas_activas')
        .select('simulation_id, created_at')
        .order('created_at', { ascending: false });
      
      if (error) {
        throw new Error(`Error al listar simulaciones: ${error.message}`);
      }
      
      // Agrupar por simulation_id
      const uniqueSimulations = Array.from(
        new Map(data?.map(item => [item.simulation_id, item])).values()
      );
      
      return NextResponse.json({
        success: true,
        simulations: uniqueSimulations
      });
    }
    
  } catch (error: any) {
    console.error('Error al obtener simulación:', error);
    return NextResponse.json(
      { 
        success: false,
        error: error.message 
      },
      { status: 500 }
    );
  }
}
