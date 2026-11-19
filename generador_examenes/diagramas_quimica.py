"""Diagramas de química universitaria para los bloques ```` ```estructura ````.

| `type` | Qué dibuja |
| --- | --- |
| `molecule` | Fórmula estructural: de Lewis (pares libres, radicales, cargas formales) o esqueletal; anillos aromáticos, cuñas y rayas, y flechas curvas de mecanismo. |
| `reaction` | Una ecuación química o un mecanismo: fórmulas y moléculas con flechas de reacción, equilibrio o resonancia, y condiciones arriba y abajo. |
| `vsepr` | Geometría molecular (TRePEV): el átomo central, sus ligandos en perspectiva, los pares libres, el ángulo, la notación AXE y la hibridación. |
| `orbitals` | Diagrama de casilleros de una configuración electrónica, o de orbitales moleculares de una diatómica (orden de enlace y magnetismo). |
| `energy_profile` | Perfil de energía de una reacción: estados de transición, intermedios, Ea, ΔH y el camino catalizado. |
| `titration` | Curva de titulación ácido-base calculada: puntos de equivalencia, semiequivalencia e indicador. |
| `speciation` | Fracciones de las especies de un ácido poliprótico en función del pH. |
| `kinetics` | Concentración en función del tiempo (orden 0, 1 y 2, consecutivas, reversibles), sus linealizaciones y el gráfico de Arrhenius. |
| `phase_diagram` | Diagrama de fases de una sustancia (puntos triple y crítico, 1 atm) o de una mezcla binaria con eutéctico. |
| `heating_curve` | Curva de calentamiento: temperatura en función del calor, con el calor de cada tramo. |
| `spectrum` | Espectros IR, RMN de ¹H (multipletes n + 1) y de ¹³C, UV-visible y de masas. |
| `galvanic_cell` | Pila: electrodos, puente salino, flujo de electrones e iones, semirreacciones, notación y E (con Nernst). |
| `unit_cell` | Celda unidad cúbica (simple, centrada en el cuerpo y en las caras, NaCl, CsCl): Z, coordinación, empaquetamiento y densidad. |

Las cuentas están en `generador_examenes.quimica`. Las fórmulas se escriben en texto: los números
después de un símbolo quedan como subíndice (`H2SO4`) y lo que sigue a `^` como superíndice
(`SO4^2-`, `Fe^3+`). Cada tipo acepta claves `blank*` para dejar casilleros en blanco.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from generador_examenes import diagramas as d
from generador_examenes import quimica as q
from generador_examenes.diagramas_control import _GUIONES, _Ejes, _g, _leyenda

Punto = tuple[float, float]


def _errores(funcion: Callable) -> Callable:
    def envuelta(c, b):
        try:
            return funcion(c, b)
        except q.ErrorQuimica as e:
            raise d.ErrorDiagrama(f"{b.get('type')}: {e}") from e
    return envuelta


# --- Fórmulas: subíndices y superíndices -------------------------------------------------------------------

_CARGA = set("0123456789+-−*•·‡")


def partes_formula(texto: Any) -> list[tuple[str, str]]:
    """`SO4^2-` → [("SO", "n"), ("4", "sub"), ("2−", "sup")]. `_` fuerza un subíndice (`K_a`, `_{2p}`)."""
    texto = str(texto)
    partes: list[tuple[str, str]] = []

    def poner(ch: str, modo: str) -> None:
        if partes and partes[-1][1] == modo:
            partes[-1] = (partes[-1][0] + ch, modo)
        else:
            partes.append((ch, modo))

    i, previo = 0, ""
    while i < len(texto):
        ch = texto[i]
        if ch in "^_":
            modo = "sup" if ch == "^" else "sub"
            i += 1
            if i < len(texto) and texto[i] == "{":
                fin = texto.find("}", i)
                fin = len(texto) if fin < 0 else fin
                for x in texto[i + 1:fin]:
                    poner(x.replace("-", "−"), modo)
                i = fin + 1
            else:
                valido = _CARGA if modo == "sup" else set("0123456789abcdefghijklmnopqrstuvwxyzαβγ")
                while i < len(texto) and texto[i] in valido:
                    poner(texto[i].replace("-", "−"), modo)
                    i += 1
            previo = "x"
            continue
        if ch in "0123456789" and (previo.isalpha() or previo in ")]") and previo not in ("", " "):
            poner(ch, "sub")
            previo = previo if previo.isalpha() or previo in ")]" else previo
            i += 1
            # dígitos seguidos: siguen en subíndice
            while i < len(texto) and texto[i] in "0123456789":
                poner(texto[i], "sub")
                i += 1
            previo = "0"
            continue
        poner(ch, "n")
        previo = ch
        i += 1
    return partes


def ancho_formula(texto: Any, size: float = 11) -> float:
    return sum(len(t) * size * (0.66 if m == "n" else 0.48) for t, m in partes_formula(texto))


def _tq(c: d._Lienzo, x: float, y: float, texto: Any, size: float = 11, peso: int = 400, color: str = "textMain",
        ancla: str = "start", fuente: str = d.SANS, fondo: bool = False) -> float:
    """Un texto con fórmula química (subíndices y superíndices con tspan y dy); devuelve el ancho.

    Con `fondo`, un rectángulo blanco detrás, para que se lea sobre una curva o una guía."""
    ancho = ancho_formula(texto, size)
    if fondo:
        x0 = x if ancla == "start" else (x - ancho / 2 if ancla == "middle" else x - ancho)
        c.add(f'<rect x="{x0 - 2:.1f}" y="{y - size:.1f}" width="{ancho + 4:.1f}" height="{size * 1.45:.1f}" '
              f'fill="{c.pal["fillCell"]}" opacity="0.88"/>')
    piezas, desplazado, pendiente = [], 0.0, 0
    for t, modo in partes_formula(texto):
        # Los visores recortan los espacios al borde de cada tspan: se cambian por un corrimiento dx.
        pendiente += len(t) - len(t.lstrip(" "))
        finales = len(t.lstrip(" ")) - len(t.strip(" "))
        t = t.strip(" ")
        if not t:
            continue
        objetivo = {"n": 0.0, "sub": size * 0.3, "sup": -size * 0.4}[modo]
        dy = objetivo - desplazado
        desplazado = objetivo
        tamano = size if modo == "n" else size * 0.72
        dx = f' dx="{pendiente * size * 0.32:.1f}"' if pendiente else ""
        pendiente = finales
        piezas.append(f'<tspan{dx} dy="{dy:.1f}" font-size="{tamano:.1f}">{d._esc(t.replace(" ", chr(160)))}</tspan>')
    c.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancla}" font-family="{fuente}" font-size="{size}" '
          f'font-weight="{peso}" fill="{c.pal[color]}">{"".join(piezas)}</text>')
    return ancho


def _caja_vacia(c: d._Lienzo, x: float, y: float, w: float = 28, h: float = 16) -> None:
    """Un casillero punteado para completar, centrado en (x, y)."""
    c.add(f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="none" '
          f'stroke="{c.pal["strokeMuted"]}" stroke-width="1" stroke-dasharray="3 2"/>')


def _flecha_doble(c: d._Lienzo, x: float, y1: float, y2: float, color: str = "strokeSub") -> None:
    c.add(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{c.pal[color]}" stroke-width="1.2" '
          f'marker-start="url(#flecha-sub-{c.sufijo})" marker-end="url(#flecha-sub-{c.sufijo})"/>')


def _incrustar(c: d._Lienzo, sub: d._Lienzo, x: float, y: float) -> None:
    c.add(f'<g transform="translate({x:.1f} {y:.1f})">', *sub.partes, "</g>")


def _rotulo_q(c: d._Lienzo, x: float, y: float, nombre: str, valor: str | None, blanco: bool, ancla: str = "start",
              size: float = 10) -> float:
    """`nombre = valor` (o `nombre = ____` para completar), en sans y con fórmulas; devuelve el ancho."""
    if blanco:
        texto = f"{nombre} ="
        ancho = ancho_formula(texto, size) + 50
        x0 = x if ancla == "start" else (x - ancho / 2 if ancla == "middle" else x - ancho)
        _tq(c, x0, y, texto, size=size, peso=700, fondo=True)
        c.vacio(x0 + ancho_formula(texto, size) + 4, x0 + ancho, y + 2)
        return ancho
    texto = f"{nombre} = {valor}"
    return _tq(c, x, y, texto, size=size, peso=700, ancla=ancla, fondo=True)


def _coma(x: float, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def _leyenda_q(c: d._Lienzo, x: float, y: float, etiquetas: list[str]) -> float:
    """La leyenda de las curvas, sobre un fondo blanco."""
    ancho = 40 + max(ancho_formula(e, 10) for e in etiquetas)
    c.add(f'<rect x="{x - 4:.1f}" y="{y - 9:.1f}" width="{ancho:.1f}" height="{len(etiquetas) * 16 + 4:.1f}" '
          f'fill="{c.pal["fillCell"]}" opacity="0.9"/>')
    return _leyenda(c, x, y, etiquetas)


# --- Molécula ------------------------------------------------------------------------------------------

class _Atomo:
    def __init__(self, id_: str, x: float, y: float):
        self.id, self.x, self.y = id_, x, y
        self.el = "C"
        self.carga: Any = None
        self.pares = 0
        self.radicales = 0
        self.blanco = False
        self.mostrar = False
        self.nota = ""
        self.vecinos: list[_Atomo] = []


def _carga_texto(carga: Any) -> str:
    if carga is None or carga == "" or carga == 0:
        return ""
    if isinstance(carga, bool):
        return ""
    if isinstance(carga, (int, float)):
        n = int(carga)
        signo = "+" if n > 0 else "−"
        return signo if abs(n) == 1 else f"{abs(n)}{signo}"
    return str(carga).replace("-", "−")


class _Molecula:
    """Los átomos (en unidades de longitud de enlace, y hacia arriba) y los enlaces de un bloque."""

    def __init__(self, b: dict, donde: str = "molecule"):
        self.donde = donde
        self.atomos: dict[str, _Atomo] = {}
        self.alias: dict[str, str] = {}
        self.enlaces: list[dict] = []
        self.anillos: list[tuple[list[str], float, float, int, bool]] = []
        for i, anillo in enumerate(b.get("rings") or []):
            self._anillo(anillo, i)
        for i, dato in enumerate(b.get("atoms") or []):
            self._atomo(dato, i)
        for i, dato in enumerate(b.get("bonds") or []):
            self._enlace(dato, i)
        if not self.atomos:
            raise d.ErrorDiagrama(f"{donde}: faltan atoms (o rings)")
        for e in self.enlaces:
            a, z = self.atomos[e["a"]], self.atomos[e["b"]]
            a.vecinos.append(z)
            z.vecinos.append(a)

    def atomo(self, id_: Any) -> _Atomo:
        clave = self.alias.get(str(id_), str(id_))
        if clave not in self.atomos:
            raise d.ErrorDiagrama(f"{self.donde}: no hay un átomo {id_!r}")
        return self.atomos[clave]

    def _nuevo(self, id_: str, x: float, y: float) -> _Atomo:
        for a in self.atomos.values():       # dos anillos fusionados comparten átomos
            if math.dist((a.x, a.y), (x, y)) < 0.05:
                self.alias[id_] = a.id
                return a
        a = _Atomo(id_, x, y)
        self.atomos[id_] = a
        return a

    def _anillo(self, dato: dict, i: int) -> None:
        if not isinstance(dato, dict):
            raise d.ErrorDiagrama(f"{self.donde}.rings[{i}]: {{size, center, ids}}")
        n = int(dato.get("size", 6))
        if not 3 <= n <= 8:
            raise d.ErrorDiagrama(f"{self.donde}.rings[{i}].size: de 3 a 8 átomos")
        cx, cy = (float(v) for v in dato.get("center", [0, 0]))
        inicio = float(dato.get("start", 90))
        ids = [str(x) for x in dato.get("ids") or [f"r{i}_{k}" for k in range(n)]]
        if len(ids) != n:
            raise d.ErrorDiagrama(f"{self.donde}.rings[{i}].ids: tienen que ser {n}")
        radio = 1 / (2 * math.sin(math.pi / n))
        elementos = dato.get("el")
        reales = []
        for k, id_ in enumerate(ids):
            ang = math.radians(inicio + 360 * k / n)
            a = self._nuevo(id_, cx + radio * math.cos(ang), cy + radio * math.sin(ang))
            if isinstance(elementos, list) and k < len(elementos) and elementos[k]:
                a.el = str(elementos[k])
            reales.append(a.id)
        kekule = bool(dato.get("kekule"))
        for k in range(n):
            self._enlace({"from": reales[k], "to": reales[(k + 1) % n], "order": 2 if kekule and k % 2 == 0 else 1},
                         f"rings[{i}]")
        self.anillos.append((reales, cx, cy, n, bool(dato.get("aromatic"))))

    def _atomo(self, dato: Any, i: int) -> None:
        if isinstance(dato, str):
            dato = {"el": dato}
        if not isinstance(dato, dict):
            raise d.ErrorDiagrama(f"{self.donde}.atoms[{i}]: {{id, el, at: [x, y]}} o {{id, el, from, angle}}")
        id_ = str(dato.get("id", f"a{i}"))
        existente = self.alias.get(id_, id_) in self.atomos and "at" not in dato and "from" not in dato
        if existente:
            a = self.atomo(id_)
        elif "at" in dato:
            x, y = (float(v) for v in dato["at"])
            a = self._nuevo(id_, x, y)
        elif "from" in dato:
            base = self.atomo(dato["from"])
            ang = math.radians(float(dato.get("angle", 0)))
            largo = float(dato.get("length", 1))
            a = self._nuevo(id_, base.x + largo * math.cos(ang), base.y + largo * math.sin(ang))
            if "bond" not in dato or dato["bond"]:
                orden = dato.get("bond", 1)
                enlace = orden if isinstance(orden, dict) else {"order": orden}
                self._enlace({"from": base.id, "to": a.id, **enlace}, f"atoms[{i}]")
        elif not self.atomos:
            a = self._nuevo(id_, 0, 0)
        else:
            raise d.ErrorDiagrama(f"{self.donde}.atoms[{i}]: falta at: [x, y] o from: <id> (con angle)")
        a.el = str(dato.get("el", dato.get("label", a.el)))
        if "charge" in dato:
            a.carga = dato["charge"]
        a.pares = int(dato.get("lonePairs", a.pares))
        a.radicales = int(dato.get("radical", a.radicales))
        a.blanco = bool(dato.get("blank", a.blanco))
        a.mostrar = bool(dato.get("show", a.mostrar))
        a.nota = str(dato.get("note", a.nota) or "")

    def _enlace(self, dato: Any, donde: Any) -> None:
        if isinstance(dato, (list, tuple)):
            if len(dato) < 2:
                raise d.ErrorDiagrama(f"{self.donde}.bonds[{donde}]: [a, b] o [a, b, orden]")
            dato = {"from": dato[0], "to": dato[1], "order": dato[2] if len(dato) > 2 else 1}
        if not isinstance(dato, dict):
            raise d.ErrorDiagrama(f"{self.donde}.bonds[{donde}]: [a, b, orden] o {{from, to, order, stereo}}")
        a = self.atomo(dato.get("from", dato.get("a"))).id
        z = self.atomo(dato.get("to", dato.get("b"))).id
        orden = float(dato.get("order", 1))
        if orden not in (0.5, 1, 1.5, 2, 3):
            raise d.ErrorDiagrama(f"{self.donde}.bonds[{donde}].order: 1, 2, 3, 1.5 (resonancia) o 0.5 (parcial)")
        estereo = dato.get("stereo")
        if estereo not in (None, "wedge", "hash"):
            raise d.ErrorDiagrama(f"{self.donde}.bonds[{donde}].stereo: wedge (cuña) o hash (rayas)")
        nuevo = {"a": a, "b": z, "order": orden, "stereo": estereo, "dashed": bool(dato.get("dashed")),
                 "blank": bool(dato.get("blank"))}
        for i, e in enumerate(self.enlaces):
            if {e["a"], e["b"]} == {a, z}:
                self.enlaces[i] = nuevo
                return
        self.enlaces.append(nuevo)


def _visible(a: _Atomo, esqueletal: bool) -> bool:
    return (not esqueletal or a.el != "C" or a.mostrar or a.blanco or bool(_carga_texto(a.carga)) or a.pares > 0
            or a.radicales > 0 or not a.vecinos)


def _semiejes(a: _Atomo, esqueletal: bool, size: float) -> tuple[float, float]:
    if not _visible(a, esqueletal):
        return 0.0, 0.0
    if a.blanco:
        return 9.0, 9.0
    return ancho_formula(a.el, size) / 2 + 1.5, size * 0.62


def _salida(hw: float, hh: float, ux: float, uy: float) -> float:
    """Cuánto hay desde el centro de un rótulo hasta su borde, en la dirección (ux, uy)."""
    if hw == 0:
        return 0.0
    tx = hw / abs(ux) if abs(ux) > 1e-9 else math.inf
    ty = hh / abs(uy) if abs(uy) > 1e-9 else math.inf
    return min(tx, ty) + 2


def _dibujar_molecula(c: d._Lienzo, b: dict, donde: str = "molecule") -> tuple[float, float]:
    """Dibuja en coordenadas propias y devuelve (ancho, alto) después de correr todo a (0, 0)."""
    m = _Molecula(b, donde)
    largo = float(b.get("bondLength", 34))
    esqueletal = bool(b.get("skeletal", False))
    size = float(b.get("fontSize", 12))
    pos = {k: (a.x * largo, -a.y * largo) for k, a in m.atomos.items()}
    sub = d._Lienzo(c.pal, c.sufijo)
    trazo = c.pal["strokeMain"]
    centros_anillo = {}
    for ids, cx, cy, _n, _ar in m.anillos:
        for i in range(len(ids)):
            centros_anillo[frozenset((ids[i], ids[(i + 1) % len(ids)]))] = (cx * largo, -cy * largo)
    puntos_extra: list[Punto] = []

    for e in m.enlaces:
        a, z = m.atomos[e["a"]], m.atomos[e["b"]]
        (x1, y1), (x2, y2) = pos[a.id], pos[z.id]
        dist = math.dist((x1, y1), (x2, y2)) or 1
        ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
        s1 = _salida(*_semiejes(a, esqueletal, size), ux, uy)
        s2 = _salida(*_semiejes(z, esqueletal, size), ux, uy)
        ax, ay = x1 + ux * s1, y1 + uy * s1
        bx, by = x2 - ux * s2, y2 - uy * s2
        px, py = -uy, ux                         # perpendicular
        guiones = ' stroke-dasharray="4 3"' if e["dashed"] or e["order"] == 0.5 else ""
        if e["blank"]:
            sub.add(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{c.pal["strokeMuted"]}" '
                    'stroke-width="1" stroke-dasharray="2 3"/>')
            continue
        if e["stereo"] == "wedge":
            sub.add(f'<polygon points="{ax:.1f},{ay:.1f} {bx + px * 3.6:.1f},{by + py * 3.6:.1f} '
                    f'{bx - px * 3.6:.1f},{by - py * 3.6:.1f}" fill="{trazo}" stroke="{trazo}" stroke-width="0.6"/>')
            continue
        if e["stereo"] == "hash":
            for k in range(1, 8):
                t = k / 7
                hx, hy = ax + (bx - ax) * t, ay + (by - ay) * t
                ancho = 0.6 + 3.2 * t
                sub.add(f'<line x1="{hx + px * ancho:.1f}" y1="{hy + py * ancho:.1f}" x2="{hx - px * ancho:.1f}" '
                        f'y2="{hy - py * ancho:.1f}" stroke="{trazo}" stroke-width="1.1"/>')
            continue

        def linea(x1_: float, y1_: float, x2_: float, y2_: float, extra: str = "") -> None:
            sub.add(f'<line x1="{x1_:.1f}" y1="{y1_:.1f}" x2="{x2_:.1f}" y2="{y2_:.1f}" stroke="{trazo}" '
                    f'stroke-width="1.5" stroke-linecap="round"{extra}/>')

        orden = e["order"]
        centro = centros_anillo.get(frozenset((a.id, z.id)))
        if orden in (2, 1.5) and centro is not None:
            linea(ax, ay, bx, by)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            hacia = 1 if (centro[0] - mx) * px + (centro[1] - my) * py > 0 else -1
            o, recorte = 5.0 * hacia, 0.16
            linea(ax + (bx - ax) * recorte + px * o, ay + (by - ay) * recorte + py * o,
                  bx - (bx - ax) * recorte + px * o, by - (by - ay) * recorte + py * o,
                  ' stroke-dasharray="3 2.5"' if orden == 1.5 else "")
        elif orden in (2, 1.5):
            linea(ax + px * 2.6, ay + py * 2.6, bx + px * 2.6, by + py * 2.6)
            linea(ax - px * 2.6, ay - py * 2.6, bx - px * 2.6, by - py * 2.6,
                  ' stroke-dasharray="3 2.5"' if orden == 1.5 else "")
        elif orden == 3:
            for o in (-4.0, 0.0, 4.0):
                linea(ax + px * o, ay + py * o, bx + px * o, by + py * o)
        else:
            linea(ax, ay, bx, by, guiones)

    for ids, cx, cy, n, aromatico in m.anillos:
        if aromatico:
            interior = largo / (2 * math.tan(math.pi / n))
            sub.add(f'<circle cx="{cx * largo:.1f}" cy="{-cy * largo:.1f}" r="{interior * 0.6:.1f}" fill="none" '
                    f'stroke="{trazo}" stroke-width="1.4"/>')

    for a in m.atomos.values():
        x, y = pos[a.id]
        if not _visible(a, esqueletal):
            continue
        hw, hh = _semiejes(a, esqueletal, size)
        if a.blanco:
            _caja_vacia(sub, x, y, 18, 18)
        else:
            _tq(sub, x, y + size * 0.36, a.el, size=size, peso=500, ancla="middle")
        carga = _carga_texto(a.carga)
        if carga:
            sub.t(x + hw + 1.5, y - hh + 1, carga, size=size * 0.8, peso=700, fuente=d.SANS)
            puntos_extra.append((x + hw + 10, y - hh - 6))
        if a.nota:
            sub.t(x, y - hh - 5, a.nota, size=size * 0.7, color="textSub", ancla="middle", fuente=d.SANS)
            puntos_extra.append((x, y - hh - 14))
        # Pares libres y radicales: en las direcciones más alejadas de los enlaces.
        enlaces = [math.atan2(pos[v.id][1] - y, pos[v.id][0] - x) for v in a.vecinos]
        if carga:
            enlaces.append(math.atan2(-hh, hw))
        elegidas: list[float] = []
        for _ in range(a.pares + a.radicales):
            mejor, puntaje = 0.0, -1.0
            for k in range(24):
                ang = math.radians(k * 15)
                ocupadas = enlaces + elegidas
                lejos = min((abs(math.atan2(math.sin(ang - o), math.cos(ang - o))) for o in ocupadas), default=math.pi)
                valor = lejos + (0.05 if k % 6 == 0 else 0)
                if valor > puntaje + 1e-9:
                    mejor, puntaje = ang, valor
            elegidas.append(mejor)
        for i, ang in enumerate(elegidas):
            ux, uy = math.cos(ang), math.sin(ang)
            r = _salida(max(hw, 5), max(hh, 5), ux, uy) + 4
            cx_, cy_ = x + ux * r, y + uy * r
            puntos_extra.append((cx_ + ux * 4, cy_ + uy * 4))
            if i < a.pares:
                for s in (-2.8, 2.8):
                    sub.punto(cx_ - uy * s, cy_ + ux * s, color="strokeMain", radio=1.4)
            else:
                sub.punto(cx_, cy_, color="strokeMain", radio=1.6)

    for i, flecha in enumerate(b.get("arrows") or []):
        if not isinstance(flecha, dict) or "from" not in flecha or "to" not in flecha:
            raise d.ErrorDiagrama(f"{donde}.arrows[{i}]: {{from: átomo o [a, b], to: átomo o [a, b]}}")

        def lugar(ref: Any) -> Punto:
            if isinstance(ref, (list, tuple)):
                p1, p2 = pos[m.atomo(ref[0]).id], pos[m.atomo(ref[1]).id]
                return (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            return pos[m.atomo(ref).id]

        (sx, sy), (ex, ey) = lugar(flecha["from"]), lugar(flecha["to"])
        dist = math.dist((sx, sy), (ex, ey)) or 1
        nx, ny = -(ey - sy) / dist, (ex - sx) / dist
        curva = float(flecha.get("bend", 1))
        sx, sy = sx + nx * 9 * curva, sy + ny * 9 * curva
        ex, ey = ex + nx * 9 * curva, ey + ny * 9 * curva
        kx, ky = (sx + ex) / 2 + nx * dist * 0.45 * curva, (sy + ey) / 2 + ny * dist * 0.45 * curva
        puntos_extra.append((kx, ky))
        acento = c.pal["accentPrimary"]
        if flecha.get("half"):
            sub.add(f'<path d="M {sx:.1f} {sy:.1f} Q {kx:.1f} {ky:.1f} {ex:.1f} {ey:.1f}" fill="none" '
                    f'stroke="{acento}" stroke-width="1.3"/>')
            tx, ty = ex - kx, ey - ky
            nt = math.hypot(tx, ty) or 1
            tx, ty = tx / nt, ty / nt
            ang = math.radians(28)
            hx = ex - 8 * (tx * math.cos(ang) - ty * math.sin(ang))
            hy = ey - 8 * (tx * math.sin(ang) + ty * math.cos(ang))
            sub.add(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{acento}" '
                    'stroke-width="1.3"/>')
        else:
            sub.add(f'<path d="M {sx:.1f} {sy:.1f} Q {kx:.1f} {ky:.1f} {ex:.1f} {ey:.1f}" fill="none" '
                    f'stroke="{acento}" stroke-width="1.3" marker-end="url(#flecha-main-{c.sufijo})"/>')

    xs = [p[0] for p in pos.values()] + [p[0] for p in puntos_extra]
    ys = [p[1] for p in pos.values()] + [p[1] for p in puntos_extra]
    margen = 14
    x0, y0 = min(xs) - margen, min(ys) - margen
    _incrustar(c, sub, -x0, -y0)
    return max(xs) - x0 + margen, max(ys) - y0 + margen


@_errores
def _molecula(c: d._Lienzo, b: dict) -> Punto:
    top = d._encabezado(c, b)
    sub = d._Lienzo(c.pal, c.sufijo)
    w, h = _dibujar_molecula(sub, b)
    _incrustar(c, sub, 0, top)
    alto = top + h
    if b.get("caption"):
        alto += 4
        _tq(c, w / 2, alto + 12, b["caption"], size=11, ancla="middle")
        alto += 18
    return w, alto


# --- Reacción --------------------------------------------------------------------------------------------

_FLECHAS = {"->": "forward", "→": "forward", "<=>": "equilibrium", "eq": "equilibrium", "⇌": "equilibrium",
            "<->": "resonance", "↔": "resonance", "=>": "retro"}


def _pieza_reaccion(c: d._Lienzo, dato: Any, i: int) -> tuple[d._Lienzo, float, float]:
    sub = d._Lienzo(c.pal, c.sufijo)
    if isinstance(dato, (int, float)) and not isinstance(dato, bool):
        dato = str(dato)
    if isinstance(dato, str):
        if dato.strip() == "+":
            sub.t(9, 5, "+", size=16, peso=600, ancla="middle", fuente=d.SANS)
            return sub, 18, 0
        w = _tq(sub, 0, 5, dato, size=13)
        return sub, w, 0
    if not isinstance(dato, dict):
        raise d.ErrorDiagrama(f"reaction.steps[{i}]: una fórmula, '+', {{arrow: ...}} o una molécula")
    if "arrow" in dato:
        tipo = _FLECHAS.get(str(dato["arrow"]))
        if tipo is None:
            raise d.ErrorDiagrama(f"reaction.steps[{i}].arrow: {dato['arrow']!r} (vale ->, <=>, <->, =>)")
        arriba, abajo = dato.get("above"), dato.get("below")
        largo = max(64.0, ancho_formula(arriba or "", 10) + 16, ancho_formula(abajo or "", 10) + 16)
        trazo, acento = c.pal["strokeMain"], c.pal["accentPrimary"]
        if tipo == "forward":
            sub.add(f'<line x1="4" y1="0" x2="{largo - 4:.1f}" y2="0" stroke="{acento}" stroke-width="1.6" '
                    f'marker-end="url(#flecha-main-{c.sufijo})"/>')
        elif tipo == "resonance":
            sub.add(f'<line x1="6" y1="0" x2="{largo - 6:.1f}" y2="0" stroke="{acento}" stroke-width="1.6" '
                    f'marker-start="url(#flecha-main-{c.sufijo})" marker-end="url(#flecha-main-{c.sufijo})"/>')
        elif tipo == "retro":
            for o in (-2.5, 2.5):
                sub.add(f'<line x1="4" y1="{o}" x2="{largo - 10:.1f}" y2="{o}" stroke="{trazo}" stroke-width="1.3"/>')
            sub.add(f'<path d="M {largo - 14:.1f} -7 L {largo - 4:.1f} 0 L {largo - 14:.1f} 7" fill="none" '
                    f'stroke="{trazo}" stroke-width="1.3"/>')
        else:
            sub.add(f'<path d="M 4 -3 L {largo - 4:.1f} -3 L {largo - 11:.1f} -8" fill="none" stroke="{acento}" '
                    'stroke-width="1.5"/>')
            sub.add(f'<path d="M {largo - 4:.1f} 3 L 4 3 L 11 8" fill="none" stroke="{acento}" stroke-width="1.5"/>')
        if dato.get("blank"):
            _caja_vacia(sub, largo / 2, -16, 46, 14)
        elif arriba:
            _tq(sub, largo / 2, -9, arriba, size=10, color="textSub", ancla="middle")
        if abajo:
            _tq(sub, largo / 2, 18, abajo, size=10, color="textSub", ancla="middle")
        return sub, largo, 0
    if dato.get("blank") and not dato.get("atoms") and not dato.get("rings"):
        ancho = float(dato.get("width", 70))
        _caja_vacia(sub, ancho / 2, 0, ancho, 26)
        return sub, ancho, 0
    if "formula" in dato:
        w = _tq(sub, 0, 5, dato["formula"], size=13)
        return sub, w, 0
    interior = d._Lienzo(c.pal, c.sufijo)
    w, h = _dibujar_molecula(interior, dato, f"reaction.steps[{i}]")
    _incrustar(sub, interior, 0, -h / 2)
    return sub, w, h


@_errores
def _reaccion(c: d._Lienzo, b: dict) -> Punto:
    pasos = b.get("steps")
    if not isinstance(pasos, list) or not pasos:
        raise d.ErrorDiagrama("reaction: 'steps' es una lista de fórmulas, '+', flechas y moléculas")
    top = d._encabezado(c, b)
    maximo = float(b.get("maxWidth", 640))
    piezas = [_pieza_reaccion(c, p, i) for i, p in enumerate(pasos)]
    filas: list[list[tuple[d._Lienzo, float, float]]] = [[]]
    ancho_fila = 0.0
    for pieza in piezas:
        if filas[-1] and ancho_fila + pieza[1] > maximo:
            filas.append([])
            ancho_fila = 0.0
        filas[-1].append(pieza)
        ancho_fila += pieza[1] + 10
    y, ancho = top, 0.0
    for fila in filas:
        alto = max(max(h for _, _, h in fila), 40)
        centro = y + alto / 2
        x = 0.0
        for sub, w, _h in fila:
            _incrustar(c, sub, x, centro)
            x += w + 10
        ancho = max(ancho, x)
        y += alto + 14
    return ancho, y - 14


# --- TRePEV ---------------------------------------------------------------------------------------------

# (AXE, nombre, ángulo, hibridación, ligandos [(ángulo en grados, trazo)], pares libres, par del ángulo)
GEOMETRIAS: dict[str, tuple] = {
    "linear": ("AX2", "lineal", "180°", "sp", [(180, "p"), (0, "p")], [], (0, 1)),
    "trigonal_planar": ("AX3", "trigonal plana", "120°", "sp²", [(90, "p"), (210, "p"), (330, "p")], [], (1, 2)),
    "bent_trigonal": ("AX2E", "angular", "≈ 117°", "sp²", [(210, "p"), (330, "p")], [90], (0, 1)),
    "tetrahedral": ("AX4", "tetraédrica", "109,5°", "sp³", [(90, "p"), (210, "p"), (330, "w"), (15, "h")], [], (0, 1)),
    "trigonal_pyramidal": ("AX3E", "piramidal trigonal", "≈ 107°", "sp³", [(210, "p"), (330, "w"), (290, "h")], [90],
                           (0, 1)),
    "bent": ("AX2E2", "angular", "≈ 104,5°", "sp³", [(215, "p"), (325, "p")], [60, 120], (0, 1)),
    "trigonal_bipyramidal": ("AX5", "bipirámide trigonal", "90° y 120°", "sp³d",
                             [(90, "p"), (270, "p"), (180, "p"), (330, "w"), (30, "h")], [], (0, 2)),
    "seesaw": ("AX4E", "balancín", "< 90° y < 120°", "sp³d", [(90, "p"), (270, "p"), (330, "w"), (30, "h")], [180],
               (1, 2)),
    "t_shaped": ("AX3E2", "forma de T", "< 90°", "sp³d", [(90, "p"), (270, "p"), (0, "p")], [210, 150], (0, 2)),
    "linear_tbp": ("AX2E3", "lineal", "180°", "sp³d", [(90, "p"), (270, "p")], [180, 330, 30], (0, 1)),
    "octahedral": ("AX6", "octaédrica", "90°", "sp³d²", [(90, "p"), (270, "p"), (180, "p"), (0, "p"), (225, "w"),
                                                       (45, "h")], [], (0, 2)),
    "square_pyramidal": ("AX5E", "pirámide cuadrada", "< 90°", "sp³d²",
                         [(90, "p"), (180, "p"), (0, "p"), (225, "w"), (45, "h")], [270], (0, 1)),
    "square_planar": ("AX4E2", "cuadrada plana", "90°", "sp³d²", [(180, "p"), (0, "p"), (225, "w"), (45, "h")],
                      [90, 270], (0, 2)),
}
_POR_PARES = {(2, 0): "linear", (3, 0): "trigonal_planar", (2, 1): "bent_trigonal", (4, 0): "tetrahedral",
              (3, 1): "trigonal_pyramidal", (2, 2): "bent", (5, 0): "trigonal_bipyramidal", (4, 1): "seesaw",
              (3, 2): "t_shaped", (2, 3): "linear_tbp", (6, 0): "octahedral", (5, 1): "square_pyramidal",
              (4, 2): "square_planar"}


def _lobulo(c: d._Lienzo, x: float, y: float, ang: float, largo: float = 26) -> None:
    """Un par libre: un lóbulo con dos puntos, que empieza afuera del símbolo del átomo central."""
    ux, uy = math.cos(ang), -math.sin(ang)
    cx, cy = x + ux * (11 + largo * 0.5), y + uy * (11 + largo * 0.5)
    grados = -math.degrees(ang)
    c.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{largo * 0.5:.1f}" ry="{largo * 0.27:.1f}" fill="none" '
          f'stroke="{c.pal["strokeSub"]}" stroke-width="1" transform="rotate({grados:.1f} {cx:.1f} {cy:.1f})"/>')
    for s in (-2.6, 2.6):
        c.punto(cx + ux * 3 - uy * s, cy + uy * 3 + ux * s, color="strokeMain", radio=1.4)


@_errores
def _trepev(c: d._Lienzo, b: dict) -> Punto:
    ligandos = [str(x) for x in (b.get("ligands") or [])]
    clave = b.get("geometry")
    if clave is None:
        clave = _POR_PARES.get((len(ligandos), int(b.get("lonePairs", 0))))
        if clave is None:
            raise d.ErrorDiagrama(f"vsepr: {len(ligandos)} ligandos y {b.get('lonePairs', 0)} pares libres no forman "
                                  "una geometría conocida (o indicá geometry)")
    if clave not in GEOMETRIAS:
        raise d.ErrorDiagrama(f"vsepr: geometry {clave!r} (valen {', '.join(GEOMETRIAS)})")
    axe, nombre, angulo, hibrido, posiciones, pares, par_angulo = GEOMETRIAS[clave]
    if not ligandos:
        ligandos = ["X"] * len(posiciones)
    if len(ligandos) != len(posiciones):
        raise d.ErrorDiagrama(f"vsepr: la geometría {clave} lleva {len(posiciones)} ligandos (hay {len(ligandos)})")
    top = d._encabezado(c, b)
    largo = 56.0
    cx, cy = 130.0, top + 84
    trazo = c.pal["strokeMain"]
    central = str(b.get("central", "A"))
    for ang_g, tipo in posiciones:
        ang = math.radians(ang_g)
        f = 0.82 if tipo != "p" else 1.0
        ux, uy = math.cos(ang), -math.sin(ang)
        ax, ay = cx + ux * 11, cy + uy * 11
        bx, by = cx + ux * largo * f - ux * 9, cy + uy * largo * f - uy * 9
        px, py = -uy, ux
        if tipo == "w":
            c.add(f'<polygon points="{ax:.1f},{ay:.1f} {bx + px * 4:.1f},{by + py * 4:.1f} {bx - px * 4:.1f},'
                  f'{by - py * 4:.1f}" fill="{trazo}"/>')
        elif tipo == "h":
            for k in range(1, 8):
                t = k / 7
                hx, hy = ax + (bx - ax) * t, ay + (by - ay) * t
                w = 0.6 + 3.4 * t
                c.add(f'<line x1="{hx + px * w:.1f}" y1="{hy + py * w:.1f}" x2="{hx - px * w:.1f}" y2="{hy - py * w:.1f}" '
                      f'stroke="{trazo}" stroke-width="1.1"/>')
        else:
            c.add(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{trazo}" stroke-width="1.8"/>')
    for (ang_g, tipo), etiqueta in zip(posiciones, ligandos):
        ang = math.radians(ang_g)
        f = 0.82 if tipo != "p" else 1.0
        _tq(c, cx + math.cos(ang) * largo * f, cy - math.sin(ang) * largo * f + 4, etiqueta, size=12, peso=500,
            ancla="middle")
    for ang_g in pares:
        _lobulo(c, cx, cy, math.radians(ang_g))
    _tq(c, cx, cy + 4.5, central, size=13, peso=700, ancla="middle")
    blanco = b.get("blank")
    todo_blanco = blanco is True
    blancos = set(blanco) if isinstance(blanco, list) else set()
    i, j = par_angulo
    diferencia = (posiciones[j][0] - posiciones[i][0] + 180) % 360 - 180      # el arco corto, con signo
    if b.get("showAngle", True) and abs(diferencia) < 179:
        a1 = math.radians(posiciones[i][0])
        a2 = math.radians(posiciones[i][0] + diferencia)
        r = 26
        x1, y1 = cx + math.cos(a1) * r, cy - math.sin(a1) * r
        x2, y2 = cx + math.cos(a2) * r, cy - math.sin(a2) * r
        # En pantalla y crece hacia abajo: un giro antihorario (diferencia > 0) es sweep-flag 0.
        c.add(f'<path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 0 {0 if diferencia > 0 else 1} {x2:.1f} {y2:.1f}" '
              f'fill="none" stroke="{c.pal["strokeSub"]}" stroke-width="1" stroke-dasharray="2 2"/>')
        medio = a1 + math.radians(diferencia / 2)
        tx, ty = cx + math.cos(medio) * (r + 15), cy - math.sin(medio) * (r + 15)
        if todo_blanco or "angle" in blancos:
            _caja_vacia(c, tx, ty, 34, 13)
        else:
            c.t(tx, ty + 3.5, angulo.split(" y ")[0], size=8.5, color="textSub", ancla="middle", fuente=d.SANS)
    filas = [("Notación", axe, "axe"), ("Geometría", nombre, "name"),
             ("Ángulo", angulo, "angle"), ("Hibridación", hibrido, "hybridization")]
    x, y = 270.0, top + 50
    for etiqueta, valor, clave_b in filas:
        if clave_b == "hybridization" and not b.get("showHybridization", True):
            continue
        c.t(x, y, f"{etiqueta}:", size=10.5, peso=700, fuente=d.SANS)
        if todo_blanco or clave_b in blancos:
            c.vacio(x + 88, x + 200, y + 2)
        elif clave_b == "axe":
            _tq(c, x + 88, y, _axe(valor), size=10.5)
        else:
            c.t(x + 88, y, valor, size=10.5, fuente=d.SANS)
        y += 22
    return 480, max(top + 168, y)


def _axe(texto: str) -> str:
    """AX3E2 → AX_3E_2 (los números como subíndice)."""
    return "".join(f"_{ch}" if ch.isdigit() else ch for ch in texto)


# --- Orbitales ------------------------------------------------------------------------------------------

def _flechita(c: d._Lienzo, x: float, y: float, arriba: bool, alto: float = 14) -> None:
    trazo = c.pal["strokeMain"]
    y1, y2 = (y + alto / 2, y - alto / 2) if arriba else (y - alto / 2, y + alto / 2)
    signo = -1 if arriba else 1
    c.add(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{trazo}" stroke-width="1.4"/>'
          f'<path d="M {x - 3:.1f} {y2 - signo * 4:.1f} L {x:.1f} {y2:.1f} L {x + 3:.1f} {y2 - signo * 4:.1f}" '
          f'fill="none" stroke="{trazo}" stroke-width="1.4"/>')


def _cajas(c: d._Lienzo, x: float, y: float, electrones: int, cajas: int, lado: float = 22,
           vacio: bool = False) -> float:
    """Los casilleros de un subnivel (Hund): devuelve el ancho."""
    llenas = [0] * cajas if vacio else q.llenar_cajas(electrones, cajas)
    for i, n in enumerate(llenas):
        bx = x + i * lado
        c.add(f'<rect x="{bx:.1f}" y="{y:.1f}" width="{lado:.1f}" height="{lado:.1f}" fill="{c.pal["fillCell"]}" '
              f'stroke="{c.pal["strokeMain"]}" stroke-width="1.2"/>')
        if n >= 1:
            _flechita(c, bx + (lado / 2 - 4 if n == 2 else lado / 2), y + lado / 2, True)
        if n == 2:
            _flechita(c, bx + lado / 2 + 4, y + lado / 2, False)
    return cajas * lado


@_errores
def _orbitales(c: d._Lienzo, b: dict) -> Punto:
    tipo = str(b.get("kind", "atomic"))
    if tipo == "atomic":
        return _orbitales_atomicos(c, b)
    if tipo == "molecular":
        return _orbitales_moleculares(c, b)
    raise d.ErrorDiagrama(f"orbitals: kind {tipo!r} (vale atomic o molecular)")


def _orbitales_atomicos(c: d._Lienzo, b: dict) -> Punto:
    if "element" not in b:
        raise d.ErrorDiagrama("orbitals: falta element (símbolo o número atómico)")
    conf = q.configuracion(b["element"], int(b.get("charge", 0)))
    blanco = bool(b.get("blank"))
    nucleo = conf.nucleo() if b.get("core") else None
    subniveles = [(nl, e) for nl, e in conf.ocupacion.items() if not nucleo or nl not in nucleo[1]]
    top = d._encabezado(c, b)
    x, y, ancho = 0.0, top + 22, 0.0
    if nucleo:
        c.r(0, y, 44, 22, relleno="fillHeader", trazo=1.2)
        c.t(22, y + 15, f"[{nucleo[0]}]", size=11, peso=700, ancla="middle", fuente=d.SANS)
        x = 58.0
    maximo = float(b.get("maxWidth", 600))
    for nl, e in subniveles:
        w = (2 * nl[1] + 1) * 22
        if x + w > maximo and x > 0:
            x, y = 0.0, y + 52
        _cajas(c, x, y, e, 2 * nl[1] + 1, vacio=blanco)
        c.t(x + w / 2, y + 36, q.nombre_subnivel(nl), size=10.5, peso=600, ancla="middle", fuente=d.SANS)
        x += w + 14
        ancho = max(ancho, x)
    y += 58
    carga = int(b.get("charge", 0))
    especie = conf.simbolo + (f"^{abs(carga) if abs(carga) > 1 else ''}{'+' if carga > 0 else '-'}" if carga else "")
    if b.get("showConfig", True):
        c.t(0, y, "Configuración:", size=10.5, peso=700, fuente=d.SANS)
        _tq(c, 96, y, especie, size=10.5, peso=700)
        if blanco or b.get("blankConfig"):
            c.vacio(130, 430, y + 2)
        else:
            c.t(130, y, conf.texto(bool(b.get("core"))), size=10.5, fuente=d.SANS)
        y += 20
    if b.get("showUnpaired"):
        valor = None if blanco or b.get("blankUnpaired") else str(conf.desapareados())
        _rotulo_q(c, 0, y, "Electrones desapareados", valor, valor is None, size=10.5)
        y += 20
    return max(ancho, 440), y


def _nombre_om(c: d._Lienzo, x: float, y: float, nombre: str) -> None:
    """σ*2p con el asterisco arriba y el 2p abajo, centrado en x."""
    letra, resto = nombre[0], nombre[1:]
    estrella = resto.startswith("*")
    origen = resto.lstrip("*")
    texto = letra + ("^*" if estrella else "") + "_{" + origen + "}"
    _tq(c, x, y, texto, size=10, color="textSub", ancla="middle")


def _orbitales_moleculares(c: d._Lienzo, b: dict) -> Punto:
    atomos = b.get("atoms") or b.get("molecule")
    if not atomos:
        raise d.ErrorDiagrama("orbitals: kind molecular necesita atoms: [O, O] (o molecule: O)")
    om = q.orbitales_moleculares(atomos, int(b.get("charge", 0)))
    top = d._encabezado(c, b)
    izq, der = om.atomos
    en_izq = q.ELECTRONEGATIVIDAD.get(izq, 0)
    en_der = q.ELECTRONEGATIVIDAD.get(der, 0)
    desplazar = {izq: 0.0, der: 0.0}
    if en_izq != en_der:
        desplazar[izq if en_izq > en_der else der] = 16.0
    # Las alturas, de abajo hacia arriba.
    paso = 44.0
    alto = paso * (len(om.niveles) + 1)
    base = top + 30 + alto
    y_om = {n.nombre: base - paso * (i + 1) for i, n in enumerate(om.niveles)}
    xa, xm, xb = 40.0, 230.0, 420.0
    vacio = bool(b.get("blankElectrons"))
    lado = 20.0
    # Orbitales atómicos.
    if om.capa == 1:
        orbitales_at = [("1s", 1, (y_om["σ1s"] + y_om["σ*1s"]) / 2)]
    else:
        y2s = (y_om["σ2s"] + y_om["σ*2s"]) / 2
        enlazantes_p = [y_om["π2p"], y_om["σ2p"]]
        y2p = (min(enlazantes_p) + y_om["π*2p"]) / 2
        orbitales_at = [("2s", 1, y2s), ("2p", 3, y2p)]
    puntos_at: dict[tuple[str, str], tuple[float, float, float]] = {}
    for lado_x, atomo in ((xa, izq), (xb, der)):
        conf = q.configuracion(atomo)
        for orb, cajas, y in orbitales_at:
            y += desplazar[atomo]
            n = int(orb[0])
            electrones = conf.ocupacion.get((n, "spdf".index(orb[1])), 0)
            ancho = cajas * lado
            x0 = lado_x if lado_x == xa else lado_x - ancho + lado * 3
            _cajas(c, x0, y - lado / 2, electrones, cajas, lado)
            _tq(c, x0 + ancho / 2, y + lado / 2 + 13, f"{orb}", size=9.5, color="textSub", ancla="middle")
            puntos_at[(atomo + ("i" if lado_x == xa else "d"), orb)] = (x0, x0 + ancho, y)
        _tq(c, (lado_x + lado * 1.5), top + 16, f"{atomo}", size=12, peso=700, ancla="middle")
    nombre_molecula = (izq + "2" if izq == der else izq + der)
    carga = om.carga
    if carga:
        nombre_molecula += f"^{abs(carga) if abs(carga) > 1 else ''}{'+' if carga > 0 else '-'}"
    _tq(c, xm + lado, top + 16, nombre_molecula, size=12, peso=700, ancla="middle")
    # Orbitales moleculares y las líneas de correlación.
    for nivel in om.niveles:
        y = y_om[nivel.nombre]
        ancho = nivel.degenerado * lado
        x0 = xm + lado - ancho / 2
        _cajas(c, x0, y - lado / 2, nivel.electrones, nivel.degenerado, lado, vacio=vacio)
        _nombre_om(c, x0 + ancho / 2, y + lado / 2 + 11, nivel.nombre)
        for clave, (ax0, ax1, ay) in puntos_at.items():
            if clave[1] != nivel.origen:
                continue
            if clave[0].endswith("i"):
                c.linea(ax1 + 2, ay, x0 - 2, y, color="strokeMuted", ancho=0.8, flecha=None, guiones="3 3")
            else:
                c.linea(ax0 - 2, ay, x0 + ancho + 2, y, color="strokeMuted", ancho=0.8, flecha=None, guiones="3 3")
    c.add(f'<line x1="{xa - 18:.1f}" y1="{base:.1f}" x2="{xa - 18:.1f}" y2="{top + 30:.1f}" '
          f'stroke="{c.pal["strokeSub"]}" stroke-width="1.2" marker-end="url(#flecha-sub-{c.sufijo})"/>')
    c.add(f'<text x="{xa - 24:.1f}" y="{(base + top) / 2:.1f}" text-anchor="middle" font-family="{d.SANS}" '
          f'font-size="10" fill="{c.pal["textSub"]}" transform="rotate(-90 {xa - 24:.1f} {(base + top) / 2:.1f})">'
          "Energía</text>")
    y = base + 26
    blanco = b.get("blank") is True
    orden = om.orden_enlace
    texto_orden = str(int(orden)) if orden == int(orden) else _coma(orden, 1)
    _rotulo_q(c, 0, y, "Orden de enlace", texto_orden, blanco or bool(b.get("blankBondOrder")), size=10.5)
    y += 20
    if b.get("blankMagnetism") or blanco:
        c.t(0, y, "Magnetismo:", size=10.5, peso=700, fuente=d.SANS)
        c.vacio(84, 220, y + 2)
    else:
        c.t(0, y, f"Magnetismo: {om.magnetismo} ({om.desapareados} e⁻ desapareados)", size=10.5, peso=700,
            fuente=d.SANS)
    y += 8
    return xb + lado * 3 + 10, y


# --- Perfil de energía ---------------------------------------------------------------------------------

def _estados(lista: Any, donde: str) -> list[dict]:
    if not isinstance(lista, list) or len(lista) < 2:
        raise d.ErrorDiagrama(f"energy_profile: {donde} es una lista de al menos dos estados {{label, energy}}")
    salida = []
    for i, e in enumerate(lista):
        if not isinstance(e, dict) or "energy" not in e:
            raise d.ErrorDiagrama(f"energy_profile: {donde}[{i}] es {{label, energy, ts}}")
        salida.append({"label": str(e.get("label", "")), "energy": float(e["energy"]), "ts": bool(e.get("ts"))})
    return salida


@_errores
def _perfil(c: d._Lienzo, b: dict) -> Punto:
    estados = _estados(b.get("states"), "states")
    catal = _estados(b["catalyzed"], "catalyzed") if b.get("catalyzed") else None
    top = d._encabezado(c, b)
    x0, y0, w, h = 50.0, top + 16, 480.0, 250.0
    todas = [e["energy"] for e in estados + (catal or [])]
    lo, hi = min(todas), max(todas)
    margen = (hi - lo) * 0.15 or 10

    def py(v: float) -> float:
        return y0 + h - (v - lo + margen) / (hi - lo + 2 * margen) * h

    trazo = c.pal["strokeMain"]
    c.add(f'<line x1="{x0:.1f}" y1="{y0 + h:.1f}" x2="{x0:.1f}" y2="{y0 - 6:.1f}" stroke="{trazo}" stroke-width="1.3" '
          f'marker-end="url(#flecha-sub-{c.sufijo})"/>'
          f'<line x1="{x0:.1f}" y1="{y0 + h:.1f}" x2="{x0 + w + 8:.1f}" y2="{y0 + h:.1f}" stroke="{trazo}" '
          f'stroke-width="1.3" marker-end="url(#flecha-sub-{c.sufijo})"/>')
    unidad = str(b.get("unit", "kJ/mol"))
    c.add(f'<text x="{x0 - 14:.1f}" y="{y0 + h / 2:.1f}" text-anchor="middle" font-family="{d.SANS}" font-size="10" '
          f'font-weight="600" fill="{c.pal["textMain"]}" transform="rotate(-90 {x0 - 14:.1f} {y0 + h / 2:.1f})">'
          f'{d._esc(b.get("yLabel") or f"Energía ({unidad})")}</text>')
    c.t(x0 + w / 2, y0 + h + 18, str(b.get("xLabel") or "Coordenada de reacción"), size=10, peso=600, ancla="middle",
        fuente=d.SANS)

    def recorrido(lista: list[dict]) -> list[Punto]:
        n = len(lista) - 1
        xs = [x0 + 30 + (w - 60) * i / n for i in range(n + 1)]
        puntos = []
        for i in range(n):
            for k in range(25):
                t = k / 24
                s = (1 - math.cos(math.pi * t)) / 2
                puntos.append((xs[i] + (xs[i + 1] - xs[i]) * t,
                               py(lista[i]["energy"] + (lista[i + 1]["energy"] - lista[i]["energy"]) * s)))
        return [(xs[0] - 22, py(lista[0]["energy"]))] + puntos + [(xs[-1] + 22, py(lista[-1]["energy"]))]

    def dibujar(lista: list[dict], estilo: int) -> list[float]:
        puntos = recorrido(lista)
        guiones = _GUIONES[estilo]
        c.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)}" fill="none" stroke="{trazo}" '
              f'stroke-width="1.9"' + (f' stroke-dasharray="{guiones}"' if guiones else "") + "/>")
        n = len(lista) - 1
        return [x0 + 30 + (w - 60) * i / n for i in range(n + 1)]

    xs = dibujar(estados, 0)
    blanco = bool(b.get("blankAnnotations"))
    for i, (x, e) in enumerate(zip(xs, estados)):
        y = py(e["energy"])
        if e["label"]:
            if e["ts"]:
                _tq(c, x, y - 10, e["label"], size=10, ancla="middle")
            else:
                _tq(c, x, y + 18, e["label"], size=10.5, ancla="middle")
        if b.get("showEnergies"):
            c.t(x, y - 24 if e["ts"] else y - 6, _g(e["energy"]), size=9, color="textSub", ancla="middle",
                fuente=d.SANS)
    if catal:
        dibujar(catal, 1)
        c.t(x0 + w - 4, y0 + 8, "— sin catalizador", size=9.5, ancla="end", fuente=d.SANS)
        c.t(x0 + w - 4, y0 + 22, "- - con catalizador", size=9.5, ancla="end", fuente=d.SANS)
    pedidas = b.get("annotations", ["Ea", "dH"])
    # Ea de cada etapa: desde el mínimo anterior hasta el estado de transición.
    etapas = []
    minimo = estados[0]
    for i, e in enumerate(estados):
        if e["ts"]:
            etapas.append((i, minimo, e))
        else:
            minimo = e
    if "Ea" in pedidas:
        varias = len(etapas) > 1
        for k, (i, base_e, ts) in enumerate(etapas, 1):
            x = xs[i]
            yb, yt = py(base_e["energy"]), py(ts["energy"])
            xb = xs[estados.index(base_e)]
            c.linea(xb, yb, x + 8, yb, color="strokeSub", ancho=0.9, flecha=None, guiones="4 3")
            _flecha_doble(c, x + 4, yb - 1, yt + 1)
            nombre = f"Ea_{k}" if varias else "Ea"
            valor = f"{_g(ts['energy'] - base_e['energy'])} {unidad}"
            if blanco:
                _tq(c, x + 10, (yb + yt) / 2 + 4, nombre + " =", size=10, peso=700, fondo=True)
                c.vacio(x + 10 + ancho_formula(nombre + " =", 10) + 4, x + 10 + ancho_formula(nombre, 10) + 60,
                        (yb + yt) / 2 + 6)
            else:
                _tq(c, x + 10, (yb + yt) / 2 + 4, f"{nombre} = {valor}", size=10, peso=700, fondo=True)
    if "dH" in pedidas:
        ei, ef = estados[0]["energy"], estados[-1]["energy"]
        x = xs[-1] + 36
        c.linea(xs[0], py(ei), x + 6, py(ei), color="strokeSub", ancho=0.9, flecha=None, guiones="4 3")
        _flecha_doble(c, x, py(ei), py(ef))
        signo = "exotérmica" if ef < ei else "endotérmica"
        texto = f"{_g(ef - ei)} {unidad}"
        y_texto = (py(ei) + py(ef)) / 2 + 4
        if blanco:
            c.t(x + 6, y_texto, "ΔH =", size=10, peso=700, fuente=d.SANS)
            c.vacio(x + 38, x + 100, y_texto + 2)
        else:
            c.t(x + 6, y_texto, f"ΔH = {texto}", size=10, peso=700, fuente=d.SANS)
            c.t(x + 6, y_texto + 13, f"({signo})", size=9, color="textSub", fuente=d.SANS)
    if b.get("showRateDetermining") and len(etapas) > 1:
        k, (i, base_e, ts) = max(enumerate(etapas, 1), key=lambda par: par[1][2]["energy"] - par[1][1]["energy"])
        c.t(xs[i], y0 + h - 6, f"etapa {k}: determinante", size=9, color="textSub", ancla="middle", fuente=d.SANS)
    return x0 + w + 130, y0 + h + 26


# --- Titulación y especiación ----------------------------------------------------------------------------

@_errores
def _titulacion(c: d._Lienzo, b: dict) -> Punto:
    titulante = b.get("titrant") or {}
    if not isinstance(titulante, dict):
        raise d.ErrorDiagrama("titration: 'titrant' es {conc, name}")
    t = q.titulacion(b.get("analyte"), titulante.get("conc", 0.1), b.get("vMax"))
    nombre = str(titulante.get("name") or ("NaOH" if t.analito.es_acido else "HCl"))
    top = d._encabezado(c, b)
    x0, y0, w, h = 58.0, top + 16, 460.0, 260.0
    ejes = _Ejes(c, x0, y0, w, h, (0.0, t.vmax), (0.0, 14.0), "", "pH", ypaso=2)
    _tq(c, x0 + w / 2, y0 + h + 30, f"V {nombre} (mL)", size=10, peso=600, ancla="middle")
    indicador = b.get("indicator")
    if isinstance(indicador, dict) and "range" in indicador:
        a, z = (float(v) for v in indicador["range"])
        c.add(f'<rect x="{x0:.1f}" y="{ejes.py(z):.1f}" width="{w:.1f}" height="{ejes.py(a) - ejes.py(z):.1f}" '
              f'fill="{c.pal["fillHighlight"]}" opacity="0.7"/>')
        c.t(x0 + w - 4, ejes.py(z) - 3, f"{indicador.get('name', 'indicador')} ({_coma(a, 1)}–{_coma(z, 1)})",
            size=9, color="textSub", ancla="end", fuente=d.SANS)
    ejes.curva(list(zip(t.volumenes, t.phs)), ancho=2)
    for dato in b.get("data") or []:
        c.add(f'<circle cx="{ejes.px(float(dato[0])):.1f}" cy="{ejes.py(float(dato[1])):.1f}" r="2.6" fill="none" '
              f'stroke="{c.pal["strokeSub"]}" stroke-width="1.2"/>')
    pedidas = b.get("annotations", ["equivalence", "half"])
    blanco = bool(b.get("blankAnnotations"))
    varias = len(t.equivalencias) > 1
    if "equivalence" in pedidas:
        for k, (v, ph) in enumerate(t.equivalencias, 1):
            ejes.guia(v, 0, v, ph)
            ejes.guia(0, ph, v, ph)
            c.punto(ejes.px(v), ejes.py(ph), radio=3.4)
            sufijo = f"_{k}" if varias else ""
            x_txt = ejes.px(v) + 8
            arriba = t.analito.es_acido
            y_txt = ejes.py(ph) + (14 if arriba else -8)
            _tq(c, x_txt, y_txt, f"V_eq{sufijo} = {_g(v)} mL", size=9.5, peso=700, fondo=True)
            _rotulo_q(c, x_txt, y_txt + 13, "pH", _coma(ph), blanco, size=9.5)
    if "half" in pedidas:
        for k, (v, ph, pka) in enumerate(t.semi, 1):
            ejes.guia(v, 0, v, ph, guiones="2 3")
            c.add(f'<circle cx="{ejes.px(v):.1f}" cy="{ejes.py(ph):.1f}" r="3.2" fill="{c.pal["fillCell"]}" '
                  f'stroke="{c.pal["strokeMain"]}" stroke-width="1.4"/>')
            sufijo = f"_{k}" if len(t.semi) > 1 else ""
            texto = f"pK_a{sufijo} =" if blanco else f"pH = pK_a{sufijo} = {_coma(pka)}"
            ancho = ancho_formula(texto, 9.5) + (44 if blanco else 0)
            y_txt = ejes.py(ph) - 8 if t.analito.es_acido else ejes.py(ph) + 16
            if ejes.px(v) - 6 - ancho >= x0 + 4:
                x_txt, ancla = ejes.px(v) - 6 - (44 if blanco else 0), "end"
            else:
                x_txt, ancla = ejes.px(v) + 8, "start"
            _tq(c, x_txt, y_txt, texto, size=9.5, peso=700, ancla=ancla, fondo=True)
            if blanco:
                inicio = x_txt + 3 if ancla == "end" else x_txt + ancho_formula(texto, 9.5) + 3
                c.vacio(inicio, inicio + 38, y_txt + 2)
    if "initial" in pedidas:
        valor = None if blanco else _coma(t.ph_inicial)
        _rotulo_q(c, x0 + 8, y0 + 16, "pH inicial", valor, valor is None, size=9.5)
    return x0 + w + 10, y0 + h + 40


def _especies_por_defecto(n: int) -> list[str]:
    salida = []
    for j in range(n + 1):
        protones = n - j
        h = "" if protones == 0 else ("H" if protones == 1 else f"H{protones}")
        carga = "" if j == 0 else f"^{j if j > 1 else ''}-"
        salida.append(f"{h}A{carga}")
    return salida


@_errores
def _especiacion(c: d._Lienzo, b: dict) -> Punto:
    pkas = sorted(float(p) for p in q._lista(b.get("pKa")))
    if not pkas:
        raise d.ErrorDiagrama("speciation: falta pKa (uno o una lista)")
    especies = [str(s) for s in (b.get("species") or _especies_por_defecto(len(pkas)))]
    if len(especies) != len(pkas) + 1:
        raise d.ErrorDiagrama(f"speciation: con {len(pkas)} pKa hay {len(pkas) + 1} especies (species tiene "
                              f"{len(especies)})")
    top = d._encabezado(c, b)
    x0, y0, w, h = 58.0, top + 20, 460.0, 230.0
    ejes = _Ejes(c, x0, y0, w, h, (0.0, 14.0), (0.0, 1.0), "pH", "fracción α", ypaso=0.2)
    kas = [10 ** -p for p in pkas]
    phs = [14 * i / 560 for i in range(561)]
    curvas = [[] for _ in especies]
    for ph in phs:
        for j, alfa in enumerate(q.fracciones(10 ** -ph, kas)):
            curvas[j].append((ph, alfa))
    blanco_especies = bool(b.get("blankSpecies"))
    for j, curva in enumerate(curvas):
        ejes.curva(curva, estilo=j)
        ph_max, a_max = max(curva, key=lambda p: p[1])
        x, y = ejes.px(ph_max), ejes.py(a_max) - 6
        if j == 0:
            x = max(x, x0 + 26)
        if j == len(curvas) - 1:
            x = min(x, x0 + w - 26)
        if blanco_especies:
            _caja_vacia(c, x, y - 4, 40, 14)
        else:
            _tq(c, x, y, especies[j], size=10.5, peso=700, ancla="middle")
    blanco = bool(b.get("blankPKa"))
    for k, pka in enumerate(pkas, 1):
        ejes.guia(pka, 0, pka, 0.5, guiones="2 3")
        c.punto(ejes.px(pka), ejes.py(0.5), radio=2.6)
        sufijo = f"_{k}" if len(pkas) > 1 else ""
        y = y0 + h - 8 - (12 if k % 2 == 0 else 0)
        _rotulo_q(c, ejes.px(pka) + 3, y, f"pK_a{sufijo}", _coma(pka), blanco, size=9)
    return x0 + w + 10, y0 + h + 40


# --- Cinética -------------------------------------------------------------------------------------------

@_errores
def _cinetica(c: d._Lienzo, b: dict) -> Punto:
    top = d._encabezado(c, b)
    x0, y0, w, h = 64.0, top + 16, 450.0, 240.0
    modelo = str(b.get("model", "simple"))
    grafico = str(b.get("plot", "concentration"))
    blanco = bool(b.get("blankAnnotations"))
    pedidas = b.get("annotations", [])
    if grafico == "arrhenius":
        ea = q._num(b.get("Ea", 50), "Ea (kJ/mol)", positivo=True) * 1000
        a = q._num(b.get("A", 1e10), "A", positivo=True)
        t1, t2 = (float(v) for v in b.get("T", [280, 380]))
        xs = [1000 / (t1 + (t2 - t1) * i / 100) for i in range(101)]
        ys = [math.log(a) - ea / (q.R * 1000 / x) for x in xs]
        ejes = _Ejes(c, x0, y0, w, h, (min(xs), max(xs)), (min(ys) - 0.5, max(ys) + 0.5), "1000/T (K⁻¹)", "ln k")
        ejes.curva(list(zip(xs, ys)), ancho=2)
        pendiente = -ea / q.R
        y = y0 + 18
        _rotulo_q(c, x0 + w - 200, y, "pendiente = −Ea/R", f"{pendiente:.0f} K".replace("-", "−"), blanco, size=10)
        c.t(x0 + w - 200, y + 15, "(el eje x es 1000/T: la recta baja Ea/R por cada 1000)", size=8.5,
            color="textSub", fuente=d.SANS)
        return x0 + w + 10, y0 + h + 40
    if modelo == "consecutive":
        k1, k2 = q._num(b.get("k1", 1), "k1", positivo=True), q._num(b.get("k2", 0.5), "k2", positivo=True)
        a0 = q._num(b.get("A0", 1), "A0", positivo=True)
        t_fin = float(b.get("tEnd") or 5 / min(k1, k2))
        ts = [t_fin * i / 300 for i in range(301)]
        valores = [q.consecutiva(k1, k2, a0, t) for t in ts]
        ejes = _Ejes(c, x0, y0, w, h, (0, t_fin), (0, a0 * 1.08), str(b.get("xLabel") or "t (s)"),
                     str(b.get("yLabel") or "concentración (M)"))
        nombres = [str(n) for n in (b.get("species") or ["A", "B", "C"])]
        for j in range(3):
            ejes.curva([(t, v[j]) for t, v in zip(ts, valores)], estilo=j)
        _leyenda_q(c, x0 + w - 70, y0 + 14, [f"[{n}]" for n in nombres])
        tmax = q.t_maximo_intermediario(k1, k2)
        if tmax <= t_fin:
            bmax = q.consecutiva(k1, k2, a0, tmax)[1]
            ejes.guia(tmax, 0, tmax, bmax)
            c.punto(ejes.px(tmax), ejes.py(bmax), radio=3)
            _rotulo_q(c, ejes.px(tmax) + 6, ejes.py(bmax) - 8, "t máx", _g(tmax), blanco, size=9.5)
        return x0 + w + 10, y0 + h + 40
    if modelo == "reversible":
        kf, kb = q._num(b.get("kf", 1), "kf", positivo=True), q._num(b.get("kb", 0.5), "kb", positivo=True)
        a0 = q._num(b.get("A0", 1), "A0", positivo=True)
        t_fin = float(b.get("tEnd") or 5 / (kf + kb))
        ts = [t_fin * i / 300 for i in range(301)]
        valores = [q.reversible(kf, kb, a0, t) for t in ts]
        ejes = _Ejes(c, x0, y0, w, h, (0, t_fin), (0, a0 * 1.08), str(b.get("xLabel") or "t (s)"),
                     str(b.get("yLabel") or "concentración (M)"))
        nombres = [str(n) for n in (b.get("species") or ["A", "B"])]
        for j in range(2):
            ejes.curva([(t, v[j]) for t, v in zip(ts, valores)], estilo=j)
        _leyenda_q(c, x0 + w - 70, y0 + 14, [f"[{n}]" for n in nombres])
        k_eq = kf / kb
        _rotulo_q(c, x0 + w - 150, y0 + h - 14, "K = kf/kb", _g(k_eq), blanco, size=10)
        return x0 + w + 10, y0 + h + 40
    if modelo != "simple":
        raise d.ErrorDiagrama(f"kinetics: model {modelo!r} (vale simple, consecutive o reversible)")
    curvas = b.get("curves") or [{"order": b.get("order", 1), "k": b.get("k", 0.1), "A0": b.get("A0", 1)}]
    datos = []
    for i, cv in enumerate(curvas):
        orden = int(cv.get("order", 1))
        if orden not in (0, 1, 2):
            raise d.ErrorDiagrama(f"kinetics: orden {orden} (vale 0, 1 o 2)")
        k = q._num(cv.get("k", 0.1), f"curves[{i}].k", positivo=True)
        a0 = q._num(cv.get("A0", 1), f"curves[{i}].A0", positivo=True)
        datos.append((orden, k, a0, str(cv.get("label") or f"orden {orden}")))
    t_fin = float(b.get("tEnd") or max(4 * q.vida_media(o, k, a) if o else a / k * 1.1 for o, k, a, _ in datos))
    ts = [t_fin * i / 300 for i in range(301)]
    if grafico == "linear":
        if len(datos) != 1:
            raise d.ErrorDiagrama("kinetics: la linealización es de una sola curva")
        orden, k, a0, _ = datos[0]
        nombre_y = {0: "[A] (M)", 1: "ln [A]", 2: "1/[A] (M⁻¹)"}[orden]

        def f(t: float) -> float:
            v = q.concentracion(orden, k, a0, t)
            return {0: v, 1: math.log(v) if v > 0 else math.nan, 2: 1 / v if v > 0 else math.nan}[orden]

        if orden == 0:
            ts = [t for t in ts if t <= a0 / k]
        ys = [f(t) for t in ts]
        validos = [y for y in ys if math.isfinite(y)]
        lo, hi = min(validos), max(validos)
        margen = (hi - lo) * 0.1 or 1
        ejes = _Ejes(c, x0, y0, w, h, (0, t_fin), (lo - margen, hi + margen), str(b.get("xLabel") or "t (s)"),
                     nombre_y)
        ejes.curva(list(zip(ts, ys)), ancho=2)
        pendiente = {0: -k, 1: -k, 2: k}[orden]
        _rotulo_q(c, x0 + w - 170, y0 + 18, "pendiente", _g(pendiente), blanco, size=10)
        c.t(x0 + w - 170, y0 + 33, {0: "= −k", 1: "= −k", 2: "= +k"}[orden], size=9, color="textSub", fuente=d.SANS)
        return x0 + w + 10, y0 + h + 40
    a_max = max(a for _, _, a, _ in datos)
    ejes = _Ejes(c, x0, y0, w, h, (0, t_fin), (0, a_max * 1.08), str(b.get("xLabel") or "t (s)"),
                 str(b.get("yLabel") or "[A] (M)"))
    for j, (orden, k, a0, _) in enumerate(datos):
        ejes.curva([(t, q.concentracion(orden, k, a0, t)) for t in ts], estilo=j)
    if b.get("showProduct") and len(datos) == 1:
        orden, k, a0, _ = datos[0]
        ejes.curva([(t, a0 - q.concentracion(orden, k, a0, t)) for t in ts], estilo=1, ancho=1.4, color="strokeSub")
        _leyenda_q(c, x0 + w - 70, y0 + 14, ["[A]", "[P]"])
    elif len(datos) > 1:
        _leyenda_q(c, x0 + w - 100, y0 + 14, [et for *_, et in datos])
    if "halfLife" in pedidas and len(datos) == 1:
        orden, k, a0, _ = datos[0]
        t_m = q.vida_media(orden, k, a0)
        marcas = 3 if orden == 1 else 1
        for i in range(1, marcas + 1):
            t = t_m * i
            if t > t_fin:
                break
            v = q.concentracion(orden, k, a0, t)
            ejes.guia(0, v, t, v, guiones="2 3")
            ejes.guia(t, 0, t, v, guiones="2 3")
            c.t(ejes.px(t), y0 + h - 4, f"{i}·t½" if i > 1 else "t½", size=9, peso=700, ancla="middle", fuente=d.SANS)
        _rotulo_q(c, x0 + w - 150, y0 + 60, "t½", _g(t_m), blanco, size=10)
    return x0 + w + 10, y0 + h + 40


# --- Diagramas de fases ---------------------------------------------------------------------------------

def _texto_tp(t: float, p: float) -> str:
    return f"{_g(t, 4)} K; {_g(p, 3)} atm"


@_errores
def _fases(c: d._Lienzo, b: dict) -> Punto:
    if str(b.get("kind", "single")) == "eutectic":
        return _eutectico(c, b)
    f = q.fases(b)
    top = d._encabezado(c, b)
    x0, y0, w, h = 60.0, top + 16, 440.0, 270.0
    esquematico = str(b.get("scale", "schematic")) != "log"
    tt, pt = f.triple
    tc, pc = f.critico
    t_min, t_max = tt * 0.78, tc * 1.12
    p_min = f.p_sublimacion(t_min)
    p_max = pc * 6
    lmin, lmax = math.log10(p_min), math.log10(p_max)
    trazo = c.pal["strokeMain"]
    if esquematico:
        c.add(f'<line x1="{x0:.1f}" y1="{y0 + h:.1f}" x2="{x0:.1f}" y2="{y0 - 6:.1f}" stroke="{trazo}" '
              f'stroke-width="1.3" marker-end="url(#flecha-sub-{c.sufijo})"/>'
              f'<line x1="{x0:.1f}" y1="{y0 + h:.1f}" x2="{x0 + w + 8:.1f}" y2="{y0 + h:.1f}" stroke="{trazo}" '
              f'stroke-width="1.3" marker-end="url(#flecha-sub-{c.sufijo})"/>')
        c.t(x0 + w + 4, y0 + h + 16, "T", size=11, peso=700, ancla="end", fuente=d.SANS)
        c.t(x0 - 10, y0 + 4, "P", size=11, peso=700, ancla="end", fuente=d.SANS)

        def px(t: float) -> float:
            return x0 + (t - t_min) / (t_max - t_min) * w

        def py(p: float) -> float:
            return y0 + h - (math.log10(p) - lmin) / (lmax - lmin) * h
    else:
        ejes = _Ejes(c, x0, y0, w, h, (t_min, t_max), (lmin, lmax), "T (K)", "log₁₀ P (atm)")
        px, py = ejes.px, (lambda p: ejes.py(math.log10(p)))

    def polilinea(puntos: list[Punto], ancho: float = 2.0) -> None:
        c.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)}" fill="none" stroke="{trazo}" '
              f'stroke-width="{ancho}"/>')

    polilinea([(px(t), py(f.p_sublimacion(t))) for t in (t_min + (tt - t_min) * i / 60 for i in range(61))])
    polilinea([(px(t), py(f.p_vapor(t))) for t in (tt + (tc - tt) * i / 80 for i in range(81))])
    # Fusión: en escala real casi vertical; en el esquema, inclinada para que se vea el signo de la pendiente.
    if esquematico:
        inclinacion = -0.18 if f.pendiente_fusion < 0 else 0.18
        x_tp, y_tp = px(tt), py(pt)
        fusion = [(x_tp + inclinacion * (y_tp - (y0 + 2)), y0 + 2), (x_tp, y_tp)]

        def x_fusion(p: float) -> float:
            return x_tp + inclinacion * (y_tp - py(p))
    else:
        ps = [pt * (p_max / pt) ** (i / 60) for i in range(61)]
        fusion = [(px(f.t_fusion(p)), py(p)) for p in ps]

        def x_fusion(p: float) -> float:
            return px(f.t_fusion(p))
    polilinea(fusion)
    blancos = bool(b.get("blankPoints"))
    for nombre, (t, p), dx in (("Punto triple", f.triple, 8), ("Punto crítico", f.critico, 8)):
        c.punto(px(t), py(p), radio=3.6, color="strokeMain")
        x_txt, y_txt = px(t) + dx, py(p) + 16
        c.t(x_txt, y_txt, nombre, size=9.5, peso=700, fuente=d.SANS)
        if blancos:
            c.vacio(x_txt, x_txt + 110, y_txt + 14)
        else:
            c.t(x_txt, y_txt + 12, _texto_tp(t, p), size=9, color="textSub", fuente=d.SANS)
    if b.get("atm", True) and p_min < 1 < p_max:
        y1 = py(1)
        c.linea(x0, y1, x0 + w, y1, color="strokeSub", ancho=0.9, flecha=None, guiones="5 3")
        c.t(x0 + 4, y1 - 4, "1 atm", size=9, color="textSub", fuente=d.SANS)
        cortes = []
        if pt < 1:
            tf = f.normales.get("normalMelting", f.t_fusion(1.0))
            cortes.append(("Tf", tf, x_fusion(1.0)))
        tipo, tb = f.t_de_p(1.0)
        tb = f.normales.get("normalBoiling" if tipo == "ebullición" else "normalSublimation", tb)
        cortes.append(("Teb" if tipo == "ebullición" else "Tsub", tb, px(tb)))
        for nombre, t, x in cortes:
            c.punto(x, y1, radio=2.8)
            c.linea(x, y1, x, y0 + h, color="strokeMuted", ancho=0.7, flecha=None, guiones="2 3")
            _rotulo_q(c, x + 3, y0 + h - 6, nombre, _g(t, 4) + " K", blancos, size=9)

    def p_de_y(y: float) -> float:
        return 10 ** (lmin + (y0 + h - y) / h * (lmax - lmin))

    y_solido = y0 + h * 0.3
    x_solido = max(x0 + 30, (x0 + x_fusion(p_de_y(y_solido))) / 2)
    regiones = [("Sólido", x_solido, y_solido),
                ("Líquido", (x_fusion(pc) + px(tc)) / 2 + 14, y0 + h * 0.2),
                ("Gas", px(tt + (tc - tt) * 0.7), y0 + h * 0.85)]
    if b.get("supercritical", True):
        regiones.append(("Fluido supercrítico", px(tc) + 6, py(pc) - 12))
    for nombre, x, y in regiones:
        if b.get("blankRegions"):
            _caja_vacia(c, x, y - 4, 64, 16)
        else:
            c.t(x, y, nombre, size=11 if nombre != "Fluido supercrítico" else 9, peso=700, color="textSub",
                ancla="middle" if nombre != "Fluido supercrítico" else "start", fuente=d.SANS)
    for i, punto in enumerate(b.get("points") or []):
        try:
            t, p = float(punto["T"]), float(punto["P"])
        except (KeyError, TypeError, ValueError):
            raise d.ErrorDiagrama(f"phase_diagram.points[{i}]: {{T, P, label}}") from None
        x, y = px(t), py(p)
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c.pal["fillCell"]}" stroke="{trazo}" stroke-width="1.6"/>')
        c.t(x + 7, y - 6, str(punto.get("label", i + 1)), size=10, peso=700, fuente=d.SANS)
    if f.nombre:
        _tq(c, x0 + w - 4, y0 + h - 8, f.nombre, size=11, peso=700, ancla="end")
    return x0 + w + 130, y0 + h + 40


def _eutectico(c: d._Lienzo, b: dict) -> Punto:
    try:
        ta, tb = float(b["meltingA"]), float(b["meltingB"])
        xe, te = (float(v) for v in b["eutectic"])
    except (KeyError, TypeError, ValueError):
        raise d.ErrorDiagrama("phase_diagram: el eutéctico necesita meltingA, meltingB y eutectic: [x %, T]") from None
    if not (0 < xe < 100 and te < min(ta, tb)):
        raise d.ErrorDiagrama("phase_diagram: el eutéctico está entre 0 y 100 % y por debajo de los dos puntos de "
                              "fusión")
    a, z = (str(v) for v in (b.get("components") or ["A", "B"]))
    top = d._encabezado(c, b)
    x0, y0, w, h = 64.0, top + 16, 420.0, 260.0
    t_lo = te - (max(ta, tb) - te) * 0.35
    t_hi = max(ta, tb) + (max(ta, tb) - te) * 0.12
    ejes = _Ejes(c, x0, y0, w, h, (0, 100), (t_lo, t_hi), f"% {z} (en masa)", str(b.get("yLabel") or "T (°C)"))

    def liquidus(x: float) -> float:
        if x <= xe:
            s = x / xe
            return ta + (te - ta) * (s * 0.65 + s * s * 0.35)
        s = (100 - x) / (100 - xe)
        return tb + (te - tb) * (s * 0.65 + s * s * 0.35)

    xs = [i / 2 for i in range(201)]
    ejes.curva([(x, liquidus(x)) for x in xs], ancho=2)
    ejes.curva([(0, te), (100, te)], ancho=2)
    ejes.curva([(0, t_lo), (0, ta)], ancho=2)
    ejes.curva([(100, t_lo), (100, tb)], ancho=2)
    c.punto(ejes.px(xe), ejes.py(te), radio=3.6, color="strokeMain")
    blancos = bool(b.get("blankPoints"))
    _rotulo_q(c, ejes.px(xe) + 6, ejes.py(te) + 16, "E", f"{_g(xe)} %, {_g(te)} °C", blancos, size=9.5)
    regiones = [("L", 50, (t_hi + max(liquidus(50), te)) / 2 + (t_hi - te) * 0.12),
                (f"L + {a}(s)", xe * 0.38, (te + liquidus(xe * 0.5)) / 2),
                (f"L + {z}(s)", xe + (100 - xe) * 0.62, (te + liquidus(xe + (100 - xe) * 0.5)) / 2),
                (f"{a}(s) + {z}(s)", 50, (te + t_lo) / 2)]
    for nombre, x, t in regiones:
        if b.get("blankRegions"):
            _caja_vacia(c, ejes.px(x), ejes.py(t) - 4, 64, 16)
        else:
            _tq(c, ejes.px(x), ejes.py(t), nombre, size=10.5, peso=700, color="textSub", ancla="middle")
    if "cooling" in b:
        x = float(b["cooling"])
        tl = liquidus(x)
        ejes.guia(x, t_hi, x, t_lo, guiones="5 3")
        for t in (tl, te):
            c.punto(ejes.px(x), ejes.py(t), radio=3)
        _rotulo_q(c, ejes.px(x) + 5, ejes.py(tl) - 6, "T_liq", _g(tl, 3) + " °C", bool(b.get("blankCooling")), size=9)
    return x0 + w + 10, y0 + h + 40


# --- Curva de calentamiento -----------------------------------------------------------------------------

@_errores
def _calentamiento(c: d._Lienzo, b: dict) -> Punto:
    tramos = q.calentamiento(b)
    top = d._encabezado(c, b)
    x0, y0, w, h = 60.0, top + 16, 470.0, 250.0
    q_total = tramos[-1].q1
    t_lo, t_hi = tramos[0].t0, tramos[-1].t1
    margen = (t_hi - t_lo) * 0.1
    ejes = _Ejes(c, x0, y0, w, h, (0, q_total * 1.04), (t_lo - margen, t_hi + margen), "Q (kJ)", "T (°C)")
    puntos = [(tramos[0].q0, tramos[0].t0)] + [(t.q1, t.t1) for t in tramos]
    ejes.curva(puntos, ancho=2.2)
    blanco = bool(b.get("blankHeat"))
    for t in tramos:
        xm = ejes.px((t.q0 + t.q1) / 2)
        ym = ejes.py((t.t0 + t.t1) / 2)
        cambio = t.t0 == t.t1
        dy = -22 if cambio else 16
        # Un tramo de calentamiento se rotula a su derecha; si no entra, a la izquierda.
        ancla = "middle" if cambio else "start"
        x_txt = xm if cambio else xm + 10
        if not cambio and x_txt + 70 > x0 + w:
            ancla, x_txt = "end", xm - 8
        x_txt = min(max(x_txt, x0 + 34), x0 + w - 34) if cambio else x_txt
        if b.get("blankPhases"):
            centro = {"start": x_txt + 29, "end": x_txt - 29, "middle": x_txt}[ancla]
            _caja_vacia(c, max(centro, x0 + 31), ym + dy - 4, 58, 13)
        else:
            _tq(c, x_txt, ym + dy, t.fase, size=9.5, peso=700, ancla=ancla, color="textSub", fondo=True)
        if b.get("showHeat", True):
            y_q = ym + dy + 12
            if blanco:
                inicio = {"start": x_txt, "end": x_txt - 44, "middle": x_txt - 22}[ancla]
                c.vacio(max(inicio, x0 + 4), max(inicio, x0 + 4) + 44, y_q + 2)
            else:
                _tq(c, x_txt, y_q, f"{_g(t.q)} kJ", size=9, color="textSub", ancla=ancla, fondo=True)
    datos = dict(q.CALENTAMIENTO.get(str(b.get("substance", "water")).lower(), {}))
    datos.update(b)
    for nombre, clave in (("Tf", "melting"), ("Teb", "boiling")):
        if clave in datos and t_lo <= float(datos[clave]) <= t_hi:
            ejes.guia(0, float(datos[clave]), q_total * 1.04, float(datos[clave]), guiones="2 4")
            arriba = clave == "melting"
            c.t(x0 + w - 4 if arriba else x0 + 4, ejes.py(float(datos[clave])) + (-3 if arriba else 11),
                f"{nombre} = {_g(float(datos[clave]))} °C", size=8.5, color="textSub",
                ancla="end" if arriba else "start", fuente=d.SANS)
    if b.get("showTotal", True):
        _rotulo_q(c, x0 + w - 150, y0 + h - 12, "Q total", f"{_g(q_total, 4)} kJ", blanco, size=10)
    return x0 + w + 10, y0 + h + 40


# --- Espectros ------------------------------------------------------------------------------------------

def _picos(b: dict, clave: str = "peaks") -> list[dict]:
    lista = b.get(clave) or b.get("signals") or []
    if not isinstance(lista, list) or not lista:
        raise d.ErrorDiagrama(f"spectrum: falta {clave} (una lista)")
    for i, p in enumerate(lista):
        if not isinstance(p, dict):
            raise d.ErrorDiagrama(f"spectrum.{clave}[{i}]: un diccionario")
    return lista


@_errores
def _espectro(c: d._Lienzo, b: dict) -> Punto:
    tipo = str(b.get("kind", "ir"))
    top = d._encabezado(c, b)
    x0, y0, w, h = 58.0, top + 22, 480.0, 220.0
    blanco = bool(b.get("blankLabels"))
    puestos: list[tuple[float, float, float]] = []         # (x0, x1, y) de los rótulos ya escritos

    def rotular(x: float, y: float, texto: Any, ancla: str = "middle") -> None:
        if texto in (None, ""):
            return
        ancho = 40.0 if blanco else ancho_formula(texto, 9)
        y = min(max(y, y0 + 10), y0 + h - 4)
        # Dos rótulos que se pisan: el nuevo sube un renglón.
        while any(a < x + ancho / 2 + 3 and x - ancho / 2 - 3 < z and abs(yy - y) < 11 for a, z, yy in puestos):
            y -= 12
        puestos.append((x - ancho / 2, x + ancho / 2, y))
        if blanco:
            _caja_vacia(c, x, y - 4, 40, 13)
        else:
            _tq(c, x, y, texto, size=9, color="textSub", ancla=ancla, fondo=True)

    if tipo == "ir":
        picos = _picos(b)
        rango = b.get("range", [4000, 400])
        ejes = _Ejes(c, x0, y0, w, h, (float(rango[0]), float(rango[1])), (0, 100), "número de onda (cm⁻¹)",
                     "transmitancia (%)", ypaso=20)
        nus = [float(rango[0]) + (float(rango[1]) - float(rango[0])) * i / 900 for i in range(901)]

        def transmitancia(nu: float) -> float:
            total = 0.0
            for p in picos:
                ancho = float(p.get("width", 120 if p.get("broad") else 22))
                prof = float(p.get("depth", 0.7))
                total += prof * 1 / (1 + ((nu - float(p["at"])) / (ancho / 2)) ** 2)
            return max(2.0, 100 * (1 - min(total, 0.96)) - 4)

        ejes.curva([(nu, transmitancia(nu)) for nu in nus], ancho=1.5)
        for p in picos:
            nu = float(p["at"])
            rotular(ejes.px(nu), ejes.py(transmitancia(nu)) + 14, p.get("label"))
        return x0 + w + 10, y0 + h + 40
    if tipo in ("nmr", "c13"):
        picos = _picos(b, "signals")
        mhz = float(b.get("MHz", 400))
        maximo = 12.0 if tipo == "nmr" else 220.0
        hi = max(maximo, max(float(p["shift"]) for p in picos) + 1)
        ejes = _Ejes(c, x0, y0, w, h, (hi, 0.0), (0, 1.15), "δ (ppm)", "", grilla=False)
        lineas: list[tuple[float, float, dict]] = []
        for p in picos:
            delta = float(p["shift"])
            if tipo == "c13":
                lineas.append((delta, float(p.get("intensity", 0.8)), p))
                continue
            vecinos = p.get("neighbors")
            if vecinos is None:
                mult = str(p.get("multiplicity", "s"))
                if mult not in q.MULTIPLICIDAD and mult != "m":
                    raise d.ErrorDiagrama(f"spectrum: multiplicidad {mult!r} (s, d, t, q, quint, sext, sept, m)")
                vecinos = q.MULTIPLICIDAD.get(mult, 4)
            integracion = float(p.get("integration", 1))
            for delta_l, rel in q.multiplete(delta, int(vecinos), float(p.get("J", 7)), mhz):
                lineas.append((delta_l, rel * integracion, p))
        tope = max(v for _, v, _ in lineas)
        # A escala, J = 7 Hz son 0,02 ppm: las líneas de un multiplete se separan al menos 5 px para que se cuenten.
        separacion = float(b.get("lineSpacing", 5))
        for delta, v, p in lineas:
            altura = 0.95 * v / tope if tipo == "nmr" else min(v, 1.0)
            x = ejes.px(delta)
            if tipo == "nmr":
                centro = ejes.px(float(p["shift"]))
                real = x - centro
                paso_real = abs(ejes.px(0) - ejes.px(float(p.get("J", 7)) / mhz))
                if 0 < paso_real < separacion:
                    x = centro + real * separacion / paso_real
            c.linea(x, ejes.py(0), x, ejes.py(altura), color="strokeMain", ancho=1.3, flecha=None)
        for p in picos:
            delta = float(p["shift"])
            propias = [v for dl, v, pp in lineas if pp is p]
            altura = 0.95 * max(propias) / tope if tipo == "nmr" else min(float(p.get("intensity", 0.8)), 1.0)
            texto = str(p.get("label", ""))
            if tipo == "nmr" and b.get("showIntegration", True):
                texto = (texto + " " if texto else "") + f"{_g(float(p.get('integration', 1)))}H"
            rotular(ejes.px(delta), ejes.py(altura) - 6, texto)
        if b.get("tms"):
            c.linea(ejes.px(0), ejes.py(0), ejes.px(0), ejes.py(0.35), color="strokeSub", ancho=1.2, flecha=None)
            c.t(ejes.px(0), ejes.py(0.35) - 4, "TMS", size=8.5, color="textSub", ancla="middle", fuente=d.SANS)
        leyenda = f"RMN de ¹H, {_g(mhz)} MHz" if tipo == "nmr" else "RMN de ¹³C"
        c.t(x0 + 6, y0 + 14, leyenda, size=9.5, color="textSub", fuente=d.SANS)
        return x0 + w + 10, y0 + h + 40
    if tipo == "uv":
        picos = _picos(b, "bands")
        rango = b.get("range", [200, 800])
        a_max = max(float(p.get("absorbance", 1)) for p in picos) * 1.15
        ejes = _Ejes(c, x0, y0, w, h, (float(rango[0]), float(rango[1])), (0, a_max), "λ (nm)", "absorbancia")
        lams = [float(rango[0]) + (float(rango[1]) - float(rango[0])) * i / 600 for i in range(601)]

        def absorbancia(lam: float) -> float:
            return sum(float(p.get("absorbance", 1)) * math.exp(-((lam - float(p["at"])) / float(p.get("width", 25))) ** 2)
                       for p in picos)

        ejes.curva([(lam, absorbancia(lam)) for lam in lams], ancho=1.8)
        for p in picos:
            lam = float(p["at"])
            rotular(ejes.px(lam), ejes.py(absorbancia(lam)) - 6, p.get("label", f"λmáx = {_g(lam)} nm"))
        return x0 + w + 10, y0 + h + 40
    if tipo == "ms":
        picos = _picos(b)
        mzs = [float(p["mz"]) for p in picos]
        ejes = _Ejes(c, x0, y0, w, h, (0, max(mzs) * 1.1), (0, 110), "m/z", "intensidad relativa (%)", ypaso=20)
        tope = max(float(p.get("intensity", 100)) for p in picos)
        for p in picos:
            mz, v = float(p["mz"]), 100 * float(p.get("intensity", 100)) / tope
            c.linea(ejes.px(mz), ejes.py(0), ejes.px(mz), ejes.py(v), color="strokeMain", ancho=2.2, flecha=None)
            texto = p.get("label")
            texto = f"{_g(mz, 4)}" + (f" {texto}" if texto else "")
            rotular(ejes.px(mz), ejes.py(v) - 5, texto)
        return x0 + w + 10, y0 + h + 40
    raise d.ErrorDiagrama(f"spectrum: kind {tipo!r} (vale ir, nmr, c13, uv o ms)")


# --- Pila -----------------------------------------------------------------------------------------------

@_errores
def _pila(c: d._Lienzo, b: dict) -> Punto:
    semis = b.get("halfCells") or [b.get("anode"), b.get("cathode")]
    if not isinstance(semis, list) or len(semis) != 2 or None in semis:
        raise d.ErrorDiagrama("galvanic_cell: halfCells (dos semiceldas {couple, E0, n})")
    p = q.pila([q.semicelda(s, f"halfCells[{i}]") for i, s in enumerate(semis)])
    top = d._encabezado(c, b)
    trazo = c.pal["strokeMain"]
    y_cable, y_boca, y_fondo, y_liq = top + 34, top + 110, top + 240, top + 140
    vasos = ((50.0, 200.0, p.anodo), (350.0, 500.0, p.catodo))
    for xa, xb, _s in vasos:
        c.add(f'<rect x="{xa:.1f}" y="{y_liq:.1f}" width="{xb - xa:.1f}" height="{y_fondo - y_liq:.1f}" '
              f'fill="{c.pal["fillHighlight"]}" opacity="0.6"/>'
              f'<path d="M {xa:.1f} {y_boca:.1f} L {xa:.1f} {y_fondo:.1f} L {xb:.1f} {y_fondo:.1f} L {xb:.1f} '
              f'{y_boca:.1f}" fill="none" stroke="{trazo}" stroke-width="1.8"/>')
    # Electrodos y cable.
    centros = []
    for (xa, xb, s), x_elec in zip(vasos, (95.0, 455.0)):
        c.r(x_elec - 9, y_cable + 24, 18, y_fondo - 30 - (y_cable + 24), relleno="fillPointerBox", trazo=1.4)
        _tq(c, x_elec, y_cable + 20, s.electrodo, size=11, peso=700, ancla="middle")
        _tq(c, (xa + xb) / 2 + 22, y_fondo - 14, s.solucion, size=9.5, ancla="middle")
        centros.append(x_elec)
    xv, rv = 275.0, 17.0
    c.add(f'<path d="M {centros[0]:.1f} {y_cable + 8:.1f} L {centros[0]:.1f} {y_cable:.1f} L {xv - rv:.1f} '
          f'{y_cable:.1f} M {xv + rv:.1f} {y_cable:.1f} L {centros[1]:.1f} {y_cable:.1f} L {centros[1]:.1f} '
          f'{y_cable + 8:.1f}" fill="none" stroke="{trazo}" stroke-width="1.6"/>'
          f'<circle cx="{xv:.1f}" cy="{y_cable:.1f}" r="{rv}" fill="{c.pal["fillCell"]}" stroke="{trazo}" '
          'stroke-width="1.6"/>')
    c.t(xv, y_cable + 5, "V", size=13, peso=700, ancla="middle", fuente=d.SANS)
    blanco_e = bool(b.get("blankPotential"))
    _rotulo_q(c, xv, y_cable - 24, "E°", _coma(p.e0) + " V", blanco_e, ancla="middle", size=10)
    # Flujo de electrones.
    if b.get("blankFlow"):
        _caja_vacia(c, (centros[0] + xv) / 2, y_cable - 12, 54, 13)
    else:
        c.linea(centros[0] + 30, y_cable - 10, xv - rv - 14, y_cable - 10, color="accentPrimary", ancho=1.4)
        c.t((centros[0] + xv) / 2, y_cable - 15, "e⁻", size=10, peso=700, ancla="middle", fuente=d.SANS)
        c.linea(xv + rv + 14, y_cable - 10, centros[1] - 30, y_cable - 10, color="accentPrimary", ancho=1.4)
    # Puente salino.
    puente = b.get("saltBridge", "KNO3")
    if isinstance(puente, dict):
        cation, anion, sal = str(puente.get("cation", "K^+")), str(puente.get("anion", "NO3^-")), str(
            puente.get("name", "KNO3"))
    else:
        sal, cation, anion = str(puente), "K^+", "NO3^-"
    xi, xd, yb = 170.0, 380.0, top + 76
    camino = f"M {xi:.1f} {y_liq + 34:.1f} L {xi:.1f} {yb:.1f} L {xd:.1f} {yb:.1f} L {xd:.1f} {y_liq + 34:.1f}"
    c.add(f'<path d="{camino}" fill="none" stroke="{trazo}" stroke-width="15" stroke-linejoin="round"/>'
          f'<path d="{camino}" fill="none" stroke="{c.pal["fillCell"]}" stroke-width="11.4" stroke-linejoin="round"/>')
    _tq(c, (xi + xd) / 2, yb + 22, f"puente salino ({sal})", size=9.5, color="textSub", ancla="middle")
    if b.get("showIons", True):
        c.linea((xi + xd) / 2 - 12, yb, xi + 24, yb, color="strokeSub", ancho=1.1, flecha="sub")
        _tq(c, (xi + xd) / 2 - 40, yb - 11, anion, size=9, ancla="middle")
        c.linea((xi + xd) / 2 + 12, yb, xd - 24, yb, color="strokeSub", ancho=1.1, flecha="sub")
        _tq(c, (xi + xd) / 2 + 40, yb - 11, cation, size=9, ancla="middle")
    # Rótulos de cada electrodo.
    y = y_fondo + 20
    blanco_p = bool(b.get("blankPolarity"))
    blanco_r = bool(b.get("blankReactions"))
    for (xa, xb, s), nombre, proceso, reaccion in (
            (vasos[0], "Ánodo (−)", "oxidación", p.anodo.oxidacion),
            (vasos[1], "Cátodo (+)", "reducción", p.catodo.reduccion)):
        xm = (xa + xb) / 2
        if blanco_p:
            _caja_vacia(c, xm, y - 4, 90, 15)
            _caja_vacia(c, xm, y + 13, 70, 13)
        else:
            c.t(xm, y, nombre, size=11, peso=700, ancla="middle", fuente=d.SANS)
            c.t(xm, y + 15, proceso, size=10, color="textSub", ancla="middle", fuente=d.SANS)
        if blanco_r:
            c.vacio(xm - 80, xm + 80, y + 34)
        else:
            _tq(c, xm, y + 32, reaccion, size=10, ancla="middle")
        _tq(c, xm, y + 48, f"E° = {_coma(s.e0)} V", size=9, color="textSub", ancla="middle")
    y += 72
    if b.get("showNotation", True):
        c.t(0, y, "Notación:", size=10, peso=700, fuente=d.SANS)
        if b.get("blankNotation"):
            c.vacio(66, 470, y + 2)
        else:
            _tq(c, 66, y, p.notacion, size=10)
        y += 18
    if p.e is not None:
        _rotulo_q(c, 0, y, "E (Nernst, 25 °C)", _coma(p.e, 3) + " V", blanco_e, size=10)
        y += 18
    if b.get("showDeltaG"):
        _rotulo_q(c, 0, y, "ΔG°", f"{_g(p.delta_g, 4)} kJ/mol", blanco_e, size=10)
        y += 18
    return 560, y


# --- Celda unidad ---------------------------------------------------------------------------------------

_NOMBRES_RED = {"sc": "cúbica simple", "bcc": "cúbica centrada en el cuerpo", "fcc": "cúbica centrada en las caras",
                "nacl": "tipo NaCl", "cscl": "tipo CsCl"}


def _desglose(sitios: list[tuple[float, float, float, str]], especie: str) -> str:
    cuentas: dict[float, int] = {}
    for x, y, z, e in sitios:
        if e == especie:
            fr = q._fraccion(x, y, z)
            cuentas[fr] = cuentas.get(fr, 0) + 1
    nombres = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2", 1.0: "1"}
    partes = [f"{n} × {nombres[fr]}" if fr != 1 else f"{n}" for fr, n in sorted(cuentas.items())]
    return " + ".join(partes)


@_errores
def _celda(c: d._Lienzo, b: dict) -> Punto:
    celda = q.celda_unidad(str(b.get("lattice", "fcc")))
    top = d._encabezado(c, b)
    a = 150.0
    k = 0.42
    ox, oy = 30.0, top + 30 + a + a * k * 0.5

    def proy(x: float, y: float, z: float) -> Punto:
        return ox + a * x + a * k * z * math.cos(math.radians(30)), oy - a * y - a * k * z * math.sin(math.radians(30))

    vertices = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    oculto = (0, 0, 1)
    for p1 in vertices:
        for p2 in vertices:
            if p1 < p2 and sum(abs(u - v) for u, v in zip(p1, p2)) == 1:
                (x1, y1), (x2, y2) = proy(*p1), proy(*p2)
                atras = oculto in (p1, p2)
                c.linea(x1, y1, x2, y2, color="strokeMuted" if atras else "strokeMain", ancho=1 if atras else 1.4,
                        flecha=None, guiones="4 3" if atras else "")
    dos = len(celda.z) > 1
    radios = {"A": a * (0.12 if dos else 0.1), "B": a * 0.075}
    for x, y, z, especie in sorted(celda.sitios, key=lambda s: -s[2]):
        px, py = proy(x, y, z)
        relleno = c.pal["fillHighlight"] if especie == "A" else c.pal["strokeSub"]
        opacidad = 0.55 if z == 1 and (x, y) != (1, 1) else 1
        c.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{radios[especie]:.1f}" fill="{relleno}" '
              f'stroke="{c.pal["strokeMain"]}" stroke-width="1.1" opacity="{opacidad}"/>')
    nombres = [str(n) for n in (b.get("species") or ({"nacl": ["Cl^-", "Na^+"], "cscl": ["Cl^-", "Cs^+"]}.get(
        celda.red, [str(b.get("element", "M"))])))]
    x, y = 270.0, top + 34
    blanco = b.get("blank")
    blancos = {"z", "coordination", "packing", "density"} if blanco is True else set(blanco or [])
    c.t(x, y, f"Red {_NOMBRES_RED[celda.red]}", size=11, peso=700, fuente=d.SANS)
    y += 22
    for i, especie in enumerate(sorted(celda.z)):
        nombre = nombres[i] if i < len(nombres) else especie
        _tq(c, x, y, f"{nombre}:", size=10.5, peso=700)
        if "z" in blancos:
            c.vacio(x + 44, x + 230, y + 2)
        else:
            c.t(x + 44, y, f"{_desglose(celda.sitios, especie)} = {_g(celda.z[especie])}", size=10.5, fuente=d.SANS)
        y += 18
    if dos:
        c.add(f'<circle cx="{x + 4:.1f}" cy="{y - 3:.1f}" r="5" fill="{c.pal["fillHighlight"]}" '
              f'stroke="{c.pal["strokeMain"]}"/>')
        _tq(c, x + 14, y + 1, nombres[0], size=9.5)
        c.add(f'<circle cx="{x + 64:.1f}" cy="{y - 3:.1f}" r="4" fill="{c.pal["strokeSub"]}" '
              f'stroke="{c.pal["strokeMain"]}"/>')
        _tq(c, x + 74, y + 1, nombres[1] if len(nombres) > 1 else "B", size=9.5)
        y += 20
    y += 4
    _rotulo_q(c, x, y, "Número de coordinación", celda.coordinacion, "coordination" in blancos, size=10.5)
    y += 18
    if celda.empaquetamiento is not None:
        _rotulo_q(c, x, y, "Empaquetamiento", f"{_g(100 * celda.empaquetamiento)} %", "packing" in blancos, size=10.5)
        y += 18
    c.t(x, y, celda.relacion, size=10.5, color="textSub", fuente=d.SANS)
    y += 18
    if "a" in b and "molarMass" in b:
        rho = q.densidad(celda, q._num(b["a"], "a (pm)", positivo=True),
                         q._num(b["molarMass"], "molarMass (g/mol)", positivo=True))
        c.t(x, y, f"a = {_g(float(b['a']), 4)} pm; M = {_g(float(b['molarMass']), 4)} g/mol", size=10,
            color="textSub", fuente=d.SANS)
        y += 18
        _rotulo_q(c, x, y, "ρ", f"{_coma(rho)} g/cm³", "density" in blancos, size=10.5)
        y += 18
    return 540, max(oy + 16, y)


RENDERIZADORES: dict[str, Callable[[d._Lienzo, dict], Punto]] = {
    "molecule": _molecula, "reaction": _reaccion, "vsepr": _trepev, "orbitals": _orbitales,
    "energy_profile": _perfil, "titration": _titulacion, "speciation": _especiacion, "kinetics": _cinetica,
    "phase_diagram": _fases, "heating_curve": _calentamiento, "spectrum": _espectro, "galvanic_cell": _pila,
    "unit_cell": _celda,
}
