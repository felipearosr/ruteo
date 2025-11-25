/**
 * API route para comparar las 3 rutas simultáneamente
 * 
 * Ejecuta las 3 técnicas de ruteo y retorna todas las rutas con métricas
 * para comparación visual y analítica.
 * 
 * Endpoint: GET /api/route/compare
 * Query params:
 *   - source: nodo origen (requerido)
 *   - target: nodo destino (requerido)
 *   - k: factor de penalización Dijkstra resiliente (default: 5.0)
 *   - risk_weight: peso A* (default: 3.0)
 *   - max_risk: restricción de riesgo (opcional)
 *   - max_distance: restricción de distancia (opcional)
 *   - simulation_id: ID de simulación activa (opcional)
 */
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const source = searchParams.get('source');
  const target = searchParams.get('target');

  if (!source || !target) {
    return NextResponse.json(
      { error: 'Se requieren parámetros source y target' },
      { status: 400 }
    );
  }

  const k = searchParams.get('k') || '5.0';

  const riskWeight = searchParams.get('risk_weight') || '3.0';
  const maxRisk = searchParams.get('max_risk');
  const maxDistance = searchParams.get('max_distance');
  const simulationId = searchParams.get('simulation_id');

  const startTime = performance.now();

  try {
    // Construir URLs para cada endpoint
    const baseUrl = new URL(request.url).origin;

    const params = new URLSearchParams({
      source,
      target,
      ...(maxRisk && { max_risk: maxRisk }),
      ...(maxDistance && { max_distance: maxDistance }),
      ...(simulationId && { simulation_id: simulationId })
    });

    // URLs de cada ruta
    const baselineUrl = `${baseUrl}/api/route/baseline?${params}`;
    const resilientUrl = `${baseUrl}/api/route/resilient?${params}&k=${k}`;
    const metaheuristicUrl = `${baseUrl}/api/route/metaheuristic?${params}&risk_weight=${riskWeight}`;

    // Ejecutar las 3 rutas en paralelo
    const [baseline, resilient, metaheuristic] = await Promise.allSettled([
      fetch(baselineUrl).then(r => r.json()),
      fetch(resilientUrl).then(r => r.json()),
      fetch(metaheuristicUrl).then(r => r.json())
    ]);

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Extraer resultados (manejar errores individuales)
    const getResult = (result: PromiseSettledResult<any>, method: string) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          route: { type: 'FeatureCollection', features: [] },
          metrics: {
            distance_m: 0,
            computation_time_ms: 0,
            risk_score: 0,
            num_segments: 0,
            method,
            error: true
          },
          error: result.reason?.message || 'Error desconocido'
        };
      }
    };

    const baselineResult = getResult(baseline, 'baseline');
    const resilientResult = getResult(resilient, 'resilient');
    const astarResult = getResult(metaheuristic, 'astar');

    const results = {
      baseline: baselineResult,
      resilient: resilientResult,
      astar: astarResult,
      comparison: {
        total_time_ms: totalTime,
        parameters: {
          source: parseInt(source),
          target: parseInt(target),
          k: parseFloat(k),

          risk_weight: parseFloat(riskWeight),
          max_risk: maxRisk ? parseFloat(maxRisk) : null,
          max_distance: maxDistance ? parseFloat(maxDistance) : null,
          simulation_id: simulationId
        },
        summary: {
          shortest_distance: Math.min(
            baselineResult?.metrics?.distance_m || Infinity,
            resilientResult?.metrics?.distance_m || Infinity,
            astarResult?.metrics?.distance_m || Infinity
          ),
          lowest_risk: Math.min(
            baselineResult?.metrics?.risk_score || Infinity,
            resilientResult?.metrics?.risk_score || Infinity,
            astarResult?.metrics?.risk_score || Infinity
          ),
          fastest_computation: Math.min(
            baselineResult?.metrics?.computation_time_ms || Infinity,
            resilientResult?.metrics?.computation_time_ms || Infinity,
            astarResult?.metrics?.computation_time_ms || Infinity
          )
        }
      }
    };

    return NextResponse.json(results);

  } catch (err) {
    const endTime = performance.now();
    const totalTime = endTime - startTime;

    console.error('Error en comparación de rutas:', err);

    return NextResponse.json(
      {
        error: 'Error al comparar rutas: ' + (err instanceof Error ? err.message : String(err)),
        comparison: {
          total_time_ms: totalTime,
          success: false
        }
      },
      { status: 500 }
    );
  }
}
