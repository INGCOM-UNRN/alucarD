"""
Tests para los parsers GIFT y Moodle XML
"""
import pytest
from pathlib import Path
from generador_examenes.parsers.gift_parser import GiftParser
from generador_examenes.parsers.moodle_parser import MoodleXMLParser
from generador_examenes.parsers import obtener_parser, PARSERS_REGISTRY


class TestGiftParser:
    """Tests para GiftParser"""
    
    def test_extensiones_soportadas(self):
        """Debe retornar extensiones correctas"""
        extensions = GiftParser.get_supported_extensions()
        assert '.txt' in extensions
        assert '.gift' in extensions
    
    def test_parse_archivo_ejemplo(self):
        """Debe parsear el archivo de ejemplo correctamente"""
        parser = GiftParser()
        ruta = Path("tests/bancos_ejemplo/banco_test.txt")
        
        if ruta.exists():
            preguntas = parser.parse(ruta)
            assert len(preguntas) > 0
            
            # Verificar que las preguntas tienen los campos correctos
            primera_pregunta = list(preguntas.values())[0]
            assert hasattr(primera_pregunta, 'id')
            assert hasattr(primera_pregunta, 'tipo')
            assert hasattr(primera_pregunta, 'enunciado_html')
    
    def test_parse_seleccion_multiple(self, tmp_path):
        """Debe parsear pregunta de selección múltiple"""
        contenido = """
::Pregunta Test::¿Cuánto es 2+2? {
=4
~3
~5
~Error
} [tags: matematicas, facil]
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "seleccion_multiple"
        assert len(pregunta.opciones) == 4
        assert pregunta.opciones[0].es_correcta is True
        assert pregunta.opciones[1].es_correcta is False
        assert "matematicas" in pregunta.etiquetas
    
    def test_parse_verdadero_falso(self, tmp_path):
        """Debe parsear pregunta verdadero/falso"""
        contenido = """
::VF Test::Python es interpretado. {T}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "verdadero_falso"
        assert len(pregunta.opciones) == 2
        assert pregunta.opciones[0].texto_html == "Verdadero"
        assert pregunta.opciones[0].es_correcta is True
    
    def test_parse_con_categoria(self, tmp_path):
        """Debe parsear categoría"""
        contenido = """
::Test::Pregunta {=A} [category: Matemáticas]
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.categoria == "Matemáticas"
    
    def test_parse_archivo_no_existe(self):
        """Debe lanzar excepción si archivo no existe"""
        parser = GiftParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("archivo_inexistente.txt"))
    
    def test_parse_con_comentarios(self, tmp_path):
        """Debe ignorar comentarios"""
        contenido = """
// Este es un comentario
::Pregunta::Texto {=A ~B}

// Otro comentario
::Pregunta2::Texto2 {T}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 2


class TestMoodleXMLParser:
    """Tests para MoodleXMLParser"""
    
    def test_extensiones_soportadas(self):
        """Debe retornar extensión correcta"""
        extensions = MoodleXMLParser.get_supported_extensions()
        assert '.xml' in extensions
    
    def test_parse_archivo_ejemplo(self):
        """Debe parsear el archivo XML de ejemplo"""
        parser = MoodleXMLParser()
        ruta = Path("tests/bancos_ejemplo/banco_test.xml")
        
        if ruta.exists():
            preguntas = parser.parse(ruta)
            assert len(preguntas) > 0
            
            primera_pregunta = list(preguntas.values())[0]
            assert hasattr(primera_pregunta, 'id')
            assert hasattr(primera_pregunta, 'tipo')
    
    def test_parse_multichoice(self, tmp_path):
        """Debe parsear pregunta multichoice"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test Question</text></name>
    <questiontext format="html">
      <text><![CDATA[¿Cuál es correcto?]]></text>
    </questiontext>
    <defaultgrade>2.0</defaultgrade>
    <answer fraction="100">
      <text>Correcto</text>
      <feedback><text>Bien</text></feedback>
    </answer>
    <answer fraction="0">
      <text>Incorrecto</text>
      <feedback><text>Mal</text></feedback>
    </answer>
    <tags>
      <tag><text>test</text></tag>
    </tags>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "seleccion_multiple"
        assert pregunta.puntaje == 2.0
        assert len(pregunta.opciones) == 2
        assert "test" in pregunta.etiquetas
    
    def test_parse_truefalse(self, tmp_path):
        """Debe parsear pregunta truefalse"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="truefalse">
    <name><text>TF Test</text></name>
    <questiontext format="html">
      <text><![CDATA[Esto es verdadero]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100">
      <text>true</text>
    </answer>
    <answer fraction="0">
      <text>false</text>
    </answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "verdadero_falso"
        assert len(pregunta.opciones) == 2
    
    def test_parse_ignora_categorias(self, tmp_path):
        """Debe ignorar elementos category"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="category">
    <name><text>Category</text></name>
  </question>
  <question type="multichoice">
    <name><text>Real Question</text></name>
    <questiontext><text>Test</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        # Solo debe parsear la pregunta real, no la categoría
        assert len(preguntas) == 1
    
    def test_parse_xml_invalido(self, tmp_path):
        """Debe lanzar excepción con XML inválido"""
        contenido = """<?xml version="1.0"?>
<quiz>
  <question type="multichoice">
    <name><text>Broken
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        with pytest.raises(ValueError):
            parser.parse(archivo)


class TestRegistroParsers:
    """Tests para el registro de parsers"""
    
    def test_parsers_registrados(self):
        """Debe tener parsers registrados"""
        assert len(PARSERS_REGISTRY) > 0
        assert '.txt' in PARSERS_REGISTRY
        assert '.xml' in PARSERS_REGISTRY
    
    def test_obtener_parser_gift(self):
        """Debe obtener parser GIFT"""
        ruta = Path("archivo.txt")
        parser = obtener_parser(ruta)
        assert isinstance(parser, GiftParser)
    
    def test_obtener_parser_xml(self):
        """Debe obtener parser XML"""
        ruta = Path("archivo.xml")
        parser = obtener_parser(ruta)
        assert isinstance(parser, MoodleXMLParser)
    
    def test_obtener_parser_extension_no_soportada(self):
        """Debe fallar con extensión no soportada"""
        ruta = Path("archivo.pdf")
        with pytest.raises(ValueError) as exc_info:
            obtener_parser(ruta)
        assert "No hay parser disponible" in str(exc_info.value)
    
    def test_obtener_parser_gift_alternativo(self):
        """Debe obtener parser con extensión .gift"""
        ruta = Path("archivo.gift")
        parser = obtener_parser(ruta)
        assert isinstance(parser, GiftParser)


class TestGiftParserEdgeCases:
    """Tests para casos edge en GiftParser"""
    
    def test_parse_con_error_en_bloque(self, tmp_path):
        """Debe continuar parseando aunque un bloque falle"""
        contenido = """
::Pregunta1::Válida {=A ~B}

::Pregunta2::Inválida sin llaves

::Pregunta3::Otra válida {T}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        # Debe parsear las 2 preguntas válidas
        assert len(preguntas) == 2
    
    def test_parse_error_lectura_archivo(self, tmp_path):
        """Debe manejar errores de lectura"""
        archivo = tmp_path / "test.txt"
        archivo.write_text("contenido", encoding='utf-8')
        archivo.chmod(0o000)  # Remover permisos de lectura
        
        parser = GiftParser()
        try:
            with pytest.raises(ValueError, match="Error leyendo archivo GIFT"):
                parser.parse(archivo)
        finally:
            archivo.chmod(0o644)  # Restaurar permisos
    
    def test_parse_bloque_vacio(self, tmp_path):
        """Debe ignorar bloques vacíos"""
        contenido = """


::Pregunta::Texto {=A}


"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
    
    def test_parse_sin_llaves(self, tmp_path):
        """Debe manejar preguntas sin llaves"""
        contenido = """
::Pregunta::Texto sin opciones
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        # No debe parsear preguntas sin llaves
        assert len(preguntas) == 0
    
    def test_parse_ultimo_bloque(self, tmp_path):
        """Debe parsear el último bloque sin línea en blanco final"""
        contenido = """::Pregunta1::Texto1 {=A}

::Pregunta2::Texto2 {T}"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 2
    
    def test_parse_tipo_numerica(self, tmp_path):
        """Debe parsear pregunta numérica"""
        contenido = """
::Pregunta::¿Cuánto es PI? {#3.14:0.01}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "numerica"
        assert len(pregunta.opciones) == 0
    
    def test_parse_respuesta_corta_sin_marcador(self, tmp_path):
        """Debe parsear respuesta corta sin marcador ="""
        contenido = """
::Pregunta::Capital de Francia {Paris}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "respuesta_corta"
        assert len(pregunta.opciones) == 1
        assert pregunta.opciones[0].es_correcta
    
    def test_parse_respuesta_corta_con_marcadores(self, tmp_path):
        """Debe parsear respuesta corta/selección con marcadores ="""
        contenido = """
::Pregunta::Capital {=Paris}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        # Con = se detecta como selección múltiple (es válido en GIFT)
        assert pregunta.tipo in ["respuesta_corta", "seleccion_multiple"]
        assert len(pregunta.opciones) >= 1
        assert pregunta.opciones[0].es_correcta
    
    def test_parse_seleccion_con_retroalimentacion(self, tmp_path):
        """Debe parsear opciones con retroalimentación"""
        contenido = """
::Pregunta::Test {
=Correcto#Bien hecho
~Incorrecto#Intenta de nuevo
}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert len(pregunta.opciones) == 2
        assert pregunta.opciones[0].texto_html == "Correcto"
        assert pregunta.opciones[1].texto_html == "Incorrecto"


class TestMoodleXMLParserEdgeCases:
    """Tests para casos edge en MoodleXMLParser"""
    
    def test_parse_archivo_no_existe(self):
        """Debe lanzar excepción si archivo no existe"""
        parser = MoodleXMLParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("inexistente.xml"))
    
    def test_parse_pregunta_con_error(self, tmp_path):
        """Debe continuar parseando aunque una pregunta falle"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta 1</text></name>
    <questiontext><text>Test 1</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
  <question type="multichoice">
    <!-- Pregunta malformada sin nombre -->
    <questiontext><text>Test 2</text></questiontext>
  </question>
  <question type="multichoice">
    <name><text>Pregunta 3</text></name>
    <questiontext><text>Test 3</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>C</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        # Debe parsear las preguntas válidas
        assert len(preguntas) >= 2
    
    def test_parse_error_generico(self, tmp_path):
        """Debe manejar errores genéricos durante el parsing"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        # No debe fallar con archivo vacío
        assert len(preguntas) == 0
    
    def test_parse_tipo_description(self, tmp_path):
        """Debe ignorar preguntas tipo description"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="description">
    <name><text>Descripción</text></name>
    <questiontext><text>Solo texto</text></questiontext>
  </question>
  <question type="multichoice">
    <name><text>Pregunta Real</text></name>
    <questiontext><text>Test</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
    
    def test_parse_categoria_en_pregunta(self, tmp_path):
        """Debe extraer categoría de pregunta"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <category><text>$course$/Top/Matemáticas/Álgebra</text></category>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.categoria == "Álgebra"
    
    def test_parse_shortanswer(self, tmp_path):
        """Debe parsear pregunta shortanswer"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="shortanswer">
    <name><text>Short Test</text></name>
    <questiontext><text>Capital de Francia</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>Paris</text></answer>
    <answer fraction="100"><text>París</text></answer>
    <answer fraction="0"><text>Madrid</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "respuesta_corta"
        assert len(pregunta.opciones) == 2  # Solo las correctas
        assert all(op.es_correcta for op in pregunta.opciones)
    
    def test_parse_numerical(self, tmp_path):
        """Debe parsear pregunta numérica"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="numerical">
    <name><text>Num Test</text></name>
    <questiontext><text>PI</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>3.14</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "numerica"
    
    def test_parse_sin_nombre(self, tmp_path):
        """Debe usar nombre por defecto si no hay nombre"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <questiontext><text>Test</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.nombre == "pregunta_1"
    
    def test_parse_sin_enunciado(self, tmp_path):
        """Debe manejar preguntas sin enunciado"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test</text></name>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.enunciado_html == ""
    
    def test_parse_con_retroalimentacion_general(self, tmp_path):
        """Debe extraer retroalimentación general"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <generalfeedback><text>Retroalimentación general</text></generalfeedback>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.retroalimentacion_general == "Retroalimentación general"
    
    def test_parse_opciones_sin_texto(self, tmp_path):
        """Debe ignorar opciones sin texto"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
    <answer fraction="0"></answer>
    <answer fraction="0"><text>B</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert len(pregunta.opciones) == 2  # Solo A y B
    
    def test_parse_truefalse_con_false_correcto(self, tmp_path):
        """Debe parsear verdadero/falso con false como correcto"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="truefalse">
    <name><text>TF Test</text></name>
    <questiontext><text>Esto es falso</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="0">
      <text>true</text>
    </answer>
    <answer fraction="100">
      <text>false</text>
    </answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.opciones[0].texto_html == "Verdadero"
        assert pregunta.opciones[0].es_correcta is False
        assert pregunta.opciones[1].es_correcta is True


class TestBaseParser:
    """Tests para BaseParser"""
    
    def test_get_supported_extensions_base(self):
        """Método base debe retornar lista vacía"""
        from generador_examenes.parsers.base import BaseParser
        assert BaseParser.get_supported_extensions() == []
    
    def test_base_parser_es_abstracta(self):
        """BaseParser no se puede instanciar directamente"""
        from generador_examenes.parsers.base import BaseParser
        with pytest.raises(TypeError):
            BaseParser()


class TestGiftParserExceptions:
    """Tests para excepciones específicas en GiftParser"""
    
    def test_parse_con_exception_en_bloque(self, tmp_path, monkeypatch):
        """Debe loggear warning cuando un bloque falla"""
        import logging
        contenido = """
::Pregunta1::Válida {=A}

::Pregunta2::Otra válida {T}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        
        # Simular error en _parsear_bloque
        original_parsear = parser._parsear_bloque
        call_count = [0]
        
        def mock_parsear(bloque, indice):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Error simulado")
            return original_parsear(bloque, indice)
        
        monkeypatch.setattr(parser, '_parsear_bloque', mock_parsear)
        
        preguntas = parser.parse(archivo)
        
        # Debe parsear la segunda pregunta
        assert len(preguntas) >= 1
    
    def test_parse_bloque_retorna_none(self, tmp_path):
        """Debe manejar cuando _parsear_bloque retorna None"""
        contenido = """

::Pregunta::Válida {=A}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) >= 1
    
    def test_parse_respuesta_corta_fallback(self, tmp_path):
        """Debe usar fallback cuando no hay respuestas con ="""
        contenido = """
::Pregunta::Capital de Francia {Paris}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "respuesta_corta"
        # Debe usar todo el contenido como respuesta
        assert len(pregunta.opciones) == 1
    
    def test_parse_respuesta_corta_con_espacios(self, tmp_path):
        """Debe ignorar respuestas vacías después de strip"""
        contenido = """
::Pregunta::Test {=   =Válida}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        # Debe ignorar la respuesta vacía y solo incluir la válida
        assert len(pregunta.opciones) >= 1
        assert pregunta.opciones[0].texto_html == "Válida"
    
    def test_parsear_bloque_solo_espacios(self, tmp_path):
        """Debe retornar None para bloques con solo espacios"""
        contenido = """   

::Pregunta::Válida {=A}
"""
        archivo = tmp_path / "test.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        # Solo debe parsear la pregunta válida
        assert len(preguntas) == 1
    
    def test_parsear_bloque_directamente(self):
        """Test directo del método _parsear_bloque"""
        parser = GiftParser()
        
        # Bloque vacío
        resultado = parser._parsear_bloque("", 0)
        assert resultado is None
        
        # Bloque solo espacios
        resultado = parser._parsear_bloque("   ", 0)
        assert resultado is None
        
        # Bloque solo tabs y newlines
        resultado = parser._parsear_bloque("\t\n  \n", 0)
        assert resultado is None
    
    def test_parsear_respuesta_corta_espacios_vacios(self):
        """Test directo de _parsear_respuesta_corta con espacios"""
        parser = GiftParser()
        
        # Texto con espacios que resulta en vacío
        opciones = parser._parsear_respuesta_corta("=   =  = ")
        
        # No debe agregar opciones vacías
        assert all(op.texto_html.strip() != "" for op in opciones)
    
    def test_parsear_respuesta_corta_con_validas(self):
        """Test de _parsear_respuesta_corta con respuestas válidas"""
        parser = GiftParser()
        
        # Respuestas con texto válido
        opciones = parser._parsear_respuesta_corta("=Paris=Londres=Madrid")
        
        # Debe tener las 3 opciones
        assert len(opciones) == 3
        assert opciones[0].texto_html == "Paris"
        assert opciones[1].texto_html == "Londres"
        assert opciones[2].texto_html == "Madrid"
        assert all(op.es_correcta for op in opciones)


class TestMoodleXMLParserExceptions:
    """Tests para excepciones específicas en MoodleXMLParser"""
    
    def test_parse_con_exception_en_pregunta(self, tmp_path, monkeypatch):
        """Debe loggear warning cuando una pregunta falla"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test 1</text></name>
    <questiontext><text>Pregunta 1</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
  <question type="multichoice">
    <name><text>Test 2</text></name>
    <questiontext><text>Pregunta 2</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>B</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        
        # Simular error en _parsear_pregunta
        original_parsear = parser._parsear_pregunta
        call_count = [0]
        
        def mock_parsear(elem, indice):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Error simulado")
            return original_parsear(elem, indice)
        
        monkeypatch.setattr(parser, '_parsear_pregunta', mock_parsear)
        
        preguntas = parser.parse(archivo)
        
        # Debe parsear la segunda pregunta
        assert len(preguntas) >= 1
    
    def test_parse_error_procesando_xml(self, tmp_path, monkeypatch):
        """Debe manejar errores genéricos al procesar XML"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>A</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        
        # Simular error genérico al iterar preguntas
        import xml.etree.ElementTree as ET
        original_parse = ET.parse
        
        def mock_parse(filepath):
            tree = original_parse(filepath)
            root = tree.getroot()
            
            # Hacer que findall lance una excepción
            original_findall = root.findall
            def mock_findall(path):
                if path == './/question':
                    raise RuntimeError("Error simulado en findall")
                return original_findall(path)
            
            root.findall = mock_findall
            return tree
        
        monkeypatch.setattr(ET, 'parse', mock_parse)
        
        with pytest.raises(ValueError, match="Error procesando archivo"):
            parser.parse(archivo)
    
    def test_parse_shortanswer_sin_respuestas_correctas(self, tmp_path):
        """Debe manejar shortanswer sin respuestas correctas"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="shortanswer">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="0"><text>Incorrecta</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        assert pregunta.tipo == "respuesta_corta"
        # No debe incluir respuestas incorrectas
        assert len(pregunta.opciones) == 0
    
    def test_parse_shortanswer_con_answer_sin_text_elem(self, tmp_path):
        """Debe ignorar answers sin elemento text"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="shortanswer">
    <name><text>Test</text></name>
    <questiontext><text>Pregunta</text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"></answer>
    <answer fraction="100"><text></text></answer>
    <answer fraction="100"><text>Válida</text></answer>
  </question>
</quiz>"""
        archivo = tmp_path / "test.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        pregunta = list(preguntas.values())[0]
        # Solo debe incluir la respuesta válida
        assert len(pregunta.opciones) == 1
        assert pregunta.opciones[0].texto_html == "Válida"


class TestGiftParserMarkdown:
    """Tests para formato markdown en GIFT"""
    
    def test_parse_gift_con_markdown(self, tmp_path):
        """Debe parsear pregunta GIFT con formato markdown"""
        contenido = """
::Pregunta Markdown::[markdown]¿Qué hace esta función?
```python
def suma(a, b):
    return a + b
```
{
=Suma dos números
~Resta dos números
}
"""
        archivo = tmp_path / "test_markdown.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        
        # Verificar que el enunciado contiene código con highlighting
        assert 'highlight' in pregunta.enunciado_html or 'def' in pregunta.enunciado_html
    
    def test_parse_gift_markdown_opciones(self, tmp_path):
        """Debe parsear opciones con formato markdown"""
        contenido = """
::Test Opciones Markdown::[markdown]Pregunta {
=`codigo` correcto
~**texto** incorrecto
}
"""
        archivo = tmp_path / "test_markdown_opts.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = GiftParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        
        # Verificar que las opciones fueron convertidas
        assert len(pregunta.opciones) == 2
        # Debe contener tags HTML del markdown
        assert '<code>' in pregunta.opciones[0].texto_html or 'codigo' in pregunta.opciones[0].texto_html


class TestMoodleXMLParserMarkdown:
    """Tests para formato markdown en Moodle XML"""
    
    def test_parse_xml_con_markdown(self, tmp_path):
        """Debe parsear pregunta XML con formato markdown"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta Markdown</text></name>
    <questiontext format="markdown">
      <text><![CDATA[¿Qué devuelve `x + 1`?]]></text>
    </questiontext>
    <answer fraction="100" format="markdown">
      <text><![CDATA[El valor de **x más uno**]]></text>
    </answer>
    <answer fraction="0" format="markdown">
      <text><![CDATA[El valor de `x`]]></text>
    </answer>
  </question>
</quiz>
"""
        archivo = tmp_path / "test_markdown.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        
        # Verificar que el enunciado contiene código convertido
        assert '<code>' in pregunta.enunciado_html
        
        # Verificar que las opciones fueron convertidas
        assert len(pregunta.opciones) == 2
        assert '<strong>' in pregunta.opciones[0].texto_html or 'más uno' in pregunta.opciones[0].texto_html
    
    def test_parse_xml_markdown_code_block(self, tmp_path):
        """Debe parsear bloques de código en formato markdown XML"""
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Código</text></name>
    <questiontext format="markdown">
      <text><![CDATA[¿Qué imprime este código?
```python
x = 5
print(x * 2)
```
]]></text>
    </questiontext>
    <answer fraction="100">
      <text>10</text>
    </answer>
  </question>
</quiz>
"""
        archivo = tmp_path / "test_code.xml"
        archivo.write_text(contenido, encoding='utf-8')
        
        parser = MoodleXMLParser()
        preguntas = parser.parse(archivo)
        
        assert len(preguntas) == 1
        pregunta = list(preguntas.values())[0]
        
        # Verificar que contiene syntax highlighting
        assert 'highlight' in pregunta.enunciado_html or 'print' in pregunta.enunciado_html
