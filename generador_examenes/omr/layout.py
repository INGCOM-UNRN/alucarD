"""El manifiesto geométrico `omr-layout/2`: la única fuente de las coordenadas de la carátula (§4).

Las coordenadas van en milímetros desde el centroide del marcador ArUco 0. La plantilla Typst lee
el mismo archivo con `json()` y `verify-geometry` mide en el PDF que cada burbuja quedó donde dice.

El layout estándar por filas (§4.2, compatible con el QR compacto `OMRCFG/2`):

- una fila por ejercicio desde `y = 12`, `+8` mm cada una, con burbujas desde `x = 32` cada `8` mm;
- `+4` mm de separación y una fila por cifra de la nota final, `+8` mm cada una;
- `ausente` en `x = 162`, `y = max(24, última fila)`;
- `frame_mm.h = max(55, última fila + 10)`: con la rúbrica de ejemplo de la SPEC da los 74 mm de
  su manifiesto.
"""

from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path
from typing import Any

from generador_examenes.omr.config import ConfigExamen, EscalaNotas

ESQUEMA = "omr-layout/2"
ANCHO_MARCO = 180.0
MARCADOR = 10.0
PX_POR_MM = 10
DIAMETRO = 5.0
PASO = 8.0
X0, Y0 = 32.0, 12.0
SEPARACION_NOTA = 4.0
X_AUSENTE, Y_AUSENTE_MIN = 162.0, 24.0
ALTO_MINIMO = 55.0

# DICT_4X4_50, ids 0 a 3: la matriz interior 4×4 por filas, 1 = blanco y 0 = negro (§4.1).
ARUCO = {
    0: ("1011", "0101", "0011", "0010"),
    1: ("0000", "1111", "1001", "1010"),
    2: ("0011", "0011", "0001", "1000"),
    3: ("1001", "1001", "0100", "0111"),
}


def filas_nota(escala: EscalaNotas) -> list[dict[str, Any]]:
    """Las filas de `decimal_digits` según la escala (tabla de §4.2), sin coordenadas."""
    unidades = {"place": 1.0, "start": int(escala.min), "count": int(escala.max) - int(escala.min) + 1}
    if escala.step == 0.5:
        return [unidades, {"place": 0.1, "start": 0, "count": 2, "values": [0, 5]}]
    if escala.step == 0.25:
        return [unidades, {"place": 0.01, "start": 0, "count": 4, "values": [0, 25, 50, 75]}]
    filas = [unidades]
    for lugar in (0.1, 0.01)[:escala.decimals]:
        filas.append({"place": lugar, "start": 0, "count": 10})
    return filas


def construir(config: ConfigExamen) -> dict[str, Any]:
    """El manifiesto del layout estándar por filas."""
    campos: list[dict[str, Any]] = []
    y = Y0
    for e in config.rubric:
        campos.append({
            "id": e.id, "label": e.label, "type": "single_choice", "required": True,
            "max_points": e.max_points, "levels": e.levels,
            "options": [{"step": paso, "label": etiqueta, "x_mm": X0 + PASO * paso, "y_mm": y}
                        for paso, etiqueta in enumerate(e.etiquetas())],
        })
        y += PASO
    y += SEPARACION_NOTA
    digitos = []
    for fila in filas_nota(config.grade_scale):
        digitos.append({**{k: v for k, v in fila.items() if k != "values"}, "x0_mm": X0, "y0_mm": y,
                        "step_mm": PASO, "axis": "x", **({"values": fila["values"]} if "values" in fila else {})})
        y += PASO
    ultima = y - PASO
    campos.append({"id": "nota_final", "label": "Nota final", "type": "decimal_digits", "required": True,
                   "role": "final_grade", "digits": digitos})
    campos.append({"id": "ausente", "label": "Ausente", "type": "flag", "required": False,
                   "x_mm": X_AUSENTE, "y_mm": max(Y_AUSENTE_MIN, ultima)})
    escala, curva = config.grade_scale, config.grade_map
    return {
        "schema": ESQUEMA,
        "layout_id": config.layout_id,
        "version": config.layout_version,
        "frame_mm": {"w": ANCHO_MARCO, "h": max(ALTO_MINIMO, ultima + 10.0)},
        "marker_mm": MARCADOR,
        "px_per_mm": PX_POR_MM,
        "bubble_diameter_mm": DIAMETRO,
        "grade_scale": {"min": escala.min, "max": escala.max, "decimals": escala.decimals, "step": escala.step,
                        "rounding": escala.rounding, "match_tolerance": escala.match_tolerance},
        "grade_map": {"type": curva.type, "pass_pct": curva.pass_pct, "pass_grade": curva.pass_grade,
                      "promo_pct": curva.promo_pct, "promo_grade": curva.promo_grade, "curve_k": curva.curve_k,
                      "fail_curve": curva.fail_curve},
        "fields": campos,
    }


def burbujas(manifiesto: dict[str, Any]) -> list[tuple[str, str, float, float]]:
    """Cada burbuja del manifiesto: (campo, valor, x_mm, y_mm)."""
    salida = []
    for campo in manifiesto["fields"]:
        if campo["type"] == "single_choice":
            salida += [(campo["id"], str(o["step"]), o["x_mm"], o["y_mm"]) for o in campo["options"]]
        elif campo["type"] == "decimal_digits":
            for fila in campo["digits"]:
                valores = fila.get("values") or [fila["start"] + i for i in range(fila["count"])]
                for i, valor in enumerate(valores):
                    x = fila["x0_mm"] + (fila["step_mm"] * i if fila["axis"] == "x" else 0)
                    y = fila["y0_mm"] + (fila["step_mm"] * i if fila["axis"] == "y" else 0)
                    salida.append((f"{campo['id']}@{fila['place']:g}", str(valor), x, y))
        elif campo["type"] == "flag":
            salida.append((campo["id"], "1", campo["x_mm"], campo["y_mm"]))
    return salida


@cache
def esquema(nombre: str = "omr-layout-2") -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "esquemas" / f"{nombre}.schema.json").read_text(encoding="utf-8"))


def problemas(manifiesto: dict[str, Any]) -> list[str]:
    """Lo que no cumple el JSON Schema `omr-layout/2` o las reglas de rango que el esquema no expresa."""
    import jsonschema

    validador = jsonschema.Draft202012Validator(esquema())
    salida = [f"{'/'.join(map(str, e.absolute_path)) or '(raíz)'}: {e.message}"
              for e in sorted(validador.iter_errors(manifiesto), key=lambda e: list(map(str, e.absolute_path)))]
    if salida:
        return salida
    escala, curva = manifiesto["grade_scale"], manifiesto["grade_map"]
    if escala["min"] >= escala["max"]:
        salida.append("grade_scale: min tiene que ser menor que max")
    if curva["promo_pct"] is not None:
        if not curva["pass_pct"] < curva["promo_pct"] < 100:
            salida.append("grade_map: promo_pct tiene que estar entre pass_pct y 100")
        if curva["promo_grade"] is None or not curva["pass_grade"] < curva["promo_grade"] < escala["max"]:
            salida.append("grade_map: promo_grade tiene que estar entre pass_grade y max")
    ids = [c["id"] for c in manifiesto["fields"]]
    if len(ids) != len(set(ids)):
        salida.append("fields: hay ids repetidos")
    radio = manifiesto["bubble_diameter_mm"] / 2
    w, h = manifiesto["frame_mm"]["w"], manifiesto["frame_mm"]["h"]
    for campo, valor, x, y in burbujas(manifiesto):
        if not (radio <= x <= w - radio and radio <= y <= h - radio):
            salida.append(f"{campo}={valor}: la burbuja ({x:g}, {y:g}) sale del marco de {w:g} × {h:g} mm")
    return salida


def serializar(manifiesto: dict[str, Any]) -> bytes:
    return (json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def nombre_archivo(config: ConfigExamen) -> str:
    return f"layout_{config.layout_id}_v{config.layout_version}.json"


def escribir(manifiesto: dict[str, Any], destino: Path) -> str:
    """Escribe el manifiesto y su `.sha256` (formato de `sha256sum`); devuelve el hash."""
    datos = serializar(manifiesto)
    destino.write_bytes(datos)
    huella = hashlib.sha256(datos).hexdigest()
    destino.with_suffix(".sha256").write_text(f"{huella}  {destino.name}\n", encoding="utf-8")
    return huella
