"""Consignas prácticas de deckard y repositorios externos de preguntas.

Una consigna práctica es un ejercicio del banco de deckard (`<tema>/<id>/ejercicio.yaml` con su
`enunciado.md`, `solucion.c` y cabecera `.h`). Se cargan como preguntas de tipo
`consigna_practica` con el ejercicio en `metadata`; qué se muestra en el examen (y cuánto espacio
queda para resolver) se decide al armar cada pool, con `PresentacionConsigna`. Se lee el formato
de deckard directamente: no hace falta tener deckard instalado.
"""
from __future__ import annotations

import html
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from generador_examenes.core.markdown_utils import markdown_to_html
from generador_examenes.core.models import PresentacionConsigna, Pregunta, RepositorioExterno

logger = logging.getLogger(__name__)

ARCHIVO_EJERCICIO = "ejercicio.yaml"
EXTENSIONES_PREGUNTAS = (".gift", ".txt", ".xml")
BLOOM = {1: "Recordar", 2: "Comprender", 3: "Aplicar", 4: "Analizar", 5: "Evaluar / Crear"}


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

def _ruta(ruta: str | Path) -> Path:
    return Path(ruta).expanduser()


def _raiz_deckard(ruta: Path) -> Path:
    """El banco de un repositorio de enunciados (`<ruta>/banco`) o la carpeta misma."""
    return ruta / "banco" if (ruta / "banco").is_dir() else ruta


def cargar_consigna(dir_ejercicio: Path, fuente: str) -> Optional[Pregunta]:
    """Un ejercicio de deckard como pregunta `consigna_practica`; None si su YAML no sirve."""
    try:
        datos = yaml.safe_load((dir_ejercicio / ARCHIVO_EJERCICIO).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Consigna omitida ({dir_ejercicio}): {e}")
        return None
    if not isinstance(datos, dict) or not datos.get("id"):
        logger.warning(f"Consigna omitida ({dir_ejercicio}): {ARCHIVO_EJERCICIO} sin id")
        return None

    def leer(nombre: str) -> str:
        archivo = dir_ejercicio / nombre
        return archivo.read_text(encoding="utf-8") if archivo.is_file() else ""

    eid = str(datos["id"])
    cabecera = dir_ejercicio / f"{eid}.h"
    if not cabecera.is_file():
        otras = sorted(dir_ejercicio.glob("*.h"))
        cabecera = otras[0] if len(otras) == 1 else cabecera
    tema = str(datos.get("tema") or "general")
    bloom = int(datos.get("bloom") or 0)
    minutos = datos.get("minutos_estimados", datos.get("minutos"))
    tags = [str(t) for t in datos.get("tags") or []]

    return Pregunta(
        id=f"deckard:{eid}",
        tipo="consigna_practica",
        nombre=str(datos.get("titulo") or eid),
        categoria=f"consignas/{tema}",
        enunciado_html="",
        etiquetas=tags + [tema, f"bloom:{bloom}", f"repo:{fuente}"],
        fuente_banco=fuente,
        tamano_desarrollo=None,
        metadata={
            "ejercicio_id": eid,
            "tema": tema,
            "bloom": bloom,
            "minutos": int(minutos) if minutos is not None else None,
            "publicar": datos.get("publicar", True) is not False,
            "funciones": [f for f in datos.get("funciones") or [] if isinstance(f, dict)],
            "pistas": [str(p) for p in datos.get("pistas") or []],
            "enunciado_md": leer("enunciado.md") or str(datos.get("enunciado_md") or ""),
            "solucion_c": leer("solucion.c") or str(datos.get("solucion_c") or ""),
            "cabecera_c": cabecera.read_text(encoding="utf-8") if cabecera.is_file() else "",
            "cabecera_nombre": cabecera.name if cabecera.is_file() else "",
            "ruta": str(dir_ejercicio),
        },
    )


def cargar_consignas(ruta: str | Path, fuente: Optional[str] = None, incluir_no_publicados: bool = False) -> Dict[str, Pregunta]:
    """Las consignas de una carpeta de deckard (con o sin `banco/`), sin repetir las enlazadas."""
    raiz = _raiz_deckard(_ruta(ruta))
    if not raiz.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de consignas {raiz}")
    nombre = fuente or _ruta(ruta).resolve().name
    consignas: Dict[str, Pregunta] = {}
    vistas: set[Path] = set()
    for meta in sorted(raiz.rglob(ARCHIVO_EJERCICIO)):
        real = meta.parent.resolve()
        if real in vistas:
            continue
        vistas.add(real)
        pregunta = cargar_consigna(meta.parent, nombre)
        if pregunta is None:
            continue
        if not pregunta.metadata["publicar"] and not incluir_no_publicados:
            continue
        consignas[pregunta.id] = pregunta
    logger.info(f"Consignas cargadas de {raiz}: {len(consignas)}")
    return consignas


def detectar_tipo(ruta: Path) -> str:
    raiz = _raiz_deckard(ruta)
    return "deckard" if raiz.is_dir() and next(raiz.rglob(ARCHIVO_EJERCICIO), None) else "preguntas"


def bancos_de_carpeta(ruta: Path) -> List[Path]:
    """Los bancos GIFT/XML de una carpeta (y sus subcarpetas, salvo las ocultas)."""
    return sorted(
        p for p in ruta.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONES_PREGUNTAS
        and not any(parte.startswith(".") for parte in p.relative_to(ruta).parts)
    )


def cargar_repositorio(repo: RepositorioExterno) -> Dict[str, Pregunta]:
    """Las preguntas o consignas de un repositorio externo."""
    from generador_examenes.core.logic import cargar_bancos

    ruta = _ruta(repo.ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el repositorio externo {ruta}")
    nombre = repo.nombre or ruta.resolve().name
    tipo = detectar_tipo(ruta) if repo.tipo == "auto" else repo.tipo
    logger.info(f"Repositorio externo '{nombre}' ({tipo}): {ruta}")
    if tipo == "deckard":
        return cargar_consignas(ruta, fuente=nombre, incluir_no_publicados=repo.incluir_no_publicados)
    bancos = [ruta] if ruta.is_file() else bancos_de_carpeta(ruta)
    preguntas = cargar_bancos(bancos)
    for p in preguntas.values():
        if f"repo:{nombre}" not in p.etiquetas:
            p.etiquetas.append(f"repo:{nombre}")
    return preguntas


def cargar_fuentes_complementarias(
    input_consignas: Optional[List[str]], repositorios: List[RepositorioExterno]
) -> Dict[str, Pregunta]:
    """Consignas locales (`input_consignas`) y repositorios externos, para sumar al banco del proyecto."""
    banco: Dict[str, Pregunta] = {}
    fuentes = [cargar_consignas(c) for c in input_consignas or []]
    fuentes += [cargar_repositorio(r) for r in repositorios]
    for preguntas in fuentes:
        for pid, pregunta in preguntas.items():
            if pid in banco:
                logger.warning(f"Pregunta duplicada encontrada: {pregunta} - sobrescribiendo")
            banco[pid] = pregunta
    return banco


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

_DIRECTIVA = re.compile(r"^(?P<valla>:{3,}|`{3,})\{(?P<nombre>[\w-]+)\}[ \t]*(?P<titulo>[^\n]*)$")
_OPCION = re.compile(r"^:[\w-]+:.*$")


def myst_a_markdown(texto: str) -> str:
    """El MyST de los enunciados de deckard como Markdown común, para el papel.

    Las directivas de bloque (`:::{tip} Título`, `::::{tab-set}`, `:::{dropdown}`…) dejan su
    título en negrita y su contenido; `{code-block} c` pasa a un bloque ```c; se quitan las
    opciones (`:class:`, `:linenos:`…) y las vallas de cierre.
    """
    salida: List[str] = []
    directivas: List[str] = []    # vallas de las directivas abiertas
    codigo: Optional[str] = None  # valla del bloque de código abierto
    tras_directiva = False        # las opciones `:clave: valor` van justo después de abrir
    for linea in texto.splitlines():
        limpia = linea.strip()
        if tras_directiva and _OPCION.match(limpia):
            continue
        tras_directiva = False
        if codigo is not None:
            salida.append(linea)
            if limpia == codigo:
                codigo = None
            continue
        m = _DIRECTIVA.match(limpia)
        if m:
            valla, nombre, titulo = m.group("valla"), m.group("nombre"), m.group("titulo").strip()
            tras_directiva = True
            if nombre in ("code-block", "code", "code-cell"):
                salida.append(f"{valla}{titulo}" if valla.startswith("`") else f"```{titulo}")
                codigo = valla if valla.startswith("`") else "```"
                continue
            directivas.append(valla)
            if titulo:
                salida += [f"**{titulo}**", ""]
            continue
        if directivas and limpia == directivas[-1]:
            directivas.pop()
            salida.append("")
            continue
        if limpia.startswith("```"):
            codigo = re.match(r"`+", limpia).group(0)  # type: ignore[union-attr]
        salida.append(linea)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(salida)).strip()


def quitar_secciones(texto: str, titulos: List[str]) -> str:
    """Saca del Markdown las secciones cuyo título contiene alguno de `titulos` (sin distinguir mayúsculas)."""
    if not titulos:
        return texto
    buscados = [t.lower() for t in titulos]
    salida: List[str] = []
    saltando: Optional[int] = None
    for linea in texto.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", linea)
        if m:
            nivel = len(m.group(1))
            if saltando is not None and nivel <= saltando:
                saltando = None
            if saltando is None and any(b in m.group(2).lower() for b in buscados):
                saltando = nivel
                continue
        if saltando is None:
            salida.append(linea)
    return "\n".join(salida)


def _tabla_funciones(funciones: List[Dict[str, Any]]) -> str:
    filas = ["| Función | Retorno | Parámetros | Descripción |", "| --- | --- | --- | --- |"]
    for f in funciones:
        filas.append(
            f"| `{f.get('nombre', '')}` | `{f.get('retorno') or 'void'}` | `{f.get('parametros') or 'void'}` "
            f"| {f.get('descripcion') or ''} |"
        )
    return "\n".join(filas)


def componer_markdown(pregunta: Pregunta, presentacion: PresentacionConsigna) -> str:
    """El Markdown de la consigna con sólo lo que pide la presentación (sin el título: lo pone el examen)."""
    meta = pregunta.metadata
    partes: List[str] = []
    if presentacion.metadatos:
        datos = [f"Tema: {meta['tema']}"]
        if meta.get("bloom"):
            datos.append(f"Bloom: B{meta['bloom']} ({BLOOM.get(meta['bloom'], '')})")
        if meta.get("minutos"):
            datos.append(f"Tiempo estimado: {meta['minutos']} min")
        partes.append("*" + " · ".join(datos) + "*")
    if presentacion.enunciado and meta.get("enunciado_md"):
        partes.append(quitar_secciones(myst_a_markdown(meta["enunciado_md"]), presentacion.secciones_excluidas))
    if presentacion.funciones and meta.get("funciones"):
        partes.append("**Funciones a implementar**\n\n" + _tabla_funciones(meta["funciones"]))
    if presentacion.cabecera and meta.get("cabecera_c"):
        partes.append(f"**Cabecera `{meta['cabecera_nombre']}`**\n\n```c\n{meta['cabecera_c'].strip()}\n```")
    pistas = meta.get("pistas", [])[: presentacion.pistas]
    if pistas:
        partes.append("**Pistas**\n\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(pistas, 1)))
    return "\n\n".join(p for p in partes if p.strip())


def _html_con_titulo(pregunta: Pregunta, cuerpo_md: str, presentacion: PresentacionConsigna) -> str:
    cuerpo = markdown_to_html(cuerpo_md, saltos_de_linea=False) if cuerpo_md else ""
    if presentacion.titulo:
        return f"<p><strong>{html.escape(pregunta.nombre)}</strong></p>\n{cuerpo}"
    return cuerpo


def presentar_consigna(pregunta: Pregunta, presentacion: PresentacionConsigna) -> Pregunta:
    """Copia de la consigna con el enunciado del examen, el espacio de respuesta y la solución para la clave."""
    copia = pregunta.model_copy(deep=True)
    copia.enunciado_html = _html_con_titulo(pregunta, componer_markdown(pregunta, presentacion), presentacion)
    copia.lineas_respuesta = presentacion.lineas if presentacion.espacio_respuesta else 0
    solucion = pregunta.metadata.get("solucion_c", "").strip()
    copia.metadata["solucion_html"] = (
        markdown_to_html(f"```c\n{solucion}\n```", saltos_de_linea=False) if presentacion.solucion_en_clave and solucion else ""
    )
    copia.metadata["solucion_c_clave"] = solucion if presentacion.solucion_en_clave else ""
    return copia


def presentacion_efectiva(general: PresentacionConsigna, del_pool: Optional[PresentacionConsigna]) -> PresentacionConsigna:
    """La presentación del examen con lo que el pool cambia explícitamente."""
    if del_pool is None:
        return general
    return general.model_copy(update=del_pool.model_dump(exclude_unset=True))
