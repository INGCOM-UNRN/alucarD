"""Bloques ```tabla: su lectura y su presentación en el PDF."""
import pytest

from generador_examenes.core.markdown_utils import detect_and_convert_format, markdown_to_html
from generador_examenes.generators.typst_markup import html_a_typst
from generador_examenes.gift_linter import revisar_moodle, revisar_tablas
from generador_examenes.parsers.gift_parser import GiftParser

TABLA = "| Paso | Valor |\n|---|---|\n| `[M1]` |  |"


def bloque(*opciones, tabla=TABLA):
    return "```tabla\n" + "".join(f"// {o}\n" for o in opciones) + tabla + "\n```"


def typst(*opciones):
    return html_a_typst(markdown_to_html(bloque(*opciones)))


def test_sin_opciones_es_una_tabla_comun():
    resultado = markdown_to_html(f"Antes\n{bloque()}\nDespués")
    assert "<table>" in resultado and "```" not in resultado and "//" not in resultado
    assert resultado.index("Antes") < resultado.index("<table>") < resultado.index("Después")


def test_tambien_en_preguntas_sin_markdown():
    assert "<table" in detect_and_convert_format(bloque("[centrado]"), "plain")


def test_las_opciones_viajan_al_pdf_y_no_se_imprimen():
    resultado = markdown_to_html(bloque("[centrado] [ancho, 80%]", "un comentario común", "[cebra]"))
    assert "data-opciones" in resultado and "comentario" not in resultado


@pytest.mark.parametrize("opcion, esperado", [
    ("[centrado]", "#align(center)["),
    ("[derecha]", "#align(right)["),
    ("[ancho, 80%]", "#block(width: 80%)["),
    ("[letra, 0.8em]", "#text(size: 0.8em)["),
    ("[relleno, 8pt]", "inset: 8pt"),
    ("[alto, 3em]", "#box(height: 3em)"),
    ("[columnas, auto, 2fr]", "columns: (auto, 2fr,)"),
    ("[columnas:30%,12mm]", "columns: (30%, 12mm,)"),
    ("[alinear, derecha, centro]", "align: (right, center,)"),
    ("[bordes, ninguno]", "stroke: none"),
    ("[bordes, horizontales]", "stroke: (x: none, y: 0.5pt)"),
    ("[cebra]", "calc.even(y)"),
    ("[sombrear-encabezado]", "y == 0"),
])
def test_cada_opcion_llega_al_typst(opcion, esperado):
    assert esperado in typst(opcion)


def test_sin_encabezado_se_saltea_la_primera_fila():
    tabla = typst("[sin-encabezado]").split("#table(")[1]
    assert "Paso" not in tabla and "M1" in tabla


def test_con_ancho_las_columnas_lo_reparten():
    tabla = "| a | b |\n|---|---|\n| c | d |"
    assert "columns: (1fr, 1fr,)" in html_a_typst(markdown_to_html(bloque("[ancho:50%]", tabla=tabla)))


def test_una_tabla_ubicada_no_centra_sus_celdas():
    assert "align: left" in typst("[centrado]")


@pytest.mark.parametrize("opciones, motivo", [
    (["[rara]"], "opción desconocida"),
    (["[ancho:mucho]"], "medida"),
    (["[bordes:dobles]"], "bordes"),
    (["[columnas:1fr]"], "2 columnas"),
    (["[columnas:ancha,1fr]"], "fracción"),
    (["[alinear:centro]"], "2 columnas"),
    (["[alinear:arriba,centro]"], "se alinea"),
])
def test_una_opcion_invalida_se_avisa(opciones, motivo):
    texto = bloque(*opciones)
    assert "tabla-error" in markdown_to_html(texto)
    (problema,) = revisar_tablas(f"::a::[markdown]Mirá\n{texto}\n{{}}\n")
    assert "Línea 2 («a»): tabla inválida" in problema and motivo in problema


def test_un_bloque_sin_tabla_se_avisa():
    assert "no hay una tabla" in revisar_tablas("```tabla\nsolo texto\n```")[0]


def test_una_tabla_valida_no_tiene_problemas():
    contenido = f"::a::[markdown]Mirá\n{bloque('[centrado] [ancho, 80%]')}\n{{}}\n"
    assert revisar_tablas(contenido) == [] and revisar_moodle(contenido) == []


def test_el_parser_de_gift_conserva_las_opciones(tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text(f"// [tag:x]\n::a::[markdown]Completá\n{bloque('[centrado]')}\n{{}}\n\n::b::Otra {{T}}\n",
                     encoding="utf-8")
    primera, segunda = GiftParser().parse(banco).values()
    assert primera.etiquetas == ["x"] and primera.tipo == "desarrollo"
    assert "data-opciones" in primera.enunciado_html and "//" not in primera.enunciado_html
    assert segunda.nombre == "b"


def test_en_gift_una_tabla_admite_los_escapes(tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text("::a::[markdown]Mirá\n```tabla\n| a |\n|---|\n| x\\: y |\n```\n{}\n", encoding="utf-8")
    assert "x: y" in list(GiftParser().parse(banco).values())[0].enunciado_html


def test_para_moodle_es_html_en_un_renglon_con_sus_bordes():
    from generador_examenes.tablas import tabla_a_moodle

    resultado = tabla_a_moodle(f"// [centrado]\n{TABLA}\n", markdown_to_html)
    assert "\n" not in resultado and "data-opciones" not in resultado
    assert resultado.startswith('<table style="border-collapse:collapse">') and "border:1px solid" in resultado
    assert ">&nbsp;</td>" in resultado and "<code>[M1]</code>" in resultado


def test_las_opciones_admiten_los_dos_separadores():
    assert "columns: (auto, 2fr,)" in typst("[columnas:auto,2fr]")
