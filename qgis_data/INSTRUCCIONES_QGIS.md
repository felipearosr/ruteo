# Instrucciones para QGIS

## Cargar capas

1. Abrir QGIS
2. Arrastrar archivos .geojson a la ventana de capas
3. O usar: Capa > Anadir capa > Anadir capa vectorial

## Orden de capas recomendado (de arriba a abajo)

1. amenaza_pasos_bajo_nivel (puntos rojos)
2. amenaza_reportes (puntos morados)
3. amenaza_dga (puntos azules)
4. aristas_muy_alto_riesgo (lineas rojas gruesas)
5. aristas_alto_riesgo (lineas naranjas)
6. aristas_primarias (lineas grises)
7. buffer_pasos_500m (poligonos rojos transparentes)
8. buffer_reportes_200m (poligonos morados transparentes)
9. buffer_dga_1000m (poligonos azules transparentes)
10. OpenStreetMap (base)

## Estilos recomendados

### Aristas por riesgo (aristas_riesgo.geojson)
- Estilo: Categorizado
- Columna: categoria_riesgo
- Valores:
  - bajo: #2ecc71 (verde), ancho 0.5
  - medio: #f1c40f (amarillo), ancho 0.8
  - alto: #e67e22 (naranja), ancho 1.2
  - muy_alto: #e74c3c (rojo), ancho 2.0

### Aristas alto riesgo (graduado por p_fallo)
- Estilo: Graduado
- Columna: p_fallo_arista
- Metodo: Quantile, 5 clases
- Rampa: RdYlGn invertida
- Ancho: 1.5 - 3.0

### Buffers de amenazas
- Relleno: color con 20% opacidad
- Borde: color solido, 0.5px
- DGA: #3498db
- Pasos: #e74c3c
- Reportes: #9b59b6

### Puntos de amenazas
- Marcador simple
- Tamano: 8-12 puntos
- Con etiqueta del nombre

## Mapas sugeridos para el informe

1. **Mapa general de la red**
   - Capas: aristas_primarias + base OSM
   - Escala: 1:150,000
   - Mostrar extension de la red

2. **Mapa de distribucion de riesgo**
   - Capas: aristas_riesgo (categorizado)
   - Escala: 1:100,000
   - Leyenda con categorias

3. **Mapa de zonas criticas**
   - Capas: aristas_muy_alto_riesgo + zonas_criticas_centroid
   - Escala: 1:50,000
   - Zoom a zona con mas riesgo

4. **Mapa de amenazas y buffers**
   - Capas: todos los buffers + puntos de amenazas
   - Escala: 1:100,000
   - Mostrar superposicion de amenazas

5. **Mapa de detalle: zona centro**
   - Capas: aristas_alto_riesgo + amenazas
   - Extent: -70.68, -33.47 a -70.62, -33.43
   - Escala: 1:25,000

6. **Mapa de corredores de riesgo**
   - Capas: corredores_riesgo + intersecciones
   - Identificar rutas criticas

## Exportar mapas

1. Proyecto > Nuevo diseno de impresion
2. Agregar mapa, leyenda, escala, norte
3. Exportar como imagen (300 DPI para informe)

## Composicion de mapa para IEEE

- Tamano: 3.5" x 3" (columna simple) o 7" x 5" (doble columna)
- DPI: 300
- Formato: PNG o TIFF
- Incluir: escala grafica, leyenda compacta, norte
