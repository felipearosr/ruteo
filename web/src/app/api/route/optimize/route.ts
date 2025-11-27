/**
 * API route para Ruta 2: Optimización MILP con GUROBI
 *
 * Ejecuta el modelo ResilientRouter en Python (gurobi_router_api.py) y retorna
 * la ruta óptima considerando distancia y riesgo.
 *
 * Endpoint: GET /api/route/optimize
 * Query params:
 *   - source: nodo origen
 *   - target: nodo destino
 *   - lambda_risk: factor de penalización de riesgo (default: 5.0)
 *   - max_risk: riesgo máximo permitido (opcional)
 *   - max_distance: distancia máxima permitida en metros (opcional)
 */
import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const lambdaRisk = parseFloat(searchParams.get('lambda_risk') || '5.0');
  const maxRisk = searchParams.get('max_risk');
  const maxDistance = searchParams.get('max_distance');
  const avoidFloodZones = searchParams.get('avoid_flood_zones') === 'true';

  const startTime = performance.now();

  try {
    const scriptPath = path.join(process.cwd(), '..', 'optimization', 'gurobi_router_api.py');

    const args = [
      scriptPath,
      '--source', source.toString(),
      '--target', target.toString(),
      '--lambda-risk', lambdaRisk.toString()
    ];

    if (maxRisk) {
      args.push('--max-risk', maxRisk);
    }
    if (maxDistance) {
      args.push('--max-distance', maxDistance);
    }
    if (avoidFloodZones) {
      args.push('--avoid-flood');
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

    const result = await new Promise<any>((resolve) => {
      pythonProcess.on('close', (code) => {
        // El script siempre imprime JSON; si hay ruido previo, intentar limpiar
        const trimmed = (outputData || '').trim();
        let parsed: any = null;
        try {
          parsed = JSON.parse(trimmed);
        } catch {
          // Si no se puede parsear, devolver un error estandarizado
          parsed = {
            route: { type: 'FeatureCollection', features: [] },
            metrics: {
              distance_m: 0,
              computation_time_ms: 0,
              risk_score: 0,
              num_segments: 0,
              method: 'gurobi',
              status: 'error'
            },
            error: trimmed || errorData || `GUROBI process exited with code ${code}`,
            gurobi_available: false
          };
        }
        resolve(parsed);
      });

      pythonProcess.on('error', (err) => resolve({
        route: { type: 'FeatureCollection', features: [] },
        metrics: {
          distance_m: 0,
          computation_time_ms: 0,
          risk_score: 0,
          num_segments: 0,
          method: 'gurobi',
          status: 'error'
        },
        error: err instanceof Error ? err.message : String(err),
        gurobi_available: false
      }));
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    if (result.metrics) {
      result.metrics.total_api_time_ms = totalTime;
    }

    return NextResponse.json(result);

  } catch (err) {
    const endTime = performance.now();
    const computationTime = endTime - startTime;

    console.error('Error en el endpoint de GUROBI:', err);

    return NextResponse.json(
      {
        route: { type: 'FeatureCollection', features: [] },
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'gurobi',
          status: 'error',
          parameters: {
            lambda_risk: lambdaRisk,
            max_risk: maxRisk ? parseFloat(maxRisk) : null,
            max_distance: maxDistance ? parseFloat(maxDistance) : null
          }
        },
        error: err instanceof Error ? err.message : String(err)
      },
      { status: 500 }
    );
  }
}
