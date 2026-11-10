"""Tablas en un bloque ```tabla, con su presentación en el PDF.

```tabla
// [centrado] [ancho, 80%]
// [columnas, auto, 1fr] [alinear, izquierda, centro]
| Paso | Valor |
|---|---|
| `[M1]` |  |
```

Las opciones van en comentarios, entre corchetes: Moodle descarta esos renglones y muestra la tabla
como un bloque de código, sin confundirla con la sintaxis de GIFT. Una opción desconocida o que no
coincide con las columnas es un error, para que no se pierda sin avisar.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from typing import Any, Callable, Dict, List, Tuple

_MEDIDA = r"\d+(?:\.\d+)?(?:pt|mm|cm|em|%)"
_COLUMNA = rf"auto|\d+(?:\.\d+)?fr|{_MEDIDA}"
POSICIONES = ("centrado", "izquierda", "derecha")
BANDERAS = ("sin-encabezado", "sombrear-encabezado", "cebra")
ALINEACIONES = {"izquierda": "left", "centro": "center", "derecha": "right"}
BORDES = ("todos", "horizontales", "ninguno")
MEDIDAS = ("ancho", "alto", "relleno", "letra")

_FENCE = re.compile(r"^(?P<valla>`{3,}|~{3,})[ \t]*tabla[ \t]*\n(?P<cuerpo>.*?)^(?P=valla)[ \t]*$", re.S | re.M)
# El parser de GIFT descarta los comentarios: los de una tabla pasan con esta marca, del área de uso
# privado de Unicode.
_MARCA = ""
_COMENTARIO = re.compile(rf"^[ \t]*(?://|{_MARCA})(?P<texto>.*)$", re.M)
_OPCION = re.compile(r"\[([^\]]*)\]")
_CON_COMENTARIOS = re.compile(r"^(?P<valla>`{3,}|~{3,})[ \t]*tabla[ \t]*\n.*?^(?P=valla)[ \t]*$", re.S | re.M)



_CELDA_MOODLE = "border:1px solid #888;padding:0.25em 0.5em;min-width:4em;text-align:left"


class ErrorTabla(ValueError):
    """Un bloque ```tabla que no se puede interpretar."""


def _opcion(texto: str, opciones: Dict[str, Any]) -> None:
    nombre, valor = (re.split(r"[,:]", texto, maxsplit=1) + [""])[:2]
    nombre, valor = nombre.strip(), valor.strip()
    if nombre in POSICIONES:
        opciones["posicion"] = nombre
    elif nombre in BANDERAS:
        opciones[nombre] = True
    elif nombre in MEDIDAS:
        if not re.fullmatch(_MEDIDA, valor):
            raise ErrorTabla(f"[{texto}]: se espera una medida, como 80%, 12cm o 2em")
        opciones[nombre] = valor
    elif nombre == "bordes":
        if valor not in BORDES:
            raise ErrorTabla(f"[{texto}]: los bordes son {', '.join(BORDES)}")
        opciones[nombre] = valor
    elif nombre == "columnas":
        valores = [v.strip() for v in valor.split(",")]
        if not all(re.fullmatch(_COLUMNA, v) for v in valores):
            raise ErrorTabla(f"[{texto}]: cada columna es auto, una fracción como 2fr o una medida")
        opciones[nombre] = valores
    elif nombre == "alinear":
        valores = [v.strip() for v in valor.split(",")]
        if not all(v in ALINEACIONES for v in valores):
            raise ErrorTabla(f"[{texto}]: cada columna se alinea a {', '.join(ALINEACIONES)}")
        opciones[nombre] = [ALINEACIONES[v] for v in valores]
    else:
        raise ErrorTabla(f"opción desconocida [{texto}]")


def _leer(cuerpo: str) -> Tuple[Dict[str, Any], str]:
    """Las opciones de un bloque y su tabla, sin los comentarios."""
    opciones: Dict[str, Any] = {}
    for comentario in _COMENTARIO.finditer(cuerpo):
        for texto in _OPCION.findall(comentario.group("texto")):
            _opcion(texto, opciones)
    return opciones, _COMENTARIO.sub("", cuerpo).strip("\n")


def tabla_a_html(cuerpo: str, a_html: Callable[[str], str]) -> str:
    """El HTML de un bloque, con sus opciones en `data-opciones` para el PDF."""
    opciones, tabla = _leer(cuerpo)
    resultado = a_html(tabla)
    if "<table>" not in resultado:
        raise ErrorTabla("no hay una tabla: necesita un encabezado y un renglón |---|---|")
    columnas = len(re.findall(r"<th[ >]", resultado))
    for nombre in ("columnas", "alinear"):
        if nombre in opciones and len(opciones[nombre]) != columnas:
            raise ErrorTabla(f"[{nombre}] tiene {len(opciones[nombre])} valores y la tabla {columnas} columnas")
    if not opciones:
        return resultado
    datos = html.escape(json.dumps(opciones), quote=True)
    return resultado.replace("<table>", f'<table data-opciones="{datos}">', 1)


def tabla_a_moodle(cuerpo: str, a_html: Callable[[str], str]) -> str:
    """Un bloque como una tabla HTML en un solo renglón, con los bordes en línea: Moodle no aplica
    nuestros estilos, y en un campo Markdown un renglón en blanco cortaría el bloque."""
    resultado = re.sub(r"<table[^>]*>", '<table style="border-collapse:collapse">', tabla_a_html(cuerpo, a_html))
    resultado = re.sub(r"<(t[hd])\b[^>]*>", rf'<\1 style="{_CELDA_MOODLE}">', resultado)
    resultado = re.sub(r"(<td[^>]*>)(</td>)", r"\1&nbsp;\2", resultado)
    return re.sub(r">\s+<", "><", resultado).strip()


def expandir_tablas(texto: str, a_html: Callable[[str], str]) -> Tuple[str, Dict[str, str]]:
    """Reemplaza los bloques por marcadores; devuelve el texto y el HTML de cada marcador."""
    tablas: Dict[str, str] = {}

    def reemplazar(m: re.Match) -> str:
        marcador = f"TABLA{len(tablas)}X{hashlib.sha1(m.group(0).encode()).hexdigest()[:8]}"
        try:
            tablas[marcador] = tabla_a_html(m.group("cuerpo"), a_html)
        except ErrorTabla as e:
            tablas[marcador] = f'<p class="tabla-error"><strong>Tabla inválida:</strong> {html.escape(str(e))}</p>'
        return f"\n\n{marcador}\n\n"

    return _FENCE.sub(reemplazar, texto), tablas


def proteger_comentarios(contenido: str) -> str:
    """Para que los comentarios de las tablas sobrevivan al parser de GIFT."""
    def proteger(m: re.Match) -> str:
        return re.sub(r"^([ \t]*)//", rf"\g<1>{_MARCA}", m.group(0), flags=re.M)

    return _CON_COMENTARIOS.sub(proteger, contenido)


def errores_en_texto(contenido: str, a_html: Callable[[str], str]) -> List[Tuple[int, str]]:
    """(posición, motivo) de cada bloque inválido de un texto, para `lint-gift`."""
    errores = []
    for m in _FENCE.finditer(contenido):
        try:
            tabla_a_html(m.group("cuerpo"), a_html)
        except ErrorTabla as e:
            errores.append((m.start(), str(e)))
    return errores
