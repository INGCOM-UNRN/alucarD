"""Por dónde se parte una pregunta en el PDF, y las preguntas de desarrollo en su propia hoja."""

import pytest
from pydantic import ValidationError
from pypdf import PdfReader
from typer.testing import CliRunner

from generador_examenes.__main__ import app
from generador_examenes.config import proyecto
from generador_examenes.core.logic import construir_pool_examen
from generador_examenes.core.markdown_utils import markdown_to_html
from generador_examenes.core.consignas import presentar_consigna
from generador_examenes.core.models import DefinicionExamen, PresentacionConsigna, Pregunta
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


def desarrollo(etiqueta=""):
    comentario = f"// [tag, {etiqueta}]\n" if etiqueta else ""
    return f"{comentario}::a::Explicá.\n{{}}\n"


@pytest.mark.parametrize("etiqueta, tamano", [
    ("", None), ("desarrollo-cero", "cero"), ("desarrollo-chico", "chico"), ("desarrollo-pequeno", "chico"),
    ("desarrollo-mediano", "mediano"), ("desarrollo-grande", "grande"), ("desarrollo-pagina", "pagina"),
    ("desarrollo-página", "pagina"),
])
def test_la_pregunta_pide_su_espacio_con_una_etiqueta(tmp_path, etiqueta, tamano):
    (p,) = pregunta(tmp_path, desarrollo(etiqueta))
    assert p.tamano_desarrollo == tamano and p.etiquetas == []


def definicion_con(**configuracion):
    return DefinicionExamen(nombre_examen="x", institucion="x", materia="x", configuracion_examen=configuracion,
                            secciones_examen=[{"nombre": "s", "pools": [{"tipos": ["desarrollo"]}]}])


def espacios(tmp_path, gift, **configuracion):
    banco = tmp_path / "banco.gift"
    banco.write_text(gift, encoding="utf-8")
    examen = construir_pool_examen(definicion_con(**configuracion), GiftParser().parse(banco))
    return sorted(p.tamano_desarrollo for p in examen["secciones"][0]["preguntas"])


DOS_PREGUNTAS = "::a::Sin etiqueta\n{}\n\n// [tag, desarrollo-cero]\n::b::Con etiqueta\n{}\n"


def test_sin_nada_el_espacio_es_mediano(tmp_path):
    assert espacios(tmp_path, DOS_PREGUNTAS) == ["cero", "mediano"]


def test_la_opcion_general_vale_para_las_que_no_piden_otro(tmp_path):
    assert espacios(tmp_path, DOS_PREGUNTAS, espacio_desarrollo="grande") == ["cero", "grande"]


def test_forzar_el_espacio_pisa_las_etiquetas(tmp_path):
    gift = "// [tag, desarrollo-grande]\n::a::Uno\n{}\n\n::b::Dos\n{}\n"
    assert espacios(tmp_path, gift, espacio_desarrollo="cero", forzar_espacio_desarrollo=True) == ["cero", "cero"]


def test_sin_forzar_la_etiqueta_sigue_mandando(tmp_path):
    gift = "// [tag, desarrollo-grande]\n::a::Uno\n{}\n\n::b::Dos\n{}\n"
    assert espacios(tmp_path, gift, espacio_desarrollo="cero", forzar_espacio_desarrollo=False) == ["cero", "grande"]


def test_la_hoja_separada_manda_sobre_el_espacio_forzado(tmp_path):
    assert espacios(tmp_path, DOS_PREGUNTAS, espacio_desarrollo="cero", forzar_espacio_desarrollo=True,
                    desarrollo_en_hoja_separada=True) == ["pagina", "pagina"]


def test_la_hoja_separada_manda_sobre_las_preguntas(tmp_path):
    assert espacios(tmp_path, DOS_PREGUNTAS, desarrollo_en_hoja_separada=True) == ["pagina", "pagina"]


def test_el_nombre_anterior_vale_en_la_opcion_general():
    assert definicion_con(espacio_desarrollo="pequeno").configuracion_examen.espacio_desarrollo == "chico"


def test_un_espacio_desconocido_es_un_error():
    with pytest.raises(ValidationError):
        definicion_con(espacio_desarrollo="enorme")


def alturas(tmp_path, tamano, formato="pdf"):
    """Lo que ocupa una pregunta de ese tamaño, en el documento generado."""
    (tmp_path / "e.yaml").write_text(
        "nombre_examen: x\ninstitucion: x\nmateria: x\nconfiguracion_examen:\n  generar_clave_profesor: false\n"
        f"  espacio_desarrollo: {tamano}\nsecciones_examen:\n  - nombre: s\n    pools:\n      - tipos: [desarrollo]\n",
        encoding="utf-8")
    (tmp_path / "b.gift").write_text("::uno::Primera\n{}\n\n::dos::Segunda\n{}\n", encoding="utf-8")
    resultado = CliRunner().invoke(app, ["generar", "-d", str(tmp_path / "e.yaml"), "-i", str(tmp_path / "b.gift"),
                                         "-o", str(tmp_path / "out"), "-f", formato])
    assert resultado.exit_code == 0, resultado.output
    return tmp_path / "out" / f"examen_tema_01.{formato}"


@pytest.mark.parametrize("tamano, recuadros", [("cero", 0), ("chico", 2), ("grande", 2)])
def test_el_pdf_dibuja_el_recuadro_del_tamano(tmp_path, tamano, recuadros):
    texto = "".join(p.extract_text() for p in PdfReader(alturas(tmp_path, tamano)).pages)
    assert texto.count("Espacio para desarrollo") == recuadros


def test_pagina_pone_cada_pregunta_en_su_hoja(tmp_path):
    paginas = [p.extract_text() for p in PdfReader(alturas(tmp_path, "pagina")).pages]
    assert len(paginas) == 2 and "Espacio para desarrollo" in paginas[0] and "Espacio para desarrollo" in paginas[1]


def test_el_html_usa_el_tamano(tmp_path):
    assert 'desarrollo-box grande' in alturas(tmp_path, "grande", "html").read_text(encoding="utf-8")


def test_el_html_sin_espacio_no_dibuja_el_recuadro(tmp_path):
    assert '<div class="desarrollo-box' not in alturas(tmp_path, "cero", "html").read_text(encoding="utf-8")


def generar_con_toml(tmp_path, toml, yaml_extra=""):
    """Un examen en un proyecto con `alucard.toml`; devuelve el resultado y la carpeta de salida."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "alucard.toml").write_text(toml, encoding="utf-8")
    (tmp_path / "e.yaml").write_text(
        f"nombre_examen: x\ninstitucion: x\nmateria: x\nconfiguracion_examen:\n  generar_clave_profesor: true\n{yaml_extra}"
        "secciones_examen:\n  - nombre: s\n    pools:\n      - tipos: [desarrollo]\n", encoding="utf-8")
    (tmp_path / "b.gift").write_text("::la-primera::Explicá\n{=a}\n\n::la-segunda::Otra\n{}\n", encoding="utf-8")
    salida = tmp_path / "out"
    return CliRunner().invoke(app, ["generar", "-d", str(tmp_path / "e.yaml"), "-i", str(tmp_path / "b.gift"),
                                    "-o", str(salida), "-f", "pdf"]), salida


def texto_pdf(archivo):
    return "".join(p.extract_text() for p in PdfReader(archivo).pages)


def test_debug_consignas_muestra_el_titulo(tmp_path):
    resultado, salida = generar_con_toml(tmp_path, 'debug_consignas = "titulo"\n')
    assert resultado.exit_code == 0, resultado.output
    assert "[la-segunda]" in texto_pdf(salida / "examen_tema_01.pdf")


def test_debug_consignas_muestra_el_id_y_tambien_en_la_clave(tmp_path):
    resultado, salida = generar_con_toml(tmp_path, 'debug_consignas = "id"\n')
    assert resultado.exit_code == 0, resultado.output
    assert "gift_" in texto_pdf(salida / "examen_tema_01.pdf") and "gift_" in texto_pdf(salida / "clave_tema_01.pdf")


def test_sin_debug_consignas_no_se_ve_de_donde_salio(tmp_path):
    _, salida = generar_con_toml(tmp_path, "")
    assert "la-segunda" not in texto_pdf(salida / "examen_tema_01.pdf")
    assert "Debug" not in texto_pdf(salida / "examen_tema_01.pdf")


@pytest.mark.parametrize("archivo", ["examen_tema_01.pdf", "clave_tema_01.pdf"])
def test_debug_consignas_pone_la_marca_de_agua_en_cada_pagina(tmp_path, archivo):
    _, salida = generar_con_toml(tmp_path, 'debug_consignas = "id"\n', "  espacio_desarrollo: pagina\n")
    paginas = PdfReader(salida / archivo).pages
    assert all("Debug" in p.extract_text() for p in paginas)


def test_debug_consignas_en_html_no_deja_fondos_que_tapen_la_marca(tmp_path):
    (tmp_path / "e.yaml").write_text(
        "nombre_examen: x\ninstitucion: x\nmateria: x\nconfiguracion_examen:\n  debug_consignas: titulo\n"
        "secciones_examen:\n  - nombre: s\n    pools:\n      - tipos: [desarrollo]\n", encoding="utf-8")
    (tmp_path / "b.gift").write_text("::uno::Primera\n{}\n", encoding="utf-8")
    CliRunner().invoke(app, ["generar", "-d", str(tmp_path / "e.yaml"), "-i", str(tmp_path / "b.gift"),
                             "-o", str(tmp_path / "out"), "-f", "html"])
    texto = (tmp_path / "out" / "examen_tema_01.html").read_text(encoding="utf-8")
    assert 'class="marca-debug"' in texto and "background-color: transparent !important" in texto


def test_la_definicion_manda_sobre_el_toml(tmp_path):
    _, salida = generar_con_toml(tmp_path, 'debug_consignas = "titulo"\n', "  debug_consignas: id\n")
    texto = texto_pdf(salida / "examen_tema_01.pdf")
    assert "gift_" in texto and "[la-segunda]" not in texto


def test_debug_consignas_invalido_lo_dice_con_el_archivo(tmp_path):
    (tmp_path / "alucard.toml").write_text('debug_consignas = "nombre"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="alucard.toml.*debug_consignas"):
        proyecto.cargar(tmp_path)


def renglones_del_pdf(archivo):
    """Cuántos trazos punteados tiene el PDF: un renglón es uno, y cada recuadro suma los suyos."""
    return sum(p.get_contents().get_data().count(b" d\n") for p in PdfReader(archivo).pages)


def test_el_pdf_tiene_mas_renglones_cuanto_mas_espacio(tmp_path):
    cantidades = []
    for tamano in ("cero", "chico", "grande", "pagina"):
        carpeta = tmp_path / tamano
        carpeta.mkdir()
        cantidades.append(renglones_del_pdf(alturas(carpeta, tamano)))
    assert cantidades == sorted(set(cantidades)) and cantidades[1] > cantidades[0]


@pytest.mark.parametrize("tamano, renglones", [("cero", 0), ("chico", 6), ("mediano", 14), ("grande", 30), ("pagina", 60)])
def test_el_html_tiene_renglones(tmp_path, tamano, renglones):
    assert alturas(tmp_path, tamano, "html").read_text(encoding="utf-8").count('<div class="renglon"></div>') == renglones


@pytest.mark.parametrize("presentacion, renglones", [
    ({"lineas": 0}, 0), ({"lineas": 0, "espacio_respuesta": True}, 0), ({"lineas": 5, "espacio_respuesta": False}, 0),
    ({"lineas": 5}, 5),
])
def test_los_renglones_de_una_consigna(presentacion, renglones):
    consigna = Pregunta(id="deckard:x", tipo="consigna_practica", nombre="x", categoria="c", enunciado_html="",
                        metadata={"enunciado_md": "Hacé algo."})
    assert presentar_consigna(consigna, PresentacionConsigna(**presentacion)).lineas_respuesta == renglones


def test_un_comentario_que_nombra_la_marca_no_cambia_los_ids(tmp_path):
    """Los ids entran en el sorteo: si un comentario los corriera, saldrían otras preguntas."""
    gift = "::a::Uno\n// [corte]\nDos\n{}\n"
    (sin,) = pregunta(tmp_path, gift)
    (con,) = pregunta(tmp_path, "// Las secciones llevan // [corte] antes.\n\n" + gift)
    assert con.id == sin.id and "<!--corte-->" in con.enunciado_html
