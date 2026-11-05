"""Reparto de los temas generados entre estudiantes, para entregarlos con uatu (Ola 47).

alucarD arma el examen en papel: esto no cifra ni publica nada. Copia el PDF del tema que le toca a
cada estudiante a `<salida>/<usuario>/examen.pdf`, la carpeta que espera `uatu-admin paquetes
sellar`. Las claves de corrección (`clave_tema_*`) nunca se copian. La asignación queda al lado de
la salida, no adentro: si no, se sellaría junto con los exámenes.
"""

from __future__ import annotations

import csv
import random
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

_USUARIO = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?")


class RepartoError(ValueError):
    """El padrón, los temas o la carpeta de salida no permiten repartir."""


@dataclass
class Reparto:
    asignacion: Dict[str, str]  # usuario → archivo del tema
    registro: Path


def leer_padron(ruta: Path) -> List[str]:
    """Usuarios de GitHub, uno por línea (se ignoran las líneas vacías y lo que sigue a un #)."""
    usuarios: List[str] = []
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        usuario = linea.split("#", 1)[0].strip().lower()
        if not usuario:
            continue
        if not _USUARIO.fullmatch(usuario):
            raise RepartoError(f"{ruta}:{numero}: '{usuario}' no es un usuario de GitHub válido.")
        if usuario in usuarios:
            raise RepartoError(f"{ruta}:{numero}: '{usuario}' está repetido.")
        usuarios.append(usuario)
    if not usuarios:
        raise RepartoError(f"{ruta} no tiene usuarios.")
    return usuarios


def asignar(usuarios: List[str], temas: List[Path], semilla: int) -> Dict[str, Path]:
    """Los temas en partes iguales (difieren en uno como mucho), en orden sorteado con la semilla."""
    orden = sorted(usuarios)
    random.Random(semilla).shuffle(orden)
    return {usuario: temas[i % len(temas)] for i, usuario in enumerate(orden)}


def repartir(temas_dir: Path, padron: Path, salida: Path, semilla: int) -> Reparto:
    temas = sorted(temas_dir.glob("examen_tema_*.pdf"))
    if not temas:
        raise RepartoError(f"{temas_dir} no tiene temas (examen_tema_*.pdf): generalos con `alucard build -f pdf`.")
    if salida.exists() and any(salida.iterdir()):
        raise RepartoError(f"{salida} no está vacía: un reparto viejo se sellaría junto con el nuevo.")
    usuarios = leer_padron(padron)
    asignacion = asignar(usuarios, temas, semilla)
    for usuario, tema in asignacion.items():
        destino = salida / usuario
        destino.mkdir(parents=True)
        shutil.copyfile(tema, destino / "examen.pdf")
    registro = salida.with_name(salida.name + ".asignacion.csv")
    with registro.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(["usuario", "tema"])
        escritor.writerows((u, asignacion[u].name) for u in sorted(asignacion))
    return Reparto({u: t.name for u, t in asignacion.items()}, registro)
