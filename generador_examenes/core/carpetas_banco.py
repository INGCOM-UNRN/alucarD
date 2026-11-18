"""Categorías y etiquetas de las preguntas a partir de las carpetas de un banco.

Cuando `input_banco` (o `-i`) nombra una carpeta, un `banco.toml` en ella o en cualquiera de sus
subcarpetas dice cómo usar la ruta de cada archivo. Las claves de un `banco.toml` valen para su
carpeta y todo lo que tiene adentro; uno más adentro cambia sólo las claves que escribe.

```toml
categoria = "prefijo"          # "archivo" | "carpeta" | "prefijo" | "si_falta"
etiquetas = true               # cada carpeta, una etiqueta
incluir_archivo = false        # el nombre del archivo, sin extensión, también cuenta como carpeta
agregar_etiquetas = ["parcial1"]
```
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path

from generador_examenes.core.models import Pregunta

ARCHIVO = "banco.toml"
MODOS_CATEGORIA = ("archivo", "carpeta", "prefijo", "si_falta")
# La categoría que ponen los parsers cuando el archivo no trae ninguna.
SIN_CATEGORIA = "General"
_CLAVES = {"categoria", "etiquetas", "incluir_archivo", "agregar_etiquetas"}


@dataclass(frozen=True)
class ReglasCarpeta:
    categoria: str = "archivo"
    etiquetas: bool = False
    incluir_archivo: bool = False
    agregar_etiquetas: tuple[str, ...] = field(default_factory=tuple)

    @property
    def activas(self) -> bool:
        return self != ReglasCarpeta()


def _leer(ruta: Path, base: ReglasCarpeta) -> ReglasCarpeta:
    """Las reglas de `base` con lo que cambia el `banco.toml` de `ruta`. Un archivo mal escrito es
    un error con su nombre."""
    try:
        datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{ruta}: {e}") from e
    desconocidas = sorted(set(datos) - _CLAVES)
    if desconocidas:
        raise ValueError(f"{ruta}: claves desconocidas: {', '.join(desconocidas)} "
                         f"(valen {', '.join(sorted(_CLAVES))})")
    cambios: dict = {}
    if "categoria" in datos:
        if datos["categoria"] not in MODOS_CATEGORIA:
            raise ValueError(f"{ruta}: categoria es {', '.join(repr(m) for m in MODOS_CATEGORIA)}: "
                             f"{datos['categoria']!r}")
        cambios["categoria"] = datos["categoria"]
    for clave in ("etiquetas", "incluir_archivo"):
        if clave in datos:
            if not isinstance(datos[clave], bool):
                raise ValueError(f"{ruta}: {clave} es true o false: {datos[clave]!r}")
            cambios[clave] = datos[clave]
    if "agregar_etiquetas" in datos:
        valor = datos["agregar_etiquetas"]
        if not isinstance(valor, list) or not all(isinstance(v, str) and v.strip() for v in valor):
            raise ValueError(f"{ruta}: agregar_etiquetas es una lista de textos: {valor!r}")
        cambios["agregar_etiquetas"] = tuple(v.strip() for v in valor)
    return replace(base, **cambios)


class ReglasDeCarpetas:
    """Las reglas de cada archivo de una carpeta de bancos, leyendo cada `banco.toml` una vez."""

    def __init__(self, raiz: Path):
        self.raiz = raiz
        self._por_carpeta: dict[Path, ReglasCarpeta] = {}

    def de_carpeta(self, carpeta: Path) -> ReglasCarpeta:
        if carpeta in self._por_carpeta:
            return self._por_carpeta[carpeta]
        base = ReglasCarpeta() if carpeta == self.raiz or carpeta == carpeta.parent else self.de_carpeta(carpeta.parent)
        archivo = carpeta / ARCHIVO
        reglas = _leer(archivo, base) if archivo.is_file() else base
        self._por_carpeta[carpeta] = reglas
        return reglas

    def de_archivo(self, archivo: Path) -> ReglasCarpeta:
        return self.de_carpeta(archivo.parent)


def niveles(archivo: Path, raiz: Path, incluir_archivo: bool) -> list[str]:
    """Las carpetas entre `raiz` y `archivo` (sin `raiz`) y, si se pide, el nombre del archivo."""
    partes = list(archivo.relative_to(raiz).parent.parts)
    if incluir_archivo:
        partes.append(archivo.stem)
    return partes


def _sin_contexto_moodle(categoria: str) -> str:
    """`$course$/Top/Punteros` → `Punteros`: el contexto de Moodle no aporta debajo de una carpeta."""
    partes = [p for p in re.split(r"\s*/\s*", categoria.strip()) if p]
    while partes and (re.fullmatch(r"\$\w+\$", partes[0]) or partes[0].lower() in ("top", "default")):
        partes.pop(0)
    return "/".join(partes)


def categoria(propia: str, carpetas: list[str], modo: str) -> str:
    if not carpetas or modo == "archivo":
        return propia
    de_carpeta = "/".join(carpetas)
    sin_categoria = not propia or propia == SIN_CATEGORIA
    if modo == "carpeta":
        return de_carpeta
    if modo == "si_falta":
        return de_carpeta if sin_categoria else propia
    # prefijo
    resto = "" if sin_categoria else _sin_contexto_moodle(propia)
    return f"{de_carpeta}/{resto}" if resto else de_carpeta


def aplicar(preguntas: Iterable[Pregunta], archivo: Path, raiz: Path, reglas: ReglasCarpeta) -> None:
    """Cambia, en el lugar, la categoría y las etiquetas de las preguntas de `archivo`."""
    if not reglas.activas:
        return
    carpetas = niveles(archivo, raiz, reglas.incluir_archivo)
    nuevas = [*(carpetas if reglas.etiquetas else []), *reglas.agregar_etiquetas]
    for pregunta in preguntas:
        pregunta.categoria = categoria(pregunta.categoria, carpetas, reglas.categoria)
        for etiqueta in nuevas:
            if etiqueta not in pregunta.etiquetas:
                pregunta.etiquetas.append(etiqueta)

