"""Pruebas del sintetizador daedalus (c-synthesizer verificado con gcc)."""

import shutil
import sys
from pathlib import Path

import pytest

from generador_examenes.synthesizer import (
    compilar_y_ejecutar,
    diagnosticos,
    exportar_gift,
    exportar_xml,
    memoria_sin_liberar,
    plantillas_disponibles,
    sintetizar,
)
from generador_examenes.synthesizer.plantillas import UB_DOBLE, UB_LIBERADA, UB_LOCAL, UB_SALVAJE

pytestmark = pytest.mark.skipif(
    shutil.which("gcc") is None, reason="requiere gcc en el PATH"
)


TRAZAS = {"precedencia", "traza-punteros", "recursion", "incrementos"}
PLANTILLAS_ESPERADAS = TRAZAS | {"array-decay", "punteros-salvajes", "punteros-colgantes", "fugas-malloc"}


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


@pytest.mark.parametrize("planta", sorted(TRAZAS))
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


@pytest.mark.parametrize("planta", sorted(PLANTILLAS_ESPERADAS))
@pytest.mark.parametrize("opciones", [2, 5, 8])
def test_la_cantidad_de_opciones_es_configurable(planta, opciones):
    for s in sintetizar(planta, cantidad=3, semilla=11, opciones=opciones):
        assert len(s.opciones) == opciones
        assert len(set(s.opciones)) == opciones and s.opciones.count(s.salida_correcta) == 1


def test_opciones_fuera_de_rango():
    with pytest.raises(ValueError):
        sintetizar("recursion", cantidad=1, opciones=9)


def test_array_decay_verificado_con_la_salida_real():
    for s in sintetizar("array-decay", cantidad=6, semilla=3):
        ok, salida = compilar_y_ejecutar(s.codigo, flags_extra=["-Wno-sizeof-array-argument",
                                                                "-Wno-sizeof-pointer-div"])
        assert ok and salida == s.salida_correcta
        assert "bytes" in s.enunciado


DEFECTOS = {UB_SALVAJE, UB_LIBERADA, UB_LOCAL, UB_DOBLE}


@pytest.mark.parametrize("planta", ["punteros-salvajes", "punteros-colgantes"])
def test_comportamiento_indefinido_verificado_por_gcc(planta):
    snippets = sintetizar(planta, cantidad=8, semilla=4)
    defectuosos = [s for s in snippets if s.salida_correcta in DEFECTOS]
    correctos = [s for s in snippets if s.salida_correcta not in DEFECTOS]
    assert defectuosos and correctos  # hay de los dos: el alumno no puede responder siempre «indefinido»
    for s in defectuosos:
        assert diagnosticos(s.codigo)
    for s in correctos:
        ok, salida = compilar_y_ejecutar(s.codigo)
        assert ok and s.salida_correcta == f"Imprime `{salida}`."


def test_fugas_cuentan_la_memoria_sin_liberar():
    for s in sintetizar("fugas-malloc", cantidad=6, semilla=2):
        _, fuga, _ = memoria_sin_liberar(s.codigo)
        assert s.salida_correcta == str(fuga) and fuga > 0
        assert "bytes" not in s.titulo


def test_memoria_sin_liberar_sigue_realloc_y_calloc():
    codigo = (
        "#include <stdlib.h>\n"
        "int main(void) {\n"
        "    char *a = malloc(5);\n"
        "    char *b = realloc(a, 30);\n"
        "    if (b == NULL) { free(a); return 1; }\n"
        "    char *c = calloc(3, 4);\n"
        "    free(c);\n"
        "    return 0;\n"
        "}\n"
    )
    assert memoria_sin_liberar(codigo)[1:] == (30, 1)


def test_gift_declara_markdown_y_el_codigo_se_ve_como_codigo(tmp_path):
    from generador_examenes.parsers.gift_parser import GiftParser

    snippets = sintetizar("punteros-colgantes", cantidad=4, semilla=1)
    gift = exportar_gift(snippets)
    assert all(linea.split("::")[2].startswith(" [markdown]") for linea in gift.splitlines() if linea.startswith("::"))
    banco = tmp_path / "banco.gift"
    banco.write_text(gift, encoding="utf-8")
    preguntas = GiftParser().parse(banco)
    assert len(preguntas) == 4
    for p in preguntas.values():
        assert "<code" in p.enunciado_html and "```" not in p.enunciado_html


def test_titulos_repetidos_se_numeran():
    snippets = sintetizar("traza-punteros", cantidad=6, semilla=5)
    titulos = [l.split("::")[1] for l in exportar_gift(snippets).splitlines() if l.startswith("::")]
    assert len(set(titulos)) == len(titulos)


def test_comando_sintetizar(tmp_path, monkeypatch, capsys):
    import sys

    from generador_examenes.__main__ import main

    monkeypatch.setattr(sys, "argv", ["alucard", "sintetizar", "fugas-malloc", "-c", "2", "--opciones", "5",
                                      "-o", str(tmp_path), "--sin-voight"])
    assert main() == 0
    gift = (tmp_path / "sintetizados_fugas-malloc.gift").read_text(encoding="utf-8")
    assert gift.count("[markdown]") == 2
    assert all(len([l for l in bloque.splitlines() if l and l[0] in "=~"]) == 5 for bloque in gift.split("// daedalus")[1:])

    monkeypatch.setattr(sys, "argv", ["alucard", "sintetizar"])
    assert main() == 0
    assert "punteros-colgantes" in capsys.readouterr().out


def test_sintetizar_ya_no_es_una_opcion(monkeypatch):
    import sys

    from generador_examenes.__main__ import main

    monkeypatch.setattr(sys, "argv", ["alucard", "--sintetizar", "recursion"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_gift_con_categoria_por_plantilla(tmp_path):
    from generador_examenes.parsers.gift_parser import GiftParser

    banco = tmp_path / "b.gift"
    banco.write_text(exportar_gift(sintetizar("fugas-malloc", cantidad=2, semilla=1)), encoding="utf-8")
    assert {p.categoria for p in GiftParser().parse(banco).values()} == {"sintetizados/fugas-malloc"}


# --- Catálogo y muestra (sintetizar más explorable) -------------------------------------------

def test_cada_plantilla_dice_como_se_verifica():
    from generador_examenes.synthesizer import catalogo
    from generador_examenes.synthesizer.plantillas import PLANTILLAS

    filas = catalogo()
    assert [n for n, _, _ in filas] == sorted(PLANTILLAS)
    assert all(verificacion for _, _, verificacion in filas)


def test_muestra_sin_escribir_el_banco(tmp_path, monkeypatch, capsys):
    import shutil
    import sys

    import pytest

    if shutil.which("gcc") is None:
        pytest.skip("hace falta gcc")
    from generador_examenes.__main__ import main

    monkeypatch.setattr(sys, "argv", ["alucard", "sintetizar", "incrementos", "--muestra", "-o", str(tmp_path)])
    assert main() == 0
    salida = capsys.readouterr().out
    assert salida.startswith("[incrementos] ") and "✓ a) " in salida and "int main" in salida
    assert not list(tmp_path.iterdir())


# --- GIFT sin dos puntos y formato final con voight --------------------------------------------

def test_el_gift_no_usa_dos_puntos_en_titulo_ni_texto():
    from generador_examenes.synthesizer.engine import DOS_PUNTOS, exportar_gift
    from generador_examenes.synthesizer.plantillas import SnippetGenerado

    s = SnippetGenerado(plantilla="p", titulo="Punteros: uso tras free", enunciado="Elegí: ¿qué pasa?",
                        codigo='int main(void) { int x = 1 ? 2 : 3; return x; }',
                        salida_correcta="Comportamiento indefinido: uso tras free",
                        distractores=["Imprime 0: el puntero queda en NULL"])
    gift = exportar_gift([s])
    titulo = next(l for l in gift.splitlines() if l.startswith("::"))
    assert titulo.startswith(f"::Punteros{DOS_PUNTOS} uso tras free:: ")
    assert ":" not in titulo.replace("::", "", 2)
    assert f"Elegí{DOS_PUNTOS}" in gift
    assert f"=Comportamiento indefinido{DOS_PUNTOS}" in gift and f"~Imprime 0{DOS_PUNTOS}" in gift
    assert "1 ? 2 : 3" in gift  # el código lo convierte voight (code-chars), no esto


@pytest.mark.skipif(sys.platform == "win32", reason="el voight falso es un script de sh")
def test_voight_corre_los_tres_pasos_en_orden(tmp_path):
    import os
    import stat

    from generador_examenes.synthesizer.voight import formatear

    registro = tmp_path / "llamadas.txt"
    falso = tmp_path / "voight"
    falso.write_text(f"#!/bin/sh\necho \"$@\" >> {registro}\n", encoding="utf-8")
    falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
    banco = tmp_path / "b.gift"
    banco.write_text("x", encoding="utf-8")
    assert formatear(banco, voight=str(falso)) is None
    assert registro.read_text(encoding="utf-8").splitlines() == [
        f"fix code-indent {banco}", f"fix code-chars --to-fullwidth {banco}", f"fix format {banco}"]
    assert os.access(falso, os.X_OK)


def test_sin_voight_avisa_y_deja_el_banco(tmp_path, monkeypatch):
    from generador_examenes.synthesizer import voight

    monkeypatch.setattr(voight.shutil, "which", lambda _nombre: None)
    banco = tmp_path / "b.gift"
    banco.write_text("x", encoding="utf-8")
    problema = voight.formatear(banco)
    assert problema and "voight no está instalado" in problema and "uv tool install" in problema
    assert banco.read_text(encoding="utf-8") == "x"


@pytest.mark.skipif(sys.platform == "win32", reason="el voight falso es un script de sh")
def test_un_paso_que_falla_dice_cual(tmp_path):
    import stat

    from generador_examenes.synthesizer.voight import formatear

    falso = tmp_path / "voight"
    falso.write_text('#!/bin/sh\nif [ "$2" = "format" ]; then echo "GIFT inválido" >&2; exit 1; fi\n', encoding="utf-8")
    falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
    assert formatear(tmp_path / "b.gift", voight=str(falso)) == "`voight fix format` falló: GIFT inválido"
