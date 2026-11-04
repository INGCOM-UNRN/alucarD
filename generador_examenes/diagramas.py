"""Diagramas SVG de estructuras de datos, con el formato de bloques de statics.

Porta a Python los renderizadores de statics (`estructuras.html`: arreglo, lista enlazada simple,
doble y circular, pila, cola lineal y circular) y suma matrices (estáticas, con su disposición en
memoria, y dinámicas como arreglo de punteros a filas) y árboles (binario, ABB, AVL con factor de
balance y montículo), para usarlos en preguntas y consignas sin navegador.

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

TIPOS = ("array", "matrix", "linked_list", "stack", "call_stack", "queue", "tree")


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

    def punto(self, x: float, y: float, color: str = "accentPrimary", radio: float = 3.2) -> None:
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio}" fill="{self.pal[color]}"/>')

    def null(self, x: float, y: float) -> None:
        """El símbolo de tierra de NULL que usa statics."""
        self.linea(x, y - 10, x, y + 10, color="strokeMain", ancho=2, flecha=None)
        self.linea(x + 5, y - 6, x + 5, y + 6, color="strokeMain", ancho=1.5, flecha=None)
        self.t(x + 12, y + 4, "NULL", size=10, peso=700, color="textMuted")


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

def _arreglo(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    valores = _valores(b)
    cap = _entero(b.get("capacity", len(valores) or 8), 8, 1, 16)
    base, paso = _hex(b.get("baseAddr")), _entero(b.get("typeSize"), 4, 1, 64)
    direcciones, offsets = bool(b.get("showAddresses")), bool(b.get("showOffsets"))
    indices = b.get("showIndices", True)
    top = _encabezado(c, b, f"Base: {_fmt_hex(base)} | sizeof: {paso}B" if direcciones else "")

    punteros: Dict[int, List[str]] = {}
    for par in str(b.get("pointers") or "").split(","):
        etiqueta, _, idx = par.partition(":")
        if idx.strip().isdigit() and int(idx) < cap:
            punteros.setdefault(int(idx), []).append(etiqueta.strip())

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
    if variante != "static":
        raise ErrorDiagrama(f"variante de matriz no soportada: {variante!r} (static, dynamic o jagged)")
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
    extra = f"{tipo} **{nombre}"
    if con_largos:
        extra += f" | size_t {nombre_largos}[{nf}]"
    if centinela is not None:
        extra += f" | centinela: {centinela}"
    top = _encabezado(c, b, extra)

    def dir_fila(i: int) -> str:
        if sin_dirs:
            return "0x____"
        return _fmt_hex(_hex(dirs_filas[i])) if i < len(dirs_filas) else _fmt_hex(base_filas + i * 0x40)

    largos = [0 if f is None else nc_fijo if nc_fijo else len(f)
              for f in filas[:nf]]
    celda_w, celda_h, paso_y = 56, 40, 54
    # Las cajas crecen con el nombre (`palabras[0]` no entra en una de 52).
    ptr_w = max(72 if direcciones else 52, math.ceil(len(f"{nombre}[{nf - 1}]") * 6.2 + 14))
    m_w = max(56, math.ceil(len(str(nombre)) * 8.5 + 14))
    largos_w = max(64, math.ceil(len(str(nombre_largos)) * 8.5 + 14)) if con_largos else 0
    x_m = largos_w + (36 if con_largos else 0)
    x_ptr = x_m + m_w + 56
    x_filas = x_ptr + ptr_w + 70
    y0 = top + (44 if indices and any(largos) else 30)

    if con_largos:
        # El arreglo de largos, fila por fila, a la izquierda: `largos[i]` celdas tiene la fila i.
        declarados = list(b.get("lengths") or [])
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
    c.t(x_m + m_w / 2, y0 - 8, nombre, size=12, peso=700, ancla="middle")
    c.r(x_m, y0, m_w, celda_h, relleno="fillPointerBox", trazo=1.75, rx=3)
    if direcciones:
        c.t(x_m + m_w / 2, y0 + celda_h / 2 + 4, "0x____" if sin_dirs else _fmt_hex(base), size=9,
            ancla="middle")
        c.linea(x_m + m_w, y0 + celda_h / 2, x_ptr - 3, y0 + celda_h / 2, ancho=1.6)
    else:
        c.punto(x_m + m_w / 2, y0 + celda_h / 2)
        c.linea(x_m + m_w / 2, y0 + celda_h / 2, x_ptr - 3, y0 + celda_h / 2, ancho=1.6)
    if direcciones:
        c.t(x_ptr + ptr_w / 2, y0 - 8, "0x____" if sin_dirs else _fmt_hex(base), size=9, color="textSub",
            ancla="middle")

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
        if filas[i] is None:  # fila NULL: la barra cruzada de statics
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
            v = filas[i][j] if j < len(filas[i]) else ""
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
    return ancho, y0 + (nf - 1) * paso_y + celda_h + 10


# ---------------------------------------------------------------------------
# Lista enlazada: simple, doble y circular
# ---------------------------------------------------------------------------

def _lista(c: _Lienzo, b: Dict[str, Any]) -> Tuple[float, float]:
    valores = _valores(b) or [""]
    n = min(7, len(valores))
    variante = b.get("variant", "singly")
    doble, circular = variante in ("doubly", "circular_doubly"), variante in ("circular", "circular_doubly")
    sin_dirs, sin_flechas = bool(b.get("blankNextAddrs")), b.get("drawArrows") is False
    sin_valores = bool(b.get("blankValues"))
    top = _encabezado(c, b)

    direcciones = [_fmt_hex(d) if isinstance(d, int) else str(d) for d in b.get("addresses") or []]
    direcciones += [_fmt_hex(0x4000 + i * 0x180) for i in range(len(direcciones), n)]
    y, alto_nodo, cabeza_w, x0 = top + 28, 54, 72, 104
    nodo_w = 126 if doble else 102
    gap = 44

    c.t(cabeza_w / 2, y, b.get("headLabel") or "HEAD", size=10, peso=700, ancla="middle")
    c.r(0, y + 7, cabeza_w, 40, relleno="fillPointerBox", trazo=1.75, rx=3)
    if not sin_dirs:
        c.t(cabeza_w / 2, y + 31, direcciones[0], size=10, peso=600, color="textSub", ancla="middle")
    if not sin_flechas:
        c.linea(cabeza_w, y + 27, x0 - 3, y + 27, ancho=1.75)

    for i in range(n):
        nx = x0 + i * (nodo_w + gap)
        valor = valores[i]
        siguiente = direcciones[i + 1] if i < n - 1 else (direcciones[0] if circular else "NULL")
        anterior = direcciones[i - 1] if i > 0 else (direcciones[n - 1] if circular else "NULL")
        c.t(nx + nodo_w / 2, y - 7, f"Dir: {direcciones[i]}", size=10, peso=700, color="textSub", ancla="middle")

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
    return ancho, y + alto_nodo + (50 if circular else 24)


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


_RENDERIZADORES: Dict[str, Callable[[_Lienzo, Dict[str, Any]], Tuple[float, float]]] = {
    "array": _arreglo, "matrix": _matriz, "linked_list": _lista, "stack": _pila, "call_stack": _pila_llamadas, "queue": _cola, "tree": _arbol,
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
    sufijo = hashlib.sha1(json.dumps(bloque, sort_keys=True, default=str).encode()).hexdigest()[:8]
    lienzo = _Lienzo(pal, sufijo)
    ancho, alto = _RENDERIZADORES[tipo](lienzo, bloque)
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


def renderizar_bloque_markdown(cuerpo: str, tinta: bool = True) -> str:
    """Todas las estructuras de un bloque ```estructura en un único `<svg>`, apiladas."""
    svgs = [renderizar(b, tinta) for b in leer_bloques(cuerpo)]
    if len(svgs) == 1:
        return svgs[0]
    ancho, y, partes = 0, 0, []
    for svg in svgs:
        w = int(re.search(r'width="(\d+)"', svg).group(1))
        h = int(re.search(r'height="(\d+)"', svg).group(1))
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
