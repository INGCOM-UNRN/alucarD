"""Modo --watch: volver a generar cuando cambia una fuente (definición, bancos, consignas, imágenes).

Se miran las fechas de modificación cada `intervalo` segundos (sin dependencias ni inotify, igual en
las tres plataformas). Las rutas se recalculan en cada vuelta: si la definición suma un banco, se
empieza a mirar. La carpeta de salida no se mira nunca, así lo generado no dispara otra vuelta.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Tuple

Huella = Dict[Path, Tuple[float, int]]


def huella(rutas: Iterable[Path], excluir: Iterable[Path] = ()) -> Huella:
    """Fecha y tamaño de cada archivo de `rutas` (las carpetas, con todo lo que tienen)."""
    afuera = [e.resolve() for e in excluir]
    resultado: Huella = {}
    for ruta in rutas:
        ruta = Path(ruta).expanduser()
        archivos = sorted(ruta.rglob("*")) if ruta.is_dir() else [ruta]
        for a in archivos:
            try:
                a_res = a.resolve()
                if any(a_res.is_relative_to(e) for e in afuera) or not a.is_file():
                    continue
                st = a.stat()
            except OSError:
                continue
            resultado[a_res] = (st.st_mtime, st.st_size)
    return resultado


def vigilar(rutas: Callable[[], Iterable[Path]], accion: Callable[[], int], excluir: Iterable[Path] = (),
            intervalo: float = 1.0, vueltas: Optional[int] = None,
            dormir: Callable[[float], None] = time.sleep) -> int:
    """Corre `accion` y la repite cada vez que cambia algo de `rutas()`, hasta Ctrl+C.

    `vueltas` limita los sondeos (para las pruebas). Devuelve el código de la última corrida.
    """
    excluir = list(excluir)
    codigo = accion()
    anterior = huella(rutas(), excluir)
    print(f"\nMirando {len(anterior)} archivo(s); Ctrl+C para terminar.", file=sys.stderr)
    n = 0
    try:
        while vueltas is None or n < vueltas:
            n += 1
            dormir(intervalo)
            actual = huella(rutas(), excluir)
            if actual == anterior:
                continue
            cambiados = sorted({*actual} ^ {*anterior} | {r for r in actual if actual[r] != anterior.get(r)})
            nombres = ", ".join(p.name for p in cambiados[:3]) + ("…" if len(cambiados) > 3 else "")
            print(f"\n— Cambió {nombres}: generando de nuevo —", file=sys.stderr)
            codigo = accion()
            anterior = huella(rutas(), excluir)
    except KeyboardInterrupt:
        print("", file=sys.stderr)
    return codigo
