"""HTML de las preguntas → marcado Typst, para las plantillas PDF (`|typst`, Ola 14).

Los enunciados y opciones llegan como HTML (el Moodle XML de idkfa, o el GIFT ya convertido): tal
cual, Typst mostraba las etiquetas (`</code></p>`) e interpretaba como marcado los `*`, `_`, `#`, `$`
o el `//` de una URL (que abre un comentario). Acá cada bloque `<pre>` pasa a `#raw(block: true)` con
su lenguaje, `<code>` a `#raw(...)`, `<strong>`/`<b>` y `<em>`/`<i>` a `#strong[...]`/`#emph[...]`,
los párrafos y `<br>` a saltos, los `<svg>` (diagramas de estructuras) a `#image`, los `<math>` a su
matemática de Typst (`data-typst`), y el resto del texto se escapa. Las demás etiquetas se quitan.
"""
from __future__ import annotations

import html
import json
import re

_ESPECIALES = re.compile(r"([\\#$*_`<>@\[\]~/=+\-])")
_ETIQUETA = re.compile(r"<(/?)([a-zA-Z0-9]+)\b[^>]*?>", re.S)
_PRE = re.compile(r"<pre\b(?P<pre>[^>]*)>(?:\s*<code\b(?P<attrs>[^>]*)>)?(?P<codigo>.*?)(?:</code>\s*)?</pre>", re.S | re.I)
_FENCE = re.compile(r"```(?P<lang>[\w+#-]*)\n(?P<codigo>.*?)```", re.S)
_CODE = re.compile(r"<code\b[^>]*>(?P<codigo>.*?)</code>", re.S | re.I)
_LENGUAJE = re.compile(r"language-([\w+#-]+)")
_TABLA = re.compile(r"<table\b(?P<attrs>[^>]*)>(?P<cuerpo>.*?)</table>", re.S | re.I)
_OPCIONES_TABLA = re.compile(r'\bdata-opciones="(?P<opciones>[^"]*)"')
_FILA = re.compile(r"<tr\b[^>]*>(?P<celdas>.*?)</tr>", re.S | re.I)
_CELDA = re.compile(r"<t(?P<tipo>[hd])\b[^>]*>(?P<contenido>.*?)</t[hd]>", re.S | re.I)
_SVG = re.compile(r"<svg\b(?P<attrs>[^>]*)>.*?</svg>", re.S | re.I)
_ANCHO_SVG = re.compile(r'\bwidth="(?P<px>[\d.]+)"')
_ALTO_SVG = re.compile(r'\bheight="(?P<px>[\d.]+)"')
_COMENTARIO = re.compile(r"<!--.*?-->", re.S)
# En una grilla, para que un renglón demasiado largo siga alineado con el código y no debajo del número.
_LINEA_NUMERADA = ("it => box(width: 100%, grid(columns: (2.2em, 1fr), column-gutter: 0.8em, "
                   "align(right, text(fill: luma(110), size: 0.85em, str(it.number))), it.body))")
# Dónde se puede partir una pregunta: `<!--corte-->` (la marca `// [corte]`) y los encabezados.
_CORTE = re.compile(r"<!--\s*corte\s*-->|(?=<h[1-6]\b)", re.I)
_MATH = re.compile(r'<math\b(?P<attrs>[^>]*)>.*?</math>', re.S | re.I)
_TYPST_MATH = re.compile(r'\bdata-typst="(?P<typst>[^"]*)"')


def _cadena(texto: str) -> str:
    """Un literal de cadena de Typst."""
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'


def _texto_plano(fragmento: str) -> str:
    """El contenido de un bloque de código: sin etiquetas (p. ej. el resaltado de voight) y sin entidades."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


def escapar(texto: str) -> str:
    return _ESPECIALES.sub(r"\\\1", texto)


def _tabla_typst(filas: list, opciones: dict) -> str:
    """Una tabla como `(tipo, contenido)` por celda, con las opciones de un bloque ```tabla."""
    if opciones.get("sin-encabezado"):
        filas = [f for f in filas if f[0][0] != "h"]
    if not filas:
        return ""
    # Una celda vacía es para completar a mano: su columna toma el ancho que sobra y conserva el alto
    # de un renglón aunque toda la fila esté vacía.
    columnas = [("1fr" if any(j < len(f) and not f[j][1].strip() for f in filas) else "auto")
                for j in range(max(len(f) for f in filas))]
    if "ancho" in opciones and "1fr" not in columnas:
        columnas = ["1fr"] * len(columnas)
    columnas = opciones.get("columnas", columnas)
    vacia = f"[#box(height: {opciones.get('alto', '1em')})]"
    argumentos = [f"columns: ({', '.join(columnas)},)" if "1fr" in columnas or "columnas" in opciones
                  else f"columns: {len(columnas)}",
                  f"inset: {opciones.get('relleno', '4pt')}"]
    # `align` pasa a las celdas: con la tabla ubicada en la página, se fija el de ellas.
    if "alinear" in opciones:
        argumentos.append(f"align: ({', '.join(opciones['alinear'])},)")
    elif "posicion" in opciones:
        argumentos.append("align: left")
    if opciones.get("bordes") == "ninguno":
        argumentos.append("stroke: none")
    elif opciones.get("bordes") == "horizontales":
        argumentos.append("stroke: (x: none, y: 0.5pt)")
    sombra = [c for clave, c in (("sombrear-encabezado", "y == 0"), ("cebra", "(y > 0 and calc.even(y))"))
              if opciones.get(clave)]
    if sombra:
        argumentos.append(f"fill: (_, y) => if {' or '.join(sombra)} {{ luma(235) }}")
    celdas = ", ".join(f"[#strong[{c}]]" if tipo == "h" else f"[{c}]" if c.strip() else vacia
                       for f in filas for tipo, c in f)
    tabla = f"#table({', '.join(argumentos)}, {celdas})"
    if "letra" in opciones:
        tabla = f"#text(size: {opciones['letra']})[{tabla}]"
    if "ancho" in opciones:
        tabla = f"#block(width: {opciones['ancho']})[{tabla}]"
    if "posicion" in opciones:
        lugar = {"centrado": "center", "izquierda": "left", "derecha": "right"}[opciones["posicion"]]
        tabla = f"#align({lugar})[{tabla}]"
    return f"\n{tabla}\n"


def partes_typst(fragmento: object) -> list:
    """El enunciado en las partes por las que se puede cortar, como `{"marca", "typst"}`: `marca` dice
    si la parte viene de un `// [corte]` y no de un encabezado. Siempre hay al menos una parte."""
    texto = "" if fragmento is None else str(fragmento)
    partes: list = []
    inicio, marca = 0, False
    for m in [*_CORTE.finditer(texto), None]:
        tramo = html_a_typst(texto[inicio:m.start() if m else len(texto)])
        if tramo.strip():
            partes.append({"marca": marca and bool(partes), "typst": tramo})
            marca = False
        if m:
            inicio, marca = m.end(), marca or bool(m.group())
    return partes or [{"marca": False, "typst": ""}]


def _limite(medida: str, base: str) -> str:
    """Una medida como longitud de Typst; un porcentaje es de `base`."""
    if medida.endswith("%"):
        return f"{base} * {float(medida[:-1]) / 100:g}"
    return f"({medida}).to-absolute()"


def _vigia_de_tabla(cuerpo: str) -> str:
    """Typst achica las columnas de una tabla ancha y lo que no se puede partir se sale de la celda, sin que
    `measure` lo vea. Si no entran ni las palabras más largas de cada columna, deja una marca <desborde>."""
    columnas: dict = {}
    for fila in _FILA.finditer(cuerpo):
        for j, celda in enumerate(_CELDA.finditer(fila.group("celdas"))):
            contenido = celda.group("contenido")
            palabras = html.unescape(re.sub(r"<[^>]+>", " ", contenido)).split() or [""]
            palabra = max(palabras, key=len)
            if len(palabra) > len(columnas.get(j, ("",))[0]):
                columnas[j] = (palabra, "<code" in contenido)
    if not columnas:
        return ""
    muestras = ", ".join(f"raw({_cadena(p)})" if codigo else _cadena(p) for p, codigo in columnas.values())
    return (f"#place(layout(lugar => if ({muestras},).map(m => measure(m).width + 10pt).sum() > lugar.width "
            '{ context [#metadata((pregunta: state("pregunta-actual").get(), motivo: "una tabla no entra en el '
            'ancho de la página")) <desborde>] }))\n')


def html_a_typst(fragmento: object) -> str:
    """El HTML (o texto) de una pregunta como marcado Typst."""
    texto = ("" if fragmento is None else str(fragmento)).replace("\r\n", "\n").replace("\r", "\n")
    texto = _COMENTARIO.sub("", texto)
    bloques: list = []

    def apartar(contenido: str) -> str:
        bloques.append(contenido)
        return f"\x00{len(bloques) - 1}\x00"

    def bloque_pre(m: re.Match) -> str:
        lenguaje = _LENGUAJE.search(m.group("attrs") or "")
        codigo = _texto_plano(m.group("codigo")).strip("\n")
        lang = f', lang: "{lenguaje.group(1)}"' if lenguaje else ""
        bloque = f"#raw(block: true{lang}, {_cadena(codigo)})"
        if 'data-numerar="si"' in m.group("pre"):
            bloque = f"#[#show raw.line: {_LINEA_NUMERADA}\n{bloque}]"
        return apartar(f"\n{bloque}\n")

    def bloque_fence(m: re.Match) -> str:
        lang = f', lang: "{m.group("lang")}"' if m.group("lang") else ""
        return apartar(f"\n#raw(block: true{lang}, {_cadena(_texto_plano(m.group('codigo')).rstrip())})\n")

    def tabla(m: re.Match) -> str:
        filas = [[(c.group("tipo").lower(), html_a_typst(c.group("contenido"))) for c in _CELDA.finditer(f.group("celdas"))]
                 for f in _FILA.finditer(m.group("cuerpo"))]
        filas = [f for f in filas if f]
        opciones = _OPCIONES_TABLA.search(m.group("attrs"))
        return apartar(_vigia_de_tabla(m.group("cuerpo"))
                       + _tabla_typst(filas, json.loads(html.unescape(opciones.group("opciones"))) if opciones else {}))

    def svg(m: re.Match) -> str:
        # Los diagramas de estructuras (statics): 0.06 em por px (0.6 pt con letra de 10), así crecen
        # con la letra del examen, sin pasar del ancho disponible.
        ancho = _ANCHO_SVG.search(m.group("attrs"))
        alto = _ALTO_SVG.search(m.group("attrs"))
        # Un diagrama PlantUML puede traer su posición y sus límites, que achican pero no agrandan.
        datos = _OPCIONES_TABLA.search(m.group("attrs"))
        opciones = json.loads(html.unescape(datos.group("opciones"))) if datos else {}
        if ancho:
            px = float(ancho.group("px"))
            limites = [f"({px * 0.06:.1f}em).to-absolute()", "disponible.width"]
            if "ancho" in opciones:
                limites.append(_limite(opciones["ancho"], "disponible.width"))
            if "alto" in opciones and alto:
                limites.append(f"{_limite(opciones['alto'], 'page.height')} * {px / float(alto.group('px')):.4f}")
            medida = f"width: calc.min({', '.join(limites)})"
        else:
            medida = "width: 100%"
        posicion = {"izquierda": "left", "derecha": "right"}.get(opciones.get("posicion", ""), "center")
        return apartar(f"\n#layout(disponible => align({posicion}, image(bytes({_cadena(m.group(0))}), "
                       f"format: \"svg\", {medida})))\n")

    def formula(m: re.Match) -> str:
        typst = _TYPST_MATH.search(m.group("attrs"))
        if not typst:  # MathML que no pasó por matematica.py (Moodle): queda su texto
            return html.escape(_texto_plano(m.group(0)))
        contenido = html.unescape(typst.group("typst"))
        return apartar(f"$ {contenido} $" if 'display="block"' in m.group("attrs") else f"${contenido}$")

    texto = _SVG.sub(svg, texto)
    texto = _TABLA.sub(tabla, texto)
    texto = _MATH.sub(formula, texto)
    texto = _PRE.sub(bloque_pre, texto)
    texto = _FENCE.sub(bloque_fence, texto)
    texto = _CODE.sub(lambda m: apartar(f"#raw({_cadena(_texto_plano(m.group('codigo')))})"), texto)

    salida: list = []
    ultimo = 0
    for m in _ETIQUETA.finditer(texto):
        salida.append(escapar(html.unescape(texto[ultimo:m.start()])))
        cierra, nombre = m.group(1) == "/", m.group(2).lower()
        if nombre in ("strong", "b"):
            salida.append("]" if cierra else "#strong[")
        elif nombre in ("em", "i"):
            salida.append("]" if cierra else "#emph[")
        elif nombre == "br":
            salida.append(" \\\n")
        elif re.fullmatch(r"h[1-6]", nombre):
            salida.append("]\n\n" if cierra else "\n\n#strong[")
        elif nombre == "li" and not cierra:
            salida.append("\n- ")
        elif nombre in ("p", "div", "li", "ul", "ol") and cierra:
            salida.append("\n\n")
        ultimo = m.end()
    salida.append(escapar(html.unescape(texto[ultimo:])))
    resultado = "".join(salida)
    # Los bloques apartados (sus \x00N\x00 no tienen caracteres que escapar).
    resultado = re.sub(r"\x00(\d+)\x00", lambda m: bloques[int(m.group(1))], resultado)
    return re.sub(r"\n{3,}", "\n\n", resultado).strip()


def letra(indice: int) -> str:
    return chr(ord("A") + indice)


def largo_visible(fragmento: object) -> int:
    """Cuántos caracteres se ven de un fragmento HTML (para decidir las columnas de las opciones);
    un bloque de código cuenta como largo."""
    texto = "" if fragmento is None else str(fragmento)
    if re.search(r"<pre\b|```|\n", texto):
        return 1000
    return len(html.unescape(re.sub(r"<[^>]+>", "", texto)).strip())
