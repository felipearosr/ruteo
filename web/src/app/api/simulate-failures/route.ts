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
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

/**
 * POST - Generar nueva simulación de fallas
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { seed, min_probability = 0.01, propagation_probability = 0.8, max_steps = 50 } = body;

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

    console.log(`[PROPAGATION] Starting simulation ${simulationId}`);

    // 1. Obtener nodos semilla (initial failures based on probability)
    const { data: nodos, error: nodosError } = await supabase
      .from('infra_nodos')
      .select('id, p_fallo_nodo')
      .gt('p_fallo_nodo', min_probability);

    if (nodosError) {
      throw new Error(`Error al obtener nodos: ${nodosError.message}`);
    }

    const failedNodeIds = new Set<number>();
    const failedEdgeIds = new Set<number>();
    const processedEdgeIds = new Set<number>();
    const queue: number[] = [];
    const simulaciones = [];

    // 2. Determinar fallas iniciales (Semillas)
    let nodosFailedCount = 0;
    for (const nodo of nodos || []) {
      const randomValue = random();
      const isFailed = randomValue < nodo.p_fallo_nodo;

      if (isFailed) {
        nodosFailedCount++;
        failedNodeIds.add(nodo.id);
        queue.push(nodo.id);

        simulaciones.push({
          simulation_id: simulationId,
          entity_type: 'nodo',
          entity_id: nodo.id,
          p_fallo: nodo.p_fallo_nodo,
          random_value: randomValue,
          is_failed: true
        });
      }
    }

    console.log(`[PROPAGATION] Initial seeds: ${nodosFailedCount}`);

    // 3. Propagación tipo "agua" (BFS con fetch on-demand)
    let propagatedCount = 0;
    let step = 0;

    while (queue.length > 0 && step < max_steps) {
      step++;
      const batchSize = Math.min(queue.length, 10); // Process up to 10 nodes at a time
      const currentBatch = queue.splice(0, batchSize);

      console.log(`[PROPAGATION] Step ${step}: Processing ${currentBatch.length} nodes, queue size: ${queue.length}`);

      // Fetch neighbors for this batch of nodes
      // We query edges where source OR target is in currentBatch
      const { data: edges, error: edgesError } = await supabase
        .from('infra_aristas')
        .select('id, source, target')
        .or(`source.in.(${currentBatch.join(',')}),target.in.(${currentBatch.join(',')})`);

      if (edgesError) {
        console.error(`Error fetching neighbors:`, edgesError);
        throw new Error(`Error al obtener vecinos: ${edgesError.message}`);
      }

      edges?.forEach(edge => processedEdgeIds.add(edge.id));

      // Process each edge to find neighbors
      for (const edge of edges || []) {
        // Determine which end is the neighbor
        for (const currentId of currentBatch) {
          let neighborId: number | null = null;

          if (edge.source === currentId) {
            neighborId = edge.target;
          } else if (edge.target === currentId) {
            neighborId = edge.source;
          }

          if (neighborId && !failedNodeIds.has(neighborId)) {
            // Evaluar propagación
            const randomValue = random();
            if (randomValue < propagation_probability) {
              failedNodeIds.add(neighborId);
              queue.push(neighborId);
              propagatedCount++;

              simulaciones.push({
                simulation_id: simulationId,
                entity_type: 'nodo',
                entity_id: neighborId,
                p_fallo: propagation_probability,
                random_value: randomValue,
                is_failed: true
              });

              // Fail the connecting edge
              if (!failedEdgeIds.has(edge.id)) {
                failedEdgeIds.add(edge.id);
                simulaciones.push({
                  simulation_id: simulationId,
                  entity_type: 'arista',
                  entity_id: edge.id,
                  p_fallo: propagation_probability,
                  random_value: randomValue,
                  is_failed: true
                });
              }
            }
          }
        }
      }
    }

    console.log(`[PROPAGATION] Completed: ${propagatedCount} nodes propagated in ${step} steps`);

    // 4. Guardar en BD (en lotes de 1000)
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

    const totalNodesChecked = nodos?.length ?? 0;
    const totalEntitiesFailed = failedNodeIds.size + failedEdgeIds.size;
    const totalEdgesProcessed = processedEdgeIds.size;

    return NextResponse.json({
      success: true,
      simulation_id: simulationId,
      summary: {
        total_nodos_checked: totalNodesChecked,
        initial_seeds: nodosFailedCount,
        propagated_nodes: propagatedCount,
        total_nodes_failed: failedNodeIds.size,
        total_edges_failed: failedEdgeIds.size,
        total_failed: totalEntitiesFailed,
        total_entities: totalEntitiesFailed,
        nodos_failed: failedNodeIds.size,
        total_nodos: totalNodesChecked,
        aristas_failed: failedEdgeIds.size,
        total_aristas: totalEdgesProcessed,
        steps: step,
        note: 'Simulación con propagación tipo agua completada'
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
      const { data: simulationData, error: simulationError } = await supabase
        .from('sim_fallas_activas')
        .select('*')
        .eq('simulation_id', simulationId);

      if (simulationError) {
        throw new Error(`Error al obtener simulación: ${simulationError.message}`);
      }

      const nodosData = simulationData?.filter(s => s.entity_type === 'nodo') || [];
      const aristasData = simulationData?.filter(s => s.entity_type === 'arista') || [];

      // Obtener geometrías de nodos
      let nodesWithGeom = [];
      if (nodosData.length > 0) {
        const nodeIds = nodosData.map(n => n.entity_id);
        const { data: nodesGeom } = await supabase
          .from('infra_nodos')
          .select('id, geom')
          .in('id', nodeIds);

        // Map geometries to simulation data
        const geomMap = new Map(nodesGeom?.map(n => [n.id, n.geom]));
        nodesWithGeom = nodosData.map(n => ({
          ...n,
          geom: geomMap.get(n.entity_id)
        }));
      }

      // Obtener geometrías de aristas
      let edgesWithGeom = [];
      if (aristasData.length > 0) {
        const edgeIds = aristasData.map(a => a.entity_id);
        const { data: edgesGeom } = await supabase
          .from('infra_aristas')
          .select('id, geom')
          .in('id', edgeIds);

        // Map geometries to simulation data
        const geomMap = new Map(edgesGeom?.map(e => [e.id, e.geom]));
        edgesWithGeom = aristasData.map(a => ({
          ...a,
          geom: geomMap.get(a.entity_id)
        }));
      }

      const allEntities = [...nodesWithGeom, ...edgesWithGeom];

      return NextResponse.json({
        success: true,
        simulation_id: simulationId,
        summary: {
          total_nodos: nodosData.length,
          nodos_failed: nodosData.filter(n => n.is_failed).length,
          total_aristas: aristasData.length,
          aristas_failed: aristasData.filter(a => a.is_failed).length
        },
        entities: allEntities
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
