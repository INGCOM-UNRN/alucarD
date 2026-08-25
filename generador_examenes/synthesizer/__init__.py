"""daedalus — generador paramétrico de preguntas de C compiladas al vuelo.

Cada plantilla produce un snippet C con parámetros aleatorios, el motor lo
compila con GCC y lo ejecuta en un directorio temporal para determinar la
salida correcta (respuesta verificada al 100%) y deriva distractores
verosímiles a partir de errores típicos de los alumnos.
"""

from .engine import (
    SnippetGenerado,
    compilar_y_ejecutar,
    sintetizar,
    plantillas_disponibles,
    exportar_gift,
    exportar_xml,
)

__all__ = [
    "SnippetGenerado",
    "compilar_y_ejecutar",
    "sintetizar",
    "plantillas_disponibles",
    "exportar_gift",
    "exportar_xml",
]
