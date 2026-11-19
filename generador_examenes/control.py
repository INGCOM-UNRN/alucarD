"""Cuentas de control de procesos para los diagramas: funciones de transferencia, raíces, respuesta en
frecuencia y simulación en el tiempo, sin numpy.

Un sistema se escribe de cualquiera de estas formas (todas con `delay`, el tiempo muerto, opcional):

- `{num: [1], den: [1, 3, 2]}`: coeficientes en `s`, de la mayor potencia a la menor.
- `{gain: 2, tau: 5}`: primer orden, `K / (τs + 1)`.
- `{gain: 1, zeta: 0.3, wn: 2}`: segundo orden, `K ωn² / (s² + 2ζωn s + ωn²)`.
- `{k: 10, poles: [-1, -2, [-1, 3]], zeros: [-5]}`: ceros, polos y ganancia; `[re, im]` es un par
  complejo (el conjugado se agrega solo).
- `{kp: 2, ki: 0.5, kd: 0.1}`: un controlador PID (sólo como `controller` de un lazo cerrado).
"""

from __future__ import annotations

import cmath
import itertools
import math
from dataclasses import dataclass, field
from typing import Any


class ErrorControl(ValueError):
    pass


# --- Polinomios (coeficientes de la mayor potencia a la menor) ----------------------------------------

def recortar(p: list[complex]) -> list[complex]:
    i = 0
    while i < len(p) - 1 and abs(p[i]) < 1e-14:
        i += 1
    return list(p[i:]) or [0]


def mul(a: list, b: list) -> list:
    salida = [0j] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            salida[i + j] += x * y
    return salida


def suma(a: list, b: list) -> list:
    n = max(len(a), len(b))
    a, b = [0] * (n - len(a)) + list(a), [0] * (n - len(b)) + list(b)
    return recortar([x + y for x, y in zip(a, b, strict=True)])


def evaluar(p: list, s: complex) -> complex:
    valor = 0j
    for coef in p:
        valor = valor * s + coef
    return valor


def de_raices(raices: list[complex], k: complex = 1) -> list[complex]:
    p: list = [k]
    for r in raices:
        p = mul(p, [1, -r])
    return p


def raices(p: list) -> list[complex]:
    """Las raíces de `p` (Durand-Kerner, con un pulido de Newton)."""
    p = recortar([complex(c) for c in p])
    n = len(p) - 1
    if n < 1:
        return []
    ceros = 0
    while n > 0 and abs(p[-1]) < 1e-14:  # raíces en el origen, exactas
        p, n, ceros = p[:-1], n - 1, ceros + 1
    salida = [0j] * ceros
    if n == 0:
        return salida
    monico = [c / p[0] for c in p]
    radio = 1 + max(abs(c) for c in monico[1:])
    z = [radio * cmath.exp(2j * math.pi * (k + 0.25) / n) for k in range(n)]
    for _ in range(500):
        maximo = 0.0
        for i in range(n):
            den = 1 + 0j
            for j in range(n):
                if i != j:
                    den *= z[i] - z[j]
            if den == 0:
                den = 1e-12
            delta = evaluar(monico, z[i]) / den
            z[i] -= delta
            maximo = max(maximo, abs(delta))
        if maximo < 1e-13 * radio:
            break
    derivada = [c * (n - i) for i, c in enumerate(monico[:-1])]
    for i in range(n):
        for _ in range(3):
            d = evaluar(derivada, z[i])
            if abs(d) > 1e-14:
                z[i] -= evaluar(monico, z[i]) / d
    for r in z:
        salida.append(complex(r.real, 0.0) if abs(r.imag) < 1e-7 * max(1, abs(r)) else r)
    return sorted(salida, key=lambda r: (r.real, r.imag))


# --- Sistemas -----------------------------------------------------------------------------------------

@dataclass
class Sistema:
    num: list[complex]
    den: list[complex]
    delay: float = 0.0
    etiqueta: str = ""
    pid: tuple[float, float, float] | None = None   # (kp, ki, kd) de un controlador

    def __call__(self, s: complex) -> complex:
        return evaluar(self.num, s) / evaluar(self.den, s) * cmath.exp(-s * self.delay)

    @property
    def ceros(self) -> list[complex]:
        return raices(self.num)

    @property
    def polos(self) -> list[complex]:
        return raices(self.den)

    @property
    def ganancia_estatica(self) -> float | None:
        d = evaluar(self.den, 0)
        return None if abs(d) < 1e-12 else (evaluar(self.num, 0) / d).real

    def serie(self, otro: Sistema) -> Sistema:
        return Sistema(mul(self.num, otro.num), mul(self.den, otro.den), self.delay + otro.delay)


def _numero(valor: Any, donde: str) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorControl(f"{donde}: {valor!r} tiene que ser un número")
    return float(valor)


def _coeficientes(valor: Any, donde: str) -> list[complex]:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        valor = [valor]
    if not isinstance(valor, list) or not valor:
        raise ErrorControl(f"{donde}: tiene que ser una lista de coeficientes, como [1, 3, 2]")
    p = recortar([complex(_numero(v, donde)) for v in valor])
    if all(abs(c) < 1e-14 for c in p):
        raise ErrorControl(f"{donde}: es el polinomio nulo")
    return p


def _raices_de(valor: Any, donde: str) -> list[complex]:
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise ErrorControl(f"{donde}: tiene que ser una lista, como [-1, [-2, 3]]")
    salida = []
    for r in valor:
        if isinstance(r, list):
            if len(r) != 2:
                raise ErrorControl(f"{donde}: un par complejo es [real, imaginaria]: {r!r}")
            re_, im = _numero(r[0], donde), _numero(r[1], donde)
            salida += [complex(re_, abs(im)), complex(re_, -abs(im))] if im else [complex(re_, 0)]
        else:
            salida.append(complex(_numero(r, donde), 0))
    return salida


def sistema(dato: Any, donde: str = "system") -> Sistema:
    if isinstance(dato, (int, float)) and not isinstance(dato, bool):
        return Sistema([complex(dato)], [1 + 0j])
    if not isinstance(dato, dict):
        raise ErrorControl(f"{donde}: tiene que ser un diccionario (num/den, gain/tau, gain/zeta/wn, k/poles/zeros "
                           "o kp/ki/kd)")
    delay = _numero(dato.get("delay", 0), f"{donde}.delay")
    if delay < 0:
        raise ErrorControl(f"{donde}.delay: el tiempo muerto no puede ser negativo")
    etiqueta = str(dato.get("label") or "")
    if "num" in dato or "den" in dato:
        s = Sistema(_coeficientes(dato.get("num", [1]), f"{donde}.num"), _coeficientes(dato.get("den"), f"{donde}.den"))
    elif "tau" in dato:
        tau = _numero(dato["tau"], f"{donde}.tau")
        if tau <= 0:
            raise ErrorControl(f"{donde}.tau: tiene que ser positiva")
        s = Sistema([complex(_numero(dato.get("gain", 1), f"{donde}.gain"))], [complex(tau), 1 + 0j])
    elif "zeta" in dato or "wn" in dato:
        zeta, wn = _numero(dato.get("zeta", 1), f"{donde}.zeta"), _numero(dato.get("wn", 1), f"{donde}.wn")
        if wn <= 0 or zeta < 0:
            raise ErrorControl(f"{donde}: wn tiene que ser positiva y zeta no negativa")
        k = _numero(dato.get("gain", 1), f"{donde}.gain")
        s = Sistema([complex(k * wn * wn)], [1 + 0j, complex(2 * zeta * wn), complex(wn * wn)])
    elif "poles" in dato or "zeros" in dato:
        k = _numero(dato.get("k", 1), f"{donde}.k")
        s = Sistema(de_raices(_raices_de(dato.get("zeros"), f"{donde}.zeros"), k),
                    de_raices(_raices_de(dato.get("poles"), f"{donde}.poles")))
        s.num = [complex(round(c.real, 12), 0) for c in s.num]
        s.den = [complex(round(c.real, 12), 0) for c in s.den]
    elif any(k in dato for k in ("kp", "ki", "kd")):
        kp, ki, kd = (_numero(dato.get(k, 0), f"{donde}.{k}") for k in ("kp", "ki", "kd"))
        s = Sistema(recortar([complex(kd), complex(kp), complex(ki)]), [1 + 0j, 0j] if ki else [1 + 0j])
        if not ki:
            s.num = recortar([complex(kd), complex(kp)])
        s.pid = (kp, ki, kd)
    else:
        raise ErrorControl(f"{donde}: falta num/den, gain/tau, gain/zeta/wn, k/poles/zeros o kp/ki/kd")
    s.delay, s.etiqueta = delay, etiqueta
    return s


@dataclass
class Lazo:
    """Un lazo cerrado: controlador, planta, sensor (realimentación) y signo."""
    planta: Sistema
    controlador: Sistema = field(default_factory=lambda: Sistema([1 + 0j], [1 + 0j]))
    sensor: Sistema = field(default_factory=lambda: Sistema([1 + 0j], [1 + 0j]))
    signo: int = -1
    etiqueta: str = ""

    @property
    def abierto(self) -> Sistema:
        """L(s) = C(s) G(s) H(s)."""
        return self.controlador.serie(self.planta).serie(self.sensor)

    def cerrado(self) -> Sistema:
        """T(s) = C G / (1 ∓ C G H), sin tiempo muerto (con tiempo muerto se simula)."""
        cg = self.controlador.serie(self.planta)
        h = self.sensor
        num = mul(cg.num, h.den)
        den = suma(mul(cg.den, h.den), [-self.signo * c for c in mul(cg.num, h.num)])
        return Sistema(recortar(num), recortar(den))


def lazo(dato: Any, donde: str = "closedLoop") -> Lazo:
    if not isinstance(dato, dict) or "plant" not in dato:
        raise ErrorControl(f"{donde}: tiene que tener plant (y opcionalmente controller, feedback y sign)")
    signo = dato.get("sign", "-")
    if signo not in ("-", "+"):
        raise ErrorControl(f"{donde}.sign: es '-' (realimentación negativa) o '+'")
    return Lazo(planta=sistema(dato["plant"], f"{donde}.plant"),
                controlador=sistema(dato.get("controller", 1), f"{donde}.controller"),
                sensor=sistema(dato.get("feedback", 1), f"{donde}.feedback"),
                signo=-1 if signo == "-" else 1, etiqueta=str(dato.get("label") or ""))


def abierto_de(b: dict, donde: str = "system") -> Sistema:
    """El sistema de un bloque de frecuencia: `system`, o el lazo abierto L(s) de `closedLoop`."""
    if "closedLoop" in b:
        return lazo(b["closedLoop"]).abierto
    if "system" not in b:
        raise ErrorControl(f"falta {donde} (o closedLoop)")
    return sistema(b["system"], donde)


# --- Simulación en el tiempo --------------------------------------------------------------------------

class _Estado:
    """Un sistema propio en forma canónica controlable, integrado con RK4 y entrada constante en cada paso."""

    def __init__(self, s: Sistema, dt: float):
        num, den = recortar(s.num), recortar(s.den)
        if len(num) > len(den):
            raise ErrorControl("el sistema es impropio (más ceros que polos): no se puede simular")
        a0 = den[0]
        den = [(c / a0).real for c in den]
        num = [(c / a0).real for c in num]
        n = len(den) - 1
        num = [0.0] * (n + 1 - len(num)) + num
        self.d = num[0]
        self.c = [num[i + 1] - num[0] * den[i + 1] for i in range(n)][::-1]   # para x1..xn
        self.a = [-den[i] for i in range(n, 0, -1)]                            # a0..a(n-1) de la última fila
        self.x = [0.0] * n
        self.dt = dt
        self.atraso = [0.0] * max(0, round(s.delay / dt))

    def _f(self, x: list[float], u: float) -> list[float]:
        n = len(x)
        if not n:
            return []
        dx = x[1:] + [sum(a * xi for a, xi in zip(self.a, x, strict=True)) + u]
        return dx

    def salida(self, u: float) -> float:
        return sum(c * xi for c, xi in zip(self.c, self.x, strict=True)) + self.d * u

    def paso(self, u: float) -> float:
        """Avanza un paso con la entrada `u` (antes del tiempo muerto) y devuelve la salida al empezar."""
        if self.atraso:
            self.atraso.append(u)
            u = self.atraso.pop(0)
        y = self.salida(u)
        x, h = self.x, self.dt
        if x:
            k1 = self._f(x, u)
            k2 = self._f([xi + h / 2 * k for xi, k in zip(x, k1, strict=True)], u)
            k3 = self._f([xi + h / 2 * k for xi, k in zip(x, k2, strict=True)], u)
            k4 = self._f([xi + h * k for xi, k in zip(x, k3, strict=True)], u)
            self.x = [xi + h / 6 * (a + 2 * b + 2 * c + d) for xi, a, b, c, d in zip(x, k1, k2, k3, k4, strict=True)]
        return y


def entrada(tipo: str, amplitud: float, t: float, dt: float) -> float:
    if tipo == "step":
        return amplitud
    if tipo == "ramp":
        return amplitud * t
    if tipo == "impulse":
        return amplitud / dt if t < dt / 2 else 0.0
    raise ErrorControl(f"input: {tipo!r} es step, ramp o impulse")


def simular_abierto(s: Sistema, t_fin: float, tipo: str = "step", amplitud: float = 1.0,
                    pasos: int = 3000) -> tuple[list[float], list[float], list[float]]:
    dt = t_fin / pasos
    estado = _Estado(s, dt)
    ts, us, ys = [], [], []
    for i in range(pasos + 1):
        t = i * dt
        u = entrada(tipo, amplitud, t, dt)
        ts.append(t)
        us.append(u if tipo != "impulse" else 0.0)
        ys.append(estado.paso(u))
    return ts, us, ys


def simular_lazo(lz: Lazo, t_fin: float, tipo: str = "step", amplitud: float = 1.0, perturbacion: dict | None = None,
                 pasos: int = 4000) -> tuple[list[float], list[float], list[float], list[float]]:
    """La respuesta del lazo cerrado: (t, referencia, salida, acción de control). Un PID se simula
    discreto, con el derivativo filtrado (N = 10)."""
    dt = t_fin / pasos
    planta, sensor = _Estado(lz.planta, dt), _Estado(lz.sensor, dt)
    controlador = None if lz.controlador.pid else _Estado(lz.controlador, dt)
    kp, ki, kd = lz.controlador.pid or (0.0, 0.0, 0.0)
    tf = kd / (10 * kp) if kd and kp else (kd / 10 if kd else 0.0)
    integral, derivada, e_ant = 0.0, 0.0, 0.0
    d_t = float((perturbacion or {}).get("at", 0.0))
    d_a = float((perturbacion or {}).get("amplitude", 0.0))
    d_en = (perturbacion or {}).get("where", "output")
    ts, rs, ys, us = [], [], [], []
    y = 0.0
    for i in range(pasos + 1):
        t = i * dt
        r = entrada(tipo, amplitud, t, dt)
        medida = sensor.paso(y)
        e = r + lz.signo * medida
        if controlador is None:
            integral += e * dt
            if tf:
                derivada += dt / (tf + dt) * ((e - e_ant) / dt - derivada) if i else 0.0
            else:
                derivada = (e - e_ant) / dt if i else 0.0
            u = kp * e + ki * integral + kd * derivada
            e_ant = e
        else:
            u = controlador.paso(e)
        d = d_a if perturbacion and t >= d_t else 0.0
        y = planta.paso(u + (d if d_en == "input" else 0.0)) + (d if d_en == "output" else 0.0)
        ts.append(t)
        rs.append(r if tipo != "impulse" else 0.0)
        ys.append(y)
        us.append(u)
    return ts, rs, ys, us


# --- Características de la respuesta --------------------------------------------------------------------

def caracteristicas(ts: list[float], ys: list[float], final: float | None = None, banda: float = 0.02,
                    inicial: float = 0.0) -> dict[str, float | None]:
    """Valor final, sobrepico (%), tiempo de pico, de subida (10-90 %), de establecimiento, y el tiempo
    muerto y la constante de tiempo aparentes (63,2 %)."""
    final = ys[-1] if final is None else final
    cambio = final - inicial
    salida: dict[str, float | None] = {"final": final, "overshoot": None, "peak": None, "rise": None,
                                          "settling": None, "tau": None, "delay": None}
    if abs(cambio) < 1e-12:
        return salida
    signo = 1 if cambio > 0 else -1
    i_pico = max(range(len(ys)), key=lambda i: signo * ys[i])
    exceso = (ys[i_pico] - final) / cambio * 100
    if exceso > 0.05:
        salida["overshoot"], salida["peak"] = exceso, ts[i_pico]

    def cruce(fraccion: float) -> float | None:
        objetivo = inicial + fraccion * cambio
        for i in range(1, len(ys)):
            if signo * (ys[i] - objetivo) >= 0:
                y0, y1 = ys[i - 1], ys[i]
                f = (objetivo - y0) / (y1 - y0) if y1 != y0 else 0
                return ts[i - 1] + f * (ts[i] - ts[i - 1])
        return None

    t10, t90 = cruce(0.1), cruce(0.9)
    if t10 is not None and t90 is not None:
        salida["rise"] = t90 - t10
    tolerancia = banda * abs(cambio)
    fuera = [i for i, y in enumerate(ys) if abs(y - final) > tolerancia]
    if not fuera:
        salida["settling"] = 0.0
    elif fuera[-1] < len(ys) - 1:
        salida["settling"] = ts[fuera[-1] + 1]
    inicio = next((ts[i] for i, y in enumerate(ys) if abs(y - inicial) > 1e-4 * abs(cambio)), None)
    salida["delay"] = inicio
    t632 = cruce(0.632)
    if t632 is not None and inicio is not None:
        salida["tau"] = t632 - inicio
    return salida


def tangente_inflexion(ts: list[float], ys: list[float], final: float, inicial: float = 0.0) -> dict | None:
    """La tangente en el punto de máxima pendiente (método de la curva de reacción): L, T y el punto."""
    pendientes = [(ys[i + 1] - ys[i - 1]) / (ts[i + 1] - ts[i - 1]) for i in range(1, len(ys) - 1)]
    if not pendientes:
        return None
    signo = 1 if final >= inicial else -1
    i = max(range(len(pendientes)), key=lambda k: signo * pendientes[k]) + 1
    m = pendientes[i - 1]
    if abs(m) < 1e-12:
        return None
    t_l = ts[i] + (inicial - ys[i]) / m
    t_f = ts[i] + (final - ys[i]) / m
    return {"t": ts[i], "y": ys[i], "slope": m, "L": t_l, "T": t_f - t_l}


# --- Frecuencia -------------------------------------------------------------------------------------------

def fase_continua(s: Sistema, w: float) -> float:
    """La fase en grados, sumando cada cero, polo y el tiempo muerto: sin saltos de ±360°."""
    total = 0.0
    k = s.num[0] / s.den[0]
    total += math.degrees(cmath.phase(k)) if abs(k.imag) > 1e-14 or k.real < 0 else 0.0
    for z in s.ceros:
        total += math.degrees(cmath.phase(1j * w - z)) if abs(z) > 1e-12 else 90.0
    for p in s.polos:
        total -= math.degrees(cmath.phase(1j * w - p)) if abs(p) > 1e-12 else 90.0
    return total - math.degrees(w * s.delay)


def magnitud_db(s: Sistema, w: float) -> float:
    return 20 * math.log10(max(abs(s(1j * w)), 1e-300))


def asintota_db(s: Sistema, w: float) -> float:
    """La aproximación por rectas de Bode: cada raíz no nula quiebra en |r| (±20 dB/década)."""
    k = abs(s.num[0] / s.den[0])
    total = 20 * math.log10(k) if k > 0 else -300.0
    for signo, lista in ((1, s.ceros), (-1, s.polos)):
        for r in lista:
            if abs(r) < 1e-12:
                total += signo * 20 * math.log10(w)
            else:
                total += signo * 20 * math.log10(max(w, abs(r)))
    return total


def rango_frecuencias(s: Sistema) -> tuple[float, float]:
    quiebres = [abs(r) for r in s.ceros + s.polos if abs(r) > 1e-12]
    if s.delay:
        quiebres.append(1 / s.delay)
    if not quiebres:
        return 0.01, 100.0
    return 10 ** math.floor(math.log10(min(quiebres)) - 1), 10 ** math.ceil(math.log10(max(quiebres)) + 1)


def _bisectar(f, a: float, b: float) -> float:
    fa = f(a)
    for _ in range(80):
        m = math.sqrt(a * b)
        fm = f(m)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
    return math.sqrt(a * b)


def margenes(s: Sistema, w_min: float, w_max: float) -> dict[str, float | None]:
    """Margen de ganancia (dB) y de fase (°), con sus frecuencias de cruce."""
    ws = [w_min * (w_max / w_min) ** (k / 800) for k in range(801)]
    salida: dict[str, float | None] = {"gm": None, "w180": None, "pm": None, "wc": None}
    mags = [magnitud_db(s, w) for w in ws]
    for a, b, ma, mb in zip(ws, ws[1:], mags, mags[1:], strict=False):
        if (ma > 0) != (mb > 0):
            wc = _bisectar(lambda w: magnitud_db(s, w), a, b)
            salida["wc"], salida["pm"] = wc, 180 + fase_continua(s, wc)
            break
    fases = [fase_continua(s, w) + 180 for w in ws]
    for a, b, fa, fb in zip(ws, ws[1:], fases, fases[1:], strict=False):
        if (fa > 0) != (fb > 0):
            w180 = _bisectar(lambda w: fase_continua(s, w) + 180, a, b)
            salida["w180"], salida["gm"] = w180, -magnitud_db(s, w180)
            break
    return salida


# --- Lugar de las raíces -----------------------------------------------------------------------------------

def lugar_raices(s: Sistema, k_max: float, muestras: int = 400) -> tuple[list[float], list[list[complex]]]:
    """Las raíces de den(s) + K num(s) para K de 0 a `k_max` (más densas cerca de 0), en ramas continuas."""
    ks = [k_max * (i / muestras) ** 2 for i in range(muestras + 1)]
    ramas: list[list[complex]] = []
    anterior: list[complex] | None = None
    for k in ks:
        actuales = raices(suma(s.den, [k * c for c in s.num]))
        if anterior is None:
            orden = actuales
        else:
            orden, libres = [], list(actuales)
            for r in anterior:
                j = min(range(len(libres)), key=lambda i: abs(libres[i] - r))
                orden.append(libres.pop(j))
        anterior = orden
        ramas.append(orden)
    return ks, [list(rama) for rama in zip(*ramas, strict=True)]


def asintotas(s: Sistema) -> tuple[float | None, list[float]]:
    """El centroide y los ángulos (°) de las asíntotas del lugar de las raíces."""
    n, m = len(s.polos), len(s.ceros)
    if n <= m:
        return None, []
    centro = (sum(p.real for p in s.polos) - sum(z.real for z in s.ceros)) / (n - m)
    return centro, [180 * (2 * q + 1) / (n - m) for q in range(n - m)]


def cruce_imaginario(s: Sistema, k_max: float) -> tuple[float, float] | None:
    """El primer K (y la frecuencia) en que una rama cruza al semiplano derecho."""
    ks = [k_max * (i / 2000) for i in range(2001)]

    def mayor_real(k: float) -> float:
        return max(r.real for r in raices(suma(s.den, [k * c for c in s.num])))

    previo = mayor_real(0)
    for a, b in itertools.pairwise(ks):
        actual = mayor_real(b)
        if previo < 0 <= actual:
            lo, hi = a, b
            for _ in range(60):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if mayor_real(mid) < 0 else (lo, mid)
            w = max(abs(r.imag) for r in raices(suma(s.den, [hi * c for c in s.num])) if abs(r.real) < 1e-3 * max(1, abs(r)) + 1e-6) \
                if any(abs(r.real) < 1e-3 * max(1, abs(r)) + 1e-6 for r in raices(suma(s.den, [hi * c for c in s.num]))) else 0.0
            return hi, w
        previo = actual
    return None
