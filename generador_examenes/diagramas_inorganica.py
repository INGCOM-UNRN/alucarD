"""Diagramas de química inorgánica para los bloques ```` ```estructura ````.

| `type` | Qué dibuja |
| --- | --- |
| `crystal_field` | Desdoblamiento del campo cristalino (octaédrico, tetraédrico, cuadrado plano), con el llenado de alto o bajo espín, la EECC, los electrones desapareados y el momento magnético. |
| `complex` | Un complejo de coordinación en perspectiva: fórmula, estado de oxidación del metal, número de coordinación, electrones d e isómero cis/trans o fac/mer. |
| `latimer` | Diagrama de Latimer: las especies de un elemento con los potenciales entre ellas, el potencial entre dos especies cualesquiera y las que desproporcionan. |
| `frost` | Diagrama de Frost (N·E° en función del estado de oxidación), calculado desde los potenciales de Latimer. |
| `born_haber` | Ciclo de Born-Haber: los niveles de energía desde los elementos a los iones gaseosos y la energía de red por la ley de Hess. |

Las configuraciones, los orbitales moleculares y las celdas unidad están en `diagramas_quimica`
(`orbitals`, `unit_cell`). Las cuentas, en `generador_examenes.quimica`.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from generador_examenes import diagramas as d
from generador_examenes import quimica as q
from generador_examenes.diagramas_control import _Ejes, _g
from generador_examenes.diagramas_quimica import (
    _encabezado_q,
    GEOMETRIAS,
    _caja_vacia,
    _coma,
    _errores,
    _flecha_doble,
    _flechita,
    _rotulo_q,
    _tq,
    ancho_formula,
)

Punto = tuple[float, float]


def _carga_sup(carga: int) -> str:
    if not carga:
        return ""
    return f"^{abs(carga) if abs(carga) > 1 else ''}{'+' if carga > 0 else '-'}"


def _filas(c: d._Lienzo, x: float, y: float, filas: list[tuple[str, str, bool]], ancho: float = 120) -> float:
    for nombre, valor, blanco in filas:
        c.t(x, y, f"{nombre}:", size=10.5, peso=700, fuente=d.SANS)
        x_valor = x + ancho
        if blanco:
            c.vacio(x_valor, x_valor + 110, y + 2)
        else:
            _tq(c, x_valor, y, valor, size=10.5)
        y += 20
    return y


# --- Campo cristalino ------------------------------------------------------------------------------------

_DELTA = {"octahedral": "Δ_o", "tetrahedral": "Δ_t", "square_planar": "Δ"}
_NOMBRE_GEOMETRIA = {"octahedral": "octaédrico", "tetrahedral": "tetraédrico", "square_planar": "cuadrado plano"}


def _electrones_y_espin(b: dict, donde: str) -> tuple[int, bool, str]:
    if "electrons" in b:
        n = int(b["electrons"])
    elif "metal" in b and "oxidation" in b:
        n = q.electrones_d(str(b["metal"]), int(b["oxidation"]))
    else:
        raise d.ErrorDiagrama(f"{donde}: falta electrons (los d) o metal y oxidation")
    geometria = str(b.get("geometry", "octahedral"))
    espin = b.get("spin")
    origen = ""
    if geometria == "tetrahedral" and espin is None:
        espin, origen = "high", "Δt chico: siempre alto espín"
    elif espin is None and "ligand" in b:
        fuerte = q.es_campo_fuerte(str(b["ligand"]))
        espin = "low" if fuerte else "high"
        origen = f"{b['ligand']}: campo {'fuerte' if fuerte else 'débil'}"
    elif espin is None:
        espin = "low" if geometria == "square_planar" else "high"
    if espin not in ("high", "low"):
        raise d.ErrorDiagrama(f"{donde}: spin vale high o low")
    return n, espin == "high", origen


@_errores
def _campo(c: d._Lienzo, b: dict) -> Punto:
    geometria = str(b.get("geometry", "octahedral"))
    n, alto, origen = _electrones_y_espin(b, "crystal_field")
    cc = q.campo_cristalino(geometria, n, alto)
    niveles = q.NIVELES_CAMPO[geometria]
    top = _encabezado_q(c, b)
    lado = 22.0
    x_libre, x_campo = 30.0, 210.0
    y_base = top + 40
    alto_px = 150.0
    energias = [e for _, _, e in niveles]
    lo, hi = min(energias), max(energias)

    def py(e: float) -> float:
        return y_base + alto_px - (e - lo) / (hi - lo) * alto_px

    # Dos niveles muy cercanos (dz² y dxz/dyz en el cuadrado plano) se separan al menos 32 px.
    alturas: list[float] = []
    for e in energias:
        y = py(e)
        if alturas and alturas[-1] - y < 32:
            y = alturas[-1] - 32
        alturas.append(y)
    y_de = dict(zip(energias, alturas))
    y_cero = py(0)
    trazo = c.pal["strokeMain"]
    # El ion libre: cinco orbitales degenerados en la energía promedio.
    for k in range(5):
        c.add(f'<rect x="{x_libre + k * lado:.1f}" y="{y_cero - lado / 2:.1f}" width="{lado}" height="{lado}" '
              f'fill="{c.pal["fillCell"]}" stroke="{trazo}" stroke-width="1.2"/>')
    c.t(x_libre + 2.5 * lado, y_cero + lado / 2 + 14, "ion libre", size=9.5, color="textSub", ancla="middle",
        fuente=d.SANS)
    vacio = bool(b.get("blankElectrons"))
    for (nombre, orbitales, energia), llenado in zip(niveles, cc.llenado):
        y = y_de[energia]
        ancho = len(orbitales) * lado
        x0 = x_campo + (3 * lado - ancho) / 2
        for j, e in enumerate(llenado):
            bx = x0 + j * lado
            c.add(f'<rect x="{bx:.1f}" y="{y - lado / 2:.1f}" width="{lado}" height="{lado}" '
                  f'fill="{c.pal["fillCell"]}" stroke="{trazo}" stroke-width="1.2"/>')
            if vacio:
                continue
            if e >= 1:
                _flechita(c, bx + (lado / 2 - 4 if e == 2 else lado / 2), y, True)
            if e == 2:
                _flechita(c, bx + lado / 2 + 4, y, False)
        c.linea(x_libre + 5 * lado + 4, y_cero, x0 - 4, y, color="strokeMuted", ancho=0.8, flecha=None, guiones="3 3")
        etiqueta = nombre if nombre else ", ".join(orbitales)
        _tq(c, x_campo + 3 * lado + 10, y + 4, etiqueta.replace("t2g", "t_2g").replace("t2", "t_2").replace(
            "eg", "e_g"), size=10.5, peso=600)
    if geometria != "square_planar":
        x_d = x_campo - 22
        _flecha_doble(c, x_d, y_de[energias[0]] - 2, y_de[energias[-1]] + 2)
        _tq(c, x_d - 6, (y_de[energias[0]] + y_de[energias[-1]]) / 2 + 4, _DELTA[geometria], size=11, peso=700,
            ancla="end")
    blanco = bool(b.get("blank"))
    y = y_base + alto_px + 40
    if b.get("complex"):
        _tq(c, 0, top + 14, str(b["complex"]), size=12, peso=700)
    reparto = " ".join(f"{(nombre or orbitales[0]).replace('t2g', 't_2g').replace('t2', 't_2').replace('eg', 'e_g')}"
                       f"^{sum(llenado)}" for (nombre, orbitales, _), llenado in zip(niveles, cc.llenado))
    filas = [("Configuración", f"d^{n}: {reparto}" if geometria != "square_planar" else f"d^{n}",
              blanco or bool(b.get("blankConfig"))),
             ("Espín", ("alto" if alto else "bajo") + (f" ({origen})" if origen else ""),
              blanco or bool(b.get("blankSpin"))),
             ("Desapareados", str(cc.desapareados), blanco or bool(b.get("blankUnpaired"))),
             ("μ (solo espín)", f"{_coma(cc.momento)} μB", blanco or bool(b.get("blankMoment")))]
    if geometria != "square_planar":
        eecc = 0.0 if abs(cc.eecc) < 1e-9 else cc.eecc
        filas.append(("EECC", f"{_coma(eecc, 1).replace('-', '−')} {_DELTA[geometria]}",
                      blanco or bool(b.get("blankCFSE"))))
    y = _filas(c, 0, y, filas)
    return 430, y


# --- Complejos ------------------------------------------------------------------------------------------

_SITIOS = {
    "octahedral": [(90, "p"), (270, "p"), (180, "p"), (0, "p"), (225, "w"), (45, "h")],
    "square_planar": [(180, "p"), (0, "p"), (225, "w"), (45, "h")],
    "tetrahedral": GEOMETRIAS["tetrahedral"][4],
}


def _formula_complejo(metal: str, ligandos: list[str], carga: int) -> str:
    orden: list[str] = []
    for lig in ligandos:
        if lig not in orden:
            orden.append(lig)
    partes = []
    for lig in orden:
        limpio = lig.split("^")[0]
        n = ligandos.count(lig)
        compuesto = sum(1 for ch in limpio if ch.isupper()) > 1 or any(ch.isdigit() for ch in limpio) or len(limpio) > 2
        texto = f"({limpio})" if compuesto and n > 1 else limpio
        partes.append(texto + (str(n) if n > 1 else ""))
    return f"[{metal}{''.join(partes)}]{_carga_sup(carga)}"


@_errores
def _complejo(c: d._Lienzo, b: dict) -> Punto:
    geometria = str(b.get("geometry", "octahedral"))
    if geometria not in _SITIOS:
        raise d.ErrorDiagrama("complex: geometry vale octahedral, square_planar o tetrahedral")
    metal = str(b.get("metal", "M"))
    ligandos = [str(x) for x in (b.get("ligands") or [])]
    sitios = _SITIOS[geometria]
    if len(ligandos) != len(sitios):
        raise d.ErrorDiagrama(f"complex: la geometría {geometria} tiene {len(sitios)} sitios (hay {len(ligandos)} "
                              "ligandos); el orden es arriba, abajo, izquierda, derecha, adelante, atrás")
    carga = int(b.get("charge", 0))
    top = _encabezado_q(c, b)
    cx, cy, largo = 120.0, top + 96, 60.0
    trazo = c.pal["strokeMain"]
    for (ang_g, tipo), etiqueta in zip(sitios, ligandos):
        ang = math.radians(ang_g)
        f = 0.8 if tipo != "p" else 1.0
        ux, uy = math.cos(ang), -math.sin(ang)
        ax, ay = cx + ux * 13, cy + uy * 13
        bx, by = cx + ux * (largo * f - 12), cy + uy * (largo * f - 12)
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
        _tq(c, cx + ux * largo * f, cy + uy * largo * f + 4, etiqueta.split("^")[0], size=11, peso=500,
            ancla="middle")
    _tq(c, cx, cy + 5, metal, size=13, peso=700, ancla="middle")
    blanco = b.get("blank")
    blancos = {"formula", "oxidation", "coordination", "d", "isomer"} if blanco is True else set(blanco or [])
    oxidacion = int(b["oxidation"]) if "oxidation" in b else q.oxidacion_metal(carga, ligandos)
    filas = [("Fórmula", _formula_complejo(metal, ligandos, carga), "formula" in blancos),
             ("Estado de oxidación", f"{metal}({_romano(oxidacion)})", "oxidation" in blancos),
             ("N.º de coordinación", str(len(ligandos)), "coordination" in blancos)]
    try:
        filas.append(("Electrones d", f"d^{q.electrones_d(metal, oxidacion)}", "d" in blancos))
    except q.ErrorQuimica:
        pass
    isom = q.isomero(geometria, ligandos)
    if isom:
        filas.append(("Isómero", isom, "isomer" in blancos))
    y = _filas(c, 250, top + 46, filas, ancho=150)
    return 560, max(top + 190, y)


def _romano(n: int) -> str:
    if n <= 0:
        return str(n)
    valores = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    salida = ""
    for v, s in valores:
        while n >= v:
            salida += s
            n -= v
    return salida


# --- Latimer y Frost ------------------------------------------------------------------------------------

@_errores
def _latimer(c: d._Lienzo, b: dict) -> Punto:
    lt = q.latimer(b)
    top = _encabezado_q(c, b) + 28
    x, y = 0.0, top + 20
    posiciones = []
    ocultos = set(b.get("blankPotentials") or [])
    for i, especie in enumerate(lt.especies):
        ancho = ancho_formula(especie, 12)
        _tq(c, x, y, especie, size=12, peso=600)
        c.t(x + ancho / 2, y - 18, _romano_signo(lt.oxidacion[i]), size=9, color="textMuted", ancla="middle",
            fuente=d.SANS)
        posiciones.append((x, x + ancho))
        x += ancho
        if i < len(lt.potenciales):
            largo = 66.0
            c.linea(x + 6, y - 4, x + largo - 6, y - 4, color="accentPrimary", ancho=1.5)
            if i in ocultos:
                _caja_vacia(c, x + largo / 2, y - 18, 40, 13)
            else:
                c.t(x + largo / 2, y - 12, f"{_coma(lt.potenciales[i])}", size=9.5, peso=700, ancla="middle",
                    fuente=d.SANS)
            x += largo
    ancho_total = x
    y_arco = y + 12
    blanco_calc = bool(b.get("blankComputed"))
    pedidos = b.get("compute") or []
    rotulos = []
    for k, par in enumerate(pedidos):
        i, j = int(par[0]), int(par[1])
        if not (0 <= i < len(lt.especies) and 0 <= j < len(lt.especies)) or i == j:
            raise d.ErrorDiagrama(f"latimer: compute[{k}] son dos índices distintos de species")
        i, j = min(i, j), max(i, j)
        xa = (posiciones[i][0] + posiciones[i][1]) / 2
        xb = (posiciones[j][0] + posiciones[j][1]) / 2
        hondo = 22 + 30 * k
        c.add(f'<path d="M {xa:.1f} {y_arco:.1f} Q {(xa + xb) / 2:.1f} {y_arco + 2 * hondo:.1f} {xb:.1f} {y_arco:.1f}" '
              f'fill="none" stroke="{c.pal["strokeSub"]}" stroke-width="1.1" marker-end="url(#flecha-sub-{c.sufijo})"/>')
        rotulos.append(((xa + xb) / 2, y_arco + hondo + 13, lt.potencial(i, j)))
    # Los rótulos después de todos los arcos, para que ninguna curva les pase por encima.
    for x_r, y_r, e in rotulos:
        _rotulo_q(c, x_r, y_r, "E°", f"{_coma(e, 2)} V", blanco_calc, ancla="middle", size=9.5)
    y_fin = y_arco + 22 + 30 * len(pedidos) + 10 if pedidos else y + 20
    if b.get("showDisproportionation"):
        des = lt.desproporcionan()
        texto = ", ".join(lt.especies[k] for k in des) if des else "ninguna"
        _rotulo_q(c, 0, y_fin + 14, "Desproporcionan", texto, bool(b.get("blankDisproportionation")), size=10)
        y_fin += 26
    return ancho_total + 10, y_fin


def _romano_signo(n: float) -> str:
    entero = int(round(n))
    if abs(n - entero) > 1e-9:
        return _g(n)
    return f"{'+' if entero > 0 else ''}{entero}"


@_errores
def _frost(c: d._Lienzo, b: dict) -> Punto:
    lt = q.latimer(b)
    puntos = list(zip(lt.oxidacion, lt.frost()))
    top = _encabezado_q(c, b)
    x0, y0, w, h = 60.0, top + 18, 440.0, 250.0
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    margen = (max(ys) - min(ys)) * 0.12 or 1
    ejes = _Ejes(c, x0, y0, w, h, (min(xs) - 0.5, max(xs) + 0.5), (min(ys) - margen, max(ys) + margen),
                 "estado de oxidación", "N·E° (V)", origen=True)
    orden = sorted(puntos)
    ejes.curva(orden, ancho=1.8)
    des = set(lt.desproporcionan()) if b.get("showDisproportionation") else set()
    blanco = bool(b.get("blankLabels"))
    for k, (ox, ne) in enumerate(puntos):
        x, y = ejes.px(ox), ejes.py(ne)
        relleno = c.pal["fillCell"] if k in des else c.pal["strokeMain"]
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{relleno}" stroke="{c.pal["strokeMain"]}" '
              'stroke-width="1.5"/>')
        if blanco:
            _caja_vacia(c, x, y - 15, 44, 13)
        else:
            _tq(c, x, y - 10, lt.especies[k], size=10, peso=600, ancla="middle", fondo=True)
    if des:
        for k in sorted(des):
            (oa, na), (ob, nb) = puntos[k - 1], puntos[k + 1]
            ejes.guia(oa, na, ob, nb, guiones="3 3")
        c.t(x0 + 8, y0 + 16, "○ desproporciona (queda por encima de la recta entre sus vecinas)", size=9,
            color="textSub", fuente=d.SANS)
    return x0 + w + 10, y0 + h + 40


# --- Born-Haber -----------------------------------------------------------------------------------------

@_errores
def _born_haber(c: d._Lienzo, b: dict) -> Punto:
    bh = q.born_haber(b)
    etiquetas = [str(p.get("label", "")) for p in b["steps"]]
    ocultos = {i for i, p in enumerate(b["steps"]) if isinstance(p, dict) and p.get("blank")}
    top = _encabezado_q(c, b)
    niveles = [0.0]
    for _, dh in bh.pasos:
        niveles.append(niveles[-1] + dh)
    todos = niveles + [bh.formacion]
    lo, hi = min(todos), max(todos)
    y0, alto = top + 20, 340.0

    def py(e: float) -> float:
        return y0 + alto - (e - lo) / (hi - lo) * alto

    x_inicio = 40.0
    paso_x = 112.0
    trazo = c.pal["strokeMain"]

    def nivel(x1: float, x2: float, e: float, texto: str, al_final: bool = False) -> None:
        c.linea(x1, py(e), x2, py(e), color="strokeMain", ancho=1.6, flecha=None)
        if al_final:
            _tq(c, x2 + 4, py(e) + 4, texto, size=10)
        else:
            _tq(c, x1 + 2, py(e) - 5, texto, size=9.5, fondo=True)

    nivel(x_inicio - 20, x_inicio + 60, 0, bh.inicio)
    for k, ((estado, dh), etiqueta) in enumerate(zip(bh.pasos, etiquetas)):
        x = x_inicio + 60 + paso_x * k
        e0, e1 = niveles[k], niveles[k + 1]
        c.add(f'<line x1="{x:.1f}" y1="{py(e0):.1f}" x2="{x:.1f}" y2="{py(e1):.1f}" stroke="{c.pal["accentPrimary"]}" '
              f'stroke-width="1.5" marker-end="url(#flecha-main-{c.sufijo})"/>')
        nivel(x - 14, x + paso_x, e1, estado)          # hasta la flecha siguiente
        texto = f"{etiqueta} " if etiqueta else ""
        y_texto = (py(e0) + py(e1)) / 2 + 4
        if k in ocultos:
            _tq(c, x + 5, y_texto, texto + "=", size=9, peso=700, fondo=True)
            c.vacio(x + 6 + ancho_formula(texto + "=", 9), x + 50 + ancho_formula(texto, 9), y_texto + 2)
        else:
            _tq(c, x + 5, y_texto, f"{texto}{'+' if dh > 0 else ''}{_g(dh, 4)}", size=9, peso=700, fondo=True)
    x_red = x_inicio + 60 + paso_x * len(bh.pasos)
    e_iones = niveles[-1]
    c.add(f'<line x1="{x_red:.1f}" y1="{py(e_iones):.1f}" x2="{x_red:.1f}" y2="{py(bh.formacion):.1f}" '
          f'stroke="{c.pal["accentPrimary"]}" stroke-width="2" marker-end="url(#flecha-main-{c.sufijo})"/>')
    nivel(x_inicio - 20, x_red + 20, bh.formacion, bh.producto, al_final=True)
    _rotulo_q(c, x_red + 6, (py(e_iones) + py(bh.formacion)) / 2, "U_red", f"{_g(bh.energia_red, 4)} kJ/mol",
              bool(b.get("blankLattice")), size=10)
    c.add(f'<line x1="{x_inicio:.1f}" y1="{py(0):.1f}" x2="{x_inicio:.1f}" y2="{py(bh.formacion):.1f}" '
          f'stroke="{trazo}" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#flecha-main-{c.sufijo})"/>')
    _tq(c, x_inicio + 4, (py(0) + py(bh.formacion)) / 2, f"ΔH_f = {_g(bh.formacion, 4)}", size=9, peso=700,
        fondo=True)
    c.t(0, y0 + alto + 24, "Energías en kJ/mol.", size=9, color="textSub", fuente=d.SANS)
    return x_red + 150, y0 + alto + 30


RENDERIZADORES: dict[str, Callable[[d._Lienzo, dict], Punto]] = {
    "crystal_field": _campo, "complex": _complejo, "latimer": _latimer, "frost": _frost, "born_haber": _born_haber,
}
