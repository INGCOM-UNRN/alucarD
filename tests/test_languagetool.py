"""Tests para el verificador de LanguageTool en alucard."""

import json
from pathlib import Path
import pytest

# myst-tools llega con el extra `languagetool` (uv sync --extra languagetool).
pytest.importorskip("myst_tools", reason="requiere el extra languagetool (myst-tools)")

from generador_examenes.core.models import Pregunta, Opcion  # noqa: E402
from generador_examenes.core.languagetool_checker import (  # noqa: E402
    enmascarar_pregunta,
    consultar_languagetool,
    analizar_pregunta_languagetool,
    aplicar_autofix_pregunta,
    generar_reporte_markdown_languagetool,
    LanguageToolIssue,
)


def test_enmascarar_pregunta_alucard():
    texto = (
        "<p>¿Cuál es la complejidad temporal de la búsqueda binaria?</p>"
        "<pre><code>int x = 10;</code></pre>"
        "Fórmula: \\(O(\\log N)\\) y código `void* ptr`."
    )
    enmascarado, _ = enmascarar_pregunta(texto)
    assert "¿Cuál es la complejidad temporal de la búsqueda binaria?" in enmascarado
    assert "<p>" not in enmascarado
    assert "int x = 10;" not in enmascarado
    assert "O(\\log N)" not in enmascarado
    assert "void* ptr" not in enmascarado
    assert len(enmascarado) == len(texto)


def test_consultar_languagetool_alucard_premium(monkeypatch):
    captured = []

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps({"matches": []}).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10.0: (captured.append(req), MockResponse())[1])

    # 1. Local
    consultar_languagetool("Texto")
    assert len(captured) == 1
    assert "localhost:8081" in captured[0].full_url or "api.languagetool.org" in captured[0].full_url

    # 2. Premium con credenciales
    consultar_languagetool("Texto", username="docente@fi.uba.ar", api_key="lt-key-456", premium=True)
    assert len(captured) == 2
    assert "api.languagetoolplus.com" in captured[1].full_url
    body = captured[1].data.decode("utf-8")
    assert "username=docente%40fi.uba.ar" in body
    assert "apiKey=lt-key-456" in body


def test_analizar_y_autofix_pregunta(monkeypatch):
    p = Pregunta(
        id="p1",
        tipo="seleccion_multiple",
        nombre="Pregunta con eror",
        categoria="algoritmos",
        enunciado_html="<p>Enunciado con prueva de error.</p>",
        opciones=[
            Opcion(texto_html="Opcion corecta", es_correcta=True),
            Opcion(texto_html="Opcion incorecta", es_correcta=False),
        ]
    )

    sample_response = {
        "matches": [
            {
                "message": "Falta de ortografía",
                "shortMessage": "Error",
                "offset": 13,
                "length": 4,
                "rule": {"id": "MORFOLOGIK_RULE_ES", "category": {"name": "Ortografía"}},
                "context": {"text": "Pregunta con eror", "offset": 13, "length": 4},
                "replacements": [{"value": "error"}],
            }
        ]
    }

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps(sample_response).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10.0: MockResponse())

    issues = analizar_pregunta_languagetool(p)
    assert len(issues) >= 1
    assert issues[0].original_word == "eror"

    cambios = aplicar_autofix_pregunta(p, issues)
    assert cambios >= 1
    assert "error" in p.nombre
