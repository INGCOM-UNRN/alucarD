"""`alucard --spellcheck` revisa las preguntas de los bancos (N-ALUCARD-04).

El modo importaba generador_examenes.config.config_loader, que no existe, leía
`definicion.bancos_preguntas` (el campo es input_banco) y trataba el
{id: Pregunta} de cargar_bancos como listas: terminaba siempre en error sin
revisar una sola pregunta. Los tests reemplazan la consulta a LanguageTool
(no usan la red).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

# myst-tools llega con el extra `languagetool` (uv sync --extra languagetool).
pytest.importorskip("myst_tools", reason="requiere el extra languagetool (myst-tools)")

from generador_examenes.__main__ import main  # noqa: E402
from generador_examenes.core import languagetool_checker  # noqa: E402
from generador_examenes.core.logic import cargar_bancos  # noqa: E402

EJEMPLOS = Path(__file__).parent / "bancos_ejemplo"
BANCO = EJEMPLOS / "banco_test.txt"


def _correr(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    captura = capsys.readouterr()
    return codigo or 0, captura.out + captura.err


@pytest.fixture
def revisadas(monkeypatch, tmp_path):
    """Reemplaza la consulta a LanguageTool y anota qué preguntas se revisaron."""
    monkeypatch.chdir(tmp_path)  # sin definicion.yaml de la carpeta actual
    ids: list[str] = []

    def analizar(pregunta, **_opciones):
        ids.append(pregunta.id)
        return []

    monkeypatch.setattr(languagetool_checker, "analizar_pregunta_languagetool", analizar)
    return ids


def test_revisa_las_preguntas_del_banco_indicado(monkeypatch, capsys, revisadas):
    codigo, salida = _correr(monkeypatch, capsys, ["--spellcheck", "-i", str(BANCO)])

    esperadas = set(cargar_bancos([BANCO]))
    assert codigo == 0, salida
    assert esperadas and set(revisadas) == esperadas
    assert f"{len(esperadas)} preguntas sin observaciones" in salida


def test_toma_los_bancos_de_la_definicion(monkeypatch, capsys, revisadas, tmp_path):
    datos = yaml.safe_load((EJEMPLOS / "definicion_ejemplo.yaml").read_text(encoding="utf-8"))
    datos["input_banco"] = [str(BANCO)]
    definicion = tmp_path / "examen.yaml"
    definicion.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")

    codigo, salida = _correr(monkeypatch, capsys, ["--spellcheck", "--definicion", str(definicion)])

    assert codigo == 0, salida
    assert set(revisadas) == set(cargar_bancos([BANCO]))


def test_informa_las_observaciones(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)

    def analizar(pregunta, **_opciones):
        return [SimpleNamespace(pregunta_id=pregunta.id, campo="enunciado", line=1, column=5,
                                original_word="ejenplo", context="un ejenplo", replacements=["ejemplo"])]

    monkeypatch.setattr(languagetool_checker, "analizar_pregunta_languagetool", analizar)
    codigo, salida = _correr(monkeypatch, capsys, ["--spellcheck", "-i", str(BANCO)])

    assert codigo == 1
    assert "ejenplo" in salida and "ejemplo" in salida
