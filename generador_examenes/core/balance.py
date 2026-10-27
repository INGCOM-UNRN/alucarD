"""Balance de la posición de la opción correcta en los temas generados (`alucard balance-check`, Ola 14).

`mezclar_examen` reparte la correcta entre las letras (ver `logic.asignar_posiciones_correctas`);
esta auditoría lo verifica sobre las variantes que se van a imprimir: cuenta en qué letra quedó la
correcta de cada pregunta de selección múltiple, en cada tema y en total, y avisa si alguna letra
supera el umbral (30 % por omisión). Con preguntas de 2 o 3 opciones el mínimo alcanzable es mayor
(una de 3 opciones reparte en tercios): el umbral efectivo es el mayor entre el pedido y lo que el
banco permite (el reparto ideal más 5 puntos), y se informa.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

UMBRAL_POR_OMISION = 0.30


def definicion_implicita(bancos: Sequence[Path], titulo: Optional[str] = None, materia: str = "",
                         institucion: str = "") -> Dict[str, Any]:
    """Una definición con todas las preguntas de los bancos en una sección: para `alucard build -i banco`
    sin YAML (por ejemplo, el Moodle XML que genera idkfa)."""
    nombre = titulo or (Path(bancos[0]).stem.replace("_", " ") if bancos else "Examen")
    return {
        "nombre_examen": nombre,
        "institucion": institucion,
        "materia": materia,
        "configuracion_examen": {"mezclar_preguntas_dentro_seccion": True, "mezclar_opciones_dentro_pregunta": True,
                                 "generar_clave_profesor": True},
        "secciones_examen": [{"nombre": "Preguntas", "pools": [{"accion_si_insuficiente": "usar_todas"}]}],
    }


def armar_temas(definicion, bancos: Sequence[Path], numero_temas: int, semilla: int) -> List[Dict[str, Any]]:
    """Los temas tal como los genera `alucard` (misma semilla por tema), sin renderizarlos."""
    from generador_examenes.core import logic

    banco = logic.cargar_bancos(list(bancos))
    base = logic.construir_pool_examen(definicion, banco)
    uso_global: Dict[int, int] = {}
    return [logic.mezclar_examen(base, semilla + i, definicion.configuracion_examen, uso_global=uso_global)
            for i in range(numero_temas)]


def auditar_balance(temas: Sequence[Dict[str, Any]], umbral: float = UMBRAL_POR_OMISION) -> Dict[str, Any]:
    """Frecuencia de cada letra correcta por tema y en total, y si alguna supera el umbral efectivo."""
    por_tema: List[Dict[str, int]] = []
    total: Dict[str, int] = {}
    ideal: Dict[str, float] = {}
    preguntas = 0
    for tema in temas:
        conteo: Dict[str, int] = {}
        for seccion in tema.get("secciones", []):
            for pregunta in seccion.get("preguntas", []):
                if pregunta.tipo != "seleccion_multiple" or len(pregunta.opciones) < 2:
                    continue
                indices = [i for i, o in enumerate(pregunta.opciones) if o.es_correcta]
                if len(indices) != 1:
                    continue
                letra = chr(ord("A") + indices[0])
                conteo[letra] = conteo.get(letra, 0) + 1
                total[letra] = total.get(letra, 0) + 1
                preguntas += 1
                for i in range(len(pregunta.opciones)):  # el reparto ideal: 1/k para cada una de sus k letras
                    l_ = chr(ord("A") + i)
                    ideal[l_] = ideal.get(l_, 0.0) + 1 / len(pregunta.opciones)
        por_tema.append(dict(sorted(conteo.items())))
    frecuencias = {letra: round(n / preguntas, 4) for letra, n in sorted(total.items())} if preguntas else {}
    minimo = max((v / preguntas for v in ideal.values()), default=0.0) if preguntas else 0.0
    efectivo = max(umbral, round(minimo + 0.05, 4))
    mas_frecuente = max(frecuencias, key=lambda letra: frecuencias[letra]) if frecuencias else None
    return {
        "schema_version": "1.0.0",
        "temas": len(temas),
        "preguntas_por_tema": preguntas // len(temas) if temas else 0,
        "por_tema": por_tema,
        "global": dict(sorted(total.items())),
        "frecuencias": frecuencias,
        "umbral": umbral,
        "umbral_efectivo": efectivo,
        "minimo_alcanzable": round(minimo, 4),
        "letra_mas_frecuente": mas_frecuente,
        "ok": mas_frecuente is None or frecuencias[mas_frecuente] <= efectivo,
    }


def texto_del_informe(reporte: Dict[str, Any]) -> str:
    if not reporte["frecuencias"]:
        return "No hay preguntas de selección múltiple con una sola correcta: nada que balancear."
    letras = list(reporte["frecuencias"])
    lineas = ["Posición de la opción correcta (selección múltiple)", "",
              "| Tema | " + " | ".join(letras) + " |", "| :-: | " + " | ".join(":-:" for _ in letras) + " |"]
    for n, conteo in enumerate(reporte["por_tema"], 1):
        lineas.append(f"| {n} | " + " | ".join(str(conteo.get(letra, 0)) for letra in letras) + " |")
    lineas.append("| **Total** | " + " | ".join(f"{reporte['global'][letra]} ({reporte['frecuencias'][letra]:.0%})"
                                               for letra in letras) + " |")
    lineas.append("")
    letra = reporte["letra_mas_frecuente"]
    umbral = f"{reporte['umbral_efectivo']:.0%}"
    if reporte["umbral_efectivo"] > reporte["umbral"]:
        umbral += (f" (pedido {reporte['umbral']:.0%}; con las opciones de este banco el mínimo es "
                   f"{reporte['minimo_alcanzable']:.0%})")
    if reporte["ok"]:
        lineas.append(f"✓ Ninguna letra supera {umbral}: la más frecuente es {letra} con "
                      f"{reporte['frecuencias'][letra]:.0%}.")
    else:
        lineas.append(f"✗ La {letra} es la correcta en el {reporte['frecuencias'][letra]:.0%} de los casos "
                      f"(máximo {umbral}): quien contesta por frecuencia saca ventaja.")
    return "\n".join(lineas)
