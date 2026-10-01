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
    # arbol_manual.html.golden es la salida del f-string original con este mismo árbol, con la
    # línea del botón Copiar ya corregida (N-ALUCARD-05).
    assert generate_html_content(_arbol(), [{"name": "a.gift", "count": 3}], 3) == GOLDEN.read_text(encoding="utf-8")


def test_los_nombres_se_escapan():
    raiz = _arbol()
    raiz.add_child("</script><b>x</b>", "</script><b>x</b>").add_question("multichoice")
    html = generate_html_content(raiz, [{"name": "<b>banco</b>.gift", "count": 1}], 1)
    assert "&lt;b&gt;banco&lt;/b&gt;.gift" in html and "<b>banco</b>" not in html
    # Dentro del <script>, «</» se escribe «<\/» para no cerrarlo antes de tiempo.
    assert "<\\/script><b>x<\\/b>" in html and html.count("</script>") == 1


def test_el_script_de_la_pagina_compila(tmp_path):
    """N-ALUCARD-05: los escapes del f-string dejaban «copyCategory(event, '' + …» y el script entero
    no compilaba: el árbol interactivo no se mostraba."""
    import re
    import shutil
    import subprocess

    import pytest

    html = generate_html_content(_arbol(), [{"name": "a.gift", "count": 3}], 3)
    assert "copyCategory(event, \\'' + node.full_path" in html
    node = shutil.which("node")
    if node is None:
        pytest.skip("hace falta node para compilar el JavaScript")
    script = tmp_path / "visor.js"
    script.write_text(re.findall(r"<script>(.*?)</script>", html, re.S)[-1], encoding="utf-8")
    res = subprocess.run([node, "--check", str(script)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
