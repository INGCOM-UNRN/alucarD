"""Calibrador dinámico de espacio para desarrollo en ALUCARD."""

from __future__ import annotations

from typing import Dict, Any, List


def calibrar_espacio_desarrollo(pregunta: Dict[str, Any] | Any) -> Dict[str, Any]:
    """Calcula la cantidad recomendada de renglones o cuadrícula para preguntas de desarrollo."""
    texto = getattr(pregunta, "enunciado", "") if hasattr(pregunta, "enunciado") else str(pregunta.get("enunciado", ""))
    tipo = getattr(pregunta, "tipo", "") if hasattr(pregunta, "tipo") else str(pregunta.get("tipo", ""))

    lineas_base = 6
    if "implement" in texto.lower() or "escriba" in texto.lower() or "desarrolle" in texto.lower():
        lineas_base = 14
    if "tda" in texto.lower() or "struct" in texto.lower() or "puntero" in texto.lower():
        lineas_base = 20

    usar_hoja_extra = lineas_base > 18
    return {
        "lineas_sugeridas": lineas_base,
        "tipo_espacio": "cuadricula" if "codigo" in texto.lower() else "renglones",
        "usar_hoja_extra": usar_hoja_extra,
        "nota_estudiante": "Usar hoja adjunta si el espacio es insuficiente." if usar_hoja_extra else "Responder en el recuadro.",
    }
