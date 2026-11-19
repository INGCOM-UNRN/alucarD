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
