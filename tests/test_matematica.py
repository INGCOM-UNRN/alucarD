"""Fórmulas `$...$`: LaTeX a MathML (HTML) y a Typst (PDF), en preguntas y consignas."""

import html
import re
import sys
import xml.etree.ElementTree as ET

import pytest

from generador_examenes.core.markdown_utils import detect_and_convert_format, markdown_to_html
from generador_examenes.generators.typst_markup import html_a_typst
from generador_examenes.matematica import ErrorFormula, a_html, a_typst, errores_en_texto, expandir_formulas

MML = "{http://www.w3.org/1998/Math/MathML}"

# Lo que se usa en el banco de enunciados, y lo común en complejidad y matemática discreta.
FORMULAS = [
    r"O(\log N)", r"O(n^2)", r"O(n \log n)", r"\Theta(2^n)", r"O(\alpha(N))", r"n \ge 0", r"3 \times 3",
    r"\binom{n}{k}", r"P(n, k) = \frac{n!}{(n-k)!}", r"D = \sum_{i=0}^{n-1} b_i \cdot 2^{n-1-i}", r"\sqrt{n}",
    r"\sqrt[3]{x}", r"-273.15^\circ\text{C}", r"X_{n+1} = (a X_n + c) \pmod m", r"[n, m)", r"(a, b]", r"c_{ij}",
    r"A^T", r"\prod_{i=1}^{n} i", r"\left( \frac{a}{b} \right)^2", r"\left\{ x \mid x > 0 \right\}", r"\bar{x}",
    r"\lceil \log_2 n \rceil", r"\lfloor n / 2 \rfloor", r"\max_{i} v_i", r"\lim_{n \to \infty} f(n)", r"a \bmod b",
    r"\begin{cases} 1 & \text{si } n = 0 \\ n \cdot f(n-1) & \text{si } n > 0 \end{cases}",
    r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}", r"\begin{bmatrix} a \\ b \end{bmatrix}",
    r"\begin{aligned} a &= b \\ c &= d \end{aligned}", r"\mathbb{N} \subset \mathbb{Z}", r"\mathbf{v} \cdot \mathcal{L}",
    r"x', x''", r"100\%", r"\{1, 2\}", r"a_1, a_2, \dots, a_n", r"\sin^2 x + \cos^2 x = 1", r"{ab}^2", r"^\circ",
    r"\vec{v}", r"\hat{y}", r"f(x) = x", r"a < b \le c", r"a = b; c = d", r"x_{\text{máx}}", r'\text{dijo "hola"}',
]


@pytest.mark.parametrize("fuente", FORMULAS)
@pytest.mark.parametrize("bloque", [False, True])
def test_cada_formula_da_mathml_valido(fuente, bloque):
    raiz = ET.fromstring(a_html(fuente, bloque))
    assert raiz.tag == f"{MML}math" and raiz.get("alttext") == fuente
    assert raiz.get("display") == ("block" if bloque else "inline") and raiz.get("data-typst")


def test_typst_compila_todas(tmp_path):
    pytest.importorskip("typst")
    from generador_examenes.generators.pdf_renderer import compilar_typst_a_pdf

    cuerpo = "\n\n".join(f"${a_typst(f)}$ y $ {a_typst(f)} $" for f in FORMULAS)
    assert compilar_typst_a_pdf(f"#set page(width: 16cm, height: auto)\n{cuerpo}\n", tmp_path / "f.pdf").is_file()


def test_estructura_mathml():
    assert "<mfrac>" in a_html(r"\frac{a}{b}") and "<msqrt>" in a_html(r"\sqrt{x}") and "<mroot>" in a_html(r"\sqrt[3]{x}")
    assert "<msup><mi>n</mi><mn>2</mn></msup>" in a_html("n^2")
    assert "<msubsup>" in a_html(r"\sum_{i}^{n}") and "<munderover>" in a_html(r"\sum_{i}^{n}", True)
    assert "<mtable" in a_html(r"\begin{pmatrix} 1 \end{pmatrix}")


def test_el_indice_toma_un_solo_digito_como_latex():
    assert "<msup><mi>x</mi><mn>2</mn></msup><mn>3</mn>" in a_html("x^23")


def test_las_funciones_se_separan_de_su_argumento():
    assert '<mi mathvariant="normal">log</mi><mspace width="0.167em"/><mi>n</mi>' in a_html(r"\log n")
    assert "<mspace" not in a_html(r"\log(n)")


def test_las_funciones_se_separan_de_lo_que_tienen_antes():
    assert '<mi>n</mi><mspace width="0.167em"/><mi mathvariant="normal">log</mi>' in a_html(r"n \log n")
    assert '<mi>a</mi><mspace width="0.167em"/><mi mathvariant="normal">mod</mi>' in a_html(r"a \bmod b")
    assert '<mo>+</mo><mi mathvariant="normal">log</mi>' in a_html(r"2 + \log n")


def test_el_espacio_de_un_texto_no_se_pierde():
    assert "<mtext>si\u00a0</mtext>" in a_html(r"\text{si } n")  # sin él se lee «sin»


def test_los_parentesis_no_se_estiran_ni_llevan_espacio_de_operador():
    assert '<mo stretchy="false" lspace="0" rspace="0">(</mo>' in a_html("f(n)")
    assert 'stretchy="true"' in a_html(r"\left( x \right)")


def test_las_columnas_de_cases_van_a_la_izquierda():
    assert '<mtd style="text-align:left">' in a_html(r"\begin{cases} 1 & 2 \end{cases}")


def test_la_prima_no_es_un_superindice():
    assert "<msup>" not in a_html("x'") and "′" in a_html("x'")
    assert "<msup>" in a_html("x^2")


def test_typst_escapa_lo_que_tiene_sentido_en_su_matematica():
    assert a_typst("a/b") == r"a \/ b"
    assert a_typst("[n, m)") == r"\[ n \, m \)"
    assert a_typst(r"\text{a b}") == '"a b"'
    assert a_typst(r"\log n") == 'op("log") n'
    assert a_typst(r"x_{i}^{2}") == "x_(i)^(2)"


@pytest.mark.parametrize("fuente, mensaje", [
    (r"\noexiste", r"desconocido: \\noexiste"), (r"\frac{a", "cerrar una llave"), ("a}", "llave de cierre"),
    (r"\frac", "argumento"), ("x^", "argumento"), ("x^2^3", "doble"), (r"\left( a", r"\\right"),
    (r"\begin{cases} 1", r"\\end"), (r"\begin{tikz} \end{tikz}", "entorno desconocido"),
    (r"\begin{cases} a \end{pmatrix}", "no cierra"), ("\\", r"suelta"),
])
def test_errores_claros(fuente, mensaje):
    with pytest.raises(ErrorFormula, match=mensaje):
        a_html(fuente)


@pytest.mark.parametrize("texto", [
    "Cuesta $100 y $200 en total", "De $100-$200", "$ 5 y $ 6", "precio: $5", "`$x$` es código", "$(CC) -o $(TARGET)",
    "```\n$x$\n```", "<code>$x$</code>", "<pre>$x$</pre>", "US$100$", "$ x$", "$x $",
])
def test_lo_que_no_es_formula_queda_igual(texto):
    assert expandir_formulas(texto) == (texto, {})


@pytest.mark.parametrize("texto, fuente", [("El costo es $O(n)$.", "O(n)"), ("$x$", "x"), ("($x$)", "x"), ("$ O(n) $", "O(n)"),
                                           (r"$\{a\}$", r"\{a\}"), ("$$ x + y $$", " x + y ")])
def test_lo_que_si_es_formula(texto, fuente):
    _, formulas = expandir_formulas(texto)
    assert len(formulas) == 1 and html.escape(fuente.strip()) in next(iter(formulas.values()))


def test_formula_multilinea_aparte():
    _, formulas = expandir_formulas("$$\na\n+ b\n$$")
    assert 'display="block"' in next(iter(formulas.values()))


def test_signo_pesos_escapado():
    assert "$5" in html.unescape(markdown_to_html(r"Vale \$5 y $x$")) and "<math" in markdown_to_html(r"Vale \$5 y $x$")


def test_markdown_no_se_come_los_guiones_bajos_ni_los_asteriscos():
    salida = markdown_to_html("$a_1 * b_2$ y $c_3 * d_4$")
    assert "<em>" not in salida and salida.count("<math") == 2 and "<msub>" in salida


def test_una_formula_invalida_queda_como_codigo_con_el_motivo():
    salida = markdown_to_html(r"Mirá $\noexiste$ acá")
    assert 'class="formula-error"' in salida and "noexiste" in salida and "<math" not in salida
    assert "$" in html_a_typst(salida)  # el PDF la muestra como código, sin romper


def test_html_de_moodle_con_delimitadores_latex():
    assert "<math" in detect_and_convert_format(r"<p>Sea \(x^2\) y \[y\]</p>", "html")
    assert "<math" in detect_and_convert_format("<p>Sea $a &lt; b$</p>", "html")
    assert "a < b" in html.unescape(detect_and_convert_format("<p>Sea $a &lt; b$</p>", "html"))


def test_en_markdown_los_corchetes_escapados_no_son_formula():
    assert "<math" not in markdown_to_html(r"Una lista \[1, 2\]")


def test_formula_al_pdf():
    typst = html_a_typst(markdown_to_html(r"Costo $O(n^2)$ y $$\frac{a}{b}$$"))
    assert "$O \\( n^(2) \\)$" in typst and "$ frac(a, b) $" in typst


def test_formula_en_tabla_al_pdf():
    typst = html_a_typst(markdown_to_html("| a |\n|---|\n| $x^2$ |"))
    assert "$x^(2)$" in typst


def test_errores_en_texto_para_el_linter():
    assert [e[1:] for e in errores_en_texto(r"bien $x$ y mal $\noexiste$")] == [(r"$\noexiste$", r"comando desconocido: \noexiste")]


def test_consigna_con_formula():
    html_consigna = markdown_to_html("En tiempo $O(1)$.", saltos_de_linea=False)
    assert "<math" in html_consigna


def test_lint_gift_marca_las_formulas_invalidas(tmp_path, monkeypatch, capsys):
    from generador_examenes.__main__ import main

    banco = tmp_path / "b.gift"
    banco.write_text("::mala:: [markdown]Mirá $\\noexiste$ {=a ~b}\n\n::bien:: [markdown]$a$ {=$a \\= b$ ~c}\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alucard", "lint-gift", str(banco)])
    assert main() == 1
    salida = capsys.readouterr().out
    assert "mala" in salida and "noexiste" in salida and "«bien»" not in salida


def test_generar_avisa_de_una_formula_invalida(tmp_path, monkeypatch, capsys):
    from generador_examenes.__main__ import main

    (tmp_path / "b.gift").write_text("::P:: [markdown]Mirá $\\noexiste$ {=a ~b}\n", encoding="utf-8")
    definicion = tmp_path / "d.yaml"
    definicion.write_text("""nombre_examen: "E"
institucion: "U"
materia: "M"
configuracion_examen:
  generar_clave_profesor: false
secciones_examen:
  - nombre: "A"
    pools:
      - cantidad: 1
""", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion), "-i", str(tmp_path / "b.gift"),
                                      "-o", str(tmp_path / "o")])
    assert main() == 0
    assert "fórmula inválida" in capsys.readouterr().err


def test_la_ortografia_no_lee_las_formulas(monkeypatch):
    from generador_examenes.core import languagetool_checker as lt

    visto = {}

    def base(texto, **_):
        visto["texto"] = texto
        return []

    monkeypatch.setattr(lt, "_analizar_texto_base", base)
    fuente = "Sea " + a_html("x^2") + " fin"
    lt.analizar_texto_languagetool(fuente, pregunta_id="p", campo="enunciado")
    assert "<math" not in visto["texto"] and len(visto["texto"]) == len(fuente)
    assert re.search(r"fin$", visto["texto"])
