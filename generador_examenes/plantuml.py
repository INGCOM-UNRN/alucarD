"""Diagramas PlantUML en un bloque ```plantuml, con su presentación.

```plantuml
// [centrado] [ancho, 60%] [alt, Clases del TAD lista]
class Lista {
  +agregar(x: int)
}
Lista --> Nodo : cabeza
```

Las opciones van en comentarios al principio del bloque, igual que en un ```tabla; `@startuml` y
`@enduml` son optativos. `ancho` y `alto` son límites: para cambiar el tamaño está `escala`. Como un ```estructura, un bloque así necesita preprocesamiento para Moodle
(`voight unify`): adentro valen `:`, llaves y renglones en blanco.

Lo dibuja el programa `plantuml`, o el que digan `ALUCARD_PLANTUML` o `PLANTUML_JAR`. Levantar Java
tarda un par de segundos, así que cada dibujo queda en una caché por contenido.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from generador_examenes.tablas import _MARCA, _MEDIDA, _OPCION, POSICIONES

FORMATOS = ("svg", "png")
MEDIDAS = ("ancho", "alto")

_FENCE = re.compile(r"^(?P<valla>`{3,}|~{3,})[ \t]*plantuml[ \t]*\n(?P<cuerpo>.*?)^(?P=valla)[ \t]*$", re.S | re.M)
_COMENTARIO = re.compile(rf"^[ \t]*(?://|{_MARCA})(?P<texto>.*)$")
_INICIO = re.compile(r"^[ \t]*@start\w+.*$", re.M)
_ATRIBUTOS_DE_MAS = re.compile(r'\s(?:preserveAspectRatio|style|contentStyleType|zoomAndPan)="[^"]*"')
_ESPERA = 120
_SVG_PLANTUML = re.compile(r'(?<=<div class="estructura plantuml" )[^>]*><svg\b[^>]*>')


class ErrorPlantuml(ValueError):
    """Un bloque ```plantuml que no se puede dibujar."""


def _opcion(texto: str, opciones: Dict[str, Any]) -> None:
    nombre, valor = (re.split(r"[,:]", texto, maxsplit=1) + [""])[:2]
    nombre, valor = nombre.strip(), valor.strip()
    if nombre in POSICIONES:
        opciones["posicion"] = nombre
    elif nombre == "color":
        opciones[nombre] = True
    elif nombre in MEDIDAS:
        if not re.fullmatch(_MEDIDA, valor):
            raise ErrorPlantuml(f"[{texto}]: se espera una medida, como 80%, 12cm o 2em")
        opciones[nombre] = valor
    elif nombre == "escala":
        if not re.fullmatch(r"\d+(?:\.\d+)?", valor) or float(valor) == 0:
            raise ErrorPlantuml(f"[{texto}]: se espera un número, como 1.5")
        opciones[nombre] = valor
    elif nombre == "letra":
        if not re.fullmatch(r"[1-9]\d*(?:pt)?", valor):
            raise ErrorPlantuml(f"[{texto}]: se espera un tamaño en puntos, como 12")
        opciones[nombre] = valor.removesuffix("pt")
    elif nombre == "tema":
        if not re.fullmatch(r"[\w-]+", valor):
            raise ErrorPlantuml(f"[{texto}]: se espera el nombre de un tema de PlantUML, como plain")
        opciones[nombre] = valor
    elif nombre == "alt":
        if not valor:
            raise ErrorPlantuml(f"[{texto}]: falta el texto alternativo")
        opciones[nombre] = valor
    else:
        raise ErrorPlantuml(f"opción desconocida [{texto}]")


def leer(cuerpo: str) -> Tuple[Dict[str, Any], str]:
    """Las opciones de un bloque y su diagrama. Más abajo, `//` es de PlantUML (itálica en una nota)."""
    opciones: Dict[str, Any] = {}
    lineas = cuerpo.split("\n")
    inicio = 0
    for linea in lineas:
        comentario = _COMENTARIO.match(linea)
        if not comentario and linea.strip():
            break
        for texto in _OPCION.findall(comentario.group("texto")) if comentario else ():
            _opcion(texto, opciones)
        inicio += 1
    fuente = "\n".join(lineas[inicio:]).replace(_MARCA, "//").rstrip()
    if not fuente:
        raise ErrorPlantuml("el bloque no tiene un diagrama")
    return opciones, fuente


def _armar(fuente: str, opciones: Dict[str, Any]) -> Tuple[str, int]:
    """El diagrama con sus directivas, y cuántos renglones hay que restar a los de un error de PlantUML."""
    directivas = [f"!theme {opciones['tema']}"] if "tema" in opciones else []
    if "tema" not in opciones and not opciones.get("color"):
        directivas.append("skinparam monochrome true")  # un examen se imprime
    if "letra" in opciones:
        directivas.append(f"skinparam defaultFontSize {opciones['letra']}")
    if "escala" in opciones:
        directivas.append(f"scale {opciones['escala']}")
    agregado = "".join(f"{d}\n" for d in directivas)
    inicio = _INICIO.search(fuente)
    if inicio is None:
        return f"@startuml\n{agregado}{fuente}\n@enduml\n", len(directivas)
    return f"{fuente[:inicio.end()]}\n{agregado}{fuente[inicio.end() + 1:]}\n", len(directivas) - 1


def comando() -> Optional[List[str]]:
    """Cómo se ejecuta PlantUML: `ALUCARD_PLANTUML`, `plantuml` en el PATH o `PLANTUML_JAR` con Java."""
    propio = os.environ.get("ALUCARD_PLANTUML")
    if propio:
        return shlex.split(propio)
    instalado = shutil.which("plantuml")
    if instalado:
        return [instalado]
    jar, java = os.environ.get("PLANTUML_JAR"), shutil.which("java")
    return [java, "-jar", jar] if jar and java else None


def _cache(clave: str, formato: str) -> Path:
    raiz = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return raiz / "alucard" / "plantuml" / f"{hashlib.sha256(clave.encode()).hexdigest()}.{formato}"


def _ejecutar(diagrama: str, formato: str, desplazamiento: int) -> bytes:
    programa = comando()
    if programa is None:
        raise ErrorPlantuml("no se encontró PlantUML: instalalo (sudo dnf install plantuml) o indicá su ruta en "
                            "ALUCARD_PLANTUML o PLANTUML_JAR")
    try:
        r = subprocess.run([*programa, f"-t{formato}", "-pipe", "-nometadata", "-charset", "UTF-8"],
                           input=diagrama.encode(), capture_output=True, timeout=_ESPERA)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ErrorPlantuml(f"PlantUML no pudo ejecutarse: {e}") from e
    if r.returncode == 0 and r.stdout:
        return r.stdout
    detalle = r.stderr.decode(errors="replace").strip().splitlines()
    if len(detalle) >= 3 and detalle[0] == "ERROR" and detalle[1].isdigit():
        raise ErrorPlantuml(f"renglón {int(detalle[1]) - desplazamiento}: {detalle[2]}")
    raise ErrorPlantuml(" ".join(detalle[:3]) or f"PlantUML terminó con el código {r.returncode}")


def _svg_limpio(svg: str) -> str:
    """Sólo el `<svg>`, con su medida en números: `preserveAspectRatio="none"` lo deformaría al cambiarla."""
    svg = svg[svg.index("<svg"):]
    abre = svg[:svg.index(">") + 1]
    nuevo = re.sub(r'\b(width|height)="([\d.]+)px"', r'\1="\2"', _ATRIBUTOS_DE_MAS.sub("", abre))
    return nuevo + svg[len(abre):]


def a_imagen(cuerpo: str, formato: str = "svg") -> bytes:
    """El dibujo de un bloque, con sus opciones aplicadas."""
    opciones, fuente = leer(cuerpo)
    diagrama, desplazamiento = _armar(fuente, opciones)
    archivo = _cache(diagrama, formato)
    try:
        return archivo.read_bytes()
    except OSError:
        pass
    datos = _ejecutar(diagrama, formato, desplazamiento)
    if formato == "svg":
        datos = _svg_limpio(datos.decode("utf-8")).encode("utf-8")
    try:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(datos)
    except OSError:
        pass  # sin caché también se dibuja
    return datos


def estilo(opciones: Dict[str, Any]) -> str:
    """Las medidas de un bloque como CSS, para una imagen o un `<svg>`: son límites, así que un diagrama
    chico no crece. Para agrandarlo está `[escala]`."""
    medidas = [f"max-width:{opciones.get('ancho', '100%')}", "height:auto"]
    return ";".join(medidas + ([f"max-height:{opciones['alto']}"] if "alto" in opciones else []))


def a_html(cuerpo: str) -> str:
    """El `<svg>` de un bloque; lleva sus opciones en `data-opciones` para el PDF."""
    opciones, _ = leer(cuerpo)
    svg = a_imagen(cuerpo).decode("utf-8")
    datos = html.escape(json.dumps({k: opciones[k] for k in ("posicion", "escala", *MEDIDAS) if k in opciones}), quote=True)
    alt = html.escape(opciones.get("alt", "diagrama"), quote=True)
    svg = svg.replace("<svg", f'<svg role="img" aria-label="{alt}" style="{estilo(opciones)}" '
                              f'data-opciones="{datos}"', 1)
    alineacion = {"izquierda": "left", "derecha": "right"}.get(opciones.get("posicion", ""), "center")
    return f'<div class="estructura plantuml" style="text-align:{alineacion}">{svg}</div>'


def aplicar_escala(html_texto: str, factor: float) -> str:
    """`escala_plantuml`: cambia el tamaño de los diagramas que no traen su `[escala]`."""
    def escalar(m: re.Match) -> str:
        if '&quot;escala&quot;' in m.group(0):
            return m.group(0)
        return re.sub(r'\b(width|height)="([\d.]+)"', lambda d: f'{d.group(1)}="{float(d.group(2)) * factor:g}"', m.group(0))

    return _SVG_PLANTUML.sub(escalar, html_texto)


def expandir_plantuml(texto: str) -> Tuple[str, Dict[str, str]]:
    """Reemplaza los bloques por marcadores; devuelve el texto y el HTML de cada marcador."""
    diagramas: Dict[str, str] = {}

    def reemplazar(m: re.Match) -> str:
        marcador = f"PLANTUML{len(diagramas)}X{hashlib.sha1(m.group(0).encode()).hexdigest()[:8]}"
        try:
            diagramas[marcador] = a_html(m.group("cuerpo"))
        except ErrorPlantuml as e:
            diagramas[marcador] = (f'<p class="estructura-error"><strong>Diagrama inválido:</strong> '
                                   f'{html.escape(str(e))}</p>')
        return f"\n\n{marcador}\n\n"

    return _FENCE.sub(reemplazar, texto), diagramas


def tramos(contenido: str) -> List[Tuple[int, int]]:
    """Dónde hay bloques ```plantuml, que Moodle no importa sin preprocesar."""
    return [m.span() for m in _FENCE.finditer(contenido)]


def errores_en_texto(contenido: str) -> List[Tuple[int, str]]:
    """(posición, motivo) de cada bloque inválido, para `lint-gift`. Sin PlantUML sólo mira las opciones."""
    errores = []
    for m in _FENCE.finditer(contenido):
        try:
            leer(m.group("cuerpo"))
            if comando():
                a_imagen(m.group("cuerpo"))
        except ErrorPlantuml as e:
            errores.append((m.start(), str(e)))
    return errores
