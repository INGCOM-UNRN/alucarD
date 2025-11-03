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
