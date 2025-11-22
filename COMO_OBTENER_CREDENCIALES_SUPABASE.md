# Cómo obtener las credenciales correctas de Supabase

1. Ve a https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Click en "Settings" (⚙️) en el menú izquierdo
4. Click en "Database"
5. Scroll hasta "Connection string"
6. Selecciona "Transaction pooler" en el dropdown
7. Copia la cadena de conexión

Debería verse así:
```
postgresql://postgres.XXXXX:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

Extrae de ahí:
- SUPABASE_DB_HOST = `aws-0-us-west-1.pooler.supabase.com`
- SUPABASE_DB_PORT = `6543`
- SUPABASE_DB_USER = `postgres.XXXXX` (lo que viene después de `postgres://` y antes de `:`)
- SUPABASE_DB_PASSWORD = Tu password real (entre `:` y `@`)
- SUPABASE_DB_NAME = `postgres`

Actualiza `/home/faros/ruteo/web/.env.local` con los valores correctos.

**IMPORTANTE**: El project ref podría haber cambiado. Verifica que sea el mismo proyecto.
