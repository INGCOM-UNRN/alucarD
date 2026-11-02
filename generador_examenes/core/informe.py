"""Informe de la generación (`informe.md` junto a los temas): qué se eligió, de dónde y por qué.

- Pools: cuántas preguntas podía elegir cada uno y cuántas eligió.
- Preguntas: sección, título, tipo, categoría, banco y puntaje.
- Orden de cada tema: los temas comparten preguntas y cambian el orden (y el de las opciones).
- Consignas prácticas que no entraron en ningún pool, con el filtro que las dejó afuera, y las del
  proyecto que tienen `publicar: false`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from generador_examenes.core.models import DefinicionExamen, PoolConfig, Pregunta

# Grupos de filtros de un pool, en el orden en que se aplican.
_FILTROS = [
    ("categoría", ("categoria", "categorias")),
    ("tipo", ("tipos",)),
    ("etiquetas", ("etiquetas",)),
    ("minutos", ("minutos_min", "minutos_max")),
]


def _celda(texto: Any) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def motivo_fuera(pregunta: Pregunta, pool: PoolConfig) -> Optional[str]:
    """Por qué el pool no puede elegir la pregunta (el primer filtro que no pasa), o None si puede."""
    from generador_examenes.core.logic import _minutos, candidatas_pool

    solo = {pregunta.id: pregunta}
    if pool.preguntas_fijadas:
        return None if pregunta.id in pool.preguntas_fijadas else "no está entre las fijadas"
    for nombre, campos in _FILTROS:
        valores = {c: getattr(pool, c) for c in campos}
        if not any(valores.values()) and valores.get("minutos_min") is None:
            continue
        if candidatas_pool(PoolConfig(**valores), solo):
            continue
        if nombre == "minutos":
            minutos = _minutos(pregunta)
            if minutos is None:
                return "no tiene minutos estimados"
            return f"{minutos} min, fuera de [{pool.minutos_min or 0}, {pool.minutos_max or '∞'}]"
        if nombre == "categoría":
            return f"categoría {pregunta.categoria}"
        if nombre == "tipo":
            return f"tipo {pregunta.tipo}"
        return f"etiquetas {', '.join(pregunta.etiquetas) or '(ninguna)'}"
    return None


def no_publicadas(rutas: Iterable[str]) -> List[Pregunta]:
    """Las consignas de las carpetas `rutas` que tienen `publicar: false`."""
    from generador_examenes.core.consignas import cargar_consignas

    resultado: List[Pregunta] = []
    for ruta in rutas:
        try:
            todas = cargar_consignas(ruta, incluir_no_publicados=True)
        except Exception:
            continue
        resultado += [p for p in todas.values() if not p.metadata.get("publicar", True)]
    return resultado


def armar_informe(definicion: DefinicionExamen, banco: Dict[str, Pregunta], examen_base: Dict[str, Any],
                  temas: List[Dict[str, Any]], semilla: int, formatos: List[str]) -> str:
    from generador_examenes.core.logic import candidatas_pool

    l: List[str] = [f"# Informe de generación: {definicion.nombre_examen}", ""]
    l.append(f"{datetime.now():%d/%m/%Y %H:%M} · semilla {semilla} · {len(temas)} tema(s) · "
             f"{', '.join(formatos)}")
    l += ["", "## Pools", "", "| Sección | Pool | Filtro | Podía elegir | Eligió |", "| --- | --- | --- | ---: | ---: |"]
    pools_consignas: List[PoolConfig] = []
    for seccion_def, seccion in zip(definicion.secciones_examen, examen_base.get("secciones", []), strict=False):
        ids_seccion = {p.id for p in seccion.get("preguntas", [])}
        for n, pool in enumerate(seccion_def.pools, 1):
            candidatas = candidatas_pool(pool, banco)
            elegidas = sum(1 for p in candidatas if p.id in ids_seccion)
            l.append(f"| {_celda(seccion_def.nombre)} | {n} | {_celda(pool)} | {len(candidatas)} | {elegidas} |")
            if "consigna_practica" in pool.tipos or any(p.tipo == "consigna_practica" for p in candidatas):
                pools_consignas.append(pool)

    l += ["", "## Preguntas", "", "| Sección | Pregunta | Tipo | Categoría | Banco | Puntaje |",
          "| --- | --- | --- | --- | --- | ---: |"]
    for seccion in examen_base.get("secciones", []):
        for p in seccion.get("preguntas", []):
            banco_p = Path(p.fuente_banco).name if p.fuente_banco else "—"
            l.append(f"| {_celda(seccion['nombre'])} | {_celda(p.nombre)} | {p.tipo} | {_celda(p.categoria)} | "
                     f"{_celda(banco_p)} | {p.puntaje:g} |")

    if len(temas) > 1:
        l += ["", "## Orden de cada tema", "",
              "Todos los temas tienen las mismas preguntas; cambian su orden y el de las opciones.", ""]
        for i, tema in enumerate(temas, 1):
            orden = [p.nombre for s in tema.get("secciones", []) for p in s.get("preguntas", [])]
            l.append(f"- **Tema {i}:** " + " → ".join(_celda(o) for o in orden))

    consignas = [p for p in banco.values() if p.tipo == "consigna_practica"]
    elegidas_ids = {p.id for s in examen_base.get("secciones", []) for p in s.get("preguntas", [])}
    fuera = []
    for c in consignas:
        if c.id in elegidas_ids or not pools_consignas:
            continue
        motivos = [m for m in (motivo_fuera(c, pool) for pool in pools_consignas) if m]
        if len(motivos) == len(pools_consignas):
            fuera.append(f"- «{_celda(c.nombre)}» ({c.id}): {'; '.join(dict.fromkeys(motivos))}")
    ocultas = no_publicadas(definicion.input_consignas or [])
    if fuera or ocultas:
        l += ["", "## Consignas que no podían entrar", ""]
        l += fuera
        l += [f"- «{_celda(c.nombre)}» ({c.id}): publicar: false" for c in ocultas]
    return "\n".join(l) + "\n"
