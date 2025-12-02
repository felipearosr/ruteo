import { NextResponse } from 'next/server';
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
