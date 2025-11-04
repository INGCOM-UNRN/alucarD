"""
Tests para los diferentes layouts de secciones
"""
import pytest
from pathlib import Path
from generador_examenes.core.models import SeccionExamen, PoolConfig, DefinicionExamen


def test_seccion_layout_default():
    """Test layout por defecto"""
    seccion = SeccionExamen(
        nombre="Test Section",
        pools=[PoolConfig(cantidad=5)]
    )
    assert seccion.layout == "default"
    assert "default" not in str(seccion)  # No se muestra en el string


def test_seccion_layout_compact_2col():
    """Test layout compacto de 2 columnas"""
    seccion = SeccionExamen(
        nombre="Test Section",
        layout="compact-2col",
        pools=[PoolConfig(cantidad=10)]
    )
    assert seccion.layout == "compact-2col"
    assert "compact-2col" in str(seccion)


def test_seccion_layout_compact_3col():
    """Test layout compacto de 3 columnas"""
    seccion = SeccionExamen(
        nombre="Test Section",
        layout="compact-3col",
        pools=[PoolConfig(cantidad=15)]
    )
    assert seccion.layout == "compact-3col"
    assert "compact-3col" in str(seccion)


def test_seccion_layout_compact_4col():
    """Test layout compacto de 4 columnas"""
    seccion = SeccionExamen(
        nombre="Test Section",
        layout="compact-4col",
        pools=[PoolConfig(cantidad=20)]
    )
    assert seccion.layout == "compact-4col"
    assert "compact-4col" in str(seccion)


def test_seccion_layout_invalido():
    """Test que layout inválido falla validación"""
    with pytest.raises(Exception):
        SeccionExamen(
            nombre="Test",
            layout="invalid-layout",
            pools=[PoolConfig(cantidad=5)]
        )


def test_definicion_con_multiples_layouts():
    """Test definición con secciones de diferentes layouts"""
    from generador_examenes.core.models import ConfiguracionExamen
    
    definicion = DefinicionExamen(
        nombre_examen="Test",
        institucion="Test Uni",
        materia="Test Subject",
        configuracion_examen=ConfiguracionExamen(),
        secciones_examen=[
            SeccionExamen(
                nombre="Section 1",
                layout="default",
                pools=[PoolConfig(cantidad=5)]
            ),
            SeccionExamen(
                nombre="Section 2",
                layout="compact-2col",
                pools=[PoolConfig(cantidad=10)]
            ),
            SeccionExamen(
                nombre="Section 3",
                layout="compact-3col",
                pools=[PoolConfig(cantidad=15)]
            )
        ]
    )
    
    assert len(definicion.secciones_examen) == 3
    assert definicion.secciones_examen[0].layout == "default"
    assert definicion.secciones_examen[1].layout == "compact-2col"
    assert definicion.secciones_examen[2].layout == "compact-3col"


def test_repr_seccion_con_layout():
    """Test representación de sección con layout"""
    seccion = SeccionExamen(
        nombre="Test",
        layout="compact-2col",
        pools=[PoolConfig(cantidad=5)]
    )
    repr_str = repr(seccion)
    assert "compact-2col" in repr_str
    assert "Test" in repr_str


def test_yaml_con_layouts(tmp_path):
    """Test carga de YAML con layouts configurados"""
    import yaml
    from generador_examenes.core.models import DefinicionExamen
    
    yaml_content = """
nombre_examen: "Test Layouts"
institucion: "Test"
materia: "Test"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  - nombre: "Default Layout"
    pools:
      - cantidad: 5
    # layout: default es implícito
  
  - nombre: "Compact 2 Columns"
    layout: compact-2col
    pools:
      - cantidad: 10
  
  - nombre: "Compact 3 Columns"
    layout: compact-3col
    pools:
      - cantidad: 15
"""
    
    yaml_file = tmp_path / "test_layouts.yaml"
    yaml_file.write_text(yaml_content)
    
    with open(yaml_file) as f:
        data = yaml.safe_load(f)
    
    definicion = DefinicionExamen(**data)
    
    assert definicion.secciones_examen[0].layout == "default"
    assert definicion.secciones_examen[1].layout == "compact-2col"
    assert definicion.secciones_examen[2].layout == "compact-3col"


def test_html_render_con_layout_class(tmp_path):
    """Test que el HTML generado incluye la clase de layout"""
    from generador_examenes.generators.html_renderer import HtmlRenderer
    from generador_examenes.core.models import DefinicionExamen, Pregunta, Opcion, ConfiguracionExamen
    
    definicion = DefinicionExamen(
        nombre_examen="Test",
        institucion="Test",
        materia="Test",
        configuracion_examen=ConfiguracionExamen(),
        secciones_examen=[
            SeccionExamen(
                nombre="Compact Section",
                layout="compact-2col",
                pools=[PoolConfig(cantidad=2)]
            )
        ]
    )
    
    # Datos de ejemplo para renderizado
    examen_data = {
        'secciones': [{
            'nombre': 'Compact Section',
            'layout': 'compact-2col',
            'preguntas': [
                {
                    'id': 'p1',
                    'tipo': 'seleccion_multiple',
                    'enunciado_html': 'Test question',
                    'puntaje': 1.0,
                    'opciones': [
                        {'texto_html': 'A', 'es_correcta': True},
                        {'texto_html': 'B', 'es_correcta': False}
                    ]
                }
            ]
        }]
    }
    
    renderer = HtmlRenderer()
    output_dir = tmp_path
    
    output_file = renderer.renderizar_examen(
        examen_data=examen_data,
        definicion=definicion,
        output_dir=output_dir,
        tema=0
    )
    
    # Verificar que el archivo contiene la clase de layout
    html_content = output_file.read_text()
    assert 'class="section layout-compact-2col"' in html_content


def test_todos_los_layouts_validos():
    """Test que todos los valores de layout son válidos"""
    layouts_validos = ["default", "compact-2col", "compact-3col", "compact-4col"]
    
    for layout in layouts_validos:
        seccion = SeccionExamen(
            nombre=f"Test {layout}",
            layout=layout,
            pools=[PoolConfig(cantidad=5)]
        )
        assert seccion.layout == layout
