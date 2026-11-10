"""Bloques ```plantuml: opciones, dibujo y su lugar en GIFT, Markdown y el PDF."""
import re
import stat

import pytest

from generador_examenes import plantuml
from generador_examenes.core.markdown_utils import detect_and_convert_format, markdown_to_html
from generador_examenes.generators.typst_markup import html_a_typst
from generador_examenes.gift_linter import corregir_para_moodle, lint_gift_file, revisar_moodle, revisar_plantuml
from generador_examenes.parsers.gift_parser import GiftParser
from generador_examenes.plantuml import ErrorPlantuml, a_imagen, aplicar_escala, leer

SVG = ('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" height="100px" preserveAspectRatio="none" '
       'style="width:200px;height:100px;" viewBox="0 0 200 100" width="200px"><g/></svg>')


@pytest.fixture
def falso(tmp_path, monkeypatch):
    """Un `plantuml` que guarda lo que recibe: un diagrama con `ROTO` falla como el verdadero."""
    programa = tmp_path / "plantuml"
    programa.write_text(f"""#!/bin/sh
cat > "{tmp_path}/entrada"
echo x >> "{tmp_path}/llamadas"
if grep -q ROTO "{tmp_path}/entrada"; then printf 'ERROR\\n4\\nSyntax Error?\\n' >&2; exit 200; fi
printf '%s' '{SVG}'
""")
    programa.chmod(programa.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("ALUCARD_PLANTUML", str(programa))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    return tmp_path


def bloque(*renglones):
    return "```plantuml\n" + "\n".join(renglones) + "\n```"


def test_lee_las_opciones_del_principio():
    opciones, fuente = leer("// [izquierda] [ancho, 80%]\n// [letra, 12pt] [alt, Un texto: largo]\n\nA -> B\n")
    assert opciones == {"posicion": "izquierda", "ancho": "80%", "letra": "12", "alt": "Un texto: largo"}
    assert fuente == "A -> B"


def test_mas_abajo_las_barras_son_de_plantuml():
    assert leer("A -> B\n// [ancho, x]\n")[1] == "A -> B\n// [ancho, x]"


@pytest.mark.parametrize("opcion", ["[ancha, 3cm]", "[ancho, grande]", "[escala, 0]", "[letra, x]", "[tema, a b]", "[alt]"])
def test_una_opcion_invalida_es_un_error(opcion):
    with pytest.raises(ErrorPlantuml):
        leer(f"// {opcion}\nA -> B\n")


def test_un_bloque_sin_diagrama_es_un_error():
    with pytest.raises(ErrorPlantuml, match="no tiene un diagrama"):
        leer("// [centrado]\n")


def test_agrega_las_directivas_y_startuml(falso):
    a_imagen("// [letra, 12] [escala, 1.5]\nA -> B\n")
    assert (falso / "entrada").read_text() == ("@startuml\nskinparam monochrome true\nskinparam defaultFontSize 12\n"
                                               "scale 1.5\nA -> B\n@enduml\n")


def test_respeta_otro_tipo_de_diagrama(falso):
    a_imagen("@startmindmap\n* a\n@endmindmap\n")
    assert (falso / "entrada").read_text() == "@startmindmap\nskinparam monochrome true\n* a\n@endmindmap\n"


@pytest.mark.parametrize("opcion", ["[color]", "[tema, plain]"])
def test_color_y_tema_no_son_monocromos(falso, opcion):
    a_imagen(f"// {opcion}\nA -> B\n")
    assert "monochrome" not in (falso / "entrada").read_text()


def test_el_svg_no_se_deforma_al_cambiar_su_medida(falso):
    svg = a_imagen("A -> B\n").decode()
    assert svg.startswith("<svg") and "preserveAspectRatio" not in svg
    assert 'width="200"' in svg and 'height="100"' in svg


def test_dibuja_una_sola_vez_lo_mismo(falso):
    assert a_imagen("A -> B\n") == a_imagen("A -> B\n")
    assert (falso / "llamadas").read_text().count("x") == 1


def test_el_renglon_de_un_error_es_el_del_bloque(falso):
    with pytest.raises(ErrorPlantuml, match="renglón 3: Syntax Error"):
        a_imagen("ROTO\n")  # 4 de PlantUML, menos skinparam


def test_sin_plantuml_lo_dice(falso, monkeypatch):
    monkeypatch.delenv("ALUCARD_PLANTUML")
    monkeypatch.delenv("PLANTUML_JAR", raising=False)
    monkeypatch.setattr(plantuml.shutil, "which", lambda _: None)
    assert "no se encontró PlantUML" in markdown_to_html(bloque("A -> B"))


def test_markdown_y_html(falso):
    for texto in (markdown_to_html(bloque("// [alt, Clases]", "A -> B")),
                  detect_and_convert_format(bloque("// [alt, Clases]", "A -> B"), "html")):
        assert '<div class="estructura plantuml"' in texto and 'aria-label="Clases"' in texto
        assert "```" not in texto


def test_el_pdf_usa_la_posicion_y_las_medidas(falso):
    typst = html_a_typst(markdown_to_html(bloque("// [derecha] [ancho, 60%] [alto, 4cm]", "A -> B")))
    assert "align(right, image(" in typst
    assert "width: calc.min((12.0em).to-absolute(), disponible.width, disponible.width * 0.6, (4cm).to-absolute() * 2.0000)" in typst


def test_sin_opciones_crece_con_la_letra_como_una_estructura(falso):
    typst = html_a_typst(markdown_to_html(bloque("A -> B")))
    assert "align(center, image(" in typst and "12.0em" in typst


def test_gift_conserva_el_bloque_y_encuentra_las_respuestas(falso, tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text("::a::[markdown]Mirá\n" + bloque("// [color]", "class A {", "  +x: int", "}", "", "//nota//")
                     + "\n{=sí ~no}\n\n::b::Otra {T}\n", encoding="utf-8")
    primera, segunda = GiftParser().parse(banco).values()
    assert primera.tipo == "seleccion_multiple" and segunda.tipo == "verdadero_falso"
    assert "plantuml" in primera.enunciado_html


def test_lint_informa_el_diagrama_invalido(falso):
    gift = "::a::[markdown]Mirá\n" + bloque("ROTO") + "\n{}\n"
    assert revisar_plantuml(gift) == ["Línea 2 («a»): diagrama PlantUML inválido: renglón 3: Syntax Error?"]


def test_moodle_no_revisa_el_interior_del_bloque():
    gift = "::a::[markdown]Mirá\n" + bloque("A -> B : hola") + "\n{}\n"
    assert revisar_moodle(gift) == [] and corregir_para_moodle(gift) == gift


@pytest.mark.skipif(plantuml.comando() is None, reason="sin PlantUML")
def test_con_plantuml_de_verdad(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert a_imagen("class A\nA --> B : usa\n").startswith(b"<svg")
    assert a_imagen("class A\n", "png").startswith(b"\x89PNG")
    with pytest.raises(ErrorPlantuml, match="renglón 2"):
        a_imagen("class A\nfoo bar ((\n")


def test_lint_acepta_renglones_en_blanco_en_el_bloque(falso, tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text("::a::[markdown]Mirá\n" + bloque("class A {", "}", "", "class B") + "\n{=sí ~no}\n", encoding="utf-8")
    assert lint_gift_file(banco)


def test_ancho_es_un_limite_en_html(falso):
    html = markdown_to_html(bloque("// [ancho, 60%]", "A -> B"))
    assert 'style="max-width:60%;height:auto"' in html and 'width="200"' in html


def test_escala_general_cambia_los_que_no_traen_la_suya(falso):
    html = markdown_to_html(bloque("A -> B"))
    assert 'width="100"' in aplicar_escala(html, 0.5) and 'height="50"' in aplicar_escala(html, 0.5)


def test_la_escala_propia_manda_sobre_la_general(falso):
    html = markdown_to_html(bloque("// [escala, 2]", "A -> B"))
    assert aplicar_escala(html, 0.5) == html


def test_escala_general_no_toca_otros_diagramas():
    html = markdown_to_html("```estructura\ntype: array\nvalues: [1]\n```\n")
    assert aplicar_escala(html, 0.5) == html


@pytest.mark.skipif(plantuml.comando() is None, reason="sin PlantUML")
def test_una_escala_menor_da_un_dibujo_menor(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    def ancho(cuerpo):
        return float(re.search(r'width="([\d.]+)"', a_imagen(cuerpo).decode()).group(1))

    assert ancho("// [escala, 0.5]\nclass A\n") < ancho("class A\n") * 0.7

