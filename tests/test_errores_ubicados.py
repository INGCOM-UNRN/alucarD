"""Los errores dicen en qué pregunta, sección o pool están, no sólo qué pasó."""


import pytest
from jinja2 import Template

from generador_examenes.cli_commands import diagramas_invalidos
from generador_examenes.core import logic
from generador_examenes.core.models import DefinicionExamen, Pregunta
from generador_examenes.generators import pdf_renderer


def _pregunta(id_, nombre, enunciado="Texto"):
    return Pregunta(id=id_, tipo="ensayo", nombre=nombre, categoria="c", enunciado_html=enunciado,
                    fuente_banco="banco.gift")


def test_typst_dice_que_pregunta_no_compila(monkeypatch, capsys):
    def compilar(fuente, salida, root_dir=None):
        if "MALA" in fuente:
            raise RuntimeError("Fallo en compilación Typst: unclosed delimiter")
        return salida

    monkeypatch.setattr(pdf_renderer, "compilar_typst_a_pdf", compilar)
    plantilla = Template("{% for s in secciones %}{% for p in s.preguntas %}{{ p.enunciado_html }}{% endfor %}{% endfor %}")
    contexto = {"secciones": [{"nombre": "A", "preguntas": [_pregunta("1", "buena"), _pregunta("2", "rota", "MALA")]}]}
    renderer = pdf_renderer.PdfRenderer()
    assert renderer._pregunta_que_falla(plantilla, contexto) == "«rota» de banco.gift"
    renderer._avisar_fallo_typst(RuntimeError("Fallo en compilación Typst: unclosed delimiter"), plantilla, contexto)
    assert "en la pregunta «rota» de banco.gift" in capsys.readouterr().err


def test_si_falla_sin_preguntas_no_culpa_a_ninguna(monkeypatch):
    def compilar(fuente, salida, root_dir=None):
        raise RuntimeError("Typst no está instalado")

    monkeypatch.setattr(pdf_renderer, "compilar_typst_a_pdf", compilar)
    contexto = {"secciones": [{"nombre": "A", "preguntas": [_pregunta("1", "una")]}]}
    assert pdf_renderer.PdfRenderer()._pregunta_que_falla(Template("x"), contexto) is None


def test_diagrama_invalido_con_su_pregunta():
    roto = '<p class="estructura-error"><strong>Diagrama inválido:</strong> tipo &quot;arbolito&quot; desconocido</p>'
    examen = {"secciones": [{"preguntas": [_pregunta("1", "abb", roto), _pregunta("2", "ok")]}]}
    assert diagramas_invalidos(examen) == [
        'la pregunta «abb» de banco.gift tiene un diagrama inválido: tipo "arbolito" desconocido']


def test_pool_insuficiente_dice_seccion_pool_y_que_hacer():
    definicion = DefinicionExamen(nombre_examen="E", institucion="I", materia="M", configuracion_examen={}, secciones_examen=[
        {"nombre": "Teoría", "pools": [{"categoria": "c", "cantidad": 3}]}])
    banco = {"1": _pregunta("1", "una")}
    with pytest.raises(ValueError) as error:
        logic.construir_pool_examen(definicion, banco, 1)
    mensaje = str(error.value)
    assert "en la sección «Teoría», pool 1" in mensaje and "cat:c" in mensaje
    assert "accion_si_insuficiente: usar_todas" in mensaje
