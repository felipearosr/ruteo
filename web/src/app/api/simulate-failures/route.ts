/**
 * API Endpoint: Simulacion de Fallas Dinamicas
 *
 * POST: Genera fallas aleatorias basadas en probabilidades
 * DELETE: Limpia simulaciones activas
 * GET: Obtiene estado de simulacion activa
 */

import { NextRequest, NextResponse } from 'next/server';
import { pool } from '@/lib/db';
import { v4 as uuidv4 } from 'uuid';

/**
 * POST - Generar nueva simulacion de fallas
 */
export async function POST(request: NextRequest) {
  const client = await pool.connect();
  try {
    const body = await request.json();
    const { seed, initial_failures = 200, propagation_probability = 1.0, max_steps = 50, decay_rate = 0.99 } = body;

    const simulationId = uuidv4();

    let random = Math.random;
    if (seed !== undefined && seed !== null) {
      let seedValue = seed;
      random = () => {
        seedValue = (seedValue * 9301 + 49297) % 233280;
        return seedValue / 233280;
      };
    }

    console.log(`[PROPAGATION] Starting simulation ${simulationId}`);

    // 1. Obtener nodos semilla - seleccionar exactamente N nodos aleatorios
    // Ordenados por p_fallo para priorizar zonas de riesgo, pero con componente aleatorio
    const nodosResult = await client.query(
      `SELECT id, p_fallo_nodo FROM infra_nodos_cleaned
       WHERE p_fallo_nodo > 0.05
       ORDER BY RANDOM()
       LIMIT $1`,
      [initial_failures]
    );
    const nodos = nodosResult.rows;

    const failedNodeIds = new Set<number>();
    const failedEdgeIds = new Set<number>();
    const processedEdgeIds = new Set<number>();
    const queue: number[] = [];
    const simulaciones: any[] = [];

    // 2. Todos los nodos seleccionados son semillas iniciales
    let nodosFailedCount = 0;
    for (const nodo of nodos) {
      nodosFailedCount++;
      failedNodeIds.add(nodo.id);
      queue.push(nodo.id);

      simulaciones.push({
        simulation_id: simulationId,
        entity_type: 'nodo',
        entity_id: nodo.id,
        p_fallo: nodo.p_fallo_nodo,
        random_value: 0,
        is_failed: true
      });
    }

    console.log(`[PROPAGATION] Initial seeds: ${nodosFailedCount}`);

    // 3. Propagacion tipo "agua" (BFS) con probabilidad decreciente
    // step 1: 95%, step 2: 47.5%, step 3: 23.75%, etc.
    let propagatedCount = 0;
    let step = 0;

    while (queue.length > 0 && step < max_steps) {
      step++;
      // Probabilidad decae exponencialmente: p * decay^(step-1)
      const currentProbability = propagation_probability * Math.pow(decay_rate, step - 1);

      // Si la probabilidad es muy baja, parar
      if (currentProbability < 0.05) break;

      const batchSize = Math.min(queue.length, 10);
      const currentBatch = queue.splice(0, batchSize);

      console.log(`[PROPAGATION] Step ${step}: Processing ${currentBatch.length} nodes, probability: ${(currentProbability * 100).toFixed(1)}%`);

      const edgesResult = await client.query(
        `SELECT id, source, target FROM infra_aristas_cleaned WHERE source = ANY($1) OR target = ANY($1)`,
        [currentBatch]
      );
      const edges = edgesResult.rows;

      edges.forEach((edge: any) => processedEdgeIds.add(edge.id));

      for (const edge of edges) {
        for (const currentId of currentBatch) {
          let neighborId: number | null = null;

          if (edge.source === currentId) {
            neighborId = edge.target;
          } else if (edge.target === currentId) {
            neighborId = edge.source;
          }

          if (neighborId && !failedNodeIds.has(neighborId)) {
            const randomValue = random();
            if (randomValue < currentProbability) {
              failedNodeIds.add(neighborId);
              queue.push(neighborId);
              propagatedCount++;

              simulaciones.push({
                simulation_id: simulationId,
                entity_type: 'nodo',
                entity_id: neighborId,
                p_fallo: currentProbability,
                random_value: randomValue,
                is_failed: true
              });

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

    // 4. Guardar en BD (en lotes)
    const batchSize = 1000;
    for (let i = 0; i < simulaciones.length; i += batchSize) {
      const batch = simulaciones.slice(i, i + batchSize);
      const values = batch.map((s, idx) => {
        const offset = i + idx;
        return `($${offset * 6 + 1}, $${offset * 6 + 2}, $${offset * 6 + 3}, $${offset * 6 + 4}, $${offset * 6 + 5}, $${offset * 6 + 6})`;
      });

      // Simplify: insert one by one for smaller batches
      for (const sim of batch) {
        await client.query(
          `INSERT INTO sim_fallas_activas (simulation_id, entity_type, entity_id, p_fallo, random_value, is_failed)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [sim.simulation_id, sim.entity_type, sim.entity_id, sim.p_fallo, sim.random_value, sim.is_failed]
        );
      }
    }

    return NextResponse.json({
      success: true,
      simulation_id: simulationId,
      summary: {
        total_nodos_checked: nodos.length,
        initial_seeds: nodosFailedCount,
        propagated_nodes: propagatedCount,
        total_nodes_failed: failedNodeIds.size,
        total_edges_failed: failedEdgeIds.size,
        total_failed: failedNodeIds.size + failedEdgeIds.size,
        total_entities: failedNodeIds.size + failedEdgeIds.size,
        nodos_failed: failedNodeIds.size,
        total_nodos: nodos.length,
        aristas_failed: failedEdgeIds.size,
        total_aristas: failedEdgeIds.size,
        steps: step
      },
      timestamp: new Date().toISOString(),
      seed
    });

  } catch (error: any) {
    console.error('Error en simulacion:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  } finally {
    client.release();
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
      await pool.query(`DELETE FROM sim_fallas_activas WHERE simulation_id = $1`, [simulationId]);
      return NextResponse.json({ success: true, message: `Simulacion ${simulationId} eliminada` });
    } else {
      await pool.query(`DELETE FROM sim_fallas_activas`);
      return NextResponse.json({ success: true, message: 'Todas las simulaciones eliminadas' });
    }
  } catch (error: any) {
    console.error('Error al eliminar simulacion:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
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
      // Limitar entidades para evitar congelar el navegador (max 2000 total)
      const maxNodos = 1500;
      const maxAristas = 500;

      // Obtener nodos fallidos con geometria
      const nodosResult = await pool.query(
        `SELECT
          s.entity_type,
          s.entity_id,
          s.p_fallo,
          s.is_failed,
          ST_AsGeoJSON(n.geom) as geom
        FROM sim_fallas_activas s
        JOIN infra_nodos_cleaned n ON s.entity_id = n.id
        WHERE s.simulation_id = $1 AND s.entity_type = 'nodo' AND s.is_failed = true
        ORDER BY s.p_fallo DESC
        LIMIT $2`,
        [simulationId, maxNodos]
      );

      // Obtener aristas fallidas con geometria
      const aristasResult = await pool.query(
        `SELECT
          s.entity_type,
          s.entity_id,
          s.p_fallo,
          s.is_failed,
          ST_AsGeoJSON(a.geom) as geom
        FROM sim_fallas_activas s
        JOIN infra_aristas_cleaned a ON s.entity_id = a.id
        WHERE s.simulation_id = $1 AND s.entity_type = 'arista' AND s.is_failed = true
        ORDER BY s.p_fallo DESC
        LIMIT $2`,
        [simulationId, maxAristas]
      );

      const entities = [...nodosResult.rows, ...aristasResult.rows];

      return NextResponse.json({
        success: true,
        simulation_id: simulationId,
        entities: entities,
        summary: {
          total_nodos: nodosResult.rows.length,
          nodos_failed: nodosResult.rows.length,
          total_aristas: aristasResult.rows.length,
          aristas_failed: aristasResult.rows.length
        }
      });
    } else {
      const result = await pool.query(
        `SELECT DISTINCT simulation_id, created_at FROM sim_fallas_activas ORDER BY created_at DESC`
      );

      return NextResponse.json({
        success: true,
        simulations: result.rows
      });
    }
  } catch (error: any) {
    console.error('Error al obtener simulacion:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
