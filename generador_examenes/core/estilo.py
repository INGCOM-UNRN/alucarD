"""Tipografía, encabezado y pie, logotipo y contraste: lo que las plantillas reciben como `estilo`.

Las plantillas no deciden colores ni arman el encabezado: lo hace `contexto_estilo`, que devuelve el
marcado Typst y el HTML ya listos, y la paleta (`c`). Con `alto_contraste`, todo el texto es negro
(también el de los diagramas) y los bordes, negros.
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from typing import Any, Dict, Optional

from generador_examenes.core.models import DefinicionExamen, EstiloExamen, Franja

FUENTE = ["Liberation Sans", "DejaVu Sans", "Arial"]
FUENTE_CODIGO = ["DejaVu Sans Mono", "Liberation Mono"]
TAMANO = 10

# Colores (hex sin #) de las plantillas Typst, por su uso.
PALETA = {
    "titulo": "1b365d", "seccion": "2b6cb0", "sub": "4a5568", "tenue": "718096", "franja": "888888",
    "guia": "a0aec0", "borde": "e2e8f0", "borde_fuerte": "718096", "borde_inst": "cbd5e0",
    "fondo_inst": "f7fafc", "linea_pie": "cccccc",
}
PALETA_CONTRASTE = {**{k: "000000" for k in PALETA}, "fondo_inst": "ffffff"}

# Los grises de la paleta de impresión de los diagramas (statics) que pasan a negro.
_GRISES_DIAGRAMA = re.compile(r"#(?:334155|475569|64748b)\b", re.IGNORECASE)

_FORMATOS_LOGO = {".png": "png", ".jpg": "jpg", ".jpeg": "jpg", ".gif": "gif", ".svg": "svg"}
_MIME = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml"}


class ErrorEstilo(ValueError):
    """Un estilo que no se puede aplicar (p. ej. el logotipo no existe o no es una imagen)."""


def contrastar_diagramas(fragmento: Any) -> Any:
    """Los textos y trazos grises de los diagramas, en negro (para `alto_contraste`)."""
    if not isinstance(fragmento, str) or "<svg" not in fragmento:
        return fragmento
    return _GRISES_DIAGRAMA.sub("#000000", fragmento)


def combinar(del_curso: Dict[str, Any], de_la_definicion: Dict[str, Any],
             base_definicion: Optional[Path] = None) -> EstiloExamen:
    """El `[estilo]` de alucard.toml con lo que escribió la definición encima (clave por clave).

    El logotipo de la definición es relativo a su carpeta (el del curso ya viene resuelto); si no
    existe, es un error antes de generar nada.
    """
    propio = dict(de_la_definicion or {})
    if propio.get("logo") and base_definicion is not None:
        propio["logo"] = str(base_definicion / str(propio["logo"]))
    estilo = EstiloExamen(**{**(del_curso or {}), **propio})
    if estilo.logo and not Path(estilo.logo).is_file():
        raise ErrorEstilo(f"no se encontró el logotipo {estilo.logo}")
    leer_logo(estilo.logo)  # formato soportado
    return estilo


def preparar_examen(examen_data: Dict[str, Any], definicion: DefinicionExamen) -> Dict[str, Any]:
    """Con `alto_contraste`, una copia del examen con los diagramas de enunciados y opciones en negro."""
    if not definicion.estilo.alto_contraste:
        return examen_data

    def pregunta(p):
        opciones = [o.model_copy(update={"texto_html": contrastar_diagramas(o.texto_html)}) for o in p.opciones]
        return p.model_copy(update={"enunciado_html": contrastar_diagramas(p.enunciado_html), "opciones": opciones})

    secciones = [{**s, "preguntas": [pregunta(p) for p in s.get("preguntas", [])]}
                 for s in examen_data.get("secciones", [])]
    return {**examen_data, "secciones": secciones}


def leer_logo(ruta: Optional[str]) -> Optional[tuple[str, bytes]]:
    """(formato, contenido) del logotipo; None si no hay."""
    if not ruta:
        return None
    archivo = Path(ruta)
    formato = _FORMATOS_LOGO.get(archivo.suffix.lower())
    if formato is None:
        raise ErrorEstilo(f"logotipo {archivo}: formato no soportado (se acepta PNG, JPG, GIF o SVG)")
    try:
        return formato, archivo.read_bytes()
    except OSError as e:
        raise ErrorEstilo(f"logotipo {archivo}: {e.strerror}") from e


def _valores(definicion: DefinicionExamen, tema: int) -> Dict[str, str]:
    return {"institucion": definicion.institucion or "", "materia": definicion.materia or "",
            "examen": definicion.nombre_examen or "", "fecha": definicion.fecha or "", "tema": str(tema + 1)}


def _por_omision(definicion: DefinicionExamen, clave: bool) -> tuple[Franja, Franja]:
    """El encabezado y el pie de siempre."""
    curso = " — ".join(p for p in ("{institucion}" if definicion.institucion else "",
                                   "" if clave else ("{materia}" if definicion.materia else "")) if p)
    if clave:
        encabezado = "CLAVE DOCENTE" + (f" — {curso}" if curso else "") + " | Tema {tema}"
        pie = "SOLUCIONARIO: {examen}"
    else:
        encabezado = (f"{curso} | " if curso else "") + "Tema {tema}"
        pie = "{examen}"
    return Franja(derecha=encabezado), Franja(izquierda=pie, derecha="Página {pagina} / {paginas}")


def _typst(texto: str, valores: Dict[str, str]) -> str:
    """Una parte de la franja como marcado Typst: el texto escapado y la página con `counter`."""
    from generador_examenes.generators.typst_markup import escapar

    partes = []
    for i, trozo in enumerate(re.split(r"\{(\w+)\}", texto)):
        if i % 2 == 0:
            partes.append(escapar(trozo))
        elif trozo == "pagina":
            partes.append("#counter(page).display()")
        elif trozo == "paginas":
            partes.append("#counter(page).final().first()")
        else:
            partes.append(escapar(valores[trozo]))
    return "".join(partes)


def _html(texto: str, valores: Dict[str, str]) -> str:
    """Una parte de la franja en HTML; el número de página no existe en HTML: la parte se omite."""
    if re.search(r"\{paginas?\}", texto):
        return ""
    return html.escape(re.sub(r"\{(\w+)\}", lambda m: valores[m.group(1)], texto))


def _franja_typst(franja: Franja, valores: Dict[str, str], color: str, logo: Optional[str], posicion: str) -> str:
    celdas = [f'align({a} + horizon)[#text(size: 8pt, fill: rgb("{color}"))[{_typst(t, valores)}]]'
              for a, t in (("left", franja.izquierda), ("center", franja.centro), ("right", franja.derecha))]
    columnas = ["1fr", "auto", "1fr"]
    if logo:
        if posicion == "izquierda":
            celdas.insert(0, "align(left + horizon, logo)")
            columnas.insert(0, "auto")
        else:
            celdas.append("align(right + horizon, logo)")
            columnas.append("auto")
    return f"grid(columns: ({', '.join(columnas)}), column-gutter: 8pt, {', '.join(celdas)})"


def _franja_html(franja: Franja, valores: Dict[str, str], clase: str, logo: Optional[str], posicion: str) -> str:
    partes = [_html(t, valores) for t in (franja.izquierda, franja.centro, franja.derecha)]
    if not any(partes) and not logo:
        return ""
    celdas = "".join(f'<div class="franja-{n}">{p}</div>' for n, p in zip(("izq", "centro", "der"), partes))
    if logo:
        img = f'<img class="franja-logo" src="{logo}" alt="">'
        celdas = img + celdas if posicion == "izquierda" else celdas + img
    return f'<div class="franja {clase}">{celdas}</div>'


def _familias_typst(familias: list[str]) -> str:
    from generador_examenes.generators.typst_markup import _cadena

    return "(" + ", ".join(_cadena(f) for f in familias) + ",)"


def _familias_css(familias: list[str], generica: str) -> str:
    nombres = [f.replace("\\", "").replace("'", "\\'").replace("<", "") for f in familias]
    return ", ".join([f"'{f}'" for f in nombres] + [generica])


def contexto_estilo(definicion: DefinicionExamen, tema: int, clave: bool = False) -> Dict[str, Any]:
    """Lo que necesitan las plantillas: `estilo.*` para Typst y para HTML, y la paleta en `c`."""
    estilo: EstiloExamen = definicion.estilo
    valores = _valores(definicion, tema)
    enc_omision, pie_omision = _por_omision(definicion, clave)
    encabezado, pie = estilo.encabezado or enc_omision, estilo.pie or pie_omision
    paleta = PALETA_CONTRASTE if estilo.alto_contraste else PALETA
    fuente = estilo.fuente or FUENTE
    fuente_codigo = estilo.fuente_codigo or FUENTE_CODIGO

    logo = leer_logo(estilo.logo)
    logo_typst = logo_html = None
    if logo:
        formato, datos = logo
        if formato == "svg":
            from generador_examenes.generators.typst_markup import _cadena
            fuente_logo = f"bytes({_cadena(datos.decode('utf-8'))})"
        else:
            fuente_logo = "bytes((" + ",".join(map(str, datos)) + ",))"
        logo_typst = f'image({fuente_logo}, format: "{formato}", height: {estilo.logo_alto_mm:g}mm)'
        logo_html = f"data:{_MIME[formato]};base64,{base64.b64encode(datos).decode('ascii')}"

    # El logotipo vive en el margen superior: si es alto, el margen crece.
    margen_sup = max(20.0, estilo.logo_alto_mm + 12) if logo_typst else 20.0
    return {
        "c": paleta,
        "estilo": {
            "alto_contraste": estilo.alto_contraste,
            "tamano": f"{estilo.tamano or TAMANO:g}",
            "fuente_typst": _familias_typst(fuente),
            "fuente_codigo_typst": _familias_typst(fuente_codigo),
            # En HTML, sin configurar, quedan las de siempre (Arial y Courier New, al tamaño del navegador).
            "fuente_css": _familias_css(estilo.fuente or ["Arial"], "sans-serif"),
            "fuente_codigo_css": _familias_css(estilo.fuente_codigo or ["Courier New"], "monospace"),
            "tamano_css": f"{estilo.tamano:g}pt" if estilo.tamano else None,
            "margen_sup_mm": margen_sup,
            "logo_typst": logo_typst,
            "logo_alto_mm_css": f"{estilo.logo_alto_mm:g}mm",
            "encabezado_typst": _franja_typst(encabezado, valores, paleta["franja"],
                                              logo_typst, estilo.logo_posicion),
            "pie_typst": _franja_typst(pie, valores, paleta["franja"], None, estilo.logo_posicion),
            # En HTML las franjas salen sólo si se configuraron (o hay logotipo).
            "encabezado_html": _franja_html(encabezado, valores, "franja-superior", logo_html, estilo.logo_posicion)
            if (estilo.encabezado or logo_html) else "",
            "pie_html": _franja_html(pie, valores, "franja-inferior", None, estilo.logo_posicion) if estilo.pie else "",
        },
    }
