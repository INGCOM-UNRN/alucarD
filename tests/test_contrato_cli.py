"""Contrato de línea de comandos (LINEAMIENTOS §3.2, N-ECO-04): -h/--help, --version/-v y doctor --json.

Ayuda y versión con el test reutilizable de yutani (N-ECO-14); `doctor --json` se prueba con
`main()`, que es quien devuelve el código de salida del comando.
"""

from __future__ import annotations

import json
import sys

import pytest
from typer.testing import CliRunner
from yutani.testing import pruebas_de_contrato

from generador_examenes import __version__
from generador_examenes.__main__ import app, main

test_ayuda, test_version = pruebas_de_contrato(app, doctor=False)


def _correr(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    return codigo or 0, capsys.readouterr().out


@pytest.mark.parametrize("opcion", ["-h", "--help", "--version", "-v"])
def test_ayuda_y_version_desde_main(monkeypatch, capsys, opcion):
    codigo, salida = _correr(monkeypatch, capsys, [opcion])
    assert codigo == 0
    assert salida.strip()


def test_la_version_nombra_la_herramienta(monkeypatch, capsys):
    _, salida = _correr(monkeypatch, capsys, ["--version"])
    assert salida.strip() == f"alucard {__version__}"


def test_la_ayuda_esta_en_espanol():
    salida = CliRunner().invoke(app, ["--help"], env={"COLUMNS": "150"}).output
    assert "Uso:" in salida and "Muestra esta ayuda y sale." in salida


def test_doctor_json(monkeypatch, capsys):
    codigo, salida = _correr(monkeypatch, capsys, ["doctor", "--json"])
    datos = json.loads(salida)
    assert datos["schema_version"] == "1.0.0"
    assert datos["herramienta"] == "alucard"
    assert codigo == (0 if datos["ok"] else 1)
