import pg from 'pg';

const { Pool } = pg;

// Configuracion de SSL: solo usar para conexiones remotas (Supabase)
// Para desarrollo local con Docker, no usar SSL
const isLocalDb = process.env.SUPABASE_DB_HOST === 'localhost' ||
                  process.env.SUPABASE_DB_HOST === 'db' ||
                  process.env.SUPABASE_DB_HOST?.startsWith('192.168.') ||
                  process.env.SUPABASE_DB_HOST?.startsWith('172.') ||
                  process.env.SUPABASE_DB_HOST?.startsWith('10.');

const sslConfig = isLocalDb ? false : { rejectUnauthorized: false };

export const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST || 'aws-1-us-east-1.pooler.supabase.com',
  port: parseInt(process.env.SUPABASE_DB_PORT || '6543'),
  database: process.env.SUPABASE_DB_NAME || 'postgres',
  user: process.env.SUPABASE_DB_USER || 'postgres.eqjzlgbjgwbnvqzbomsn',
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: sslConfig
});
