"""Adaptador de diagramas SVG de alucarD hacia el binario externo `dibu`.

Delega el renderizado de los diagramas (estructuras de datos, control de procesos, química,
sistemas digitales, arquitectura, sistemas operativos, redes, bases de datos, señales,
probabilidad y circuitos) a `dibu batch` (protocolo JSONL por stdin/stdout: 1 solo proceso por
documento o directorio). Los tipos y los themes disponibles se le preguntan al binario.

El theme de los diagramas (`ink`, `color`, `high-contrast`, `dark` o un diccionario con
`extends`, `colors` y `typography`) se elige por llamada o, para todo un examen, con
`fijar_tema`: lo usa `alucard generar` según el `[estilo]` (`tema_diagramas`, `alto_contraste`).
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
import sys
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache
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

# Los tipos de dibu 0.1 (para documentación y como respaldo); los reales los informa el binario
# con `tipos_disponibles()`.
TIPOS: Tuple[str, ...] = (
    "adt", "array", "avl", "block_diagram", "bode", "born_haber", "bplus_tree", "cache",
    "call_stack", "call_tree", "chair", "circuit", "complex", "complexity", "convolution",
    "cost_table", "cpu_scheduling", "crystal_field", "dijkstra", "distribution", "dp_table",
    "energy_profile", "fischer", "flowchart", "fourier", "frost", "galvanic_cell", "grafcet",
    "hash_table", "heap", "heating_curve", "ieee754", "instrumentation", "karnaugh", "kinetics",
    "ladder", "latimer", "linked_list", "logic_circuit", "matrix", "molecule", "newman", "nyquist",
    "orbitals", "page_replacement", "page_table", "phase_diagram", "phasor", "pipeline", "pole_zero",
    "queue", "reaction", "root_locus", "sampling", "signal", "speciation", "spectrum", "stack",
    "struct", "subnetting", "time_response", "titration", "trace_table", "transaction_schedule",
    "tree", "truth_table", "turing", "unit_cell", "venn", "vsepr",
)

# Presets de theme de dibu.
TEMAS: Tuple[str, ...] = ("ink", "color", "high-contrast", "dark")

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
    """Ruta al binario `dibu` (`ALUCARD_DIBU` / `DIBU_BIN`, `.venv/bin/dibu` o `$PATH`)."""
    for var in ("ALUCARD_DIBU", "DIBU_BIN"):
        candidato = os.environ.get(var)
        if candidato:
            return candidato
    junto_python = Path(sys.executable).parent / ("dibu.exe" if os.name == "nt" else "dibu")
    if junto_python.is_file() and os.access(junto_python, os.X_OK):
        return str(junto_python)
    return shutil.which("dibu")


def _consultar(subcomando: str) -> Optional[Tuple[str, ...]]:
    """Las líneas que imprime `dibu <subcomando>`, o None si no hay binario o el comando falla."""
    ruta = binario_dibu()
    if not ruta:
        return None
    try:
        proc = subprocess.run([ruta, subcomando], capture_output=True, text=True, encoding="utf-8",
                              check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return tuple(l.strip() for l in proc.stdout.splitlines() if l.strip())


@lru_cache(maxsize=4)
def _tipos_de(ruta: Optional[str], huella: str) -> Tuple[str, ...]:
    return _consultar("list-types") or TIPOS


def tipos_disponibles() -> Tuple[str, ...]:
    """Los tipos que dibuja el binario `dibu` instalado (o `TIPOS` si no se puede preguntar)."""
    return _tipos_de(binario_dibu(), huella_dibu())


@lru_cache(maxsize=4)
def _temas_de(ruta: Optional[str], huella: str) -> Tuple[str, ...]:
    return _consultar("list-themes") or ("ink", "color")


def temas_disponibles() -> Tuple[str, ...]:
    """Los presets de theme del binario (un `dibu` anterior a los themes sólo tiene ink y color)."""
    return _temas_de(binario_dibu(), huella_dibu())


def huella_dibu() -> str:
    """Identifica el binario `dibu` (ruta, tamaño y fecha): si se actualiza, cambia."""
    ruta = binario_dibu()
    if not ruta:
        return "sin-dibu"
    try:
        st = Path(ruta).stat()
    except OSError:
        return f"{ruta}:?"
    return f"{ruta}:{st.st_size}:{st.st_mtime_ns}"


# ---------------------------------------------------------------------------
# Theme activo
# ---------------------------------------------------------------------------

_TEMA: ContextVar[Optional[Any]] = ContextVar("alucard_tema_diagramas", default=None)


def resolver_tema(tema: Optional[Any], base: Optional[Path] = None) -> Optional[Any]:
    """Un theme listo para dibu: un preset, un diccionario o la ruta a un archivo YAML/JSON.

    Una ruta relativa se busca primero junto a `base` (la carpeta de la definición o del curso).
    """
    if tema is None or isinstance(tema, dict):
        return tema
    texto = str(tema).strip()
    if not texto:
        return None
    for candidato in ([base / texto] if base is not None else []) + [Path(texto)]:
        if candidato.suffix.lower() in (".yaml", ".yml", ".json") and candidato.is_file():
            try:
                datos = yaml.safe_load(candidato.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as e:
                raise ErrorDiagrama(f"no se pudo leer el theme {candidato}: {e}") from e
            if not isinstance(datos, dict):
                raise ErrorDiagrama(f"el theme {candidato} tiene que ser un diccionario")
            return datos
    if texto.lower().endswith((".yaml", ".yml", ".json")):
        raise ErrorDiagrama(f"no se encontró el archivo de theme {texto}")
    return texto


def fijar_tema(tema: Optional[Any]) -> None:
    """El theme que usan los diagramas que no piden otro (None: el de `tinta`)."""
    _TEMA.set(tema)


def tema_activo() -> Optional[Any]:
    return _TEMA.get()


def huella_render() -> str:
    """Lo que, además del texto, decide cómo sale un diagrama: el binario y el theme activo.

    La usa la caché de bancos, que guarda las preguntas con sus SVG ya dibujados.
    """
    tema = tema_activo()
    return f"{huella_dibu()}|{json.dumps(_json_seguro(tema), sort_keys=True, ensure_ascii=False)}"


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
    theme: Optional[Any] = None,
) -> List[Tuple[Optional[str], Optional[str]]]:
    """Renderiza una secuencia de bloques en un único spawn de `dibu batch`.

    `theme` puede ser el nombre de un preset (`"ink"`, `"color"`, `"high-contrast"`, `"dark"`)
    o un diccionario parcial (`{"extends": ..., "colors": ..., "typography": ...}`); sin él, se usa
    el de `fijar_tema`. Un bloque con su propio `theme` o `inkSaver` manda sobre ambos.
    Devuelve una lista paralela de `(svg, error)` del mismo largo que `bloques`.
    """
    if not bloques:
        return []
    if theme is None:
        theme = tema_activo()
    resultados: List[Tuple[Optional[str], Optional[str]]] = [(None, None)] * len(bloques)
    lineas_req: List[str] = []
    indices_enviados: List[int] = []
    for idx, bloque in enumerate(bloques):
        if not isinstance(bloque, dict):
            resultados[idx] = (None, "el bloque tiene que ser un diccionario con 'type'")
            continue
        req: Dict[str, Any] = {"id": str(idx), "block": _json_seguro(bloque), "tinta": bool(tinta)}
        if theme is not None:
            req["theme"] = _json_seguro(theme)
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


def renderizar(bloque: Dict[str, Any], tinta: bool = True, theme: Optional[Any] = None) -> str:
    """El bloque como un `<svg>` independiente (con su tamaño y sus marcadores de flecha).

    `tinta` usa la paleta de ahorro de tinta de statics (negro), para imprimir; False, la de color.
    """
    svg, err = renderizar_lote([bloque], tinta=tinta, theme=theme)[0]
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


def expandir_en_markdown(
    texto: str, tinta: bool = True, theme: Optional[Any] = None
) -> Tuple[str, Dict[str, str]]:
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

    resultados_lote = renderizar_lote(lote_bloques, tinta=tinta, theme=theme) if lote_bloques else []

    svgs: Dict[str, str] = {}
    partes_texto: List[str] = []
    cursor_texto = 0
    cursor_lote = 0

    for m, marcador, bloques_fence, err_parse in fences_info:
        partes_texto.append(texto[cursor_texto:m.start()])
        partes_texto.append(f"\n\n{marcador}\n\n")
        cursor_texto = m.end()

        if err_parse is not None or bloques_fence is None:
            svgs[marcador] = f'<p class="estructura-error"><strong>Diagrama inválido:</strong> {_esc(err_parse)}</p>'
            continue

        tramo = resultados_lote[cursor_lote:cursor_lote + len(bloques_fence)]
        cursor_lote += len(bloques_fence)
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


def renderizar_bloque_markdown(cuerpo: str, tinta: bool = True, theme: Optional[Any] = None) -> str:
    """Todas las estructuras de un bloque ```estructura en un único `<svg>`, apiladas."""
    bloques = leer_bloques(cuerpo)
    resultados = renderizar_lote(bloques, tinta=tinta, theme=theme)
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


def sincronizar_svgs(
    directorio: Path, tinta: bool = True, escribir: bool = True, theme: Optional[Any] = None
) -> Sincronizacion:
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

    resultados_lote = renderizar_lote(lote_bloques, tinta=tinta, theme=theme) if lote_bloques else []

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
