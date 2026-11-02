"""Compilación Typst: un error de compilación no reintenta con el binario, y el binario tiene timeout."""

import subprocess
from pathlib import Path
import sys
import time

import pytest

from generador_examenes.generators import pdf_renderer
from generador_examenes.generators.pdf_renderer import compilar_typst_a_pdf

pytest.importorskip("typst")


def test_error_de_compilacion_no_lanza_el_binario(tmp_path, monkeypatch):
    def no_llamar(*_a, **_k):
        raise AssertionError("no tiene que reintentar con el binario typst")

    monkeypatch.setattr(pdf_renderer.subprocess, "run", no_llamar)
    inicio = time.monotonic()
    with pytest.raises(RuntimeError, match="cannot compare"):
        compilar_typst_a_pdf("#calc.min(1pt, 100%)\n", tmp_path / "x.pdf")
    assert time.monotonic() - inicio < 30


def test_compila_con_la_libreria(tmp_path):
    assert compilar_typst_a_pdf("Hola\n", tmp_path / "x.pdf").stat().st_size > 0


def test_sin_libreria_usa_el_binario_con_timeout(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "typst", None)  # import typst → ImportError
    llamadas = []

    def lento(cmd, **opciones):
        llamadas.append(opciones.get("timeout"))
        raise subprocess.TimeoutExpired(cmd, opciones.get("timeout"))

    monkeypatch.setattr(pdf_renderer.subprocess, "run", lento)
    with pytest.raises(RuntimeError, match="no terminó"):
        compilar_typst_a_pdf("Hola\n", tmp_path / "x.pdf")
    assert llamadas == [pdf_renderer.TIMEOUT_TYPST]


def test_sin_typst_en_ningun_lado(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "typst", None)

    def no_existe(cmd, **_):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(pdf_renderer.subprocess, "run", no_existe)
    with pytest.raises(RuntimeError, match="no está instalado"):
        compilar_typst_a_pdf("Hola\n", tmp_path / "x.pdf")


def test_las_fuentes_se_cargan_una_vez_por_proceso(monkeypatch, tmp_path):
    """Cada typst.compile volvía a buscar las fuentes del sistema (~0,3 s): ahora se comparten."""
    import types

    from generador_examenes.generators import pdf_renderer

    cargas, usadas = [], []

    class Fonts:
        def __init__(self):
            cargas.append(1)

    def compile(entrada, output, root=None, font_paths=None):
        usadas.append(font_paths)
        Path(output).write_bytes(b"%PDF-1.7")

    falsa = types.ModuleType("typst")
    falsa.Fonts, falsa.compile = Fonts, compile
    monkeypatch.setitem(sys.modules, "typst", falsa)
    pdf_renderer._fuentes_typst.cache_clear()
    for i in range(3):
        pdf_renderer.compilar_typst_a_pdf("= Tema", tmp_path / f"t{i}.pdf")
    assert len(cargas) == 1
    assert len(usadas) == 3 and all(isinstance(f, Fonts) for f in usadas) and len({id(f) for f in usadas}) == 1
    pdf_renderer._fuentes_typst.cache_clear()
