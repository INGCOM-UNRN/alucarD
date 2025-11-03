"""
Tests para los renderers HTML y PDF
"""
import pytest
from pathlib import Path
from generador_examenes.generators.html_renderer import HtmlRenderer
from generador_examenes.generators.pdf_renderer import PdfRenderer
from generador_examenes.generators import obtener_renderer, RENDERERS_REGISTRY
from generador_examenes.core.models import (
    Pregunta, Opcion, DefinicionExamen, SeccionExamen,
    PoolConfig, ConfiguracionExamen
)


@pytest.fixture
def definicion_ejemplo():
    """Fixture con definición de examen de ejemplo"""
    config = ConfiguracionExamen()
    seccion = SeccionExamen(
        nombre="Sección A",
        instrucciones="Lee cuidadosamente",
        pools=[PoolConfig()]
    )
    
    return DefinicionExamen(
        nombre_examen="Examen de Prueba",
        institucion="Universidad Test",
        materia="Matemáticas",
        fecha="2024-06-15",
        duracion_minutos=90,
        idioma="es",
        configuracion_examen=config,
        secciones_examen=[seccion]
    )


@pytest.fixture
def examen_data():
    """Fixture con datos de examen"""
    preguntas = [
        Pregunta(
            id="p1",
            tipo="seleccion_multiple",
            nombre="Pregunta 1",
            categoria="Matemáticas",
            enunciado_html="¿Cuánto es 2+2?",
            puntaje=2.0,
            opciones=[
                Opcion(texto_html="3", es_correcta=False),
                Opcion(texto_html="4", es_correcta=True),
                Opcion(texto_html="5", es_correcta=False),
            ]
        ),
        Pregunta(
            id="p2",
            tipo="verdadero_falso",
            nombre="Pregunta 2",
            categoria="Matemáticas",
            enunciado_html="2x2 = 4",
            puntaje=1.0,
            opciones=[
                Opcion(texto_html="Verdadero", es_correcta=True),
                Opcion(texto_html="Falso", es_correcta=False),
            ]
        ),
    ]
    
    return {
        'secciones': [{
            'nombre': 'Sección A',
            'instrucciones': 'Lee cuidadosamente',
            'preguntas': preguntas
        }]
    }


class TestHtmlRenderer:
    """Tests para HtmlRenderer"""
    
    def test_extensiones_soportadas(self):
        """Debe retornar formato correcto"""
        formatos = HtmlRenderer.get_supported_formats()
        assert 'html' in formatos
    
    def test_inicializacion(self):
        """Debe inicializar correctamente"""
        renderer = HtmlRenderer()
        assert renderer.templates_dir.exists()
        assert renderer.env is not None
    
    def test_inicializacion_con_directorio_custom(self, tmp_path):
        """Debe permitir directorio custom de templates"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Crear un template mínimo
        (templates_dir / "base_examen.html.j2").write_text("<html>Test</html>")
        
        renderer = HtmlRenderer(templates_dir)
        assert renderer.templates_dir == templates_dir
    
    def test_inicializacion_directorio_inexistente(self):
        """Debe fallar con directorio inexistente"""
        with pytest.raises(ValueError):
            HtmlRenderer(Path("/directorio/inexistente"))
    
    def test_cargar_i18n_es(self):
        """Debe cargar traducciones en español"""
        renderer = HtmlRenderer()
        i18n = renderer._cargar_i18n("es")
        assert "exam_title" in i18n
        assert i18n["exam_title"] == "Examen"
    
    def test_cargar_i18n_en(self):
        """Debe cargar traducciones en inglés"""
        renderer = HtmlRenderer()
        i18n = renderer._cargar_i18n("en")
        assert "exam_title" in i18n
        assert i18n["exam_title"] == "Exam"
    
    def test_cargar_i18n_idioma_inexistente(self):
        """Debe usar español por defecto si idioma no existe"""
        renderer = HtmlRenderer()
        i18n = renderer._cargar_i18n("fr")  # francés no existe
        # Debe cargar español por defecto
        assert "exam_title" in i18n
    
    def test_renderizar_examen(self, tmp_path, definicion_ejemplo, examen_data):
        """Debe generar HTML de examen"""
        renderer = HtmlRenderer()
        output_file = renderer.renderizar_examen(
            examen_data,
            definicion_ejemplo,
            tmp_path,
            tema=0
        )
        
        assert output_file.exists()
        assert output_file.name == "examen_tema_01.html"
        
        # Verificar contenido
        contenido = output_file.read_text(encoding='utf-8')
        assert "Examen de Prueba" in contenido
        assert "Universidad Test" in contenido
        assert "Matemáticas" in contenido
        assert "¿Cuánto es 2+2?" in contenido
    
    def test_renderizar_clave(self, tmp_path, definicion_ejemplo, examen_data):
        """Debe generar HTML de clave"""
        renderer = HtmlRenderer()
        output_file = renderer.renderizar_clave(
            examen_data,
            definicion_ejemplo,
            tmp_path,
            tema=0
        )
        
        assert output_file.exists()
        assert output_file.name == "clave_tema_01.html"
        
        # Verificar contenido
        contenido = output_file.read_text(encoding='utf-8')
        assert "Clave de Respuestas" in contenido
        assert "CONFIDENCIAL" in contenido
    
    def test_renderizar_multiples_temas(self, tmp_path, definicion_ejemplo, examen_data):
        """Debe generar múltiples temas"""
        renderer = HtmlRenderer()
        
        for tema in range(3):
            output_file = renderer.renderizar_examen(
                examen_data,
                definicion_ejemplo,
                tmp_path,
                tema=tema
            )
            assert output_file.exists()
        
        # Verificar que se crearon 3 archivos
        archivos = list(tmp_path.glob("examen_tema_*.html"))
        assert len(archivos) == 3
    
    def test_renderizar_idioma_ingles(self, tmp_path, examen_data):
        """Debe renderizar en inglés"""
        config = ConfiguracionExamen()
        seccion = SeccionExamen(nombre="Section A", pools=[PoolConfig()])
        
        definicion = DefinicionExamen(
            nombre_examen="Test Exam",
            institucion="Test University",
            materia="Math",
            idioma="en",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        renderer = HtmlRenderer()
        output_file = renderer.renderizar_examen(examen_data, definicion, tmp_path, 0)
        
        contenido = output_file.read_text(encoding='utf-8')
        assert "Exam" in contenido  # Palabra en inglés


class TestPdfRenderer:
    """Tests para PdfRenderer"""
    
    def test_extensiones_soportadas(self):
        """Debe retornar formato correcto"""
        formatos = PdfRenderer.get_supported_formats()
        assert 'pdf' in formatos
    
    def test_inicializacion(self):
        """Debe inicializar con HtmlRenderer"""
        try:
            renderer = PdfRenderer()
            assert renderer.html_renderer is not None
            assert hasattr(renderer, 'HTML')
        except ImportError:
            # WeasyPrint no instalado, skip test
            pytest.skip("WeasyPrint no instalado")
    
    @pytest.mark.skipif(True, reason="WeasyPrint requiere dependencias del sistema")
    def test_renderizar_examen_pdf(self, tmp_path, definicion_ejemplo, examen_data):
        """Debe generar PDF de examen"""
        try:
            renderer = PdfRenderer()
            output_file = renderer.renderizar_examen(
                examen_data,
                definicion_ejemplo,
                tmp_path,
                tema=0
            )
            
            assert output_file.exists()
            assert output_file.name == "examen_tema_01.pdf"
            assert output_file.suffix == ".pdf"
        except ImportError:
            pytest.skip("WeasyPrint no instalado")
    
    @pytest.mark.skipif(True, reason="WeasyPrint requiere dependencias del sistema")
    def test_renderizar_clave_pdf(self, tmp_path, definicion_ejemplo, examen_data):
        """Debe generar PDF de clave"""
        try:
            renderer = PdfRenderer()
            output_file = renderer.renderizar_clave(
                examen_data,
                definicion_ejemplo,
                tmp_path,
                tema=0
            )
            
            assert output_file.exists()
            assert output_file.name == "clave_tema_01.pdf"
        except ImportError:
            pytest.skip("WeasyPrint no instalado")


class TestRegistroRenderers:
    """Tests para el registro de renderers"""
    
    def test_renderers_registrados(self):
        """Debe tener renderers registrados"""
        assert len(RENDERERS_REGISTRY) > 0
        assert 'html' in RENDERERS_REGISTRY
        assert 'pdf' in RENDERERS_REGISTRY
    
    def test_obtener_renderer_html(self):
        """Debe obtener renderer HTML"""
        renderer = obtener_renderer('html')
        assert isinstance(renderer, HtmlRenderer)
    
    def test_obtener_renderer_pdf(self):
        """Debe obtener renderer PDF"""
        try:
            renderer = obtener_renderer('pdf')
            assert isinstance(renderer, PdfRenderer)
        except ImportError:
            pytest.skip("WeasyPrint no instalado")
    
    def test_obtener_renderer_formato_no_soportado(self):
        """Debe fallar con formato no soportado"""
        with pytest.raises(ValueError) as exc_info:
            obtener_renderer('docx')
        assert "No hay renderer disponible" in str(exc_info.value)
    
    def test_obtener_renderer_case_insensitive(self):
        """Debe ser case-insensitive"""
        renderer1 = obtener_renderer('HTML')
        renderer2 = obtener_renderer('html')
        assert type(renderer1) == type(renderer2)
