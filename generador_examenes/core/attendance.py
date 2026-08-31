"""Exportador de actas de asistencia y control en aula para ALUCARD."""

from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path


def generar_acta_asistencia(
    nombre_examen: str,
    alumnos: List[Dict[str, str]],
    output_path: Path | None = None,
) -> str:
    """Genera una planilla de control de asistencia y asignación de tema."""
    lineas = [
        f"# 📝 Acta de Asistencia y Firmas: {nombre_examen}",
        f"**Total de Estudiantes Inscriptos:** {len(alumnos)}\n",
        "| Padrón | Apellido y Nombre | Tema Asignado | Firma Entrega |",
        "|---|---|:---:|:---:|",
    ]

    for a in alumnos:
        padron = a.get("padron", "------")
        nombre = a.get("nombre", "Estudiante")
        tema = a.get("tema", "Tema 1")
        lineas.append(f"| `{padron}` | {nombre} | {tema} | [                      ] |")

    resultado = "\n".join(lineas)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(resultado, encoding="utf-8")
    return resultado
