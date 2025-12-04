#!/usr/bin/env python3
"""
Script para corregir tildes faltantes en documentos LaTeX en espanol.
Usa un diccionario de palabras comunes que requieren acento.
"""

import re
import sys
from pathlib import Path

# Diccionario de palabras sin tilde -> con tilde
# Solo incluye palabras que SIEMPRE llevan tilde (no homografos como "el/él", "si/sí")
ACCENT_FIXES = {
    # Palabras tecnicas/academicas
    "algoritmo": "algoritmo",  # no lleva tilde
    "analisis": "análisis",
    "anos": "años",
    "arbol": "árbol",
    "arboles": "árboles",
    "area": "área",
    "areas": "áreas",
    "articulo": "artículo",
    "automatica": "automática",
    "automatico": "automático",
    "basico": "básico",
    "basica": "básica",
    # "calculo" se maneja de forma especial - solo reemplazar cuando es sustantivo
    # (cuando va precedido de articulo o preposicion)
    "caracteristica": "característica",
    "caracteristicas": "características",
    "catalogo": "catálogo",
    "clasico": "clásico",
    "clasica": "clásica",
    "climatico": "climático",
    "climatica": "climática",
    "codigo": "código",
    "combinacion": "combinación",
    "comparacion": "comparación",
    "computo": "cómputo",
    "comunicacion": "comunicación",
    "conexion": "conexión",
    "configuracion": "configuración",
    "conservacion": "conservación",
    "critica": "crítica",
    "criticas": "críticas",
    "critico": "crítico",
    "criticos": "críticos",
    "decadas": "décadas",
    "definicion": "definición",
    "descripcion": "descripción",
    "detras": "detrás",
    "diagnosico": "diagnóstico",
    "dialogo": "diálogo",
    "dinamica": "dinámica",
    "dinamicas": "dinámicas",
    "dinamico": "dinámico",
    "direccion": "dirección",
    # "diseno" se maneja de forma especial - solo reemplazar cuando es sustantivo
    "distribucion": "distribución",
    "economica": "económica",
    "economico": "económico",
    "economicas": "económicas",
    "ecuacion": "ecuación",
    "eficacia": "eficacia",  # no lleva tilde
    "electronica": "electrónica",
    "electronico": "electrónico",
    "elevacion": "elevación",
    "empirica": "empírica",
    "empirico": "empírico",
    "energia": "energía",
    "especifica": "específica",
    "especificas": "específicas",
    "especifico": "específico",
    "especificos": "específicos",
    "estadistica": "estadística",
    "estadisticas": "estadísticas",
    "estadistico": "estadístico",
    "estatica": "estática",
    "estatico": "estático",
    "estrategia": "estrategia",  # no lleva tilde
    "evaluacion": "evaluación",
    "exito": "éxito",
    "explicacion": "explicación",
    "exposicion": "exposición",
    "extraccion": "extracción",
    "facil": "fácil",
    "fenomeno": "fenómeno",
    "formulacion": "formulación",
    "funcion": "función",
    "funciones": "funciones",  # no lleva tilde
    "geografica": "geográfica",
    "geograficas": "geográficas",
    "geografico": "geográfico",
    "geograficos": "geográficos",
    "geologica": "geológica",
    "geologicas": "geológicas",
    "geologico": "geológico",
    "geologicos": "geológicos",
    "hidrologica": "hidrológica",
    "hidrologicas": "hidrológicas",
    "hidrologico": "hidrológico",
    "hidrologicos": "hidrológicos",
    "hidrometeorologicos": "hidrometeorológicos",
    "grafica": "gráfica",
    "grafico": "gráfico",
    "heuristica": "heurística",
    "heuristicas": "heurísticas",
    "heuristico": "heurístico",
    "hidrometeorologica": "hidrometeorológica",
    "hidrometeorologicas": "hidrometeorológicas",
    "hidrometeorologico": "hidrometeorológico",
    "hipotesis": "hipótesis",
    "historica": "histórica",
    "historico": "histórico",
    "identificacion": "identificación",
    "impermeabilizacion": "impermeabilización",
    "implementacion": "implementación",
    "indice": "índice",
    "informacion": "información",
    "integracion": "integración",
    "interaccion": "interacción",
    "linea": "línea",
    "lineas": "líneas",
    "logica": "lógica",
    "logico": "lógico",
    "maquina": "máquina",
    # "mas" -> "más" se agrega aqui ya que en textos tecnicos casi siempre es adverbio
    "mas": "más",
    "matematica": "matemática",
    "matematico": "matemático",
    "maximo": "máximo",
    "maxima": "máxima",
    "mecanica": "mecánica",
    "mecanico": "mecánico",
    "metaheuristica": "metaheurística",
    "metaheuristicas": "metaheurísticas",
    "meteorologica": "meteorológica",
    "meteorologicas": "meteorológicas",
    "meteorologico": "meteorológico",
    "metodo": "método",
    "metodos": "métodos",
    "metodologia": "metodología",
    "metrica": "métrica",
    "metricas": "métricas",
    "minimo": "mínimo",
    "minima": "mínima",
    "montana": "montaña",
    "montanas": "montañas",
    "multiples": "múltiples",
    "navegacion": "navegación",
    "numero": "número",
    "numeros": "números",
    "operacion": "operación",
    "optimizacion": "optimización",
    "optima": "óptima",
    "optimo": "óptimo",
    "optimas": "óptimas",
    "optimos": "óptimos",
    "pagina": "página",
    "paginas": "páginas",
    "parametro": "parámetro",
    "parametros": "parámetros",
    "perdida": "pérdida",
    "perdidas": "pérdidas",
    "periodo": "período",
    "periodos": "períodos",
    "pluvial": "pluvial",  # no lleva tilde
    "politica": "política",
    "politico": "político",
    "poligono": "polígono",
    "poligonos": "polígonos",
    "practica": "práctica",
    "practicas": "prácticas",
    "practico": "práctico",
    "precipitacion": "precipitación",
    "presentacion": "presentación",
    "probabilidad": "probabilidad",  # no lleva tilde
    "problematica": "problemática",
    "procesamiento": "procesamiento",  # no lleva tilde
    "programacion": "programación",
    "pronostico": "pronóstico",
    "proximo": "próximo",
    "proxima": "próxima",
    "publico": "público",
    "publica": "pública",
    "publicas": "públicas",
    "publicos": "públicos",
    "rapida": "rápida",
    "rapido": "rápido",
    "reaccion": "reacción",
    "recuperacion": "recuperación",
    "reduccion": "reducción",
    "referencia": "referencia",  # no lleva tilde
    "region": "región",
    "regiones": "regiones",  # no lleva tilde
    "relacion": "relación",
    "repeticion": "repetición",
    "restriccion": "restricción",
    "restricciones": "restricciones",  # no lleva tilde
    "revision": "revisión",
    "rio": "río",
    "rios": "ríos",
    "seccion": "sección",
    "secciones": "secciones",  # no lleva tilde
    "segun": "según",
    "semantica": "semántica",
    "semantico": "semántico",
    "simulacion": "simulación",
    "sintaxis": "sintaxis",  # no lleva tilde
    "sismica": "sísmica",
    "sismico": "sísmico",
    "solucion": "solución",
    "soluciones": "soluciones",  # no lleva tilde
    "tecnologia": "tecnología",
    "tecnologias": "tecnologías",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnico": "técnico",
    "tecnicos": "técnicos",
    "teoria": "teoría",
    "teorico": "teórico",
    "topologia": "topología",
    "topologica": "topológica",
    "topologico": "topológico",
    "topografia": "topografía",
    "trafico": "tráfico",
    "transformacion": "transformación",
    "transito": "tránsito",
    "unico": "único",
    "unica": "única",
    "unicos": "únicos",
    "unicas": "únicas",
    "utilizacion": "utilización",
    "validacion": "validación",
    "vehicular": "vehicular",  # no lleva tilde
    "vehiculo": "vehículo",
    "vehiculos": "vehículos",
    "via": "vía",
    "vias": "vías",
    "visualizacion": "visualización",
    "zoologico": "zoológico",
    # Palabras geograficas
    "America": "América",
    "Asuncion": "Asunción",
    "Concepcion": "Concepción",
    "Latinoamerica": "Latinoamérica",
    "Pacifico": "Pacífico",
    "Atlantico": "Atlántico",
    # Verbos y formas verbales - SOLO los que no son ambiguos
    # NO incluir: calculo, desarrollo, diseno, estudio, implemento (pueden ser sustantivos)
    "estan": "están",
    "asi": "así",
    "analizo": "analizó",
    "encontro": "encontró",
    "identifico": "identificó",
    "realizo": "realizó",
    "utilizo": "utilizó",
    # Adverbios y conectores
    "ademas": "además",
    "aqui": "aquí",
    "alli": "allí",
    "detras": "detrás",
    "despues": "después",
    "tambien": "también",
    "todavia": "todavía",
    "ultima": "última",
    "ultimas": "últimas",
    "ultimo": "último",
    "ultimos": "últimos",
    # Otras palabras frecuentes
    "algun": "algún",
    "comun": "común",
    "facil": "fácil",
    "dificil": "difícil",
    "util": "útil",
    "inutil": "inútil",
    "rapido": "rápido",
    "valido": "válido",
    "valida": "válida",
}

# Palabras que NO deben cambiarse (son correctas sin tilde o son homografos)
# Estas se excluyen del reemplazo automatico
EXCEPTIONS = {
    "esta",  # puede ser demostrativo "esta casa" vs "está" verbo
    "como",  # puede ser "como" (manera) vs "cómo" (interrogativo)
    "que",   # puede ser "que" (relativo) vs "qué" (interrogativo)
    "donde", # puede ser "donde" (relativo) vs "dónde" (interrogativo)
    "cuando",# puede ser "cuando" (relativo) vs "cuándo" (interrogativo)
    "cual",  # puede ser "cual" (relativo) vs "cuál" (interrogativo)
    "quien", # puede ser "quien" (relativo) vs "quién" (interrogativo)
    "solo",  # puede ser "solo" (adjetivo/adverbio) - la RAE acepta sin tilde
    "aun",   # puede ser "aun" (incluso) vs "aún" (todavía)
    "de",    # preposicion, no "dé" (verbo dar)
    "se",    # pronombre, no "sé" (verbo saber)
    "te",    # pronombre, no "té" (bebida)
    "mi",    # posesivo, no "mí" (pronombre)
    "tu",    # posesivo, no "tú" (pronombre)
    "el",    # articulo, no "él" (pronombre)
    "si",    # condicional, no "sí" (afirmativo)
    # "mas" se maneja aparte - casi siempre es "más" en textos modernos
}

# Palabras adicionales terminadas en -cion que necesitan -ción
CION_WORDS = [
    "aceleracion", "actualizacion", "administracion", "adquisicion", "agregacion",
    "alimentacion", "ampliacion", "animacion", "aplicacion", "aproximacion",
    "asignacion", "asociacion", "autenticacion", "automatizacion", "calibracion",
    "clasificacion", "comunicacion", "concatenacion", "concentracion", "condicion",
    "configuracion", "construccion", "continuacion", "contribucion", "conversion",
    "coordinacion", "correlacion", "creacion", "declaracion", "degradacion",
    "demostracion", "depreciacion", "derivacion", "descomposicion", "destinacion",
    "deteccion", "determinacion", "dimension", "discriminacion", "documentacion",
    "edicion", "educacion", "eleccion", "eliminacion", "ejecucion", "emision",
    "estimacion", "evacuacion", "excepcion", "expansion", "exploracion",
    "exportacion", "extension", "fabricacion", "fijacion", "filtracion",
    "fluctuacion", "formacion", "fragmentacion", "fundacion", "generacion",
    "geocodificacion", "geolocalizacion", "graduacion", "ilustracion",
    "incorporacion", "indexacion", "indicacion", "inicializacion", "innovacion",
    "insercion", "instalacion", "intensificacion", "interpolacion", "interpretacion",
    "inundacion", "investigacion", "iteracion", "justificacion", "liberacion",
    "limitacion", "localizacion", "manifestacion", "manipulacion", "marginacion",
    "migracion", "minimizacion", "mitigacion", "modificacion", "motivacion", "multiplicacion",
    "normalizacion", "notacion", "notificacion", "observacion", "ocupacion",
    "operacion", "ordenacion", "organizacion", "orientacion", "oscilacion",
    "paginacion", "paralelizacion", "parametrizacion", "participacion", "penalizacion", "percepcion",
    "planificacion", "poblacion", "polarizacion", "popularizacion", "posicion",
    "prediccion", "preparacion", "preservacion", "prevencion", "priorizacion",
    "procesacion", "produccion", "programacion", "promocion", "propagacion",
    "proposicion", "proteccion", "proyeccion", "publicacion", "puntuacion",
    "ramificacion", "reaccion", "reactivacion", "recomendacion", "reconciliacion",
    "recuperacion", "reduccion", "reeleccion", "referenciacion", "reflexion",
    "regeneracion", "regulacion", "reiteracion", "relocalizacion", "remocion",
    "renovacion", "replicacion", "representacion", "reproduccion", "resolucion",
    "restauracion", "restriccion", "retribucion", "retroalimentacion", "rotacion",
    "satisfaccion", "saturacion", "seccion", "segmentacion", "seleccion", "sensacion",
    "separacion", "serializacion", "sincronizacion", "situacion", "solucion",
    "subdivisicion", "sumarizacion", "sustitucion", "terminacion", "transaccion",
    "transcripcion", "transferencia", "transicion", "traduccion", "triangulacion",
    "ubicacion", "utilizacion", "validacion", "valoracion", "variacion",
    "verificacion", "vinculacion", "virtualizacion", "visualizacion",
]

# Agregar al diccionario
for word in CION_WORDS:
    if word not in ACCENT_FIXES:
        ACCENT_FIXES[word] = word.replace("cion", "ción")

def fix_accents_in_text(text: str) -> tuple[str, list[tuple[str, str, int]]]:
    """
    Corrige tildes faltantes en el texto.
    Retorna el texto corregido y una lista de cambios realizados.
    """
    changes = []

    # Palabras ambiguas que pueden ser verbo o sustantivo
    # Se reemplazan como sustantivos cuando van precedidas de articulos/preposiciones
    AMBIGUOUS_NOUNS = {
        "calculo": "cálculo",
        "diseno": "diseño",
        "estudio": "estudio",  # sustantivo no lleva tilde!
        "desarrollo": "desarrollo",  # sustantivo no lleva tilde!
    }

    # Patron para sustantivos precedidos de articulos o preposiciones
    # Ejemplos: "el calculo", "del calculo", "un estudio", "de desarrollo"
    articles_prep = r'(?:el|la|los|las|un|una|unos|unas|del|de|al|en|con|para|por|su|este|esta|ese|esa|nuestro|nuestra)\s+'

    for wrong, correct in AMBIGUOUS_NOUNS.items():
        if wrong == correct:
            continue
        # Solo reemplazar cuando es claramente un sustantivo
        pattern = r'(' + articles_prep + r')(' + re.escape(wrong) + r')(?![a-zA-Z])'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            def replace_noun(match):
                prefix = match.group(1)
                word = match.group(2)
                if word.isupper():
                    return prefix + correct.upper()
                elif word[0].isupper():
                    return prefix + correct.capitalize()
                else:
                    return prefix + correct
            new_text = re.sub(pattern, replace_noun, text, flags=re.IGNORECASE)
            if new_text != text:
                changes.append((wrong, correct, len(matches)))
                text = new_text

    # Procesar cada palabra del diccionario
    for wrong, correct in ACCENT_FIXES.items():
        if wrong == correct:
            continue  # Saltar si no hay cambio

        if wrong in EXCEPTIONS:
            continue  # Saltar excepciones

        # Crear patron que busca la palabra completa (word boundary)
        # Pero respetando que en LaTeX puede haber comandos
        # Buscar variantes: inicio de palabra, fin de palabra

        # Patron para palabra completa (no dentro de comandos LaTeX)
        # Evitar reemplazar dentro de \comando{...} o URLs
        pattern = r'(?<![\\a-zA-Z])' + re.escape(wrong) + r'(?![a-zA-Z])'

        # Contar ocurrencias antes
        matches = list(re.finditer(pattern, text, re.IGNORECASE))

        if matches:
            # Realizar reemplazo preservando mayusculas/minusculas
            def replace_preserving_case(match):
                original = match.group(0)
                if original.isupper():
                    return correct.upper()
                elif original[0].isupper():
                    return correct.capitalize()
                else:
                    return correct

            new_text = re.sub(pattern, replace_preserving_case, text, flags=re.IGNORECASE)

            if new_text != text:
                changes.append((wrong, correct, len(matches)))
                text = new_text

    return text, changes


def process_latex_file(filepath: Path, dry_run: bool = False) -> None:
    """
    Procesa un archivo LaTeX y corrige las tildes.
    """
    print(f"\nProcesando: {filepath}")
    print("-" * 60)

    # Leer archivo
    content = filepath.read_text(encoding='utf-8')

    # Aplicar correcciones
    corrected, changes = fix_accents_in_text(content)

    if not changes:
        print("No se encontraron palabras para corregir.")
        return

    # Mostrar cambios
    print(f"Cambios encontrados ({len(changes)} tipos de palabras):")
    total_fixes = 0
    for wrong, correct, count in sorted(changes, key=lambda x: -x[2]):
        print(f"  {wrong:30} -> {correct:30} ({count} ocurrencias)")
        total_fixes += count

    print(f"\nTotal de correcciones: {total_fixes}")

    if dry_run:
        print("\n[MODO DRY-RUN] No se guardaron cambios.")
    else:
        # Crear backup
        backup_path = filepath.with_suffix('.tex.bak')
        filepath.rename(backup_path)
        print(f"Backup creado: {backup_path}")

        # Guardar archivo corregido
        filepath.write_text(corrected, encoding='utf-8')
        print(f"Archivo corregido guardado: {filepath}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Corrige tildes faltantes en archivos LaTeX en español'
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Archivos LaTeX a procesar'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Solo mostrar cambios sin aplicarlos'
    )

    args = parser.parse_args()

    for filepath in args.files:
        if not filepath.exists():
            print(f"Error: No existe el archivo {filepath}")
            continue
        if not filepath.suffix == '.tex':
            print(f"Advertencia: {filepath} no es un archivo .tex")

        process_latex_file(filepath, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
