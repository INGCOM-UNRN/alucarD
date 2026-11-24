"""Caché de los bancos ya leídos: un banco que no cambió no se vuelve a parsear.

La clave es el contenido del archivo, su nombre y la versión del código de alucard (sus `.py`), así
que editar el banco o actualizar alucard la invalida sola. Se guarda en `~/.cache/alucard/bancos/`
(o `$XDG_CACHE_HOME`, o `ALUCARD_CACHE_DIR`), y `ALUCARD_SIN_CACHE=1` la apaga.

Con las preguntas se guardan los avisos que dio el parser, que se repiten al leer del caché: un
banco con un error lo sigue mostrando aunque no se vuelva a parsear.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from generador_examenes.core.models import Pregunta

logger = logging.getLogger(__name__)

FORMATO = 1                       # cambia si cambia lo que se guarda
_VENCE_DIAS = 60                  # una entrada sin usar en tanto tiempo se borra
_PAQUETE = Path(__file__).resolve().parents[1]
_podado = False


def activo() -> bool:
    return os.environ.get("ALUCARD_SIN_CACHE", "").strip().lower() in ("", "0", "false", "no")


def carpeta() -> Path:
    propia = os.environ.get("ALUCARD_CACHE_DIR")
    if propia:
        return Path(propia).expanduser()
    raiz = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return raiz / "alucard" / "bancos"


@lru_cache(maxsize=1)
def huella_codigo() -> str:
    """La versión del código: fecha y tamaño de cada `.py` del paquete, para que un cambio en los
    parsers (aunque no cambie el número de versión) no use lo leído con el código anterior."""
    from generador_examenes import __version__

    h = hashlib.sha256(f"{FORMATO}:{__version__}".encode())
    for py in sorted(_PAQUETE.rglob("*.py")):
        try:
            st = py.stat()
        except OSError:
            continue
        h.update(f"{py.relative_to(_PAQUETE)}:{st.st_mtime_ns}:{st.st_size}\n".encode())
    return h.hexdigest()


def clave(archivo: Path) -> str:
    """Contenido y nombre del banco, versión de alucard y cómo se dibujan los diagramas (el binario
    `dibu` y el theme activo), porque las preguntas se guardan con sus SVG ya dibujados."""
    from generador_examenes.diagramas import huella_render

    h = hashlib.sha256(huella_codigo().encode())
    h.update(f"\0{huella_render()}".encode())
    h.update(f"\0{archivo.name}\0".encode())
    h.update(archivo.read_bytes())
    return h.hexdigest()


class _Avisos(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.registros: list[tuple[str, int, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.registros.append((record.name, record.levelno, record.getMessage()))


def _leer(entrada: Path) -> dict | None:
    try:
        datos = json.loads(entrada.read_text(encoding="utf-8"))
        preguntas = {p["id"]: Pregunta.model_validate(p) for p in datos["preguntas"]}
        avisos = [(str(n), int(nivel), str(m)) for n, nivel, m in datos["avisos"]]
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError) as e:
        logger.debug(f"Caché de banco ilegible ({entrada}): {e}")
        return None
    try:
        os.utime(entrada)          # sigue en uso: no se poda
    except OSError:
        pass
    return {"preguntas": preguntas, "avisos": avisos}


def _escribir(entrada: Path, preguntas: dict[str, Pregunta], avisos: list[tuple[str, int, str]]) -> None:
    datos = {"preguntas": [p.model_dump(mode="json") for p in preguntas.values()], "avisos": avisos}
    try:
        entrada.parent.mkdir(parents=True, exist_ok=True)
        temporal = entrada.with_suffix(f".{os.getpid()}.tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        os.replace(temporal, entrada)
    except OSError as e:
        logger.debug(f"No se pudo guardar el caché del banco ({entrada}): {e}")
    _podar(entrada.parent)


def _podar(directorio: Path) -> None:
    global _podado
    if _podado:
        return
    _podado = True
    limite = time.time() - _VENCE_DIAS * 86400
    for viejo in directorio.glob("*.json"):
        try:
            if viejo.stat().st_mtime < limite:
                viejo.unlink()
        except OSError:
            pass


def leer_banco(archivo: Path, parsear: Callable[[Path], dict[str, Pregunta]]) -> dict[str, Pregunta]:
    """Las preguntas de `archivo`: del caché si el banco no cambió; si no, de `parsear`, y quedan
    guardadas para la próxima."""
    if not activo():
        return parsear(archivo)
    try:
        entrada = carpeta() / f"{clave(archivo)}.json"
    except OSError:
        return parsear(archivo)            # que el parser dé el error de lectura de siempre
    guardado = _leer(entrada)
    if guardado is not None:
        logger.info(f"Banco sin cambios, del caché: {archivo}")
        for nombre, nivel, mensaje in guardado["avisos"]:
            logging.getLogger(nombre).log(nivel, mensaje)
        return guardado["preguntas"]

    avisos = _Avisos()
    raiz = logging.getLogger("generador_examenes")
    raiz.addHandler(avisos)
    try:
        preguntas = parsear(archivo)
    finally:
        raiz.removeHandler(avisos)
    _escribir(entrada, preguntas, avisos.registros)
    return preguntas
