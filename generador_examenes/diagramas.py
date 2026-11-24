"""Adaptador de diagramas SVG de alucarD hacia el binario externo `dibu`.

Delega el renderizado de los 44 tipos de diagramas (estructuras de datos/CS,
control de procesos y química general/orgánica/inorgánica) a `dibu batch`
(protocolo JSONL por stdin/stdout: 1 solo proceso por documento o directorio).
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

# Paletas de statics: `tinta` (ahorro de tinta, para imprimir) y color.
PALETAS = {
    True: {
        "strokeMain": "#000000", "strokeSub": "#334155", "strokeMuted": "#64748b", "fillHeader": "#f8fafc",
        "fillCell": "#ffffff", "fillPointerBox": "#f1f5f9", "fillBadge": "#ffffff", "accentPrimary": "#000000",
        "textMain": "#000000", "textSub": "#334155", "textMuted": "#475569", "fillHighlight": "#e2e8f0",
    },
    False: {
        "strokeMain": "#0f172a", "strokeSub": "#1e40af", "strokeMuted": "#64748b", "fillHeader": "#eff6ff",
        "fillCell": "#ffffff", "fillPointerBox": "#e0f2fe", "fillBadge": "#dbeafe", "accentPrimary": "#1d4ed8",
        "textMain": "#0f172a", "textSub": "#1e3a8a", "textMuted": "#475569", "fillHighlight": "#fef3c7",
    },
}

TIPOS: Tuple[str, ...] = (
    "adt", "array", "block_diagram", "bode", "born_haber", "call_stack", "call_tree", "chair",
    "complex", "complexity", "cost_table", "crystal_field", "energy_profile", "fischer", "flowchart",
    "frost", "galvanic_cell", "grafcet", "heating_curve", "instrumentation", "kinetics", "ladder",
    "latimer", "linked_list", "matrix", "molecule", "newman", "nyquist", "orbitals", "phase_diagram",
    "pole_zero", "queue", "reaction", "root_locus", "speciation", "spectrum", "stack", "struct",
    "time_response", "titration", "trace_table", "tree", "unit_cell", "vsepr",
)

DIR_SVGS = "diagramas"

_FENCE = re.compile(
    r"^(?P<valla>`{3,}|~{3,})[ \t]*(?:estructura|statics)[ \t]*\n(?P<cuerpo>.*?)^(?P=valla)[ \t]*$",
    re.S | re.M,
)


class ErrorDiagrama(ValueError):
    """Un bloque que no se puede dibujar (tipo desconocido, datos inválidos o falta `dibu`)."""


def _esc(valor: Any) -> str:
    return html.escape("" if valor is None else str(valor), quote=True)


def binario_dibu() -> Optional[str]:
    """Ruta al binario `dibu` (respeta `ALUCARD_DIBU` / `DIBU_BIN` o busca en `$PATH`)."""
    for var in ("ALUCARD_DIBU", "DIBU_BIN"):
        candidato = os.environ.get(var)
        if candidato:
            return candidato
    return shutil.which("dibu")


def _clave_json(k: Any) -> str:
    if k is False:
        return "false"
    if k is True:
        return "true"
    return str(k)


def _json_seguro(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {_clave_json(k): _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    if isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor)):
        return str(valor)
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    return str(valor)


def renderizar_lote(
    bloques: Sequence[Any],
    tinta: bool = True,
) -> List[Tuple[Optional[str], Optional[str]]]:
    """Renderiza una secuencia de bloques en un único spawn de `dibu batch`.

    Devuelve una lista paralela de `(svg, error)` del mismo largo que `bloques`.
    """
    if not bloques:
        return []
    resultados: List[Tuple[Optional[str], Optional[str]]] = [(None, None)] * len(bloques)
    lineas_req: List[str] = []
    indices_enviados: List[int] = []
    for idx, bloque in enumerate(bloques):
        if not isinstance(bloque, dict):
            resultados[idx] = (None, "el bloque tiene que ser un diccionario con 'type'")
            continue
        req = {"id": str(idx), "block": _json_seguro(bloque), "tinta": bool(tinta)}
        lineas_req.append(json.dumps(req, ensure_ascii=False, allow_nan=False))
        indices_enviados.append(idx)

    if not lineas_req:
        return resultados

    ruta = binario_dibu()
    if not ruta:
        raise ErrorDiagrama(
            "no se encontró el binario 'dibu' en $PATH (instalá dibu o definí ALUCARD_DIBU / DIBU_BIN)"
        )

    try:
        proc = subprocess.run(
            [ruta, "batch"],
            input="\n".join(lineas_req) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as e:
        raise ErrorDiagrama(f"no se pudo ejecutar 'dibu' ({ruta}): {e}") from e

    if proc.returncode != 0 and not proc.stdout.strip():
        detalle = proc.stderr.strip() or f"código de salida {proc.returncode}"
        raise ErrorDiagrama(f"dibu batch falló: {detalle}")

    por_id: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    for linea in proc.stdout.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            resp = json.loads(linea)
        except json.JSONDecodeError as e:
            raise ErrorDiagrama(f"respuesta JSON inválida de dibu batch: {e}") from e
        rid = str(resp.get("id", ""))
        por_id[rid] = (resp.get("svg"), resp.get("error"))

    for idx in indices_enviados:
        svg, err = por_id.get(str(idx), (None, "dibu batch no devolvió respuesta para el bloque"))
        resultados[idx] = (svg, err)
    return resultados


def renderizar(bloque: Dict[str, Any], tinta: bool = True) -> str:
    """El bloque como un `<svg>` independiente (con su tamaño y sus marcadores de flecha).

    `tinta` usa la paleta de ahorro de tinta de statics (negro), para imprimir; False, la de color.
    """
    svg, err = renderizar_lote([bloque], tinta=tinta)[0]
    if err is not None or svg is None:
        raise ErrorDiagrama(err or "error desconocido al renderizar diagrama")
    return svg


def leer_bloques(texto: str) -> List[Dict[str, Any]]:
    """Los bloques de un texto YAML/JSON: un bloque, una lista de bloques o un documento de statics (`blocks`)."""
    try:
        dato = yaml.safe_load(texto)
    except yaml.YAMLError as e:
        raise ErrorDiagrama(f"el bloque no es YAML/JSON válido: {e}") from e
    if isinstance(dato, dict) and "blocks" in dato:
        dato = dato["blocks"]
    bloques = dato if isinstance(dato, list) else [dato]
    if not all(isinstance(b, dict) for b in bloques):
        raise ErrorDiagrama("cada bloque tiene que ser un diccionario con 'type'")
    return bloques


def expandir_en_markdown(texto: str, tinta: bool = True) -> Tuple[str, Dict[str, str]]:
    """Reemplaza los bloques ```estructura por marcadores; devuelve el texto y el SVG de cada marcador.

    Usa un único spawn de `dibu batch` para todos los bloques del texto.
    """
    matches = list(_FENCE.finditer(texto))
    if not matches:
        return texto, {}

    fences_info: List[Tuple[re.Match[str], str, Optional[List[Dict[str, Any]]], Optional[str]]] = []
    lote_bloques: List[Dict[str, Any]] = []
    for idx, m in enumerate(matches):
        marcador = f"ESTRUCTURA{idx}X{hashlib.sha1(m.group(0).encode()).hexdigest()[:8]}"
        try:
            bloques = leer_bloques(m.group("cuerpo"))
            fences_info.append((m, marcador, bloques, None))
            lote_bloques.extend(bloques)
        except ErrorDiagrama as e:
            fences_info.append((m, marcador, None, str(e)))

    resultados_lote = renderizar_lote(lote_bloques, tinta=tinta) if lote_bloques else []

    svgs: Dict[str, str] = {}
    partes_texto: List[str] = []
    cursor_texto = 0
    cursor_lote = 0

    for m, marcador, bloques, err_parse in fences_info:
        partes_texto.append(texto[cursor_texto:m.start()])
        partes_texto.append(f"\n\n{marcador}\n\n")
        cursor_texto = m.end()

        if err_parse is not None or bloques is None:
            svgs[marcador] = f'<p class="estructura-error"><strong>Diagrama inválido:</strong> {_esc(err_parse)}</p>'
            continue

        tramo = resultados_lote[cursor_lote:cursor_lote + len(bloques)]
        cursor_lote += len(bloques)
        error_bloque = next((err for _, err in tramo if err is not None), None)
        if error_bloque is not None:
            svgs[marcador] = f'<p class="estructura-error"><strong>Diagrama inválido:</strong> {_esc(error_bloque)}</p>'
        else:
            svgs[marcador] = "".join(f'<div class="estructura">{svg}</div>' for svg, _ in tramo)

    partes_texto.append(texto[cursor_texto:])
    return "".join(partes_texto), svgs


def reponer_svgs(html_texto: str, svgs: Dict[str, str]) -> str:
    """Cambia los marcadores de `expandir_en_markdown` (solos o dentro de un <p>) por su SVG."""
    for marcador, svg in svgs.items():
        html_texto = html_texto.replace(f"<p>{marcador}</p>", svg).replace(marcador, svg)
    return html_texto


def nombre_svg(cuerpo: str) -> str:
    """Nombre del SVG de un bloque ```estructura: `estructura-<sha1(cuerpo.strip())[:12]>.svg`."""
    return f"estructura-{hashlib.sha1(cuerpo.strip().encode('utf-8')).hexdigest()[:12]}.svg"


def cuerpos_en_markdown(texto: str) -> List[str]:
    """El cuerpo (YAML/JSON) de cada bloque ```estructura (o ```statics) de un Markdown."""
    return [m.group("cuerpo") for m in _FENCE.finditer(texto)]


def _atributo_numerico(svg: str, nombre: str) -> str:
    m = re.search(rf'{nombre}="(\d+)"', svg)
    if m is None:
        raise ErrorDiagrama(f"el SVG no tiene {nombre}")
    return m.group(1)


def _apilar_svgs(svgs: Sequence[str]) -> str:
    if len(svgs) == 1:
        return svgs[0]
    ancho, y, partes = 0, 0, []
    for svg in svgs:
        w, h = (int(_atributo_numerico(svg, nombre)) for nombre in ("width", "height"))
        partes.append(svg.replace("<svg ", f'<svg x="0" y="{y}" ', 1))
        ancho, y = max(ancho, w), y + h + 8
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{y - 8}" '
        f'viewBox="0 0 {ancho} {y - 8}">' + "".join(partes) + "</svg>"
    )


def renderizar_bloque_markdown(cuerpo: str, tinta: bool = True) -> str:
    """Todas las estructuras de un bloque ```estructura en un único `<svg>`, apiladas."""
    bloques = leer_bloques(cuerpo)
    resultados = renderizar_lote(bloques, tinta=tinta)
    svgs: List[str] = []
    for svg, err in resultados:
        if err is not None or svg is None:
            raise ErrorDiagrama(err or "error desconocido al renderizar diagrama")
        svgs.append(svg)
    return _apilar_svgs(svgs)


@dataclass
class Sincronizacion:
    escritos: List[str] = field(default_factory=list)
    borrados: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)


def sincronizar_svgs(directorio: Path, tinta: bool = True, escribir: bool = True) -> Sincronizacion:
    """Deja `directorio/diagramas/` con exactamente un SVG al día por bloque de los `.md` del directorio.

    Escribe los que faltan o cambiaron y borra los `estructura-*.svg` que ningún bloque usa. Con
    `escribir=False` sólo informa qué cambiaría (para verificar en CI).
    """
    directorio = Path(directorio)
    destino = directorio / DIR_SVGS
    res = Sincronizacion()
    vistos: set[str] = set()
    pendientes: List[Tuple[Path, str, List[Dict[str, Any]]]] = []
    lote_bloques: List[Dict[str, Any]] = []

    for md in sorted(directorio.glob("*.md")):
        for cuerpo in cuerpos_en_markdown(md.read_text(encoding="utf-8")):
            nombre = nombre_svg(cuerpo)
            if nombre in vistos:
                continue
            vistos.add(nombre)
            try:
                bloques = leer_bloques(cuerpo)
            except ErrorDiagrama as e:
                res.errores.append(f"{md}: {e}")
                continue
            pendientes.append((md, nombre, bloques))
            lote_bloques.extend(bloques)

    resultados_lote = renderizar_lote(lote_bloques, tinta=tinta) if lote_bloques else []

    esperados: Dict[str, str] = {}
    cursor = 0
    for md, nombre, bloques in pendientes:
        tramo = resultados_lote[cursor:cursor + len(bloques)]
        cursor += len(bloques)
        error_bloque = next((err for _, err in tramo if err is not None), None)
        if error_bloque is not None:
            res.errores.append(f"{md}: {error_bloque}")
        else:
            esperados[nombre] = _apilar_svgs([svg for svg, _ in tramo if svg is not None])

    for nombre, svg in sorted(esperados.items()):
        ruta = destino / nombre
        if not ruta.is_file() or ruta.read_text(encoding="utf-8") != svg:
            res.escritos.append(str(ruta))
            if escribir:
                destino.mkdir(parents=True, exist_ok=True)
                ruta.write_text(svg, encoding="utf-8")

    if destino.is_dir():
        for ruta in sorted(destino.glob("estructura-*.svg")):
            if ruta.name not in esperados:
                res.borrados.append(str(ruta))
                if escribir:
                    ruta.unlink()
        if escribir and not any(destino.iterdir()):
            destino.rmdir()
    return res
