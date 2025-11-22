const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

// Load env vars from .env.local manually
const envPath = path.join(__dirname, '../.env.local');
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

async function exportGraph() {
    const bbox = [-70.66, -33.45, -70.64, -33.43]; // Santiago Centro approx
    const outputFile = path.join(__dirname, '../public/debug_graph.json');

    console.log(`Exporting graph for bbox: ${bbox} `);

    try {
        const client = await pool.connect();

        // Fetch Nodes
        const nodesQuery = `
      SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat
      FROM infra_nodos
      WHERE ST_Intersects(geom, ST_MakeEnvelope($1, $2, $3, $4, 4326))
    `;
        const nodesRes = await client.query(nodesQuery, bbox);
        console.log(`Found ${nodesRes.rowCount} nodes`);

        // Fetch Edges
        const edgesQuery = `
      SELECT id, source, target, ST_AsGeoJSON(geom) as geom_json, length_m
      FROM infra_aristas
      WHERE ST_Intersects(geom, ST_MakeEnvelope($1, $2, $3, $4, 4326))
    `;
        const edgesRes = await client.query(edgesQuery, bbox);
        console.log(`Found ${edgesRes.rowCount} edges`);

        const features = [];

        // Add Nodes
        for (const node of nodesRes.rows) {
            features.push({
                type: "Feature",
                geometry: {
                    type: "Point",
                    coordinates: [node.lon, node.lat]
                },
                properties: {
                    type: "node",
                    id: node.id
                }
            });
        }

        // Add Edges
        for (const edge of edgesRes.rows) {
            features.push({
                type: "Feature",
                geometry: JSON.parse(edge.geom_json),
                properties: {
                    type: "edge",
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    length: edge.length_m
                }
            });
        }

        const geojson = {
            type: "FeatureCollection",
            features: features
        };

        fs.writeFileSync(outputFile, JSON.stringify(geojson));
        console.log(`Exported to ${outputFile} `);

        client.release();
        await pool.end();

    } catch (err) {
        console.error('Error exporting graph:', err);
        process.exit(1);
    }
}

exportGraph();
