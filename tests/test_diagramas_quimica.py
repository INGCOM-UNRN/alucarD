"""Diagramas de química: validación de los SVG generados por `dibu`."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from generador_examenes.diagramas import TIPOS, ErrorDiagrama, leer_bloques, renderizar

EJEMPLOS = leer_bloques((Path(__file__).parent / "datos" / "diagramas_quimica.yaml").read_text(encoding="utf-8"))


# --- SVG -------------------------------------------------------------------------------------------------

def test_los_tipos_nuevos_estan_registrados():
    assert {"molecule", "reaction", "vsepr", "orbitals", "energy_profile", "titration", "speciation", "kinetics",
            "phase_diagram", "heating_curve", "spectrum", "galvanic_cell", "unit_cell", "newman", "chair", "fischer",
            "crystal_field", "complex", "latimer", "frost", "born_haber"} <= set(TIPOS)


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


# --- Orgánica -----------------------------------------------------------------------------------------

def test_glucosa_por_centro():
    texto = _plano(renderizar(_ejemplo("fischer-glucosa")))
    assert texto.count("(R)") == 3 and texto.count("(S)") == 1 and "Serie=D" in texto


def test_silla_estabilidad_y_cis_trans():
    texto = _plano(renderizar(_ejemplo("silla-metil")))
    assert "laderecha,por7,3kJ/mol" in texto


# --- Inorgánica ---------------------------------------------------------------------------------------

def test_serie_espectroquimica():
    texto = _plano(renderizar(_ejemplo("campo-co-nh3")))
    assert "bajo" in texto and "Desapareados:0" in texto and "−2,4" in texto


def test_born_haber():
    assert "−787" in _texto(renderizar(_ejemplo("born-haber-nacl"))).replace("-", "−")
    assert "689" not in _texto(renderizar(_ejemplo("born-haber-blanco")))


def test_complejo_estado_de_oxidacion_y_formula():
    texto = _plano(renderizar(_ejemplo("complejo-trans")))
    assert "Co(III)" in texto and "d6" in texto and "trans" in texto
    assert "fac" not in _texto(renderizar(_ejemplo("complejo-fac-blanco")))


@pytest.mark.parametrize("bloque, mensaje", [
    ({"type": "newman", "front": ["H"], "back": ["H", "H", "H"]}, "tres sustituyentes"),
    ({"type": "chair", "substituents": [{"position": 7, "group": "CH3"}]}, "de 1 a 6"),
    ({"type": "fischer", "centers": []}, "centers"),
    ({"type": "fischer", "top": "tBu", "bottom": "Ph", "centers": [{"left": "H", "right": "OH"}]}, "empatan"),
    ({"type": "crystal_field", "geometry": "octahedral"}, "electrons"),
    ({"type": "crystal_field", "metal": "Na", "oxidation": 1}, "transición"),
    ({"type": "crystal_field", "electrons": 5, "ligand": "agua"}, "serie espectroquímica"),
    ({"type": "complex", "ligands": ["Cl"] * 5}, "6 sitios"),
    ({"type": "latimer", "species": ["A", "B"], "oxidation": [0, 2], "potentials": [1]}, "bajar"),
    ({"type": "born_haber", "steps": []}, "faltan steps"),
])
def test_errores_de_organica_e_inorganica(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=mensaje):
        renderizar(bloque)
