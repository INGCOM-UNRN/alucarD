"""Estilo del examen: tipografía, encabezado y pie, logotipo y alto contraste ([estilo] de alucard.toml)."""
import base64
import re
import sys

import pytest
from pydantic import ValidationError

from generador_examenes.__main__ import main
from generador_examenes.config import proyecto
from generador_examenes.core import logic
from generador_examenes.core.estilo import (
    ErrorEstilo, combinar, contexto_estilo, contrastar_diagramas, preparar_examen,
)
from generador_examenes.core.models import (
    ConfiguracionExamen, DefinicionExamen, EstiloExamen, Franja, Opcion, PoolConfig, Pregunta, SeccionExamen,
)
from generador_examenes.diagramas import renderizar
from generador_examenes.generators import pdf_renderer
from generador_examenes.generators.html_renderer import HtmlRenderer
from generador_examenes.generators.pdf_renderer import PdfRenderer
from tests.test_proyecto import _proyecto

# PNG de 1x1 (blanco)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC")
SVG_LOGO = '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20"><rect width="40" height="20" fill="navy"/></svg>'


def _definicion(**estilo) -> DefinicionExamen:
    return DefinicionExamen(nombre_examen="Parcial 1", institucion="UNRN", materia="Programación 1",
                            fecha="2026-11-19", configuracion_examen=ConfiguracionExamen(),
                            secciones_examen=[SeccionExamen(nombre="S", pools=[PoolConfig()])],
                            estilo=EstiloExamen(**estilo))


def _examen():
    svg = renderizar({"type": "linked_list", "values": [1, 2]})
    pregunta = Pregunta(id="p", tipo="seleccion_multiple", nombre="p", categoria="a",
                        enunciado_html=f"<p>¿Qué ves?</p>{svg}<pre><code>// comentario\nint x;</code></pre>",
                        opciones=[Opcion(texto_html="sí", es_correcta=True), Opcion(texto_html="no", es_correcta=False)])
    return {"secciones": [{"nombre": "S", "instrucciones": None, "preguntas": [pregunta]}]}


# --- Modelo -----------------------------------------------------------------------------------

def test_franja_con_texto_solo_va_al_centro_y_valida_marcadores():
    assert Franja.model_validate("{examen}") == Franja(centro="{examen}")
    with pytest.raises(ValidationError, match=r"marcador desconocido \{curso\}"):
        Franja(izquierda="{curso}")
    assert EstiloExamen(fuente="Fira Sans").fuente == ["Fira Sans"]
    with pytest.raises(ValidationError):
        EstiloExamen(logo_posicion="arriba")


def test_sin_estilo_el_encabezado_y_el_pie_de_siempre():
    ctx = contexto_estilo(_definicion(), 0)["estilo"]
    assert "UNRN — Programación 1 | Tema 1" in ctx["encabezado_typst"]
    assert "Parcial 1" in ctx["pie_typst"] and "#counter(page).final().first()" in ctx["pie_typst"]
    assert ctx["encabezado_html"] == ctx["pie_html"] == ""  # en HTML no se agregan franjas
    assert "CLAVE DOCENTE" in contexto_estilo(_definicion(), 1, clave=True)["estilo"]["encabezado_typst"]


def test_franjas_con_marcadores():
    definicion = _definicion(encabezado={"izquierda": "{institucion}", "derecha": "{materia} — Tema {tema}"},
                             pie={"izquierda": "{examen} ({fecha})", "derecha": "Página {pagina} de {paginas}"})
    ctx = contexto_estilo(definicion, 2)["estilo"]
    assert "UNRN" in ctx["encabezado_typst"] and "Programación 1 — Tema 3" in ctx["encabezado_typst"]
    assert "#counter(page).display() de #counter(page).final().first()" in ctx["pie_typst"]
    assert ">UNRN<" in ctx["encabezado_html"]
    assert "Parcial 1 (2026-11-19)" in ctx["pie_html"] and "Página" not in ctx["pie_html"]  # sin páginas en HTML


def test_contraste_quita_los_grises():
    normal, contraste = contexto_estilo(_definicion(), 0)["c"], contexto_estilo(_definicion(alto_contraste=True), 0)["c"]
    assert normal["sub"] != "000000"
    assert {v for k, v in contraste.items() if k != "fondo_inst"} == {"000000"}
    svg = renderizar({"type": "array", "values": [1, 2], "showAddresses": True})
    assert re.search(r"#(334155|475569)", svg)
    assert not re.search(r"#(334155|475569|64748b)", contrastar_diagramas(svg))


# --- Configuración: alucard.toml y definición ---------------------------------------------------

def test_combinar_curso_y_definicion(tmp_path):
    (tmp_path / "logo.png").write_bytes(PNG)
    curso = {"fuente": ["Liberation Serif"], "tamano": 11, "alto_contraste": True}
    estilo = combinar(curso, {"tamano": 12, "logo": "logo.png"}, tmp_path)
    assert estilo.fuente == ["Liberation Serif"] and estilo.tamano == 12 and estilo.alto_contraste
    assert estilo.logo == str(tmp_path / "logo.png")
    with pytest.raises(ErrorEstilo, match="no se encontró el logotipo"):
        combinar({}, {"logo": "falta.png"}, tmp_path)
    (tmp_path / "logo.bmp").write_bytes(b"BM")
    with pytest.raises(ErrorEstilo, match="formato no soportado"):
        combinar({}, {"logo": "logo.bmp"}, tmp_path)


def test_toml_con_estilo(tmp_path):
    _proyecto(tmp_path, '[estilo]\nlogo = "img/logo.png"\nencabezado = "{examen}"\n')
    conf = proyecto.cargar(tmp_path / "examenes")
    assert conf.estilo["logo"] == str(tmp_path / "img" / "logo.png")  # relativo al toml
    assert conf.estilo["encabezado"] == "{examen}"
    (tmp_path / "alucard.toml").write_text('[estilo]\ntamano = 40\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"alucard.toml: \[estilo\]"):
        proyecto.cargar(tmp_path)


def test_generar_con_estilo_del_toml_y_de_la_definicion(tmp_path, monkeypatch):
    (tmp_path / "logo.png").write_bytes(PNG)
    definicion = _proyecto(
        tmp_path,
        'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n'
        '[estilo]\nlogo = "logo.png"\nencabezado = { derecha = "{materia}" }\nalto_contraste = true\n',
        'estilo:\n  fuente: "Liberation Serif"\n  logo_posicion: derecha\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion)])
    assert main() == 0
    html = next((tmp_path / "salida").glob("examen_*.html")).read_text(encoding="utf-8")
    assert "font-family: 'Liberation Serif', sans-serif" in html
    assert re.search(r'<div class="franja-der">Programación</div><img class="franja-logo" src="data:image/png;base64,', html)
    assert "body, body * { color: #000 !important; }" in html


def test_generar_con_logo_inexistente_falla_antes(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
                           'estilo:\n  logo: "no-esta.png"\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion)])
    assert main() == 1
    assert "no se encontró el logotipo" in capsys.readouterr().err
    assert not (tmp_path / "salida").exists()


# --- Salida ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("logo, formato", [("logo.png", "png"), ("logo.svg", "svg")])
def test_pdf_con_estilo_completo(tmp_path, monkeypatch, logo, formato):
    (tmp_path / "logo.png").write_bytes(PNG)
    (tmp_path / "logo.svg").write_text(SVG_LOGO, encoding="utf-8")
    fuentes = []
    compilar = pdf_renderer.compilar_typst_a_pdf

    def capturar(fuente, salida, root_dir=None):
        fuentes.append(fuente)
        return compilar(fuente, salida, root_dir=root_dir)

    def sin_respaldo(*_a, **_k):
        raise AssertionError("Typst falló y se usó WeasyPrint")

    monkeypatch.setattr(pdf_renderer, "compilar_typst_a_pdf", capturar)
    monkeypatch.setattr(PdfRenderer, "_renderizar_examen_weasyprint", sin_respaldo)
    monkeypatch.setattr(PdfRenderer, "_renderizar_clave_weasyprint", sin_respaldo)
    definicion = _definicion(fuente=["Liberation Serif"], fuente_codigo="DejaVu Sans Mono", tamano=11,
                             encabezado={"izquierda": "{institucion}"}, pie="Página {pagina}",
                             logo=str(tmp_path / logo), logo_posicion="derecha", logo_alto_mm=20,
                             alto_contraste=True)
    renderer = PdfRenderer()
    assert renderer.renderizar_examen(_examen(), definicion, tmp_path, 0).stat().st_size > 0
    assert renderer.renderizar_clave(_examen(), definicion, tmp_path, 0).stat().st_size > 0
    examen = fuentes[0]
    assert 'font: ("Liberation Serif",), size: 11pt' in examen
    assert '#show raw: set text(font: ("DejaVu Sans Mono",))' in examen
    assert f'format: "{formato}", height: 20mm' in examen and "align(right + horizon, logo)" in examen
    assert "margin: (top: 32.0mm" in examen  # el margen crece con el logotipo
    assert "#set raw(theme: none)" in examen
    grises = re.findall(r'rgb\("([0-9a-f]{6})"\)', examen)
    assert set(grises) <= {"000000", "ffffff"}  # sin grises en el examen
    assert not re.search(r"#(334155|475569|64748b)", examen)  # ni en los diagramas


def test_html_con_contraste_y_diagramas_en_negro(tmp_path):
    definicion = _definicion(alto_contraste=True, tamano=12)
    html = HtmlRenderer().renderizar_examen(_examen(), definicion, tmp_path, 0).read_text(encoding="utf-8")
    assert "font-size: 12pt" in html and "body, body * { color: #000 !important; }" in html
    assert not re.search(r"#(334155|475569|64748b)", html)
    # el examen original no cambia
    assert re.search(r"#(334155|475569)", _examen()["secciones"][0]["preguntas"][0].enunciado_html)
    assert preparar_examen(_examen(), _definicion())["secciones"][0]["preguntas"][0].enunciado_html == \
        _examen()["secciones"][0]["preguntas"][0].enunciado_html
