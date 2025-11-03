"""
Configuración de pytest y fixtures globales
"""
import pytest
import logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging después de cada test"""
    yield
    # Limpiar handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


@pytest.fixture
def sample_gift_content():
    """Contenido GIFT de ejemplo"""
    return """
// Banco de preguntas de prueba

::Pregunta 1::¿Cuánto es 2+2? {
=4
~3
~5
~Error
} [tags: matematicas, facil]

::Pregunta 2::Python es interpretado. {T} [tags: programacion]

::Pregunta 3::¿Qué es un compilador? {
=Un programa que traduce código
~Un editor de texto
~Un debugger
} [category: Programación]
"""


@pytest.fixture
def sample_xml_content():
    """Contenido XML de ejemplo"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test Question</text></name>
    <questiontext format="html">
      <text><![CDATA[¿Cuál es correcto?]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100">
      <text>Opción A</text>
    </answer>
    <answer fraction="0">
      <text>Opción B</text>
    </answer>
    <tags>
      <tag><text>test</text></tag>
    </tags>
  </question>
</quiz>
"""


@pytest.fixture
def sample_definicion_yaml():
    """Definición YAML de ejemplo"""
    return {
        "nombre_examen": "Examen de Prueba",
        "institucion": "Universidad Test",
        "materia": "Matemáticas",
        "fecha": "2024-06-15",
        "duracion_minutos": 90,
        "idioma": "es",
        "configuracion_examen": {
            "mezclar_preguntas_dentro_seccion": True,
            "mezclar_opciones_dentro_pregunta": True,
            "generar_clave_profesor": True
        },
        "secciones_examen": [
            {
                "nombre": "Sección A",
                "instrucciones": "Responde todas las preguntas",
                "pools": [
                    {
                        "cantidad": 5,
                        "accion_si_insuficiente": "usar_todas"
                    }
                ]
            }
        ]
    }
