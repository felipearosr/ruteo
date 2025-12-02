import type { PoolClient } from 'pg';

export type NodeAdjustment = {
  requested: number;
  resolved: number;
  exists: boolean;
  degree: number | null;
  snapped: boolean;
  nearestDistanceM: number | null;
  requestedLat: number | null;
  requestedLon: number | null;
  resolvedLat: number | null;
  resolvedLon: number | null;
};

type Resolution = {
  source: NodeAdjustment;
  target: NodeAdjustment;
  adjustedSource: number;
  adjustedTarget: number;
};

async function resolveNode(nodeId: number, client: PoolClient): Promise<NodeAdjustment> {
  const { rows } = await client.query(
    `
    WITH input_geom AS (
      SELECT geom FROM infra_nodos_cleaned WHERE id = $1
    ),
    deg AS (
      SELECT COUNT(*) AS degree FROM infra_aristas_cleaned WHERE source = $1 OR target = $1
    ),
    connected AS (
      SELECT n.id, n.geom
      FROM infra_nodos_cleaned n
      WHERE EXISTS (SELECT 1 FROM infra_aristas_cleaned a WHERE a.source = n.id OR a.target = n.id)
    ),
    nearest AS (
      SELECT c.id,
             ST_Distance(c.geom::geography, ig.geom::geography) AS distance_m,
             ST_Y(c.geom) AS nearest_lat,
             ST_X(c.geom) AS nearest_lon
      FROM connected c
      JOIN input_geom ig ON true
      ORDER BY c.geom <-> ig.geom
      LIMIT 1
    )
    SELECT 
      (SELECT COUNT(*) FROM input_geom) > 0 AS exists,
      (SELECT degree FROM deg) AS degree,
      (SELECT id FROM nearest) AS nearest_id,
      (SELECT distance_m FROM nearest) AS nearest_distance_m,
      (SELECT ST_Y(geom) FROM input_geom) AS requested_lat,
      (SELECT ST_X(geom) FROM input_geom) AS requested_lon,
      (SELECT nearest_lat FROM nearest) AS nearest_lat,
      (SELECT nearest_lon FROM nearest) AS nearest_lon;
  `,
    [nodeId]
  );

  const row = rows?.[0] || {};
  const degree = row.degree === undefined || row.degree === null ? null : Number(row.degree);
  const exists = !!row.exists;
  const nearestId = row.nearest_id === undefined || row.nearest_id === null ? null : Number(row.nearest_id);
  const nearestDistanceM =
    row.nearest_distance_m === undefined || row.nearest_distance_m === null
      ? null
      : Number(row.nearest_distance_m);
  const requestedLat = row.requested_lat === undefined || row.requested_lat === null ? null : Number(row.requested_lat);
  const requestedLon = row.requested_lon === undefined || row.requested_lon === null ? null : Number(row.requested_lon);
  const nearestLat = row.nearest_lat === undefined || row.nearest_lat === null ? null : Number(row.nearest_lat);
  const nearestLon = row.nearest_lon === undefined || row.nearest_lon === null ? null : Number(row.nearest_lon);

  const isConnected = exists && typeof degree === 'number' && degree > 0;
  const resolved = isConnected ? nodeId : nearestId ?? nodeId;
  const resolvedLat = isConnected ? requestedLat : nearestLat;
  const resolvedLon = isConnected ? requestedLon : nearestLon;

  return {
    requested: nodeId,
    resolved,
    exists,
    degree,
    snapped: resolved !== nodeId,
    nearestDistanceM,
    requestedLat,
    requestedLon,
    resolvedLat,
    resolvedLon
  };
}

export async function resolveConnectedNodes(
  sourceId: number,
  targetId: number,
  client: PoolClient
): Promise<Resolution> {
  const [source, target] = await Promise.all([
    resolveNode(sourceId, client),
    resolveNode(targetId, client)
  ]);

  return {
    source,
    target,
    adjustedSource: source.resolved,
    adjustedTarget: target.resolved
  };
}
