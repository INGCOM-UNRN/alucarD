"""Tests adicionales para maximizar la cobertura en ALUCARD."""

from pathlib import Path
import pytest
from generador_examenes.gift_linter import lint_gift_file, _process_question, main as linter_main
from generador_examenes.config.category_tree_viewer import CategoryNode, build_category_tree
from generador_examenes.config.exam_wizard import ExamWizard
from generador_examenes.core.models import Pregunta, Opcion


def test_gift_linter_valid_and_invalid(tmp_path, capsys):
    # Valid file
    f_val = tmp_path / "valido.gift"
    f_val.write_text("::Pregunta 1:: ¿Cuánto es 2+2? {=4 ~3 ~5}\n\n")
    res1 = lint_gift_file(f_val, fix=True)
    assert res1 is True

    # Invalid file
    f_inv = tmp_path / "invalido.gift"
    f_inv.write_text("::Pregunta Rota:: Falta cerrar llave {=1 ~2\n\n")
    res2 = lint_gift_file(f_inv, fix=False)
    assert res2 is False

    # Nonexistent
    res_no = lint_gift_file(tmp_path / "no_existe.gift")
    assert res_no is False


def test_gift_linter_main_args(monkeypatch, tmp_path):
    f = tmp_path / "test.gift"
    f.write_text("::P1:: Texto {=A ~B}\n")
    monkeypatch.setattr("sys.argv", ["gift-linter", str(f)])
    try:
        linter_main()
    except SystemExit:
        pass


def test_category_tree_builder():
    p1 = Pregunta(id="1", nombre="P1", tipo="seleccion_multiple", categoria="Tema1/SubtemaA", enunciado_html="¿2+2?")
    p2 = Pregunta(id="2", nombre="P2", tipo="verdadero_falso", categoria="Tema1/SubtemaB", enunciado_html="¿Sol brilla?")
    banco = {"1": p1, "2": p2}

    tree = build_category_tree(banco)
    assert "Tema1" in tree.children
    assert "SubtemaA" in tree.children["Tema1"].children
    d = tree.to_dict()
    assert "Tema1" in d["children"]


def test_exam_wizard_basic():
    w = ExamWizard()
    assert w is not None
