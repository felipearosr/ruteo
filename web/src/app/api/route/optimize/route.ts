/**
 * API route para Ruta 2: Optimización MILP con CPLEX
 *
 * Ejecuta el modelo ResilientRouter en Python (cplex_router_api.py) y retorna
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
import { pool } from '@/lib/db';
import { resolveConnectedNodes } from '@/lib/connectedNodes';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const lambdaRisk = parseFloat(searchParams.get('lambda_risk') || '5.0');
  const maxRisk = searchParams.get('max_risk');
  const maxDistance = searchParams.get('max_distance');
  const avoidFloodZones = searchParams.get('avoid_flood_zones') === 'true';
  const defaultBboxMargin = process.env.CPLEX_BBOX_MARGIN || process.env.NEXT_PUBLIC_CPLEX_BBOX_MARGIN;
  const bboxMarginParam = searchParams.get('bbox_margin') || defaultBboxMargin || undefined;
  const bboxMargin = bboxMarginParam !== undefined ? parseFloat(bboxMarginParam) : undefined;

  const startTime = performance.now();
  let client;

  try {
    client = await pool.connect();
    const nodeResolution = await resolveConnectedNodes(source, target, client);
    const usedSource = nodeResolution.adjustedSource;
    const usedTarget = nodeResolution.adjustedTarget;

    // En Docker, optimization está en /app/optimization; en local, está en ../optimization
    const scriptPath = process.env.OPTIMIZATION_PATH
      ? path.join(process.env.OPTIMIZATION_PATH, 'cplex_router_api.py')
      : path.join(process.cwd(), '..', 'optimization', 'cplex_router_api.py');
    const pythonBin = process.env.PYTHON_BIN || 'python3';

    const args = [
      scriptPath,
      '--source', usedSource.toString(),
      '--target', usedTarget.toString(),
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
    if (bboxMargin !== undefined && !Number.isNaN(bboxMargin)) {
      args.push('--bbox-margin', bboxMargin.toString());
    }

    const pythonProcess = spawn(pythonBin, args);

    let outputData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      outputData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
    });

    const tryParseJson = (text: string): any | null => {
      if (!text) return null;
      try {
        return JSON.parse(text);
      } catch {
        const firstBrace = text.indexOf('{');
        const lastBrace = text.lastIndexOf('}');
        if (firstBrace !== -1 && lastBrace > firstBrace) {
          const candidate = text.slice(firstBrace, lastBrace + 1);
          try {
            return JSON.parse(candidate);
          } catch {
            return null;
          }
        }
        return null;
      }
    };

    const result = await new Promise<any>((resolve) => {
      pythonProcess.on('close', (code) => {
        const exitCode = code;
        const stdoutText = (outputData || '').trim();
        const stderrText = (errorData || '').trim();

        // El script siempre imprime JSON; si hay ruido previo, intentar limpiar
        const parsed =
          tryParseJson(stdoutText) ||
          tryParseJson(stderrText) ||
          {
            route: { type: 'FeatureCollection', features: [] },
            metrics: {
              distance_m: 0,
              computation_time_ms: 0,
              risk_score: 0,
              num_segments: 0,
              method: 'cplex',
              status: 'error',
              parameters: {
                lambda_risk: lambdaRisk,
                max_risk: maxRisk ? parseFloat(maxRisk) : null,
                max_distance: maxDistance ? parseFloat(maxDistance) : null,
                avoid_flood: avoidFloodZones,
                bbox_margin: bboxMargin
              }
            },
            error: stdoutText || stderrText || `CPLEX process exited with code ${exitCode}`,
            cplex_available: false
          };
        if (parsed && typeof parsed === 'object') {
          parsed.debug = {
            stderr: stderrText,
            stdout: stdoutText,
            exit_code: exitCode
          };
          parsed.node_adjustments = nodeResolution;
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
          method: 'cplex',
          status: 'error'
        },
        error: err instanceof Error ? err.message : String(err),
        cplex_available: false
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

    console.error('Error en el endpoint de CPLEX:', err);

    return NextResponse.json(
      {
        route: { type: 'FeatureCollection', features: [] },
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'cplex',
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
  } finally {
    if (client) client.release();
  }
}
