"""Por dónde se parte una pregunta en el PDF, y las preguntas de desarrollo en su propia hoja."""

import pytest
from pypdf import PdfReader
from typer.testing import CliRunner

from generador_examenes.__main__ import app
from generador_examenes.core.markdown_utils import markdown_to_html
from generador_examenes.generators.typst_markup import html_a_typst, partes_typst
from generador_examenes.parsers.gift_parser import GiftParser


def pregunta(tmp_path, contenido):
    banco = tmp_path / "banco.gift"
    banco.write_text(contenido, encoding="utf-8")
    return list(GiftParser().parse(banco).values())


def test_la_marca_corte_llega_al_enunciado_sin_verse(tmp_path):
    (p,) = pregunta(tmp_path, "::a::[markdown]Uno\n// [corte]\nDos\n{}\n")
    assert "<!--corte-->" in p.enunciado_html and "[corte]" not in p.enunciado_html
    assert "corte" not in html_a_typst(p.enunciado_html)


def test_una_marca_separada_por_un_renglon_no_corta_la_pregunta(tmp_path):
    (p,) = pregunta(tmp_path, "::a::[markdown]Uno\n\n// [corte]\nDos\n{}\n")
    assert "Dos" in p.enunciado_html and p.tipo == "desarrollo"


@pytest.mark.parametrize("contenido", ["// [corte]\n::a::Uno {T}\n", "::a::Uno {T}\n// [corte]\n",
                                       "::a::Uno {\n=x\n// [corte]\n~y\n}\n"])
def test_una_marca_fuera_del_enunciado_no_hace_nada(tmp_path, contenido):
    (p,) = pregunta(tmp_path, contenido)
    assert "corte" not in p.enunciado_html and "corte" not in "".join(o.texto_html for o in p.opciones)


def test_los_comentarios_comunes_no_son_marcas(tmp_path):
    (p,) = pregunta(tmp_path, "::a::Uno\n// corte aca\nDos {T}\n")
    assert "corte" not in p.enunciado_html


def test_el_enunciado_se_parte_por_marcas_y_encabezados():
    html = markdown_to_html("Uno\n\n<!--corte-->\n\nDos\n\n#### Tres\n\nCuatro")
    partes = partes_typst(html)
    assert [p["marca"] for p in partes] == [False, True, False]
    assert "Uno" in partes[0]["typst"] and "Dos" in partes[1]["typst"] and "Tres" in partes[2]["typst"]


def test_un_encabezado_al_principio_no_deja_una_parte_vacia():
    partes = partes_typst("<h4>Título</h4><p>Texto</p>")
    assert len(partes) == 1 and "Título" in partes[0]["typst"]


def test_sin_cortes_es_una_sola_parte():
    assert len(partes_typst("<p>Texto</p>")) == 1 and partes_typst("")[0]["typst"] == ""


def test_una_marca_en_el_codigo_no_parte_el_enunciado():
    assert len(partes_typst(markdown_to_html("```c\nint x;\n```"))) == 1


def test_los_dos_puntos_escapados_del_codigo_se_ven_normales(tmp_path):
    (p,) = pregunta(tmp_path, "::a::[markdown]Mirá\n```c\nprintf(\"a\\: b\");\n```\n{T}\n")
    assert "\\:" not in p.enunciado_html and "a: b" in p.enunciado_html.replace("</span>", "").replace('<span class="s">', "")


def _pdf(tmp_path, banco, *opciones):
    archivo = tmp_path / "banco.gift"
    archivo.write_text(banco, encoding="utf-8")
    salida = tmp_path / "salida"
    r = CliRunner().invoke(app, ["ver", str(archivo), "-f", "pdf", "-o", str(salida), *opciones])
    assert r.exit_code == 0, r.output
    return [p.extract_text() for p in PdfReader(salida / "examen_tema_01.pdf").pages]


LARGO = "\n".join(f"Renglón {i} del enunciado." for i in range(40))


def test_una_pregunta_larga_se_corta_por_sus_encabezados_sin_encimarse(tmp_path):
    texto = f"::a::[markdown]Inicio\n#### Primera\n{LARGO}\n#### Segunda\n{LARGO}\n#### Tercera\n{LARGO}\n{{}}\n"
    paginas = _pdf(tmp_path, texto)
    assert len(paginas) >= 3
    assert sum("Segunda" in p for p in paginas) == 1
    assert not any("Primera" in p and "Tercera" in p for p in paginas)


def test_una_pregunta_que_entra_no_se_parte_por_sus_encabezados(tmp_path):
    relleno = "\n\n".join(f"::r{i}::Relleno {i} {{T}}" for i in range(14))
    paginas = _pdf(tmp_path, f"{relleno}\n\n::a::[markdown]Inicio\n#### Título\n{LARGO}\n{{}}\n")
    assert any("Inicio" in p and "Título" in p for p in paginas)


def test_una_parte_mas_alta_que_la_pagina_tampoco_se_encima(tmp_path):
    codigo = "\n".join(f"int x{i};" for i in range(120))
    paginas = _pdf(tmp_path, f"::a::[markdown]Mirá\n```c\n{codigo}\n```\n{{}}\n")
    assert len(paginas) >= 2 and "x119" in paginas[-1]


DEFINICION = """
nombre_examen: Prueba
institucion: UNRN
materia: P1
input_banco: [banco.gift]
numero_temas: 1
semilla: 1
formato: [pdf]
output_dir: salida
configuracion_examen:
  desarrollo_en_hoja_separada: {hoja}
  generar_clave_profesor: false
  mezclar_preguntas_dentro_seccion: false
secciones_examen:
  - nombre: Parte A
    pools:
      - {{cantidad: 1, puntos_por_pregunta: 1, tipos: [verdadero_falso]}}
  - nombre: Parte B
    pools:
      - {{cantidad: 2, puntos_por_pregunta: 5, tipos: [desarrollo]}}
"""


@pytest.mark.parametrize("hoja, esperadas", [("false", 1), ("true", 3)])
def test_cada_desarrollo_va_en_su_hoja_si_se_pide(tmp_path, monkeypatch, hoja, esperadas):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "banco.gift").write_text("::v::Verdad {T}\n\n::d1::Explicá uno {}\n\n::d2::Explicá dos {}\n",
                                         encoding="utf-8")
    (tmp_path / "e.yaml").write_text(DEFINICION.format(hoja=hoja), encoding="utf-8")
    r = CliRunner().invoke(app, ["generar", "-d", "e.yaml"])
    assert r.exit_code == 0, r.output
    paginas = [p.extract_text() for p in PdfReader(tmp_path / "salida" / "examen_tema_01.pdf").pages]
    assert len(paginas) == esperadas
    if hoja == "true":
        assert "Parte A" in paginas[0] and "Parte B" not in paginas[0]
        assert not any("uno" in p and "dos" in p for p in paginas)


def test_un_comentario_que_nombra_la_marca_no_cambia_los_ids(tmp_path):
    """Los ids entran en el sorteo: si un comentario los corriera, saldrían otras preguntas."""
    gift = "::a::Uno\n// [corte]\nDos\n{}\n"
    (sin,) = pregunta(tmp_path, gift)
    (con,) = pregunta(tmp_path, "// Las secciones llevan // [corte] antes.\n\n" + gift)
    assert con.id == sin.id and "<!--corte-->" in con.enunciado_html
