import { NextResponse } from 'next/server';
import { pool } from '@/lib/db';
import { resolveConnectedNodes } from '@/lib/connectedNodes';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const source = searchParams.get('source');
  const target = searchParams.get('target');

  if (!source || !target) {
    return NextResponse.json({ error: 'source y target son requeridos' }, { status: 400 });
  }

  const sourceNum = parseInt(source, 10);
  const targetNum = parseInt(target, 10);

  let client;
  try {
    client = await pool.connect();
    const nodeResolution = await resolveConnectedNodes(sourceNum, targetNum, client);
    return NextResponse.json({ node_adjustments: nodeResolution });
  } catch (err) {
    console.error('Error resolviendo nodos:', err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 }
    );
  } finally {
    if (client) client.release();
  }
}
