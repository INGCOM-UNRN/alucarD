"""`alucard lint-gift` reemplaza al ejecutable suelto gift-linter, que queda como alias (N-ALUCARD-02).

gift-linter no respondía el contrato: `gift-linter --version` no existía y `gift-linter doctor`
tomaba «doctor» por un archivo y salía con 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from generador_examenes import __version__
from generador_examenes.__main__ import main
from generador_examenes.gift_linter import main as gift_linter

LIMPIO = "::P1:: ¿Cuánto es 2+2? {=4 ~3 ~5}\n"
CON_ERRORES = "::P1:: Sin respuesta correcta {~3 ~5}\n"


def _alucard(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    captura = capsys.readouterr()
    return codigo or 0, captura.out + captura.err


def _gift_linter(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["gift-linter", *args])
    with pytest.raises(SystemExit) as salida:
        gift_linter()
    return salida.value.code or 0, capsys.readouterr().out


def test_lint_gift_revisa_los_bancos(monkeypatch, capsys, tmp_path):
    limpio, con_errores = tmp_path / "limpio.gift", tmp_path / "errores.gift"
    limpio.write_text(LIMPIO, encoding="utf-8")
    con_errores.write_text(CON_ERRORES, encoding="utf-8")

    codigo, salida = _alucard(monkeypatch, capsys, ["lint-gift", str(limpio)])
    assert codigo == 0 and "Todos sin errores" in salida
    codigo, salida = _alucard(monkeypatch, capsys, ["lint-gift", str(limpio), str(con_errores)])
    assert codigo == 1 and "Algunos con errores" in salida


def test_lint_gift_con_un_archivo_que_no_existe_es_un_error_de_uso(monkeypatch, capsys, tmp_path):
    codigo, salida = _alucard(monkeypatch, capsys, ["lint-gift", str(tmp_path / "no_existe.gift")])
    assert codigo == 2 and "no_existe.gift" in salida


def test_gift_linter_responde_el_contrato(monkeypatch, capsys, tmp_path):
    codigo, salida = _gift_linter(monkeypatch, capsys, ["--version"])
    assert codigo == 0 and salida.strip() == f"gift-linter {__version__}"

    codigo, salida = _gift_linter(monkeypatch, capsys, ["doctor", "--json"])
    datos = json.loads(salida)
    assert datos["schema_version"] == "1.0.0" and codigo == (0 if datos["ok"] else 1)

    banco = tmp_path / "banco.gift"
    banco.write_text(LIMPIO, encoding="utf-8")
    codigo, salida = _gift_linter(monkeypatch, capsys, [str(banco)])
    assert codigo == 0 and "Todos sin errores" in salida


def test_la_ayuda_de_gift_linter_esta_en_espanol(monkeypatch, capsys):
    codigo, salida = _gift_linter(monkeypatch, capsys, ["--help"])
    assert codigo == 0
    assert salida.startswith("Uso: gift-linter") and "Muestra esta ayuda y sale." in salida
    assert "Usage" not in salida and "Show " not in salida


def test_install_completion_sin_bashrc_es_un_error(monkeypatch, capsys, tmp_path):
    # Path.home y no HOME: en Windows, Path.home() toma USERPROFILE.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(sys, "argv", ["gift-linter", "--install-completion"])
    with pytest.raises(SystemExit) as salida:
        gift_linter()
    assert salida.value.code == 1
    assert "no se instaló el autocompletado" in capsys.readouterr().err

    (tmp_path / ".bashrc").write_text("# bashrc\n", encoding="utf-8")
    with pytest.raises(SystemExit) as salida:
        gift_linter()
    assert salida.value.code == 0
    assert "complete -F _gift_linter_completion gift-linter" in (tmp_path / ".bashrc").read_text(encoding="utf-8")
