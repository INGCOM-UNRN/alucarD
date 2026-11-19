"""Diagramas de química: las cuentas (contra valores de tabla) y los SVG."""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from generador_examenes.diagramas import TIPOS, ErrorDiagrama, leer_bloques, renderizar
from generador_examenes import quimica as q
from generador_examenes.diagramas_quimica import partes_formula

EJEMPLOS = leer_bloques((Path(__file__).parent / "datos" / "diagramas_quimica.yaml").read_text(encoding="utf-8"))


# --- Cuentas -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("elemento, carga, nucleo, desapareados", [
    ("O", 0, "[He] 2s² 2p⁴", 2),
    ("Fe", 0, "[Ar] 4s² 3d⁶", 4),
    ("Fe", 2, "[Ar] 3d⁶", 4),                 # el catión pierde primero el 4s
    ("Cr", 0, "[Ar] 4s¹ 3d⁵", 6),             # excepción
    ("Cu", 0, "[Ar] 4s¹ 3d¹⁰", 1),
    ("Cu", 2, "[Ar] 3d⁹", 1),
    ("Cl", -1, "[Ne] 3s² 3p⁶", 0),
    ("Na", 0, "[Ne] 3s¹", 1),
])
def test_configuraciones(elemento, carga, nucleo, desapareados):
    conf = q.configuracion(elemento, carga)
    assert conf.texto(nucleo=True) == nucleo and conf.desapareados() == desapareados


def test_configuracion_completa_y_por_numero_atomico():
    assert q.configuracion(8).texto() == "1s² 2s² 2p⁴"
    with pytest.raises(q.ErrorQuimica, match="desconocido"):
        q.configuracion("Xx")


@pytest.mark.parametrize("atomos, carga, orden, magnetismo", [
    ("H", 0, 1, "diamagnética"), ("He", 0, 0, "diamagnética"), ("N", 0, 3, "diamagnética"),
    ("O", 0, 2, "paramagnética"), ("O", -1, 1.5, "paramagnética"), ("O", 2, 3, "diamagnética"),
    ("F", 0, 1, "diamagnética"), ("C", 0, 2, "diamagnética"), ("B", 0, 1, "paramagnética"),
    (["C", "O"], 0, 3, "diamagnética"), (["N", "O"], 0, 2.5, "paramagnética"),
])
def test_orbitales_moleculares(atomos, carga, orden, magnetismo):
    om = q.orbitales_moleculares(atomos, carga)
    assert om.orden_enlace == orden and om.magnetismo == magnetismo


def test_mezcla_sp_cambia_el_orden_de_los_niveles():
    nombres = [n.nombre for n in q.orbitales_moleculares("N").niveles]
    assert nombres.index("π2p") < nombres.index("σ2p")
    nombres = [n.nombre for n in q.orbitales_moleculares("O").niveles]
    assert nombres.index("σ2p") < nombres.index("π2p")


@pytest.mark.parametrize("analito, inicial, equivalencias, semi", [
    ({"kind": "weak_acid", "pKa": 4.76, "conc": 0.1, "volume": 25}, 2.88, [(25, 8.73)], [(12.5, 4.76)]),
    ({"kind": "strong_acid", "conc": 0.1, "volume": 25}, 1.0, [(25, 7.0)], []),
    ({"kind": "weak_base", "pKb": 4.75, "conc": 0.1, "volume": 25}, 11.12, [(25, 5.28)], [(12.5, 9.25)]),
    # Con un pKa1 tan bajo, en la primera semiequivalencia el pH (2,29) ya no es el pKa: se disocia de más.
    ({"kind": "weak_acid", "pKa": [2.15, 7.2, 12.35], "conc": 0.1, "volume": 25}, 1.63, [(25, 4.70), (50, 9.66)],
     [(12.5, 2.29), (37.5, 7.2), (62.5, 11.86)]),
    ({"kind": "weak_base", "pKa": [6.35, 10.33], "charge": -2, "conc": 0.1, "volume": 25}, 11.65,
     [(25, 8.34), (50, 3.91)], [(12.5, 10.32), (37.5, 6.35)]),
])
def test_titulaciones(analito, inicial, equivalencias, semi):
    t = q.titulacion(analito, 0.1)
    assert t.ph_inicial == pytest.approx(inicial, abs=0.01)
    assert [(round(v, 2), round(ph, 2)) for v, ph in t.equivalencias] == equivalencias
    for (v, ph, _), (v_esp, ph_esp) in zip(t.semi, semi, strict=True):
        assert v == pytest.approx(v_esp) and ph == pytest.approx(ph_esp, abs=0.02)


def test_fracciones_suman_uno_y_se_cruzan_en_el_pka():
    kas = [10 ** -2.15, 10 ** -7.2, 10 ** -12.35]
    alfas = q.fracciones(10 ** -7.2, kas)
    assert sum(alfas) == pytest.approx(1) and alfas[1] == pytest.approx(alfas[2], rel=1e-3)


@pytest.mark.parametrize("orden, k, a0, t_medio", [(0, 0.05, 1, 10), (1, 0.1, 1, math.log(2) / 0.1), (2, 0.2, 1, 5)])
def test_vida_media_y_concentracion(orden, k, a0, t_medio):
    assert q.vida_media(orden, k, a0) == pytest.approx(t_medio)
    assert q.concentracion(orden, k, a0, t_medio) == pytest.approx(a0 / 2)


def test_consecutivas_y_reversibles():
    tmax = q.t_maximo_intermediario(0.5, 0.2)
    assert tmax == pytest.approx(math.log(0.2 / 0.5) / (0.2 - 0.5))
    a, b, c = q.consecutiva(0.5, 0.2, 1, tmax)
    assert a + b + c == pytest.approx(1)
    a, b = q.reversible(0.3, 0.1, 1, 1e3)
    assert b / a == pytest.approx(3)


def test_diagrama_de_fases_pasa_por_los_puntos_normales():
    agua = q.fases({"substance": "water"})
    assert agua.t_de_p(1.0) == ("ebullición", pytest.approx(373.15))
    assert agua.p_vapor(647.1) == pytest.approx(217.7, rel=1e-6)
    co2 = q.fases({"substance": "co2"})
    tipo, t = co2.t_de_p(1.0)
    assert tipo == "sublimación" and t == pytest.approx(194.65)          # el hielo seco sublima a 1 atm


def test_curva_de_calentamiento_del_agua():
    tramos = q.calentamiento({"substance": "water", "mass": 100, "from": -20, "to": 120})
    assert [t.fase for t in tramos] == ["sólido", "fusión", "líquido", "vaporización", "gas"]
    assert [round(t.q, 2) for t in tramos] == [4.18, 33.4, 41.8, 225.7, 4.02]
    solo_liquido = q.calentamiento({"substance": "water", "from": 20, "to": 80})
    assert [t.fase for t in solo_liquido] == ["líquido"]


def test_pila_de_daniell_con_nernst():
    p = q.pila([q.semicelda({"couple": "Cu^2+/Cu", "E0": 0.34, "conc": 1}, "a"),
                q.semicelda({"couple": "Zn^2+/Zn", "E0": -0.76, "conc": 0.01}, "b")])
    assert p.anodo.electrodo == "Zn" and p.e0 == pytest.approx(1.10)
    assert p.e == pytest.approx(1.10 + 0.05916, abs=1e-4)
    assert p.delta_g == pytest.approx(-2 * 96485.33212 * 1.10 / 1000)
    assert p.anodo.oxidacion == "Zn → Zn^2+ + 2e^-"
    assert p.notacion == "Zn(s) | Zn^2+ (0,01 M) || Cu^2+ (1 M) | Cu(s)"


def test_pila_con_distinto_numero_de_electrones():
    p = q.pila([q.semicelda({"couple": "Ag^+/Ag", "E0": 0.80, "n": 1, "conc": 0.1}, "a"),
                q.semicelda({"couple": "Cu^2+/Cu", "E0": 0.34, "n": 2, "conc": 1}, "b")])
    assert p.n == 2 and p.e0 == pytest.approx(0.46)
    assert p.e == pytest.approx(0.46 - 0.05916 / 2 * math.log10(1 / 0.1 ** 2))


@pytest.mark.parametrize("red, z, coordinacion, empaquetamiento", [
    ("sc", {"A": 1}, "6", 52.4), ("bcc", {"A": 2}, "8", 68.0), ("fcc", {"A": 4}, "12", 74.0),
    ("nacl", {"A": 4, "B": 4}, "6:6", None), ("cscl", {"A": 1, "B": 1}, "8:8", None),
])
def test_celdas_unidad(red, z, coordinacion, empaquetamiento):
    celda = q.celda_unidad(red)
    assert celda.z == z and celda.coordinacion == coordinacion
    if empaquetamiento is None:
        assert celda.empaquetamiento is None
    else:
        assert 100 * celda.empaquetamiento == pytest.approx(empaquetamiento, abs=0.1)


def test_densidades_de_tabla():
    assert q.densidad(q.celda_unidad("fcc"), 361.5, 63.55) == pytest.approx(8.93, abs=0.01)
    assert q.densidad(q.celda_unidad("nacl"), 564, 58.44) == pytest.approx(2.16, abs=0.01)


def test_multiplete_n_mas_uno():
    lineas = q.multiplete(1.2, 2, 7, 400)
    assert [round(i, 3) for _, i in lineas] == [0.25, 0.5, 0.25]
    assert lineas[1][0] == pytest.approx(1.2) and lineas[2][0] - lineas[1][0] == pytest.approx(7 / 400)


# --- Fórmulas ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("texto, partes", [
    ("H2SO4", [("H", "n"), ("2", "sub"), ("SO", "n"), ("4", "sub")]),
    ("SO4^2-", [("SO", "n"), ("4", "sub"), ("2−", "sup")]),
    ("[Cu(NH3)4]^2+", [("[Cu(NH", "n"), ("3", "sub"), (")", "n"), ("4", "sub"), ("]", "n"), ("2+", "sup")]),
    ("2 H2O", [("2 H", "n"), ("2", "sub"), ("O", "n")]),
    ("pK_a1 = 4", [("pK", "n"), ("a1", "sub"), (" = 4", "n")]),
    ("g/cm³", [("g/cm³", "n")]),
])
def test_formulas(texto, partes):
    assert partes_formula(texto) == partes


# --- SVG -------------------------------------------------------------------------------------------------

def test_los_tipos_nuevos_estan_registrados():
    assert {"molecule", "reaction", "vsepr", "orbitals", "energy_profile", "titration", "speciation", "kinetics",
            "phase_diagram", "heating_curve", "spectrum", "galvanic_cell", "unit_cell"} <= set(TIPOS)


@pytest.mark.parametrize("bloque", EJEMPLOS, ids=[b["id"] for b in EJEMPLOS])
@pytest.mark.parametrize("tinta", [True, False])
def test_cada_ejemplo_es_un_svg_valido(bloque, tinta):
    svg = renderizar(bloque, tinta=tinta)
    raiz = ET.fromstring(svg)
    assert raiz.tag.endswith("svg") and float(raiz.get("width")) > 80 and float(raiz.get("height")) > 40
    assert not re.search(r"(?<![a-z])(nan|inf)(?![a-z])", svg.lower())


def _texto(svg: str) -> str:
    return " ".join("".join(t.itertext()) for t in ET.fromstring(svg).iter() if t.tag.endswith("text"))


def _plano(svg: str) -> str:
    """El texto sin espacios: los subíndices separan el texto en tspans y los espacios pasan a dx."""
    return "".join(_texto(svg).split()).replace(chr(160), "")


def _ejemplo(id_: str) -> dict:
    return next(b for b in EJEMPLOS if b["id"] == id_)


def test_la_titulacion_rotula_los_valores_calculados():
    texto = _plano(renderizar(_ejemplo("titulacion-acetico")))
    assert "pH=8,73" in texto and "pH=pKa=4,76" in texto and "pHinicial=2,88" in texto
    blanco = _texto(renderizar(_ejemplo("titulacion-amoniaco")))
    assert "5,28" not in blanco and "9,25" not in blanco


def test_orden_de_enlace_y_magnetismo_en_el_dibujo():
    texto = _plano(renderizar(_ejemplo("om-oxigeno")))
    assert "Ordendeenlace=2" in texto and "paramagnética" in texto
    assert "Ordendeenlace=3" not in _plano(renderizar(_ejemplo("om-nitrogeno")))


def test_trepev_por_pares_y_en_blanco():
    texto = _texto(renderizar(_ejemplo("trepev-amoniaco")))
    assert "piramidal trigonal" in texto and "107" in texto
    blanco = _texto(renderizar(_ejemplo("trepev-xef4-blanco")))
    assert "cuadrada plana" not in blanco and "sp³d²" not in blanco


def test_pila_en_blanco_no_revela_nada():
    texto = _texto(renderizar(_ejemplo("pila-blanco")))
    assert "Ánodo" not in texto and "0,46" not in texto and "→" not in texto
    completa = _plano(renderizar(_ejemplo("pila-daniell")))
    assert "Ánodo(−)" in completa and "E°=1,10V" in completa and "1,159V" in completa


def test_celda_unidad_y_densidad():
    texto = _plano(renderizar(_ejemplo("celda-fcc")))
    assert "8×1/8+6×1/2=4" in texto and "74%" in texto and "8,94" in texto
    assert "68" not in _texto(renderizar(_ejemplo("celda-bcc-blanco")))


def test_fases_y_eutectico():
    texto = _texto(renderizar(_ejemplo("fases-agua")))
    assert "Teb" in texto and "373,1" in texto and "Punto triple" in texto
    assert "Tsub" in _texto(renderizar(_ejemplo("fases-co2-log")))
    assert "Sólido" not in _texto(renderizar(_ejemplo("fases-blanco")))


def test_molecula_con_anillos_fusionados_comparte_atomos():
    from generador_examenes.diagramas_quimica import _Molecula

    m = _Molecula(_ejemplo("naftaleno-kekule"))
    assert len(m.atomos) == 10 and len(m.enlaces) == 11
    assert sum(1 for e in m.enlaces if e["order"] == 2) == 5


@pytest.mark.parametrize("bloque, mensaje", [
    ({"type": "molecule"}, "faltan atoms"),
    ({"type": "molecule", "atoms": [{"id": "a", "el": "C"}, {"id": "b", "from": "z"}]}, "no hay un átomo"),
    ({"type": "molecule", "atoms": [{"el": "C"}], "bonds": [["a0", "a0", 4]]}, "order"),
    ({"type": "reaction", "steps": [{"arrow": "~>"}]}, "arrow"),
    ({"type": "vsepr", "ligands": ["F"] * 7}, "geometría conocida"),
    ({"type": "vsepr", "geometry": "tetrahedral", "ligands": ["H"] * 3}, "lleva 4"),
    ({"type": "orbitals", "element": "Xx"}, "desconocido"),
    ({"type": "orbitals", "kind": "molecular", "atoms": ["Na", "Na"]}, "dos primeros períodos"),
    ({"type": "titration", "analyte": {"kind": "weak_acid", "conc": 0.1}}, "pKa"),
    ({"type": "titration", "analyte": {"kind": "sal"}}, "analyte.kind"),
    ({"type": "speciation", "pKa": [2, 7], "species": ["A", "B"]}, "3 especies"),
    ({"type": "kinetics", "order": 3}, "orden 3"),
    ({"type": "phase_diagram", "substance": "mercurio"}, "sustancia"),
    ({"type": "phase_diagram", "triple": [300, 1], "critical": [200, 50]}, "crítico"),
    ({"type": "phase_diagram", "kind": "eutectic", "meltingA": 300}, "eutéctico"),
    ({"type": "heating_curve", "from": 50, "to": 10}, "from < to"),
    ({"type": "spectrum", "kind": "raman", "peaks": [{"at": 1}]}, "kind"),
    ({"type": "spectrum", "kind": "nmr", "signals": [{"shift": 1, "multiplicity": "x"}]}, "multiplicidad"),
    ({"type": "galvanic_cell", "halfCells": [{"couple": "Zn", "E0": 1}, {"couple": "Cu^2+/Cu", "E0": 0.34}]},
     "oxidada/reducida"),
    ({"type": "unit_cell", "lattice": "hcp"}, "red"),
])
def test_errores_claros(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=mensaje):
        renderizar(bloque)
