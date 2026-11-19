"""El cuerpo del examen de cada variante, con el motor de alucard.

Con `definicion` en `exam.yaml`, cada variante es un tema de esa definición: el mismo sorteo y la
misma mezcla que `alucard generar` con la semilla del tema. Sin ella, el cuerpo tiene una sección
con una pregunta por ejercicio de la rúbrica: la que tiene la etiqueta del `id` del ejercicio, otra
en cada variante cuando el banco tiene más de una (`sortear_por_tema`).

`--questions` reemplaza los bancos (`input_banco`) de la definición.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from generador_examenes.omr.config import ConfigExamen


class ErrorCuerpo(ValueError):
    """El cuerpo del examen no se puede armar (definición inválida, sin preguntas, clave incompleta)."""


@dataclass
class Cuerpo:
    definicion: Any                 # DefinicionExamen
    variantes: dict[str, dict]      # letra → examen mezclado (secciones y preguntas)
    semilla: int
    avisos: list[str]


def _definicion_de_la_rubrica(config: ConfigExamen) -> dict[str, Any]:
    return {
        "nombre_examen": config.title, "institucion": "", "materia": "",
        # Los ejercicios en el orden de la rúbrica, que es el de la carátula.
        "configuracion_examen": {"sortear_por_tema": True, "mezclar_preguntas_dentro_seccion": False},
        "secciones_examen": [{"nombre": "Ejercicios", "pools": [
            {"etiquetas": [e.id], "cantidad": 1, "puntaje_fijo_por_pregunta": e.max_points} for e in config.rubric]}],
    }


def _rutas(rutas: list[str], base: Path) -> list[Path]:
    """Una ruta relativa vale desde la carpeta actual y, si no existe ahí, desde la definición."""
    salida = []
    for r in rutas:
        ruta = Path(r)
        salida.append(ruta if ruta.is_absolute() or ruta.exists() else base / ruta)
    return salida


def armar(config: ConfigExamen, preguntas: list[Path] | None = None) -> Cuerpo:
    from pydantic import ValidationError

    from generador_examenes.config import proyecto
    from generador_examenes.core import logic
    from generador_examenes.core.estilo import ErrorEstilo, combinar
    from generador_examenes.core.models import DefinicionExamen

    if config.definicion is not None:
        base = config.definicion.parent
        datos = yaml.safe_load(config.definicion.read_text(encoding="utf-8")) or {}
        donde = str(config.definicion)
    else:
        base = config.origen.parent if config.origen else Path.cwd()
        datos = _definicion_de_la_rubrica(config)
        donde = "la rúbrica"
    try:
        definicion = DefinicionExamen(**datos)
    except ValidationError as e:
        raise ErrorCuerpo(f"{donde}: {e}") from e

    curso = proyecto.cargar(base)
    try:
        definicion = definicion.model_copy(update={"estilo": combinar(curso.estilo, datos.get("estilo") or {}, base)})
    except (ErrorEstilo, ValidationError) as e:
        raise ErrorCuerpo(f"estilo: {e}") from e

    escritos = definicion.model_fields_set
    rutas = (list(preguntas) if preguntas else None) or (
        _rutas(definicion.input_banco, base) if "input_banco" in escritos and definicion.input_banco else None
    ) or list(curso.input_banco or [])
    if not rutas and not definicion.input_consignas and not definicion.repositorios_externos:
        raise ErrorCuerpo("no hay preguntas: pasá --questions o poné input_banco en la definición")
    semilla = next(v for v in (config.seed, definicion.semilla if "semilla" in escritos else None, curso.semilla, 42)
                   if v is not None)

    repetidos: list = []
    banco = logic.cargar_banco_definicion(definicion, rutas, repetidos)
    if not banco:
        raise ErrorCuerpo(f"no se cargaron preguntas de {', '.join(map(str, rutas)) or 'los bancos'}")
    avisos = [str(r) for r in repetidos]

    n = len(config.variants)
    try:
        bases = logic.pools_de_temas(definicion, banco, semilla, n)
    except ValueError as e:
        raise ErrorCuerpo(str(e)) from e
    sin_clave = list(dict.fromkeys(p for b in bases for p in logic.auditar_claves(b)))
    if sin_clave:
        raise ErrorCuerpo("hay preguntas sin respuesta correcta: " + "; ".join(sin_clave))

    uso: dict = {}
    variantes = {}
    for i, letra in enumerate(config.variants):
        variantes[letra] = logic.mezclar_examen(bases[i], semilla + i, definicion.configuracion_examen, uso_global=uso)
    if n > 1:
        def letras(m: re.Match) -> str:
            return "las variantes " + re.sub(r"\d+", lambda d: config.variants[int(d.group()) - 1], m.group(1))
        avisos += [re.sub(r"los temas ([\d, y]+?)(?= (?:son|tienen))", letras, a)
                   for a in logic.temas_con_mismas_preguntas(list(variantes.values()), definicion)]
    return Cuerpo(definicion=definicion, variantes=variantes, semilla=semilla, avisos=avisos)
