"""daedalus — generador paramétrico de preguntas de C compiladas al vuelo.

Cada plantilla (`plantillas.py`) produce un snippet C con parámetros aleatorios;
el motor (`engine.py`) lo verifica en un directorio temporal (`sandbox.py`):
ejecutándolo, con los avisos de gcc para el comportamiento indefinido o
contando la memoria dinámica sin liberar, y deriva distractores verosímiles a
partir de errores típicos de los alumnos.
"""

from .engine import (
    ajustar_opciones,
    catalogo,
    exportar_gift,
    exportar_xml,
    plantillas_disponibles,
    sintetizar,
)
from .plantillas import SnippetGenerado
from .sandbox import compilar_y_ejecutar, diagnosticos, memoria_sin_liberar

__all__ = [
    "SnippetGenerado",
    "ajustar_opciones",
    "catalogo",
    "compilar_y_ejecutar",
    "diagnosticos",
    "exportar_gift",
    "exportar_xml",
    "memoria_sin_liberar",
    "plantillas_disponibles",
    "sintetizar",
]
