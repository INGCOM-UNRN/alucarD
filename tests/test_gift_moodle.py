"""Bancos GIFT que Moodle importa tal cual."""
import logging

import pytest

from generador_examenes.gift_linter import (
    corregir_para_moodle,
    dos_puntos_sueltos,
    lint_gift_file,
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
    ("", "mediano"),
    ("// [tag, desarrollo-pequeno]\n", "pequeno"),
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
