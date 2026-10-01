"""Visor de categorías: plantilla Jinja en lugar de un f-string de 526 líneas (N-ALUCARD-03)."""

from pathlib import Path

from generador_examenes.config.category_tree_viewer import CategoryNode, generate_html_content

GOLDEN = Path(__file__).parent / "caracterizacion" / "arbol_manual.html.golden"


def _arbol() -> CategoryNode:
    raiz = CategoryNode("Raíz", "")
    hijo = raiz.add_child("Punteros", "Punteros")
    hijo.add_question("multichoice")
    hijo.add_question("truefalse")
    nieto = hijo.add_child("Aritmética", "Punteros/Aritmética")
    nieto.add_question("multichoice")
    raiz.count = 3
    return raiz


def test_misma_pagina_que_antes_del_refactor():
    # arbol_manual.html.golden es la salida del f-string original con este mismo árbol.
    assert generate_html_content(_arbol(), [{"name": "a.gift", "count": 3}], 3) == GOLDEN.read_text(encoding="utf-8")


def test_los_nombres_se_escapan():
    raiz = _arbol()
    raiz.add_child("</script><b>x</b>", "</script><b>x</b>").add_question("multichoice")
    html = generate_html_content(raiz, [{"name": "<b>banco</b>.gift", "count": 1}], 1)
    assert "&lt;b&gt;banco&lt;/b&gt;.gift" in html and "<b>banco</b>" not in html
    # Dentro del <script>, «</» se escribe «<\/» para no cerrarlo antes de tiempo.
    assert "<\\/script><b>x<\\/b>" in html and html.count("</script>") == 1
