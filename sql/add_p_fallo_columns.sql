-- Add p_fallo columns to infra_nodos and infra_aristas
ALTER TABLE infra_nodos 
ADD COLUMN IF NOT EXISTS p_fallo_nodo DOUBLE PRECISION DEFAULT 0.0;

ALTER TABLE infra_aristas 
ADD COLUMN IF NOT EXISTS p_fallo_arista DOUBLE PRECISION DEFAULT 0.0;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_nodos_p_fallo ON infra_nodos(p_fallo_nodo) WHERE p_fallo_nodo > 0;
CREATE INDEX IF NOT EXISTS idx_aristas_p_fallo ON infra_aristas(p_fallo_arista) WHERE p_fallo_arista > 0;

SELECT 'Columns added successfully' as status;
