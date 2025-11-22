const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

// Load env vars from .env.local manually
const envPath = path.join(__dirname, '.env.local');
if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, 'utf8');
    envConfig.split('\n').forEach(line => {
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            const value = match[2].trim().replace(/^["']|["']$/g, '');
            process.env[key] = value;
        }
    });
}

const pool = new Pool({
    host: process.env.SUPABASE_DB_HOST,
    port: parseInt(process.env.SUPABASE_DB_PORT || '5432'),
    database: 'postgres',
    user: process.env.SUPABASE_DB_USER,
    password: process.env.SUPABASE_DB_PASSWORD,
    ssl: { rejectUnauthorized: false }
});

async function runCalculation() {
    console.log('🔄 Starting probability calculation...\n');

    try {
        // Step 1: Add columns
        console.log('📊 Step 1: Adding columns and indexes...');
        const addColumnsSQL = fs.readFileSync(path.join(__dirname, '../../sql/add_p_fallo_columns.sql'), 'utf8');
        await pool.query(addColumnsSQL);
        console.log('✅ Columns added\n');

        // Step 2: Calculate probabilities
        console.log('🧮 Step 2: Calculating probabilities (this may take 5-15 minutes)...');
        const calcSQL = fs.readFileSync(path.join(__dirname, '../../sql/calculate_probabilities_optimized.sql'), 'utf8');

        const startTime = Date.now();
        const result = await pool.query(calcSQL);
        const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);

        console.log(`✅ Calculation complete in ${duration} minutes\n`);

        // Show statistics
        console.log('📈 Statistics:');
        if (result.rows && result.rows.length > 0) {
            console.table(result.rows);
        }

        await pool.end();
        console.log('\n✅ All done!');

    } catch (error) {
        console.error('❌ Error:', error.message);
        await pool.end();
        process.exit(1);
    }
}

runCalculation();
