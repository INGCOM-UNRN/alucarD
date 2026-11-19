"""La nómina: quién rinde, con qué `student_id` interno y qué variante (§3.2).

`inscriptos.csv` trae `legajo,apellido,nombre` y, si ya se asignaron, `student_id` y `variante`.
A los que no traen `student_id` se les da el siguiente libre de `C001`…`C999`, en el orden de la
nómina: no se deriva del legajo ni del DNI. Las variantes que faltan se reparten en ronda.

`roster_<exam_id>.csv` (UTF-8 con BOM) es el único vínculo entre `student_id` y la persona.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

STUDENT_ID = re.compile(r"^[A-Z0-9]{1,8}$")
COLUMNAS = ("student_id", "legajo", "apellido", "nombre", "variante")
MAXIMO_AUTOMATICO = 999


class ErrorNomina(ValueError):
    def __init__(self, archivo: str, problemas: list[str]):
        self.problemas = problemas
        super().__init__(f"{archivo}: " + "; ".join(problemas))


@dataclass(frozen=True)
class Inscripto:
    student_id: str
    legajo: str
    apellido: str
    nombre: str
    variante: str

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellido}, {self.nombre}" if self.nombre else self.apellido


def leer(ruta: Path, variantes: tuple[str, ...]) -> list[Inscripto]:
    try:
        with ruta.open(encoding="utf-8-sig", newline="") as f:
            lector = csv.DictReader(f)
            filas = list(lector)
            columnas = {c.strip().lower() for c in (lector.fieldnames or []) if c}
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        raise ErrorNomina(str(ruta), [f"no se puede leer: {e}"]) from e
    return asignar(ruta.name, filas, columnas, variantes)


def asignar(nombre: str, filas: list[dict], columnas: set[str], variantes: tuple[str, ...]) -> list[Inscripto]:
    problemas: list[str] = []
    faltan = [c for c in ("legajo", "apellido", "nombre") if c not in columnas]
    if not filas:
        raise ErrorNomina(nombre, ["la nómina está vacía"])
    if faltan:
        raise ErrorNomina(nombre, [f"faltan las columnas {', '.join(faltan)} (van legajo,apellido,nombre)"])

    def valor(fila: dict, columna: str) -> str:
        for clave, v in fila.items():
            if clave is not None and clave.strip().lower() == columna:
                return (v or "").strip()
        return ""

    usados: set[str] = set()
    legajos: set[str] = set()
    for n, fila in enumerate(filas, 2):
        sid = valor(fila, "student_id").upper()
        if sid:
            if not STUDENT_ID.match(sid):
                problemas.append(f"fila {n}: student_id {sid!r} tiene que ser de 1 a 8 letras mayúsculas o dígitos")
            elif sid in usados:
                problemas.append(f"fila {n}: student_id {sid} repetido")
            usados.add(sid)
        legajo = valor(fila, "legajo")
        if not legajo:
            problemas.append(f"fila {n}: falta el legajo")
        elif legajo in legajos:
            problemas.append(f"fila {n}: legajo {legajo} repetido")
        legajos.add(legajo)
        if not valor(fila, "apellido"):
            problemas.append(f"fila {n}: falta el apellido")
        var = valor(fila, "variante").upper()
        if var and var not in variantes:
            problemas.append(f"fila {n}: la variante {var} no está en variants ({', '.join(variantes)})")
    if problemas:
        raise ErrorNomina(nombre, problemas)

    libres = (f"C{i:03d}" for i in range(1, MAXIMO_AUTOMATICO + 1) if f"C{i:03d}" not in usados)
    inscriptos, ronda = [], 0
    for fila in filas:
        sid = valor(fila, "student_id").upper()
        if not sid:
            sid = next(libres, None)
            if sid is None:
                raise ErrorNomina(nombre, [f"más de {MAXIMO_AUTOMATICO} inscriptos sin student_id"])
        var = valor(fila, "variante").upper()
        if not var:
            var = variantes[ronda % len(variantes)]
            ronda += 1
        inscriptos.append(Inscripto(student_id=sid, legajo=valor(fila, "legajo"), apellido=valor(fila, "apellido"),
                                    nombre=valor(fila, "nombre"), variante=var))
    return inscriptos


def escribir(inscriptos: list[Inscripto], destino: Path) -> None:
    with destino.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUMNAS)
        for i in inscriptos:
            escritor.writerow([i.student_id, i.legajo, i.apellido, i.nombre, i.variante])
