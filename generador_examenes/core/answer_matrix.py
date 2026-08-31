"""Generador de matrices de claves de corrección diferenciadas por tema."""

from __future__ import annotations

from typing import Dict, List, Any
from pathlib import Path


def generar_matriz_respuestas_temas(examenes_por_tema: List[Dict[str, Any]]) -> str:
    """Genera una matriz comparativa en Markdown de respuestas correctas por tema."""
    lineas = ["# 📋 Matriz Docente de Respuestas y Claves de Corrección\n"]
    lineas.append("| Pregunta | " + " | ".join([f"Tema {i+1}" for i in range(len(examenes_por_tema))]) + " |")
    lineas.append("|" + "---|" * (len(examenes_por_tema) + 1))

    # Suponiendo que todos los temas tienen la misma cantidad de preguntas
    max_preguntas = max((len(t.get("preguntas", [])) for t in examenes_por_tema), default=0)

    for p_idx in range(max_preguntas):
        fila = [f"**P{p_idx + 1}**"]
        for t in examenes_por_tema:
            pregs = t.get("preguntas", [])
            if p_idx < len(pregs):
                p = pregs[p_idx]
                ans = getattr(p, "respuesta_correcta", "Desarrollo") if hasattr(p, "respuesta_correcta") else p.get("respuesta_correcta", "Desarrollo")
                fila.append(f"`{ans}`")
            else:
                fila.append("—")
        lineas.append("| " + " | ".join(fila) + " |")

    return "\n".join(lineas)
