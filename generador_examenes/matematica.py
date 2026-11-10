"""Expresiones matemáticas `$ ... $`: LaTeX a MathML (HTML) y a matemática de Typst (PDF).

Un solo analizador con dos salidas, para que el HTML y el PDF de un examen muestren lo mismo sin
depender de JavaScript, de la red ni de una instalación de LaTeX. Cubre lo que se usa en enunciados
(fracciones, raíces, sumatorias, índices, `cases`, matrices, `\\left…\\right`, símbolos y funciones);
un comando que no conoce es un error con su nombre, no una fórmula mal dibujada.

La fórmula queda en el HTML de la pregunta como `<math>`, con el LaTeX en `alttext` (para lectores
de pantalla) y el Typst en `data-typst`, que es lo que toma `typst_markup` para el PDF.

Delimitadores: `$...$` y `$ ... $` en línea, y `$$...$$` aparte. Los espacios de adentro tienen que
ser parejos y el `$` que cierra no va seguido de un dígito, así que `$100 y $200`, `$ 5 y $ 6` o
`$(CC) -o $(TARGET)` son texto. Lo que está en código no se toca y `\\$` es un signo pesos. En texto
HTML (Moodle) también valen `\\(...\\)` y `\\[...\\]`.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class ErrorFormula(ValueError):
    """Una fórmula que no se puede interpretar."""


_GRIEGAS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "varpi": "ϖ", "rho": "ρ", "varrho": "ϱ", "sigma": "σ", "varsigma": "ς", "tau": "τ", "upsilon": "υ",
    "phi": "ϕ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "ell": "ℓ", "hbar": "ℏ", "aleph": "ℵ",
}
_OPERADORES = {
    "times": "×", "cdot": "⋅", "div": "÷", "pm": "±", "mp": "∓", "ast": "∗", "star": "⋆", "circ": "∘", "bullet": "∙",
    "oplus": "⊕", "otimes": "⊗", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠", "approx": "≈",
    "equiv": "≡", "sim": "∼", "simeq": "≃", "cong": "≅", "propto": "∝", "ll": "≪", "gg": "≫", "in": "∈", "notin": "∉",
    "ni": "∋", "subset": "⊂", "subseteq": "⊆", "supset": "⊃", "supseteq": "⊇", "cup": "∪", "cap": "∩",
    "setminus": "∖", "emptyset": "∅", "varnothing": "∅", "forall": "∀", "exists": "∃", "neg": "¬", "lnot": "¬",
    "land": "∧", "wedge": "∧", "lor": "∨", "vee": "∨", "to": "→", "rightarrow": "→", "leftarrow": "←", "gets": "←",
    "leftrightarrow": "↔", "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔", "implies": "⟹", "iff": "⟺",
    "mapsto": "↦", "uparrow": "↑", "downarrow": "↓", "infty": "∞", "partial": "∂", "nabla": "∇", "ldots": "…",
    "dots": "…", "cdots": "⋯", "vdots": "⋮", "ddots": "⋱", "mid": "∣", "parallel": "∥", "perp": "⟂", "angle": "∠",
    "prime": "′", "lceil": "⌈", "rceil": "⌉", "lfloor": "⌊", "rfloor": "⌋", "langle": "⟨", "rangle": "⟩", "vert": "|",
    "Vert": "‖", "backslash": "\\", "top": "⊤", "bot": "⊥",
}
_GRANDES = {"sum": "∑", "prod": "∏", "coprod": "∐", "bigcup": "⋃", "bigcap": "⋂"}  # con límites arriba y abajo
_INTEGRALES = {"int": "∫", "oint": "∮"}
_FUNCIONES = {f: False for f in ("log ln lg exp sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh det dim "
                                 "ker deg arg").split()}
_FUNCIONES.update({f: True for f in ("max", "min", "lim", "sup", "inf", "gcd")})
_ESCAPADOS = {"%": "%", "$": "$", "#": "#", "&": "&", "_": "_", "{": "{", "}": "}", "|": "‖"}
_ESPACIOS = {",": 0.167, ":": 0.222, ";": 0.278, "!": -0.167, " ": 0.333, "quad": 1.0, "qquad": 2.0}
_ACENTOS = {"bar": ("macron", "‾"), "overline": ("overline", "‾"), "hat": ("hat", "^"), "widehat": ("hat", "^"),
            "vec": ("arrow", "→"), "tilde": ("tilde", "~"), "widetilde": ("tilde", "~"), "dot": ("dot", "˙")}
_IGNORADOS = {"limits", "nolimits", "displaystyle", "textstyle", "scriptstyle", "big", "Big", "bigg", "Bigg", "bigl",
              "bigr", "Bigl", "Bigr", "biggl", "biggr", "Biggl", "Biggr"}
_ENTORNOS = {"matrix": ("", ""), "pmatrix": ("(", ")"), "bmatrix": ("[", "]"), "Bmatrix": ("{", "}"),
             "vmatrix": ("|", "|"), "Vmatrix": ("‖", "‖"), "cases": ("{", ""), "array": ("", ""), "aligned": ("", ""),
             "align": ("", ""), "align*": ("", "")}


@dataclass
class _Sim:
    texto: str
    clase: str  # mi, mn, mo o mtext


@dataclass
class _Funcion:
    nombre: str
    limites: bool = False


@dataclass
class _Fila:
    hijos: List["_Nodo"] = field(default_factory=list)


@dataclass
class _Frac:
    arriba: "_Nodo"
    abajo: "_Nodo"
    binomial: bool = False


@dataclass
class _Raiz:
    base: "_Nodo"
    indice: Optional["_Nodo"] = None


@dataclass
class _Indices:
    base: "_Nodo"
    sub: Optional["_Nodo"] = None
    sup: Optional["_Nodo"] = None


@dataclass
class _Acento:
    cual: str
    base: "_Nodo"


@dataclass
class _Estilo:
    cual: str  # bold, bb o cal
    base: "_Nodo"


@dataclass
class _Cerco:
    izq: str
    der: str
    base: "_Nodo"


@dataclass
class _Tabla:
    entorno: str
    filas: List[List["_Nodo"]]


@dataclass
class _Espacio:
    em: float


_Nodo = object


class _Analizador:
    def __init__(self, fuente: str):
        self.s, self.i = fuente, 0

    def _mira(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ""

    def _blancos(self) -> None:
        while self._mira().isspace():
            self.i += 1

    def _nombre(self) -> str:
        """El nombre del comando que empieza en la `\\` actual, sin consumirlo."""
        m = re.match(r"\\([A-Za-z]+|.)", self.s[self.i:], re.S)
        if not m:
            raise ErrorFormula("hay una \\ suelta al final")
        return m.group(1)

    def _corta(self, hasta: Tuple[str, ...]) -> bool:
        c = self._mira()
        if not c:
            return True
        if c == "}":
            if "}" not in hasta:
                raise ErrorFormula("sobra una llave de cierre")
            return True
        if c == "&":
            return "&" in hasta
        return c == "\\" and self._nombre() in hasta

    def fila(self, hasta: Tuple[str, ...] = ()) -> _Fila:
        hijos: List[_Nodo] = []
        while True:
            self._blancos()
            if self._corta(hasta):
                return _Fila(hijos)
            hijos.append(self._con_indices())

    def _con_indices(self) -> _Nodo:
        base = _Fila([]) if self._mira() in ("^", "_") else self._atomo()
        sub: Optional[_Nodo] = None
        sup: Optional[_Nodo] = None
        while True:
            self._blancos()
            c = self._mira()
            if c == "'":
                self.i += 1
                sup = _Fila([*(sup.hijos if isinstance(sup, _Fila) else [sup] if sup else []), _Sim("′", "mo")])
            elif c == "_" and sub is None:
                self.i += 1
                sub = self._argumento()
            elif c == "^" and sup is None:
                self.i += 1
                sup = self._argumento()
            elif c in ("_", "^"):
                raise ErrorFormula(f"doble {c}: agrupá con llaves")
            else:
                return base if sub is None and sup is None else _Indices(base, sub, sup)

    def _grupo(self) -> _Fila:
        self.i += 1  # {
        fila = self.fila(("}",))
        if self._mira() != "}":
            raise ErrorFormula("falta cerrar una llave")
        self.i += 1
        return fila

    def _argumento(self) -> _Nodo:
        self._blancos()
        c = self._mira()
        if not c:
            raise ErrorFormula("falta un argumento al final")
        if c == "{":
            return self._grupo()
        if c.isdigit():  # x^23 es x al cuadrado y un 3, como en LaTeX
            self.i += 1
            return _Sim(c, "mn")
        return self._atomo()

    def _llaves_crudas(self) -> str:
        """El contenido de `{...}` sin interpretar, para `\\text`."""
        self._blancos()
        if self._mira() != "{":
            raise ErrorFormula("se esperaba un argumento entre llaves")
        inicio, nivel = self.i + 1, 0
        while self.i < len(self.s):
            c = self.s[self.i]
            if c == "\\":
                self.i += 2
                continue
            nivel += (c == "{") - (c == "}")
            self.i += 1
            if nivel == 0:
                return re.sub(r"\\([%$#&_{}])", r"\1", self.s[inicio:self.i - 1])
        raise ErrorFormula("falta cerrar una llave")

    def _atomo(self) -> _Nodo:
        self._blancos()
        c = self._mira()
        if c == "{":
            return self._grupo()
        if c == "\\":
            return self._comando()
        if c.isdigit():
            m = re.match(r"\d+(?:\.\d+)?", self.s[self.i:])
            self.i += m.end()  # type: ignore[union-attr]
            return _Sim(m.group(0), "mn")  # type: ignore[union-attr]
        self.i += 1
        if c == "~":
            return _Espacio(0.333)
        if unicodedata.category(c).startswith("L"):
            return _Sim(c, "mi")
        if unicodedata.category(c).startswith("N"):
            return _Sim(c, "mn")
        return _Sim("−" if c == "-" else c, "mo")

    def _delimitador(self) -> str:
        self._blancos()
        c = self._mira()
        if c == "\\":
            nombre = self._nombre()
            self.i += 1 + len(nombre)
            if nombre in _OPERADORES:
                return _OPERADORES[nombre]
            if nombre in _ESCAPADOS:
                return _ESCAPADOS[nombre]
            raise ErrorFormula(f"delimitador desconocido: \\{nombre}")
        self.i += 1
        return "" if c == "." else c

    def _comando(self) -> _Nodo:
        nombre = self._nombre()
        self.i += 1 + len(nombre)
        if nombre in _GRIEGAS:
            return _Sim(_GRIEGAS[nombre], "mi")
        if nombre in _OPERADORES:
            return _Sim(_OPERADORES[nombre], "mo")
        if nombre in _GRANDES:
            return _Sim(_GRANDES[nombre], "grande")
        if nombre in _INTEGRALES:
            return _Sim(_INTEGRALES[nombre], "mo")
        if nombre in _FUNCIONES:
            return _Funcion(nombre, _FUNCIONES[nombre])
        if nombre in _ESCAPADOS:
            return _Sim(_ESCAPADOS[nombre], "mo")
        if nombre in _ESPACIOS:
            return _Espacio(_ESPACIOS[nombre])
        if nombre in _IGNORADOS:
            return _Fila([])
        if nombre in ("frac", "dfrac", "tfrac"):
            return _Frac(self._argumento(), self._argumento())
        if nombre in ("binom", "dbinom", "tbinom"):
            return _Frac(self._argumento(), self._argumento(), binomial=True)
        if nombre == "sqrt":
            indice = None
            self._blancos()
            if self._mira() == "[":
                self.i += 1
                inicio = self.i
                while self._mira() not in ("]", ""):
                    self.i += 1
                indice = _Analizador(self.s[inicio:self.i]).fila()
                self.i += 1
            return _Raiz(self._argumento(), indice)
        if nombre in ("text", "textrm", "textit", "mathrm", "mathit", "mbox"):
            return _Sim(self._llaves_crudas(), "mtext")
        if nombre == "operatorname":
            return _Funcion(self._llaves_crudas())
        if nombre in ("mathbf", "boldsymbol", "textbf"):
            return _Estilo("bold", self._argumento())
        if nombre in ("mathbb", "mathcal"):
            return _Estilo("bb" if nombre == "mathbb" else "cal", self._argumento())
        if nombre in _ACENTOS:
            return _Acento(nombre, self._argumento())
        if nombre == "left":
            izq = self._delimitador()
            base = self.fila(("right",))
            if self._mira() != "\\":
                raise ErrorFormula("\\left sin su \\right")
            self.i += len("\\right")
            return _Cerco(izq, self._delimitador(), base)
        if nombre == "pmod":
            return _Fila([_Espacio(0.333), _Sim("(", "mo"), _Funcion("mod"), self._argumento(), _Sim(")", "mo")])
        if nombre in ("bmod", "mod"):
            return _Funcion("mod")
        if nombre == "begin":
            return self._entorno(self._llaves_crudas())
        if nombre == "\\":
            return _Espacio(1.0)
        raise ErrorFormula(f"comando desconocido: \\{nombre}")

    def _entorno(self, entorno: str) -> _Tabla:
        if entorno not in _ENTORNOS:
            raise ErrorFormula(f"entorno desconocido: {entorno}")
        if entorno == "array":
            self._llaves_crudas()  # la alineación de las columnas
        filas: List[List[_Nodo]] = [[]]
        while True:
            filas[-1].append(self.fila(("&", "\\", "end")))
            c = self._mira()
            if not c:
                raise ErrorFormula(f"falta \\end{{{entorno}}}")
            if c == "&":
                self.i += 1
            elif self._nombre() == "\\":
                self.i += 2
                filas.append([])
            else:
                self.i += len("\\end")
                if self._llaves_crudas() != entorno:
                    raise ErrorFormula(f"\\begin{{{entorno}}} no cierra con su \\end")
                if filas[-1] == [_Fila([])]:  # el \\ del último renglón
                    filas.pop()
                return _Tabla(entorno, filas)


def _analizar(fuente: str) -> _Fila:
    return _Analizador(fuente).fila()


# --- Salida a Typst ---------------------------------------------------------------------------

_TYPST_ESCAPAR = re.compile(r'([\\$#_^/"&()\[\]{}|,;\'*~`:<>=])')


def _typst_cadena(texto: str) -> str:
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _typst_simbolo(texto: str) -> str:
    return _TYPST_ESCAPAR.sub(r"\\\1", texto)


def _typst_espacio(em: float) -> str:
    nombres = {0.167: "thin", 0.222: "med", 0.278: "thick", 0.333: "space", 1.0: "quad", 2.0: "wide"}
    return nombres.get(em) or f"#h({em}em)"


def _a_typst(n: _Nodo, en_fila: bool = False) -> str:
    if isinstance(n, _Sim):
        return _typst_cadena(n.texto) if n.clase == "mtext" else _typst_simbolo(n.texto)
    if isinstance(n, _Funcion):
        return f'op({_typst_cadena(n.nombre)}, limits: #true)' if n.limites else f'op({_typst_cadena(n.nombre)})'
    if isinstance(n, _Fila):
        return " ".join(_a_typst(h) for h in n.hijos)
    if isinstance(n, _Frac):
        return f"{'binom' if n.binomial else 'frac'}({_a_typst(n.arriba)}, {_a_typst(n.abajo)})"
    if isinstance(n, _Raiz):
        if n.indice is not None:
            return f"root({_a_typst(n.indice)}, {_a_typst(n.base)})"
        return f"sqrt({_a_typst(n.base)})"
    if isinstance(n, _Indices):
        sub = f"({_a_typst(n.sub)})" if n.sub is not None else None
        sup = f"({_a_typst(n.sup)})" if n.sup is not None else None
        if isinstance(n.base, (_Sim, _Funcion)):
            return _a_typst(n.base) + (f"_{sub}" if sub else "") + (f"^{sup}" if sup else "")
        if isinstance(n.base, _Fila) and not n.base.hijos:
            return '""' + (f"_{sub}" if sub else "") + (f"^{sup}" if sup else "")
        partes = ([f"b: {sub[1:-1]}"] if sub else []) + ([f"t: {sup[1:-1]}"] if sup else [])
        return f"attach({_a_typst(n.base)}, {', '.join(partes)})"
    if isinstance(n, _Acento):
        return f"{_ACENTOS[n.cual][0]}({_a_typst(n.base)})"
    if isinstance(n, _Estilo):
        return f"{n.cual}({_a_typst(n.base)})"
    if isinstance(n, _Cerco):
        return f"lr({_typst_simbolo(n.izq)} {_a_typst(n.base)} {_typst_simbolo(n.der)})"
    if isinstance(n, _Espacio):
        return _typst_espacio(n.em)
    if isinstance(n, _Tabla):
        if n.entorno == "cases":
            return "cases(" + ", ".join(" & ".join(_a_typst(c) for c in f) for f in n.filas) + ")"
        if n.entorno in ("aligned", "align", "align*"):
            return " \\ ".join(" & ".join(_a_typst(c) for c in f) for f in n.filas)
        delim = {"(": '"("', "[": '"["', "{": '"{"', "|": '"|"', "‖": '"||"'}.get(_ENTORNOS[n.entorno][0], "#none")
        return f"mat(delim: {delim}, " + "; ".join(", ".join(_a_typst(c) for c in f) for f in n.filas) + ")"
    raise ErrorFormula(f"nodo desconocido: {n!r}")


# --- Salida a MathML --------------------------------------------------------------------------

ACENTO_ATRIBUTOS = ' stretchy="true" accent="true"'


def _mo(texto: str, atributos: str = "") -> str:
    return f"<mo{atributos}>{html.escape(texto, quote=False)}</mo>"


def _doble(letra: str) -> str:
    especiales = {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ", "R": "ℝ", "Z": "ℤ"}
    return especiales.get(letra) or (chr(0x1D538 + ord(letra) - 65) if "A" <= letra <= "Z" else letra)


def _caligrafica(letra: str) -> str:
    especiales = {"B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ", "L": "ℒ", "M": "ℳ", "R": "ℛ"}
    return especiales.get(letra) or (chr(0x1D49C + ord(letra) - 65) if "A" <= letra <= "Z" else letra)


def _con_letras(n: _Nodo, cambio) -> _Nodo:
    if isinstance(n, _Sim) and n.clase == "mi":
        return _Sim("".join(cambio(c) for c in n.texto), "mi")
    if isinstance(n, _Fila):
        return _Fila([_con_letras(h, cambio) for h in n.hijos])
    return n


def _es_funcion(n: _Nodo) -> bool:
    return isinstance(n, _Funcion) or (isinstance(n, _Indices) and isinstance(n.base, _Funcion))


_DELIMITADORES = set("()[]{}|‖⌈⌉⌊⌋⟨⟩")
_ESPACIO_FUNCION = '<mspace width="0.167em"/>'


def _separa_de_la_funcion(vecino: Optional[_Nodo], abre: str) -> bool:
    """Si entre una función y `vecino` va un espacio: `n log n`, pero `log(n)`, `(log n)` o `2 + log n`."""
    if vecino is None or isinstance(vecino, _Espacio):
        return False
    return not (isinstance(vecino, _Sim) and vecino.clase == "mo" and vecino.texto != abre)


def _primas(n: Optional[_Nodo]) -> int:
    """Cuántas primas tiene un superíndice que no tiene otra cosa."""
    if isinstance(n, _Fila) and all(isinstance(h, _Sim) and h.texto == "′" for h in n.hijos):
        return len(n.hijos)
    return 0


def _alineacion(entorno: str, columna: int) -> str:
    if entorno == "cases":
        return "left"
    if entorno in ("aligned", "align", "align*"):
        return "right" if columna % 2 == 0 else "left"
    return "center"


def _a_mathml(n: _Nodo, bloque: bool) -> str:
    def m(x: _Nodo) -> str:
        return _a_mathml(x, bloque)

    if isinstance(n, _Sim):
        texto = html.escape(n.texto, quote=False)
        if n.clase == "grande":
            return f'<mo largeop="true">{texto}</mo>'
        if n.clase == "mo" and n.texto in _DELIMITADORES:
            # Sin esto se estiran con lo que tienen al lado y llevan el espacio de un operador.
            return f'<mo stretchy="false" lspace="0" rspace="0">{texto}</mo>'
        if n.clase == "mtext":  # MathML recorta los espacios de los extremos: «si n» sería «sin»
            texto = re.sub(r"^ +| +$", lambda m: "\u00a0" * len(m.group(0)), texto)
        return f"<{n.clase}>{texto}</{n.clase}>"
    if isinstance(n, _Funcion):
        return f'<mi mathvariant="normal">{html.escape(n.nombre, quote=False)}</mi>'
    if isinstance(n, _Fila):
        partes = []
        for i, h in enumerate(n.hijos):
            anterior = n.hijos[i - 1] if i else None
            siguiente = n.hijos[i + 1] if i + 1 < len(n.hijos) else None
            antes = _es_funcion(h) and _separa_de_la_funcion(anterior, ")")
            despues = _es_funcion(h) and _separa_de_la_funcion(siguiente, "")
            partes += [_ESPACIO_FUNCION if antes else "", m(h), _ESPACIO_FUNCION if despues else ""]
        return "<mrow>" + "".join(partes) + "</mrow>"
    if isinstance(n, _Frac):
        if n.binomial:
            parentesis = '<mo fence="true" stretchy="true" lspace="0" rspace="0">{}</mo>'
            return ("<mrow>" + parentesis.format("(") + '<mfrac linethickness="0">' + m(n.arriba) + m(n.abajo)
                    + "</mfrac>" + parentesis.format(")") + "</mrow>")
        return "<mfrac>" + m(n.arriba) + m(n.abajo) + "</mfrac>"
    if isinstance(n, _Raiz):
        if n.indice is not None:
            return "<mroot>" + m(n.base) + m(n.indice) + "</mroot>"
        return "<msqrt>" + m(n.base) + "</msqrt>"
    if isinstance(n, _Indices):
        con_limites = bloque and ((isinstance(n.base, _Sim) and n.base.clase == "grande")
                                  or (isinstance(n.base, _Funcion) and n.base.limites))
        abajo, arriba, ambos = ("munder", "mover", "munderover") if con_limites else ("msub", "msup", "msubsup")
        if n.sub is None and _primas(n.sup):  # como superíndice quedarían demasiado arriba
            return m(n.base) + _mo("′", ' lspace="0" rspace="0"') * _primas(n.sup)
        if n.sub is not None and n.sup is not None:
            return f"<{ambos}>{m(n.base)}{m(n.sub)}{m(n.sup)}</{ambos}>"
        if n.sub is not None:
            return f"<{abajo}>{m(n.base)}{m(n.sub)}</{abajo}>"
        return f"<{arriba}>{m(n.base)}{m(n.sup)}</{arriba}>"  # type: ignore[arg-type]
    if isinstance(n, _Acento):
        return f'<mover accent="true">{m(n.base)}{_mo(_ACENTOS[n.cual][1], ACENTO_ATRIBUTOS)}</mover>'
    if isinstance(n, _Estilo):
        if n.cual == "bold":
            return f'<mrow style="font-weight:bold">{m(n.base)}</mrow>'
        return m(_con_letras(n.base, _doble if n.cual == "bb" else _caligrafica))
    if isinstance(n, _Cerco):
        izq = _mo(n.izq, ' fence="true" stretchy="true" lspace="0" rspace="0"') if n.izq else ""
        der = _mo(n.der, ' fence="true" stretchy="true" lspace="0" rspace="0"') if n.der else ""
        return f"<mrow>{izq}{m(n.base)}{der}</mrow>"
    if isinstance(n, _Espacio):
        return f'<mspace width="{n.em}em"/>'
    if isinstance(n, _Tabla):
        izq, der = _ENTORNOS[n.entorno]
        # Los navegadores no respetan `columnalign`: la alineación va por CSS.
        filas = "".join("<mtr>" + "".join(f'<mtd style="text-align:{_alineacion(n.entorno, j)}">{m(c)}</mtd>'
                                          for j, c in enumerate(f)) + "</mtr>" for f in n.filas)
        tabla = f"<mtable>{filas}</mtable>"
        return f"<mrow>{_mo(izq) if izq else ''}{tabla}{_mo(der) if der else ''}</mrow>"
    raise ErrorFormula(f"nodo desconocido: {n!r}")


def a_typst(fuente: str) -> str:
    """El LaTeX como el contenido de una matemática de Typst (sin los `$`)."""
    return _a_typst(_analizar(fuente))


def a_html(fuente: str, bloque: bool = False) -> str:
    """El elemento `<math>` de una fórmula, con el LaTeX y el Typst en sus atributos."""
    arbol = _analizar(fuente)
    latex = html.escape(fuente.strip(), quote=True)
    typst = html.escape(_a_typst(arbol), quote=True)
    modo = "block" if bloque else "inline"
    return (f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="{modo}" alttext="{latex}" '
            f'data-typst="{typst}">{_a_mathml(arbol, bloque)}</math>')


# --- En el texto de una pregunta --------------------------------------------------------------

_PROTEGIDO = r"(?P<codigo>```.*?```|~~~.*?~~~|``[^\n]*?``|`[^`\n]*`|<pre\b.*?</pre>|<code\b.*?</code>)"
_DOLAR = r"(?P<dolar>\\\$)"
_BLOQUE = r"\$\$(?P<bloque>.+?)\$\$"
_LINEA = r"(?<![\\$\w])\$(?P<linea>[^\s$](?:(?:\\.|[^$\\\n])*(?:\\.|[^\s$\\]))?)\$(?![\d$])"
_ESPACIADA = r"(?<![\\$\w])\$[ \t]+(?P<linea3>[^\s$\d][^$\n]*?)[ \t]+\$(?![ \t]*[\d$])"
_LATEX = r"\\\[(?P<bloque2>.+?)\\\]|\\\((?P<linea2>.+?)\\\)"
_FORMULAS = re.compile("|".join((_PROTEGIDO, _DOLAR, _BLOQUE, _LINEA, _ESPACIADA)), re.S)
_FORMULAS_LATEX = re.compile("|".join((_PROTEGIDO, _DOLAR, _BLOQUE, _LINEA, _ESPACIADA, _LATEX)), re.S)


def _fuente(m: re.Match) -> Tuple[Optional[str], bool]:
    """(LaTeX, va aparte) de una coincidencia; sin LaTeX si es código o un `\\$`."""
    grupos = m.groupdict()
    for nombre, bloque in (("bloque", True), ("bloque2", True), ("linea", False), ("linea2", False), ("linea3", False)):
        if grupos.get(nombre) is not None:
            return html.unescape(grupos[nombre]), bloque
    return None, False


def expandir_formulas(texto: str, delimitadores_latex: bool = False) -> Tuple[str, Dict[str, str]]:
    """Reemplaza las fórmulas por marcadores; devuelve el texto y el HTML de cada marcador.

    Los marcadores sobreviven a la conversión de Markdown (que si no se comería los `_` y los `*`).
    Una fórmula inválida queda como código, con el motivo en `title`.
    """
    formulas: Dict[str, str] = {}

    def reemplazar(m: re.Match) -> str:
        if m.group("dolar"):
            return "&#36;"
        fuente, bloque = _fuente(m)
        if fuente is None:
            return m.group(0)
        marcador = f"FORMULA{len(formulas)}X{hashlib.sha1(m.group(0).encode()).hexdigest()[:8]}"
        try:
            formulas[marcador] = a_html(fuente, bloque)
        except ErrorFormula as e:
            formulas[marcador] = (f'<code class="formula-error" title="{html.escape(str(e), quote=True)}">'
                                  f"{html.escape(m.group(0), quote=False)}</code>")
        return marcador

    return (_FORMULAS_LATEX if delimitadores_latex else _FORMULAS).sub(reemplazar, texto), formulas


def reponer_formulas(html_texto: str, formulas: Dict[str, str]) -> str:
    for marcador, formula in formulas.items():
        html_texto = html_texto.replace(marcador, formula)
    return html_texto


def errores_en_texto(texto: str) -> List[Tuple[int, str, str]]:
    """(posición, fórmula, motivo) de cada fórmula inválida de un texto, para `lint-gift`."""
    errores = []
    for m in _FORMULAS.finditer(texto):
        fuente, _ = _fuente(m)
        if fuente is None:
            continue
        try:
            _analizar(fuente)
        except ErrorFormula as e:
            errores.append((m.start(), m.group(0), str(e)))
    return errores
