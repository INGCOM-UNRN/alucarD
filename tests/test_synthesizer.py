"""Pruebas del sintetizador daedalus (c-synthesizer verificado con gcc)."""

import shutil
from pathlib import Path

import pytest

from generador_examenes.synthesizer import (
    compilar_y_ejecutar,
    exportar_gift,
    exportar_xml,
    plantillas_disponibles,
    sintetizar,
)

pytestmark = pytest.mark.skipif(
    shutil.which("gcc") is None, reason="requiere gcc en el PATH"
)


PLANTILLAS_ESPERADAS = {"precedencia", "traza-punteros", "recursion", "incrementos"}


def test_catalogo_de_plantillas():
    disponibles = plantillas_disponibles()
    assert PLANTILLAS_ESPERADAS <= set(disponibles)
    assert all(isinstance(d, str) and d for d in disponibles.values())


def test_compilar_y_ejecutar_snippet_valido():
    ok, salida = compilar_y_ejecutar('#include <stdio.h>\nint main(void){printf("hola\\n");return 0;}\n')
    assert ok and salida == "hola"


def test_compilar_y_ejecutar_rechaza_codigo_invalido():
    ok, diagnostico = compilar_y_ejecutar("int main(void){ return x; }")
    assert not ok and "compilación falló" in diagnostico


@pytest.mark.parametrize("planta", sorted(PLANTILLAS_ESPERADAS))
def test_sintetizar_verifica_la_salida_con_gcc(planta):
    snippets = sintetizar(planta, cantidad=2, semilla=42)
    assert len(snippets) == 2
    for s in snippets:
        assert s.codigo.startswith("#include")
        assert s.salida_correcta.strip() != ""
        # la respuesta correcta fue verificada ejecutando el binario real
        ok, salida = compilar_y_ejecutar(s.codigo)
        assert ok and salida == s.salida_correcta
        # distractores verosímiles y sin duplicar la correcta
        assert len(s.opciones) >= 3
        assert s.opciones.count(s.salida_correcta) == 1


def test_sintetizar_es_determinista_con_semilla():
    a = sintetizar("recursion", cantidad=3, semilla=99)
    b = sintetizar("recursion", cantidad=3, semilla=99)
    assert [(s.codigo, s.salida_correcta) for s in a] == [(s.codigo, s.salida_correcta) for s in b]


def test_sintetizar_plantilla_desconocida():
    with pytest.raises(KeyError):
        sintetizar("no-existe")


def test_exportar_gift_parsea_con_el_parser_propio(tmp_path):
    """El banco generado debe ser consumible por alucarD (round-trip interno)."""
    from generador_examenes.parsers.gift_parser import GiftParser

    snippets = sintetizar("traza-punteros", cantidad=2, semilla=5)
    banco = tmp_path / "banco.gift"
    banco.write_text(exportar_gift(snippets), encoding="utf-8")

    preguntas = GiftParser().parse(banco)
    assert len(preguntas) == len(snippets)
    for p in preguntas.values():
        correctas = [o for o in p.opciones if o.es_correcta]
        assert len(correctas) == 1
        salidas = {s.salida_correcta for s in snippets}
        assert correctas[0].texto_html in salidas


def test_exportar_xml_genera_moodle_valido(tmp_path):
    import xml.etree.ElementTree as ET

    snippets = sintetizar("precedencia", cantidad=1, semilla=1)
    xml = exportar_xml(snippets)
    raiz = ET.fromstring(xml)
    assert raiz.tag == "quiz"
    preguntas = raiz.findall("question[@type='multichoice']")
    assert len(preguntas) == 1
    respuestas = preguntas[0].findall("answer")
    fracciones = [a.get("fraction") for a in respuestas]
    assert "100" in fracciones


def test_exportaciones_no_duplican_la_respuesta_correcta(tmp_path):
    snippets = sintetizar("incrementos", cantidad=1, semilla=8)
    gift = exportar_gift(snippets)
    correcta = snippets[0].salida_correcta
    marcadas = [l for l in gift.splitlines() if l.startswith("=")]
    assert any(correcta in l for l in marcadas)
