"""Diagramas de control de procesos: validación de los SVG generados por `dibu`."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from generador_examenes.diagramas import (
    TIPOS,
    ErrorDiagrama,
    expandir_en_markdown,
    leer_bloques,
    renderizar,
)

EJEMPLOS = leer_bloques((Path(__file__).parent / "datos" / "diagramas_control.yaml").read_text(encoding="utf-8"))


# --- SVG -----------------------------------------------------------------------------------------------

def test_los_tipos_nuevos_estan_registrados():
    assert {"block_diagram", "time_response", "bode", "nyquist", "pole_zero", "root_locus", "instrumentation",
            "ladder", "grafcet"} <= set(TIPOS)


@pytest.mark.parametrize("bloque", EJEMPLOS, ids=[b["id"] for b in EJEMPLOS])
@pytest.mark.parametrize("tinta", [True, False])
def test_cada_ejemplo_es_un_svg_valido(bloque, tinta):
    svg = renderizar(bloque, tinta=tinta)
    raiz = ET.fromstring(svg)
    assert raiz.tag.endswith("svg") and float(raiz.get("width")) > 100 and float(raiz.get("height")) > 80
    assert "nan" not in svg.lower().replace("nanosec", "")


def _texto(svg: str) -> str:
    return " ".join(t.text or "" for t in ET.fromstring(svg).iter() if t.tag.endswith("text"))


def test_anotaciones_de_la_respuesta():
    svg = renderizar({"type": "time_response", "system": {"zeta": 0.3, "wn": 2}, "annotations": ["overshoot", "peak"]})
    assert "Mp = 37,2 %" in _texto(svg) and "tp = 1,65" in _texto(svg)
    blanco = renderizar({"type": "time_response", "system": {"zeta": 0.3, "wn": 2}, "annotations": ["overshoot"],
                         "blankAnnotations": True})
    assert "Mp =" in _texto(blanco) and "37,2" not in _texto(blanco)


def test_los_margenes_de_bode_en_el_rotulo():
    texto = _texto(renderizar({"type": "bode", "system": {"k": 1, "poles": [0, -1, -2]}, "margins": True}))
    assert "MG = 15,6 dB" in texto and "ω180 = 1,41" in texto


def test_lugar_de_las_raices_marca_kcritico():
    assert "Kcrít = 6" in _texto(renderizar({"type": "root_locus", "system": {"k": 1, "poles": [0, -1, -2]}}))


def test_el_centroide_queda_en_blanco_con_blankmarks():
    bloque = {"type": "root_locus", "system": {"k": 1, "poles": [0, -1, -2, -4], "zeros": [-3]}, "showCrossing": False}
    assert "σa = −1,33" in _texto(renderizar(bloque)).replace("-", "−")
    assert "1,33" not in _texto(renderizar({**bloque, "blankMarks": True}))


def test_bloques_en_blanco_y_signos():
    svg = renderizar({"type": "block_diagram", "forward": [{"blank": True}, "Gp(s)"], "feedback": [], "blankSigns": True})
    texto = _texto(svg)
    assert "Gp(s)" in texto and "−" not in texto


def test_la_escalera_acepta_no_aunque_yaml_lo_lea_como_false():
    bloque = leer_bloques("type: ladder\nrungs:\n  - logic:\n      - no: I0.0\n      - coil: Q0.0\n")[0]
    assert "I0.0" in _texto(renderizar(bloque))


def test_instrumento_en_blanco():
    svg = renderizar({"type": "instrumentation", "instruments": [{"id": "x", "tag": "TIC 5", "at": [1, 1], "blank": True}]})
    assert "TIC" not in _texto(svg)


@pytest.mark.parametrize("bloque, mensaje", [
    ({"type": "time_response"}, "falta system"),
    ({"type": "time_response", "system": {"tau": 1}, "annotations": ["magia"]}, "anotaciones desconocidas"),
    ({"type": "bode", "system": {"tau": 1}, "show": "todo"}, "show"),
    ({"type": "block_diagram", "forward": []}, "forward"),
    ({"type": "block_diagram", "forward": ["G"], "disturbance": {"at": 5}}, "disturbance.at"),
    ({"type": "instrumentation", "equipment": [{"id": "a", "kind": "cohete", "at": [1, 1]}]}, "kind"),
    ({"type": "instrumentation", "equipment": [{"id": "a", "kind": "pump", "at": [1, 1]}],
      "lines": [{"from": "a", "to": "b"}]}, "no hay un equipo"),
    ({"type": "ladder", "rungs": [{"logic": [{"coil": "Q"}]}]}, "al menos un contacto"),
    ({"type": "ladder", "rungs": [{"logic": [{"nc": "I"}]}]}, "terminar en una salida"),
    ({"type": "ladder", "rungs": [{"logic": [{"nc": "I"}, {"motor": "Q"}]}]}, "elemento desconocido"),
    ({"type": "grafcet", "steps": [{"etapa": 1}]}, "elemento desconocido"),
    ({"type": "root_locus", "system": {"num": [1], "den": [2]}}, "no tiene polos"),
])
def test_errores_claros(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=mensaje):
        renderizar(bloque)


def test_en_markdown():
    _, svgs = expandir_en_markdown("Mirá:\n\n```estructura\ntype: bode\nsystem: {gain: 1, tau: 2}\n```\n")
    assert len(svgs) == 1 and "<svg" in next(iter(svgs.values()))
