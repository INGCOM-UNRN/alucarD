"""Compilación Typst: un error de compilación no reintenta con el binario, y el binario tiene timeout."""

import subprocess
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
