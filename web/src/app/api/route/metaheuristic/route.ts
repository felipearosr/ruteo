/**
 * API route para Ruta 4: A* con Heurística de Riesgo
 * 
 * Usa el algoritmo A* modificado que considera riesgo en la heurística
 * para encontrar rutas resilientes eficientemente.
 * 
 * Endpoint: GET /api/route/metaheuristic
 * Query params:
 *   - source: nodo origen
 *   - target: nodo destino
 *   - risk_weight: peso del riesgo en el costo (default: 3.0)
 *   - heuristic_weight: peso de la heurística (default: 1.0)
 */
import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import pg from 'pg';
import { resolveConnectedNodes } from '@/lib/connectedNodes';

const { Pool } = pg;

const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST || 'aws-1-us-east-1.pooler.supabase.com',
  port: parseInt(process.env.SUPABASE_DB_PORT || '6543'),
  database: process.env.SUPABASE_DB_NAME || 'postgres',
  user: process.env.SUPABASE_DB_USER || 'postgres.eqjzlgbjgwbnvqzbomsn',
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const riskWeight = parseFloat(searchParams.get('risk_weight') || '3.0');
  const heuristicWeight = parseFloat(searchParams.get('heuristic_weight') || '1.0');
  const defaultBboxMargin = process.env.ASTAR_BBOX_MARGIN || process.env.NEXT_PUBLIC_ASTAR_BBOX_MARGIN;
  const bboxMarginParam = searchParams.get('bbox_margin') || defaultBboxMargin || undefined;
  const bboxMargin = bboxMarginParam !== undefined ? parseFloat(bboxMarginParam) : undefined;

  const startTime = performance.now();
  let client;

  try {
    client = await pool.connect();
    const nodeResolution = await resolveConnectedNodes(source, target, client);
    const usedSource = nodeResolution.adjustedSource;
    const usedTarget = nodeResolution.adjustedTarget;

    // Ejecutar el script Python de A*
    const scriptPath = path.join(process.cwd(), '..', 'optimization', 'astar_router_api.py');
    
    const args = [
      scriptPath,
      '--source', usedSource.toString(),
      '--target', usedTarget.toString(),
      '--risk-weight', riskWeight.toString(),
      '--heuristic-weight', heuristicWeight.toString()
    ];

    if (bboxMargin !== undefined && !Number.isNaN(bboxMargin)) {
      args.push('--bbox-margin', bboxMargin.toString());
    }

    const pythonProcess = spawn('python', args);

    let outputData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      outputData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
    });

    const result = await new Promise<any>((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}: ${errorData}`));
          return;
        }

        try {
          const jsonResult = JSON.parse(outputData);
          resolve(jsonResult);
        } catch (err) {
          reject(new Error(`Failed to parse Python output: ${outputData}`));
        }
      });

      pythonProcess.on('error', (err) => {
        reject(err);
      });
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Agregar tiempo total de API
    result.metrics.total_api_time_ms = totalTime;
    result.node_adjustments = nodeResolution;

    return NextResponse.json(result);

  } catch (err) {
    const endTime = performance.now();
    const computationTime = endTime - startTime;

    console.error('Error en el endpoint de A*:', err);
    
    return NextResponse.json(
      { 
        route: {
          type: 'FeatureCollection',
          features: []
        },
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          nodes_explored: 0,
          method: 'astar',
          parameters: { risk_weight: riskWeight, heuristic_weight: heuristicWeight }
        },
        error: 'Error en A*: ' + (err instanceof Error ? err.message : String(err))
      },
      { status: 500 }
    );
  } finally {
    if (client) client.release();
  }
}
