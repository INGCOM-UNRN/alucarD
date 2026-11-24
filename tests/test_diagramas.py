"""Pruebas de los diagramas de estructuras (formato de bloques de statics)."""

import re
import sys
import xml.etree.ElementTree as ET

import pytest
import yaml

from generador_examenes.core.markdown_utils import markdown_to_html
from generador_examenes.diagramas import (
    PALETAS,
    ErrorDiagrama,
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
    {"type": "matrix", "variant": "jagged", "values": [[1, 2, 3], [4], None, [7, 8]]},
    {"type": "matrix", "variant": "jagged", "name": "palabras", "values": [["h", "o", "l", "a"], ["s", "i"]],
     "sentinel": "'\\0'", "showAddresses": True},
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


def test_matriz_dentada_con_arreglo_de_largos():
    svg = renderizar({"type": "matrix", "variant": "jagged", "values": [[1, 2, 3], [4], None, [7, 8]]})
    assert ">int **m | size_t largos[4]<" in svg and ">largos<" in svg
    for largo in (3, 1, 0, 2):
        assert f">{largo}<" in svg
    # `lengths` fija los largos que se muestran; `blankLengths` los deja para completar.
    svg = renderizar({"type": "matrix", "variant": "jagged", "values": [[1]], "lengths": [5],
                      "lengthsName": "tam", "blankLengths": False})
    assert ">tam<" in svg and ">5<" in svg
    svg = renderizar({"type": "matrix", "variant": "jagged", "values": [[1, 2, 3]], "blankLengths": True})
    assert ">3<" in svg  # el dato de la fila sigue; el largo no
    assert svg.count("stroke-dasharray") == 1
    # La variante dinámica no dibuja los largos.
    assert ">largos<" not in renderizar({"type": "matrix", "variant": "dynamic", "values": [[1]]})


def test_matriz_dentada_con_centinela():
    svg = renderizar({"type": "matrix", "variant": "jagged", "values": [[3, 1], [2]], "sentinel": -1})
    assert "centinela: -1" in svg and svg.count(">-1<") == 2
    assert ">largos<" not in svg  # con centinela, los largos sólo si se piden
    svg = renderizar({"type": "matrix", "variant": "jagged", "values": [[3]], "sentinel": -1, "showLengths": True})
    assert ">largos<" in svg


def test_matriz_errores_claros():
    with pytest.raises(ErrorDiagrama, match="variante de matriz"):
        renderizar({"type": "matrix", "variant": "triangular", "values": [[1]]})
    with pytest.raises(ErrorDiagrama, match="lista de filas"):
        renderizar({"type": "matrix", "values": "1 2 3"})
    with pytest.raises(ErrorDiagrama, match="highlight"):
        renderizar({"type": "matrix", "values": [[1]], "highlight": "a,b"})


@pytest.mark.parametrize("bloque, mensaje", [
    ({"values": [[1]] * 11}, "11 filas; el máximo es 10"),
    ({"values": [[1, 2], list(range(11))]}, "fila 1 de la matriz tiene 11 columnas"),
    ({"values": list(range(30)), "cols": 2}, "15 filas"),
    ({"values": [[1]], "rows": 11}, "'rows' de una matriz tiene que estar entre 1 y 10: 11"),
    ({"values": [[1]], "cols": 12}, "'cols' de una matriz tiene que estar entre 1 y 10: 12"),
    ({"values": [[1]], "cols": 0}, "'cols'"),
    ({"values": [[1]], "rows": "muchas"}, "tiene que ser un entero"),
    ({"variant": "dynamic", "values": [[1]] * 11}, "11 filas"),
    ({"variant": "dynamic", "values": [[1]], "cols": 11}, "'cols'"),
])
def test_matriz_de_mas_de_10_es_error(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=re.escape(mensaje)):
        renderizar({"type": "matrix", **bloque})


def test_matriz_de_10_por_10_entra():
    svg = renderizar({"type": "matrix", "values": [list(range(10))] * 10})
    assert svg.count(">9<") == 10


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


def test_avl_rebalancea():
    svg = renderizar({"type": "tree", "variant": "avl", "insert": [10, 20, 30, 40, 50, 25]})
    assert ">-1<" in svg  # factor de balance del 40


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

    cuerpo = "\n\n".join(html_a_typst(f'<div class="estructura">{renderizar(b)}</div>') for b in BLOQUES + MATRICES + [PILA_LLAMADAS] + TEMAS)
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


@pytest.mark.parametrize("bloque", [{"type": "matrix", "rows": 1, "cols": 1}, {"type": "stack", "values": [1]},
                                    {"type": "array", "values": [1]}])
def test_el_titulo_largo_no_se_corta(bloque):
    titulo = "Completar con la transpuesta de la matriz original"
    raiz = ET.fromstring(renderizar({**bloque, "title": titulo}))
    assert int(raiz.get("width")) >= len(titulo) * 8.6


ENUNCIADO = """## Consigna

```estructura
type: stack
values: [1, 2]
```

Y después:

```estructura
- type: array
  values: [3]
- type: queue
  values: [a]
```
"""


def test_nombre_svg_es_el_contrato_con_deckard():
    from generador_examenes.diagramas import nombre_svg
    import hashlib
    cuerpo = "type: stack\nvalues: [1, 2]\n"
    esperado = hashlib.sha1(cuerpo.strip().encode()).hexdigest()[:12]
    assert nombre_svg(cuerpo) == f"estructura-{esperado}.svg"
    assert nombre_svg("  " + cuerpo + "\n\n") == nombre_svg(cuerpo)


def test_sincronizar_svgs_escribe_es_idempotente_y_borra_lo_que_sobra(tmp_path):
    from generador_examenes.diagramas import cuerpos_en_markdown, nombre_svg, sincronizar_svgs
    (tmp_path / "enunciado.md").write_text(ENUNCIADO, encoding="utf-8")
    res = sincronizar_svgs(tmp_path)
    nombres = sorted(nombre_svg(c) for c in cuerpos_en_markdown(ENUNCIADO))
    assert sorted(p.rsplit("/", 1)[1] for p in res.escritos) == nombres and not res.errores
    for nombre in nombres:
        ET.fromstring((tmp_path / "diagramas" / nombre).read_text(encoding="utf-8"))
    # El bloque con dos estructuras queda en un único SVG.
    assert (tmp_path / "diagramas" / nombre_svg(cuerpos_en_markdown(ENUNCIADO)[1])).read_text().count("<svg") == 3

    res = sincronizar_svgs(tmp_path)
    assert not res.escritos and not res.borrados

    (tmp_path / "enunciado.md").write_text("Sin diagramas.", encoding="utf-8")
    assert sincronizar_svgs(tmp_path, escribir=False).borrados  # verificar no toca nada
    assert len(list((tmp_path / "diagramas").iterdir())) == 2
    res = sincronizar_svgs(tmp_path)
    assert len(res.borrados) == 2 and not (tmp_path / "diagramas").exists()


def test_comando_diagramas_md(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from generador_examenes.__main__ import app, _ultimo_codigo_salida
    md = tmp_path / "enunciado.md"
    md.write_text(ENUNCIADO.replace("[1, 2]", "[1, 2]\ntype2: x"), encoding="utf-8")
    runner = CliRunner()
    runner.invoke(app, ["diagramas-md", str(md)])
    assert _ultimo_codigo_salida["code"] == 1  # escribió: el hook falla para que se agreguen
    runner.invoke(app, ["diagramas-md", "--verificar", str(md)])
    assert _ultimo_codigo_salida["code"] == 0
    md.write_text("```estructura\ntype: grafo\n```\n", encoding="utf-8")
    r = runner.invoke(app, ["diagramas-md", str(md)])
    assert _ultimo_codigo_salida["code"] == 1 and "grafo" in r.output


PILA_LLAMADAS = {
    "type": "call_stack", "showAddresses": True, "showTypes": True,
    "frames": [
        {"function": "main", "vars": [{"name": "a", "value": 3, "type": "int"}, {"name": "b", "value": 7, "type": "int"}]},
        {"function": "intercambiar", "returnTo": "main",
         "params": [{"name": "x", "value": "&a", "type": "int *"}, {"name": "y", "value": "&b", "type": "int *"}],
         "vars": ["aux = 3"]},
    ],
    "pointers": "1.x -> 0.a; intercambiar.y -> main.b",
}


def test_pila_de_llamadas_marcos_direcciones_y_punteros():
    svg = renderizar(PILA_LLAMADAS)
    ET.fromstring(svg)
    assert ">intercambiar(x, y)<" in svg and ">main()<" in svg and ">vuelve a main<" in svg
    assert ">int * x<" in svg and ">&amp;a<" in svg and ">3<" in svg
    # La pila crece hacia abajo: int de 4 bytes y punteros de 8.
    assert re.findall(r">(0x[0-9A-F]+)<", svg) == ["0x7FFC", "0x7FF8", "0x7FF0", "0x7FE8", "0x7FE4"]
    assert svg.count("marker-end") == 2  # una flecha por puntero


def test_pila_de_llamadas_en_el_tiempo():
    svg = renderizar({"type": "call_stack", "steps": [
        {"label": "llama a fact(2)", "frames": [{"function": "main", "vars": {"r": "?"}},
                                                {"function": "fact", "params": {"n": 2}}]},
        {"label": "fact(1) devuelve 1", "frames": [{"function": "main", "vars": {"r": "?"}},
                                                   {"function": "fact", "params": {"n": 2}},
                                                   {"function": "fact", "params": {"n": 1}, "returns": 1, "popped": True}]},
    ]})
    ET.fromstring(svg)
    assert ">llama a fact(2)<" in svg and ">fact(1) devuelve 1<" in svg
    assert ">devolvió 1<" in svg and "stroke-dasharray=\"5 3\"" in svg  # el marco que retornó, punteado
    assert svg.count(">fact(n)<") == 3


def test_pila_de_llamadas_rotulos_largos_no_se_pisan():
    rotulo = "segunda llamada, antes de c++"
    svg = renderizar({"type": "call_stack", "steps": [
        {"label": rotulo, "frames": [{"function": "f"}]},
        {"label": rotulo, "frames": [{"function": "f"}]},
    ]})
    xs = [float(x) for x in re.findall(r'<text x="([\d.]+)"[^>]*>' + re.escape(rotulo) + "<", svg)]
    x0, ancho = map(float, re.search(r'viewBox="([-\d.]+) [-\d.]+ ([\d.]+)', svg).groups())
    assert len(xs) == 2 and xs[1] - xs[0] >= len(rotulo) * 7  # la 2.ª columna no pisa el rótulo de la 1.ª
    assert x0 + ancho >= xs[1] + len(rotulo) * 7  # ni se corta el último


def test_pila_de_llamadas_en_blanco():
    svg = renderizar({**PILA_LLAMADAS, "blankValues": True, "blankAddrs": True})
    assert ">7<" not in svg and ">0x____<" in svg


@pytest.mark.parametrize("bloque, mensaje", [
    ({"frames": []}, "lista de marcos"),
    ({"frames": [{"vars": {"x": 1}}]}, "necesita 'function'"),
    ({"frames": [{"function": "main", "vars": {"x": 1}}], "pointers": "0.x -> 0.z"}, "no tiene la variable 'z'"),
    ({"frames": [{"function": "main", "vars": {"x": 1}}], "pointers": "0.x"}, "flecha"),
    ({"frames": [{"function": "f"}] * 11}, "el máximo es 10"),
    ({"steps": [{"frames": [{"function": "main"}]}] * 9}, "el máximo es 8"),
])
def test_pila_de_llamadas_errores(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=re.escape(mensaje)):
        renderizar({"type": "call_stack", **bloque})


# --- Diagramas para evaluar TADs, structs, complejidad, análisis y recursividad ----------------

FIB3 = {"call": "fib(3)", "returns": 2, "children": [
    {"call": "fib(2)", "returns": 1, "children": [{"call": "fib(1)", "returns": 1}, {"call": "fib(0)", "returns": 0}]},
    {"call": "fib(1)", "returns": 1}]}
FLUJO = [{"io": "leer n"}, "i = 0",
         {"while": "i < n", "do": [{"if": "par(i)", "then": ["s = s + i"], "else": ["s = s - i"]}, "i = i + 1"]},
         {"if": "s > 0", "else": ["s = 0"]}, {"if": "s == 0", "then": ["t = 1"]}]
TEMAS = [
    {"type": "struct", "name": "struct persona", "typedef": "persona_t", "fields": ["char c = 'A'", "int edad = 30"]},
    {"type": "struct", "variant": "opaque", "name": "struct pila", "operations": ["void f(pila_t p)"],
     "fields": ["int *datos", "size_t tope"]},
    {"type": "adt", "name": "Pila", "operations": ["pila_t crear(void)"], "client": ["crear();"], "invariant": "tope >= 0",
     "representations": ["Arreglo", {"name": "Lista", "fields": ["nodo_t *cabeza"]}]},
    {"type": "complexity"},
    {"type": "complexity", "variant": "classes", "items": {"O(n)": ["búsqueda lineal"]}},
    {"type": "flowchart", "steps": FLUJO},
    {"type": "cost_table", "lines": [["int s = 0;", "c1", 1]], "total": "c1"},
    {"type": "trace_table", "columns": ["i", "s"], "rows": [[0, 1]]},
    {"type": "trace_table", "capacity": 4, "operations": ["push(1)"]},
    {"type": "call_tree", "root": FIB3, "showOrder": True, "levelCosts": ["1", "2", "2"], "total": "2^n"},
    {"type": "matrix", "variant": "flat", "values": [[1, 2], [3, 4]], "showLogical": True, "showAddresses": True},
    {"type": "linked_list", "values": [1, 2], "pointers": "actual:1"},
    {"type": "linked_list", "values": []},
]


@pytest.mark.parametrize("bloque", TEMAS, ids=lambda b: f"{b['type']}-{b.get('variant', '')}")
def test_cada_tema_es_un_svg_valido(bloque):
    raiz = ET.fromstring(renderizar(bloque))
    assert int(raiz.get("width")) > 50 and int(raiz.get("height")) > 50


def _textos(svg: str) -> list:
    return [t.text for t in ET.fromstring(svg).iter(f"{SVG}text")]


def test_struct_dibuja_offsets_relleno_y_sizeof():
    textos = _textos(renderizar({"type": "struct", "name": "struct s", "fields": ["char a", "int b"]}))
    assert "+4" in textos and "(relleno)" in textos and "3 B" in textos
    assert any("sizeof(struct s) = 8 bytes" in t for t in textos)


def test_struct_en_blanco_para_completar():
    bloque = {"type": "struct", "name": "struct s", "fields": ["char a", "int b"], "blankOffsets": True,
              "blankSizes": True, "blankPadding": True, "blankSizeof": True}
    textos = _textos(renderizar(bloque))
    assert "+4" not in textos and "(relleno)" not in textos and "4 B" not in textos
    assert not any("8 bytes" in t for t in textos)


def test_tipo_opaco_el_cliente_no_ve_los_campos():
    bloque = {"type": "struct", "variant": "opaque", "name": "struct pila", "typedef": "pila_t", "fields": ["int *datos"]}
    assert "int *datos;" in _textos(renderizar(bloque))
    oculto = _textos(renderizar({k: v for k, v in bloque.items() if k != "fields"} | {"hidden": True}))
    assert "int *datos;" not in oculto and "typedef struct pila *pila_t;" in oculto


@pytest.mark.parametrize("bloque, mensaje", [
    ({"type": "struct"}, "fields"),
    ({"type": "struct", "fields": ["punto_t p"]}, "tamaño"),
    ({"type": "struct", "fields": ["?"]}, "no entiendo"),
    ({"type": "struct", "fields": [{"name": "x"}]}, "'type'"),
    ({"type": "struct", "variant": "otra", "fields": ["int a"]}, "variante"),
    ({"type": "struct", "fields": ["int a"] * 17}, "máximo"),
    ({"type": "adt"}, "operations"),
    ({"type": "adt", "operations": [{"kind": "x"}]}, "signature"),
    ({"type": "complexity", "curves": ["n^4"]}, "desconocido"),
    ({"type": "complexity", "curves": [{"label": "x"}]}, "points"),
    ({"type": "complexity", "curves": [{"points": [[1]]}]}, "points"),
    ({"type": "complexity", "curves": 5}, "curves"),
    ({"type": "complexity", "variant": "otra"}, "variante"),
    ({"type": "complexity", "variant": "classes", "classes": ["P"], "items": {"NP": ["SAT"]}}, "NP"),
    ({"type": "flowchart"}, "steps"),
    ({"type": "flowchart", "steps": [{"x": 1}]}, "paso 0"),
    ({"type": "flowchart", "steps": [{"while": "a"}]}, "cuerpo"),
    ({"type": "cost_table"}, "lines"),
    ({"type": "trace_table"}, "filas"),
    ({"type": "trace_table", "columns": ["a"]}, "filas"),
    ({"type": "trace_table", "columns": ["a"], "rows": [[1, 2]]}, "columnas"),
    ({"type": "call_tree"}, "root"),
    ({"type": "call_tree", "root": {"returns": 1}}, "call"),
    ({"type": "call_tree", "root": {"call": "f", "children": ["g"] * 40}}, "máximo"),
    ({"type": "matrix", "variant": "flat", "rows": 5, "cols": 5}, "máximo"),
])
def test_temas_errores_claros(bloque, mensaje):
    with pytest.raises(ErrorDiagrama, match=mensaje):
        renderizar(bloque)


@pytest.mark.parametrize("bloque", [
    {"type": "adt", "operations": [1, 2], "representations": 5},
    {"type": "call_tree", "root": {"call": "f"}, "levelCosts": 5},
    {"type": "complexity", "variant": "classes", "classes": ["P"], "items": {"P": 3}, "maxN": []},
    {"type": "stack", "values": 5},
])
def test_un_dato_de_otro_tipo_no_corta_la_generacion(bloque):
    try:
        ET.fromstring(renderizar(bloque))
    except ErrorDiagrama:
        pass  # dibujarlo o rechazarlo: lo que no puede pasar es otra excepción


def test_tad_operaciones_y_lo_que_no_aplica_no_es_para_completar():
    bloque = {"type": "adt", "name": "Pila", "operations": [{"signature": "f()", "kind": "observador", "pre": "p"},
                                                            {"signature": "g()", "post": "q", "blank": True}]}
    textos = _textos(renderizar(bloque))
    assert "f()" in textos and "g()" not in textos and "—" in textos
    assert "observador" not in _textos(renderizar(bloque | {"blankKinds": True}))


def test_curvas_con_alias_y_rotuladas_con_letras():
    assert "O(n²)" in _textos(renderizar({"type": "complexity", "curves": ["Θ(n²)"]}))
    textos = _textos(renderizar({"type": "complexity", "curves": ["n", "n^2"], "blankLabels": True}))
    assert {"A", "B"} <= set(textos) and "O(n)" not in textos


def test_curvas_sin_desbordes_con_n_grande():
    ET.fromstring(renderizar({"type": "complexity", "curves": ["2^n", "n!", "n^3"], "maxN": 10000, "maxY": 1000}))


def test_curva_no_se_sale_del_grafico():
    svg = renderizar({"type": "complexity", "curves": ["2^n"], "maxN": 20, "maxY": 100})
    ys = [float(p.split(",")[1]) for p in re.search(r'polyline points="([^"]+)"', svg)[1].split()]
    assert min(ys) >= 37  # el tope del gráfico: y0 = 38, menos el redondeo


def test_curvas_con_mediciones():
    svg = renderizar({"type": "complexity", "curves": [{"label": "medido", "points": [[2, 5], [10, 90]]}]})
    assert "medido" in _textos(svg) and svg.count("<circle") == 2


def test_clases_anidadas_de_la_mas_chica_a_la_mas_grande():
    svg = renderizar({"type": "complexity", "variant": "classes", "classes": ["P", "NP"], "items": {"P": ["ordenar"]}})
    textos = _textos(svg)
    assert textos.index("NP") < textos.index("P") and "• ordenar" in textos
    sin = _textos(renderizar({"type": "complexity", "variant": "classes", "blankClasses": True}))
    assert "O(n)" not in sin


def test_flujo_decision_y_repeticion():
    svg = renderizar({"type": "flowchart", "steps": FLUJO})
    textos = _textos(svg)
    assert {"Inicio", "Fin", "leer n", "i < n", "par(i)", "s = 0"} <= set(textos)
    assert textos.count("Sí") == 4 and textos.count("No") == 4
    assert svg.count("<polygon") == 5  # la entrada y las cuatro condiciones


def test_flujo_en_blanco_y_sin_terminales():
    bloque = {"type": "flowchart", "steps": ["a = 1", {"step": "b = 2", "blank": True}], "start": False, "end": False}
    textos = _textos(renderizar(bloque))
    assert "a = 1" in textos and "b = 2" not in textos and "Inicio" not in textos


def test_flujo_las_ramas_no_se_pisan():
    largo = "una instruccion bastante larga"
    svg = renderizar({"type": "flowchart", "steps": [{"if": "c", "then": [largo], "else": [largo]}]})
    cajas = [(float(x), float(w)) for x, w in re.findall(r'<rect x="([\d.-]+)" y="[\d.]+" width="([\d.]+)" height="34', svg)]
    (x1, w1), (x2, _) = sorted(cajas)
    assert x1 + w1 < x2 and x1 >= 0


def test_costos_y_sangria_del_codigo():
    bloque = {"type": "cost_table", "lines": [["for (;;)", "c1", "n"], ["    x++;", "c2", "n - 1"]], "total": "2n"}
    svg = renderizar(bloque)
    assert "T(n) = 2n" in _textos(svg)
    x_for = float(re.search(r'<text x="([\d.]+)"[^>]*>for \(;;\)', svg)[1])
    x_cuerpo = float(re.search(r'<text x="([\d.]+)"[^>]*>x\+\+;', svg)[1])
    assert x_cuerpo > x_for + 20
    blanco = _textos(renderizar(bloque | {"blankCosts": True, "blankTimes": True, "blankTotal": True}))
    assert "c1" not in blanco and "n - 1" not in blanco and "T(n) = 2n" not in blanco


def test_traza_de_statics():
    bloque = {"type": "trace_table", "variant": "stack", "capacity": 5, "pointerLabel": "TOPE: ___",
              "operations": ["1. push(10)", "2. pop()"]}
    textos = _textos(renderizar(bloque))
    assert {"[0]", "[4]", "Puntero TOPE", "1. push(10)"} <= set(textos) and textos.count("TOPE: ___") == 2


def test_traza_de_variables_lo_que_falta_queda_para_completar():
    bloque = {"type": "trace_table", "columns": ["i", "suma"], "rows": [[0, 7], [1, None]], "rowCount": 4}
    svg = renderizar(bloque)
    assert "7" in _textos(svg) and svg.count('stroke-dasharray="3 2"') == 5
    assert "7" not in _textos(renderizar(bloque | {"blankValues": True}))


def test_traza_con_instrucciones():
    bloque = {"type": "trace_table", "columns": ["a"], "operations": ["a = 1", "a++"], "operationHeader": "Línea"}
    assert {"Línea", "a = 1", "a++"} <= set(_textos(renderizar(bloque)))


def test_arbol_de_llamadas_orden_y_retornos():
    textos = _textos(renderizar({"type": "call_tree", "root": FIB3, "showOrder": True}))
    assert textos.count("fib(1)") == 2 and "→ 2" in textos
    assert [t for t in textos if t.isdigit()] == ["1", "2", "3", "4", "5"]


def test_arbol_de_llamadas_el_padre_queda_sobre_sus_hijos():
    svg = renderizar({"type": "call_tree", "root": {"call": "a", "children": ["b", "c"]}})
    x = {m[1]: float(m[0]) for m in re.findall(r'<text x="([\d.]+)"[^>]*>([abc])</text>', svg)}
    assert x["b"] < x["a"] < x["c"] and x["a"] == pytest.approx((x["b"] + x["c"]) / 2)


def test_arbol_de_llamadas_en_blanco_y_costos():
    bloque = {"type": "call_tree", "root": FIB3, "blankReturns": True, "levelCosts": ["n", "2n"], "total": "n^2"}
    textos = _textos(renderizar(bloque))
    assert "→ 2" not in textos and "costo del nivel" in textos and "2n" in textos and "T(n) = n^2" in textos
    assert "fib(3)" not in _textos(renderizar({"type": "call_tree", "root": FIB3, "blankCalls": True}))
    assert "n" not in _textos(renderizar(bloque | {"blankLevelCosts": True}))


def test_matriz_plana_contigua_con_su_formula():
    svg = renderizar({"type": "matrix", "variant": "flat", "values": [[1, 2, 3], [4, 5, 6]], "baseAddr": "0x1000",
                      "showAddresses": True})
    textos = _textos(svg)
    assert "[5]" in textos and "(1,2)" in textos and "0x1014" in textos
    assert any("malloc(2 * 3 * sizeof(int))" in t for t in textos) and any("m[i * 3 + j]" in t for t in textos)


def test_matriz_plana_para_preguntar_la_conversion():
    bloque = {"type": "matrix", "variant": "flat", "values": [[1, 2], [3, 4]], "showIndices": False, "showFormula": False}
    textos = _textos(renderizar(bloque))
    assert "[3]" not in textos and "(1,1)" in textos and not any("i * 2" in t for t in textos)
    assert "(1,1)" not in _textos(renderizar(bloque | {"showCoords": False}))


def test_matriz_plana_vista_logica():
    textos = _textos(renderizar({"type": "matrix", "variant": "flat", "values": [[1, 2]], "showLogical": True}))
    assert textos.count("1") == 2 and any("int m[1][2]" in t for t in textos)


def test_lista_con_cursores():
    textos = _textos(renderizar({"type": "linked_list", "values": [1, 2, 3], "pointers": "ant:0, actual:1, final:2"}))
    assert {"ant", "actual", "final"} <= set(textos)


def test_lista_vacia_llega_a_null():
    textos = _textos(renderizar({"type": "linked_list", "headLabel": "cabeza", "values": []}))
    assert "cabeza" in textos and "NULL" in textos and "dato" not in textos


def test_diagramas_nuevos_en_una_pregunta_gift(tmp_path):
    from generador_examenes.core import logic

    banco = tmp_path / "b.gift"
    banco.write_text("""::flujo:: [markdown]¿Qué imprime?
```estructura
type: flowchart
steps:
  - "max = v[0]"
  - while: i < n
    do:
      - i = i + 1
```
{
=3
~4
}

::padding:: [markdown]¿Cuánto da `sizeof`?
```estructura
type: struct
name: struct s
fields: ["char a", "int b"]
blankSizeof: true
```
{
=8
~5
}
""", encoding="utf-8")
    preguntas = list(logic.cargar_bancos([banco]).values())
    assert len(preguntas) == 2
    assert all("<svg" in p.enunciado_html and "estructura-error" not in p.enunciado_html for p in preguntas)


@pytest.mark.parametrize("plantilla", ["base_examen.html.j2", "clave_profesor.html.j2"])
def test_los_diagramas_anchos_no_se_salen_de_la_pregunta(plantilla):
    from pathlib import Path

    import generador_examenes

    raiz = Path(generador_examenes.__file__).parent.parent
    assert "svg.estructura { max-width: 100%" in (raiz / "templates" / plantilla).read_text(encoding="utf-8")


LISTA_CON_CABECERA = {"type": "linked_list", "values": [12, 25, 8], "addresses": ["@N1", "@N2", "@N3"],
                      "nodeType": "nodo_t", "zones": {"stack": "Stack: main", "heap": "Heap"},
                      "header": {"name": "mi_lista", "type": "lista_t",
                                 "fields": ["primero -> 0", "ultimo -> 2", "cant = 3"]}}
DENTADA_EN_ESTRUCTURA = {"type": "matrix", "variant": "jagged", "name": "filas", "values": [[4, 8], [9]],
                         "showAddresses": True, "baseAddr": "@F", "rowAddresses": ["@R0", "@R1"], "lengthsType": "int",
                         "lengthsAddr": "@L", "zones": True,
                         "owner": {"name": "d", "type": "dentada_t",
                                   "fields": ["n = 2", "largos -> lengths", "filas -> rows"]}}


def textos(svg):
    return re.findall(r">([^<]+)</text>", svg)


def test_la_cabecera_de_una_lista_reemplaza_a_head():
    svg = renderizar(LISTA_CON_CABECERA)
    assert "mi_lista (lista_t)" in textos(svg) and "HEAD" not in textos(svg)
    assert {"primero", "ultimo", "cant", "3", "@N1 (nodo_t)"} <= set(textos(svg))
    assert textos(svg).count("@N3") == 1  # el valor de `ultimo`: el nodo lleva `@N3 (nodo_t)`


def test_las_zonas_tienen_sus_titulos():
    assert {"Stack: main", "Heap"} <= set(textos(renderizar(LISTA_CON_CABECERA)))
    assert {"Stack", "Heap"} <= set(textos(renderizar({**LISTA_CON_CABECERA, "zones": True})))
    assert "Heap" not in textos(renderizar({"type": "linked_list", "values": [1]}))


def test_un_puntero_de_la_cabecera_que_no_llega_a_un_nodo_es_un_error():
    malo = {**LISTA_CON_CABECERA, "header": {"name": "l", "fields": ["ultimo -> 3"]}}
    with pytest.raises(ErrorDiagrama, match="ultimo apunta al nodo"):
        renderizar(malo)


@pytest.mark.parametrize("cabecera", [{"name": "l"}, {"fields": []}, {"fields": ["sin separador"]}, "texto"])
def test_una_cabecera_mal_escrita_es_un_error(cabecera):
    with pytest.raises(ErrorDiagrama):
        renderizar({**LISTA_CON_CABECERA, "header": cabecera})


def test_una_matriz_con_direcciones_simbolicas():
    svg = renderizar({"type": "matrix", "variant": "jagged", "name": "mat", "values": [[1], [2, 3]], "showAddresses": True,
                      "baseAddr": "@M", "rowAddresses": ["@F0", "@F1"], "lengthsType": "int"})
    assert {"@M", "@F1", "← @F0"} <= set(textos(svg))
    assert "int **mat | int largos[2]" in textos(svg) and not any(t.startswith("0x") for t in textos(svg))


def test_la_estructura_duena_lleva_los_largos_al_heap():
    svg = renderizar(DENTADA_EN_ESTRUCTURA)
    assert {"d (dentada_t)", "@L (largos: int[2])", "@F", "@L", "n"} <= set(textos(svg))
    assert svg.count("<path") >= 2  # las flechas a los largos y a las filas


def test_un_puntero_de_la_duena_a_un_destino_desconocido_es_un_error():
    with pytest.raises(ErrorDiagrama, match="se espera rows"):
        renderizar({**DENTADA_EN_ESTRUCTURA, "owner": {"name": "d", "fields": ["x -> otra"]}})


def test_las_direcciones_en_blanco_no_se_escapan_por_la_duena():
    assert "@L" not in textos(renderizar({**DENTADA_EN_ESTRUCTURA, "blankAddrs": True}))


def test_sin_las_claves_nuevas_el_dibujo_no_cambia():
    assert "Dir: 0x4000" in textos(renderizar({"type": "linked_list", "values": [1]}))
    assert any("size_t largos[1]" in t for t in textos(renderizar({"type": "matrix", "variant": "jagged", "values": [[1]]})))

