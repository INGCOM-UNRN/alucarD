"""La nota de una carátula, con la misma matemática que la app Escáner OMR (§5).

1. Cada ejercicio vale `step / (levels - 1) * max_points`, sin redondear.
2. El porcentaje es `100 * Σ pts / Σ max_points`.
3. La curva es lineal de `min` a `pass_grade` para los desaprobados y, en cada tramo de aprobados
   o promocionados, `g0 + (g1 - g0) * f(t)`, con `f` logarítmica (k > 0), lineal (k = 0) o
   exponencial (k < 0).
4. El redondeo nunca cruza un umbral: la condición sale siempre del porcentaje.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal

from generador_examenes.omr.config import ConfigExamen, CurvaNotas, EscalaNotas

DESAPROBADO, APROBADO, PROMOCIONADO, AUSENTE = "DESAPROBADO", "APROBADO", "PROMOCIONADO", "AUSENTE"


def puntaje(paso: int, niveles: int, maximo: float) -> float:
    return paso / (niveles - 1) * maximo


def porcentaje(config: ConfigExamen, pasos: dict[str, int]) -> float:
    """El porcentaje global con los pasos marcados de cada ejercicio (0 si no se marcó)."""
    total = sum(puntaje(pasos.get(e.id, 0), e.levels, e.max_points) for e in config.rubric)
    return min(100.0, max(0.0, 100.0 * total / config.puntaje_total))


def f(t: float, k: float) -> float:
    if k > 0:
        return math.log(1 + k * t) / math.log(1 + k)
    if k < 0:
        return ((1 + abs(k)) ** t - 1) / abs(k)
    return t


def _tramos(curva: CurvaNotas, escala: EscalaNotas) -> list[tuple[float, float, float, float]]:
    """Los tramos de aprobados (y promocionados): (p0, p1, g0, g1)."""
    if curva.promo_pct is None or curva.promo_grade is None:
        return [(curva.pass_pct, 100.0, curva.pass_grade, escala.max)]
    return [(curva.pass_pct, curva.promo_pct, curva.pass_grade, curva.promo_grade),
            (curva.promo_pct, 100.0, curva.promo_grade, escala.max)]


def nota_continua(p: float, curva: CurvaNotas, escala: EscalaNotas) -> float:
    """La nota sin redondear."""
    if p < curva.pass_pct:
        return escala.min + (curva.pass_grade - escala.min) * p / curva.pass_pct
    for p0, p1, g0, g1 in _tramos(curva, escala):
        if p <= p1:
            return g0 + (g1 - g0) * f((p - p0) / (p1 - p0), curva.curve_k)
    return escala.max


def redondear(valor: float, escala: EscalaNotas) -> float:
    """Al múltiplo más cercano de la unidad (el paso, o 10^-decimals), con el modo de la escala."""
    unidad = Decimal(str(escala.unidad))
    modo = ROUND_HALF_UP if escala.rounding == "half_up" else ROUND_HALF_EVEN
    # repr del float: 6.25 se redondea como 6.25, no como 6.2499999…
    cociente = (Decimal(repr(valor)) / unidad).quantize(Decimal(1), rounding=modo)
    return float(cociente * unidad)


def condicion(p: float, curva: CurvaNotas, ausente: bool = False) -> str:
    if ausente:
        return AUSENTE
    if p < curva.pass_pct:
        return DESAPROBADO
    if curva.promo_pct is not None and p >= curva.promo_pct:
        return PROMOCIONADO
    return APROBADO


def nota(p: float, config: ConfigExamen) -> float:
    """La nota redondeada, sin cruzar un umbral que el porcentaje no alcanzó."""
    curva, escala = config.grade_map, config.grade_scale
    g = redondear(nota_continua(p, curva, escala), escala)
    unidad = escala.unidad
    if p < curva.pass_pct and g >= curva.pass_grade:
        g = redondear(curva.pass_grade - unidad, escala)
    if curva.promo_pct is not None and curva.promo_grade is not None and p < curva.promo_pct and g >= curva.promo_grade:
        g = redondear(curva.promo_grade - unidad, escala)
    return min(escala.max, max(escala.min, g))


def coincide(marcada: float, calculada: float, escala: EscalaNotas) -> bool:
    """Si la nota final marcada en la carátula coincide con la calculada, dentro de la tolerancia."""
    ultima = 10.0 ** -escala.decimals if not escala.step else escala.step
    return abs(marcada - calculada) <= escala.match_tolerance * ultima + 1e-9


def puntos_de_verificacion(curva: CurvaNotas) -> list[float]:
    """0 %, 30 %, justo antes y en cada umbral, los puntos medios y 100 % (§5)."""
    puntos: list[float] = [0.0, 30.0, curva.pass_pct - 0.1, curva.pass_pct]
    if curva.promo_pct is None:
        puntos += [(curva.pass_pct + 100.0) / 2]
    else:
        puntos += [(curva.pass_pct + curva.promo_pct) / 2, curva.promo_pct - 0.1, curva.promo_pct,
                   (curva.promo_pct + 100.0) / 2]
    puntos.append(100.0)
    return sorted(dict.fromkeys(round(x, 4) for x in puntos))


def formato_nota(g: float, escala: EscalaNotas) -> str:
    decimales = escala.decimals if not escala.step else max(escala.decimals, len(f"{escala.step:g}") - 2)
    return f"{g:.{decimales}f}".replace(".", ",")


def tabla_verificacion(config: ConfigExamen, puntos: Iterable[float] | None = None) -> list[tuple[float, float, str]]:
    curva = config.grade_map
    return [(p, nota(p, config), condicion(p, curva)) for p in (puntos or puntos_de_verificacion(curva))]


def texto_tabla(config: ConfigExamen) -> str:
    """La vista previa de la curva que se imprime antes de compilar los PDF."""
    escala, curva = config.grade_scale, config.grade_map
    promo = (f", promoción {curva.promo_pct:g} % → {curva.promo_grade:g}" if curva.promo_pct is not None
             else ", sin promoción")
    lineas = [(f"Curva de notas de {config.exam_id}: aprobación {curva.pass_pct:g} % → {curva.pass_grade:g}{promo}, "
               f"k = {curva.curve_k:g}, escala {escala.min:g}–{escala.max:g}"),
              "", f"  {'Porcentaje':>10}  {'Nota':>6}  Condición", f"  {'-' * 10}  {'-' * 6}  {'-' * 12}"]
    for p, g, c in tabla_verificacion(config):
        lineas.append(f"  {p:>9.1f}%  {formato_nota(g, escala):>6}  {c}")
    return "\n".join(lineas)
