"""Exportador directo de examen a cuestionario Moodle XML evaluable."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Dict, List, Any


def exportar_a_moodle_xml(examen: Dict[str, Any], output_path: Path) -> Path:
    """Convierte el pool de preguntas del examen en un archivo Moodle XML importable."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n']
    
    # Categoría raíz
    cat_name = examen.get("nombre", "Examen ALUCARD")
    xml_parts.append(f"""  <question type="category">
    <category>
      <text>$course$/top/{html.escape(cat_name)}</text>
    </category>
  </question>\n""")

    secciones = examen.get("secciones", [])
    for sec in secciones:
        preguntas = sec.get("preguntas", [])
        for idx, p in enumerate(preguntas):
            enunciado = getattr(p, "enunciado", "") if hasattr(p, "enunciado") else str(p.get("enunciado", ""))
            titulo = getattr(p, "titulo", f"Pregunta {idx+1}") if hasattr(p, "titulo") else str(p.get("titulo", f"Pregunta {idx+1}"))
            puntaje = getattr(p, "puntaje", 1.0) if hasattr(p, "puntaje") else float(p.get("puntaje", 1.0))

            xml_parts.append(f"""  <question type="essay">
    <name><text>{html.escape(titulo)}</text></name>
    <questiontext format="html">
      <text><![CDATA[{enunciado}]]></text>
    </questiontext>
    <defaultgrade>{puntaje}</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
  </question>\n""")

    xml_parts.append("</quiz>\n")
    content = "".join(xml_parts)
    out.write_text(content, encoding="utf-8")
    return out
