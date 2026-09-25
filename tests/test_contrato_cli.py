"""Contrato de línea de comandos (LINEAMIENTOS §3.2, N-ECO-04): -h/--help, --version/-v y doctor --json."""

from __future__ import annotations

import json
import sys

import pytest

from generador_examenes.__main__ import main


def _correr(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    return codigo or 0, capsys.readouterr().out


@pytest.mark.parametrize("opcion", ["-h", "--help", "--version", "-v"])
def test_ayuda_y_version(monkeypatch, capsys, opcion):
    codigo, salida = _correr(monkeypatch, capsys, [opcion])
    assert codigo == 0
    assert salida.strip()


def test_version_informa_el_paquete(monkeypatch, capsys):
    from generador_examenes import __version__

    _, salida = _correr(monkeypatch, capsys, ["--version"])
    assert __version__ in salida


def test_doctor_json(monkeypatch, capsys):
    codigo, salida = _correr(monkeypatch, capsys, ["doctor", "--json"])
    datos = json.loads(salida)
    assert datos["schema_version"] == "1.0.0"
    assert datos["herramienta"] == "alucard"
    assert codigo == (0 if datos["ok"] else 1)
