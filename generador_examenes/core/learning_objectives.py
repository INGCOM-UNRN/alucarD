"""Mapeo de preguntas a objetivos de aprendizaje y cobertura curricular."""

from __future__ import annotations

from typing import Dict, List, Any


def auditar_cobertura_objetivos(preguntas: List[Any], objetivos_materia: List[str] | None = None) -> Dict[str, Any]:
    """Evalúa la cobertura de objetivos pedagógicos según las preguntas del examen."""
    objetivos_default = [
        "Manejo de Punteros y Memoria Dinámica",
        "Estructuras de Datos y Tipos Abstractos (TDAs)",
        "Control de Flujo, Bucles y Modularización",
        "Recursión y Complejidad Algorítmica",
        "Manejo de Archivos y Persistencia",
    ]
    objs = objetivos_materia or objetivos_default
    cobertura = {o: 0 for o in objs}

    for p in preguntas:
        texto = getattr(p, "enunciado", "") if hasattr(p, "enunciado") else str(p.get("enunciado", ""))
        txt_low = texto.lower()
        if "malloc" in txt_low or "free" in txt_low or "puntero" in txt_low or "*" in txt_low:
            cobertura[objs[0]] += 1
        if "struct" in txt_low or "nodo" in txt_low or "tda" in txt_low or "lista" in txt_low:
            cobertura[objs[1]] += 1
        if "for" in txt_low or "while" in txt_low or "if" in txt_low or "funcion" in txt_low:
            cobertura[objs[2]] += 1
        if "recursiv" in txt_low or "caso base" in txt_low or "o(n" in txt_low:
            cobertura[objs[3]] += 1
        if "fopen" in txt_low or "fclose" in txt_low or "fread" in txt_low or "archivo" in txt_low:
            cobertura[objs[4]] += 1

    cubiertos = sum(1 for v in cobertura.values() if v > 0)
    porcentaje = (cubiertos / len(objs)) * 100 if objs else 100.0

    return {
        "cobertura_por_objetivo": cobertura,
        "objetivos_totales": len(objs),
        "objetivos_cubiertos": cubiertos,
        "porcentaje_cobertura": round(porcentaje, 1),
        "balance_optimo": porcentaje >= 60.0,
    }
