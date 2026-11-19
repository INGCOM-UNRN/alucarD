"""Cuentas de química para los diagramas, sin dependencias: configuraciones electrónicas, orbitales
moleculares de diatómicas, curvas de titulación y fracciones de especies, cinética, diagramas de fases,
curvas de calentamiento, pilas, celdas unidad y multipletes de RMN.

Así, lo que muestra cada dibujo (el pH en la equivalencia, el orden de enlace, la E de la pila) sale de
la teoría y no de lo que alguien copió a mano.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

R = 8.314462618                   # J/(mol·K)
F = 96485.33212                   # C/mol
NA = 6.02214076e23
KW = 1e-14                        # a 25 °C


class ErrorQuimica(ValueError):
    pass


def _num(valor: Any, donde: str, positivo: bool = False, minimo: float | None = None) -> float:
    try:
        x = float(valor)
    except (TypeError, ValueError):
        raise ErrorQuimica(f"{donde}: {valor!r} no es un número") from None
    if not math.isfinite(x):
        raise ErrorQuimica(f"{donde}: tiene que ser un número finito")
    if positivo and x <= 0:
        raise ErrorQuimica(f"{donde}: tiene que ser positivo")
    if minimo is not None and x < minimo:
        raise ErrorQuimica(f"{donde}: tiene que ser al menos {minimo:g}")
    return x


def _lista(valor: Any) -> list:
    if valor is None:
        return []
    return list(valor) if isinstance(valor, (list, tuple)) else [valor]


# --- Elementos y configuraciones electrónicas -------------------------------------------------------------

SIMBOLOS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb "
    "Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf "
    "Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og").split()
Z_DE = {s: i + 1 for i, s in enumerate(SIMBOLOS)}
GASES_NOBLES = (("He", 2), ("Ne", 10), ("Ar", 18), ("Kr", 36), ("Xe", 54), ("Rn", 86))
# Electronegatividad de Pauling, para ordenar los orbitales atómicos de una diatómica heteronuclear.
ELECTRONEGATIVIDAD = {"H": 2.20, "He": 0, "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55, "N": 3.04, "O": 3.44,
                      "F": 3.98, "Ne": 0, "Na": 0.93, "Mg": 1.31, "Al": 1.61, "Si": 1.90, "P": 2.19, "S": 2.58,
                      "Cl": 3.16, "Ar": 0}

LETRAS = "spdf"
# El orden de llenado (regla de Madelung, n + l y después n).
SUBNIVELES = sorted(((n, ll) for n in range(1, 8) for ll in range(4) if ll < n), key=lambda nl: (nl[0] + nl[1], nl[0]))
# Las excepciones que se enseñan: un electrón s pasa al d para completarlo o dejarlo a medias.
EXCEPCIONES = {"Cr": {(4, 0): 1, (3, 2): 5}, "Cu": {(4, 0): 1, (3, 2): 10}, "Nb": {(5, 0): 1, (4, 2): 4},
               "Mo": {(5, 0): 1, (4, 2): 5}, "Ru": {(5, 0): 1, (4, 2): 7}, "Rh": {(5, 0): 1, (4, 2): 8},
               "Pd": {(5, 0): 0, (4, 2): 10}, "Ag": {(5, 0): 1, (4, 2): 10}, "Pt": {(6, 0): 1, (5, 2): 9},
               "Au": {(6, 0): 1, (5, 2): 10}}


def nombre_subnivel(nl: tuple[int, int]) -> str:
    return f"{nl[0]}{LETRAS[nl[1]]}"


def capacidad(nl: tuple[int, int]) -> int:
    return 2 * (2 * nl[1] + 1)


def numero_atomico(elemento: Any) -> int:
    if isinstance(elemento, int) and not isinstance(elemento, bool):
        z = elemento
    else:
        texto = str(elemento).strip()
        if texto.isdigit():
            z = int(texto)
        elif texto in Z_DE:
            z = Z_DE[texto]
        else:
            raise ErrorQuimica(f"elemento desconocido: {elemento!r}")
    if not 1 <= z <= len(SIMBOLOS):
        raise ErrorQuimica(f"número atómico fuera de rango: {z}")
    return z


@dataclass
class Configuracion:
    simbolo: str
    z: int
    carga: int
    ocupacion: dict[tuple[int, int], int]          # en orden de llenado

    @property
    def electrones(self) -> int:
        return sum(self.ocupacion.values())

    def texto(self, nucleo: bool = False) -> str:
        """`1s² 2s² 2p⁴`, o con el gas noble anterior entre corchetes: `[He] 2s² 2p⁴`."""
        partes = [(nl, e) for nl, e in self.ocupacion.items() if e]
        prefijo = ""
        if nucleo:
            gas = self.nucleo()
            if gas:
                prefijo = f"[{gas[0]}] "
                partes = [(nl, e) for nl, e in partes if nl not in gas[1]]
        return prefijo + " ".join(f"{nombre_subnivel(nl)}{superindice(e)}" for nl, e in partes)

    def nucleo(self) -> tuple[str, set[tuple[int, int]]] | None:
        """El gas noble anterior y sus subniveles (los del carozo)."""
        previo = None
        for simbolo, z in GASES_NOBLES:
            if z < self.z and z <= self.electrones:
                previo = (simbolo, z)
        if previo is None:
            return None
        llenos, cuenta = set(), 0
        for nl in SUBNIVELES:
            if cuenta >= previo[1]:
                break
            llenos.add(nl)
            cuenta += capacidad(nl)
        return previo[0], llenos

    def desapareados(self) -> int:
        total = 0
        for nl, e in self.ocupacion.items():
            cajas = 2 * nl[1] + 1
            total += e if e <= cajas else 2 * cajas - e
        return total


def superindice(n: int | str) -> str:
    tabla = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
    return str(n).translate(tabla)


def configuracion(elemento: Any, carga: int = 0) -> Configuracion:
    z = numero_atomico(elemento)
    simbolo = SIMBOLOS[z - 1]
    electrones = z - int(carga)
    if electrones < 0:
        raise ErrorQuimica(f"{simbolo} con carga {carga:+d} no tiene electrones")
    ocupacion: dict[tuple[int, int], int] = {}
    quedan = z
    for nl in SUBNIVELES:
        if quedan <= 0:
            break
        ocupacion[nl] = min(capacidad(nl), quedan)
        quedan -= ocupacion[nl]
    for nl, e in EXCEPCIONES.get(simbolo, {}).items():
        ocupacion[nl] = e
    if carga > 0:
        # Un catión pierde primero los electrones del n más alto (el 4s antes que el 3d).
        for _ in range(int(carga)):
            nl = max((k for k, e in ocupacion.items() if e), key=lambda k: (k[0], k[1]))
            ocupacion[nl] -= 1
    elif carga < 0:
        extra = -int(carga)
        for nl in SUBNIVELES:
            if extra == 0:
                break
            libre = capacidad(nl) - ocupacion.get(nl, 0)
            if libre > 0:
                pone = min(libre, extra)
                ocupacion[nl] = ocupacion.get(nl, 0) + pone
                extra -= pone
    ordenada = {nl: ocupacion[nl] for nl in SUBNIVELES if nl in ocupacion and (ocupacion[nl] or nl[1] == 0)}
    # Un subnivel que quedó vacío por una excepción o una carga se conserva sólo si no es el último.
    while ordenada and not list(ordenada.values())[-1]:
        ordenada.popitem()
    return Configuracion(simbolo, z, int(carga), ordenada)


def llenar_cajas(electrones: int, cajas: int) -> list[int]:
    """Regla de Hund: primero uno en cada caja (↑) y después se aparean (↑↓). 1 = ↑, 2 = ↑↓."""
    salida = [0] * cajas
    for i in range(electrones):
        salida[i % cajas] += 1
    return salida


# --- Orbitales moleculares de diatómicas ---------------------------------------------------------------

@dataclass
class NivelOM:
    nombre: str              # "σ2s", "π*2p"
    enlazante: bool
    degenerado: int          # 1 o 2 (los π)
    electrones: int = 0
    origen: str = "2p"       # de qué orbitales atómicos sale


@dataclass
class DiagramaOM:
    atomos: tuple[str, str]
    carga: int
    niveles: list[NivelOM]                  # de abajo hacia arriba
    electrones: int
    mezcla_sp: bool
    capa: int                               # 1 (H2, He2) o 2

    @property
    def orden_enlace(self) -> float:
        enl = sum(n.electrones for n in self.niveles if n.enlazante)
        anti = sum(n.electrones for n in self.niveles if not n.enlazante)
        return (enl - anti) / 2

    @property
    def desapareados(self) -> int:
        return sum(sum(1 for e in llenar_cajas(n.electrones, n.degenerado) if e == 1) for n in self.niveles)

    @property
    def magnetismo(self) -> str:
        return "paramagnética" if self.desapareados else "diamagnética"


def _electrones_de_valencia(simbolo: str) -> int:
    z = numero_atomico(simbolo)
    if z <= 2:
        return z
    if z <= 10:
        return z - 2
    raise ErrorQuimica(f"orbitales moleculares: sólo diatómicas de los dos primeros períodos ({simbolo} no)")


def orbitales_moleculares(atomos: Any, carga: int = 0) -> DiagramaOM:
    """Las diatómicas de H a Ne: niveles ordenados y llenos. Con mezcla s-p (hasta N2 o con hasta 10
    electrones de valencia), el π2p queda por debajo del σ2p."""
    lista = [str(a).strip() for a in _lista(atomos)]
    if len(lista) == 1:
        lista *= 2
    if len(lista) != 2:
        raise ErrorQuimica("orbitales moleculares: 'atoms' son los dos átomos de la diatómica")
    a, b = lista
    za, zb = numero_atomico(a), numero_atomico(b)
    capa = 1 if za <= 2 and zb <= 2 else 2
    if capa == 1:
        electrones = za + zb - carga
        niveles = [NivelOM("σ1s", True, 1, origen="1s"), NivelOM("σ*1s", False, 1, origen="1s")]
        mezcla = False
    else:
        if za <= 2 or zb <= 2:
            raise ErrorQuimica("orbitales moleculares: las dos capas tienen que ser la misma (H2 o N2, no NH)")
        electrones = _electrones_de_valencia(a) + _electrones_de_valencia(b) - carga
        mezcla = electrones <= 10
        pi, sigma = NivelOM("π2p", True, 2), NivelOM("σ2p", True, 1)
        niveles = [NivelOM("σ2s", True, 1, origen="2s"), NivelOM("σ*2s", False, 1, origen="2s"),
                   *((pi, sigma) if mezcla else (sigma, pi)), NivelOM("π*2p", False, 2), NivelOM("σ*2p", False, 1)]
    capacidad_total = sum(2 * n.degenerado for n in niveles)
    if not 0 <= electrones <= capacidad_total:
        raise ErrorQuimica(f"orbitales moleculares: {electrones} electrones no entran en los niveles")
    quedan = electrones
    for n in niveles:
        n.electrones = min(quedan, 2 * n.degenerado)
        quedan -= n.electrones
    return DiagramaOM((SIMBOLOS[za - 1], SIMBOLOS[zb - 1]), carga, niveles, electrones, mezcla, capa)


# --- Ácido-base: titulaciones y fracciones de especies ---------------------------------------------------

def fracciones(h: float, kas: list[float]) -> list[float]:
    """α_j de cada especie, de la más protonada (j = 0) a la menos (j = n)."""
    n = len(kas)
    terminos, producto = [], 1.0
    for j in range(n + 1):
        if j:
            producto *= kas[j - 1]
        terminos.append(h ** (n - j) * producto)
    total = sum(terminos)
    return [t / total for t in terminos]


@dataclass
class Analito:
    tipo: str                    # strong_acid, strong_base, weak_acid, weak_base
    conc: float
    volumen: float
    pkas: list[float] = field(default_factory=list)
    carga: int = 0               # la carga de la forma que se agrega (NH4+: 1; CO3 2-: -2)

    @property
    def es_acido(self) -> bool:
        return self.tipo in ("strong_acid", "weak_acid")

    @property
    def equivalentes(self) -> int:
        return len(self.pkas) if self.tipo.startswith("weak") else 1

    @property
    def z0(self) -> int:
        """La carga de la forma más protonada."""
        if self.tipo == "weak_acid":
            return self.carga
        return self.carga + len(self.pkas)


def analito(dato: Any) -> Analito:
    if not isinstance(dato, dict):
        raise ErrorQuimica("titration: 'analyte' es {kind, conc, volume, pKa}")
    tipo = str(dato.get("kind", "weak_acid"))
    if tipo not in ("strong_acid", "strong_base", "weak_acid", "weak_base"):
        raise ErrorQuimica(f"analyte.kind: {tipo!r} (vale strong_acid, strong_base, weak_acid o weak_base)")
    conc = _num(dato.get("conc", 0.1), "analyte.conc", positivo=True)
    volumen = _num(dato.get("volume", 25), "analyte.volume", positivo=True)
    pkas: list[float] = []
    if tipo.startswith("weak"):
        if "pKb" in dato and tipo == "weak_base":
            pkas = [14 - _num(p, "analyte.pKb") for p in _lista(dato["pKb"])]
        else:
            pkas = [_num(p, "analyte.pKa") for p in _lista(dato.get("pKa"))]
        if not pkas:
            raise ErrorQuimica(f"analyte: un {tipo} necesita pKa (o pKb)")
        pkas.sort()
    carga = int(dato.get("charge", 0))
    return Analito(tipo, conc, volumen, pkas, carga)


@dataclass
class Titulacion:
    analito: Analito
    titulante: float             # concentración del ácido o la base fuerte
    vmax: float
    volumenes: list[float]
    phs: list[float]
    equivalencias: list[tuple[float, float]]       # (V, pH) de las que se ven
    semi: list[tuple[float, float, float]]         # (V, pH, pKa) en la mitad de cada tramo

    @property
    def ph_inicial(self) -> float:
        return self.phs[0]


def ph_de(a: Analito, ct: float, vt: float) -> float:
    """El pH después de agregar `vt` mL del titulante (base fuerte si el analito es ácido; si no, ácido
    fuerte), por balance de cargas."""
    v = a.volumen + vt
    c_sist = a.conc * a.volumen / v
    c_tit = ct * vt / v
    kas = [10 ** -p for p in a.pkas]
    fijo = 0.0                                   # cationes − aniones espectadores
    fijo += c_tit if a.es_acido else -c_tit
    if a.tipo == "strong_acid":
        fijo -= c_sist
    elif a.tipo == "strong_base":
        fijo += c_sist
    else:
        agregada = a.carga if a.tipo == "weak_base" else a.z0
        fijo -= agregada * c_sist               # el contraión de la forma agregada

    def balance(log_h: float) -> float:
        h = 10 ** log_h
        carga = h - KW / h + fijo
        if kas:
            for j, alfa in enumerate(fracciones(h, kas)):
                carga += (a.z0 - j) * c_sist * alfa
        return carga

    lo, hi = -15.5, 1.5
    flo = balance(lo)
    for _ in range(200):
        medio = (lo + hi) / 2
        fm = balance(medio)
        if (fm > 0) == (flo > 0):
            lo, flo = medio, fm
        else:
            hi = medio
        if hi - lo < 1e-10:
            break
    return -(lo + hi) / 2


def titulacion(dato_analito: Any, conc_titulante: Any, vmax: Any = None, puntos: int = 400) -> Titulacion:
    a = analito(dato_analito)
    ct = _num(conc_titulante, "titrant.conc", positivo=True)
    veq = a.conc * a.volumen / ct
    vmax = _num(vmax, "vMax", positivo=True) if vmax is not None else veq * (a.equivalentes + 0.6)
    volumenes = [vmax * i / puntos for i in range(puntos + 1)]
    phs = [ph_de(a, ct, v) for v in volumenes]
    equivalencias, semi = [], []
    for k in range(1, a.equivalentes + 1):
        v = k * veq
        if v > vmax:
            break
        antes, despues = ph_de(a, ct, v * 0.97), ph_de(a, ct, v * 1.03)
        if abs(despues - antes) >= 1.0:          # un salto que se ve
            equivalencias.append((v, ph_de(a, ct, v)))
    if a.tipo.startswith("weak"):
        pkas = a.pkas if a.es_acido else list(reversed(a.pkas))
        for k, pka in enumerate(pkas):
            v = (k + 0.5) * veq
            if v <= vmax:
                semi.append((v, ph_de(a, ct, v), pka))
    return Titulacion(a, ct, vmax, volumenes, phs, equivalencias, semi)


# --- Cinética ------------------------------------------------------------------------------------------

def concentracion(orden: int, k: float, a0: float, t: float) -> float:
    if orden == 0:
        return max(a0 - k * t, 0.0)
    if orden == 1:
        return a0 * math.exp(-k * t)
    if orden == 2:
        return a0 / (1 + a0 * k * t)
    raise ErrorQuimica(f"kinetics: orden {orden} (vale 0, 1 o 2)")


def vida_media(orden: int, k: float, a0: float) -> float:
    return {0: a0 / (2 * k), 1: math.log(2) / k, 2: 1 / (k * a0)}[orden]


def consecutiva(k1: float, k2: float, a0: float, t: float) -> tuple[float, float, float]:
    """A → B → C."""
    a = a0 * math.exp(-k1 * t)
    if abs(k1 - k2) < 1e-12:
        b = a0 * k1 * t * math.exp(-k1 * t)
    else:
        b = a0 * k1 / (k2 - k1) * (math.exp(-k1 * t) - math.exp(-k2 * t))
    return a, b, a0 - a - b


def t_maximo_intermediario(k1: float, k2: float) -> float:
    return 1 / k1 if abs(k1 - k2) < 1e-12 else math.log(k2 / k1) / (k2 - k1)


def reversible(kf: float, kb: float, a0: float, t: float) -> tuple[float, float]:
    """A ⇌ B, empezando con A puro."""
    s = kf + kb
    a = a0 * (kb + kf * math.exp(-s * t)) / s
    return a, a0 - a


# --- Diagramas de fases ----------------------------------------------------------------------------------

SUSTANCIAS = {
    "water": {"name": "H2O", "triple": (273.16, 0.00604), "critical": (647.1, 217.7), "meltingSlope": -134.0,
              "normalMelting": 273.15, "normalBoiling": 373.15},
    "co2": {"name": "CO2", "triple": (216.55, 5.11), "critical": (304.13, 72.8), "meltingSlope": 40.0,
            "normalSublimation": 194.65},
}


def _interpolar_cc(anclas: list[tuple[float, float]], t: float) -> float:
    """ln P lineal en 1/T entre anclas (Clausius-Clapeyron por tramos), extrapolando en los extremos."""
    anclas = sorted(anclas)
    for (t0, p0), (t1, p1) in zip(anclas, anclas[1:]):
        if t <= t1 or (t1, p1) == anclas[-1]:
            b = math.log(p1 / p0) / (1 / t0 - 1 / t1)
            return math.exp(math.log(p0) - b * (1 / t - 1 / t0))
    return anclas[-1][1]


def _t_de_p_cc(anclas: list[tuple[float, float]], p: float) -> float:
    anclas = sorted(anclas)
    for (t0, p0), (t1, p1) in zip(anclas, anclas[1:]):
        if p <= p1 or (t1, p1) == anclas[-1]:
            b = math.log(p1 / p0) / (1 / t0 - 1 / t1)
            return 1 / (1 / t0 - math.log(p / p0) / b)
    return anclas[-1][0]


@dataclass
class Fases:
    nombre: str
    triple: tuple[float, float]
    critico: tuple[float, float]
    pendiente_fusion: float           # atm/K
    anclas_vap: list[tuple[float, float]]
    anclas_sub: list[tuple[float, float]]
    normales: dict[str, float]

    def p_vapor(self, t: float) -> float:
        return _interpolar_cc(self.anclas_vap, t)

    def p_sublimacion(self, t: float) -> float:
        return _interpolar_cc(self.anclas_sub, t)

    def t_fusion(self, p: float) -> float:
        return self.triple[0] + (p - self.triple[1]) / self.pendiente_fusion

    def t_de_p(self, p: float) -> tuple[str, float]:
        """A 1 atm (u otra p): dónde corta la frontera más baja: sublimación o ebullición."""
        if p < self.triple[1]:
            return "sublimación", _t_de_p_cc(self.anclas_sub, p)
        return "ebullición", _t_de_p_cc(self.anclas_vap, p)


def fases(dato: dict) -> Fases:
    base = dict(SUSTANCIAS.get(str(dato.get("substance", "")).lower(), {}))
    if dato.get("substance") and not base:
        raise ErrorQuimica(f"phase_diagram: sustancia {dato['substance']!r} (valen {', '.join(SUSTANCIAS)}; "
                           "si no, triple y critical)")
    base.update({k: v for k, v in dato.items() if k in ("triple", "critical", "meltingSlope", "name",
                                                         "normalMelting", "normalBoiling", "normalSublimation")})
    try:
        tt, pt = (float(x) for x in base["triple"])
        tc, pc = (float(x) for x in base["critical"])
    except (KeyError, TypeError, ValueError):
        raise ErrorQuimica("phase_diagram: faltan triple: [T, P] y critical: [T, P] (o substance)") from None
    if not (0 < tt < tc and 0 < pt < pc):
        raise ErrorQuimica("phase_diagram: el punto crítico tiene que estar arriba y a la derecha del triple")
    pendiente = float(base.get("meltingSlope", 50.0))
    if pendiente == 0:
        raise ErrorQuimica("phase_diagram: meltingSlope no puede ser 0")
    normales = {k: float(base[k]) for k in ("normalMelting", "normalBoiling", "normalSublimation") if k in base}
    vap = [(tt, pt), (tc, pc)]
    if "normalBoiling" in normales and pt < 1 < pc:
        vap.append((normales["normalBoiling"], 1.0))
    b_vap = math.log(pc / pt) / (1 / tt - 1 / tc)
    if "normalSublimation" in normales and pt > 1:
        sub = [(normales["normalSublimation"], 1.0), (tt, pt)]
    else:
        b_sub = b_vap * float(dato.get("sublimationRatio", 1.3))      # ΔHsub = ΔHvap + ΔHfus
        t_bajo = tt * 0.8
        sub = [(t_bajo, pt * math.exp(-b_sub * (1 / t_bajo - 1 / tt))), (tt, pt)]
    return Fases(str(base.get("name", "")), (tt, pt), (tc, pc), pendiente, vap, sub, normales)


# --- Curva de calentamiento -------------------------------------------------------------------------------

CALENTAMIENTO = {"water": {"name": "H2O", "cpSolid": 2.09, "cpLiquid": 4.18, "cpGas": 2.01, "melting": 0.0,
                           "boiling": 100.0, "hFusion": 334.0, "hVaporization": 2257.0}}


@dataclass
class Tramo:
    fase: str                     # sólido, fusión, líquido, vaporización, gas
    q0: float                     # kJ acumulados
    q1: float
    t0: float
    t1: float

    @property
    def q(self) -> float:
        return self.q1 - self.q0


def calentamiento(dato: dict) -> list[Tramo]:
    base = dict(CALENTAMIENTO.get(str(dato.get("substance", "water")).lower(), {}))
    base.update(dato)
    masa = _num(base.get("mass", 100), "mass (g)", positivo=True)
    t0 = _num(base.get("from", -20), "from (°C)")
    t1 = _num(base.get("to", 120), "to (°C)")
    try:
        tm, tb = float(base["melting"]), float(base["boiling"])
        cps, cpl, cpg = float(base["cpSolid"]), float(base["cpLiquid"]), float(base["cpGas"])
        hf, hv = float(base["hFusion"]), float(base["hVaporization"])
    except (KeyError, TypeError, ValueError):
        raise ErrorQuimica("heating_curve: faltan datos (melting, boiling, cpSolid, cpLiquid, cpGas, hFusion, "
                           "hVaporization) o substance") from None
    if not t0 < t1 or not tm < tb:
        raise ErrorQuimica("heating_curve: tiene que ser from < to y melting < boiling")
    tramos, q, t = [], 0.0, t0

    def calentar(fase: str, hasta: float, cp: float) -> None:
        nonlocal q, t
        if hasta > t:
            dq = masa * cp * (hasta - t) / 1000
            tramos.append(Tramo(fase, q, q + dq, t, hasta))
            q, t = q + dq, hasta

    def cambio(fase: str, h: float) -> None:
        nonlocal q
        dq = masa * h / 1000
        tramos.append(Tramo(fase, q, q + dq, t, t))
        q += dq

    if t0 <= tm:
        calentar("sólido", min(tm, t1), cps)
        if t1 > tm:
            cambio("fusión", hf)
    if t0 <= tb and t1 > tm:
        calentar("líquido", min(tb, t1), cpl)
        if t1 > tb:
            cambio("vaporización", hv)
    if t1 > tb:
        calentar("gas", t1, cpg)
    return tramos


# --- Electroquímica -------------------------------------------------------------------------------------

@dataclass
class Semicelda:
    pareja: str                   # "Zn^2+/Zn"
    e0: float
    n: int
    electrodo: str
    solucion: str
    conc: float | None
    reduccion: str                # "Zn^2+ + 2e^- → Zn"

    @property
    def oxidada(self) -> str:
        return self.pareja.split("/")[0].strip()

    @property
    def reducida(self) -> str:
        return self.pareja.split("/")[-1].strip()

    @property
    def oxidacion(self) -> str:
        izq, _, der = self.reduccion.partition("→")
        return f"{der.strip()} → {izq.strip()}"


def semicelda(dato: Any, donde: str) -> Semicelda:
    if not isinstance(dato, dict) or "couple" not in dato or "E0" not in dato:
        raise ErrorQuimica(f"{donde}: cada semicelda es {{couple: 'Zn^2+/Zn', E0: -0.76, n: 2}}")
    pareja = str(dato["couple"])
    if "/" not in pareja:
        raise ErrorQuimica(f"{donde}.couple: 'oxidada/reducida', por ejemplo 'Cu^2+/Cu'")
    n = int(dato.get("n", 2))
    if n < 1:
        raise ErrorQuimica(f"{donde}.n: los electrones son al menos 1")
    ox, _, red = pareja.partition("/")
    reduccion = str(dato.get("reaction") or f"{ox.strip()} + {n if n > 1 else ''}e^- → {red.strip()}")
    conc = _num(dato["conc"], f"{donde}.conc", positivo=True) if "conc" in dato else None
    electrodo = str(dato.get("electrode") or red.strip())
    solucion = str(dato.get("solution") or (f"{ox.strip()} {_corto(conc)} M" if conc else f"{ox.strip()} 1 M"))
    return Semicelda(pareja, _num(dato["E0"], f"{donde}.E0"), n, electrodo, solucion, conc, reduccion)


def _corto(x: float | None) -> str:
    return f"{x:g}".replace(".", ",") if x is not None else ""


@dataclass
class Pila:
    anodo: Semicelda
    catodo: Semicelda
    n: int
    e0: float
    e: float | None               # con Nernst, si hay concentraciones

    @property
    def notacion(self) -> str:
        def lado(s: Semicelda) -> str:
            return f"{s.oxidada} ({_corto(s.conc) or '1'} M)"
        return f"{self.anodo.electrodo}(s) | {lado(self.anodo)} || {lado(self.catodo)} | {self.catodo.electrodo}(s)"

    @property
    def delta_g(self) -> float:
        """ΔG° en kJ/mol."""
        return -self.n * F * self.e0 / 1000


def pila(semiceldas: list[Semicelda]) -> Pila:
    if len(semiceldas) != 2:
        raise ErrorQuimica("galvanic_cell: dos semiceldas")
    anodo, catodo = sorted(semiceldas, key=lambda s: s.e0)
    n = anodo.n * catodo.n // math.gcd(anodo.n, catodo.n)
    e0 = catodo.e0 - anodo.e0
    e = None
    if anodo.conc is not None and catodo.conc is not None:
        q = anodo.conc ** (n / anodo.n) / catodo.conc ** (n / catodo.n)
        e = e0 - 0.05916 / n * math.log10(q)
    return Pila(anodo, catodo, n, e0, e)


# --- Celdas unidad --------------------------------------------------------------------------------------

@dataclass
class Celda:
    red: str
    sitios: list[tuple[float, float, float, str]]    # (x, y, z, especie A o B)
    z: dict[str, float]                                # átomos por celda de cada especie
    coordinacion: str
    empaquetamiento: float | None                      # fracción
    relacion: str                                      # a en función de r

    @property
    def total(self) -> float:
        return sum(self.z.values())


def _fraccion(x: float, y: float, z: float) -> float:
    """Qué parte de un sitio cae adentro de la celda: 1/8 en un vértice, 1/4 en una arista, 1/2 en una cara."""
    bordes = sum(1 for v in (x, y, z) if v in (0.0, 1.0))
    return 1 / 2 ** bordes


def celda_unidad(red: str) -> Celda:
    vertices = [(x, y, z) for x in (0.0, 1.0) for y in (0.0, 1.0) for z in (0.0, 1.0)]
    caras = [(0.5, 0.5, 0.0), (0.5, 0.5, 1.0), (0.5, 0.0, 0.5), (0.5, 1.0, 0.5), (0.0, 0.5, 0.5), (1.0, 0.5, 0.5)]
    aristas = [p for p in ((a, b, c) for a in (0.0, 0.5, 1.0) for b in (0.0, 0.5, 1.0) for c in (0.0, 0.5, 1.0))
               if sorted(p).count(0.5) == 1]
    centro = [(0.5, 0.5, 0.5)]
    if red == "sc":
        sitios, coord, emp, rel = [(*p, "A") for p in vertices], "6", math.pi / 6, "a = 2r"
    elif red == "bcc":
        sitios = [(*p, "A") for p in vertices + centro]
        coord, emp, rel = "8", math.pi * math.sqrt(3) / 8, "a = 4r/√3"
    elif red == "fcc":
        sitios = [(*p, "A") for p in vertices + caras]
        coord, emp, rel = "12", math.pi / (3 * math.sqrt(2)), "a = 2√2 r"
    elif red == "nacl":
        sitios = [(*p, "A") for p in vertices + caras] + [(*p, "B") for p in aristas + centro]
        coord, emp, rel = "6:6", None, "a = 2(r₊ + r₋)"
    elif red == "cscl":
        sitios = [(*p, "A") for p in vertices] + [(*p, "B") for p in centro]
        coord, emp, rel = "8:8", None, "a√3 = 2(r₊ + r₋)"
    else:
        raise ErrorQuimica(f"unit_cell: red {red!r} (valen sc, bcc, fcc, nacl, cscl)")
    z: dict[str, float] = {}
    for x, y, zz, especie in sitios:
        z[especie] = z.get(especie, 0) + _fraccion(x, y, zz)
    return Celda(red, sitios, z, coord, emp, rel)


def densidad(celda: Celda, a_pm: float, masa_molar: float) -> float:
    """g/cm³: Z·M / (N_A·a³). Con dos especies, `masa_molar` es la de la unidad fórmula."""
    unidades = celda.z.get("A", 0) if len(celda.z) == 1 else min(celda.z.values())
    return unidades * masa_molar / (NA * (a_pm * 1e-10) ** 3)


# --- RMN -----------------------------------------------------------------------------------------------

MULTIPLICIDAD = {"s": 0, "d": 1, "t": 2, "q": 3, "quint": 4, "sext": 5, "sept": 6}


def pascal(n: int) -> list[int]:
    fila = [1]
    for _ in range(n):
        fila = [a + b for a, b in zip([0] + fila, fila + [0])]
    return fila


def multiplete(desplazamiento: float, vecinos: int, j_hz: float, mhz: float) -> list[tuple[float, float]]:
    """Las líneas (δ, intensidad relativa, que suma 1) de la regla n + 1."""
    intensidades = pascal(vecinos)
    total = sum(intensidades)
    paso = j_hz / mhz
    centro = (len(intensidades) - 1) / 2
    return [(desplazamiento + (i - centro) * paso, v / total) for i, v in enumerate(intensidades)]


# --- Orgánica: prioridades CIP, R/S, Newman y silla ------------------------------------------------------

def _z(simbolo: str) -> int:
    return Z_DE[simbolo]


# Sustituyentes comunes: (Z del primer átomo, Z de lo que tiene unido, con los dobles enlaces duplicados).
GRUPOS_CIP: dict[str, tuple[int, tuple[int, ...]]] = {
    "H": (1, ()), "D": (1, (0,)),
    "CH3": (6, (1, 1, 1)), "C2H5": (6, (6, 1, 1)), "CH2CH3": (6, (6, 1, 1)), "Et": (6, (6, 1, 1)),
    "CH(CH3)2": (6, (6, 6, 1)), "iPr": (6, (6, 6, 1)), "C(CH3)3": (6, (6, 6, 6)), "tBu": (6, (6, 6, 6)),
    "C6H5": (6, (6, 6, 6)), "Ph": (6, (6, 6, 6)),
    "CH2OH": (6, (8, 1, 1)), "CHO": (6, (8, 8, 1)), "COOH": (6, (8, 8, 8)), "COCH3": (6, (8, 8, 6)),
    "CN": (6, (7, 7, 7)), "CH2NH2": (6, (7, 1, 1)), "CONH2": (6, (8, 8, 7)), "CH2Cl": (6, (17, 1, 1)),
    "CH2Br": (6, (35, 1, 1)), "CH2SH": (6, (16, 1, 1)), "CCl3": (6, (17, 17, 17)),
    "OH": (8, (1,)), "OCH3": (8, (6,)), "NH2": (7, (1, 1)), "NHCH3": (7, (6, 1)), "N(CH3)2": (7, (6, 6)),
    "NH3^+": (7, (1, 1, 1)), "NO2": (7, (8, 8, 8)), "SH": (16, (1,)), "F": (9, ()), "Cl": (17, ()),
    "Br": (35, ()), "I": (53, ()),
}


def _clave_cip(grupo: str) -> tuple[int, tuple[int, ...]]:
    clave = GRUPOS_CIP.get(str(grupo).strip())
    if clave is None:
        raise ErrorQuimica(f"no sé la prioridad CIP de {grupo!r}: indicá priorities (de mayor a menor)")
    return clave[0], tuple(sorted(clave[1], reverse=True))


def prioridades(grupos: list[str]) -> list[int]:
    """El orden CIP (1 = mayor) de cada grupo, mirando el primer átomo y lo que tiene unido."""
    claves = [_clave_cip(g) for g in grupos]
    if len(set(claves)) != len(claves):
        raise ErrorQuimica(f"dos grupos empatan en la primera esfera ({', '.join(grupos)}): indicá priorities")
    orden = sorted(range(len(grupos)), key=lambda i: claves[i], reverse=True)
    rango = [0] * len(grupos)
    for puesto, i in enumerate(orden, 1):
        rango[i] = puesto
    return rango


# En una proyección de Fischer: arriba, derecha, abajo, izquierda (los horizontales salen hacia uno).
_FISCHER = {"top": (0, 1), "right": (1, 0), "bottom": (0, -1), "left": (-1, 0)}


def configuracion_fischer(por_lugar: dict[str, int]) -> str:
    """R o S, con la prioridad (1 a 4) de lo que hay arriba, a la derecha, abajo y a la izquierda."""
    lugar = {p: k for k, p in por_lugar.items()}
    if sorted(lugar) != [1, 2, 3, 4]:
        raise ErrorQuimica("Fischer: las prioridades son 1, 2, 3 y 4, una por lugar")
    (x1, y1), (x2, y2), (x3, y3) = (_FISCHER[lugar[k]] for k in (1, 2, 3))
    giro = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)        # > 0: antihorario
    horario = giro < 0
    if lugar[4] in ("left", "right"):                           # el menor hacia uno: se invierte
        horario = not horario
    return "R" if horario else "S"


def conformacion_newman(diedro: float) -> str:
    d = abs((diedro + 180) % 360 - 180)
    if d < 15:
        return "eclipsada (sinperiplanar)"
    if abs(d - 60) < 15:
        return "alternada gauche"
    if abs(d - 120) < 15:
        return "eclipsada (anticlinal)"
    if d > 165:
        return "alternada anti"
    return f"diedro de {d:g}°"


# Valores A (kJ/mol): lo que cuesta poner el grupo axial en lugar de ecuatorial.
VALORES_A = {"CH3": 7.3, "C2H5": 7.5, "CH2CH3": 7.5, "Et": 7.5, "CH(CH3)2": 9.2, "iPr": 9.2, "C(CH3)3": 21.0,
             "tBu": 21.0, "C6H5": 12.6, "Ph": 12.6, "OH": 3.9, "OCH3": 2.5, "NH2": 5.9, "F": 1.0, "Cl": 2.2,
             "Br": 2.0, "I": 1.8, "CN": 0.8, "COOH": 5.9, "CHO": 3.0, "H": 0.0}


def axial_arriba(carbono: int) -> bool:
    """En la silla dibujada, el enlace axial de los carbonos impares apunta hacia arriba."""
    return carbono % 2 == 1


def cara(carbono: int, axial: bool) -> str:
    """De qué lado del anillo queda el sustituyente: arriba o abajo."""
    return "arriba" if axial == axial_arriba(carbono) else "abajo"


def costo_axial(sustituyentes: list[dict]) -> float:
    total = 0.0
    for s in sustituyentes:
        if s["axial"]:
            if s["group"] not in VALORES_A:
                raise ErrorQuimica(f"chair: no hay valor A para {s['group']!r}")
            total += VALORES_A[s["group"]]
    return total


def relacion_cis_trans(sustituyentes: list[dict]) -> str | None:
    distintos = [s for s in sustituyentes if s["group"] != "H"]
    if len(distintos) != 2:
        return None
    a, b = distintos
    return "cis" if cara(a["position"], a["axial"]) == cara(b["position"], b["axial"]) else "trans"


# --- Inorgánica: campo cristalino, Latimer y Frost, Born-Haber y complejos ---------------------------------

def electrones_d(metal: str, oxidacion: int) -> int:
    """Los electrones d de un ion de transición: los del grupo menos la carga."""
    z = numero_atomico(metal)
    for inicio, fin, base in ((21, 30, 18), (39, 48, 36), (72, 80, 68)):
        if inicio <= z <= fin:
            n = z - base - oxidacion
            if not 0 <= n <= 10:
                raise ErrorQuimica(f"{metal} con estado de oxidación {oxidacion:+d} no queda con 0 a 10 electrones d")
            return n
    if z == 57:
        return max(0, 1 - oxidacion + 2)
    raise ErrorQuimica(f"{metal} no es un metal de transición del bloque d")


# Serie espectroquímica, de campo débil a fuerte. Desde el NH3 se toma como campo fuerte (bajo espín).
SERIE_ESPECTROQUIMICA = ["I^-", "Br^-", "S^2-", "SCN^-", "Cl^-", "NO3^-", "F^-", "OH^-", "C2O4^2-", "H2O", "NCS^-",
                         "CH3CN", "NH3", "en", "bipy", "phen", "NO2^-", "PPh3", "CN^-", "CO"]
CAMPO_FUERTE_DESDE = SERIE_ESPECTROQUIMICA.index("NH3")

# Niveles de cada geometría, de abajo hacia arriba: (nombre, orbitales, energía en unidades de Δ).
NIVELES_CAMPO = {
    "octahedral": [("t2g", ["dxy", "dxz", "dyz"], -0.4), ("eg", ["dz²", "dx²−y²"], 0.6)],
    "tetrahedral": [("e", ["dz²", "dx²−y²"], -0.6), ("t2", ["dxy", "dxz", "dyz"], 0.4)],
    "square_planar": [("", ["dxz", "dyz"], -0.514), ("", ["dz²"], -0.428), ("", ["dxy"], 0.228),
                      ("", ["dx²−y²"], 1.228)],
}


@dataclass
class CampoCristalino:
    geometria: str
    electrones: int
    alto_espin: bool
    llenado: list[list[int]]            # por nivel, por orbital: 0, 1 (↑) o 2 (↑↓)

    @property
    def desapareados(self) -> int:
        return sum(1 for nivel in self.llenado for e in nivel if e == 1)

    @property
    def momento(self) -> float:
        """Momento magnético de solo espín, en magnetones de Bohr."""
        n = self.desapareados
        return math.sqrt(n * (n + 2))

    @property
    def eecc(self) -> float:
        """La energía de estabilización del campo cristalino, en unidades de Δ (sin el apareamiento)."""
        return sum(sum(nivel) * energia for nivel, (_, _, energia) in zip(self.llenado, NIVELES_CAMPO[self.geometria]))

    @property
    def pares(self) -> int:
        return sum(1 for nivel in self.llenado for e in nivel if e == 2)


def campo_cristalino(geometria: str, electrones: int, alto_espin: bool) -> CampoCristalino:
    if geometria not in NIVELES_CAMPO:
        raise ErrorQuimica(f"crystal_field: geometry {geometria!r} (vale octahedral, tetrahedral o square_planar)")
    if not 0 <= electrones <= 10:
        raise ErrorQuimica("crystal_field: de 0 a 10 electrones d")
    niveles = NIVELES_CAMPO[geometria]
    llenado = [[0] * len(orbitales) for _, orbitales, _ in niveles]
    orden = [(i, j) for i, (_, orbitales, _) in enumerate(niveles) for j in range(len(orbitales))]
    quedan = electrones
    if alto_espin:
        # Uno en cada orbital, de abajo hacia arriba, y después se aparean.
        for vuelta in (1, 2):
            for i, j in orden:
                if quedan and llenado[i][j] < vuelta:
                    llenado[i][j] += 1
                    quedan -= 1
    else:
        # Se llena cada nivel (con Hund adentro) antes de subir al siguiente.
        for i, (_, orbitales, _) in enumerate(niveles):
            for vuelta in (1, 2):
                for j in range(len(orbitales)):
                    if quedan and llenado[i][j] < vuelta:
                        llenado[i][j] += 1
                        quedan -= 1
    return CampoCristalino(geometria, electrones, alto_espin, llenado)


def es_campo_fuerte(ligando: str) -> bool:
    if ligando not in SERIE_ESPECTROQUIMICA:
        raise ErrorQuimica(f"el ligando {ligando!r} no está en la serie espectroquímica: indicá spin")
    return SERIE_ESPECTROQUIMICA.index(ligando) >= CAMPO_FUERTE_DESDE


@dataclass
class Latimer:
    especies: list[str]
    oxidacion: list[float]
    potenciales: list[float]             # entre cada especie y la siguiente (reducción)

    def electrones(self, i: int) -> float:
        return self.oxidacion[i] - self.oxidacion[i + 1]

    def potencial(self, i: int, j: int) -> float:
        """E° entre dos especies cualesquiera (i más oxidada que j): Σ nE / Σ n."""
        if i > j:
            i, j = j, i
        n = sum(self.electrones(k) for k in range(i, j))
        return sum(self.electrones(k) * self.potenciales[k] for k in range(i, j)) / n

    def frost(self) -> list[float]:
        """N·E° de cada especie respecto de la de estado de oxidación 0 (o de la última)."""
        ref = next((k for k, o in enumerate(self.oxidacion) if o == 0), len(self.especies) - 1)
        salida = []
        for k in range(len(self.especies)):
            if k == ref:
                salida.append(0.0)
            elif k < ref:
                salida.append(sum(self.electrones(m) * self.potenciales[m] for m in range(k, ref)))
            else:
                salida.append(-sum(self.electrones(m) * self.potenciales[m] for m in range(ref, k)))
        return salida

    def desproporcionan(self) -> list[int]:
        """Las especies que desproporcionan: el E° de su reducción supera al de su oxidación."""
        return [k for k in range(1, len(self.especies) - 1) if self.potenciales[k] > self.potenciales[k - 1]]


def latimer(dato: dict) -> Latimer:
    especies = [str(e) for e in _lista(dato.get("species"))]
    oxidacion = [float(o) for o in _lista(dato.get("oxidation"))]
    potenciales = [float(p) for p in _lista(dato.get("potentials"))]
    if len(especies) < 2 or len(oxidacion) != len(especies) or len(potenciales) != len(especies) - 1:
        raise ErrorQuimica("latimer: species y oxidation (uno por especie) y potentials (uno entre cada par), "
                           "de la más oxidada a la más reducida")
    if any(a <= b for a, b in zip(oxidacion, oxidacion[1:])):
        raise ErrorQuimica("latimer: los estados de oxidación tienen que bajar de izquierda a derecha")
    return Latimer(especies, oxidacion, potenciales)


@dataclass
class BornHaber:
    pasos: list[tuple[str, float]]       # (estado al que llega, ΔH del paso)
    formacion: float
    producto: str
    inicio: str

    @property
    def energia_red(self) -> float:
        """ΔH de red (formación del sólido desde los iones gaseosos), por la ley de Hess."""
        return self.formacion - sum(dh for _, dh in self.pasos)


def born_haber(dato: dict) -> BornHaber:
    pasos = []
    for i, p in enumerate(_lista(dato.get("steps"))):
        if not isinstance(p, dict) or "dH" not in p:
            raise ErrorQuimica(f"born_haber: steps[{i}] es {{to: estado, dH: kJ/mol, label}}")
        pasos.append((str(p.get("to", "")), _num(p["dH"], f"steps[{i}].dH")))
    if not pasos or "formation" not in dato:
        raise ErrorQuimica("born_haber: faltan steps (de los elementos a los iones gaseosos) y formation (ΔHf)")
    return BornHaber(pasos, _num(dato["formation"], "formation"), str(dato.get("product", "MX(s)")),
                     str(dato.get("start", "elementos")))


CARGA_LIGANDOS = {"NH3": 0, "H2O": 0, "CO": 0, "en": 0, "py": 0, "PPh3": 0, "NO": 0, "Cl": -1, "Cl^-": -1,
                  "Br": -1, "Br^-": -1, "I": -1, "I^-": -1, "F": -1, "F^-": -1, "CN": -1, "CN^-": -1, "OH": -1,
                  "OH^-": -1, "NO2": -1, "NO2^-": -1, "SCN": -1, "SCN^-": -1, "NCS^-": -1, "ox": -2,
                  "C2O4^2-": -2, "O^2-": -2}
# Los sitios de cada geometría y cuáles quedan opuestos (a 180°).
SITIOS_COMPLEJO = {"octahedral": 6, "square_planar": 4, "tetrahedral": 4}
OPUESTOS = {"octahedral": {(0, 1), (2, 3), (4, 5)}, "square_planar": {(0, 1), (2, 3)}, "tetrahedral": set()}


def isomero(geometria: str, ligandos: list[str]) -> str | None:
    """cis/trans (MA4B2, MA2B2) o fac/mer (MA3B3), según dónde quedan los ligandos iguales."""
    opuestos = OPUESTOS[geometria]
    conteo: dict[str, list[int]] = {}
    for i, lig in enumerate(ligandos):
        conteo.setdefault(lig, []).append(i)
    tamanos = sorted(len(v) for v in conteo.values())
    if geometria in ("octahedral", "square_planar") and 2 in tamanos and len(conteo) == 2:
        par = next(v for v in conteo.values() if len(v) == 2)
        return "trans" if tuple(sorted(par)) in opuestos else "cis"
    if geometria == "octahedral" and tamanos == [3, 3]:
        tres = next(iter(conteo.values()))
        alguno_opuesto = any(tuple(sorted((a, b))) in opuestos for a in tres for b in tres if a < b)
        return "mer" if alguno_opuesto else "fac"
    return None


def oxidacion_metal(carga: int, ligandos: list[str]) -> int:
    total = 0
    for lig in ligandos:
        if lig not in CARGA_LIGANDOS:
            raise ErrorQuimica(f"complex: no sé la carga del ligando {lig!r}: indicá oxidation")
        total += CARGA_LIGANDOS[lig]
    return carga - total
