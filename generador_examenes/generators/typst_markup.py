"""HTML de las preguntas → marcado Typst, para las plantillas PDF (`|typst`, Ola 14).

Los enunciados y opciones llegan como HTML (el Moodle XML de idkfa, o el GIFT ya convertido): tal
cual, Typst mostraba las etiquetas (`</code></p>`) e interpretaba como marcado los `*`, `_`, `#`, `$`
o el `//` de una URL (que abre un comentario). Acá cada bloque `<pre>` pasa a `#raw(block: true)` con
su lenguaje, `<code>` a `#raw(...)`, `<strong>`/`<b>` y `<em>`/`<i>` a `#strong[...]`/`#emph[...]`,
los párrafos y `<br>` a saltos, y el resto del texto se escapa. Las demás etiquetas se quitan.
"""
from __future__ import annotations

import html
import re

_ESPECIALES = re.compile(r"([\\#$*_`<>@\[\]~/=+\-])")
_ETIQUETA = re.compile(r"<(/?)([a-zA-Z0-9]+)\b[^>]*?>", re.S)
_PRE = re.compile(r"<pre\b[^>]*>(?:\s*<code\b(?P<attrs>[^>]*)>)?(?P<codigo>.*?)(?:</code>\s*)?</pre>", re.S | re.I)
_FENCE = re.compile(r"```(?P<lang>[\w+#-]*)\n(?P<codigo>.*?)```", re.S)
_CODE = re.compile(r"<code\b[^>]*>(?P<codigo>.*?)</code>", re.S | re.I)
_LENGUAJE = re.compile(r"language-([\w+#-]+)")


def _cadena(texto: str) -> str:
    """Un literal de cadena de Typst."""
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'


def _texto_plano(fragmento: str) -> str:
    """El contenido de un bloque de código: sin etiquetas (p. ej. el resaltado de voight) y sin entidades."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


def escapar(texto: str) -> str:
    return _ESPECIALES.sub(r"\\\1", texto)


def html_a_typst(fragmento: object) -> str:
    """El HTML (o texto) de una pregunta como marcado Typst."""
    texto = ("" if fragmento is None else str(fragmento)).replace("\r\n", "\n").replace("\r", "\n")
    bloques: list = []

    def apartar(contenido: str) -> str:
        bloques.append(contenido)
        return f"\x00{len(bloques) - 1}\x00"

    def bloque_pre(m: re.Match) -> str:
        lenguaje = _LENGUAJE.search(m.group("attrs") or "")
        codigo = _texto_plano(m.group("codigo")).strip("\n")
        lang = f', lang: "{lenguaje.group(1)}"' if lenguaje else ""
        return apartar(f"\n#raw(block: true{lang}, {_cadena(codigo)})\n")

    def bloque_fence(m: re.Match) -> str:
        lang = f', lang: "{m.group("lang")}"' if m.group("lang") else ""
        return apartar(f"\n#raw(block: true{lang}, {_cadena(_texto_plano(m.group('codigo')).rstrip())})\n")

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
