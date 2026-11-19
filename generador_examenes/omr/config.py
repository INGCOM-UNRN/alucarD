"""`exam.yaml` / `exam.json`: identidad del examen, variantes, escala de notas, curva y rúbrica (§3.1).

Las reglas de §3.3 se revisan todas juntas: `cargar` junta cada problema con su clave y levanta
`ErrorConfig` con la lista, así un archivo con varios errores se corrige de una vez.

Además de las claves de la SPEC, alucard acepta:

- `definicion`: una definición de examen de alucard (YAML) para el cuerpo; cada variante es un tema.
  Sin ella, el cuerpo tiene una pregunta por ejercicio de la rúbrica: la que tenga la etiqueta con el
  `id` del ejercicio (`// [tag, ej1]`), otra en cada variante si hay más de una.
- `seed`: semilla del sorteo del cuerpo (por omisión, la de la definición o 42).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

EXAM_ID = re.compile(r"^[A-Z0-9-]{1,16}$")
LAYOUT_ID = re.compile(r"^[A-Z0-9-]+$")
VARIANTE = re.compile(r"^[A-Z]$")
# Los ids viajan en el QR compacto, separados por `,`, `:` y `/`.
ID_EJERCICIO = re.compile(r"^[A-Za-z0-9_-]+$")
RESERVADOS = {"nota_final", "ausente"}
PASOS = (None, 0.5, 0.25)


class ErrorConfig(ValueError):
    """La configuración no cumple las reglas de §3.3: el motor no sigue (código de salida ≠ 0)."""

    def __init__(self, archivo: str, problemas: list[str]):
        self.problemas = problemas
        super().__init__(f"{archivo}: " + "; ".join(problemas))


@dataclass(frozen=True)
class EscalaNotas:
    min: float = 1.0
    max: float = 10.0
    decimals: int = 1
    step: float | None = None
    rounding: Literal["half_up", "half_even"] = "half_up"
    match_tolerance: int = 0

    @property
    def unidad(self) -> float:
        """La menor diferencia entre dos notas: el paso o una unidad de la última cifra."""
        return self.step if self.step else 10.0 ** -self.decimals


@dataclass(frozen=True)
class CurvaNotas:
    type: str = "piecewise_log"
    pass_pct: float = 60.0
    pass_grade: float = 4.0
    promo_pct: float | None = None
    promo_grade: float | None = None
    curve_k: float = 0.0
    fail_curve: str = "linear"


@dataclass(frozen=True)
class Ejercicio:
    id: str
    label: str
    max_points: float
    levels: int
    labels: tuple[str, ...] | None = None

    def etiquetas(self) -> list[str]:
        """Lo que va arriba de cada burbuja: las propias o el porcentaje redondeado de cada nivel."""
        if self.labels:
            return list(self.labels)
        return [str(round(paso / (self.levels - 1) * 100)) for paso in range(self.levels)]


@dataclass(frozen=True)
class ConfigExamen:
    exam_id: str
    title: str
    layout_id: str
    layout_version: int
    variants: tuple[str, ...]
    grade_scale: EscalaNotas
    grade_map: CurvaNotas
    rubric: tuple[Ejercicio, ...]
    cloud_sync_default: bool = False
    definicion: Path | None = None
    seed: int | None = None
    origen: Path | None = field(default=None, compare=False)

    @property
    def puntaje_total(self) -> float:
        return sum(e.max_points for e in self.rubric)


def _numero(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def leer_archivo(ruta: Path) -> dict:
    texto = ruta.read_text(encoding="utf-8")
    try:
        datos = json.loads(texto) if ruta.suffix.lower() == ".json" else yaml.safe_load(texto)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ErrorConfig(str(ruta), [f"no se puede leer: {e}"]) from e
    if not isinstance(datos, dict):
        raise ErrorConfig(str(ruta), ["el archivo tiene que ser un diccionario de claves"])
    return datos


def cargar(ruta: Path) -> ConfigExamen:
    return desde_dict(leer_archivo(ruta), ruta)


def desde_dict(datos: dict, ruta: Path | None = None) -> ConfigExamen:
    """La configuración validada. Junta todos los problemas antes de rechazarla."""
    p: list[str] = []
    nombre = str(ruta) if ruta else "configuración"

    conocidas = {"exam_id", "title", "layout_id", "layout_version", "variants", "cloud_sync_default",
                 "grade_scale", "grade_map", "rubric", "definicion", "seed"}
    for clave in sorted(set(datos) - conocidas):
        p.append(f"{clave}: clave desconocida")

    exam_id = datos.get("exam_id")
    if not isinstance(exam_id, str) or not EXAM_ID.match(exam_id):
        p.append(f"exam_id: {exam_id!r} no cumple ^[A-Z0-9-]{{1,16}}$")
    title = datos.get("title")
    if not isinstance(title, str) or not title.strip():
        p.append("title: falta el título del examen")
    layout_id = datos.get("layout_id")
    if not isinstance(layout_id, str) or not LAYOUT_ID.match(layout_id):
        p.append(f"layout_id: {layout_id!r} no cumple ^[A-Z0-9-]+$")
    version = datos.get("layout_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        p.append(f"layout_version: {version!r} tiene que ser un entero >= 1")

    variantes = datos.get("variants", ["A"])
    if not isinstance(variantes, list) or not variantes:
        p.append("variants: tiene que ser una lista de letras, como [\"A\", \"B\"]")
        variantes = []
    for v in variantes:
        if not isinstance(v, str) or not VARIANTE.match(v):
            p.append(f"variants: {v!r} no cumple ^[A-Z]$")
    if len(set(map(str, variantes))) != len(variantes):
        p.append("variants: hay letras repetidas")

    cloud = datos.get("cloud_sync_default", False)
    if not isinstance(cloud, bool):
        p.append("cloud_sync_default: es true o false")

    escala = _escala(datos.get("grade_scale") or {}, p)
    curva = _curva(datos.get("grade_map") or {}, escala, p)
    rubrica = _rubrica(datos.get("rubric"), p)

    definicion = datos.get("definicion")
    ruta_definicion = None
    if definicion is not None:
        if not isinstance(definicion, str):
            p.append("definicion: es la ruta a una definición YAML de alucard")
        else:
            ruta_definicion = Path(definicion)
            if ruta and not ruta_definicion.is_absolute():
                ruta_definicion = ruta.parent / ruta_definicion
            if not ruta_definicion.is_file():
                p.append(f"definicion: no existe {ruta_definicion}")
    seed = datos.get("seed")
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
        p.append(f"seed: {seed!r} tiene que ser un entero")

    if p:
        raise ErrorConfig(nombre, p)
    return ConfigExamen(exam_id=exam_id, title=title.strip(), layout_id=layout_id, layout_version=version,
                        variants=tuple(variantes), grade_scale=escala, grade_map=curva, rubric=rubrica,
                        cloud_sync_default=cloud, definicion=ruta_definicion, seed=seed, origen=ruta)


def _escala(d: Any, p: list[str]) -> EscalaNotas:
    if not isinstance(d, dict):
        p.append("grade_scale: tiene que ser un diccionario")
        return EscalaNotas()
    base = EscalaNotas()
    minimo, maximo = d.get("min", base.min), d.get("max", base.max)
    decimales, paso = d.get("decimals", base.decimals), d.get("step", base.step)
    redondeo, tolerancia = d.get("rounding", base.rounding), d.get("match_tolerance", base.match_tolerance)
    for clave in sorted(set(d) - {"min", "max", "decimals", "step", "rounding", "match_tolerance"}):
        p.append(f"grade_scale.{clave}: clave desconocida")
    bien = True
    if not _numero(minimo) or not _numero(maximo):
        p.append("grade_scale: min y max son números")
        bien = False
    elif minimo >= maximo:
        p.append(f"grade_scale: min ({minimo:g}) tiene que ser menor que max ({maximo:g})")
    elif minimo < 0 or maximo - int(minimo) > 10 or minimo != int(minimo) or maximo != int(maximo):
        # Una fila de burbujas por cifra: las unidades van de min a max, hasta 11 burbujas.
        p.append("grade_scale: min y max son enteros y la fila de unidades tiene hasta 11 burbujas "
                 f"(de {minimo:g} a {maximo:g} son {int(maximo) - int(minimo) + 1})")
    if decimales not in (0, 1, 2) or isinstance(decimales, bool):
        p.append(f"grade_scale.decimals: {decimales!r} tiene que ser 0, 1 o 2")
        bien = False
    if paso not in PASOS or isinstance(paso, bool):
        p.append(f"grade_scale.step: {paso!r} tiene que ser null, 0.5 o 0.25")
    elif paso is not None and bien and decimales != 0 and round(paso, decimales) != paso:
        p.append(f"grade_scale.step: {paso:g} no se puede escribir con {decimales} decimal(es)")
    if redondeo not in ("half_up", "half_even"):
        p.append(f"grade_scale.rounding: {redondeo!r} tiene que ser \"half_up\" o \"half_even\"")
    if not isinstance(tolerancia, int) or isinstance(tolerancia, bool) or tolerancia < 0:
        p.append(f"grade_scale.match_tolerance: {tolerancia!r} tiene que ser un entero >= 0")
    try:
        return EscalaNotas(min=float(minimo), max=float(maximo), decimals=int(decimales),
                           step=None if paso is None else float(paso), rounding=redondeo,
                           match_tolerance=int(tolerancia))
    except (TypeError, ValueError):
        return EscalaNotas()


def _curva(d: Any, escala: EscalaNotas, p: list[str]) -> CurvaNotas:
    if not isinstance(d, dict):
        p.append("grade_map: tiene que ser un diccionario")
        return CurvaNotas()
    for clave in sorted(set(d) - {"type", "pass_pct", "pass_grade", "promo_pct", "promo_grade", "curve_k",
                                  "fail_curve"}):
        p.append(f"grade_map.{clave}: clave desconocida")
    tipo = d.get("type", "piecewise_log")
    if tipo != "piecewise_log":
        p.append(f"grade_map.type: {tipo!r}: la única curva es \"piecewise_log\"")
    falla = d.get("fail_curve", "linear")
    if falla != "linear":
        p.append(f"grade_map.fail_curve: {falla!r}: el tramo de desaprobados es \"linear\"")
    pass_pct = d.get("pass_pct")
    if not _numero(pass_pct):
        p.append("grade_map.pass_pct: es obligatorio")
        pass_pct = 60.0
    elif not 50.0 <= pass_pct <= 70.0:
        p.append(f"grade_map.pass_pct: {pass_pct:g} está fuera de [50.0, 70.0]")
    pass_grade = d.get("pass_grade", 4.0)
    if pass_grade != 4.0:
        p.append(f"grade_map.pass_grade: {pass_grade!r}: la nota de aprobación es 4.0")
    elif not escala.min < 4.0 < escala.max:
        p.append(f"grade_map.pass_grade: 4.0 tiene que quedar entre min ({escala.min:g}) y max ({escala.max:g})")
    promo_pct, promo_grade = d.get("promo_pct"), d.get("promo_grade")
    if promo_pct is not None:
        if not _numero(promo_pct):
            p.append(f"grade_map.promo_pct: {promo_pct!r} es un número o null")
            promo_pct = None
        elif not pass_pct < promo_pct < 100.0:
            p.append(f"grade_map.promo_pct: {promo_pct:g} tiene que estar entre pass_pct ({pass_pct:g}) y 100")
        if promo_grade is None:
            p.append("grade_map.promo_grade: es obligatorio si hay promo_pct")
        elif not _numero(promo_grade) or not 4.0 < promo_grade < escala.max:
            p.append(f"grade_map.promo_grade: {promo_grade!r} tiene que estar en (4.0, {escala.max:g})")
    elif promo_grade is not None:
        p.append("grade_map.promo_grade: sin promo_pct no hay promoción; sacalo o poné promo_pct")
        promo_grade = None
    k = d.get("curve_k", 0.0)
    if not _numero(k) or not -10.0 <= k <= 10.0:
        p.append(f"grade_map.curve_k: {k!r} está fuera de [-10.0, +10.0]")
        k = 0.0
    return CurvaNotas(type="piecewise_log", pass_pct=float(pass_pct), pass_grade=4.0,
                      promo_pct=None if promo_pct is None else float(promo_pct),
                      promo_grade=None if promo_pct is None or not _numero(promo_grade) else float(promo_grade),
                      curve_k=float(k), fail_curve="linear")


def _rubrica(lista: Any, p: list[str]) -> tuple[Ejercicio, ...]:
    if not isinstance(lista, list) or not lista:
        p.append("rubric: tiene que ser una lista con al menos un ejercicio")
        return ()
    ejercicios, vistos = [], set()
    for n, e in enumerate(lista, 1):
        donde = f"rubric[{n}]"
        if not isinstance(e, dict):
            p.append(f"{donde}: tiene que ser un diccionario")
            continue
        for clave in sorted(set(e) - {"id", "label", "max_points", "levels", "labels"}):
            p.append(f"{donde}.{clave}: clave desconocida")
        id_ = e.get("id")
        if not isinstance(id_, str) or not ID_EJERCICIO.match(id_):
            p.append(f"{donde}.id: {id_!r} tiene que ser letras, números, _ o -")
            id_ = f"?{n}"
        elif id_ in RESERVADOS:
            p.append(f"{donde}.id: {id_!r} es un campo reservado de la carátula")
        if id_ in vistos:
            p.append(f"{donde}.id: {id_!r} está duplicado")
        vistos.add(id_)
        puntos, niveles = e.get("max_points"), e.get("levels")
        if not _numero(puntos) or puntos <= 0:
            p.append(f"{donde}.max_points: {puntos!r} tiene que ser mayor que 0")
            puntos = 1.0
        if not isinstance(niveles, int) or isinstance(niveles, bool) or not 2 <= niveles <= 11:
            p.append(f"{donde}.levels: {niveles!r} está fuera de [2, 11]")
            niveles = 2
        etiquetas = e.get("labels")
        if etiquetas is not None:
            if (not isinstance(etiquetas, list) or len(etiquetas) != niveles
                    or not all(isinstance(t, str) and t.strip() for t in etiquetas)):
                p.append(f"{donde}.labels: tienen que ser {niveles} textos, uno por burbuja")
                etiquetas = None
            else:
                etiquetas = tuple(t.strip() for t in etiquetas)
        etiqueta = e.get("label") or id_
        ejercicios.append(Ejercicio(id=id_, label=str(etiqueta), max_points=float(puntos), levels=niveles,
                                    labels=etiquetas))
    return tuple(ejercicios)
