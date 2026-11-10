"""Bancos GIFT que Moodle importa tal cual, y bancos repartidos en carpetas."""
import logging

import pytest

from generador_examenes.__main__ import app
from generador_examenes.core.logic import candidatas_pool, cargar_bancos
from generador_examenes.core.models import PoolConfig
from generador_examenes.gift_linter import (
    corregir_para_moodle,
    dos_puntos_sueltos,
    lint_gift_file,
    revisar_archivos,
    revisar_moodle,
)
from generador_examenes.parsers.gift_parser import GiftParser


def preguntas(tmp_path, contenido):
    banco = tmp_path / "banco.gift"
    banco.write_text(contenido, encoding="utf-8")
    return list(GiftParser().parse(banco).values())


@pytest.mark.parametrize("contenido", [
    "// [tag, punteros, bloom:2]\n::a::Texto {T}\n",
    "// [tag, punteros] [tag, bloom:2]\n::a::Texto {T}\n",
    "// [tag:punteros] [tag:bloom:2]\n::a::Texto {T}\n",
    "::a::Texto {T}\n// [tag:punteros] [tag:bloom:2]\n",
    "::a::Texto\n// [tag:punteros]\n// [tag:bloom:2]\n{T}\n",
])
def test_las_etiquetas_van_en_un_comentario_del_parrafo_de_la_pregunta(tmp_path, contenido):
    assert preguntas(tmp_path, contenido)[0].etiquetas == ["punteros", "bloom:2"]


def test_cada_comentario_etiqueta_a_su_pregunta(tmp_path):
    primera, segunda = preguntas(tmp_path, "// [tag:x]\n::a::Uno {T}\n\n// [tag:y]\n::b::Dos {F}\n")
    assert (primera.nombre, primera.etiquetas) == ("a", ["x"])
    assert (segunda.nombre, segunda.etiquetas) == ("b", ["y"])


def test_un_comentario_en_otro_parrafo_no_etiqueta_como_en_moodle(tmp_path):
    (pregunta,) = preguntas(tmp_path, "// [tag:suelta]\n\n::a::Texto {T}\n")
    assert pregunta.etiquetas == []


def test_los_comentarios_comunes_siguen_ignorandose(tmp_path):
    (pregunta,) = preguntas(tmp_path, "// [id:q1] nota\n::a::Texto {T}\n")
    assert pregunta.etiquetas == [] and "nota" not in pregunta.enunciado_html


def test_la_categoria_de_una_pregunta_va_en_el_comentario(tmp_path):
    (pregunta,) = preguntas(tmp_path, "$CATEGORY: General\n\n// [category, Tipos/Structs]\n::a::Texto {T}\n")
    assert pregunta.categoria == "Tipos/Structs"


@pytest.mark.parametrize("comentario, tamano", [
    ("", None),
    ("// [tag, desarrollo-pequeno]\n", "chico"),
    ("// [tag, tema, desarrollo-grande]\n", "grande"),
])
def test_el_desarrollo_es_el_ensayo_de_moodle_y_su_tamano_una_etiqueta(tmp_path, comentario, tamano):
    (pregunta,) = preguntas(tmp_path, f"{comentario}::a::Explicá {{}}\n")
    assert (pregunta.tipo, pregunta.tamano_desarrollo) == ("desarrollo", tamano)
    assert not any(e.startswith("desarrollo-") for e in pregunta.etiquetas)


def test_la_sintaxis_vieja_se_sigue_leyendo_con_un_aviso(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        (pregunta,) = preguntas(tmp_path, "::a::Explicá {desarrollo:grande} [tags: x, y] [category: C]\n")
    assert (pregunta.tamano_desarrollo, pregunta.etiquetas, pregunta.categoria) == ("grande", ["x", "y"], "C")
    assert "lint-gift --fix" in caplog.text


def test_los_dos_puntos_anchos_se_ven_normales_tambien_sin_markdown(tmp_path):
    (pregunta,) = preguntas(tmp_path, "::a::Elegí uno：{=d：：n ~b}\n")
    assert "：" not in pregunta.enunciado_html + pregunta.opciones[0].texto_html
    assert pregunta.opciones[0].texto_html == "d::n"


def test_marca_los_dos_puntos_de_toda_la_pregunta():
    contenido = "::a:b::Elegí: {=c:d #retro: e ~f}\n"
    assert [contenido[p - 1:p + 2] for p in dos_puntos_sueltos(contenido)] == ["a:b", "í: ", "c:d", "o: "]


@pytest.mark.parametrize("contenido", [
    "// comentario: libre\n::a::Texto {T}\n",
    "$CATEGORY: tipos/structs\n\n::a::Texto {T}\n",
    "::a::Texto\\: con escape {T}\n",
    "::a::¿Cuánto? {#3:2}\n",
    "::a::Mirá\n```estructura\ntype: stack\nvalues: [1]\n```\n{T}\n",
    "::a::Sea $f: A \\to B$ {T}\n",
])
def test_lo_que_puede_llevar_dos_puntos(contenido):
    assert dos_puntos_sueltos(contenido) == []


def test_el_codigo_no_esta_exento_de_los_dos_puntos():
    assert len(dos_puntos_sueltos("::a::Mirá\n```c\ncase 1:\n```\n{T}\n")) == 1


def test_avisa_lo_que_moodle_no_importa():
    problemas = revisar_moodle("::a::Texto {T} [tags: x]\n\n::b::Explicá {desarrollo:grande}\n")
    assert len(problemas) == 2
    assert "Línea 1 («a»)" in problemas[0] and "[tags: x]" in problemas[0]
    assert "Línea 3 («b»)" in problemas[1] and "{}" in problemas[1]


def test_corrige_para_moodle_sin_cambiar_las_preguntas(tmp_path):
    viejo = ("// encabezado\n\n$CATEGORY: a/b\n\n"
             "::uno::[markdown]Elegí: {\n=`x`\n~`y`\n} [tags: t1, t2] [category: C]\n\n"
             "// nota\n::dos::Explicá {desarrollo:grande} [tags: t3]\n\n"
             "::tres::Sin tamaño {\n  desarrollo\n}\n[tag: t4]\n\n"
             "::cuatro::Mirá\n```estructura\ntype: stack\nvalues: [1]\n```\n{T}\n")
    nuevo = corregir_para_moodle(viejo)

    assert revisar_moodle(nuevo) == []
    assert corregir_para_moodle(nuevo) == nuevo
    assert "// [tag, t1, t2] [category, C]\n::uno::" in nuevo
    assert "// nota\n// [tag, desarrollo-grande, t3]\n::dos::Explicá {}\n" in nuevo
    assert "// [tag, t4]\n::tres::Sin tamaño {}\n\n" in nuevo
    assert "type: stack" in nuevo

    def datos(contenido):
        return [(p.nombre, p.tipo, sorted(p.etiquetas), p.categoria, p.enunciado_html, p.tamano_desarrollo)
                for p in preguntas(tmp_path, contenido)]
    assert datos(nuevo) == datos(viejo)


def test_los_metadatos_con_dos_puntos_se_avisan_y_se_corrigen():
    viejo = "// [tag:a] [category:b] [id:q1]\n::p::Texto {T}\n"
    assert len(revisar_moodle(viejo)) == 2
    nuevo = corregir_para_moodle(viejo)
    assert nuevo.startswith("// [tag, a] [category, b] [id:q1]\n") and revisar_moodle(nuevo) == []


def test_un_tamano_que_nunca_se_leyo_queda_como_desarrollo_sin_etiqueta():
    assert corregir_para_moodle("::a::Texto {desarrollo:3}\n") == "::a::Texto {}\n"


def test_lint_falla_sin_fix_y_con_fix_reescribe(tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text("::a::Texto: {T} [tags: x]\n\n", encoding="utf-8")
    assert lint_gift_file(banco) is False
    assert "[tags" in banco.read_text(encoding="utf-8")

    assert lint_gift_file(banco, fix=True) is True
    corregido = banco.read_text(encoding="utf-8")
    assert corregido == "// [tag, x]\n::a::Texto： {T}\n\n"
    assert lint_gift_file(banco, fix=True) is True
    assert banco.read_text(encoding="utf-8") == corregido


@pytest.fixture
def arbol(tmp_path):
    raiz = tmp_path / "bancos"
    for ruta, nombre in [("u1/teoria.gift", "uno"), ("u2/teoria.gift", "dos"), ("u2/sub/extra.gift", "tres"), ("u1/leeme.txt", "texto"),
                         (".oculta/x.gift", "oculta")]:
        archivo = raiz / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(f"::{nombre}::Texto {{T}}\n", encoding="utf-8")
    (raiz / "u1" / "notas.md").write_text("no es un banco", encoding="utf-8")
    return raiz


def test_una_carpeta_aporta_los_bancos_de_sus_subcarpetas(arbol):
    banco = cargar_bancos([arbol])
    assert {p.nombre: p.fuente_banco for p in banco.values()} == {
        "uno": "u1/teoria.gift", "dos": "u2/teoria.gift", "tres": "u2/sub/extra.gift"}


def test_un_archivo_nombrado_y_su_carpeta_no_cargan_dos_veces(arbol, caplog):
    with caplog.at_level(logging.WARNING):
        banco = cargar_bancos([arbol / "u1" / "teoria.gift", arbol])
    assert len(banco) == 3 and "duplicada" not in caplog.text


def test_un_txt_se_lee_solo_si_se_lo_nombra(arbol):
    banco = cargar_bancos([arbol / "u1" / "leeme.txt"])
    assert [p.nombre for p in banco.values()] == ["texto"]


def test_avisa_si_la_carpeta_no_tiene_bancos(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        assert cargar_bancos([tmp_path]) == {}
    assert "no tiene bancos" in caplog.text


@pytest.mark.parametrize("filtro, nombres", [
    ("teoria.gift", {"uno", "dos"}),
    ("u2/teoria.gift", {"dos"}),
    ("bancos/u1/teoria.gift", {"uno"}),
    ("extra.gift", {"tres"}),
])
def test_el_filtro_banco_distingue_por_subcarpeta(arbol, filtro, nombres):
    pool = PoolConfig(nombre="p", cantidad=1, puntos_por_pregunta=1, banco=filtro)
    assert {p.nombre for p in candidatas_pool(pool, cargar_bancos([arbol]))} == nombres


def test_lint_gift_recorre_una_carpeta_sin_los_xml(arbol, capsys):
    (arbol / "u1" / "moodle.xml").write_text("<quiz/>", encoding="utf-8")
    assert revisar_archivos([arbol]) == 0
    salida = capsys.readouterr().out
    assert "Total archivos: 3" in salida and "moodle.xml" not in salida and "leeme.txt" not in salida


def test_el_cli_acepta_carpetas_de_bancos(arbol):
    from typer.testing import CliRunner

    assert CliRunner().invoke(app, ["lint-gift", str(arbol)]).exit_code == 0


def test_el_comentario_de_arriba_es_el_criterio_de_la_clave(tmp_path):
    uno, dos = preguntas(tmp_path, (
        "// =====\n// Encabezado del banco\n\n"
        "// =====\n// Criterio (5 puntos):\n// - [2 pts] **cpp**\n// =====\n"
        "// [tag, desarrollo-mediano, gcc]\n::a::Explicá {}\n\n"
        "// suelto, separado\n\n// [tag, x]\n::b::Mirá\n```c\nint x;\n\n// no es criterio\n```\n{}\n"))
    criterio = uno.metadata["criterio_html"]
    assert "Criterio (5 puntos)" in criterio and "<strong>cpp</strong>" in criterio
    assert "=" not in criterio and "Encabezado" not in criterio and "tag" not in criterio
    assert uno.etiquetas == ["gcc"] and uno.tamano_desarrollo == "mediano"
    assert dos.nombre == "b" and "criterio_html" not in dos.metadata

