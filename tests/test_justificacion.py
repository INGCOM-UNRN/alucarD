"""Sección «Justificación» con renglones debajo de las preguntas de selección múltiple."""
import pytest

from generador_examenes.core import logic
from generador_examenes.core.models import (
    ConfiguracionExamen, DefinicionExamen, Opcion, PoolConfig, Pregunta, SeccionExamen,
)
from generador_examenes.generators import pdf_renderer
from generador_examenes.generators.html_renderer import HtmlRenderer
from generador_examenes.generators.pdf_renderer import PdfRenderer


def _pregunta(pid: str, tipo: str = "seleccion_multiple", categoria: str = "a") -> Pregunta:
    return Pregunta(id=pid, tipo=tipo, nombre=pid, categoria=categoria, enunciado_html=f"¿{pid}?",
                    opciones=[Opcion(texto_html="sí", es_correcta=True), Opcion(texto_html="no", es_correcta=False)])


@pytest.fixture
def banco():
    preguntas = [_pregunta("mc1"), _pregunta("vf", tipo="verdadero_falso"), _pregunta("mc2", categoria="b")]
    return {p.id: p for p in preguntas}


def _definicion(pools, **config) -> DefinicionExamen:
    return DefinicionExamen(
        nombre_examen="P", institucion="I", materia="M",
        configuracion_examen=ConfiguracionExamen(**config),
        secciones_examen=[SeccionExamen(nombre="S", pools=pools)],
    )


def _lineas(examen):
    return {p.id: p.lineas_justificacion for s in examen["secciones"] for p in s["preguntas"]}


def test_por_omision_no_hay_justificacion(banco):
    examen = logic.construir_pool_examen(_definicion([PoolConfig(categoria="a")]), banco)
    assert not any(_lineas(examen).values())


def test_la_configuracion_la_suma_a_toda_la_seleccion_multiple(banco):
    examen = logic.construir_pool_examen(
        _definicion([PoolConfig(categoria="a"), PoolConfig(categoria="b")], lineas_justificacion=3), banco)
    assert _lineas(examen) == {"mc1": 3, "vf": None, "mc2": 3}  # verdadero/falso, tal cual


def test_cada_pool_puede_cambiarla_o_quitarla(banco):
    pools = [PoolConfig(categoria="a", lineas_justificacion=0), PoolConfig(categoria="b", lineas_justificacion=6)]
    examen = logic.construir_pool_examen(_definicion(pools, lineas_justificacion=3), banco)
    assert _lineas(examen) == {"mc1": 0, "vf": None, "mc2": 6}
    examen = logic.construir_pool_examen(  # también sin justificación general
        _definicion([PoolConfig(preguntas_fijadas=["mc2"], lineas_justificacion=2)]), banco)
    assert _lineas(examen) == {"mc2": 2}


def test_lineas_fuera_de_rango():
    with pytest.raises(ValueError):
        ConfiguracionExamen(lineas_justificacion=-1)
    with pytest.raises(ValueError):
        PoolConfig(lineas_justificacion=61)


def test_html_con_renglones_y_titulo(banco, tmp_path):
    definicion = _definicion([PoolConfig(categoria="a")], lineas_justificacion=4)
    examen = logic.construir_pool_examen(definicion, banco)
    html = HtmlRenderer().renderizar_examen(examen, definicion, tmp_path, 0).read_text(encoding="utf-8")
    assert html.count('class="justificacion"') == 1  # sólo la de selección múltiple
    assert html.count('class="renglon"') == 4
    assert "Justificación" in html

    definicion = _definicion([PoolConfig(categoria="a")], lineas_justificacion=2, titulo_justificacion="¿Por qué?")
    examen = logic.construir_pool_examen(definicion, banco)
    html = HtmlRenderer().renderizar_examen(examen, definicion, tmp_path, 0).read_text(encoding="utf-8")
    assert "¿Por qué?" in html and "Justificación" not in html


def test_pdf_con_renglones_y_titulo(banco, tmp_path, monkeypatch):
    fuentes = []
    compilar = pdf_renderer.compilar_typst_a_pdf

    def capturar(fuente, salida, root_dir=None):
        fuentes.append(fuente)
        return compilar(fuente, salida, root_dir=root_dir)

    monkeypatch.setattr(pdf_renderer, "compilar_typst_a_pdf", capturar)
    definicion = _definicion([PoolConfig(categoria="b")], lineas_justificacion=5)
    definicion = definicion.model_copy(update={"idioma": "en"})
    examen = logic.construir_pool_examen(definicion, banco)
    salida = PdfRenderer().renderizar_examen(examen, definicion, tmp_path, 0)
    assert salida.stat().st_size > 0
    assert "[Justification]" in fuentes[0]
    assert fuentes[0].count("height: 16pt") == 5
