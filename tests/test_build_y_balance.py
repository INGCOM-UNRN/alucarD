"""Ola 14 (Decisión 4, QoL #517, #546, #20, #7): `alucard build -i` desde el Moodle XML de idkfa, con las
claves balanceadas, y `alucard balance-check`."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

from generador_examenes.__main__ import main
from generador_examenes.core.balance import auditar_balance
from generador_examenes.core.logic import asignar_posiciones_correctas
from generador_examenes.core.models import Opcion, Pregunta


def _pregunta(i, n=4):
    return Pregunta(id=f"p{i}", tipo="seleccion_multiple", nombre=f"P{i}", categoria="c", enunciado_html="?",
                    opciones=[Opcion(texto_html=str(k), es_correcta=(k == 0)) for k in range(n)])


def _alucard(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    captura = capsys.readouterr()
    return codigo or 0, captura.out + captura.err


def _banco(tmp_path: Path, n: int = 12) -> Path:
    """Un Moodle XML como el de idkfa (format="markdown", código con la convención de voight) con la
    correcta siempre primera."""
    preguntas = []
    for i in range(n):
        opciones = "".join(
            f'<answer fraction="{100 if k == 0 else 0}" format="markdown"><text>{v}</text></answer>'
            for k, v in enumerate((i, i + 1, i + 2, i + 3)))
        preguntas.append(
            f'<question type="multichoice"><name><text>Suma {i}</text></name>'
            f'<questiontext format="markdown"><text><![CDATA[¿Qué imprime?\n```c\nint a = {i};↵\n'
            f'printf（"%d\\n", a）；↵\n```\n]]></text></questiontext>'
            f"<single>true</single>{opciones}</question>")
    ruta = tmp_path / "idkfa_output.xml"
    ruta.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<quiz>' + "".join(preguntas) + "</quiz>\n",
                    encoding="utf-8")
    return ruta


def test_auditar_balance_umbral_efectivo_con_pocas_opciones():
    examen = {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i, n=3) for i in range(9)]}]}
    asignar_posiciones_correctas(examen, random.Random(1))
    reporte = auditar_balance([examen], umbral=0.30)
    assert reporte["frecuencias"] == {"A": 0.3333, "B": 0.3333, "C": 0.3333}
    # Con 3 opciones no se puede bajar del 33 %: el umbral efectivo lo dice y no falla.
    assert reporte["umbral_efectivo"] == 0.3833 and reporte["ok"]
    sesgado = {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i) for i in range(8)]}]}
    assert not auditar_balance([sesgado])["ok"]  # todas en la A


def test_balance_check_sobre_el_xml_de_idkfa(monkeypatch, capsys, tmp_path):
    banco = _banco(tmp_path)
    codigo, salida = _alucard(monkeypatch, capsys, ["balance-check", "-i", str(banco), "-n", "4", "--json"])
    assert codigo == 0, salida
    reporte, _ = json.JSONDecoder().raw_decode(salida[salida.index("{"):])
    assert reporte["temas"] == 4 and reporte["preguntas_por_tema"] == 12
    assert max(reporte["frecuencias"].values()) <= 0.30
    assert all(sorted(t.values()) == [3, 3, 3, 3] for t in reporte["por_tema"])
    codigo, _ = _alucard(monkeypatch, capsys, ["balance-check", "-i", str(banco), "--umbral", "0.2"])
    assert codigo == 0  # con 4 opciones el mínimo es 25 %: el umbral efectivo sube a 30 %


@pytest.mark.skipif(pytest.importorskip("typst", reason="hace falta el módulo typst") is None, reason="typst")
def test_build_genera_examen_y_clave_en_pdf_sin_yaml(monkeypatch, capsys, tmp_path):
    from pypdf import PdfReader

    salida_dir = tmp_path / "salida"
    codigo, salida = _alucard(monkeypatch, capsys, ["build", "-i", str(_banco(tmp_path, n=6)), "-n", "2",
                                                    "-o", str(salida_dir), "--titulo", "Parcial 1"])
    assert codigo == 0, salida
    assert "Ninguna letra supera 30%" in salida
    examen = "".join(p.extract_text() for p in PdfReader(salida_dir / "examen_tema_01.pdf").pages)
    clave = "".join(p.extract_text() for p in PdfReader(salida_dir / "clave_tema_01.pdf").pages)
    assert "Parcial 1" in examen and "int a = 0;" in examen and 'printf("%d\\n", a);' in examen
    assert "✓" not in examen and "</" not in examen and "None" not in examen  # el examen no muestra la clave
    assert "A)" in examen and "D)" in examen
    assert "✓" in clave and "Ver criterio" not in clave
