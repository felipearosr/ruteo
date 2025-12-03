# Amenazas Data - Resumen

## Resumen de Datos

### Amenazas (afectan calculo de riesgo)

| Amenaza | Cantidad | Peso | Fuente |
|---------|----------|------|--------|
| **Zonas de Inundacion** | 15 | 50% | Basado en mapas SERNAGEOMIN, registros historicos y reportes municipales |
| **Pasos Bajo Nivel** | 20 | 25% | Basado en noticias, reportes de Carabineros y documentacion municipal |
| **Reportes Ciudadanos** | 25 | 15% | Basado en puntos criticos de inundacion documentados en noticias |
| **Lluvia** | (metadata) | 10% | Datos meteorologicos |

### Informacion (no afectan calculo de riesgo)

| Dato | Cantidad | Fuente |
|------|----------|--------|
| **Estaciones DGA** | 94 | [Datos Abiertos MMA](https://lineasdebasepublicas.mma.gob.cl/datos_abiertos/dataset/hidrosfera) - Datos oficiales de la DGA |

---

## Zonas de Inundacion (15 zonas)

Poligonos realistas basados en areas documentadas con riesgo de inundacion.

### Por Severidad
| Severidad | Cantidad |
|-----------|----------|
| Muy Alta | 1 |
| Alta | 7 |
| Media | 5 |
| Baja | 2 |

### Por Fuente
| Fuente | Cantidad |
|--------|----------|
| SERNAGEOMIN | 7 |
| Registro municipal | 7 |
| DGA | 1 |

### Zonas Incluidas

#### Rio Mapocho
- Providencia (evento 1982)
- Santiago Centro / Parque Forestal (evento 1997)
- Pudahuel sector poniente (evento 2016)

#### Zanjon de la Aguada
- San Miguel (evento 1993)
- Pedro Aguirre Cerda (zona recurrente)

#### Quebradas Precordilleranas
- **Quebrada de Macul** - Aluvion historico 1993 (26 fallecidos)
- **Quebrada Lo Canas** - Zona de riesgo aluvional
- **Quebrada de Ramon** - La Reina/Penalolen
- **Quebradas Lo Barnechea** - Sector cordillerano (evento 2017)

#### Rio Maipo
- El Monte sector rural (evento 2008)
- Puente Alto ribera norte (evento 2013)

#### Esteros
- Estero Lampa (evento 2017)
- Estero Colina (evento 2015)

#### Otros
- Canal San Carlos - Nunoa
- Vitacura - El Golf (drenaje insuficiente)

### Referencias
- SERNAGEOMIN: Peligro de Remociones en Masa e Inundacion, Cuenca de Santiago
- https://www.sernageomin.cl/peligrosgeologicos/

---

## Pasos Bajo Nivel (20 pasos)

Los pasos bajo nivel (underpasses) son puntos criticos durante inundaciones. Acumulan agua rapidamente y pueden atrapar vehiculos.

### Por Severidad
| Severidad | Cantidad |
|-----------|----------|
| Muy Alta | 1 |
| Alta | 8 |
| Media | 9 |
| Baja | 2 |

### Pasos Incluidos

#### Americo Vespucio
- **Pudahuel** (muy_alta) - Historial recurrente de vehiculos atrapados
- **San Bernardo** (alta) - Cierres frecuentes
- **Renca** (alta) - Problemas de drenaje
- **Lo Prado** (alta) - Historial de cierres
- **Quilicura** (media) - Problemas de drenaje
- **Kennedy/Las Condes** (baja) - Sector oriente

#### Sector Centro-Sur
- **Alameda/Estacion Central** (alta) - Frente a Terminal de Buses
- **Gran Avenida/San Miguel** (alta) - Sector comercial
- **Gran Avenida/La Cisterna** (media) - Avenida principal del sur
- **Departamental/PAC** (alta) - Cerca del Zanjon de la Aguada
- **Lo Valledor/Cerrillos** (media) - Sector de feria

#### Sector Poniente
- **Pajaritos/5 de Abril** (alta) - Drenaje insuficiente
- **Ruta 68/Cerro Navia** (alta) - Autopista a Valparaiso
- **Matucana/Ecuador** (media) - Cerca de Estacion Central

#### Sector Oriente-Sur
- **Vicuna Mackenna/Departamental** (media) - Avenida principal
- **Vicuna Mackenna/Macul** (media) - Cerca de quebrada de Macul
- **Costanera Norte/Providencia** (media) - Tunel acumula agua
- **Concha y Toro/Puente Alto** (media) - Cerca del rio Maipo
- **Grecia/Tobalaba** (baja) - Sector oriente

#### Sector Norte
- **El Salto/Recoleta** (media) - Acceso norte

### Referencias
- Noticias La Tercera, BioBioChile sobre inundaciones
- Reportes de Carabineros sobre cierres de pasos bajo nivel
- Documentacion municipal de puntos criticos

---

## Reportes Ciudadanos (25 reportes)

Reportes simulados basados en puntos criticos reales de inundacion documentados en noticias.

### Por Severidad
| Severidad | Cantidad |
|-----------|----------|
| Muy Alta | 1 |
| Alta | 9 |
| Media | 10 |
| Baja | 5 |

### Puntos Criticos Incluidos

#### Comunas Mas Afectadas
- **Quilicura**: Estero Las Cruces
- **Pudahuel**: Paso bajo nivel Americo Vespucio
- **Lo Espejo**: Poblacion Lo Sierra
- **Maipu**: Canal Lo Espejo y Ruta 78
- **Recoleta**: Colector Independencia

#### Otros Puntos
- Conchali - Calle Huechuraba
- La Cisterna - Gran Avenida
- Cerro Navia - Canal Ortuzano
- Penalolen - Av. Grecia
- La Florida - Av. Vicuna Mackenna
- Puente Alto - Sector Rio Maipo
- San Bernardo - Sector industrial
- El Bosque - Gran Avenida
- Renca - Canal Zapata
- Huechuraba - Ciudad Empresarial
- Lampa - Centro
- Colina - Chicureo
- Santiago Centro - Metro U. de Chile
- Providencia - Canal San Carlos
- Nunoa - Av. Irarrazaval
- La Reina - Av. Larrain
- Las Condes - Apoquindo con El Golf
- Estacion Central - Terminal de Buses
- Pedro Aguirre Cerda - Zanjon de la Aguada
- San Miguel - Club Hipico

### Referencias
- La Tercera: Inundaciones en Santiago
- BioBioChile: Reportes de emergencias
- SENAPRED: Puntos criticos Region Metropolitana

---

## Estaciones DGA (94 estaciones) - SOLO INFORMACION

**NOTA:** Las estaciones DGA son puntos de monitoreo hidrologico. NO afectan el calculo de riesgo de las rutas. Se muestran como capa informativa opcional.

Datos reales del GeoJSON oficial de la Direccion General de Aguas (DGA) de Chile.

### Tipos de Estacion
| Tipo | Cantidad |
|------|----------|
| Calidad de agua | 66 |
| Meteorologica | 12 |
| Fluviometrica | 7 |
| Fluviometrica - Meteorologica | 5 |
| Fluviometrica - Calidad de agua | 3 |
| Sedimentometrica | 1 |

### Cobertura
- Rio Mapocho y afluentes
- Rio Maipo y afluentes
- Esteros de la Region Metropolitana

### Fuente de Datos
- URL: https://lineasdebasepublicas.mma.gob.cl/datos_abiertos/dataset/hidrosfera
- Formato: GeoJSON
- Total nacional: 3,425 estaciones
- Filtrado por bounding box de Santiago

---

## Formula de Probabilidad de Fallo

```
P_fallo = 0.50 * f(inundaciones) +    // Zonas de inundacion historicas
          0.25 * f(pasos_bajo_nivel) + // Pasos bajo nivel criticos
          0.15 * f(reportes) +         // Reportes ciudadanos
          0.10 * f(lluvia)             // Precipitacion
```

Donde `f(x)` es una funcion de decaimiento exponencial basada en la distancia al punto de amenaza.

---

## Uso de los ETL

```bash
# Generar datos de zonas de inundacion
python amenazas/inundaciones_hist_etl.py

# Generar datos de pasos bajo nivel
python amenazas/pasos_bajo_nivel_etl.py

# Generar reportes ciudadanos
python amenazas/reportes_ciudadanos_etl.py

# Generar datos de estaciones DGA (solo informacion)
python amenazas/dga_etl.py
```

## Archivos Generados

- `inundaciones_hist.json` - 15 zonas de inundacion
- `pasos_bajo_nivel.json` - 20 pasos bajo nivel
- `reportes_ciudadanos.json` - 25 reportes ciudadanos
- `dga_estaciones.json` - 94 estaciones DGA (solo informacion)

## Carga a Base de Datos

Los datos se cargan a las siguientes tablas en Supabase:
- `amenaza_inundaciones_hist`
- `amenaza_pasos_bajo_nivel`
- `amenaza_reportes_ciudadanos`
- `amenaza_dga` (solo informacion, no afecta calculo)
