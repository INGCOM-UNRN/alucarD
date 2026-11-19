"""Diagramas SVG de estructuras de datos, con el formato de bloques de statics.

Porta a Python los renderizadores de statics (`estructuras.html`: arreglo, lista enlazada simple,
doble y circular, pila, cola lineal y circular, tabla de traza) y suma matrices (estáticas, con su
disposición en memoria, dinámicas como arreglo de punteros a filas, dentadas y planas), árboles
(binario, ABB, AVL con factor de balance y montículo), la pila y el árbol de llamadas, structs (offsets,
relleno y tipos opacos), TADs, curvas y clases de complejidad, diagramas de flujo y tablas de costos,
para usarlos en preguntas y consignas sin navegador.

Un bloque es un diccionario con las mismas claves que statics (`type`, `values`, `variant`,
`capacity`…), así que un bloque exportado de statics se puede pegar tal cual. En Markdown va en un
bloque de código ```` ```estructura ```` con el bloque en YAML o JSON::

    ```estructura
    type: linked_list
    variant: doubly
    values: [10, 20, 30]
    ```

`renderizar(bloque)` devuelve el `<svg>`; `expandir_en_markdown(texto)` reemplaza esos bloques.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

MONO = "DejaVu Sans Mono, Menlo, Consolas, Courier New, monospace"
SANS = "DejaVu Sans, Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif"

# Paletas de statics: `tinta` (ahorro de tinta, para imprimir) y color.
PALETAS = {
    True: {"strokeMain": "#000000", "strokeSub": "#334155", "strokeMuted": "#64748b", "fillHeader": "#f8fafc",
           "fillCell": "#ffffff", "fillPointerBox": "#f1f5f9", "fillBadge": "#ffffff", "accentPrimary": "#000000",
           "textMain": "#000000", "textSub": "#334155", "textMuted": "#475569", "fillHighlight": "#e2e8f0"},
    False: {"strokeMain": "#0f172a", "strokeSub": "#1e40af", "strokeMuted": "#64748b", "fillHeader": "#eff6ff",
            "fillCell": "#ffffff", "fillPointerBox": "#e0f2fe", "fillBadge": "#dbeafe", "accentPrimary": "#1d4ed8",
            "textMain": "#0f172a", "textSub": "#1e3a8a", "textMuted": "#475569", "fillHighlight": "#fef3c7"},
}

TIPOS = ("array", "matrix", "linked_list", "stack", "call_stack", "call_tree", "queue", "tree", "struct", "adt",
         "complexity", "flowchart", "cost_table", "trace_table")


class ErrorDiagrama(ValueError):
    """Un bloque que no se puede dibujar (tipo desconocido, datos inválidos)."""


def _esc(valor: Any) -> str:
    return html.escape("" if valor is None else str(valor), quote=True)


def _hex(texto: Any, defecto: int = 0x1000) -> int:
    if isinstance(texto, int) and not isinstance(texto, bool):
        return texto  # YAML lee 0x7FF0 como entero
    try:
        return int(str(texto).strip().lower().removeprefix("0x"), 16)
    except (TypeError, ValueError):
        return defecto


def _fmt_hex(numero: int) -> str:
    return "0x" + format(max(0, numero), "X").rjust(4, "0")


def _entero(valor: Any, defecto: int, minimo: int, maximo: int) -> int:
    try:
        n = int(valor)
    except (TypeError, ValueError):
        n = defecto
    return max(minimo, min(maximo, n))


def _valores(bloque: Dict[str, Any]) -> List[str]:
    return ["" if v is None else str(v) for v in bloque.get("values") or []]


@dataclass
class _Lienzo:
    """Las piezas de un SVG y su paleta; `t()` y `r()` escriben texto y rectángulos."""

    pal: Dict[str, str]
    sufijo: str
    partes: List[str] = field(default_factory=list)
    ancho_min: float = 0  # lo que ocupan el título y el subtítulo, para no cortarlos

    def add(self, *piezas: str) -> None:
        self.partes.extend(piezas)

    def t(self, x: float, y: float, texto: Any, size: float = 10, peso: int = 400, color: str = "textMain",
          ancla: str = "start", fuente: str = MONO) -> None:
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancla}" font-family="{fuente}" font-size="{size}" '
                 f'font-weight="{peso}" fill="{self.pal[color]}">{_esc(texto)}</text>')

    def r(self, x: float, y: float, w: float, h: float, relleno: str = "fillCell", trazo: float = 1.5,
          rx: float = 0) -> None:
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                 f'fill="{self.pal[relleno]}" stroke="{self.pal["strokeMain"]}" stroke-width="{trazo}"/>')

    def linea(self, x1: float, y1: float, x2: float, y2: float, color: str = "accentPrimary", ancho: float = 1.6,
              flecha: Optional[str] = "main", guiones: str = "") -> None:
        marca = f' marker-end="url(#flecha-{flecha}-{self.sufijo})"' if flecha else ""
        dash = f' stroke-dasharray="{guiones}"' if guiones else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{self.pal[color]}" '
                 f'stroke-width="{ancho}"{dash}{marca}/>')

    def vacio(self, x1: float, x2: float, y: float) -> None:
        """La raya punteada de una celda sin valor (para completar)."""
        self.linea(x1, y, x2, y, color="strokeMuted", ancho=1, flecha=None, guiones="3 2")

    def ruta(self, *puntos: Tuple[float, float]) -> None:
        """Una flecha con codos."""
        camino = " L ".join(f"{x:.1f} {y:.1f}" for x, y in puntos)
        self.add(f'<path d="M {camino}" fill="none" stroke="{self.pal["accentPrimary"]}" stroke-width="1.6" '
                 f'marker-end="url(#flecha-main-{self.sufijo})"/>')

    def punto(self, x: float, y: float, color: str = "accentPrimary", radio: float = 3.2) -> None:
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio}" fill="{self.pal[color]}"/>')

    def null(self, x: float, y: float) -> None:
        """El símbolo de tierra de NULL que usa statics."""
        self.linea(x, y - 10, x, y + 10, color="strokeMain", ancho=2, flecha=None)
        self.linea(x + 5, y - 6, x + 5, y + 6, color="strokeMain", ancho=1.5, flecha=None)
        self.t(x + 12, y + 4, "NULL", size=10, peso=700, color="textMuted")


@dataclass
class _CampoCabecera:
    """Un renglón de una estructura cabecera: un valor o un puntero a otra parte del dibujo."""
    nombre: str
    valor: str = ""
    destino: Any = None


FILA_CABECERA = 26


def _campos_cabecera(cabecera: Any, donde: str) -> List[_CampoCabecera]:
    """`"cant = 4"`, `"primero -> 0"` o `{name, value, to}`."""
    if not isinstance(cabecera, dict) or not isinstance(cabecera.get("fields"), list) or not cabecera["fields"]:
        raise ErrorDiagrama(f"'{donde}' necesita 'fields', la lista de sus campos")
    campos = []
    for dato in cabecera["fields"]:
        if isinstance(dato, dict) and dato.get("name"):
            campos.append(_CampoCabecera(str(dato["name"]), _texto(dato.get("value")), dato.get("to")))
        elif isinstance(dato, str) and "->" in dato:
            nombre, _, destino = dato.partition("->")
            campos.append(_CampoCabecera(nombre.strip(), destino=destino.strip()))
        elif isinstance(dato, str) and "=" in dato:
            nombre, _, valor = dato.partition("=")
            campos.append(_CampoCabecera(nombre.strip(), valor.strip()))
        else:
            raise ErrorDiagrama(f"'{donde}': campo inválido {dato!r} (se espera 'x = 5', 'p -> destino' o name/value/to)")
    return campos


def _titulo_cabecera(cabecera: Dict[str, Any]) -> str:
    nombre, tipo = cabecera.get("name") or "", cabecera.get("type")
    return f"{nombre} ({tipo})" if tipo else str(nombre)


def _ancho_cabecera(cabecera: Dict[str, Any], campos: List[_CampoCabecera], valores: List[str]) -> float:
    nombres = max(len(campo.nombre) for campo in campos) * 7.4 + 16
    return max(nombres + max(max(len(v) for v in valores) * 8 + 18, 44), len(_titulo_cabecera(cabecera)) * 7 + 8)


def _cabecera(c: _Lienzo, x: float, y: float, ancho: float, cabecera: Dict[str, Any], campos: List[_CampoCabecera],
              valores: List[str]) -> List[float]:
    """Dibuja la estructura con su primer renglón en `y`; devuelve el centro de cada renglón."""
    c.t(x, y - 6, _titulo_cabecera(cabecera), size=10.5, peso=700)
    nombres = max(len(campo.nombre) for campo in campos) * 7.4 + 16
    centros = []
    for i, (campo, valor) in enumerate(zip(campos, valores, strict=True)):
        fila = y + i * FILA_CABECERA
        c.r(x, fila, ancho, FILA_CABECERA, relleno="fillPointerBox" if campo.destino is not None else "fillCell")
        c.linea(x + nombres, fila, x + nombres, fila + FILA_CABECERA, color="strokeMain", ancho=1, flecha=None)
        c.t(x + 8, fila + 17, campo.nombre, size=11)
        c.t(x + (nombres + ancho) / 2, fila + 17, valor, size=11.5, peso=700, ancla="middle")
        centros.append(fila + FILA_CABECERA / 2)
    return centros


def _nombres_de_zonas(b: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """`zones: true` o `zones` con `stack` y `heap`, los títulos de cada zona."""
    zonas = b.get("zones")
    if not zonas:
        return None
    propios = zonas if isinstance(zonas, dict) else {}
    return str(propios.get("stack") or "Stack"), str(propios.get("heap") or "Heap")


ALTO_ZONA = 20


def _zona(c: _Lienzo, x1: float, x2: float, y1: float, y2: float, titulo: str) -> None:
    c.add(f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{x2 - x1:.1f}" height="{y2 - y1:.1f}" rx="4" fill="none" '
          f'stroke="{c.pal["strokeMuted"]}" stroke-width="1" stroke-dasharray="5 3"/>')
    c.t(x1 + 6, y1 + 13, titulo, size=10, peso=700, color="textSub", fuente=SANS)


def _encabezado(c: _Lienzo, bloque: Dict[str, Any], extra: str = "") -> float:
    """Título y subtítulo (si el bloque los trae); devuelve dónde empieza el dibujo."""
    titulo, subtitulo = bloque.get("title"), bloque.get("subtitle")
    if not titulo and not subtitulo and not extra:
        return 0
    if titulo:
        c.t(0, 16, titulo, size=14, peso=700, fuente=SANS)
        c.ancho_min = max(c.ancho_min, len(str(titulo)) * 8.6)
    texto = " | ".join(p for p in (subtitulo, extra) if p)
    if texto:
        c.t(0, 32 if titulo else 14, texto, size=10.5, color="textMuted")
        c.ancho_min = max(c.ancho_min, len(texto) * 6.4)
    return 40 if titulo else 22


# ---------------------------------------------------------------------------
# Arreglo
# ---------------------------------------------------------------------------

def _punteros(b: Dict[str, Any], limite: int) -> Dict[int, List[str]]:
    """`pointers: "p:0, q:3"` como {índice: [etiquetas]}."""
    punteros: Dict[int, List[str]] = {}
    for par in str(b.get("pointers") or "").split(","):
        etiqueta, _, idx = par.partition(":")
        if idx.strip().isdigit() and int(idx) < limite:
            punteros.setdefault(int(idx), []).append(etiqueta.strip())
    return punteros


def _arreglo(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    valores = _valores(b)
    cap = _entero(b.get("capacity", len(valores) or 8), 8, 1, 16)
    base, paso = _hex(b.get("baseAddr")), _entero(b.get("typeSize"), 4, 1, 64)
    direcciones, offsets = bool(b.get("showAddresses")), bool(b.get("showOffsets"))
    indices = b.get("showIndices", True)
    top = _encabezado(c, b, f"Base: {_fmt_hex(base)} | sizeof: {paso}B" if direcciones else "")

    punteros = _punteros(b, cap)

    x0, celda_w, celda_h = 78, 64, 54
    y = top + (64 if punteros else 30)
    if indices:
        c.t(x0 - 10, y - 8, "Índice [i]:", size=10, peso=600, color="textSub", ancla="end")
    c.t(x0 - 10, y + celda_h / 2 + 4, "Valor:", size=10.5, peso=700, ancla="end")
    if direcciones:
        c.t(x0 - 10, y + celda_h + 17, "Dirección:", size=10, peso=600, color="textSub", ancla="end")
    if offsets:
        c.t(x0 - 10, y + celda_h + 32, "Offset:", size=9.5, color="textMuted", ancla="end")

    for i in range(cap):
        cx = x0 + i * celda_w
        centro = cx + celda_w / 2
        if i in punteros:
            texto = ", ".join(punteros[i])
            ancho = max(40, len(texto) * 7.5 + 12)
            c.r(centro - ancho / 2, y - 48, ancho, 18, relleno="fillBadge", trazo=1.2, rx=3)
            c.t(centro, y - 35, texto, size=10, peso=700, ancla="middle")
            c.linea(centro, y - 30, centro, y - 19, ancho=1.5)
        if indices:
            c.t(centro, y - 7, f"[{i}]", size=11, peso=700, color="textSub", ancla="middle")
        c.r(cx, y, celda_w, celda_h, trazo=1.75)
        valor = valores[i] if i < len(valores) else ""
        if valor and not b.get("blankValues"):
            c.t(centro, y + celda_h / 2 + 5, valor, size=15, peso=700, ancla="middle")
        else:
            c.vacio(cx + 10, cx + celda_w - 10, y + celda_h - 12)
        if direcciones:
            c.t(centro, y + celda_h + 17, "0x____" if b.get("blankAddrs") else _fmt_hex(base + i * paso),
                size=10, peso=600, color="textSub", ancla="middle")
        if offsets:
            c.t(centro, y + celda_h + 32, f"+{i * paso}B", size=9, color="textMuted", ancla="middle")

    alto = y + celda_h + (42 if offsets else 26 if direcciones else 12)
    return x0 + cap * celda_w + 20, alto


# ---------------------------------------------------------------------------
# Matriz: estática (int m[F][C], row-major) y dinámica (int **m, punteros a filas)
# ---------------------------------------------------------------------------

MAX_FILAS, MAX_COLUMNAS = 10, 10
MAX_CELDAS_PLANA = 24  # en una sola línea, para que se vea que es un bloque contiguo


def _dimension(b: Dict[str, Any], clave: str, defecto: int, maximo: int) -> int:
    """`rows`/`cols` del bloque (o `defecto`), entre 1 y `maximo`; si no, un error."""
    valor = b.get(clave)
    if valor is None:
        valor = defecto
    try:
        n = int(valor)
    except (TypeError, ValueError):
        raise ErrorDiagrama(f"'{clave}' de una matriz tiene que ser un entero: {valor!r}") from None
    if not 1 <= n <= maximo:
        raise ErrorDiagrama(f"'{clave}' de una matriz tiene que estar entre 1 y {maximo}: {n}")
    return n


def _filas(b: Dict[str, Any]) -> List[Optional[List[str]]]:
    """Las filas del bloque: `values` como lista de filas, o plana y cortada en `cols`.

    Una fila `null` es un puntero a NULL (sólo tiene sentido en la variante dinámica).
    """
    valores = b.get("values") or []
    if not isinstance(valores, list):
        raise ErrorDiagrama("'values' de una matriz tiene que ser una lista de filas")
    if valores and not any(isinstance(v, list) for v in valores):  # plana: se corta en `cols`
        cols = _dimension(b, "cols", min(len(valores), MAX_COLUMNAS), MAX_COLUMNAS)
        valores = [valores[i:i + cols] for i in range(0, len(valores), cols)]
    if len(valores) > MAX_FILAS:
        raise ErrorDiagrama(f"la matriz tiene {len(valores)} filas; el máximo es {MAX_FILAS}")
    filas: List[Optional[List[str]]] = []
    for i, fila in enumerate(valores):
        if fila is None:
            filas.append(None)
        elif isinstance(fila, list):
            if len(fila) > MAX_COLUMNAS:
                raise ErrorDiagrama(f"la fila {i} de la matriz tiene {len(fila)} columnas; "
                                    f"el máximo es {MAX_COLUMNAS}")
            filas.append(["" if v is None else str(v) for v in fila])
        else:
            raise ErrorDiagrama("cada fila de una matriz tiene que ser una lista (o null)")
    return filas


def _pares(valor: Any) -> set:
    """Celdas `(i, j)` de `highlight`: `[[0, 1], [2, 2]]` o `"0,1; 2,2"`."""
    if isinstance(valor, str):
        valor = [p.split(",") for p in valor.split(";") if p.strip()]
    celdas = set()
    for par in valor or []:
        try:
            i, j = (int(str(x).strip()) for x in par)
        except (TypeError, ValueError):
            raise ErrorDiagrama(f"celda de 'highlight' inválida: {par!r} (se espera [fila, columna])") from None
        celdas.add((i, j))
    return celdas


def _matriz(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    variante = b.get("variant", "static")
    if variante in ("dynamic", "pointers", "jagged"):
        return _matriz_dinamica(c, b, dentada=variante == "jagged")
    if variante == "flat":
        return _matriz_plana(c, b)
    if variante != "static":
        raise ErrorDiagrama(f"variante de matriz no soportada: {variante!r} (static, dynamic, jagged o flat)")
    filas = [f or [] for f in _filas(b)]
    nf = _dimension(b, "rows", len(filas) or 3, MAX_FILAS)
    nc = _dimension(b, "cols", max((len(f) for f in filas), default=0) or 3, MAX_COLUMNAS)
    base, paso = _hex(b.get("baseAddr")), _entero(b.get("typeSize"), 4, 1, 64)
    nombre, tipo = b.get("name") or "m", b.get("elementType") or "int"
    direcciones, indices = bool(b.get("showAddresses")), b.get("showIndices", True)
    sin_valores, sin_dirs = bool(b.get("blankValues")), bool(b.get("blankAddrs"))
    resaltadas = _pares(b.get("highlight"))
    filas_r, cols_r = set(b.get("highlightRows") or []), set(b.get("highlightCols") or [])
    extra = f"{tipo} {nombre}[{nf}][{nc}]"
    if direcciones:
        extra += f" | Base: {_fmt_hex(base)} | sizeof: {paso}B"
    top = _encabezado(c, b, extra)

    x0, celda_w, celda_h = 46, 64, 50 if direcciones else 42
    y0 = top + (26 if indices else 8)

    def valor(i: int, j: int) -> str:
        return filas[i][j] if i < len(filas) and j < len(filas[i]) else ""

    for j in range(nc):
        if indices:
            c.t(x0 + j * celda_w + celda_w / 2, y0 - 8, f"[{j}]", size=11, peso=700, color="textSub",
                ancla="middle")
    for i in range(nf):
        y = y0 + i * celda_h
        if indices:
            c.t(x0 - 8, y + celda_h / 2 + 4, f"[{i}]", size=11, peso=700, color="textSub", ancla="end")
        for j in range(nc):
            x = x0 + j * celda_w
            marcada = (i, j) in resaltadas or i in filas_r or j in cols_r
            c.r(x, y, celda_w, celda_h, relleno="fillHighlight" if marcada else "fillCell", trazo=1.5)
            v = valor(i, j)
            centro_v = y + (celda_h / 2 - 2 if direcciones else celda_h / 2 + 5)
            if v and not sin_valores:
                c.t(x + celda_w / 2, centro_v, v, size=14, peso=700, ancla="middle")
            else:
                c.vacio(x + 10, x + celda_w - 10, centro_v + 3)
            if direcciones:
                c.t(x + celda_w / 2, y + celda_h - 7, "0x____" if sin_dirs else _fmt_hex(base + (i * nc + j) * paso),
                    size=9, color="textMain", ancla="middle")
    # Borde exterior más grueso: la matriz es un único bloque contiguo.
    c.add(f'<rect x="{x0}" y="{y0:.1f}" width="{nc * celda_w}" height="{nf * celda_h}" fill="none" '
          f'stroke="{c.pal["strokeMain"]}" stroke-width="2.25"/>')
    ancho, alto = x0 + nc * celda_w + 12, y0 + nf * celda_h + 8

    if b.get("showLinear"):
        # La misma matriz en memoria: fila tras fila (row-major), con su índice [i][j].
        lw, lh = 52, 36
        y = alto + 34
        c.t(0, y - 22, f"En memoria (fila por fila): {nombre}[i][j] = *(&{nombre}[0][0] + i*{nc} + j)", size=10,
            color="textMuted")
        for k in range(nf * nc):
            i, j = divmod(k, nc)
            x = k * lw
            marcada = (i, j) in resaltadas or i in filas_r or j in cols_r
            c.t(x + lw / 2, y - 5, f"[{i}][{j}]", size=9, color="textMain", ancla="middle")
            c.r(x, y, lw, lh, relleno="fillHighlight" if marcada else "fillCell", trazo=1.25)
            v = valor(i, j)
            if v and not sin_valores:
                c.t(x + lw / 2, y + lh / 2 + 5, v, size=13, peso=700, ancla="middle")
            else:
                c.vacio(x + 8, x + lw - 8, y + lh - 9)
            if direcciones:
                c.t(x + lw / 2, y + lh + 13, "0x____" if sin_dirs else _fmt_hex(base + k * paso), size=8.5,
                    color="textSub", ancla="middle")
        for i in range(1, nf):  # separador entre filas
            c.linea(i * nc * lw, y - 3, i * nc * lw, y + lh + 3, color="strokeMain", ancho=2.5, flecha=None)
        ancho = max(ancho, nf * nc * lw + 4)
        alto = y + lh + (20 if direcciones else 6)
    return ancho, alto


def _matriz_plana(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """`int *m = malloc(F * C * sizeof(int))`: un solo bloque, con `m[i * C + j]` como acceso."""
    filas = [f or [] for f in _filas(b)]
    nf = _dimension(b, "rows", len(filas) or 3, MAX_FILAS)
    nc = _dimension(b, "cols", max((len(f) for f in filas), default=0) or 3, MAX_COLUMNAS)
    if nf * nc > MAX_CELDAS_PLANA:
        raise ErrorDiagrama(f"la matriz plana tiene {nf * nc} celdas; el máximo es {MAX_CELDAS_PLANA}")
    base, paso = _hex(b.get("baseAddr")), _entero(b.get("typeSize"), 4, 1, 64)
    nombre, tipo = str(b.get("name") or "m"), b.get("elementType") or "int"
    direcciones, sin_valores = bool(b.get("showAddresses")), bool(b.get("blankValues"))
    sin_dirs, indices = bool(b.get("blankAddrs")), b.get("showIndices", True)
    coordenadas = b.get("showCoords", True)
    resaltadas = _pares(b.get("highlight"))
    filas_r, cols_r = set(b.get("highlightRows") or []), set(b.get("highlightCols") or [])
    top = _encabezado(c, b, f"{tipo} *{nombre} = malloc({nf} * {nc} * sizeof({tipo}))")

    m_w = max(56, math.ceil(len(nombre) * 8.5 + 14))
    x0, lw, lh, y = m_w + 56, 52, 40, top + 32
    c.t(m_w / 2, y - 8, nombre, size=12, peso=700, ancla="middle")
    c.r(0, y, m_w, lh, relleno="fillPointerBox", trazo=1.75, rx=3)
    c.punto(m_w / 2, y + lh / 2)
    c.linea(m_w / 2, y + lh / 2, x0 - 3, y + lh / 2, ancho=1.6)
    for k in range(nf * nc):
        i, j = divmod(k, nc)
        x = x0 + k * lw
        marcada = (i, j) in resaltadas or i in filas_r or j in cols_r
        if indices:
            c.t(x + lw / 2, y - 7, f"[{k}]", size=10, peso=700, color="textSub", ancla="middle")
        c.r(x, y, lw, lh, relleno="fillHighlight" if marcada else "fillCell", trazo=1.25)
        v = filas[i][j] if i < len(filas) and j < len(filas[i]) else ""
        if v and not sin_valores:
            c.t(x + lw / 2, y + lh / 2 + 5, v, size=13, peso=700, ancla="middle")
        else:
            c.vacio(x + 8, x + lw - 8, y + lh - 9)
        if coordenadas:
            c.t(x + lw / 2, y + lh + 13, f"({i},{j})", size=9, color="textMain", ancla="middle")
        if direcciones:
            c.t(x + lw / 2, y + lh + (26 if coordenadas else 13), "0x____" if sin_dirs else _fmt_hex(base + k * paso),
                size=8.5, color="textSub", ancla="middle")
    c.add(f'<rect x="{x0}" y="{y:.1f}" width="{nf * nc * lw}" height="{lh}" fill="none" '
          f'stroke="{c.pal["strokeMain"]}" stroke-width="2.25"/>')
    for i in range(1, nf):  # dónde empieza cada fila: en memoria no hay ninguna marca
        c.linea(x0 + i * nc * lw, y - 3, x0 + i * nc * lw, y + lh + 3, color="strokeMain", ancho=2.5, flecha=None)
    alto = y + lh + (13 if coordenadas else 0) + (13 if direcciones else 0) + 18
    ancho: float = x0 + nf * nc * lw + 6
    if b.get("showFormula", True):
        c.t(x0, alto, f"{nombre}[i * {nc} + j] es la celda (i, j)", size=10, color="textMuted")
        alto += 6
    if b.get("showLogical"):  # la misma matriz como la piensa el programa
        sub = _Lienzo(c.pal, c.sufijo)
        ancho_m, alto_m = _matriz(sub, {k: b[k] for k in ("values", "rows", "cols", "highlight", "highlightRows",
                                                          "highlightCols", "blankValues") if k in b}
                                  | {"subtitle": "Vista lógica"})
        c.add(f'<g transform="translate(0, {alto + 10:.1f})">', *sub.partes, "</g>")
        ancho, alto = max(ancho, ancho_m), alto + 10 + alto_m
    return ancho, alto


def _matriz_dinamica(c: _Lienzo, b: Dict[str, Any], dentada: bool = False) -> Tuple[float, float]:
    """`int **m`: el puntero, el arreglo de punteros a filas y cada fila (de largo propio, o NULL).

    `dentada` (variante `jagged`) dice además dónde termina cada fila, como en C: con el arreglo de
    largos (`showLengths`, por omisión) o con un valor centinela al final (`sentinel`).
    """
    filas = _filas(b)
    nf = _dimension(b, "rows", len(filas) or 3, MAX_FILAS)
    filas += [[] for _ in range(nf - len(filas))]
    nc_fijo = _dimension(b, "cols", 1, MAX_COLUMNAS) if b.get("cols") is not None else None
    nombre, tipo = b.get("name") or "m", b.get("elementType") or "int"
    direcciones, indices = bool(b.get("showAddresses")), b.get("showIndices", True)
    sin_valores, sin_dirs = bool(b.get("blankValues")), bool(b.get("blankAddrs"))
    resaltadas = _pares(b.get("highlight"))
    base = _hex(b.get("baseAddr"))
    dirs_filas = list(b.get("rowAddresses") or [])
    base_filas = _hex(b.get("rowsBaseAddr"), base + 0x40)
    centinela = b.get("sentinel") if dentada else None
    con_largos = dentada and b.get("showLengths", centinela is None)
    nombre_largos = b.get("lengthsName") or "largos"
    tipo_largos = b.get("lengthsType") or "size_t"
    extra = f"{tipo} **{nombre}"
    if con_largos:
        extra += f" | {tipo_largos} {nombre_largos}[{nf}]"
    if centinela is not None:
        extra += f" | centinela: {centinela}"
    zonas = _nombres_de_zonas(b)
    inicio = _encabezado(c, b, extra)
    top = inicio + (ALTO_ZONA if zonas else 0)

    def direccion(valor: Any, hexadecimal: int) -> str:
        """`@M` queda como está: en un examen, las direcciones suelen ser simbólicas."""
        if sin_dirs:
            return "0x____"
        return valor if isinstance(valor, str) and valor.startswith("@") else _fmt_hex(hexadecimal)

    def dir_fila(i: int) -> str:
        return direccion(dirs_filas[i], _hex(dirs_filas[i])) if i < len(dirs_filas) else direccion(None, base_filas + i * 0x40)

    dir_base = direccion(b.get("baseAddr"), base)
    dir_largos = b.get("lengthsAddr")

    largos = [0 if f is None else nc_fijo if nc_fijo else len(f)
              for f in filas[:nf]]
    celda_w, celda_h, paso_y = 56, 40, 54
    # Las cajas crecen con el nombre (`palabras[0]` no entra en una de 52).
    ptr_w = max(72 if direcciones else 52, math.ceil(len(f"{nombre}[{nf - 1}]") * 6.2 + 14))
    m_w = max(56, math.ceil(len(str(nombre)) * 8.5 + 14))
    largos_w = max(64, math.ceil(len(str(nombre_largos)) * 8.5 + 14)) if con_largos else 0
    x_m = largos_w + (36 if con_largos else 0)
    # Una estructura dueña en lugar del puntero: `d.filas` apunta a las filas y `d.largos`, a los largos,
    # que ya no están en el stack: van arriba del arreglo de punteros, en el heap.
    dueno = b.get("owner")
    campos = _campos_cabecera(dueno, "owner") if dueno is not None else []
    valores_dueno: List[str] = []
    for campo in campos:
        if campo.destino not in (None, "rows", "lengths") or (campo.destino == "lengths" and not con_largos):
            raise ErrorDiagrama(f"'owner': {campo.nombre} apunta a {campo.destino!r} (se espera rows, o lengths con largos)")
        if campo.destino is None:
            valores_dueno.append(campo.valor)
        elif campo.destino == "lengths":
            valores_dueno.append(direccion(dir_largos, _hex(dir_largos)) if dir_largos else "")
        else:
            valores_dueno.append(dir_base if direcciones else "")
    if dueno is not None:
        m_w = math.ceil(_ancho_cabecera(dueno, campos, valores_dueno))
        largos_w = x_m = 0
    x_ptr = x_m + m_w + (72 if dueno is not None else 56)
    x_filas = x_ptr + ptr_w + 70
    y0 = top + (44 if indices and any(largos) else 30)
    largo_w, largo_h = 44, 30
    y_largos = top + 22
    if dueno is not None and con_largos:
        y0 = y_largos + largo_h + 56

    declarados = list(b.get("lengths") or [])
    if dueno is not None:
        if con_largos:
            c.t(x_ptr, y_largos - 6, " ".join(p for p in (dir_largos, f"({nombre_largos}: {tipo_largos}[{nf}])") if p),
                size=10.5, peso=700)
            for i in range(nf):
                x = x_ptr + i * largo_w
                c.r(x, y_largos, largo_w, largo_h, trazo=1.5)
                c.t(x + largo_w / 2, y_largos + largo_h + 13, f"[{i}]", size=10, color="textMain", ancla="middle")
                if b.get("blankLengths"):
                    c.vacio(x + 8, x + largo_w - 8, y_largos + largo_h - 8)
                else:
                    c.t(x + largo_w / 2, y_largos + 20, declarados[i] if i < len(declarados) else largos[i], size=13,
                        peso=700, ancla="middle")
        # El campo que apunta a las filas queda a la altura de la primera: la flecha va derecha.
        fila_filas = next((i for i, campo in enumerate(campos) if campo.destino == "rows"), 0)
        y_dueno = max(top + 22, y0 + celda_h / 2 - FILA_CABECERA / 2 - fila_filas * FILA_CABECERA)
        centros = _cabecera(c, 0, y_dueno, m_w, dueno, campos, valores_dueno)
        for campo, centro in zip(campos, centros, strict=True):
            if campo.destino == "rows":
                c.ruta((m_w, centro), (m_w + 30, centro), (m_w + 30, y0 + celda_h / 2), (x_ptr - 3, y0 + celda_h / 2))
            elif campo.destino == "lengths":
                c.ruta((m_w, centro), (m_w + 16, centro), (m_w + 16, y_largos + largo_h / 2),
                       (x_ptr - 3, y_largos + largo_h / 2))
    elif con_largos:
        # El arreglo de largos, fila por fila, a la izquierda: `largos[i]` celdas tiene la fila i.
        c.t(largos_w / 2, y0 - 8, nombre_largos, size=12, peso=700, ancla="middle")
        for i in range(nf):
            y = y0 + i * paso_y
            c.r(0, y, largos_w, celda_h, trazo=1.5)
            c.t(largos_w / 2, y + 12, f"[{i}]", size=9.5, color="textMain", ancla="middle")
            largo = declarados[i] if i < len(declarados) else largos[i]
            if b.get("blankLengths"):
                c.vacio(10, largos_w - 10, y + celda_h - 8)
            else:
                c.t(largos_w / 2, y + 32, largo, size=13, peso=700, ancla="middle")

    # El puntero `m`, que apunta al arreglo de punteros a filas.
    if dueno is None:
        c.t(x_m + m_w / 2, y0 - 8, nombre, size=12, peso=700, ancla="middle")
        c.r(x_m, y0, m_w, celda_h, relleno="fillPointerBox", trazo=1.75, rx=3)
        if direcciones:
            c.t(x_m + m_w / 2, y0 + celda_h / 2 + 4, dir_base, size=9, ancla="middle")
            c.linea(x_m + m_w, y0 + celda_h / 2, x_ptr - 3, y0 + celda_h / 2, ancho=1.6)
        else:
            c.punto(x_m + m_w / 2, y0 + celda_h / 2)
            c.linea(x_m + m_w / 2, y0 + celda_h / 2, x_ptr - 3, y0 + celda_h / 2, ancho=1.6)
    if direcciones:
        c.t(x_ptr + ptr_w / 2, y0 - 8, dir_base, size=9, color="textSub", ancla="middle")

    if indices and any(largos):
        for j in range(max(largos)):
            c.t(x_filas + j * celda_w + celda_w / 2, y0 - 8, f"[{j}]", size=11, peso=700, color="textSub",
                ancla="middle")

    ancho = x_ptr + ptr_w + 60
    for i in range(nf):
        y = y0 + i * paso_y
        cy = y + celda_h / 2
        c.r(x_ptr, y, ptr_w, celda_h, relleno="fillPointerBox", trazo=1.5)
        c.t(x_ptr + ptr_w / 2, y + 12, f"{nombre}[{i}]", size=9.5, color="textMain", ancla="middle")
        fila = filas[i]
        if fila is None:  # fila NULL: la barra cruzada de statics
            c.linea(x_ptr + 5, y + celda_h - 5, x_ptr + ptr_w - 5, y + 16, color="strokeMain", ancho=1.5,
                    flecha=None)
            c.t(x_ptr + ptr_w + 10, cy + 4, "NULL", size=10, peso=700, color="textMuted")
            continue
        if direcciones:
            c.t(x_ptr + ptr_w / 2, y + 31, dir_fila(i), size=9, ancla="middle")
            c.linea(x_ptr + ptr_w, cy + 5, x_filas - 3, cy + 5, ancho=1.6)
        else:
            c.punto(x_ptr + ptr_w / 2, cy + 5)
            c.linea(x_ptr + ptr_w / 2, cy + 5, x_filas - 3, cy + 5, ancho=1.6)
        largo = largos[i]
        for j in range(largo):
            x = x_filas + j * celda_w
            c.r(x, y, celda_w, celda_h, relleno="fillHighlight" if (i, j) in resaltadas else "fillCell",
                trazo=1.5)
            v = fila[j] if j < len(fila) else ""
            if v and not sin_valores:
                c.t(x + celda_w / 2, cy + 5, v, size=14, peso=700, ancla="middle")
            else:
                c.vacio(x + 9, x + celda_w - 9, y + celda_h - 9)
        if centinela is not None:  # la celda que marca el fin de la fila (no es un dato)
            x = x_filas + largo * celda_w
            c.r(x, y, celda_w, celda_h, relleno="fillHeader", trazo=1.5)
            c.add(f'<rect x="{x + 3:.1f}" y="{y + 3:.1f}" width="{celda_w - 6}" height="{celda_h - 6}" '
                  f'fill="none" stroke="{c.pal["strokeMuted"]}" stroke-width="1" stroke-dasharray="3 2"/>')
            c.t(x + celda_w / 2, cy + 5, centinela, size=13, peso=700, color="textSub", ancla="middle")
        total = largo + (1 if centinela is not None else 0)
        if total:
            c.add(f'<rect x="{x_filas}" y="{y:.1f}" width="{total * celda_w}" height="{celda_h}" fill="none" '
                  f'stroke="{c.pal["strokeMain"]}" stroke-width="2"/>')
        if direcciones and not sin_dirs:
            c.t(x_filas + total * celda_w + 8, cy + 4, f"← {dir_fila(i)}", size=9, color="textSub")
        ancho = max(ancho, x_filas + total * celda_w + (70 if direcciones else 16))
    alto = y0 + (nf - 1) * paso_y + celda_h + 10
    if dueno is not None:
        alto = max(alto, y_dueno + len(campos) * FILA_CABECERA + 10)
        if con_largos:
            ancho = max(ancho, x_ptr + nf * largo_w + 12)
    if zonas:
        _zona(c, -6, x_m + m_w + 8, inicio + 2, alto + 4, zonas[0])
        _zona(c, x_ptr - 14, ancho, inicio + 2, alto + 4, zonas[1])
        alto += 8
    return ancho, alto


# ---------------------------------------------------------------------------
# Lista enlazada: simple, doble y circular
# ---------------------------------------------------------------------------

def _lista_vacia(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    top = _encabezado(c, b)
    y, cabeza_w = top + 28, 72
    c.t(cabeza_w / 2, y, b.get("headLabel") or "HEAD", size=10, peso=700, ancla="middle")
    c.r(0, y + 7, cabeza_w, 40, relleno="fillPointerBox", trazo=1.75, rx=3)
    c.linea(5, y + 42, cabeza_w - 5, y + 12, color="strokeMain", ancho=1.5, flecha=None)
    c.linea(cabeza_w, y + 27, cabeza_w + 22, y + 27, ancho=1.5, flecha=None)
    c.null(cabeza_w + 22, y + 27)
    return cabeza_w + 80, y + 56


def _lista(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    if b.get("values") == []:
        return _lista_vacia(c, b)
    valores = _valores(b) or [""]
    n = min(7, len(valores))
    variante = b.get("variant", "singly")
    doble, circular = variante in ("doubly", "circular_doubly"), variante in ("circular", "circular_doubly")
    sin_dirs, sin_flechas = bool(b.get("blankNextAddrs")), b.get("drawArrows") is False
    sin_valores = bool(b.get("blankValues"))
    zonas = _nombres_de_zonas(b)
    inicio = _encabezado(c, b)
    top = inicio + (ALTO_ZONA if zonas else 0)

    direcciones = [_fmt_hex(d) if isinstance(d, int) else str(d) for d in b.get("addresses") or []]
    direcciones += [_fmt_hex(0x4000 + i * 0x180) for i in range(len(direcciones), n)]
    punteros = _punteros(b, n)  # cursores: `actual`, `ant`, y `final` en una cola enlazada
    y, alto_nodo = top + (62 if punteros else 28), 54
    cabeza_w: float = 72
    x0: float = 104
    nodo_w = 126 if doble else 102
    gap = 44
    # Una estructura cabecera en lugar de HEAD: `primero` y `ultimo` apuntan a los nodos por su posición.
    cabecera = b.get("header")
    campos = _campos_cabecera(cabecera, "header") if cabecera is not None else []
    valores_cabecera: List[str] = []
    for campo in campos:
        if campo.destino is None:
            valores_cabecera.append(campo.valor)
            continue
        if not str(campo.destino).isdigit() or int(campo.destino) >= n:
            raise ErrorDiagrama(f"'header': {campo.nombre} apunta al nodo {campo.destino!r}, y hay {n} nodos (de 0 a {n - 1})")
        valores_cabecera.append("" if sin_dirs else direcciones[int(campo.destino)])
    if cabecera is not None:
        cabeza_w = _ancho_cabecera(cabecera, campos, valores_cabecera)
        x0 = cabeza_w + 48
    tipo_nodo = b.get("nodeType")
    for i, etiquetas in punteros.items():
        centro = x0 + i * (nodo_w + gap) + nodo_w / 2
        texto = ", ".join(etiquetas)
        ancho_cursor = max(40, len(texto) * 7.5 + 12)
        c.r(centro - ancho_cursor / 2, y - 50, ancho_cursor, 18, relleno="fillBadge", trazo=1.2, rx=3)
        c.t(centro, y - 37, texto, size=10, peso=700, ancla="middle")
        c.linea(centro, y - 32, centro, y - 21, ancho=1.5)

    if cabecera is None:
        c.t(cabeza_w / 2, y, b.get("headLabel") or "HEAD", size=10, peso=700, ancla="middle")
        c.r(0, y + 7, cabeza_w, 40, relleno="fillPointerBox", trazo=1.75, rx=3)
        if not sin_dirs:
            c.t(cabeza_w / 2, y + 31, direcciones[0], size=10, peso=600, color="textSub", ancla="middle")
        if not sin_flechas:
            c.linea(cabeza_w, y + 27, x0 - 3, y + 27, ancho=1.75)
    else:
        # El primer renglón queda a la altura de los nodos: si apunta al primero, la flecha va derecha.
        centros = _cabecera(c, 0, y + 27 - FILA_CABECERA / 2, cabeza_w, cabecera, campos, valores_cabecera)
        abajo = y + alto_nodo + (50 if circular else 28)
        for k, (campo, centro) in enumerate(zip(campos, centros, strict=True)):
            if campo.destino is None or sin_flechas:
                continue
            destino = int(campo.destino)
            if k == 0 and destino == 0:
                c.linea(cabeza_w, centro, x0 - 3, centro, ancho=1.75)
                continue
            # Los demás van por debajo de los nodos y entran por abajo, sin cruzar a los otros punteros.
            codo, x_nodo = cabeza_w + 12 + 8 * k, x0 + destino * (nodo_w + gap) + 16
            c.ruta((cabeza_w, centro), (codo, centro), (codo, abajo), (x_nodo, abajo), (x_nodo, y + alto_nodo + 3))
            abajo += 10

    for i in range(n):
        nx = x0 + i * (nodo_w + gap)
        valor = valores[i]
        siguiente = direcciones[i + 1] if i < n - 1 else (direcciones[0] if circular else "NULL")
        anterior = direcciones[i - 1] if i > 0 else (direcciones[n - 1] if circular else "NULL")
        rotulo = f"{direcciones[i]} ({tipo_nodo})" if tipo_nodo else f"Dir: {direcciones[i]}"
        c.t(nx + nodo_w / 2, y - 7, rotulo, size=10, peso=700, color="textSub", ancla="middle")

        if not doble:
            dato_w = 62
            ptr_w = nodo_w - dato_w
            c.r(nx, y, nodo_w, alto_nodo, trazo=1.75, rx=3)
            c.r(nx + dato_w, y, ptr_w, alto_nodo, relleno="fillPointerBox")
            c.t(nx + dato_w / 2, y + 12, "dato", size=9.5, color="textMain", ancla="middle")
            c.t(nx + dato_w + ptr_w / 2, y + 12, "*sig", size=9.5, color="textMain", ancla="middle")
            if valor and not sin_valores:
                c.t(nx + dato_w / 2, y + 36, valor, size=14, peso=700, ancla="middle")
            else:
                c.vacio(nx + 8, nx + dato_w - 8, y + 42)
            px, py = nx + dato_w + ptr_w / 2, y + 33
            if not sin_flechas:
                if i < n - 1:
                    c.punto(px, py)
                    c.linea(px, py, nx + nodo_w + gap - 3, py, ancho=1.75)
                elif circular:
                    vuelta = y + alto_nodo + 28
                    c.punto(px, py)
                    c.add(f'<path d="M {px:.1f} {py:.1f} L {nx + nodo_w + 16:.1f} {py:.1f} L {nx + nodo_w + 16:.1f} '
                          f'{vuelta:.1f} L {x0 + 20:.1f} {vuelta:.1f} L {x0 + 20:.1f} {y + alto_nodo + 3:.1f}" '
                          f'fill="none" stroke="{c.pal["accentPrimary"]}" stroke-width="1.6" '
                          f'marker-end="url(#flecha-main-{c.sufijo})"/>')
                else:
                    c.linea(nx + dato_w + 5, y + alto_nodo - 5, nx + nodo_w - 5, y + 16, color="strokeMain",
                            ancho=1.5, flecha=None)
                    c.punto(px, py, radio=3)
                    c.linea(px, py, nx + nodo_w + 22, py, ancho=1.5, flecha=None)
                    c.null(nx + nodo_w + 22, py)
            c.t(px, y + alto_nodo + 14, f"sig:{'______' if sin_dirs else siguiente}", size=9.5, color="textMain",
                ancla="middle")
        else:
            ptr_w = 32
            dato_w = nodo_w - 2 * ptr_w
            c.r(nx, y, nodo_w, alto_nodo, trazo=1.75, rx=3)
            c.r(nx, y, ptr_w, alto_nodo, relleno="fillPointerBox")
            c.r(nx + ptr_w + dato_w, y, ptr_w, alto_nodo, relleno="fillPointerBox")
            c.t(nx + ptr_w / 2, y + 12, "*ant", size=9, color="textMain", ancla="middle")
            c.t(nx + ptr_w + dato_w / 2, y + 12, "dato", size=9.5, color="textMain", ancla="middle")
            c.t(nx + ptr_w + dato_w + ptr_w / 2, y + 12, "*sig", size=9, color="textMain", ancla="middle")
            if valor and not sin_valores:
                c.t(nx + ptr_w + dato_w / 2, y + 36, valor, size=14, peso=700, ancla="middle")
            else:
                c.vacio(nx + ptr_w + 8, nx + ptr_w + dato_w - 8, y + 42)
            if not sin_flechas:
                if i == 0 and not circular:
                    c.linea(nx + 4, y + alto_nodo - 5, nx + ptr_w - 4, y + 16, color="strokeMain", ancho=1.4,
                            flecha=None)
                if i == n - 1 and not circular:
                    c.linea(nx + ptr_w + dato_w + 4, y + alto_nodo - 5, nx + nodo_w - 4, y + 16,
                            color="strokeMain", ancho=1.4, flecha=None)
                if i < n - 1:
                    siguiente_x = nx + nodo_w + gap
                    sig_x = nx + ptr_w + dato_w + ptr_w / 2
                    c.punto(sig_x, y + 26, radio=2.8)
                    c.linea(sig_x, y + 26, siguiente_x - 3, y + 26)
                    c.punto(siguiente_x + ptr_w / 2, y + 40, color="strokeSub", radio=2.8)
                    c.linea(siguiente_x + ptr_w / 2, y + 40, nx + nodo_w + 3, y + 40, color="strokeSub", ancho=1.5,
                            flecha="sub", guiones="3 1.5")
                elif circular:
                    vuelta = y + alto_nodo + 28
                    sig_x = nx + ptr_w + dato_w + ptr_w / 2
                    c.punto(sig_x, y + 26, radio=2.8)
                    c.add(f'<path d="M {sig_x:.1f} {y + 26:.1f} L {nx + nodo_w + 16:.1f} {y + 26:.1f} '
                          f'L {nx + nodo_w + 16:.1f} {vuelta:.1f} L {x0 + 16:.1f} {vuelta:.1f} '
                          f'L {x0 + 16:.1f} {y + alto_nodo + 3:.1f}" fill="none" stroke="{c.pal["accentPrimary"]}" '
                          f'stroke-width="1.6" marker-end="url(#flecha-main-{c.sufijo})"/>')
            if not sin_dirs:
                c.t(nx + nodo_w / 2, y + alto_nodo + 14, f"ant:{anterior} | sig:{siguiente}", size=9.5,
                    color="textMain", ancla="middle")

    if circular and not sin_flechas:
        c.t(x0 + (n * (nodo_w + gap)) / 2, y + alto_nodo + 42,
            f"Enlace circular: el último apunta a HEAD ({direcciones[0]})", size=9, peso=600, color="textSub",
            ancla="middle")
    ancho = x0 + n * (nodo_w + gap) - gap + (80 if not circular else 30)
    alto = y + alto_nodo + (50 if circular else 24)
    if cabecera is not None:
        alto = max(alto, y + 27 - FILA_CABECERA / 2 + len(campos) * FILA_CABECERA + 6)
        if any(campo.destino is not None for campo in campos[1:]):
            alto = max(alto, abajo)
    if zonas:
        _zona(c, -6, cabeza_w + 8, inicio + 2, alto + 6, zonas[0])
        _zona(c, x0 - 14, ancho, inicio + 2, alto + 6, zonas[1])
        alto += 10
    return ancho, alto


# ---------------------------------------------------------------------------
# Pila
# ---------------------------------------------------------------------------

def _pila(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    valores = _valores(b)
    cap = _entero(b.get("capacity", len(valores) or 5), 5, 2, 10)
    base, paso = _hex(b.get("baseAddr")), _entero(b.get("typeSize"), 4, 1, 64)
    tope = b.get("topIndex", len([v for v in valores if v]) - 1)
    sin_valores = bool(b.get("blankValues"))
    top = _encabezado(c, b)
    celda_w, celda_h, y0 = 104, 34, top + 26
    dirs = bool(b.get("showAddresses", True))
    izq = 84 if dirs else 36  # índices (y direcciones) a la izquierda de la pila

    def instancia(x: float, etiqueta: str, inicial: bool) -> None:
        caja = x + izq
        fondo = y0 + cap * celda_h
        if etiqueta:
            c.t(x, y0 - 8, etiqueta, size=11, peso=700, color="textSub", fuente=SANS)
        for idx in range(cap - 1, -1, -1):
            cy = y0 + (cap - 1 - idx) * celda_h
            valor = valores[idx] if inicial and idx < len(valores) else ""
            c.t(caja - 8, cy + celda_h / 2 + 4, f"[{idx}]", size=10, peso=600, color="textSub", ancla="end")
            if inicial and dirs:
                c.t(caja - 34, cy + celda_h / 2 + 3, _fmt_hex(base + idx * paso), size=9, color="textMuted",
                    ancla="end")
            c.r(caja, cy, celda_w, celda_h)
            if valor and not sin_valores:
                c.t(caja + celda_w / 2, cy + celda_h / 2 + 5, valor, size=13, peso=700, ancla="middle")
            else:
                c.vacio(caja + 14, caja + celda_w - 14, cy + celda_h - 8)
            if inicial and not b.get("blankPointers") and str(idx) == str(tope):
                sx, sy = caja + celda_w + 30, cy + celda_h / 2
                c.r(sx, sy - 10, 64, 20, relleno="fillBadge", trazo=1.3, rx=3)
                c.t(sx + 32, sy + 4, b.get("topLabel") or "TOPE", size=9.5, peso=700, ancla="middle")
                c.linea(sx, sy, caja + celda_w + 3, sy)
        c.add(f'<path d="M {caja - 3} {y0 - 4} L {caja - 3} {fondo + 3} L {caja + celda_w + 3} {fondo + 3} '
              f'L {caja + celda_w + 3} {y0 - 4}" fill="none" stroke="{c.pal["strokeMain"]}" stroke-width="2.5"/>')
        tope_txt = tope if inicial and not b.get("blankPointers") else "___"
        c.t(caja + celda_w / 2, fondo + 18, f"BASE | tope = {tope_txt}", size=9.5, peso=600, color="textMuted",
            ancla="middle")

    if b.get("layout") == "vertical_multi":
        etiquetas = [str(e) for e in b.get("traceLabels") or []]
        cuantas = max(2, min(4, len(etiquetas) or 2))
        paso_x = max(izq + celda_w + 110, max((len(e) for e in etiquetas), default=0) * 6.2 + 40)
        for t in range(cuantas):
            instancia(t * paso_x, etiquetas[t] if t < len(etiquetas) else f"Paso {t + 1}", t == 0)
        ancho = cuantas * paso_x
    else:
        instancia(0, b.get("label", ""), True)
        ancho = izq + celda_w + 30 + 64 + 10
    return ancho, y0 + cap * celda_h + 28


# ---------------------------------------------------------------------------
# Pila de llamadas (call stack): marcos de activación y su evolución en el tiempo
# ---------------------------------------------------------------------------

MAX_MARCOS, MAX_PASOS = 10, 8


@dataclass
class _Var:
    nombre: str
    valor: str
    tipo: str = ""
    direccion: Optional[str] = None
    en_blanco: bool = False
    param: bool = False
    tamano: Optional[int] = None       # bytes; por omisión, 8 si el tipo es un puntero y si no typeSize


@dataclass
class _Marco:
    funcion: str
    variables: List[_Var]
    retorno: Optional[str] = None      # lo que devolvió (marco que acaba de terminar)
    terminado: bool = False            # `popped`: ya retornó; se dibuja punteado
    linea: Optional[str] = None        # `returnTo`: a dónde vuelve


def _texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, list):
        return "[" + ", ".join(_texto(v) for v in valor) + "]"
    return str(valor)


def _variables(dato: Any, param: bool, donde: str) -> List[_Var]:
    """`{x: 5, p: "&x"}` o `[{name: x, value: 5, type: int, addr: 0x7FFC, blank: true}, "y = 3"]`."""
    if dato is None:
        return []
    if isinstance(dato, dict):
        return [_Var(str(k), _texto(v), param=param) for k, v in dato.items()]
    if not isinstance(dato, list):
        raise ErrorDiagrama(f"{donde}: las variables van como diccionario o lista")
    salida = []
    for v in dato:
        if isinstance(v, str) and "=" in v:
            nombre, _, valor = v.partition("=")
            salida.append(_Var(nombre.strip(), valor.strip(), param=param))
        elif isinstance(v, dict) and "name" in v:
            addr = v.get("addr")
            tam = v.get("size")
            salida.append(_Var(str(v["name"]), _texto(v.get("value")), str(v.get("type") or ""),
                               _fmt_hex(_hex(addr)) if addr not in (None, "") else None,
                               bool(v.get("blank")), param, _entero(tam, 4, 1, 4096) if tam is not None else None))
        else:
            raise ErrorDiagrama(f"{donde}: variable inválida {v!r} (se espera 'x = 5' o name/value)")
    return salida


def _marcos(dato: Any, donde: str) -> List[_Marco]:
    if not isinstance(dato, list) or not dato:
        raise ErrorDiagrama(f"{donde}: 'frames' tiene que ser una lista de marcos (de main hacia el tope)")
    if len(dato) > MAX_MARCOS:
        raise ErrorDiagrama(f"{donde}: {len(dato)} marcos; el máximo es {MAX_MARCOS}")
    marcos = []
    for i, f in enumerate(dato):
        if not isinstance(f, dict) or not f.get("function"):
            raise ErrorDiagrama(f"{donde}: el marco {i} necesita 'function'")
        variables = (_variables(f.get("params"), True, f"{donde}, {f['function']}")
                     + _variables(f.get("vars"), False, f"{donde}, {f['function']}"))
        retorno = f.get("returns")
        marcos.append(_Marco(str(f["function"]), variables, None if retorno is None else _texto(retorno),
                             bool(f.get("popped")), f.get("returnTo")))
    return marcos


def _flechas(dato: Any, marcos: List[_Marco], donde: str) -> List[Tuple[int, int, int, int]]:
    """`"1.p -> 0.x"`: de la variable p del marco 1 a la x del 0 (índice desde main, o nombre de función)."""
    if not dato:
        return []
    partes = [p for p in (dato.split(";") if isinstance(dato, str) else dato) if str(p).strip()]

    def ubicar(ref: str) -> Tuple[int, int]:
        marco, _, var = ref.strip().rpartition(".")
        if not marco or not var:
            raise ErrorDiagrama(f"{donde}: referencia {ref!r} inválida (se espera marco.variable)")
        if marco.isdigit():
            im = int(marco)
        else:  # por nombre: el marco más alto de esa función
            im = next((k for k in range(len(marcos) - 1, -1, -1) if marcos[k].funcion == marco), -1)
        if not 0 <= im < len(marcos):
            raise ErrorDiagrama(f"{donde}: no hay marco {marco!r}")
        iv = next((k for k, v in enumerate(marcos[im].variables) if v.nombre == var), -1)
        if iv < 0:
            raise ErrorDiagrama(f"{donde}: el marco {marcos[im].funcion} no tiene la variable {var!r}")
        return im, iv

    flechas = []
    for p in partes:
        origen, sep, destino = str(p).partition("->")
        if not sep:
            raise ErrorDiagrama(f"{donde}: flecha {p!r} inválida (se espera 'marco.var -> marco.var')")
        flechas.append((*ubicar(origen), *ubicar(destino)))
    return flechas


def _pila_llamadas(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """Marcos de activación apilados desde main; con `steps`, la pila en varios momentos."""
    if b.get("steps") is not None:
        pasos_dato = b["steps"]
        if not isinstance(pasos_dato, list) or not pasos_dato:
            raise ErrorDiagrama("'steps' tiene que ser una lista de momentos, cada uno con 'frames'")
        if len(pasos_dato) > MAX_PASOS:
            raise ErrorDiagrama(f"{len(pasos_dato)} pasos; el máximo es {MAX_PASOS}")
        pasos = []
        for k, p in enumerate(pasos_dato):
            if not isinstance(p, dict):
                raise ErrorDiagrama(f"el paso {k} tiene que tener 'frames'")
            donde = f"paso {k}"
            marcos = _marcos(p.get("frames"), donde)
            pasos.append((str(p.get("label") or f"Paso {k + 1}"), marcos, _flechas(p.get("pointers"), marcos, donde)))
    else:
        marcos = _marcos(b.get("frames"), "pila de llamadas")
        pasos = [(str(b.get("label") or ""), marcos, _flechas(b.get("pointers"), marcos, "pila de llamadas"))]

    direcciones = bool(b.get("showAddresses"))
    base, paso_dir = _hex(b.get("baseAddr"), 0x7FFC), _entero(b.get("typeSize"), 4, 1, 64)
    sin_valores, con_tipos = bool(b.get("blankValues")), bool(b.get("showTypes"))
    top = _encabezado(c, b)

    # Medidas comunes a todos los pasos, para que se puedan comparar.
    todas = [v for _, ms, _ in pasos for m in ms for v in m.variables]
    rotulo = (lambda v: f"{v.tipo} {v.nombre}".strip() if con_tipos else v.nombre)
    nombre_w = max([len(rotulo(v)) for v in todas] + [4]) * 7.4 + 18
    valor_w = max(58, max([len(v.valor) for v in todas] + [1]) * 8.2 + 22)
    dir_w = 62 if direcciones else 0
    cab_h, fila_h, sep = 24, 26, 6
    def nota(m: _Marco) -> str:
        """Lo que va a la derecha del título: lo que devolvió o a dónde vuelve."""
        return f"devolvió {m.retorno}" if m.retorno is not None else f"vuelve a {m.linea}" if m.linea else ""

    marco_w = max(dir_w + nombre_w + valor_w + 8,
                  max(len(m.funcion + "(" + ", ".join(v.nombre for v in m.variables if v.param) + ")") * 7.6
                      + 24 + len(nota(m)) * 6.4 for _, ms, _ in pasos for m in ms))
    max_flechas = max(len(f) for _, _, f in pasos)
    margen_flechas = (16 + 10 * max_flechas) if max_flechas else 0

    def alto_marco(m: _Marco) -> float:
        return cab_h + max(1, len(m.variables)) * fila_h + 6

    alto_pila = max(sum(alto_marco(m) + sep for m in ms) for _, ms, _ in pasos)
    etiquetas = any(et for et, _, _ in pasos)
    y_base = top + (24 if etiquetas else 8) + alto_pila  # la base (main) alineada en todos los pasos
    # La columna crece con su rótulo (negrita de 11): «segunda llamada, antes de c++» no entra en un marco angosto.
    rotulo_w = max(len(et) for et, _, _ in pasos) * 7.0
    col_w = max(marco_w + margen_flechas + 40, rotulo_w + 24)
    c.ancho_min = max(c.ancho_min, (len(pasos) - 1) * col_w + rotulo_w)

    for col, (etiqueta, marcos, flechas) in enumerate(pasos):
        x0 = col * col_w
        if etiqueta:
            c.t(x0, top + 14, etiqueta, size=11, peso=700, color="textSub", fuente=SANS)
        activo = max((k for k, m in enumerate(marcos) if not m.terminado), default=-1)
        filas_y: Dict[Tuple[int, int], float] = {}
        # La pila crece hacia abajo: la primera variable de main está en baseAddr y cada una de las
        # siguientes, `tamaño` bytes más abajo.
        dir_actual: Optional[int] = None
        y = y_base
        for k, m in enumerate(marcos):
            h = alto_marco(m)
            y -= h
            borde = 2.5 if k == activo else 1.5
            if m.terminado:
                c.add(f'<rect x="{x0:.1f}" y="{y:.1f}" width="{marco_w:.1f}" height="{h:.1f}" rx="4" fill="none" '
                      f'stroke="{c.pal["strokeMuted"]}" stroke-width="1.5" stroke-dasharray="5 3"/>')
            else:
                c.r(x0, y, marco_w, h, trazo=borde, rx=4)
            c.add(f'<rect x="{x0 + 1:.1f}" y="{y + 1:.1f}" width="{marco_w - 2:.1f}" height="{cab_h - 1}" rx="3" '
                  f'fill="{c.pal["fillHighlight" if k == activo else "fillHeader"]}"/>')
            c.linea(x0, y + cab_h, x0 + marco_w, y + cab_h, color="strokeMuted" if m.terminado else "strokeMain",
                    ancho=1, flecha=None)
            color_txt = "textMuted" if m.terminado else "textMain"
            titulo = m.funcion + "(" + ", ".join(v.nombre for v in m.variables if v.param) + ")"
            c.t(x0 + 8, y + 16, titulo, size=11.5, peso=700, color=color_txt)
            if nota(m):
                c.t(x0 + marco_w - 8, y + 16, nota(m), size=9.5, peso=700 if m.retorno is not None else 400,
                    color="textSub", ancla="end")
            if not m.variables:
                c.t(x0 + 10, y + cab_h + 18, "(sin variables)", size=9.5, color="textMuted")
            for iv, v in enumerate(m.variables):
                fy = y + cab_h + 3 + iv * fila_h
                if direcciones:
                    tam = v.tamano or (8 if "*" in v.tipo else paso_dir)
                    dir_actual = base if dir_actual is None else dir_actual - tam
                    if v.direccion:
                        dir_actual = _hex(v.direccion)
                    c.t(x0 + 8, fy + 16, "0x____" if b.get("blankAddrs") else _fmt_hex(dir_actual), size=8.5,
                        color="textSub")
                c.t(x0 + dir_w + 10, fy + 16, rotulo(v), size=11, color=color_txt,
                    peso=600 if v.param else 400)
                vx = x0 + dir_w + nombre_w
                c.r(vx, fy + 2, valor_w - 8, fila_h - 6, relleno="fillCell", trazo=1.2, rx=2)
                if v.valor and not (sin_valores or v.en_blanco):
                    c.t(vx + (valor_w - 8) / 2, fy + 17, v.valor, size=12, peso=700, color=color_txt,
                        ancla="middle")
                else:
                    c.vacio(vx + 6, vx + valor_w - 14, fy + fila_h - 7)
                filas_y[(k, iv)] = fy + fila_h / 2 - 1
            y -= sep
        # La base de la pila (debajo de main).
        c.linea(x0 - 6, y_base + 2, x0 + marco_w + 6, y_base + 2, color="strokeMain", ancho=2.5, flecha=None)
        # Punteros: salen del valor, rodean por la derecha y entran al valor apuntado.
        borde_valor = x0 + dir_w + nombre_w + valor_w - 8
        for n, (im, iv, jm, jv) in enumerate(flechas):
            y1, y2 = filas_y[(im, iv)], filas_y[(jm, jv)]
            xm = x0 + marco_w + 12 + n * 10
            c.punto(borde_valor - 8, y1, radio=2.8)
            c.add(f'<path d="M {borde_valor - 8:.1f} {y1:.1f} L {xm:.1f} {y1:.1f} L {xm:.1f} {y2:.1f} '
                  f'L {borde_valor + 3:.1f} {y2:.1f}" fill="none" stroke="{c.pal["accentPrimary"]}" '
                  f'stroke-width="1.6" marker-end="url(#flecha-main-{c.sufijo})"/>')
    c.t(0, y_base + 18, "base de la pila", size=9, color="textMuted")
    return len(pasos) * col_w - 40 + 4, y_base + 24


# ---------------------------------------------------------------------------
# Cola: lineal y circular
# ---------------------------------------------------------------------------

def _cola(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    valores = _valores(b)
    cap = _entero(b.get("capacity", len(valores) or 8), 8, 4, 12)
    frente, final = str(b.get("frontIndex", "")), str(b.get("rearIndex", ""))
    sin_valores, sin_ptrs = bool(b.get("blankValues")), bool(b.get("blankPointers"))
    top = _encabezado(c, b)

    if b.get("variant") == "circular":
        cx, cy, r_ext, r_int = 150, top + 130, 96, 52
        r_texto, r_indice = (r_ext + r_int) / 2, r_int - 13
        for i in range(cap):
            a0 = i / cap * 2 * math.pi - math.pi / 2
            a1 = (i + 1) / cap * 2 * math.pi - math.pi / 2
            am = (a0 + a1) / 2

            def pt(radio: float, ang: float) -> str:
                return f"{cx + radio * math.cos(ang):.2f} {cy + radio * math.sin(ang):.2f}"

            c.add(f'<path d="M {pt(r_ext, a0)} A {r_ext} {r_ext} 0 0 1 {pt(r_ext, a1)} L {pt(r_int, a1)} '
                  f'A {r_int} {r_int} 0 0 0 {pt(r_int, a0)} Z" fill="{c.pal["fillCell"]}" '
                  f'stroke="{c.pal["strokeMain"]}" stroke-width="1.6"/>')
            c.t(cx + r_indice * math.cos(am), cy + r_indice * math.sin(am) + 3.5, f"[{i}]", size=10, peso=700,
                color="textSub", ancla="middle")
            valor = valores[i] if i < len(valores) else ""
            if valor and not sin_valores:
                c.t(cx + r_texto * math.cos(am), cy + r_texto * math.sin(am) + 4, valor, size=12.5, peso=700,
                    ancla="middle")
            if not sin_ptrs and str(i) in (frente, final):
                c.linea(cx + (r_ext + 28) * math.cos(am), cy + (r_ext + 28) * math.sin(am),
                        cx + (r_ext + 4) * math.cos(am), cy + (r_ext + 4) * math.sin(am), ancho=1.75)
                etiqueta = "FRENTE=FINAL" if frente == final else ("FRENTE" if str(i) == frente else "FINAL")
                c.t(cx + (r_ext + 42) * math.cos(am), cy + (r_ext + 42) * math.sin(am) + 4, etiqueta, size=10,
                    peso=700, ancla="middle")
        c.t(cx, cy + 4, f"N = {cap}", size=10, peso=700, color="textMuted", ancla="middle")
        if not b.get("showPanel", True):
            return 320, top + 270
        px, pw = 330, 400
        c.add(f'<g transform="translate({px}, {top + 30})">')
        c.r(0, 0, pw, 190, relleno="fillHeader", trazo=1.4, rx=4)
        c.t(14, 24, f"Índices de la cola circular (módulo N = {cap})", size=12, peso=700, fuente=SANS)
        c.linea(0, 34, pw, 34, color="strokeMain", ancho=1, flecha=None)
        c.t(14, 56, f"• FRENTE = {'______' if sin_ptrs else frente}   (próximo a salir)", size=11, peso=600)
        c.t(14, 78, f"• FINAL  = {'______' if sin_ptrs else final}   (último insertado)", size=11, peso=600)
        c.t(14, 108, "Aritmética modular:", size=10.5, color="textSub")
        c.t(22, 126, f"Encolar:     final  = (final + 1) % {cap}", size=10, color="textMuted")
        c.t(22, 144, f"Desencolar:  frente = (frente + 1) % {cap}", size=10, color="textMuted")
        c.t(22, 162, f"Llena:       (final + 1) % {cap} == frente", size=10, color="textMuted")
        c.t(22, 180, "Cantidad:    cant = _________", size=10, color="textMuted")
        c.add("</g>")
        return px + pw + 10, top + 270

    x0, celda_w, celda_h, y = 110, 60, 50, top + 58
    fin_x = x0 + cap * celda_w
    c.t(x0 - 14, y + 20, "DESENCOLAR", size=10, peso=700, color="textSub", ancla="end")
    c.t(x0 - 14, y + 34, "← sale frente", size=9, color="textMuted", ancla="end")
    c.t(fin_x + 14, y + 20, "ENCOLAR(x)", size=10, peso=700, color="textSub")
    c.t(fin_x + 14, y + 34, "← entra final", size=9, color="textMuted")
    c.linea(x0 - 6, y - 3, fin_x + 6, y - 3, color="strokeMain", ancho=2.2, flecha=None)
    c.linea(x0 - 6, y + celda_h + 3, fin_x + 6, y + celda_h + 3, color="strokeMain", ancho=2.2, flecha=None)
    for i in range(cap):
        cx = x0 + i * celda_w
        centro = cx + celda_w / 2
        c.t(centro, y - 9, f"[{i}]", size=10.5, peso=700, color="textSub", ancla="middle")
        c.r(cx, y, celda_w, celda_h)
        valor = valores[i] if i < len(valores) else ""
        if valor and not sin_valores:
            c.t(centro, y + celda_h / 2 + 5, valor, size=14, peso=700, ancla="middle")
        else:
            c.vacio(cx + 10, cx + celda_w - 10, y + celda_h - 12)
        if sin_ptrs:
            continue
        if str(i) == frente:
            c.linea(centro, y + celda_h + 24, centro, y + celda_h + 6)
            c.r(centro - 30, y + celda_h + 24, 60, 18, relleno="fillBadge", trazo=1.2, rx=3)
            c.t(centro, y + celda_h + 37, "FRENTE", size=9.5, peso=700, ancla="middle")
        if str(i) == final:
            centro += 18 if str(i) == frente else 0
            c.linea(centro, y - 34, centro, y - 21)
            c.r(centro - 28, y - 52, 56, 18, relleno="fillBadge", trazo=1.2, rx=3)
            c.t(centro, y - 39, "FINAL", size=9.5, peso=700, ancla="middle")
    return fin_x + 110, y + celda_h + 50


# ---------------------------------------------------------------------------
# Árboles: binario, ABB, AVL y montículo
# ---------------------------------------------------------------------------

@dataclass
class _Nodo:
    valor: str
    izq: Optional["_Nodo"] = None
    der: Optional["_Nodo"] = None
    indice: Optional[int] = None  # posición en el arreglo (montículo / orden por niveles)

    @property
    def altura(self) -> int:
        return 1 + max(self.izq.altura if self.izq else 0, self.der.altura if self.der else 0)

    @property
    def balance(self) -> int:
        return (self.izq.altura if self.izq else 0) - (self.der.altura if self.der else 0)


def _clave(valor: Any) -> Any:
    try:
        return (0, float(valor))
    except (TypeError, ValueError):
        return (1, str(valor))


def _rotar_der(n: _Nodo) -> _Nodo:
    raiz = n.izq
    assert raiz is not None
    n.izq, raiz.der = raiz.der, n
    return raiz


def _rotar_izq(n: _Nodo) -> _Nodo:
    raiz = n.der
    assert raiz is not None
    n.der, raiz.izq = raiz.izq, n
    return raiz


def _insertar(raiz: Optional[_Nodo], valor: str, avl: bool) -> _Nodo:
    """Inserción en un ABB (los repetidos se ignoran); con `avl`, rebalancea con rotaciones."""
    if raiz is None:
        return _Nodo(valor)
    if _clave(valor) == _clave(raiz.valor):
        return raiz
    if _clave(valor) < _clave(raiz.valor):
        raiz.izq = _insertar(raiz.izq, valor, avl)
    else:
        raiz.der = _insertar(raiz.der, valor, avl)
    if not avl:
        return raiz
    if raiz.balance > 1:
        assert raiz.izq is not None
        if raiz.izq.balance < 0:
            raiz.izq = _rotar_izq(raiz.izq)
        return _rotar_der(raiz)
    if raiz.balance < -1:
        assert raiz.der is not None
        if raiz.der.balance > 0:
            raiz.der = _rotar_der(raiz.der)
        return _rotar_izq(raiz)
    return raiz


def _desde_niveles(valores: List[str], i: int = 0) -> Optional[_Nodo]:
    if i >= len(valores) or valores[i] in ("", "null", "None", "~"):
        return None
    return _Nodo(valores[i], _desde_niveles(valores, 2 * i + 1), _desde_niveles(valores, 2 * i + 2), i)


def _desde_anidado(dato: Any) -> Optional[_Nodo]:
    if dato is None:
        return None
    if not isinstance(dato, dict):
        return _Nodo(str(dato))
    return _Nodo(str(dato.get("value", "")), _desde_anidado(dato.get("left")), _desde_anidado(dato.get("right")))


def construir_arbol(b: Dict[str, Any]) -> Optional[_Nodo]:
    """El árbol del bloque: `insert` (ABB/AVL por inserciones), `root` (anidado) o `values` (por niveles)."""
    variante = b.get("variant", "binary")
    if b.get("insert") is not None:
        raiz = None
        for v in b["insert"]:
            raiz = _insertar(raiz, str(v), avl=variante == "avl")
        return raiz
    if b.get("root") is not None:
        return _desde_anidado(b["root"])
    return _desde_niveles(_valores(b))


def _arbol(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    raiz = construir_arbol(b)
    if raiz is None:
        raise ErrorDiagrama("el árbol no tiene nodos (usar values, insert o root)")
    variante = b.get("variant", "binary")
    estructura = b.get("nodeStyle") == "struct"
    sin_valores, nulls = bool(b.get("blankValues")), bool(b.get("nullLeaves", estructura))
    resaltados = {str(v) for v in b.get("highlight") or []}
    top = _encabezado(c, b)

    # Posición: x por recorrido en orden, y por profundidad.
    posiciones: List[Tuple[_Nodo, int, int]] = []

    def recorrer(n: Optional[_Nodo], prof: int) -> None:
        if n is None:
            return
        recorrer(n.izq, prof + 1)
        posiciones.append((n, len(posiciones), prof))
        recorrer(n.der, prof + 1)

    recorrer(raiz, 0)
    paso_x = 112 if estructura else (58 if variante in ("avl", "heap") else 50)
    nivel_h = 78 if estructura else 66
    margen = 30 + (24 if nulls else 0)
    radio = 19
    xy = {id(n): (margen + i * paso_x, top + 34 + p * nivel_h) for n, i, p in posiciones}
    nodo_w, nodo_h = 100, 36

    puntos: List[Tuple[float, float]] = []  # los orígenes de los punteros (nodo-estructura), arriba de todo

    for n, _, _ in posiciones:
        x, y = xy[id(n)]
        for lado, hijo in (("izq", n.izq), ("der", n.der)):
            signo = -1 if lado == "izq" else 1
            if estructura:
                if hijo is None:
                    continue
                sx, sy = x + signo * (nodo_w / 2 - 13), y + 6
                hx, hy = xy[id(hijo)]
                puntos.append((sx, sy))
                c.linea(sx, sy, hx, hy - nodo_h / 2 - 2, ancho=1.5)
            elif hijo is not None:
                hx, hy = xy[id(hijo)]
                largo = math.hypot(hx - x, hy - y)
                ux, uy = (hx - x) / largo, (hy - y) / largo
                c.linea(x + ux * radio, y + uy * radio, hx - ux * radio, hy - uy * radio, color="strokeMain",
                        ancho=1.5, flecha=None)
            elif nulls:
                sx, sy = x + signo * radio * 0.7, y + radio * 0.7
                c.linea(sx, sy, sx + signo * 16, sy + 22, color="strokeMuted", ancho=1, flecha=None, guiones="3 2")
                c.t(sx + signo * 16, sy + 32, "NULL", size=7.5, color="textMuted", ancla="middle")

    for n, _, _ in posiciones:
        x, y = xy[id(n)]
        relleno = "fillHighlight" if n.valor in resaltados else "fillCell"
        trazo = 2.6 if n.valor in resaltados else 1.6
        if estructura:
            izq_x, cel = x - nodo_w / 2, 26
            c.r(izq_x, y - nodo_h / 2, nodo_w, nodo_h, relleno=relleno, trazo=trazo, rx=3)
            c.r(izq_x, y - nodo_h / 2, cel, nodo_h, relleno="fillPointerBox")
            c.r(izq_x + nodo_w - cel, y - nodo_h / 2, cel, nodo_h, relleno="fillPointerBox")
            c.t(izq_x + cel / 2, y - nodo_h / 2 - 4, "*izq", size=7.5, color="textMuted", ancla="middle")
            c.t(izq_x + nodo_w - cel / 2, y - nodo_h / 2 - 4, "*der", size=7.5, color="textMuted", ancla="middle")
            for lado, hijo in (("izq", n.izq), ("der", n.der)):
                if hijo is None:
                    cx0 = izq_x if lado == "izq" else izq_x + nodo_w - cel
                    c.linea(cx0 + 4, y + nodo_h / 2 - 4, cx0 + cel - 4, y - nodo_h / 2 + 4, color="strokeMain",
                            ancho=1.3, flecha=None)
            if n.valor and not sin_valores:
                c.t(x, y + 5, n.valor, size=13, peso=700, ancla="middle")
            else:
                c.vacio(x - 18, x + 18, y + 10)
        else:
            c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio}" fill="{c.pal[relleno]}" '
                  f'stroke="{c.pal["strokeMain"]}" stroke-width="{trazo}"/>')
            if n.valor and not sin_valores:
                c.t(x, y + 4.5, n.valor, size=12.5 if len(n.valor) < 4 else 9.5, peso=700, ancla="middle")
            else:
                c.vacio(x - 9, x + 9, y + 7)
        if variante == "avl" and b.get("showBalance", True):
            c.r(x + radio - 2, y - radio - 8, 22, 14, relleno="fillBadge", trazo=1, rx=3)
            c.t(x + radio + 9, y - radio + 2.5, "__" if b.get("blankBalance") else f"{n.balance:+d}".replace("+0", "0"),
                size=8.5, peso=700, color="textSub", ancla="middle")
        if variante == "heap" and n.indice is not None:
            c.t(x, y + radio + 13, f"[{n.indice}]", size=8.5, color="textMuted", ancla="middle")
    for px, py in puntos:
        c.punto(px, py, radio=2.8)

    ancho = margen * 2 + (len(posiciones) - 1) * paso_x + (24 if variante == "avl" else 0)
    alto = top + 34 + raiz.altura * nivel_h - nivel_h + (nodo_h if estructura else radio) + (34 if nulls else 22)

    if variante == "heap" and b.get("showArray", True) and b.get("values"):
        sub = _Lienzo(c.pal, c.sufijo)
        ancho_a, alto_a = _arreglo(sub, {"values": _valores(b), "capacity": len(_valores(b)),
                                         "blankValues": b.get("blankValues")})
        c.add(f'<g transform="translate(0, {alto + 8:.1f})">', *sub.partes, "</g>")
        return max(ancho, ancho_a), alto + 8 + alto_a
    return ancho, alto


# ---------------------------------------------------------------------------
# Piezas comunes de los diagramas de texto: tablas y paneles
# ---------------------------------------------------------------------------

def _ancho_texto(texto: Any, size: float = 10) -> float:
    """Lo que ocupa `texto` en la fuente monoespaciada (0,62 em por carácter, con un poco de aire)."""
    return len(str(texto)) * size * 0.62


def _codigo(c: _Lienzo, x: float, y: float, texto: Any, size: float = 10.5, color: str = "textMain") -> None:
    """Un renglón de código: la sangría se dibuja corriendo el texto, porque el SVG colapsa los espacios."""
    linea = str(texto)
    sangria = len(linea) - len(linea.lstrip(" "))
    c.t(x + sangria * size * 0.602, y, linea.lstrip(" "), size=size, color=color)


def _lista_de(b: Dict[str, Any], clave: str, tipo: str) -> List[Any]:
    valor = b.get(clave)
    if not isinstance(valor, list) or not valor:
        raise ErrorDiagrama(f"'{clave}' de {tipo} tiene que ser una lista con al menos un elemento")
    return valor


def _tabla(c: _Lienzo, x: float, y: float, encabezados: List[str], filas: List[List[str]],
           izquierda: Tuple[int, ...] = (), tenues: Tuple[int, ...] = (), fila_h: float = 28,
           min_w: float = 46, anchos: Optional[List[float]] = None) -> Tuple[float, float]:
    """Tabla con encabezado; una celda `""` queda con la raya para completar. Devuelve (ancho, alto).

    `izquierda` son las columnas alineadas a la izquierda y `tenues`, las filas punteadas (relleno).
    """
    cab_h, size = 26, 10.5
    columnas = len(encabezados)
    if anchos is None:
        anchos = [max([min_w, _ancho_texto(encabezados[j], size) + 16]
                      + [_ancho_texto(f[j], size) + 18 for f in filas if j < len(f)]) for j in range(columnas)]
    cx = x
    for j, titulo in enumerate(encabezados):
        c.r(cx, y, anchos[j], cab_h, relleno="fillHeader", trazo=1.5)
        c.t(cx + anchos[j] / 2, y + 17, titulo, size=size, peso=700, ancla="middle")
        cx += anchos[j]
    for i, fila in enumerate(filas):
        fy, cx = y + cab_h + i * fila_h, x
        for j in range(columnas):
            w, texto = anchos[j], fila[j] if j < len(fila) else ""
            if i in tenues:
                c.add(f'<rect x="{cx:.1f}" y="{fy:.1f}" width="{w:.1f}" height="{fila_h}" fill="none" '
                      f'stroke="{c.pal["strokeMuted"]}" stroke-width="1" stroke-dasharray="4 3"/>')
            else:
                c.r(cx, fy, w, fila_h, trazo=1.2)
            color = "textMuted" if i in tenues else "textMain"
            if not texto:
                c.vacio(cx + 8, cx + w - 8, fy + fila_h - 8)
            elif j in izquierda:
                _codigo(c, cx + 9, fy + fila_h / 2 + 4, texto, size, color)
            else:
                c.t(cx + w / 2, fy + fila_h / 2 + 4, texto, size=size, peso=600, color=color, ancla="middle")
            cx += w
    return sum(anchos), cab_h + len(filas) * fila_h


def _panel(c: _Lienzo, x: float, y: float, w: float, titulo: str, lineas: List[str],
           alto: Optional[float] = None) -> float:
    """Recuadro con título y renglones de código; devuelve su alto."""
    cab_h, renglon = 24, 17
    h = alto if alto is not None else cab_h + 8 + max(1, len(lineas)) * renglon
    c.r(x, y, w, h, trazo=1.6, rx=4)
    c.add(f'<rect x="{x + 1:.1f}" y="{y + 1:.1f}" width="{w - 2:.1f}" height="{cab_h - 1}" rx="3" '
          f'fill="{c.pal["fillHeader"]}"/>')
    c.linea(x, y + cab_h, x + w, y + cab_h, color="strokeMain", ancho=1, flecha=None)
    c.t(x + 9, y + 16, titulo, size=11, peso=700, fuente=SANS)
    for i, linea in enumerate(lineas):
        if linea:
            _codigo(c, x + 10, y + cab_h + 17 + i * renglon, linea)
        else:
            c.vacio(x + 10, x + w - 10, y + cab_h + 19 + i * renglon)
    return h


def _ancho_panel(titulo: str, lineas: List[str]) -> float:
    return max([_ancho_texto(titulo, 11) + 20] + [_ancho_texto(linea, 10.5) + 22 for linea in lineas])


# ---------------------------------------------------------------------------
# Struct: disposición en memoria (offsets, relleno, sizeof) y tipo opaco
# ---------------------------------------------------------------------------

# LP64 (Linux y macOS de 64 bits): lo que da gcc en las máquinas del curso.
_TAMANOS_C = {"char": 1, "bool": 1, "_bool": 1, "short": 2, "int": 4, "unsigned": 4, "float": 4, "long": 8,
              "long long": 8, "double": 8, "size_t": 8, "int8_t": 1, "uint8_t": 1, "int16_t": 2, "uint16_t": 2,
              "int32_t": 4, "uint32_t": 4, "int64_t": 8, "uint64_t": 8}
_CAMPO = re.compile(r"^(?P<tipo>[\w ]*?[\w*])\s*(?P<estrella>\**)\s*(?P<nombre>\w+)(?P<dims>(?:\[\d+\])*)"
                    r"\s*(?:=\s*(?P<valor>.*))?$")
MAX_CAMPOS = 16


@dataclass
class _Campo:
    nombre: str
    tipo: str  # como se declara: `char`, `int *`
    dims: str = ""
    valor: str = ""
    tamano: int = 0
    alineacion: int = 1
    offset: int = 0
    en_blanco: bool = False

    @property
    def declaracion(self) -> str:
        separador = "" if self.tipo.endswith("*") else " "
        return f"{self.tipo}{separador}{self.nombre}{self.dims}"


def _medir_campo(campo: _Campo, tamano: Any, alineacion: Any, donde: str) -> None:
    """Tamaño y alineación del campo: los que declara o, si es un tipo básico, los de C."""
    if "*" in campo.tipo:
        base = 8
    else:
        tipo = re.sub(r"\b(const|volatile|signed|unsigned)\b", " ", campo.tipo.lower())
        tipo = " ".join(tipo.split()).removesuffix(" int") or ("unsigned" if "unsigned" in campo.tipo else "int")
        if tipo not in _TAMANOS_C and tamano is None:
            raise ErrorDiagrama(f"{donde}: no conozco el tamaño de '{campo.tipo}': indicalo con 'size' (y 'align')")
        base = _TAMANOS_C.get(tipo, 0)
    elementos = math.prod(int(d) for d in re.findall(r"\[(\d+)\]", campo.dims))
    campo.tamano = _entero(tamano, 0, 1, 1 << 20) if tamano is not None else base * elementos
    campo.alineacion = _entero(alineacion, 1, 1, 64) if alineacion is not None else base or min(campo.tamano, 8) or 1


def _campos(b: Dict[str, Any]) -> List[_Campo]:
    """`fields`: `"char nombre[8]"`, `"int edad = 30"` o `{name, type, value, size, align, blank}`."""
    datos = _lista_de(b, "fields", "un struct")
    if len(datos) > MAX_CAMPOS:
        raise ErrorDiagrama(f"el struct tiene {len(datos)} campos; el máximo es {MAX_CAMPOS}")
    campos = []
    for n, dato in enumerate(datos):
        donde = f"campo {n}"
        if isinstance(dato, dict):
            nombre = str(dato.get("name") or "")
            if not nombre or not dato.get("type"):
                raise ErrorDiagrama(f"{donde}: le falta 'name' o 'type'")
            dims = "".join(re.findall(r"\[\d+\]", nombre))
            campo = _Campo(nombre.split("[")[0], str(dato["type"]).strip(), dims, _texto(dato.get("value")),
                           en_blanco=bool(dato.get("blank")))
            _medir_campo(campo, dato.get("size"), dato.get("align"), donde)
        else:
            m = _CAMPO.match(str(dato).strip().rstrip(";"))
            if not m:
                raise ErrorDiagrama(f"{donde}: no entiendo {dato!r} (se espera «char nombre[8]» o «int edad = 30»)")
            tipo = m["tipo"].strip()
            tipo = f"{tipo} {m['estrella']}" if m["estrella"] else tipo
            campo = _Campo(m["nombre"], tipo, m["dims"], (m["valor"] or "").strip())
            _medir_campo(campo, None, None, donde)
        campos.append(campo)
    return campos


def disposicion_struct(campos: List[_Campo], empaquetado: bool = False) -> Tuple[List[Tuple[int, int]], int, int]:
    """Ubica los campos y devuelve ([(offset, bytes) de cada relleno], sizeof, alineación del struct)."""
    rellenos: List[Tuple[int, int]] = []
    offset, alineacion = 0, 1
    for campo in campos:
        al = 1 if empaquetado else campo.alineacion
        alineacion = max(alineacion, al)
        if offset % al:
            rellenos.append((offset, al - offset % al))
            offset += al - offset % al
        campo.offset = offset
        offset += campo.tamano
    if offset % alineacion:
        rellenos.append((offset, alineacion - offset % alineacion))
        offset += alineacion - offset % alineacion
    return rellenos, offset, alineacion


def _struct(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    variante = b.get("variant", "layout")
    if variante == "opaque":
        return _tipo_opaco(c, b)
    if variante != "layout":
        raise ErrorDiagrama(f"variante de struct no soportada: {variante!r} (layout u opaque)")
    campos = _campos(b)
    rellenos, sizeof, alineacion = disposicion_struct(campos, bool(b.get("packed")))
    nombre = str(b.get("name") or "struct registro")
    alias = b.get("typedef")
    top = _encabezado(c, b, f"typedef {nombre} {alias};" if alias else nombre)

    con_valores = any(f.valor for f in campos) or b.get("blankValues")
    direcciones = bool(b.get("showAddresses"))
    base = _hex(b.get("baseAddr"))
    sin_offsets, sin_tamanos = bool(b.get("blankOffsets")), bool(b.get("blankSizes"))
    sin_relleno, sin_valores = bool(b.get("blankPadding")), bool(b.get("blankValues"))

    def ubicacion(offset: int) -> str:
        if sin_offsets:
            return ""
        return _fmt_hex(base + offset) if direcciones else f"+{offset}"

    entradas: List[Tuple[int, List[str], bool]] = []
    for f in campos:
        fila = [ubicacion(f.offset), f.declaracion]
        if con_valores:
            fila.append("" if sin_valores or f.en_blanco else f.valor)
        entradas.append((f.offset, fila + ["" if sin_tamanos else f"{f.tamano} B"], False))
    if not sin_relleno:  # sin los rellenos, el alumno los deduce de los offsets
        for offset, bytes_relleno in rellenos:
            fila = [ubicacion(offset), "(relleno)"] + (["—"] if con_valores else [])
            entradas.append((offset, fila + ["" if sin_tamanos else f"{bytes_relleno} B"], True))
    entradas.sort(key=lambda e: e[0])
    encabezados = ["dirección" if direcciones else "offset", "campo"] + (["valor"] if con_valores else []) + ["tamaño"]
    tenues = tuple(i for i, e in enumerate(entradas) if e[2])
    ancho, alto = _tabla(c, 0, top + 6, encabezados, [e[1] for e in entradas], izquierda=(1,), tenues=tenues)
    y = top + 6 + alto + 20
    resultado = "______" if b.get("blankSizeof") else f"{sizeof} bytes"
    pie = f"sizeof({alias or nombre}) = {resultado}"
    if b.get("packed"):
        pie += " (empaquetado)"
    elif not b.get("blankSizeof"):
        pie += f" | alineación: {alineacion}"
    c.t(0, y, pie, size=11, peso=700)
    return max(ancho, _ancho_texto(pie, 11)), y + 8


def _tipo_opaco(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """Lo que ve cada archivo: `.h` público, cliente con un puntero y `.c` con los campos."""
    nombre = str(b.get("name") or "struct pila")
    etiqueta = nombre.removeprefix("struct ").strip()
    alias = str(b.get("typedef") or f"{etiqueta}_t")
    variable = str(b.get("variable") or "p")
    cabecera, fuente = str(b.get("header") or f"{etiqueta}.h"), str(b.get("source") or f"{etiqueta}.c")
    cliente = str(b.get("client") or "main.c")
    oculto = bool(b.get("hidden"))
    top = _encabezado(c, b)

    publico = [f"typedef {nombre} *{alias};"] + [str(o).rstrip(";") + ";" for o in b.get("operations") or []]
    titulo_h = f"{cabecera} (interfaz pública)"
    campos = [] if oculto and not b.get("fields") else _campos(b)
    privado = [f"{nombre} {{"] + (["    ¿?"] if oculto else [f"    {f.declaracion};" for f in campos]) + ["};"]
    if b.get("blankValues"):
        privado = [f"{nombre} {{"] + ["    " + "_" * 16 for _ in campos] + ["};"]
    titulo_c = f"{fuente} (implementación)"
    uso = [f'#include "{cabecera}"', f"{alias} {variable};"]
    titulo_u = f"{cliente} (cliente)"

    w_u, w_c = _ancho_panel(titulo_u, uso), _ancho_panel(titulo_c, privado)
    sep = 130
    w_h = max(_ancho_panel(titulo_h, publico), w_u + sep + w_c)
    w_c = w_h - w_u - sep  # los dos de abajo ocupan lo mismo que la interfaz
    y = top + 4
    alto_h = _panel(c, 0, y, w_h, titulo_h, publico)
    y2 = y + alto_h + 34
    alto = max(24 + 8 + len(uso) * 17 + 46, 24 + 8 + len(privado) * 17)
    c.linea(w_u / 2, y + alto_h, w_u / 2, y2 - 3, color="strokeSub", ancho=1.4, flecha="sub", guiones="4 2")
    c.t(w_u / 2 + 8, y + alto_h + 21, "incluye", size=9.5, color="textMuted")
    xc = w_u + sep
    c.linea(xc + w_c / 2, y + alto_h, xc + w_c / 2, y2 - 3, color="strokeSub", ancho=1.4, flecha="sub", guiones="4 2")
    c.t(xc + w_c / 2 + 8, y + alto_h + 21, "incluye", size=9.5, color="textMuted")
    _panel(c, 0, y2, w_u, titulo_u, uso, alto)
    _panel(c, xc, y2, w_c, titulo_c, privado, alto)

    # La variable es sólo un puntero: sizeof(alias) es lo único que conoce el cliente.
    py = y2 + alto - 30
    c.r(10, py, w_u - 20, 22, relleno="fillPointerBox", trazo=1.4, rx=3)
    c.t(18, py + 15, variable, size=10.5, peso=700)
    c.punto(w_u - 22, py + 11)
    c.linea(w_u - 22, py + 11, xc - 3, py + 11, ancho=1.6)
    muro = w_u + sep / 2
    c.linea(muro, y2 - 4, muro, y2 + alto + 4, color="strokeMain", ancho=2, flecha=None, guiones="6 4")
    c.t(muro, y2 + alto + 18, "el cliente no ve los campos", size=9.5, peso=600, color="textMuted", ancla="middle")
    return w_h, y2 + alto + 24


# ---------------------------------------------------------------------------
# TAD: operaciones públicas, invariante y representaciones posibles
# ---------------------------------------------------------------------------

def _tad(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    nombre = str(b.get("name") or "TAD")
    operaciones = _lista_de(b, "operations", "un TAD")
    sin_ops, sin_clases = bool(b.get("blankOperations")), bool(b.get("blankKinds"))
    top = _encabezado(c, b)

    filas: List[List[str]] = []
    con_clase = con_pre = con_post = False
    for op in operaciones:
        dato = op if isinstance(op, dict) else {"signature": op}
        if not dato.get("signature"):
            raise ErrorDiagrama("cada operación de un TAD tiene que tener 'signature'")
        en_blanco = sin_ops or dato.get("blank")
        clase, pre, post = (_texto(dato.get(k)) for k in ("kind", "pre", "post"))
        con_clase, con_pre, con_post = con_clase or bool(clase), con_pre or bool(pre), con_post or bool(post)
        filas.append(["" if en_blanco else str(dato["signature"]), "" if sin_clases else clase or "—",
                      pre or "—", post or "—"])
    columnas = [("operación", 0, True), ("clase", 1, con_clase or sin_clases), ("pre", 2, con_pre),
                ("post", 3, con_post)]
    usadas = [(t, j) for t, j, si in columnas if si]
    tabla = [[f[j] for _, j in usadas] for f in filas]
    encabezados = [t for t, _ in usadas]

    representaciones = []
    for r in b.get("representations") or []:
        dato = r if isinstance(r, dict) else {"name": r}
        lineas = [str(f) for f in dato.get("fields") or []]
        representaciones.append((str(dato.get("name") or "representación"), lineas))
    uso = [str(u) for u in b.get("client") or []]
    invariante = b.get("invariant")

    y = top + 4
    ancho_rep = sum(max(_ancho_panel(t, ls), 130) + 24 for t, ls in representaciones) - 24
    ancho = ancho_rep
    if uso:
        titulo_u = "Cliente: sólo usa las operaciones"
        ancho_u = _ancho_panel(titulo_u, uso)
        alto_u = _panel(c, 0, y, ancho_u, titulo_u, uso)
        ancho = max(ancho, ancho_u)
        c.linea(ancho_u / 2, y + alto_u, ancho_u / 2, y + alto_u + 26, ancho=1.5)
        y += alto_u + 29
    c.t(0, y + 13, f"TAD {nombre}: interfaz", size=11.5, peso=700, fuente=SANS)
    w_t, h_t = _tabla(c, 0, y + 22, encabezados, tabla, izquierda=tuple(range(len(encabezados))), min_w=70)
    ancho = max(ancho, w_t)
    y += 22 + h_t
    if invariante:
        y += 18
        texto = f"Invariante: {invariante}"
        c.t(0, y, texto, size=10.5, peso=600, color="textSub")
        ancho = max(ancho, _ancho_texto(texto, 10.5))
    if representaciones:
        y_rep = y + 44
        c.t(0, y + 18, "Representaciones posibles (ocultas para el cliente):", size=10, peso=600, color="textMuted")
        alto_rep = max(24 + 8 + max(1, len(ls)) * 17 for _, ls in representaciones)
        x = 0.0
        for titulo, lineas in representaciones:
            w = max(_ancho_panel(titulo, lineas), 130)
            _panel(c, x, y_rep, w, titulo, lineas, alto_rep)
            x += w + 24
        y = y_rep + alto_rep
    return ancho, y + 8


# ---------------------------------------------------------------------------
# Complejidad: curvas de crecimiento y clases anidadas
# ---------------------------------------------------------------------------

_CRECIMIENTOS: Dict[str, Tuple[str, Callable[[float], float]]] = {
    "1": ("O(1)", lambda n: 1.0),
    "log n": ("O(log n)", lambda n: math.log2(n)),
    "sqrt n": ("O(√n)", math.sqrt),
    "n": ("O(n)", lambda n: n),
    "n log n": ("O(n log n)", lambda n: n * math.log2(n)),
    "n^2": ("O(n²)", lambda n: n ** 2),
    "n^3": ("O(n³)", lambda n: n ** 3),
    "2^n": ("O(2ⁿ)", lambda n: 2.0 ** n),
    "n!": ("O(n!)", lambda n: math.gamma(n + 1)),
}
_CLASES_COMUNES = ["1", "log n", "n", "n log n", "n^2", "2^n"]
_GUIONES = ("", "7 3", "2 3", "9 3 2 3")
MAX_CURVAS = 9


def _clave_crecimiento(texto: Any) -> str:
    """`O(n²)`, `n^2`, `Θ(n log n)`… como clave de `_CRECIMIENTOS`."""
    clave = str(texto).strip().lower().replace("²", "^2").replace("³", "^3").replace("ⁿ", "^n").replace("√n", "sqrt n")
    m = re.fullmatch(r"[oθω]\((.*)\)", clave)
    clave = " ".join((m[1] if m else clave).split())
    if clave not in _CRECIMIENTOS:
        raise ErrorDiagrama(f"crecimiento desconocido: {texto!r} (disponibles: {', '.join(_CRECIMIENTOS)})")
    return clave


def _evaluar(funcion: Callable[[float], float], n: float) -> float:
    try:
        return funcion(n)
    except OverflowError:  # 2^n y n! con un `maxN` grande: se sale del gráfico igual
        return math.inf


def _complejidad(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    variante = b.get("variant", "growth")
    if variante == "classes":
        return _clases(c, b)
    if variante != "growth":
        raise ErrorDiagrama(f"variante de complexity no soportada: {variante!r} (growth o classes)")
    datos = b.get("curves") or _CLASES_COMUNES
    if not isinstance(datos, list) or len(datos) > MAX_CURVAS:
        raise ErrorDiagrama(f"'curves' tiene que ser una lista de hasta {MAX_CURVAS} curvas")
    max_n, max_y = _entero(b.get("maxN"), 20, 2, 10000), _entero(b.get("maxY"), 100, 2, 10 ** 9)
    top = _encabezado(c, b)
    x0, w, h = 52, 420, 260
    y0 = top + 38
    sx, sy = w / max_n, h / max_y

    def px(n: float) -> float:
        return x0 + n * sx

    def py(valor: float) -> float:
        return y0 + h - valor * sy

    for k in range(5):  # marcas de los ejes
        n, v = max_n * k / 4, max_y * k / 4
        c.linea(px(n), y0 + h, px(n), y0 + h + 4, color="strokeMain", ancho=1, flecha=None)
        c.t(px(n), y0 + h + 16, f"{n:g}", size=9, color="textSub", ancla="middle")
        c.linea(x0 - 4, py(v), x0, py(v), color="strokeMain", ancho=1, flecha=None)
        c.t(x0 - 7, py(v) + 3, f"{v:g}", size=9, color="textSub", ancla="end")
        if k:
            c.linea(x0, py(v), x0 + w, py(v), color="strokeMuted", ancho=0.5, flecha=None, guiones="2 4")
    c.linea(x0, y0 + h, x0 + w + 8, y0 + h, color="strokeMain", ancho=1.6)
    c.linea(x0, y0 + h, x0, y0 - 8, color="strokeMain", ancho=1.6)
    c.t(x0 + w / 2, y0 + h + 32, str(b.get("xLabel") or "n (tamaño de la entrada)"), size=10, peso=600,
        ancla="middle")
    c.t(0, y0 - 22, str(b.get("yLabel") or "operaciones"), size=10, peso=600)

    derecha: List[Tuple[float, str]] = []
    arriba: List[Tuple[float, str]] = []
    sueltas: List[Tuple[float, float, str]] = []  # mediciones que terminan adentro del gráfico
    for i, dato in enumerate(datos):
        etiqueta = chr(ord("A") + i) if b.get("blankLabels") else None
        if isinstance(dato, dict):  # mediciones: {label, points: [[n, t], …]}
            try:
                puntos = sorted((float(p[0]), float(p[1])) for p in dato.get("points") or [])
            except (TypeError, ValueError, IndexError):
                raise ErrorDiagrama(f"curva {i}: 'points' tiene que ser una lista de [n, valor]") from None
            if not puntos:
                raise ErrorDiagrama(f"curva {i}: le falta 'points' (o usar un nombre, como n^2)")
            etiqueta = etiqueta or str(dato.get("label") or f"curva {i + 1}")
            for n, v in puntos:
                if n <= max_n and v <= max_y:
                    c.punto(px(n), py(v), radio=2.6)
        else:
            clave = _clave_crecimiento(dato)
            nombre, funcion = _CRECIMIENTOS[clave]
            etiqueta = etiqueta or nombre
            enteras = clave in ("1", "n", "n^2", "n^3", "sqrt n")  # las demás no están definidas antes de 1
            puntos = [(n, _evaluar(funcion, n)) for n in (max_n * k / 240 for k in range(1, 241)) if n >= 1 or enteras]
        trazo: List[Tuple[float, float]] = []
        for n, v in puntos:
            if n > max_n:
                break
            if v > max_y:  # sale por arriba: se corta justo en el borde
                if trazo:
                    n0, v0 = trazo[-1]
                    corte = (max_y - v0) / (v - v0) if math.isfinite(v) else 0
                    trazo.append((n0 + (n - n0) * corte, float(max_y)))
                break
            trazo.append((n, v))
        if not trazo:
            continue
        camino = " ".join(f"{px(n):.1f},{py(v):.1f}" for n, v in trazo)
        guiones = _GUIONES[i % len(_GUIONES)]
        c.add(f'<polyline points="{camino}" fill="none" stroke="{c.pal["strokeMain"]}" stroke-width="1.8"'
              + (f' stroke-dasharray="{guiones}"' if guiones else "") + "/>")
        n_fin, v_fin = trazo[-1]
        if v_fin >= max_y:
            arriba.append((px(n_fin), etiqueta))
        elif n_fin >= max_n * 0.98:
            derecha.append((py(v_fin), etiqueta))
        else:
            sueltas.append((px(n_fin), py(v_fin), etiqueta))

    # Etiquetas al final de cada curva, corridas lo justo para no pisarse.
    borde = x0 + w + 8
    ancho: float = borde
    tope = y0 + h + 14.0
    for y_fin, etiqueta in sorted(derecha, reverse=True):
        tope = min(y_fin + 4, tope - 14)
        c.t(borde, tope, etiqueta, size=10.5, peso=700)
        ancho = max(ancho, borde + _ancho_texto(etiqueta, 10.5))
    for x_fin, y_fin, etiqueta in sueltas:
        c.t(x_fin + 8, y_fin + 4, etiqueta, size=10.5, peso=700)
        ancho = max(ancho, x_fin + 8 + _ancho_texto(etiqueta, 10.5))
    siguiente = 0.0
    for x_fin, etiqueta in sorted(arriba):
        x = max(x_fin, siguiente)
        c.t(x, y0 - 6, etiqueta, size=10.5, peso=700, ancla="middle")
        siguiente = x + _ancho_texto(etiqueta, 10.5) + 8
        ancho = max(ancho, x + _ancho_texto(etiqueta, 10.5) / 2)
    return ancho + 4, y0 + h + 40


def _clases(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """Conjuntos anidados, del más chico al más grande: O(1) ⊂ O(log n) ⊂ …, o P ⊂ NP."""
    datos = b.get("classes") or [_CRECIMIENTOS[k][0] for k in _CLASES_COMUNES]
    if not isinstance(datos, list) or not datos or len(datos) > 10:
        raise ErrorDiagrama("'classes' tiene que ser una lista de hasta 10 clases, de la más chica a la más grande")
    clases = [str(d) for d in datos]
    items = b.get("items") or {}
    if not isinstance(items, dict):
        raise ErrorDiagrama("'items' tiene que decir qué va en cada clase: {'O(n)': [búsqueda lineal]}")
    for clase in items:
        if str(clase) not in clases:
            raise ErrorDiagrama(f"'items' nombra una clase que no está en 'classes': {clase!r}")
    contenido = {str(k): [str(i) for i in (v if isinstance(v, list) else [v])] for k, v in items.items()}
    sin_clases = bool(b.get("blankClasses"))
    top = _encabezado(c, b)

    margen, renglon, cab = 14, 15, 24
    medidas: List[Tuple[float, float]] = []  # (ancho, alto) de cada clase, de adentro hacia afuera
    interior_w = interior_h = 0.0
    for clase in clases:
        lista = contenido.get(clase, [])
        texto_w = max([_ancho_texto(clase, 11.5)] + [_ancho_texto(f"• {i}", 10) for i in lista]) + 2 * margen
        banda = cab + len(lista) * renglon
        interior_w = max(interior_w + 2 * margen, texto_w, 90)
        interior_h = interior_h + banda + (margen if interior_h else 6)
        medidas.append((interior_w, interior_h))
    ancho_total, alto_total = medidas[-1]
    # De afuera hacia adentro: cada clase se apoya abajo de la banda de la que la contiene.
    y = top + 4
    for k in range(len(clases) - 1, -1, -1):
        w, h = medidas[k]
        x = (ancho_total - w) / 2
        relleno = "fillHeader" if (len(clases) - 1 - k) % 2 == 0 else "fillCell"
        c.r(x, y, w, h, relleno=relleno, trazo=1.6, rx=8)
        if sin_clases:
            c.vacio(x + margen, x + margen + 70, y + 18)
        else:
            c.t(x + margen, y + 17, clases[k], size=11.5, peso=700)
        lista = contenido.get(clases[k], [])
        for n, item in enumerate(lista):
            c.t(x + margen, y + cab + 8 + n * renglon, f"• {item}", size=10)
        y += cab + len(lista) * renglon
    return ancho_total, top + 4 + alto_total + 6


# ---------------------------------------------------------------------------
# Diagrama de flujo: secuencia, decisión y repetición
# ---------------------------------------------------------------------------

_SEP_FLUJO = 26


@dataclass
class _Paso:
    tipo: str  # proceso, io, si o mientras
    texto: str
    a: List["_Paso"] = field(default_factory=list)  # entonces / cuerpo
    b: List["_Paso"] = field(default_factory=list)  # si no
    en_blanco: bool = False


def _pasos_flujo(dato: Any, donde: str) -> List[_Paso]:
    if dato is None:
        return []
    if not isinstance(dato, list):
        raise ErrorDiagrama(f"{donde}: los pasos van en una lista")
    pasos = []
    for n, p in enumerate(dato):
        lugar = f"{donde}, paso {n}"
        if not isinstance(p, dict):
            pasos.append(_Paso("proceso", _texto(p)))
            continue
        blanco = bool(p.get("blank"))
        if "if" in p:
            pasos.append(_Paso("si", _texto(p["if"]), _pasos_flujo(p.get("then"), lugar),
                               _pasos_flujo(p.get("else"), lugar), blanco))
        elif "while" in p or "for" in p:
            cuerpo = _pasos_flujo(p.get("do"), lugar)
            if not cuerpo:
                raise ErrorDiagrama(f"{lugar}: la repetición no tiene cuerpo ('do')")
            pasos.append(_Paso("mientras", _texto(p.get("while", p.get("for"))), cuerpo, en_blanco=blanco))
        elif "io" in p:
            pasos.append(_Paso("io", _texto(p["io"]), en_blanco=blanco))
        elif "step" in p:
            pasos.append(_Paso("proceso", _texto(p["step"]), en_blanco=blanco))
        else:
            raise ErrorDiagrama(f"{lugar}: se espera un texto o una clave if, while, for, io o step")
    return pasos


def _ancho_caja(p: _Paso) -> float:
    return max(110, _ancho_texto(p.texto, 10.5) + 26)


def _ancho_rombo(p: _Paso) -> float:
    return max(130, _ancho_texto(p.texto, 10.5) * 1.7 + 30)


_ALTO_ROMBO = 60


def _medir_lista(pasos: List[_Paso]) -> Tuple[float, float, float]:
    """(a la izquierda del eje, a la derecha, alto) de una secuencia de pasos."""
    if not pasos:
        return 0, 0, 0
    medidas = [_medir_paso(p) for p in pasos]
    return (max(m[0] for m in medidas), max(m[1] for m in medidas),
            sum(m[2] for m in medidas) + _SEP_FLUJO * (len(pasos) - 1))


def _desvios(p: _Paso) -> Tuple[float, float]:
    """Cuánto se separan del eje las dos ramas de una decisión."""
    medio = _ancho_rombo(p) / 2
    return max(medio + 12, _medir_lista(p.a)[1] + 16), max(medio + 12, _medir_lista(p.b)[0] + 16)


def _medir_paso(p: _Paso) -> Tuple[float, float, float]:
    if p.tipo in ("proceso", "io"):
        w = _ancho_caja(p) + (24 if p.tipo == "io" else 0)
        return w / 2, w / 2, 34
    medio = _ancho_rombo(p) / 2
    izq, der, alto = _medir_lista(p.a)
    if p.tipo == "mientras":
        return max(medio, izq) + 22, max(medio, der) + 34, _ALTO_ROMBO + _SEP_FLUJO + alto + 34
    izq_b, der_b, alto_b = _medir_lista(p.b)
    dx_a, dx_b = _desvios(p)
    return dx_a + izq, dx_b + der_b, _ALTO_ROMBO + _SEP_FLUJO + max(alto, alto_b) + _SEP_FLUJO


def _texto_flujo(c: _Lienzo, p: _Paso, x: float, y: float, sin_valores: bool) -> None:
    if p.texto and not (p.en_blanco or sin_valores):
        c.t(x, y + 4, p.texto, size=10.5, peso=600, ancla="middle")
    else:
        c.vacio(x - 32, x + 32, y + 6)


def _dibujar_lista(c: _Lienzo, pasos: List[_Paso], x: float, y: float, sin_valores: bool) -> float:
    for i, p in enumerate(pasos):
        if i:
            c.linea(x, y, x, y + _SEP_FLUJO - 3, color="strokeMain", ancho=1.5)
            y += _SEP_FLUJO
        y = _dibujar_paso(c, p, x, y, sin_valores)
    return y


def _camino(c: _Lienzo, puntos: List[Tuple[float, float]], flecha: bool = True) -> None:
    trazo = " L ".join(f"{x:.1f} {y:.1f}" for x, y in puntos)
    marca = f' marker-end="url(#flecha-main-{c.sufijo})"' if flecha else ""
    c.add(f'<path d="M {trazo}" fill="none" stroke="{c.pal["strokeMain"]}" stroke-width="1.5"{marca}/>')


def _rombo(c: _Lienzo, p: _Paso, x: float, y: float, sin_valores: bool) -> None:
    medio, alto = _ancho_rombo(p) / 2, _ALTO_ROMBO
    c.add(f'<polygon points="{x:.1f},{y:.1f} {x + medio:.1f},{y + alto / 2:.1f} {x:.1f},{y + alto:.1f} '
          f'{x - medio:.1f},{y + alto / 2:.1f}" fill="{c.pal["fillHeader"]}" stroke="{c.pal["strokeMain"]}" '
          f'stroke-width="1.6"/>')
    _texto_flujo(c, p, x, y + alto / 2, sin_valores)


def _dibujar_paso(c: _Lienzo, p: _Paso, x: float, y: float, sin_valores: bool) -> float:
    """Dibuja el paso con su eje en `x` y la entrada en `y`; devuelve dónde sale."""
    if p.tipo == "proceso":
        w = _ancho_caja(p)
        c.r(x - w / 2, y, w, 34, trazo=1.6)
        _texto_flujo(c, p, x, y + 17, sin_valores)
        return y + 34
    if p.tipo == "io":
        w, inc = _ancho_caja(p) + 24, 12
        c.add(f'<polygon points="{x - w / 2 + inc:.1f},{y:.1f} {x + w / 2:.1f},{y:.1f} {x + w / 2 - inc:.1f},'
              f'{y + 34:.1f} {x - w / 2:.1f},{y + 34:.1f}" fill="{c.pal["fillCell"]}" '
              f'stroke="{c.pal["strokeMain"]}" stroke-width="1.6"/>')
        _texto_flujo(c, p, x, y + 17, sin_valores)
        return y + 34

    medio, medio_y = _ancho_rombo(p) / 2, y + _ALTO_ROMBO / 2
    _rombo(c, p, x, y, sin_valores)
    cuerpo_y = y + _ALTO_ROMBO + _SEP_FLUJO
    if p.tipo == "mientras":
        izq, der, _ = _medir_paso(p)
        c.linea(x, y + _ALTO_ROMBO, x, cuerpo_y - 3, color="strokeMain", ancho=1.5)
        c.t(x + 6, y + _ALTO_ROMBO + 15, "Sí", size=9.5, peso=700, fuente=SANS)
        fin = _dibujar_lista(c, p.a, x, cuerpo_y, sin_valores)
        vuelta, salida = fin + 12, fin + 34
        # La vuelta entra por la línea que llega al rombo.
        _camino(c, [(x, fin), (x, vuelta), (x - izq + 4, vuelta), (x - izq + 4, y - 11), (x - 3, y - 11)])
        c.t(x + medio + 4, medio_y - 6, "No", size=9.5, peso=700, fuente=SANS)
        _camino(c, [(x + medio, medio_y), (x + der - 6, medio_y), (x + der - 6, salida), (x, salida)], flecha=False)
        return salida

    dx_a, dx_b = _desvios(p)
    fin_a = _dibujar_lista(c, p.a, x - dx_a, cuerpo_y, sin_valores) if p.a else medio_y
    fin_b = _dibujar_lista(c, p.b, x + dx_b, cuerpo_y, sin_valores) if p.b else medio_y
    union = max(fin_a, fin_b, cuerpo_y) + _SEP_FLUJO
    c.t(x - medio - 4, medio_y - 6, "Sí", size=9.5, peso=700, ancla="end", fuente=SANS)
    c.t(x + medio + 4, medio_y - 6, "No", size=9.5, peso=700, fuente=SANS)
    entrada = [(x - medio, medio_y), (x - dx_a, medio_y)]
    _camino(c, entrada + [(x - dx_a, cuerpo_y - 2)] if p.a else entrada + [(x - dx_a, union), (x - 3, union)])
    entrada = [(x + medio, medio_y), (x + dx_b, medio_y)]
    _camino(c, entrada + [(x + dx_b, cuerpo_y - 2)] if p.b else entrada + [(x + dx_b, union), (x + 3, union)])
    if p.a:
        _camino(c, [(x - dx_a, fin_a), (x - dx_a, union), (x - 3, union)])
    if p.b:
        _camino(c, [(x + dx_b, fin_b), (x + dx_b, union), (x + 3, union)])
    return union


def _flujo(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    pasos = _pasos_flujo(_lista_de(b, "steps", "un diagrama de flujo"), "diagrama de flujo")
    top = _encabezado(c, b)
    sin_valores = bool(b.get("blankValues"))
    inicio, fin = b.get("start", "Inicio"), b.get("end", "Fin")
    izq, der, _ = _medir_lista(pasos)
    x, y = max(izq, 60) + 4, top + 6

    def terminal(texto: Any, ty: float) -> None:
        w = max(80, _ancho_texto(texto, 10.5) + 30)
        c.r(x - w / 2, ty, w, 30, relleno="fillHeader", trazo=1.6, rx=15)
        c.t(x, ty + 19, texto, size=10.5, peso=700, ancla="middle")

    if inicio:
        terminal(inicio, y)
        c.linea(x, y + 30, x, y + 30 + _SEP_FLUJO - 3, color="strokeMain", ancho=1.5)
        y += 30 + _SEP_FLUJO
    y = _dibujar_lista(c, pasos, x, y, sin_valores)
    if fin:
        c.linea(x, y, x, y + _SEP_FLUJO - 3, color="strokeMain", ancho=1.5)
        y += _SEP_FLUJO
        terminal(fin, y)
        y += 30
    return x + max(der, 60) + 4, y + 4


# ---------------------------------------------------------------------------
# Análisis de algoritmos: costo por línea y tabla de traza
# ---------------------------------------------------------------------------

def _costos(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """Cada línea con su costo y cuántas veces se ejecuta, y el T(n) que resulta."""
    lineas = _lista_de(b, "lines", "una tabla de costos")
    sin_costos, sin_veces = bool(b.get("blankCosts")), bool(b.get("blankTimes"))
    filas = []
    for n, linea in enumerate(lineas, 1):
        if isinstance(linea, dict):
            codigo, costo, veces = linea.get("code"), linea.get("cost"), linea.get("times")
        elif isinstance(linea, list) and 1 <= len(linea) <= 3:
            codigo, costo, veces = (linea + [None, None])[:3]
        else:
            codigo, costo, veces = linea, None, None
        filas.append([str(n), _texto(codigo), "" if sin_costos else _texto(costo), "" if sin_veces else _texto(veces)])
    top = _encabezado(c, b)
    ancho, alto = _tabla(c, 0, top + 6, ["#", "código", "costo", "veces"], filas, izquierda=(1,), min_w=30)
    y = top + 6 + alto
    total = b.get("total")
    if total is not None or b.get("blankTotal"):
        y += 22
        texto = "T(n) = " + ("_" * 24 if b.get("blankTotal") else str(total))
        c.t(0, y, texto, size=12, peso=700)
        ancho = max(ancho, _ancho_texto(texto, 12))
    return ancho, y + 8


def _traza(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    """Tabla de traza: la de statics (`operations` y `capacity`) o de variables (`columns`, `rows`)."""
    operaciones = [str(o) for o in b.get("operations") or []]
    top = _encabezado(c, b)
    columnas = b.get("columns")
    if columnas is not None:
        if not isinstance(columnas, list) or not columnas:
            raise ErrorDiagrama("'columns' de una traza tiene que ser una lista con al menos una columna")
        encabezados = [str(x) for x in columnas]
        filas_dato = b.get("rows") or []
        if not isinstance(filas_dato, list) or not all(isinstance(f, list) for f in filas_dato):
            raise ErrorDiagrama("'rows' de una traza tiene que ser una lista de filas")
        sin_valores = bool(b.get("blankValues"))
        cantidad = max(len(filas_dato), len(operaciones), _entero(b.get("rowCount"), 0, 0, 30))
        if not cantidad:
            raise ErrorDiagrama("la traza no tiene filas (usar rows, operations o rowCount)")
        filas = []
        for i in range(cantidad):
            dato = filas_dato[i] if i < len(filas_dato) else []
            if len(dato) > len(encabezados):
                raise ErrorDiagrama(f"la fila {i} de la traza tiene {len(dato)} valores y hay "
                                    f"{len(encabezados)} columnas")
            celdas = ["" if sin_valores else _texto(v) for v in dato]
            celdas += [""] * (len(encabezados) - len(celdas))
            filas.append(([operaciones[i] if i < len(operaciones) else ""] + celdas) if operaciones else celdas)
        if operaciones:
            encabezados = [str(b.get("operationHeader") or "Instrucción")] + encabezados
        ancho, alto = _tabla(c, 0, top + 6, encabezados, filas, izquierda=(0,) if operaciones else ())
        return ancho, top + 6 + alto + 8
    if not operaciones:
        raise ErrorDiagrama("la traza no tiene filas (usar operations, o columns y rows)")
    cap = _entero(b.get("capacity"), 6, 3, 10)
    pila = b.get("variant") == "stack"
    puntero = str(b.get("pointerHeader") or ("Puntero TOPE" if pila else "Punteros / Índ."))
    marca = str(b.get("pointerLabel") or ("TOPE: ___" if pila else "F:___ R:___"))
    indices = [f"[{i}]" for i in range(cap)] if b.get("showIndexHeader", True) else [" "] * cap
    encabezados = ["Operación / Instrucción C", *indices, puntero]
    filas = [[o] + [""] * cap + [marca] for o in operaciones]
    ancho, alto = _tabla(c, 0, top + 6, encabezados, filas, izquierda=(0, cap + 1), fila_h=36, min_w=40)
    return ancho, top + 6 + alto + 8


# ---------------------------------------------------------------------------
# Árbol de llamadas de una función recursiva
# ---------------------------------------------------------------------------

MAX_LLAMADAS = 40


@dataclass
class _Llamada:
    texto: str
    retorno: str = ""
    hijos: List["_Llamada"] = field(default_factory=list)
    x: float = 0
    prof: int = 0
    orden: int = 0
    ancho_arbol: float = 0
    en_blanco: bool = False


def _llamadas(dato: Any, prof: int = 0) -> _Llamada:
    if isinstance(dato, dict):
        if not dato.get("call"):
            raise ErrorDiagrama("cada nodo de un árbol de llamadas tiene que tener 'call'")
        hijos = dato.get("children") or []
        if not isinstance(hijos, list):
            raise ErrorDiagrama("'children' de un árbol de llamadas tiene que ser una lista")
        return _Llamada(str(dato["call"]), _texto(dato.get("returns")), [_llamadas(h, prof + 1) for h in hijos],
                        prof=prof, en_blanco=bool(dato.get("blank")))
    return _Llamada(_texto(dato), prof=prof)


def _arbol_llamadas(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    if not b.get("root"):
        raise ErrorDiagrama("el árbol de llamadas no tiene 'root' ({call, returns, children})")
    raiz = _llamadas(b["root"])
    nodos: List[_Llamada] = []

    def en_orden(n: _Llamada) -> None:  # el orden en que se hacen las llamadas
        nodos.append(n)
        n.orden = len(nodos)
        for h in n.hijos:
            en_orden(h)

    en_orden(raiz)
    if len(nodos) > MAX_LLAMADAS:
        raise ErrorDiagrama(f"el árbol tiene {len(nodos)} llamadas; el máximo es {MAX_LLAMADAS}")
    sin_retornos, sin_llamadas = bool(b.get("blankReturns")), bool(b.get("blankCalls"))
    con_orden = bool(b.get("showOrder"))
    resaltados = {str(v) for v in b.get("highlight") or []}
    con_retorno = sin_retornos or any(n.retorno for n in nodos)
    top = _encabezado(c, b)
    alto_nodo, nivel_h, sep = (42 if con_retorno else 28), 76, 14

    def ancho_nodo(n: _Llamada) -> float:
        return max(58, _ancho_texto(n.texto, 11) + 18, _ancho_texto(f"→ {n.retorno}", 10) + 16)

    def medir(n: _Llamada) -> float:
        hijos = sum(medir(h) for h in n.hijos) + sep * max(0, len(n.hijos) - 1)
        n.ancho_arbol = max(ancho_nodo(n), hijos)
        return n.ancho_arbol

    def ubicar(n: _Llamada, x: float) -> None:
        hijos = sum(h.ancho_arbol for h in n.hijos) + sep * max(0, len(n.hijos) - 1)
        cursor = x + (n.ancho_arbol - hijos) / 2
        for h in n.hijos:
            ubicar(h, cursor)
            cursor += h.ancho_arbol + sep
        n.x = (n.hijos[0].x + n.hijos[-1].x) / 2 if n.hijos else x + n.ancho_arbol / 2

    medir(raiz)
    ubicar(raiz, 10 if con_orden else 0)
    y0 = top + 12

    def y_de(n: _Llamada) -> float:
        return y0 + n.prof * nivel_h

    for n in nodos:
        for h in n.hijos:
            c.linea(n.x, y_de(n) + alto_nodo, h.x, y_de(h) - 3, ancho=1.5)
    for n in nodos:
        w, y = ancho_nodo(n), y_de(n)
        marcada = n.texto in resaltados
        c.r(n.x - w / 2, y, w, alto_nodo, relleno="fillHighlight" if marcada else "fillCell",
            trazo=2.4 if marcada else 1.6, rx=4)
        if sin_llamadas or n.en_blanco:
            c.vacio(n.x - w / 2 + 8, n.x + w / 2 - 8, y + 20)
        else:
            c.t(n.x, y + 18, n.texto, size=11, peso=700, ancla="middle")
        if con_retorno:
            if sin_retornos or not n.retorno:
                c.t(n.x - w / 2 + 8, y + 35, "→", size=10, color="textSub")
                c.vacio(n.x - w / 2 + 22, n.x + w / 2 - 8, y + 37)
            else:
                c.t(n.x, y + 35, f"→ {n.retorno}", size=10, color="textSub", ancla="middle")
        if con_orden:
            c.add(f'<circle cx="{n.x - w / 2:.1f}" cy="{y:.1f}" r="9" fill="{c.pal["fillBadge"]}" '
                  f'stroke="{c.pal["strokeMain"]}" stroke-width="1.1"/>')
            c.t(n.x - w / 2, y + 3.5, n.orden, size=9, peso=700, ancla="middle")

    profundidad = max(n.prof for n in nodos)
    ancho = raiz.ancho_arbol + (10 if con_orden else 0)
    alto = y0 + profundidad * nivel_h + alto_nodo + 8
    niveles = b.get("levelCosts")
    if niveles is not None or b.get("blankLevelCosts"):
        datos = list(niveles or [])
        x = ancho + 34
        textos = ["" if b.get("blankLevelCosts") or i >= len(datos) else _texto(datos[i]) for i in range(profundidad + 1)]
        col_w = max([_ancho_texto(t, 10.5) for t in textos] + [_ancho_texto("costo del nivel", 9.5), 90])
        c.t(x, y0 - 8, "costo del nivel", size=9.5, peso=700, color="textSub")
        for i, texto in enumerate(textos):
            y = y0 + i * nivel_h + alto_nodo / 2
            c.linea(x - 28, y, x - 6, y, color="strokeMuted", ancho=1, flecha=None, guiones="3 2")
            if texto:
                c.t(x, y + 4, texto, size=10.5, peso=700)
            else:
                c.vacio(x, x + col_w, y + 6)
        ancho = x + col_w
    total = b.get("total")
    if total is not None or b.get("blankTotal"):
        texto = "T(n) = " + ("_" * 24 if b.get("blankTotal") else str(total))
        c.t(0, alto + 12, texto, size=12, peso=700)
        ancho, alto = max(ancho, _ancho_texto(texto, 12)), alto + 20
    return ancho, alto


_RENDERIZADORES: Dict[str, Callable[[_Lienzo, Dict[str, Any]], Tuple[float, float]]] = {
    "array": _arreglo, "matrix": _matriz, "linked_list": _lista, "stack": _pila, "call_stack": _pila_llamadas,
    "call_tree": _arbol_llamadas, "queue": _cola, "tree": _arbol, "struct": _struct, "adt": _tad,
    "complexity": _complejidad, "flowchart": _flujo, "cost_table": _costos, "trace_table": _traza,
}


def renderizar(bloque: Dict[str, Any], tinta: bool = True) -> str:
    """El bloque como un `<svg>` independiente (con su tamaño y sus marcadores de flecha).

    `tinta` usa la paleta de ahorro de tinta de statics (negro), para imprimir; False, la de color.
    """
    if not isinstance(bloque, dict):
        raise ErrorDiagrama("el bloque tiene que ser un diccionario con 'type'")
    tipo = bloque.get("type")
    if tipo not in _RENDERIZADORES:
        raise ErrorDiagrama(f"tipo de bloque no soportado: {tipo!r} (disponibles: {', '.join(TIPOS)})")
    pal = PALETAS[bool(bloque.get("inkSaver", tinta))]
    try:
        huella = json.dumps(bloque, sort_keys=True, default=str)
    except TypeError:  # claves de otro tipo (YAML lee `no:` como false)
        huella = repr(bloque)
    sufijo = hashlib.sha1(huella.encode()).hexdigest()[:8]
    lienzo = _Lienzo(pal, sufijo)
    try:
        ancho, alto = _RENDERIZADORES[tipo](lienzo, bloque)
    except ErrorDiagrama:
        raise
    except (TypeError, ValueError, AttributeError, KeyError, IndexError) as e:
        # Un dato de otro tipo (`curves: 5`) es un bloque inválido, no un motivo para frenar el examen.
        raise ErrorDiagrama(f"bloque {tipo} mal formado: {e}") from e
    ancho = max(ancho, lienzo.ancho_min)
    m = 8
    defs = (
        f'<defs><marker id="flecha-main-{sufijo}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" '
        f'markerHeight="6.5" orient="auto-start-reverse"><path d="M 0 1.5 L 9 5 L 0 8.5 z" '
        f'fill="{pal["accentPrimary"]}"/></marker>'
        f'<marker id="flecha-sub-{sufijo}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse"><path d="M 0 1.5 L 9 5 L 0 8.5 z" '
        f'fill="{pal["strokeSub"]}"/></marker></defs>'
    )
    w, h = math.ceil(ancho + 2 * m), math.ceil(alto + 2 * m)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="estructura" width="{w}" height="{h}" '
            f'viewBox="{-m} {-m} {w} {h}" role="img" aria-label="{_esc(bloque.get("title") or tipo)}">'
            f'{defs}<rect x="{-m}" y="{-m}" width="{w}" height="{h}" fill="#ffffff"/>'
            + "".join(lienzo.partes) + "</svg>")


def leer_bloques(texto: str) -> List[Dict[str, Any]]:
    """Los bloques de un texto YAML/JSON: un bloque, una lista de bloques o un documento de statics (`blocks`)."""
    try:
        dato = yaml.safe_load(texto)
    except yaml.YAMLError as e:
        raise ErrorDiagrama(f"el bloque no es YAML/JSON válido: {e}") from e
    if isinstance(dato, dict) and "blocks" in dato:
        dato = dato["blocks"]
    bloques = dato if isinstance(dato, list) else [dato]
    if not all(isinstance(b, dict) for b in bloques):
        raise ErrorDiagrama("cada bloque tiene que ser un diccionario con 'type'")
    return bloques


_FENCE = re.compile(r"^(?P<valla>`{3,}|~{3,})[ \t]*(?:estructura|statics)[ \t]*\n(?P<cuerpo>.*?)^(?P=valla)[ \t]*$",
                    re.S | re.M)


def expandir_en_markdown(texto: str, tinta: bool = True) -> Tuple[str, Dict[str, str]]:
    """Reemplaza los bloques ```estructura por marcadores; devuelve el texto y el SVG de cada marcador.

    Los marcadores (`ESTRUCTURA-<n>-<hash>`) sobreviven a la conversión de Markdown; después se
    cambian por el SVG con `reponer_svgs`. Un bloque inválido queda como un aviso en el texto.
    """
    svgs: Dict[str, str] = {}

    def reemplazar(m: re.Match) -> str:
        marcador = f"ESTRUCTURA{len(svgs)}X{hashlib.sha1(m.group(0).encode()).hexdigest()[:8]}"
        try:
            svgs[marcador] = "".join(f'<div class="estructura">{renderizar(b, tinta)}</div>'
                                     for b in leer_bloques(m.group("cuerpo")))
        except ErrorDiagrama as e:
            svgs[marcador] = f'<p class="estructura-error"><strong>Diagrama inválido:</strong> {_esc(e)}</p>'
        return f"\n\n{marcador}\n\n"

    return _FENCE.sub(reemplazar, texto), svgs


def reponer_svgs(html_texto: str, svgs: Dict[str, str]) -> str:
    """Cambia los marcadores de `expandir_en_markdown` (solos o dentro de un <p>) por su SVG."""
    for marcador, svg in svgs.items():
        html_texto = html_texto.replace(f"<p>{marcador}</p>", svg).replace(marcador, svg)
    return html_texto


# ---------------------------------------------------------------------------
# SVG versionados junto a los Markdown (hook `alucard diagramas-md`)
# ---------------------------------------------------------------------------
#
# Contrato con quien publica el Markdown sin alucarD (p. ej. `deckard export myst`): cada bloque
# ```estructura de `<dir>/<archivo>.md` se dibuja en `<dir>/diagramas/estructura-<hash>.svg`, con
# `<hash>` = los 12 primeros dígitos del SHA-1 del cuerpo del bloque sin espacios al principio ni al
# final (`nombre_svg`). Un bloque con varias estructuras queda en un único SVG, una debajo de la otra.

DIR_SVGS = "diagramas"


def nombre_svg(cuerpo: str) -> str:
    """Nombre del SVG de un bloque ```estructura: `estructura-<sha1(cuerpo.strip())[:12]>.svg`."""
    return f"estructura-{hashlib.sha1(cuerpo.strip().encode('utf-8')).hexdigest()[:12]}.svg"


def cuerpos_en_markdown(texto: str) -> List[str]:
    """El cuerpo (YAML/JSON) de cada bloque ```estructura (o ```statics) de un Markdown."""
    return [m.group("cuerpo") for m in _FENCE.finditer(texto)]


def _atributo_numerico(svg: str, nombre: str) -> str:
    """El `width` o el `height` del `<svg>`, que `renderizar` siempre escribe."""
    m = re.search(rf'{nombre}="(\d+)"', svg)
    if m is None:
        raise ErrorDiagrama(f"el SVG no tiene {nombre}")
    return m.group(1)


def renderizar_bloque_markdown(cuerpo: str, tinta: bool = True) -> str:
    """Todas las estructuras de un bloque ```estructura en un único `<svg>`, apiladas."""
    svgs = [renderizar(b, tinta) for b in leer_bloques(cuerpo)]
    if len(svgs) == 1:
        return svgs[0]
    ancho, y, partes = 0, 0, []
    for svg in svgs:
        w, h = (int(_atributo_numerico(svg, nombre)) for nombre in ("width", "height"))
        partes.append(svg.replace("<svg ", f'<svg x="0" y="{y}" ', 1))
        ancho, y = max(ancho, w), y + h + 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{y - 8}" '
            f'viewBox="0 0 {ancho} {y - 8}">' + "".join(partes) + "</svg>")


@dataclass
class Sincronizacion:
    escritos: List[str] = field(default_factory=list)
    borrados: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)


def sincronizar_svgs(directorio: "Path", tinta: bool = True, escribir: bool = True) -> Sincronizacion:
    """Deja `directorio/diagramas/` con exactamente un SVG al día por bloque de los `.md` del directorio.

    Escribe los que faltan o cambiaron y borra los `estructura-*.svg` que ningún bloque usa. Con
    `escribir=False` sólo informa qué cambiaría (para verificar en CI).
    """
    from pathlib import Path

    directorio = Path(directorio)
    destino = directorio / DIR_SVGS
    res = Sincronizacion()
    esperados: Dict[str, str] = {}
    for md in sorted(directorio.glob("*.md")):
        for cuerpo in cuerpos_en_markdown(md.read_text(encoding="utf-8")):
            nombre = nombre_svg(cuerpo)
            if nombre in esperados:
                continue
            try:
                esperados[nombre] = renderizar_bloque_markdown(cuerpo, tinta)
            except ErrorDiagrama as e:
                res.errores.append(f"{md}: {e}")
    for nombre, svg in sorted(esperados.items()):
        ruta = destino / nombre
        if not ruta.is_file() or ruta.read_text(encoding="utf-8") != svg:
            res.escritos.append(str(ruta))
            if escribir:
                destino.mkdir(parents=True, exist_ok=True)
                ruta.write_text(svg, encoding="utf-8")
    if destino.is_dir():
        for ruta in sorted(destino.glob("estructura-*.svg")):
            if ruta.name not in esperados:
                res.borrados.append(str(ruta))
                if escribir:
                    ruta.unlink()
        if escribir and not any(destino.iterdir()):
            destino.rmdir()
    return res


# Los diagramas de control de procesos (bloques, respuesta temporal, Bode, Nyquist, plano s, P&ID,
# escalera y GRAFCET) viven en su módulo y se suman acá.
from generador_examenes import diagramas_control as _control  # noqa: E402

_RENDERIZADORES.update(_control.RENDERIZADORES)
TIPOS = TIPOS + tuple(_control.RENDERIZADORES)

# Los de química universitaria (moléculas, reacciones, TRePEV, orbitales, perfiles de energía,
# titulaciones, cinética, fases, espectros, pilas y celdas unidad), en el suyo.
from generador_examenes import diagramas_quimica as _quimica  # noqa: E402

_RENDERIZADORES.update(_quimica.RENDERIZADORES)
TIPOS = TIPOS + tuple(_quimica.RENDERIZADORES)

# Orgánica (Newman, silla, Fischer) e inorgánica (campo cristalino, complejos, Latimer, Frost, Born-Haber).
from generador_examenes import diagramas_inorganica as _inorganica  # noqa: E402
from generador_examenes import diagramas_organica as _organica  # noqa: E402

for _modulo in (_organica, _inorganica):
    _RENDERIZADORES.update(_modulo.RENDERIZADORES)
    TIPOS = TIPOS + tuple(_modulo.RENDERIZADORES)
