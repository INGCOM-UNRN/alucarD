"""Pruebas de los diagramas de estructuras (formato de bloques de statics)."""

import sys
import xml.etree.ElementTree as ET

import pytest
import yaml

from generador_examenes.core.markdown_utils import markdown_to_html
from generador_examenes.diagramas import (
    PALETAS,
    ErrorDiagrama,
    construir_arbol,
    leer_bloques,
    renderizar,
)
from generador_examenes.generators.typst_markup import html_a_typst

SVG = "{http://www.w3.org/2000/svg}"

BLOQUES = [
    {"type": "array", "values": [3, 1, 4], "pointers": "p:0, q:2", "showAddresses": True, "showOffsets": True},
    {"type": "linked_list", "variant": "singly", "values": [10, 20, 30]},
    {"type": "linked_list", "variant": "doubly", "values": ["a", "b"]},
    {"type": "linked_list", "variant": "circular", "values": [1, 2, 3]},
    {"type": "linked_list", "variant": "circular_doubly", "values": [1, 2, 3]},
    {"type": "stack", "values": [5, 9], "capacity": 4},
    {"type": "stack", "layout": "vertical_multi", "values": [1], "traceLabels": ["Inicio", "push(2)", "pop()"]},
    {"type": "queue", "variant": "linear", "capacity": 6, "frontIndex": 1, "rearIndex": 3, "values": ["", "a", "b", "c"]},
    {"type": "queue", "variant": "circular", "capacity": 8, "frontIndex": 5, "rearIndex": 1},
    {"type": "tree", "variant": "bst", "insert": [8, 3, 10, 1, 6]},
    {"type": "tree", "variant": "avl", "insert": [1, 2, 3, 4, 5]},
    {"type": "tree", "variant": "heap", "values": [90, 70, 80, 30]},
    {"type": "tree", "nodeStyle": "struct", "values": ["A", "B", "C"]},
    {"type": "tree", "root": {"value": "+", "left": "x", "right": {"value": "*", "left": 2, "right": "y"}}},
]


@pytest.mark.parametrize("bloque", BLOQUES, ids=lambda b: f"{b['type']}-{b.get('variant', b.get('nodeStyle', ''))}")
def test_cada_estructura_es_un_svg_valido(bloque):
    svg = renderizar(bloque)
    raiz = ET.fromstring(svg)
    assert raiz.tag == f"{SVG}svg"
    assert int(raiz.get("width")) > 50 and int(raiz.get("height")) > 50
    for valor in bloque.get("values") or []:
        if valor != "":
            assert f">{valor}<" in svg


MATRICES = [
    {"type": "matrix", "values": [[1, 2, 3], [4, 5, 6]]},
    {"type": "matrix", "values": [1, 2, 3, 4, 5, 6], "cols": 3, "showAddresses": True, "showLinear": True},
    {"type": "matrix", "variant": "dynamic", "values": [[1, 2, 3], [4], None, [7, 8]]},
    {"type": "matrix", "variant": "dynamic", "values": [[1, 2], [3, 4]], "showAddresses": True},
]


@pytest.mark.parametrize("bloque", MATRICES, ids=lambda b: f"{b.get('variant', 'static')}")
def test_cada_matriz_es_un_svg_valido(bloque):
    svg = renderizar(bloque)
    raiz = ET.fromstring(svg)
    assert raiz.tag == f"{SVG}svg" and int(raiz.get("width")) > 100
    for fila in bloque["values"]:
        for valor in (fila if isinstance(fila, list) else [fila]) if fila is not None else []:
            assert f">{valor}<" in svg


def test_matriz_estatica_direcciones_row_major_y_vista_lineal():
    svg = renderizar({"type": "matrix", "values": [[1, 2, 3], [4, 5, 6]], "baseAddr": "0x1000",
                      "typeSize": 4, "showAddresses": True, "showLinear": True})
    assert ">int m[2][3] | Base: 0x1000 | sizeof: 4B<" in svg
    assert ">0x1010<" in svg  # m[1][1] = base + (1*3 + 1) * 4
    assert ">[1][2]<" in svg and "fila por fila" in svg
    sin = renderizar({"type": "matrix", "values": [[1, 2]]})
    assert "0x1000" not in sin and "fila por fila" not in sin


def test_matriz_resaltado_y_en_blanco():
    bloque = {"type": "matrix", "values": [[1, 2], [3, 4]]}
    gris = PALETAS[True]["fillHighlight"]
    assert gris not in renderizar(bloque)
    assert renderizar({**bloque, "highlight": "1,0"}).count(gris) == 1
    assert renderizar({**bloque, "highlight": [[0, 0], [1, 1]]}).count(gris) == 2
    assert renderizar({**bloque, "highlightRows": [0]}).count(gris) == 2
    assert renderizar({**bloque, "highlightCols": [1], "showLinear": True}).count(gris) == 4
    svg = renderizar({**bloque, "blankValues": True})
    assert ">3<" not in svg and "stroke-dasharray" in svg


def test_matriz_dinamica_filas_de_largo_propio_y_null():
    svg = renderizar({"type": "matrix", "variant": "dynamic", "name": "t", "values": [[1, 2, 3], None, [4]],
                      "showAddresses": True, "baseAddr": "0x2000", "rowAddresses": ["0x3000", "", "0x5000"]})
    assert ">int **t<" in svg and ">t[1]<" in svg and ">NULL<" in svg
    assert ">0x3000<" in svg and ">0x5000<" in svg
    # Cada fila es un bloque propio: el borde grueso abarca su largo (3 y 1 celdas).
    assert 'width="168" height="40" fill="none"' in svg and 'width="56" height="40" fill="none"' in svg


def test_matriz_errores_claros():
    with pytest.raises(ErrorDiagrama, match="lista de filas"):
        renderizar({"type": "matrix", "values": "1 2 3"})
    with pytest.raises(ErrorDiagrama, match="highlight"):
        renderizar({"type": "matrix", "values": [[1]], "highlight": "a,b"})


def test_la_paleta_de_tinta_es_negra_y_la_de_color_no():
    bloque = {"type": "linked_list", "values": [1, 2]}
    assert "#1d4ed8" not in renderizar(bloque) and "#1d4ed8" in renderizar(bloque, tinta=False)


def test_valores_en_blanco_para_completar():
    svg = renderizar({"type": "array", "values": [41, 42], "blankValues": True})
    assert ">41<" not in svg and "stroke-dasharray" in svg


def test_direcciones_hexadecimales_desde_yaml():
    bloque = yaml.safe_load("type: linked_list\naddresses: [0x3B20, 0x7E10]\nvalues: [1, 2]")
    svg = renderizar(bloque)
    assert "0x3B20" in svg and "15136" not in svg


def _en_orden(nodo):
    return [] if nodo is None else [*_en_orden(nodo.izq), nodo.valor, *_en_orden(nodo.der)]


def test_abb_por_inserciones():
    raiz = construir_arbol({"type": "tree", "variant": "bst", "insert": [50, 30, 70, 20, 40, 30]})
    assert raiz.valor == "50" and _en_orden(raiz) == ["20", "30", "40", "50", "70"]


def test_avl_rebalancea():
    raiz = construir_arbol({"type": "tree", "variant": "avl", "insert": [10, 20, 30, 40, 50, 25]})
    assert raiz.valor == "30" and raiz.altura == 3
    assert _en_orden(raiz) == ["10", "20", "25", "30", "40", "50"]
    svg = renderizar({"type": "tree", "variant": "avl", "insert": [10, 20, 30, 40, 50, 25]})
    assert ">-1<" in svg  # factor de balance del 40


def test_arbol_por_niveles_con_huecos():
    raiz = construir_arbol({"type": "tree", "values": ["A", "B", "C", "", "D"]})
    assert raiz.izq.izq is None and raiz.izq.der.valor == "D"


def test_errores_claros():
    with pytest.raises(ErrorDiagrama):
        renderizar({"type": "grafo"})
    with pytest.raises(ErrorDiagrama):
        renderizar({"type": "tree", "values": []})
    with pytest.raises(ErrorDiagrama):
        leer_bloques("type: [sin cerrar")


def test_documento_de_statics():
    doc = {"version": "2.4", "blocks": [{"type": "markdown_text"}, {"type": "stack", "values": [1]}]}
    assert [b["type"] for b in leer_bloques(yaml.safe_dump(doc))] == ["markdown_text", "stack"]


MARKDOWN = """Seguí los punteros:

```estructura
type: linked_list
values: [10, 20, 30]
```

¿Qué vale `cabeza->sig->dato`?"""


@pytest.mark.parametrize("saltos", [True, False])
def test_markdown_con_bloque_estructura(saltos):
    html = markdown_to_html(MARKDOWN, saltos_de_linea=saltos)
    assert html.count("<svg") == 1 and "estructura" in html
    assert "<p><div" not in html and "type: linked_list" not in html
    assert "<code>cabeza-&gt;sig-&gt;dato</code>" in html


def test_bloque_invalido_queda_como_aviso():
    html = markdown_to_html("```estructura\ntype: grafo\n```")
    assert "Diagrama inválido" in html and "<svg" not in html


def test_typst_recibe_el_svg_como_imagen():
    typst = html_a_typst(markdown_to_html(MARKDOWN))
    assert "#layout(disponible =>" in typst and 'format: "svg"' in typst
    assert "<svg" not in typst.replace('"<svg', "")  # sólo dentro de la cadena de bytes


def test_typst_compila_los_diagramas(tmp_path):
    pytest.importorskip("typst")
    from generador_examenes.generators.pdf_renderer import compilar_typst_a_pdf

    cuerpo = "\n\n".join(html_a_typst(f'<div class="estructura">{renderizar(b)}</div>') for b in BLOQUES + MATRICES)
    assert compilar_typst_a_pdf(f"#set page(width: 12cm, height: auto)\n{cuerpo}\n", tmp_path / "d.pdf").is_file()


def test_pregunta_gift_con_diagrama(tmp_path):
    from generador_examenes.parsers.gift_parser import GiftParser

    banco = tmp_path / "b.gift"
    banco.write_text("::abb:: [markdown]Recorré en preorden:\n```estructura\ntype: tree\nvariant: bst\n"
                     "insert: [2, 1, 3]\n```\n{\n=2 1 3\n~1 2 3\n}\n", encoding="utf-8")
    pregunta = next(iter(GiftParser().parse(banco).values()))
    assert "<svg" in pregunta.enunciado_html and len(pregunta.opciones) == 2


def test_consigna_deckard_con_diagrama():
    from generador_examenes.core.consignas import presentar_consigna
    from generador_examenes.core.models import PresentacionConsigna, Pregunta

    consigna = Pregunta(id="deckard:pila", tipo="consigna_practica", nombre="Pila", categoria="consignas/pilas",
                        enunciado_html="", metadata={"tema": "pilas", "enunciado_md": "Implementá `push`.\n\n"
                                                     "```estructura\ntype: stack\nvalues: [1, 2]\n```\n"})
    html = presentar_consigna(consigna, PresentacionConsigna()).enunciado_html
    assert "<svg" in html


def test_comando_diagrama(tmp_path, monkeypatch, capsys):
    from generador_examenes.__main__ import main

    entrada = tmp_path / "doc.json"
    entrada.write_text('{"blocks": [{"type": "markdown_text"}, {"id": "lista", "type": "linked_list", '
                       '"values": [1, 2]}, {"type": "tree", "insert": [2, 1]}]}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alucard", "diagrama", str(entrada), "-o", str(tmp_path / "out")])
    assert main() == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["doc_3.svg", "lista.svg"]
    assert "no es una estructura" in capsys.readouterr().err
