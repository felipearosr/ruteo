/**
 * API route para Ruta 2: Optimización MILP con GUROBI
 * 
 * Usa el modelo de optimización de GUROBI para encontrar la ruta óptima
 * que minimiza distancia + λ * riesgo con restricciones.
 * 
 * Endpoint: GET /api/route/optimize
 * Query params:
 *   - source: nodo origen
 *   - target: nodo destino
 *   - lambda_risk: factor de penalización por riesgo (default: 5.0)
 *   - max_risk: riesgo acumulado máximo (opcional)
 *   - max_distance: distancia máxima en metros (opcional)
 */
import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const lambdaRisk = parseFloat(searchParams.get('lambda_risk') || '5.0');
  const maxRisk = searchParams.get('max_risk') ? parseFloat(searchParams.get('max_risk')!) : null;
  const maxDistance = searchParams.get('max_distance') ? parseFloat(searchParams.get('max_distance')!) : null;

  const startTime = performance.now();

  try {
    // Ejecutar el script Python de GUROBI
    const scriptPath = path.join(process.cwd(), '..', 'optimization', 'gurobi_router_api.py');
    
    const pythonProcess = spawn('python', [
      scriptPath,
      '--source', source.toString(),
      '--target', target.toString(),
      '--lambda-risk', lambdaRisk.toString(),
      ...(maxRisk !== null ? ['--max-risk', maxRisk.toString()] : []),
      ...(maxDistance !== null ? ['--max-distance', maxDistance.toString()] : [])
    ]);

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

    // Agregar tiempo total de API (incluye spawn + ejecución Python)
    result.metrics.total_api_time_ms = totalTime;

    return NextResponse.json(result);

  } catch (err) {
    const endTime = performance.now();
    const computationTime = endTime - startTime;

    console.error('Error en el endpoint de optimización GUROBI:', err);
    
    // Verificar si el error es porque GUROBI no está disponible
    const errorMessage = err instanceof Error ? err.message : String(err);
    const isGurobiUnavailable = errorMessage.includes('GUROBI') || errorMessage.includes('gurobipy');

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
          method: 'gurobi',
          parameters: { lambda_risk: lambdaRisk, max_risk: maxRisk, max_distance: maxDistance }
        },
        error: isGurobiUnavailable 
          ? 'GUROBI no está disponible. Ver docs/instalacion_gurobi.md para instrucciones.'
          : 'Error en optimización GUROBI: ' + errorMessage,
        gurobi_available: false
      },
      { status: isGurobiUnavailable ? 503 : 500 }
    );
  }
}
