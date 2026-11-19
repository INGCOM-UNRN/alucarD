"""Diagramas de control de procesos: las cuentas (contra resultados conocidos) y los SVG."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from generador_examenes import control
from generador_examenes.diagramas import (
    TIPOS,
    ErrorDiagrama,
    expandir_en_markdown,
    leer_bloques,
    renderizar,
)

EJEMPLOS = leer_bloques((Path(__file__).parent / "datos" / "diagramas_control.yaml").read_text(encoding="utf-8"))


# --- Cuentas -----------------------------------------------------------------------------------------

def test_raices():
    assert [round(r.real, 9) for r in control.raices([1, 6, 11, 6])] == [-3, -2, -1]
    assert sorted((round(r.real, 9), round(r.imag, 9)) for r in control.raices([1, 2, 5])) == [(-1, -2), (-1, 2)]
    assert [r for r in control.raices([1, 0, 0])] == [0, 0]


@pytest.mark.parametrize("dato, num, den", [
    ({"gain": 2, "tau": 5}, [2], [5, 1]),
    ({"gain": 1, "zeta": 0.5, "wn": 2}, [4], [1, 2, 4]),
    ({"k": 3, "poles": [-1, -2], "zeros": [-5]}, [3, 15], [1, 3, 2]),
    ({"k": 1, "poles": [[-1, 2]]}, [1], [1, 2, 5]),
    ({"num": [1, 2], "den": [1, 0, 4]}, [1, 2], [1, 0, 4]),
    ({"kp": 2, "ki": 0.5, "kd": 0.1}, [0.1, 2, 0.5], [1, 0]),
])
def test_las_formas_de_escribir_un_sistema(dato, num, den):
    s = control.sistema(dato)
    assert [round(c.real, 9) for c in s.num] == num and [round(c.real, 9) for c in s.den] == den


@pytest.mark.parametrize("dato, mensaje", [
    ({"tau": -1}, "positiva"), ({"den": []}, "coeficientes"), ({"gain": 1}, "falta"), ({"poles": [[1, 2, 3]]}, "par complejo"),
    ({"num": [1], "den": [1, 1], "delay": -2}, "negativo"),
])
def test_sistemas_invalidos(dato, mensaje):
    with pytest.raises(control.ErrorControl, match=mensaje):
        control.sistema(dato)


def test_segundo_orden_coincide_con_las_formulas():
    zeta, wn = 0.3, 2.0
    ts, _, ys = control.simular_abierto(control.sistema({"zeta": zeta, "wn": wn}), 15)
    car = control.caracteristicas(ts, ys, final=1.0)
    raiz = math.sqrt(1 - zeta ** 2)
    assert car["overshoot"] == pytest.approx(100 * math.exp(-math.pi * zeta / raiz), abs=0.05)
    assert car["peak"] == pytest.approx(math.pi / (wn * raiz), abs=0.01)


def test_primer_orden_con_tiempo_muerto():
    ts, _, ys = control.simular_abierto(control.sistema({"gain": 2, "tau": 5, "delay": 1}), 40)
    car = control.caracteristicas(ts, ys, final=2.0)
    assert car["tau"] == pytest.approx(5, abs=0.05) and car["delay"] == pytest.approx(1, abs=0.05)
    tangente = control.tangente_inflexion(ts, ys, 2.0)
    assert tangente["L"] == pytest.approx(1, abs=0.05) and tangente["T"] == pytest.approx(5, abs=0.1)


def test_lazo_con_pi_no_tiene_error_en_estado_estacionario():
    lz = control.lazo({"plant": {"gain": 2, "tau": 5, "delay": 1}, "controller": {"kp": 1.2, "ki": 0.25}})
    _, _, ys, _ = control.simular_lazo(lz, 80)
    assert ys[-1] == pytest.approx(1, abs=1e-3)
    solo_p = control.lazo({"plant": {"gain": 2, "tau": 5}, "controller": {"kp": 2}})
    _, _, ys, _ = control.simular_lazo(solo_p, 40)
    assert ys[-1] == pytest.approx(4 / 5, abs=1e-3)         # Kp K / (1 + Kp K): error de posición
    assert solo_p.cerrado().ganancia_estatica == pytest.approx(0.8)


def test_margenes_y_cruce_del_eje_imaginario():
    s = control.sistema({"k": 1, "poles": [0, -1, -2]})
    m = control.margenes(s, 0.01, 100)
    assert m["w180"] == pytest.approx(math.sqrt(2), rel=1e-4)
    assert m["gm"] == pytest.approx(20 * math.log10(6), rel=1e-4)
    k, w = control.cruce_imaginario(s, 20)
    assert k == pytest.approx(6, rel=1e-3) and w == pytest.approx(math.sqrt(2), rel=1e-3)
    assert control.asintotas(s) == (-1.0, [60.0, 180.0, 300.0])


def test_la_fase_no_salta():
    s = control.sistema({"k": 1, "poles": [-1, -1, -1, -1]})
    assert control.fase_continua(s, 1000) == pytest.approx(-360, abs=0.5)
    assert control.fase_continua(control.sistema({"gain": 1, "tau": 1, "delay": 1}), 1) == pytest.approx(-45 - 57.2958, abs=0.01)


def test_asintota_de_bode():
    s = control.sistema({"k": 10, "poles": [-1, -10]})
    assert control.asintota_db(s, 0.1) == pytest.approx(0, abs=1e-9)          # 10 / (1 · 10)
    assert control.asintota_db(s, 100) == pytest.approx(-60, abs=1e-9)        # -40 dB/década desde 10


def test_un_sistema_impropio_no_se_simula():
    with pytest.raises(control.ErrorControl, match="impropio"):
        control.simular_abierto(control.sistema({"num": [1, 0, 0], "den": [1, 1]}), 5)


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
