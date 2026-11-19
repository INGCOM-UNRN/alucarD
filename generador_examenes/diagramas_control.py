"""Diagramas de control de procesos para los bloques ```` ```estructura ````.

| `type` | Qué dibuja |
| --- | --- |
| `block_diagram` | Diagrama de bloques: cadena directa, realimentación, perturbación y lazos en cascada. |
| `time_response` | Respuesta temporal (escalón, rampa, impulso) de uno o varios sistemas, de lazo abierto o cerrado (con PID y tiempo muerto), con sus características: valor final, sobrepico, tiempos de pico, subida y establecimiento, τ, θ y la tangente de la curva de reacción. |
| `bode` | Diagrama de Bode (magnitud y fase), con asíntotas y márgenes de ganancia y de fase. |
| `nyquist` | Diagrama de Nyquist, con el punto −1 y el círculo unitario. |
| `pole_zero` | Mapa de polos y ceros en el plano s, con rectas de ζ y círculos de ωn constantes. |
| `root_locus` | Lugar de las raíces, con asíntotas, cruce del eje imaginario y ganancias marcadas. |
| `instrumentation` | Diagrama P&ID con símbolos ISA-5.1: equipos, válvulas, instrumentos y líneas de señal. |
| `ladder` | Diagrama escalera (PLC): contactos, bobinas, temporizadores y contadores, en serie y en paralelo. |
| `grafcet` | GRAFCET: etapas, transiciones, acciones y divergencias en O y en Y. |

Las cuentas están en `generador_examenes.control`. Cada tipo acepta claves `blank*` para dejar
casilleros en blanco en un ejercicio para completar.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from typing import Any

from generador_examenes import control
from generador_examenes import diagramas as d

Punto = tuple[float, float]
_GUIONES = ("", "7 3", "2 3", "9 3 2 3", "4 2")


def _g(x: float | None, cifras: int = 3) -> str:
    """Un número corto, con coma decimal."""
    if x is None:
        return "—"
    if x == 0:
        return "0"
    if 1e3 <= abs(x) < 1e6 and abs(x - round(x)) < 1e-6 * abs(x) + 1e-9:
        return str(round(x))                     # 4000 cm⁻¹, no 4e+03
    texto = f"{x:.{cifras}g}"
    if "e" in texto:
        texto = f"{x:.2e}"
    return texto.replace(".", ",")


def _errores(funcion: Callable) -> Callable:
    """Un error de las cuentas es un bloque inválido, con su mensaje."""
    def envuelta(c, b):
        try:
            return funcion(c, b)
        except control.ErrorControl as e:
            raise d.ErrorDiagrama(f"{b.get('type')}: {e}") from e
    return envuelta


# --- Ejes ---------------------------------------------------------------------------------------------

def _paso_lindo(rango: float, marcas: int = 5) -> float:
    if rango <= 0:
        return 1.0
    bruto = rango / marcas
    base = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * base:
            return m * base
    return 10 * base


def _marcas(lo: float, hi: float, marcas: int = 5, paso: float | None = None) -> list[float]:
    paso = paso or _paso_lindo(hi - lo, marcas)
    inicio = math.ceil(lo / paso - 1e-9) * paso
    salida, v = [], inicio
    while v <= hi + paso * 1e-6:
        salida.append(round(v, 12))
        v += paso
    return salida


class _Ejes:
    """Un gráfico x-y: escalas, marcas, grilla y rótulos. `log` hace logarítmico el eje x."""

    def __init__(self, c: d._Lienzo, x0: float, y0: float, w: float, h: float, xr: Punto, yr: Punto,
                 xlabel: str = "", ylabel: str = "", log: bool = False, grilla: bool = True, origen: bool = False,
                 ypaso: float | None = None):
        self.c, self.x0, self.y0, self.w, self.h = c, x0, y0, w, h
        self.xr, self.yr, self.log = xr, yr, log
        pal = c.pal
        c.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" '
              f'stroke="{pal["strokeMain"]}" stroke-width="1.2"/>')
        if log:
            dec0, dec1 = math.floor(math.log10(xr[0]) + 1e-9), math.ceil(math.log10(xr[1]) - 1e-9)
            for e in range(dec0, dec1 + 1):
                for m in range(1, 10):
                    v = m * 10 ** e
                    if not xr[0] * 0.999 <= v <= xr[1] * 1.001:
                        continue
                    x = self.px(v)
                    if grilla:
                        c.linea(x, y0, x, y0 + h, color="strokeMuted", ancho=0.6 if m == 1 else 0.3, flecha=None,
                                guiones="" if m == 1 else "1 3")
                    if m == 1:
                        c.t(x, y0 + h + 14, f"10^{e}" if abs(e) > 3 else _g(v), size=9, color="textSub", ancla="middle")
        else:
            for v in _marcas(*sorted(xr)):       # un eje invertido (de 4000 a 400) también tiene marcas
                x = self.px(v)
                if grilla:
                    c.linea(x, y0, x, y0 + h, color="strokeMuted", ancho=0.4, flecha=None, guiones="2 4")
                c.t(x, y0 + h + 14, _g(v), size=9, color="textSub", ancla="middle")
        for v in _marcas(*yr, paso=ypaso):
            y = self.py(v)
            if grilla:
                c.linea(x0, y, x0 + w, y, color="strokeMuted", ancho=0.4, flecha=None, guiones="2 4")
            c.t(x0 - 6, y + 3, _g(v), size=9, color="textSub", ancla="end")
        if origen:
            if yr[0] < 0 < yr[1]:
                c.linea(x0, self.py(0), x0 + w, self.py(0), color="strokeSub", ancho=1, flecha=None)
            if not log and xr[0] < 0 < xr[1]:
                c.linea(self.px(0), y0, self.px(0), y0 + h, color="strokeSub", ancho=1, flecha=None)
        if xlabel:
            c.t(x0 + w / 2, y0 + h + 30, xlabel, size=10, peso=600, ancla="middle", fuente=d.SANS)
        if ylabel:
            c.add(f'<text x="{x0 - 38:.1f}" y="{y0 + h / 2:.1f}" text-anchor="middle" font-family="{d.SANS}" '
                  f'font-size="10" font-weight="600" fill="{c.pal["textMain"]}" '
                  f'transform="rotate(-90 {x0 - 38:.1f} {y0 + h / 2:.1f})">{d._esc(ylabel)}</text>')

    def px(self, v: float) -> float:
        if self.log:
            a, b = math.log10(self.xr[0]), math.log10(self.xr[1])
            return self.x0 + (math.log10(max(v, 1e-300)) - a) / (b - a) * self.w
        return self.x0 + (v - self.xr[0]) / (self.xr[1] - self.xr[0]) * self.w

    def py(self, v: float) -> float:
        return self.y0 + self.h - (v - self.yr[0]) / (self.yr[1] - self.yr[0]) * self.h

    def adentro(self, x: float, y: float) -> bool:
        return self.x0 - 0.5 <= x <= self.x0 + self.w + 0.5 and self.y0 - 0.5 <= y <= self.y0 + self.h + 0.5

    def _recortar(self, a: Punto, b: Punto) -> tuple[Punto, Punto] | None:
        """El segmento a-b (en px) recortado al gráfico (Liang-Barsky), o None si queda afuera."""
        x0, y0, x1, y1 = self.x0, self.y0, self.x0 + self.w, self.y0 + self.h
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
                continue
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return None
        return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)

    def curva(self, puntos: list[Punto], estilo: int = 0, ancho: float = 1.8, color: str = "strokeMain") -> None:
        """La curva, recortada en el borde del gráfico."""
        tramos: list[list[Punto]] = []
        previo: Punto | None = None
        for x, y in puntos:
            if not (math.isfinite(x) and math.isfinite(y)):
                previo = None
                continue
            actual = (self.px(x), self.py(y))
            if previo is not None and math.isfinite(actual[1]) and math.isfinite(actual[0]):
                segmento = self._recortar(previo, actual)
                if segmento:
                    inicio, fin = segmento
                    if tramos and tramos[-1] and math.dist(tramos[-1][-1], inicio) < 0.01:
                        tramos[-1].append(fin)
                    else:
                        tramos.append([inicio, fin])
            previo = actual
        guiones = _GUIONES[estilo % len(_GUIONES)]
        for tramo in tramos:
            camino = " ".join(f"{x:.1f},{y:.1f}" for x, y in tramo)
            self.c.add(f'<polyline points="{camino}" fill="none" stroke="{self.c.pal[color]}" stroke-width="{ancho}" '
                       'stroke-linejoin="round"' + (f' stroke-dasharray="{guiones}"' if guiones else "") + "/>")

    def guia(self, x1: float, y1: float, x2: float, y2: float, guiones: str = "4 3", color: str = "strokeSub") -> None:
        self.c.linea(self.px(x1), self.py(y1), self.px(x2), self.py(y2), color=color, ancho=1, flecha=None,
                     guiones=guiones)


def _rotulo(c: d._Lienzo, x: float, y: float, nombre: str, valor: str | None, blanco: bool, ancla: str = "start",
            size: float = 10) -> float:
    """`nombre = valor`, o `nombre = ____` para completar; devuelve el ancho."""
    if blanco:
        texto = f"{nombre} ="
        ancho = d._ancho_texto(texto, size) + 44
        x0 = x if ancla == "start" else (x - ancho / 2 if ancla == "middle" else x - ancho)
        c.t(x0, y, texto, size=size, peso=700)
        c.vacio(x0 + d._ancho_texto(texto, size) + 4, x0 + ancho, y + 2)
        return ancho
    texto = f"{nombre} = {valor}"
    c.t(x, y, texto, size=size, peso=700, ancla=ancla)
    return d._ancho_texto(texto, size)


def _leyenda(c: d._Lienzo, x: float, y: float, etiquetas: list[str]) -> float:
    """Las etiquetas de las curvas con su estilo de trazo; devuelve el alto."""
    for i, etiqueta in enumerate(etiquetas):
        guiones = _GUIONES[i % len(_GUIONES)]
        c.add(f'<line x1="{x:.1f}" y1="{y + i * 16:.1f}" x2="{x + 26:.1f}" y2="{y + i * 16:.1f}" '
              f'stroke="{c.pal["strokeMain"]}" stroke-width="1.8"' + (f' stroke-dasharray="{guiones}"' if guiones else "") + "/>")
        c.t(x + 32, y + i * 16 + 4, etiqueta, size=10)
    return len(etiquetas) * 16


# --- Respuesta temporal --------------------------------------------------------------------------------------

def _sistemas_de(b: dict, clave: str = "systems") -> list[tuple[str, Any]]:
    """Los sistemas del bloque: (etiqueta, Sistema o Lazo)."""
    salida = []
    if "closedLoop" in b:
        lz = control.lazo(b["closedLoop"])
        salida.append((lz.etiqueta, lz))
    if "system" in b:
        s = control.sistema(b["system"])
        salida.append((s.etiqueta, s))
    lista = b.get(clave) or []
    if not isinstance(lista, list):
        raise d.ErrorDiagrama(f"'{clave}' tiene que ser una lista de sistemas")
    for i, dato in enumerate(lista):
        if isinstance(dato, dict) and "closedLoop" in dato:
            lz = control.lazo(dato["closedLoop"], f"{clave}[{i}].closedLoop")
            salida.append((str(dato.get("label") or lz.etiqueta), lz))
        else:
            s = control.sistema(dato, f"{clave}[{i}]")
            salida.append((s.etiqueta, s))
    return salida


def _tiempo_final(sistemas: list[Any]) -> float:
    lentos = []
    for s in sistemas:
        base = s.cerrado() if isinstance(s, control.Lazo) else s
        retardo = s.planta.delay if isinstance(s, control.Lazo) else s.delay
        estables = [p for p in base.polos if p.real < -1e-9]
        lentos.append((6 / min(-p.real for p in estables) if estables else 10.0) + 2 * retardo)
    return min(max(lentos or [10.0]), 1e4)


_ANOTACIONES = ("final", "overshoot", "peak", "rise", "settling", "tau", "delay", "tangent")


@_errores
def _respuesta(c: d._Lienzo, b: dict) -> Punto:
    tipo = str(b.get("input", "step"))
    amplitud = float(b.get("amplitude", 1.0))
    sistemas = _sistemas_de(b)
    datos = b.get("data")
    if not sistemas and not datos:
        raise d.ErrorDiagrama("time_response: falta system, systems, closedLoop o data (puntos medidos)")
    t_fin = float(b.get("tEnd") or (_tiempo_final([s for _, s in sistemas]) if sistemas else 0) or 10)
    perturbacion = b.get("disturbance")
    curvas: list[tuple[str, list[float], list[float]]] = []
    referencia: tuple[list[float], list[float]] | None = None
    finales: list[float | None] = []
    for etiqueta, s in sistemas:
        if isinstance(s, control.Lazo):
            ts, rs, ys, _ = control.simular_lazo(s, t_fin, tipo, amplitud, perturbacion)
            referencia = referencia or (ts, rs)
            cerrado = s.cerrado()
            estable = s.planta.delay == 0 and all(p.real < -1e-9 for p in cerrado.polos)
            k = cerrado.ganancia_estatica
            finales.append(amplitud * k if (tipo == "step" and estable and k is not None and not perturbacion) else None)
        else:
            ts, us, ys = control.simular_abierto(s, t_fin, tipo, amplitud)
            referencia = referencia or (ts, us)
            estable = all(p.real < -1e-9 for p in s.polos)
            k = s.ganancia_estatica
            finales.append(amplitud * k if (tipo == "step" and estable and k is not None) else None)
        curvas.append((etiqueta, ts, ys))
    if datos:
        try:
            puntos = sorted((float(p[0]), float(p[1])) for p in datos)
        except (TypeError, ValueError, IndexError):
            raise d.ErrorDiagrama("time_response: 'data' es una lista de [t, y]") from None
        curvas.append((str(b.get("dataLabel") or "medición"), [p[0] for p in puntos], [p[1] for p in puntos]))
        finales.append(None)
        t_fin = max(t_fin if sistemas else 0, puntos[-1][0])

    top = d._encabezado(c, b)
    x0, y0, w, h = 58, top + 16, 460, 250
    todos = [y for _, _, ys in curvas for y in ys]
    if b.get("showInput", True) and referencia and tipo != "impulse":
        todos += referencia[1]
    y_min, y_max = min(0.0, min(todos)), max(todos)
    if "yMax" in b:
        y_max = float(b["yMax"])
    if "yMin" in b:
        y_min = float(b["yMin"])
    margen = (y_max - y_min) * 0.12 or 1
    ejes = _Ejes(c, x0, y0, w, h, (0.0, t_fin), (y_min, y_max + margen), str(b.get("xLabel") or "t (s)"),
                 str(b.get("yLabel") or "y(t)"), origen=True)
    if b.get("showInput", True) and referencia and tipo != "impulse":
        ejes.curva(list(zip(*referencia, strict=True)), estilo=2, ancho=1.2, color="strokeSub")
    for i, (_, ts, ys) in enumerate(curvas):
        ejes.curva(list(zip(ts, ys, strict=True)), estilo=i)

    pedidas = b.get("annotations") or []
    if pedidas == "all":
        pedidas = list(_ANOTACIONES)
    desconocidas = [a for a in pedidas if a not in _ANOTACIONES]
    if desconocidas:
        raise d.ErrorDiagrama(f"time_response: anotaciones desconocidas {desconocidas} (valen {', '.join(_ANOTACIONES)})")
    blanco = bool(b.get("blankAnnotations"))
    rotulos: list[tuple[str, str | None]] = []
    if pedidas and curvas:
        _, ts, ys = curvas[0]
        if isinstance(perturbacion, dict) and "at" in perturbacion:
            # Las características son de la respuesta a la referencia: hasta que entra la perturbación.
            corte = next((i for i, t in enumerate(ts) if t >= float(perturbacion["at"])), len(ts))
            ts, ys = ts[:corte], ys[:corte]
        banda = float(b.get("settlingBand", 0.02))
        car = control.caracteristicas(ts, ys, finales[0], banda)
        fin = car["final"]
        if "final" in pedidas and fin is not None:
            ejes.guia(0, fin, t_fin, fin)
            rotulos.append(("y∞", _g(fin)))
        if ("overshoot" in pedidas or "peak" in pedidas) and car["peak"] is not None:
            pico = max(ys) if fin >= 0 else min(ys)
            ejes.guia(car["peak"], y_min, car["peak"], pico)
            c.punto(ejes.px(car["peak"]), ejes.py(pico), radio=3)
            if "overshoot" in pedidas:
                rotulos.append(("Mp", f"{_g(car['overshoot'])} %"))
            if "peak" in pedidas:
                rotulos.append(("tp", _g(car["peak"])))
                c.t(ejes.px(car["peak"]), y0 + h - 4, "tp", size=9, peso=700, ancla="middle")
        if "rise" in pedidas and car["rise"] is not None:
            for frac in (0.1, 0.9):
                nivel = frac * fin
                cruce = next((t for t, y in zip(ts, ys, strict=True) if (y - nivel) * (1 if fin > 0 else -1) >= 0), None)
                if cruce is not None:
                    ejes.guia(0, nivel, cruce, nivel, guiones="1 3")
                    ejes.guia(cruce, y_min, cruce, nivel, guiones="1 3")
            rotulos.append(("tr", _g(car["rise"])))
        if "settling" in pedidas and car["settling"] is not None:
            for signo in (1, -1):
                ejes.guia(0, fin * (1 + signo * banda), t_fin, fin * (1 + signo * banda), guiones="1 2", color="strokeMuted")
            ejes.guia(car["settling"], y_min, car["settling"], fin)
            c.t(ejes.px(car["settling"]), y0 + h - 4, "ts", size=9, peso=700, ancla="middle")
            rotulos.append((f"ts ({_g(banda * 100)} %)", _g(car["settling"])))
        if "delay" in pedidas and car["delay"] is not None:
            ejes.guia(car["delay"], y_min, car["delay"], fin * 0.3)
            c.t(ejes.px(car["delay"]), y0 + h - 4, "θ", size=10, peso=700, ancla="middle")
            rotulos.append(("θ", _g(car["delay"])))
        if "tau" in pedidas and car["tau"] is not None and car["delay"] is not None:
            t63 = car["delay"] + car["tau"]
            ejes.guia(0, 0.632 * fin, t63, 0.632 * fin)
            ejes.guia(t63, y_min, t63, 0.632 * fin)
            c.punto(ejes.px(t63), ejes.py(0.632 * fin), radio=3)
            c.t(x0 + 4, ejes.py(0.632 * fin) - 4, "63,2 %", size=9, color="textSub")
            rotulos.append(("τ", _g(car["tau"])))
        if "tangent" in pedidas and fin is not None:
            tg = control.tangente_inflexion(ts, ys, fin)
            if tg:
                fin_t = tg["L"] + tg["T"]
                ejes.curva([(tg["L"], 0.0), (fin_t, fin)], estilo=1, ancho=1.2, color="strokeSub")
                ejes.guia(fin_t, y_min, fin_t, fin)
                c.t(ejes.px(tg["L"]), y0 + h - 4, "L", size=10, peso=700, ancla="middle")
                c.t(ejes.px(fin_t), y0 + h - 4, "L+T", size=9, peso=700, ancla="middle")
                rotulos += [("L", _g(tg["L"])), ("T", _g(tg["T"]))]
    ancho = x0 + w
    xr = x0 + w + 14
    yy = y0 + 10
    etiquetas = [e for e, _, _ in curvas if e]
    if etiquetas:
        yy += _leyenda(c, xr, yy, etiquetas) + 8
        ancho = max(ancho, xr + 32 + max(d._ancho_texto(e, 10) for e in etiquetas))
    for nombre, valor in rotulos:
        ancho = max(ancho, xr + _rotulo(c, xr, yy, nombre, valor, blanco))
        yy += 17
    return ancho + 6, max(y0 + h + 40, yy)


# --- Bode -----------------------------------------------------------------------------------------------

@_errores
def _bode(c: d._Lienzo, b: dict) -> Punto:
    sistemas = [(e, s.abierto if isinstance(s, control.Lazo) else s) for e, s in _sistemas_de(b)]
    if not sistemas:
        raise d.ErrorDiagrama("bode: falta system, systems o closedLoop")
    rangos = [control.rango_frecuencias(s) for _, s in sistemas]
    w_min = float(b.get("wMin") or min(r[0] for r in rangos))
    w_max = float(b.get("wMax") or max(r[1] for r in rangos))
    if not 0 < w_min < w_max:
        raise d.ErrorDiagrama("bode: wMin y wMax son positivas y wMin < wMax")
    ws = [w_min * (w_max / w_min) ** (k / 400) for k in range(401)]
    mostrar = b.get("show", "both")
    if mostrar not in ("both", "magnitude", "phase"):
        raise d.ErrorDiagrama("bode: show es both, magnitude o phase")
    top = d._encabezado(c, b)
    x0, w, h = 64, 460, 170
    y = top + 14
    blanco = bool(b.get("blankMargins"))
    mg = control.margenes(sistemas[0][1], w_min, w_max) if b.get("margins") else None
    ejes_mag = ejes_fase = None
    if mostrar in ("both", "magnitude"):
        mags = [[control.magnitud_db(s, x) for x in ws] for _, s in sistemas]
        lo, hi = min(min(m) for m in mags), max(max(m) for m in mags)
        lo, hi = math.floor(min(lo, -20) / 20) * 20, math.ceil(max(hi, 0) / 20) * 20 + (20 if hi % 20 == 0 else 0)
        lo = max(lo, hi - 200)
        ejes_mag = _Ejes(c, x0, y, w, h, (w_min, w_max), (lo, hi), "" if mostrar == "both" else "ω (rad/s)",
                         "|G(jω)| (dB)", log=True, ypaso=20 if hi - lo <= 120 else 40)
        ejes_mag.guia(w_min, 0, w_max, 0, guiones="", color="strokeSub")
        for i, (_, s) in enumerate(sistemas):
            ejes_mag.curva(list(zip(ws, mags[i], strict=True)), estilo=i)
            if b.get("asymptotes"):
                ejes_mag.curva([(x, control.asintota_db(s, x)) for x in ws], estilo=1, ancho=1.1, color="strokeSub")
        y += h + (26 if mostrar == "both" else 44)
    if mostrar in ("both", "phase"):
        fases = [[control.fase_continua(s, x) for x in ws] for _, s in sistemas]
        lo, hi = min(min(f) for f in fases), max(max(f) for f in fases)
        lo, hi = math.floor(min(lo, -180) / 45) * 45, math.ceil(max(hi, 0) / 45) * 45
        lo = max(lo, -720)
        ejes_fase = _Ejes(c, x0, y, w, h, (w_min, w_max), (lo, hi), "ω (rad/s)", "∠G(jω) (°)", log=True,
                          ypaso=45 if hi - lo <= 270 else 90)
        ejes_fase.guia(w_min, -180, w_max, -180, guiones="6 3", color="strokeSub")
        for i, f in enumerate(fases):
            ejes_fase.curva(list(zip(ws, f, strict=True)), estilo=i)
        y += h + 44
    ancho = x0 + w
    xr, yy = x0 + w + 14, top + 24
    etiquetas = [e for e, _ in sistemas if e]
    if etiquetas:
        yy += _leyenda(c, xr, yy, etiquetas) + 8
        ancho = max(ancho, xr + 32 + max(d._ancho_texto(e, 10) for e in etiquetas))
    if mg:
        if mg["w180"] is not None and ejes_mag:
            ejes_mag.guia(mg["w180"], 0, mg["w180"], -mg["gm"])
            c.punto(ejes_mag.px(mg["w180"]), ejes_mag.py(-mg["gm"]), radio=3)
            c.t(ejes_mag.px(mg["w180"]) + 4, ejes_mag.py(-mg["gm"] / 2), "MG", size=9, peso=700)
        if mg["wc"] is not None and ejes_fase:
            ejes_fase.guia(mg["wc"], -180, mg["wc"], mg["pm"] - 180)
            c.punto(ejes_fase.px(mg["wc"]), ejes_fase.py(mg["pm"] - 180), radio=3)
            c.t(ejes_fase.px(mg["wc"]) + 4, ejes_fase.py(mg["pm"] / 2 - 180), "MF", size=9, peso=700)
        for nombre, valor in (("MG", f"{_g(mg['gm'])} dB" if mg["gm"] is not None else "∞"),
                              ("ω180", _g(mg["w180"])), ("MF", f"{_g(mg['pm'])}°" if mg["pm"] is not None else "—"),
                              ("ωc", _g(mg["wc"]))):
            ancho = max(ancho, xr + _rotulo(c, xr, yy, nombre, valor, blanco))
            yy += 17
    return ancho + 6, y - 10


# --- Nyquist ------------------------------------------------------------------------------------------------

@_errores
def _nyquist(c: d._Lienzo, b: dict) -> Punto:
    sistemas = [(e, s.abierto if isinstance(s, control.Lazo) else s) for e, s in _sistemas_de(b)]
    if not sistemas:
        raise d.ErrorDiagrama("nyquist: falta system, systems o closedLoop")
    rangos = [control.rango_frecuencias(s) for _, s in sistemas]
    w_min = float(b.get("wMin") or min(r[0] for r in rangos) / 10)
    w_max = float(b.get("wMax") or max(r[1] for r in rangos) * 10)
    ws = [w_min * (w_max / w_min) ** (k / 1200) for k in range(1201)]
    curvas = [[s(1j * w) for w in ws] for _, s in sistemas]
    modulos = sorted(abs(z) for curva in curvas for z in curva if math.isfinite(abs(z)))
    limite = float(b.get("limit") or min(max(1.5, modulos[int(len(modulos) * 0.9)] * 1.1), 50))
    re_lo = min([-1.3] + [z.real for curva in curvas for z in curva if abs(z) <= limite])
    re_hi = max([0.5] + [z.real for curva in curvas for z in curva if abs(z) <= limite])
    im_lim = max([1.0] + [abs(z.imag) for curva in curvas for z in curva if abs(z) <= limite])
    alto_r = 2 * im_lim * 1.1
    ancho_r = (re_hi - re_lo) * 1.15
    escala = min(460 / ancho_r, 340 / alto_r)
    w, h = ancho_r * escala, alto_r * escala
    top = d._encabezado(c, b)
    x0, y0 = 58, top + 16
    margen_re = (re_hi - re_lo) * 0.075
    ejes = _Ejes(c, x0, y0, w, h, (re_lo - margen_re, re_hi + margen_re), (-alto_r / 2, alto_r / 2), "Re", "Im",
                 origen=True)
    if b.get("unitCircle"):
        ejes.curva([(math.cos(a / 60 * math.pi), math.sin(a / 60 * math.pi)) for a in range(121)], estilo=2, ancho=0.9,
                   color="strokeMuted")
    for i, curva in enumerate(curvas):
        positivo = [(z.real, z.imag) for z in curva]
        ejes.curva(positivo, estilo=i)
        if b.get("showNegative", True):
            ejes.curva([(x, -y) for x, y in positivo], estilo=2, ancho=1.0, color="strokeSub")
        for frac in (0.35, 0.6):  # el sentido de ω creciente
            k = int(len(positivo) * frac)
            (xa, ya), (xb, yb) = positivo[k], positivo[min(k + 4, len(positivo) - 1)]
            A, B = (ejes.px(xa), ejes.py(ya)), (ejes.px(xb), ejes.py(yb))
            if ejes.adentro(*A) and ejes.adentro(*B) and math.dist(A, B) > 0.5:
                c.linea(A[0], A[1], B[0], B[1], color="strokeMain", ancho=1.2)
    cx, cy = ejes.px(-1), ejes.py(0)
    c.linea(cx - 6, cy, cx + 6, cy, color="strokeMain", ancho=2, flecha=None)
    c.linea(cx, cy - 6, cx, cy + 6, color="strokeMain", ancho=2, flecha=None)
    c.t(cx - 4, cy - 9, "−1", size=10, peso=700, ancla="end")
    ancho = x0 + w
    etiquetas = [e for e, _ in sistemas if e]
    if etiquetas:
        _leyenda(c, x0 + w + 14, y0 + 10, etiquetas)
        ancho = max(ancho, x0 + w + 46 + max(d._ancho_texto(e, 10) for e in etiquetas))
    return ancho + 6, y0 + h + 40


# --- Plano s ---------------------------------------------------------------------------------------------

def _x(c: d._Lienzo, x: float, y: float, r: float = 5) -> None:
    c.linea(x - r, y - r, x + r, y + r, color="strokeMain", ancho=2, flecha=None)
    c.linea(x - r, y + r, x + r, y - r, color="strokeMain", ancho=2, flecha=None)


def _o(c: d._Lienzo, x: float, y: float, r: float = 5) -> None:
    c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#ffffff" stroke="{c.pal["strokeMain"]}" stroke-width="2"/>')


def _plano(c: d._Lienzo, b: dict, puntos: list[complex], minimo: float = 1.0):
    """Los ejes del plano s, con la misma escala en los dos ejes."""
    escala = max([minimo] + [abs(p.real) for p in puntos] + [abs(p.imag) for p in puntos])
    re_lo = min([-escala * 0.3] + [p.real for p in puntos]) - escala * 0.3
    re_hi = max([escala * 0.3] + [p.real for p in puntos]) + escala * 0.3
    im = max([escala * 0.5] + [abs(p.imag) for p in puntos]) * 1.3
    if "xRange" in b:
        re_lo, re_hi = (float(v) for v in b["xRange"])
    if "yRange" in b:
        im = max(abs(float(v)) for v in b["yRange"])
    px_por = min(440 / (re_hi - re_lo), 340 / (2 * im))
    top = d._encabezado(c, b)
    ejes = _Ejes(c, 58, top + 16, (re_hi - re_lo) * px_por, 2 * im * px_por, (re_lo, re_hi), (-im, im), "σ (Re s)",
                 "jω (Im s)", origen=True)
    return ejes, top


def _amortiguamiento(c: d._Lienzo, ejes: _Ejes, b: dict) -> None:
    lejos = max(abs(ejes.xr[0]), ejes.yr[1]) * 2
    for zeta in b.get("dampingLines") or []:
        zeta = float(zeta)
        if not 0 <= zeta <= 1:
            raise d.ErrorDiagrama("dampingLines: cada ζ va de 0 a 1")
        ang = math.acos(zeta)
        for signo in (1, -1):
            ejes.curva([(0, 0), (-lejos * math.cos(ang), signo * lejos * math.sin(ang))], estilo=1, ancho=0.9,
                       color="strokeMuted")
        # El rótulo, a la izquierda del extremo de la recta de arriba, adentro del gráfico.
        t = min(ejes.yr[1] * 0.9 / max(math.sin(ang), 1e-9), abs(ejes.xr[0]) * 0.9 / max(math.cos(ang), 1e-9))
        X, Y = ejes.px(-t * math.cos(ang)), ejes.py(t * math.sin(ang))
        c.t(X - 6, Y + 4, f"ζ = {_g(zeta)}", size=9, color="textSub", ancla="end")
    for wn in b.get("wnCircles") or []:
        wn = float(wn)
        ejes.curva([(wn * math.cos(a / 60 * math.pi), wn * math.sin(a / 60 * math.pi)) for a in range(30, 91)],
                   estilo=2, ancho=0.9, color="strokeMuted")
        c.t(ejes.px(-wn), ejes.py(0) + 12, f"ωn = {_g(wn)}", size=9, color="textSub", ancla="middle")


def _polos_ceros_de(b: dict) -> tuple[list[complex], list[complex]]:
    if "system" in b or "closedLoop" in b:
        s = control.abierto_de(b) if "system" in b else control.lazo(b["closedLoop"]).cerrado()
        return s.polos, s.ceros
    return control._raices_de(b.get("poles"), "poles"), control._raices_de(b.get("zeros"), "zeros")


@_errores
def _polos_ceros(c: d._Lienzo, b: dict) -> Punto:
    polos, ceros = _polos_ceros_de(b)
    ejes, _ = _plano(c, b, polos + ceros)
    _amortiguamiento(c, ejes, b)
    if not b.get("blank"):
        for z in ceros:
            _o(c, ejes.px(z.real), ejes.py(z.imag))
        for p in polos:
            _x(c, ejes.px(p.real), ejes.py(p.imag))
        if b.get("showValues"):
            for r in polos + ceros:
                texto = _g(r.real) + (f" {'+' if r.imag >= 0 else '−'} j{_g(abs(r.imag))}" if abs(r.imag) > 1e-9 else "")
                c.t(ejes.px(r.real) + 8, ejes.py(r.imag) - 7, texto, size=9, color="textSub")
    return ejes.x0 + ejes.w + 60, ejes.y0 + ejes.h + 40


@_errores
def _lugar(c: d._Lienzo, b: dict) -> Punto:
    s = control.abierto_de(b)
    polos, ceros = s.polos, s.ceros
    if not polos:
        raise d.ErrorDiagrama("root_locus: el sistema no tiene polos")
    escala = max([1.0] + [abs(r) for r in polos + ceros])
    k_max = float(b.get("kMax") or 0)
    if not k_max:
        k_max = 1.0
        while k_max < 1e7 and max(abs(r) for r in control.raices(control.suma(s.den, [k_max * x for x in s.num]))) < 3 * escala:
            k_max *= 2
    _, ramas = control.lugar_raices(s, k_max)
    cruce = control.cruce_imaginario(s, k_max) if b.get("showCrossing", True) else None
    extras = polos + ceros + ([complex(0, cruce[1])] if cruce else [])
    ejes, _ = _plano(c, b, extras, minimo=escala)
    _amortiguamiento(c, ejes, b)
    if b.get("asymptotes", True):
        centro, angulos = control.asintotas(s)
        if centro is not None and len(angulos) > 1:
            lejos = 3 * escala
            for a in angulos:
                ejes.curva([(centro, 0), (centro + lejos * math.cos(math.radians(a)), lejos * math.sin(math.radians(a)))],
                           estilo=1, ancho=0.9, color="strokeMuted")
            c.punto(ejes.px(centro), ejes.py(0), color="strokeSub", radio=2.5)
            # Con blankMarks, el centroide también queda para completar.
            _rotulo(c, ejes.px(centro), ejes.py(0) + 16, "σa", _g(centro), bool(b.get("blankMarks")), ancla="middle",
                    size=9)
    for rama in ramas:
        puntos = [(r.real, r.imag) for r in rama]
        ejes.curva(puntos, ancho=2)
        k = len(puntos) // 3
        (xa, ya), (xb, yb) = puntos[k], puntos[min(k + 3, len(puntos) - 1)]
        A, B = (ejes.px(xa), ejes.py(ya)), (ejes.px(xb), ejes.py(yb))
        if ejes.adentro(*A) and ejes.adentro(*B) and math.dist(A, B) > 1:
            c.linea(A[0], A[1], B[0], B[1], color="strokeMain", ancho=1.4)
    for z in ceros:
        _o(c, ejes.px(z.real), ejes.py(z.imag))
    for p in polos:
        _x(c, ejes.px(p.real), ejes.py(p.imag))
    blanco = bool(b.get("blankMarks"))
    rotulos = []
    for k in b.get("marks") or []:
        k = float(k)
        for r in control.raices(control.suma(s.den, [k * x for x in s.num])):
            X, Y = ejes.px(r.real), ejes.py(r.imag)
            if ejes.adentro(X, Y):
                c.add(f'<rect x="{X - 3.5:.1f}" y="{Y - 3.5:.1f}" width="7" height="7" fill="{c.pal["strokeMain"]}"/>')
        rotulos.append((f"■ K = {_g(k)}", None))
    if cruce:
        k_c, w_c = cruce
        for signo in (1, -1):
            c.punto(ejes.px(0), ejes.py(signo * w_c), radio=3.5)
        rotulos += [("Kcrít", _g(k_c)), ("ωcrít", _g(w_c))]
    xr, yy, ancho = ejes.x0 + ejes.w + 14, ejes.y0 + 10, ejes.x0 + ejes.w
    for nombre, valor in rotulos:
        if valor is None:
            c.t(xr, yy, nombre, size=10, peso=700)
            ancho = max(ancho, xr + d._ancho_texto(nombre, 10))
        else:
            ancho = max(ancho, xr + _rotulo(c, xr, yy, nombre, valor, blanco))
        yy += 17
    return ancho + 6, ejes.y0 + ejes.h + 40


# --- Diagrama de bloques ---------------------------------------------------------------------------------

_ALTO_BLOQUE, _FLECHA, _RADIO = 36, 38, 11
_CARRIL = 30          # de la línea principal a la de realimentación


class _Bloque:
    def __init__(self, dato: Any, donde: str):
        if isinstance(dato, dict):
            self.texto = str(dato.get("label", "") or "")
            self.blanco = bool(dato.get("blank"))
            self.salida = str(dato.get("out") or "")
        else:
            self.texto, self.blanco, self.salida = str(dato), False, ""
        if not self.texto and not self.blanco:
            raise d.ErrorDiagrama(f"{donde}: un bloque necesita label (o blank: true)")
        self.w = max(64.0, d._ancho_texto(self.texto or "XXXXXX", 11) + 24)
        self.arriba = self.abajo = _ALTO_BLOQUE / 2

    def dibujar(self, c: d._Lienzo, x: float, y: float) -> None:
        c.r(x, y - _ALTO_BLOQUE / 2, self.w, _ALTO_BLOQUE, trazo=1.6, rx=2)
        if self.blanco:
            c.vacio(x + 12, x + self.w - 12, y + 6)
        else:
            c.t(x + self.w / 2, y + 4, self.texto, size=11, peso=600, ancla="middle")


def _sumador(c: d._Lienzo, x: float, y: float, signos: list[tuple[str, str]], blanco: bool) -> None:
    """El sumador centrado en (x, y); `signos`: (lado, signo), con lado en izq, abajo, arriba."""
    c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{_RADIO}" fill="#ffffff" stroke="{c.pal["strokeMain"]}" stroke-width="1.6"/>')
    lugares = {"izq": (x - _RADIO - 7, y - 6), "abajo": (x - 11, y + _RADIO + 11), "arriba": (x - 11, y - _RADIO - 3)}
    for lado, signo in signos:
        sx, sy = lugares[lado]
        if blanco:
            c.add(f'<rect x="{sx - 5:.1f}" y="{sy - 9:.1f}" width="10" height="11" fill="none" '
                  f'stroke="{c.pal["strokeMuted"]}" stroke-width="1" stroke-dasharray="2 2"/>')
        else:
            c.t(sx, sy, "−" if signo == "-" else "+", size=12, peso=700, ancla="middle")


class _Perturbacion:
    def __init__(self, dato: dict, donde: str):
        if not isinstance(dato, dict) or "at" not in dato:
            raise d.ErrorDiagrama(f"{donde}: disturbance necesita at (antes de qué bloque entra)")
        self.at = int(dato["at"])
        self.texto = str(dato.get("label") or "D(s)")
        self.signo = str(dato.get("sign", "+"))
        self.bloque = _Bloque(dato["block"], f"{donde}.block") if dato.get("block") else None
        self.w = 2 * _RADIO
        self.arriba = _RADIO + 34 + (_ALTO_BLOQUE + 24 if self.bloque else 0)
        self.abajo = _RADIO

    def dibujar(self, c: d._Lienzo, x: float, y: float, blanco: bool) -> None:
        cx = x + _RADIO
        _sumador(c, cx, y, [("izq", "+"), ("arriba", self.signo)], blanco)
        tope = y - self.arriba
        c.t(cx, tope + 10, self.texto, size=11, peso=700, ancla="middle")
        if self.bloque:
            by = tope + 18 + _ALTO_BLOQUE / 2 + 6
            c.linea(cx, tope + 14, cx, by - _ALTO_BLOQUE / 2)
            bx = cx - self.bloque.w / 2
            self.bloque.dibujar(c, bx, by)
            c.linea(cx, by + _ALTO_BLOQUE / 2, cx, y - _RADIO)
        else:
            c.linea(cx, tope + 14, cx, y - _RADIO)


class _Lazo:
    """Un lazo: sumador, cadena directa, punto de toma y realimentación (vacía = unitaria)."""

    def __init__(self, dato: dict, donde: str, cerrado: bool = True):
        self.cerrado = cerrado
        self.signo = str(dato.get("sign", "-"))
        if self.signo not in ("-", "+"):
            raise d.ErrorDiagrama(f"{donde}.sign: es '-' o '+'")
        self.error = str(dato.get("error") or "")
        self.medida = str(dato.get("measured") or "")
        directa = dato.get("forward")
        if not isinstance(directa, list) or not directa:
            raise d.ErrorDiagrama(f"{donde}.forward: tiene que ser una lista de bloques")
        self.cadena: list[Any] = [_elemento(e, f"{donde}.forward[{i}]") for i, e in enumerate(directa)]
        if dato.get("disturbance"):
            p = _Perturbacion(dato["disturbance"], f"{donde}.disturbance")
            if not 0 <= p.at <= len(self.cadena):
                raise d.ErrorDiagrama(f"{donde}.disturbance.at: va de 0 a {len(self.cadena)}")
            self.cadena.insert(p.at, p)
        realim = dato.get("feedback") or []
        if not isinstance(realim, list):
            raise d.ErrorDiagrama(f"{donde}.feedback: tiene que ser una lista de bloques ([] es unitaria)")
        self.realim = [_Bloque(e, f"{donde}.feedback[{i}]") for i, e in enumerate(realim)]
        self.blanco = bool(dato.get("blankSigns"))
        ancho_cadena = sum(e.w for e in self.cadena) + sum(self._flecha(i) for i in range(len(self.cadena) - 1))
        self.inicio = (2 * _RADIO + _FLECHA) if cerrado else 0
        self.w = self.inicio + ancho_cadena + (_FLECHA if cerrado else 0)
        self.arriba = max(e.arriba for e in self.cadena) + (14 if self.error else 0)
        abajo_cadena = max(e.abajo for e in self.cadena)
        if cerrado:
            self.carril = abajo_cadena + _CARRIL + (_ALTO_BLOQUE / 2 if self.realim else 0)
            self.abajo = self.carril + (_ALTO_BLOQUE / 2 if self.realim else 0) + (14 if self.medida else 6)
        else:
            self.abajo = abajo_cadena

    def _flecha(self, i: int) -> float:
        """La flecha después del elemento i: más larga si entra a un sumador, para que el rótulo no pise el signo."""
        return _FLECHA + (14 if isinstance(self.cadena[i + 1], _Perturbacion) else 0)

    def dibujar(self, c: d._Lienzo, x: float, y: float) -> None:
        cx = x + _RADIO
        if self.cerrado:
            _sumador(c, cx, y, [("izq", "+"), ("abajo", self.signo)], self.blanco)
            c.linea(x + 2 * _RADIO, y, x + self.inicio, y)
            if self.error:
                c.t(x + 2 * _RADIO + _FLECHA / 2, y - 8, self.error, size=10, peso=600, ancla="middle")
        xi = x + self.inicio
        for i, e in enumerate(self.cadena):
            if isinstance(e, _Perturbacion):
                e.dibujar(c, xi, y, self.blanco)
            else:
                e.dibujar(c, xi, y)
            xi += e.w
            if i < len(self.cadena) - 1:
                largo = self._flecha(i)
                c.linea(xi, y, xi + largo, y)
                salida = getattr(e, "salida", "")
                if salida:
                    c.t(xi + _FLECHA / 2, y - 8, salida, size=10, peso=600, ancla="middle")
                xi += largo
        if not self.cerrado:
            return
        toma = x + self.w
        c.linea(xi, y, toma, y, flecha=None)
        salida = getattr(self.cadena[-1], "salida", "")
        if salida:
            c.t(xi + _FLECHA / 2, y - 8, salida, size=10, peso=600, ancla="middle")
        c.punto(toma, y)
        yf = y + self.carril
        if self.realim:
            ancho = sum(b.w for b in self.realim) + _FLECHA * (len(self.realim) - 1)
            bx = toma - (toma - cx - ancho) / 2 - ancho
            c.add(f'<path d="M {toma:.1f} {y:.1f} L {toma:.1f} {yf:.1f} L {bx + ancho:.1f} {yf:.1f}" fill="none" '
                  f'stroke="{c.pal["accentPrimary"]}" stroke-width="1.6" marker-end="url(#flecha-main-{c.sufijo})"/>')
            xb = bx + ancho
            for i, bloque in enumerate(reversed(self.realim)):
                xb -= bloque.w
                bloque.dibujar(c, xb, yf)
                if i < len(self.realim) - 1:
                    c.linea(xb, yf, xb - _FLECHA, yf)
                    xb -= _FLECHA
            c.ruta((bx, yf), (cx, yf), (cx, y + _RADIO))
        else:
            c.ruta((toma, y), (toma, yf), (cx, yf), (cx, y + _RADIO))
        if self.medida:
            c.t(cx + 6, yf + 14, self.medida, size=10, peso=600)


def _elemento(dato: Any, donde: str):
    if isinstance(dato, dict) and "loop" in dato:
        return _Lazo(dato["loop"], f"{donde}.loop")
    return _Bloque(dato, donde)


@_errores
def _bloques(c: d._Lienzo, b: dict) -> Punto:
    cerrado = "feedback" in b
    lazo = _Lazo(b, "block_diagram", cerrado=cerrado)
    top = d._encabezado(c, b)
    entrada, salida = str(b.get("input") or "R(s)"), str(b.get("output") or "Y(s)")
    margen = max(46.0, d._ancho_texto(entrada, 11) + 30)
    y = top + lazo.arriba + 12
    x = margen
    c.t(4, y - 8, entrada, size=11, peso=700)
    c.linea(4, y, x, y)
    lazo.dibujar(c, x, y)
    fin = x + lazo.w
    largo = max(46.0, d._ancho_texto(salida, 11) + 16)
    c.linea(fin, y, fin + largo, y)
    c.t(fin + largo, y - 8, salida, size=11, peso=700, ancla="end")
    return fin + largo + 4, y + lazo.abajo + 6


# --- P&ID (ISA-5.1) --------------------------------------------------------------------------------------

_EQUIPOS = ("tank", "vessel", "reactor", "column", "pump", "control_valve", "valve", "heat_exchanger")
_UBICACIONES = ("field", "panel", "panel_back", "dcs", "plc")
_LINEAS = ("process", "electric", "pneumatic", "data", "capillary")


class _Pieza:
    def __init__(self, id_: str, x: float, y: float, mw: float, mh: float, circular: bool = False):
        self.id, self.x, self.y, self.mw, self.mh, self.circular = id_, x, y, mw, mh, circular

    def borde(self, hacia: Punto) -> Punto:
        """Dónde sale una línea desde el centro hacia `hacia`."""
        dx, dy = hacia[0] - self.x, hacia[1] - self.y
        if dx == 0 and dy == 0:
            return self.x, self.y
        if self.circular:
            r = self.mw
            n = math.hypot(dx, dy)
            return self.x + dx / n * r, self.y + dy / n * r
        tx = self.mw / abs(dx) if dx else math.inf
        ty = self.mh / abs(dy) if dy else math.inf
        t = min(tx, ty)
        return self.x + dx * t, self.y + dy * t


def _equipo(c: d._Lienzo, e: dict, g: float, donde: str) -> _Pieza:
    tipo = e.get("kind")
    if tipo not in _EQUIPOS:
        raise d.ErrorDiagrama(f"{donde}.kind: {tipo!r} (valen {', '.join(_EQUIPOS)})")
    x, y = (float(v) * g for v in e["at"])
    etiqueta = str(e.get("label") or "")
    pal = c.pal
    trazo = f'stroke="{pal["strokeMain"]}" stroke-width="1.8"'
    if tipo in ("tank", "vessel", "reactor", "column"):
        defecto = {"tank": (2, 2.4), "vessel": (1.4, 2.6), "reactor": (1.8, 2.4), "column": (1, 4)}[tipo]
        w, h = (float(v) * g for v in e.get("size", defecto))
        if tipo == "tank":
            c.add(f'<path d="M {x - w / 2:.1f} {y - h / 2:.1f} L {x - w / 2:.1f} {y + h / 2:.1f} L {x + w / 2:.1f} '
                  f'{y + h / 2:.1f} L {x + w / 2:.1f} {y - h / 2:.1f}" fill="#ffffff" {trazo}/>')
            nivel = e.get("level")
            if nivel is not None:
                yl = y + h / 2 - float(nivel) * h
                c.linea(x - w / 2 + 4, yl, x + w / 2 - 4, yl, color="strokeSub", ancho=1, flecha=None, guiones="5 3")
        else:
            radio = min(w / 2, h / 4)
            c.add(f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{w / 2:.1f}" '
                  f'ry="{radio:.1f}" fill="#ffffff" {trazo}/>')
            if tipo == "column":
                for k in range(1, 8):
                    yk = y - h / 2 + radio + k * (h - 2 * radio) / 8
                    c.linea(x - w / 2, yk, x + w / 2 - w * 0.25 * (k % 2), yk, color="strokeSub", ancho=0.9, flecha=None)
            if tipo == "reactor":
                tope = y - h / 2
                c.add(f'<circle cx="{x:.1f}" cy="{tope - 16:.1f}" r="10" fill="#ffffff" {trazo}/>')
                c.t(x, tope - 12, "M", size=10, peso=700, ancla="middle")
                c.linea(x, tope - 6, x, y + h * 0.25, color="strokeMain", ancho=1.5, flecha=None)
                c.add(f'<path d="M {x - w * 0.28:.1f} {y + h * 0.18:.1f} L {x + w * 0.28:.1f} {y + h * 0.32:.1f} M '
                      f'{x - w * 0.28:.1f} {y + h * 0.32:.1f} L {x + w * 0.28:.1f} {y + h * 0.18:.1f}" {trazo}/>')
        if etiqueta:
            c.t(x, y + h / 2 + 14, etiqueta, size=10, peso=700, ancla="middle")
        return _Pieza(e["id"], x, y, w / 2, h / 2)
    if tipo == "pump":
        r = 0.42 * g
        c.add(f'<path d="M {x - r * 0.8:.1f} {y + r * 1.25:.1f} L {x - r * 0.45:.1f} {y + r * 0.7:.1f} M {x + r * 0.8:.1f} '
              f'{y + r * 1.25:.1f} L {x + r * 0.45:.1f} {y + r * 0.7:.1f} M {x - r:.1f} {y + r * 1.25:.1f} L '
              f'{x + r:.1f} {y + r * 1.25:.1f}" {trazo}/>')
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" {trazo}/>')
        c.linea(x, y - r, x + r * 1.3, y - r, color="strokeMain", ancho=1.8, flecha=None)
        if etiqueta:
            c.t(x, y + r * 1.25 + 14, etiqueta, size=10, peso=700, ancla="middle")
        pieza = _Pieza(e["id"], x, y, r, r, circular=True)
        pieza.descarga = (x + r * 1.3, y - r)  # type: ignore[attr-defined]
        return pieza
    if tipo in ("control_valve", "valve"):
        a = 0.36 * g
        vertical = e.get("orientation") == "v"
        if vertical:
            c.add(f'<path d="M {x - a * 0.6:.1f} {y - a:.1f} L {x + a * 0.6:.1f} {y - a:.1f} L {x - a * 0.6:.1f} {y + a:.1f} '
                  f'L {x + a * 0.6:.1f} {y + a:.1f} Z" fill="#ffffff" {trazo}/>')
        else:
            c.add(f'<path d="M {x - a:.1f} {y - a * 0.6:.1f} L {x - a:.1f} {y + a * 0.6:.1f} L {x + a:.1f} {y - a * 0.6:.1f} '
                  f'L {x + a:.1f} {y + a * 0.6:.1f} Z" fill="#ffffff" {trazo}/>')
        tope = y
        actuador = (x, y)
        if tipo == "control_valve":
            if vertical:  # con la cañería vertical, el actuador va al costado (a la derecha)
                c.linea(x, y, x + a * 1.6, y, color="strokeMain", ancho=1.5, flecha=None)
                c.add(f'<path d="M {x + a * 1.6:.1f} {y - a * 0.8:.1f} A {a * 0.6:.1f} {a * 0.8:.1f} 0 0 1 '
                      f'{x + a * 1.6:.1f} {y + a * 0.8:.1f} Z" fill="#ffffff" {trazo}/>')
                actuador = (x + a * 2.2, y)
            else:
                c.linea(x, y, x, y - a * 1.6, color="strokeMain", ancho=1.5, flecha=None)
                c.add(f'<path d="M {x - a * 0.8:.1f} {y - a * 1.6:.1f} A {a * 0.8:.1f} {a * 0.6:.1f} 0 0 1 '
                      f'{x + a * 0.8:.1f} {y - a * 1.6:.1f} Z" fill="#ffffff" {trazo}/>')
                tope = y - a * 2.2
                actuador = (x, tope)
        if etiqueta:
            if vertical:
                c.t(x - a - 4, y + 4, etiqueta, size=10, peso=700, ancla="end")
            else:
                c.t(x + a + 4, tope + 2 if tipo == "control_valve" else y - a - 4, etiqueta, size=10, peso=700)
        pieza = _Pieza(e["id"], x, y, a * 0.6 if vertical else a, a if vertical else a * 0.6)
        pieza.actuador = actuador  # type: ignore[attr-defined]
        return pieza
    # heat_exchanger
    r = 0.45 * g
    c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" {trazo}/>')
    c.add(f'<path d="M {x - r:.1f} {y:.1f} L {x - r * 0.5:.1f} {y:.1f} L {x - r * 0.25:.1f} {y - r * 0.45:.1f} L '
          f'{x + r * 0.25:.1f} {y + r * 0.45:.1f} L {x + r * 0.5:.1f} {y:.1f} L {x + r:.1f} {y:.1f}" fill="none" {trazo}/>')
    if etiqueta:
        c.t(x, y + r + 14, etiqueta, size=10, peso=700, ancla="middle")
    return _Pieza(e["id"], x, y, r, r, circular=True)


def _instrumento(c: d._Lienzo, e: dict, g: float, donde: str) -> _Pieza:
    ubicacion = e.get("location", "field")
    if ubicacion not in _UBICACIONES:
        raise d.ErrorDiagrama(f"{donde}.location: {ubicacion!r} (valen {', '.join(_UBICACIONES)})")
    x, y = (float(v) * g for v in e["at"])
    r = 0.4 * g
    pal = c.pal
    trazo = f'stroke="{pal["strokeMain"]}" stroke-width="1.5"'
    if ubicacion in ("dcs", "plc"):
        c.add(f'<rect x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" fill="#ffffff" {trazo}/>')
    if ubicacion == "plc":
        c.add(f'<path d="M {x:.1f} {y - r:.1f} L {x + r:.1f} {y:.1f} L {x:.1f} {y + r:.1f} L {x - r:.1f} {y:.1f} Z" '
              f'fill="#ffffff" {trazo}/>')
    else:
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" {trazo}/>')
    if ubicacion in ("panel", "dcs"):
        c.linea(x - r, y, x + r, y, color="strokeMain", ancho=1.2, flecha=None)
    elif ubicacion == "panel_back":
        c.linea(x - r, y, x + r, y, color="strokeMain", ancho=1.2, flecha=None, guiones="3 2")
    tag = str(e.get("tag") or "")
    letras, numero = (tag.split(None, 1) + [""])[:2] if " " in tag else (tag.rstrip("0123456789-"), tag[len(tag.rstrip("0123456789-")):])
    if e.get("blank"):
        c.vacio(x - r * 0.6, x + r * 0.6, y - 4)
        c.vacio(x - r * 0.6, x + r * 0.6, y + r * 0.6)
    else:
        c.t(x, y - 4, letras, size=10, peso=700, ancla="middle", fuente=d.SANS)
        c.t(x, y + r * 0.55, numero.strip("-"), size=9, ancla="middle", fuente=d.SANS)
    return _Pieza(e["id"], x, y, r, r, circular=ubicacion not in ("dcs", "plc"))


def _marcas_linea(c: d._Lienzo, puntos: list[Punto], tipo: str) -> None:
    """Las marcas de una señal neumática (//), de datos (o) o capilar (x), cada 26 px."""
    resto = 13.0
    for (x1, y1), (x2, y2) in itertools.pairwise(puntos):
        largo = math.dist((x1, y1), (x2, y2))
        if largo == 0:
            continue
        ux, uy = (x2 - x1) / largo, (y2 - y1) / largo
        s = resto
        while s < largo - 6:
            px, py = x1 + ux * s, y1 + uy * s
            if tipo == "pneumatic":
                for corrido in (-3, 3):
                    qx, qy = px + ux * corrido, py + uy * corrido
                    c.linea(qx - uy * 5 + ux * 3, qy + ux * 5 + uy * 3, qx + uy * 5 - ux * 3, qy - ux * 5 - uy * 3,
                            color="strokeMain", ancho=1, flecha=None)
            elif tipo == "data":
                c.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="#ffffff" stroke="{c.pal["strokeMain"]}" stroke-width="1"/>')
            elif tipo == "capillary":
                c.linea(px - 3, py - 3, px + 3, py + 3, color="strokeMain", ancho=1, flecha=None)
                c.linea(px - 3, py + 3, px + 3, py - 3, color="strokeMain", ancho=1, flecha=None)
            s += 26
        resto = s - largo


@_errores
def _instrumentacion(c: d._Lienzo, b: dict) -> Punto:
    g = float(b.get("grid", 50))
    top = d._encabezado(c, b) + 10
    c.add(f'<g transform="translate(0 {top})">')
    piezas: dict[str, _Pieza] = {}
    equipos, instrumentos = b.get("equipment") or [], b.get("instruments") or []
    if not equipos and not instrumentos:
        raise d.ErrorDiagrama("instrumentation: falta equipment o instruments")
    trazados_lineas: list[str] = []
    for i, e in enumerate(equipos):
        if not isinstance(e, dict) or "id" not in e or "at" not in e:
            raise d.ErrorDiagrama(f"equipment[{i}]: necesita id, kind y at: [x, y]")
    for i, e in enumerate(instrumentos):
        if not isinstance(e, dict) or "id" not in e or "at" not in e:
            raise d.ErrorDiagrama(f"instruments[{i}]: necesita id, tag y at: [x, y]")
    # Primero las líneas (abajo de los símbolos): las piezas se miden sin dibujarlas.
    medidas = d._Lienzo(c.pal, c.sufijo)
    for i, e in enumerate(equipos):
        piezas[str(e["id"])] = _equipo(medidas, e, g, f"equipment[{i}]")
    for i, e in enumerate(instrumentos):
        piezas[str(e["id"])] = _instrumento(medidas, e, g, f"instruments[{i}]")
    ancho = max(p.x + p.mw for p in piezas.values()) + 60
    alto = max(p.y + p.mh for p in piezas.values()) + 30
    for i, linea in enumerate(b.get("lines") or []):
        donde = f"lines[{i}]"
        tipo = linea.get("kind", "process")
        if tipo not in _LINEAS:
            raise d.ErrorDiagrama(f"{donde}.kind: {tipo!r} (valen {', '.join(_LINEAS)})")

        def lugar(ref: Any, clave: str, linea: dict = linea, tipo: str = tipo, donde: str = donde
                  ) -> tuple[_Pieza | None, Punto]:
            if isinstance(ref, list):
                return None, (float(ref[0]) * g, float(ref[1]) * g)
            pieza = piezas.get(str(ref))
            if pieza is None:
                raise d.ErrorDiagrama(f"{donde}.{clave}: no hay un equipo ni un instrumento {ref!r}")
            if clave == "from" and hasattr(pieza, "descarga"):
                return None, pieza.descarga  # type: ignore[attr-defined]  # la bomba descarga por su tobera
            if clave == "from" and linea.get("fromActuator") and hasattr(pieza, "actuador"):
                return None, pieza.actuador  # type: ignore[attr-defined]
            if clave == "to" and linea.get("toActuator", tipo != "process") and hasattr(pieza, "actuador"):
                return None, pieza.actuador  # type: ignore[attr-defined]
            return pieza, (pieza.x, pieza.y)

        a, pa = lugar(linea.get("from"), "from")
        z, pz = lugar(linea.get("to"), "to")
        intermedios = [(float(p[0]) * g, float(p[1]) * g) for p in linea.get("via") or []]
        if not intermedios and pa[0] != pz[0] and pa[1] != pz[1]:
            intermedios = [(pz[0], pa[1])] if linea.get("route", "hv") == "hv" else [(pa[0], pz[1])]
        puntos = [pa, *intermedios, pz]
        if a:
            puntos[0] = a.borde(puntos[1])
        if z:
            puntos[-1] = z.borde(puntos[-2])
        camino = " L ".join(f"{x:.1f} {y:.1f}" for x, y in puntos)
        estilo = {"process": 'stroke-width="2.2"', "electric": 'stroke-width="1.2" stroke-dasharray="7 4"',
                  "pneumatic": 'stroke-width="1.2"', "data": 'stroke-width="1.2"', "capillary": 'stroke-width="1.2"'}[tipo]
        flecha = linea.get("arrow", tipo == "process")
        trazados_lineas.append(f'<path d="M {camino}" fill="none" stroke="{c.pal["strokeMain"]}" {estilo}'
                               + (f' marker-end="url(#flecha-main-{c.sufijo})"' if flecha else "") + "/>")
        if tipo in ("pneumatic", "data", "capillary"):
            marcas = d._Lienzo(c.pal, c.sufijo)
            _marcas_linea(marcas, puntos, tipo)
            trazados_lineas.extend(marcas.partes)
        if linea.get("label"):
            (x1, y1), (x2, y2) = max(itertools.pairwise(puntos), key=lambda s: math.dist(*s))
            vertical = abs(x2 - x1) < abs(y2 - y1)   # en un tramo vertical, el rótulo va al costado
            lx, ly = ((x1 + x2) / 2 + 7, (y1 + y2) / 2 + 4) if vertical else ((x1 + x2) / 2, (y1 + y2) / 2 - 6)
            trazados_lineas.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{"start" if vertical else "middle"}" '
                f'font-family="{d.SANS}" font-size="10" fill="{c.pal["textSub"]}">{d._esc(linea["label"])}</text>')
        ancho = max(ancho, max(x for x, _ in puntos) + 40)
        alto = max(alto, max(y for _, y in puntos) + 20)
    c.add(*trazados_lineas)
    for i, e in enumerate(equipos):
        _equipo(c, e, g, f"equipment[{i}]")
    for i, e in enumerate(instrumentos):
        _instrumento(c, e, g, f"instruments[{i}]")
    if b.get("legend", True):
        presentes = sorted({str(linea.get("kind", "process")) for linea in b.get("lines") or []} - {"process"})
        nombres = {"electric": "señal eléctrica", "pneumatic": "señal neumática", "data": "enlace de datos",
                   "capillary": "tubo capilar"}
        for k, tipo in enumerate(presentes):
            ly = alto + 6 + k * 16
            trazo = d._Lienzo(c.pal, c.sufijo)
            puntos = [(10.0, ly), (62.0, ly)]
            estilo = 'stroke-dasharray="7 4"' if tipo == "electric" else ""
            c.add(f'<line x1="10" y1="{ly:.1f}" x2="62" y2="{ly:.1f}" stroke="{c.pal["strokeMain"]}" stroke-width="1.2" {estilo}/>')
            _marcas_linea(trazo, puntos, tipo) if tipo != "electric" else None
            c.add(*trazo.partes)
            c.t(70, ly + 4, nombres[tipo], size=9.5, color="textSub", fuente=d.SANS)
        alto += 6 + len(presentes) * 16
    c.add("</g>")
    return ancho, alto + top


# --- Escalera (PLC) ---------------------------------------------------------------------------------------

_CONTACTOS = ("no", "nc", "p", "n")
_SALIDAS = ("coil", "set", "reset", "ncoil")
_CAJAS = ("ton", "tof", "tp", "ctu", "ctd")
_FILA, _CONTACTO, _CAJA_W, _CAJA_H = 58, 64, 96, 48


def _clase(e: dict) -> str:
    # YAML 1.1 lee `no:` como false: el contacto normal abierto se escribe `no` o `na`.
    if False in e and "no" not in e:
        e["no"] = e.pop(False)
    if "na" in e and "no" not in e:
        e["no"] = e.pop("na")
    for k in (*_CONTACTOS, *_SALIDAS, *_CAJAS):
        if k in e:
            return k
    if "or" in e:
        return "or"
    raise d.ErrorDiagrama(f"ladder: elemento desconocido {e!r} (valen no, nc, p, n, coil, set, reset, ncoil, ton, tof, "
                          "tp, ctu, ctd y or)")


def _medir_escalon(serie: list) -> tuple[float, float]:
    ancho, alto = 0.0, _FILA
    for e in serie:
        k = _clase(e)
        if k == "or":
            ramas = [_medir_escalon(r) for r in e["or"]]
            ancho += max(w for w, _ in ramas) + 24
            alto = max(alto, sum(h for _, h in ramas))
        elif k in _CAJAS:
            ancho += _CAJA_W + 24
            alto = max(alto, _CAJA_H + 30)
        else:
            ancho += _CONTACTO
    return ancho, alto


def _simbolo(c: d._Lienzo, e: dict, x: float, y: float, w: float) -> None:
    """Un contacto, una bobina o una caja entre x y x + w, sobre la línea y."""
    k = _clase(e)
    tag = str(e.get(k) or "")
    cx = x + w / 2
    pal = c.pal
    if e.get("blank"):
        c.linea(x, y, cx - 14, y, color="strokeMain", ancho=1.5, flecha=None)
        c.linea(cx + 14, y, x + w, y, color="strokeMain", ancho=1.5, flecha=None)
        c.add(f'<rect x="{cx - 14:.1f}" y="{y - 13:.1f}" width="28" height="26" fill="none" stroke="{pal["strokeMuted"]}" '
              f'stroke-width="1.2" stroke-dasharray="3 2"/>')
    elif k in _CONTACTOS:
        c.linea(x, y, cx - 6, y, color="strokeMain", ancho=1.5, flecha=None)
        c.linea(cx + 6, y, x + w, y, color="strokeMain", ancho=1.5, flecha=None)
        for dx in (-6, 6):
            c.linea(cx + dx, y - 11, cx + dx, y + 11, color="strokeMain", ancho=2, flecha=None)
        if k == "nc":
            c.linea(cx - 9, y + 10, cx + 9, y - 10, color="strokeMain", ancho=1.5, flecha=None)
        elif k in ("p", "n"):
            c.t(cx, y + 4, k.upper(), size=9, peso=700, ancla="middle")
    elif k in _SALIDAS:
        c.linea(x, y, cx - 11, y, color="strokeMain", ancho=1.5, flecha=None)
        c.linea(cx + 11, y, x + w, y, color="strokeMain", ancho=1.5, flecha=None)
        c.add(f'<path d="M {cx - 6:.1f} {y - 11:.1f} A 12 12 0 0 0 {cx - 6:.1f} {y + 11:.1f} M {cx + 6:.1f} {y - 11:.1f} '
              f'A 12 12 0 0 1 {cx + 6:.1f} {y + 11:.1f}" fill="none" stroke="{pal["strokeMain"]}" stroke-width="2"/>')
        letra = {"set": "S", "reset": "R", "ncoil": "/"}.get(k)
        if letra:
            c.t(cx, y + 4, letra, size=10, peso=700, ancla="middle")
    else:
        bx = x + 12
        c.linea(x, y, bx, y, color="strokeMain", ancho=1.5, flecha=None)
        c.linea(bx + _CAJA_W, y, x + w, y, color="strokeMain", ancho=1.5, flecha=None)
        c.r(bx, y - 14, _CAJA_W, _CAJA_H, trazo=1.6)
        c.t(bx + _CAJA_W / 2, y + 2, k.upper(), size=11, peso=700, ancla="middle")
        preset = e.get("preset")
        if preset is not None:
            c.t(bx + 6, y + 26, f"{'PT' if k in ('ton', 'tof', 'tp') else 'PV'} {preset}", size=9, color="textSub")
    if k not in _CAJAS or e.get("blank"):
        if tag:
            c.t(cx, y - 16, tag, size=10, peso=700, ancla="middle")
        if e.get("label"):
            c.t(cx, y + 26, str(e["label"]), size=9, color="textMuted", ancla="middle", fuente=d.SANS)
    else:
        c.t(x + 12 + _CAJA_W / 2, y - 20, tag, size=10, peso=700, ancla="middle")
        if e.get("label"):
            c.t(x + 12 + _CAJA_W / 2, y + _CAJA_H + 2, str(e["label"]), size=9, color="textMuted", ancla="middle",
                fuente=d.SANS)


def _dibujar_serie(c: d._Lienzo, serie: list, x: float, y: float, ancho: float) -> None:
    """La serie entre x y x + ancho; lo que sobra queda como cable al final."""
    for e in serie:
        k = _clase(e)
        if k == "or":
            ramas = [(r, _medir_escalon(r)) for r in e["or"]]
            w = max(m[0] for _, m in ramas) + 24
            yy = y
            ys = []
            for rama, (_rw, rh) in ramas:
                c.linea(x, yy, x + 12, yy, color="strokeMain", ancho=1.5, flecha=None)
                _dibujar_serie(c, rama, x + 12, yy, w - 24)
                c.linea(x + w - 12, yy, x + w, yy, color="strokeMain", ancho=1.5, flecha=None)
                ys.append(yy)
                yy += rh
            c.linea(x, ys[0], x, ys[-1], color="strokeMain", ancho=1.5, flecha=None)
            c.linea(x + w, ys[0], x + w, ys[-1], color="strokeMain", ancho=1.5, flecha=None)
            x += w
            ancho -= w
        else:
            w = _CAJA_W + 24 if k in _CAJAS else _CONTACTO
            _simbolo(c, e, x, y, w)
            x += w
            ancho -= w
    if ancho > 0.5:
        c.linea(x, y, x + ancho, y, color="strokeMain", ancho=1.5, flecha=None)


@_errores
def _escalera(c: d._Lienzo, b: dict) -> Punto:
    escalones = b.get("rungs")
    if not isinstance(escalones, list) or not escalones:
        raise d.ErrorDiagrama("ladder: 'rungs' tiene que ser una lista de escalones con logic")
    partes = []
    for i, r in enumerate(escalones):
        logica = r.get("logic") if isinstance(r, dict) else None
        if not isinstance(logica, list) or not logica:
            raise d.ErrorDiagrama(f"rungs[{i}].logic: tiene que ser una lista de elementos")
        corte = len(logica)
        while corte > 0 and _clase(logica[corte - 1]) in (*_SALIDAS, *_CAJAS):
            corte -= 1
        if corte == len(logica):
            raise d.ErrorDiagrama(f"rungs[{i}]: el escalón tiene que terminar en una salida (coil, set, reset, un "
                                  "temporizador o un contador)")
        if corte == 0:
            raise d.ErrorDiagrama(f"rungs[{i}]: el escalón necesita al menos un contacto antes de la salida")
        entradas, salidas = logica[:corte], logica[corte:]
        partes.append((r, entradas, salidas, _medir_escalon(entradas), _medir_escalon(salidas)))
    ancho_util = max(me[0] + ms[0] for _, _, _, me, ms in partes) + 40
    top = d._encabezado(c, b) + 8
    x_izq, x_der = 30.0, 30.0 + ancho_util
    y = top
    for n, (r, entradas, salidas, me, ms) in enumerate(partes, 1):
        if r.get("comment"):
            c.t(x_izq + 6, y + 12, str(r["comment"]), size=9.5, color="textMuted", fuente=d.SANS)
            y += 16
        linea_y = y + 26
        c.t(x_izq - 10, linea_y + 4, str(n), size=10, peso=700, color="textSub", ancla="end")
        _dibujar_serie(c, entradas, x_izq, linea_y, x_der - x_izq - ms[0])
        _dibujar_serie(c, salidas, x_der - ms[0], linea_y, ms[0])
        y += max(me[1], ms[1]) + 6
    c.linea(x_izq, top, x_izq, y, color="strokeMain", ancho=3, flecha=None)
    c.linea(x_der, top, x_der, y, color="strokeMain", ancho=3, flecha=None)
    return x_der + 10, y + 4


# --- GRAFCET -------------------------------------------------------------------------------------------

_ETAPA, _ENLACE = 34, 18


def _medir_grafcet(seq: list) -> tuple[float, float, float]:
    """(izquierda, derecha, alto) de una secuencia, con el eje en x = 0."""
    izq, der, alto = _ETAPA / 2, _ETAPA / 2, 0.0
    for i, e in enumerate(seq):
        if i:
            alto += _ENLACE
        if "step" in e:
            acciones = e.get("actions") or []
            ancho_acc = sum(max(70, d._ancho_texto(a, 10) + 18) for a in acciones) + (24 if acciones else 0)
            der = max(der, _ETAPA / 2 + ancho_acc)
            alto += _ETAPA
        elif "transition" in e:
            der = max(der, 18 + d._ancho_texto(e.get("transition") or "XXXXXXXX", 10))
            alto += 4
        elif "or" in e or "and" in e:
            ramas = [_medir_grafcet(r) for r in (e.get("or") or e.get("and"))]
            ancho_total = sum(l + r for l, r, _ in ramas) + 30 * (len(ramas) - 1)
            izq = max(izq, ramas[0][0])
            der = max(der, ancho_total - ramas[0][0])
            alto += max(h for _, _, h in ramas) + 2 * (12 if "and" in e else 6)
        else:
            raise d.ErrorDiagrama(f"grafcet: elemento desconocido {e!r} (step, transition, or, and)")
    return izq, der, alto


def _dibujar_grafcet(c: d._Lienzo, seq: list, x: float, y: float) -> float:
    pal = c.pal
    for i, e in enumerate(seq):
        if i:
            c.linea(x, y, x, y + _ENLACE, color="strokeMain", ancho=1.5, flecha=None)
            y += _ENLACE
        if "step" in e:
            s = _ETAPA
            c.r(x - s / 2, y, s, s, trazo=1.6)
            if e.get("initial"):
                c.add(f'<rect x="{x - s / 2 + 4:.1f}" y="{y + 4:.1f}" width="{s - 8}" height="{s - 8}" fill="none" '
                      f'stroke="{pal["strokeMain"]}" stroke-width="1.2"/>')
            if e.get("blank"):
                c.vacio(x - 8, x + 8, y + s / 2 + 6)
            else:
                c.t(x, y + s / 2 + 4, str(e["step"]), size=11, peso=700, ancla="middle")
            ax = x + s / 2
            acciones = e.get("actions") or []
            if acciones:
                c.linea(ax, y + s / 2, ax + 24, y + s / 2, color="strokeMain", ancho=1.2, flecha=None)
                ax += 24
                for accion in acciones:
                    w = max(70, d._ancho_texto(accion, 10) + 18)
                    c.r(ax, y + 4, w, s - 8, trazo=1.2)
                    if accion:
                        c.t(ax + w / 2, y + s / 2 + 4, accion, size=10, ancla="middle")
                    else:
                        c.vacio(ax + 8, ax + w - 8, y + s / 2 + 5)
                    ax += w
            y += s
        elif "transition" in e:
            c.linea(x - 10, y + 2, x + 10, y + 2, color="strokeMain", ancho=3, flecha=None)
            texto = e.get("transition")
            if e.get("blank") or not texto:
                c.vacio(x + 16, x + 90, y + 6)
            else:
                c.t(x + 16, y + 6, str(texto), size=10)
            y += 4
        else:
            y_ini = y
            doble = "and" in e
            ramas = e.get("or") or e.get("and")
            medidas = [_medir_grafcet(r) for r in ramas]
            ejes, cx = [], x
            for k, (l, _r, _) in enumerate(medidas):
                if k:
                    cx += medidas[k - 1][1] + 30 + l
                ejes.append(cx)
            sep = 12 if doble else 6

            def barra(yb: float, doble: bool = doble, ejes: list = ejes) -> None:
                for dy in ((-2, 2) if doble else (0,)):
                    c.linea(ejes[0], yb + dy, ejes[-1], yb + dy, color="strokeMain", ancho=1.5, flecha=None)

            barra(y)
            fines = []
            for ex, rama in zip(ejes, ramas, strict=True):
                c.linea(ex, y, ex, y + sep, color="strokeMain", ancho=1.5, flecha=None)
                fines.append(_dibujar_grafcet(c, rama, ex, y + sep))
            y_fin = max(fines) + sep
            for ex, f in zip(ejes, fines, strict=True):
                c.linea(ex, f, ex, y_fin, color="strokeMain", ancho=1.5, flecha=None)
            barra(y_fin)
            y = y_fin
            _ = y_ini
    return y


@_errores
def _grafcet(c: d._Lienzo, b: dict) -> Punto:
    seq = b.get("steps")
    if not isinstance(seq, list) or not seq:
        raise d.ErrorDiagrama("grafcet: 'steps' tiene que ser una lista de step, transition, or y and")
    izq, der, _ = _medir_grafcet(seq)
    top = d._encabezado(c, b) + 18
    x = izq + 34
    fin = _dibujar_grafcet(c, seq, x, top)
    if b.get("loop", True):
        retorno = x - izq - 22
        c.add(f'<path d="M {x:.1f} {fin:.1f} L {x:.1f} {fin + 16:.1f} L {retorno:.1f} {fin + 16:.1f} L {retorno:.1f} '
              f'{top - 12:.1f} L {x:.1f} {top - 12:.1f} L {x:.1f} {top:.1f}" fill="none" stroke="{c.pal["strokeMain"]}" '
              f'stroke-width="1.5" marker-end="url(#flecha-main-{c.sufijo})"/>')
        fin += 16
    return x + der + 10, fin + 10


RENDERIZADORES: dict[str, Callable[[d._Lienzo, dict], Punto]] = {
    "block_diagram": _bloques, "time_response": _respuesta, "bode": _bode, "nyquist": _nyquist,
    "pole_zero": _polos_ceros, "root_locus": _lugar, "instrumentation": _instrumentacion, "ladder": _escalera,
    "grafcet": _grafcet,
}
