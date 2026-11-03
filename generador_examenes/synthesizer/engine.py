"""Motor de síntesis: genera con las plantillas, ajusta las opciones y exporta el banco."""

from __future__ import annotations

import random
import re
import xml.sax.saxutils as saxutils
from dataclasses import replace

from .plantillas import PLANTILLAS, SnippetGenerado
from .sandbox import GCC

OPCIONES_MIN, OPCIONES_MAX = 2, 8


def plantillas_disponibles() -> dict[str, str]:
    """Catálogo nombre -> descripción."""
    return {nombre: desc for nombre, (desc, _) in PLANTILLAS.items()}


def catalogo() -> list[tuple[str, str, str]]:
    """(nombre, descripción, cómo se verifica la respuesta) de cada plantilla, en orden alfabético."""
    from .plantillas import VERIFICACION

    return [(nombre, desc, VERIFICACION.get(nombre, "")) for nombre, (desc, _) in sorted(PLANTILLAS.items())]


def _variantes_numericas(correcta: str, rng: random.Random) -> list[str]:
    """Respuestas cercanas a una salida numérica (`7`, `0 1 2`…), para completar distractores."""
    numeros = correcta.split()
    if not numeros or not all(re.fullmatch(r"-?\d+", x) for x in numeros):
        return []
    candidatas = []
    for delta in (1, -1, 2, -2, 3, -3):
        for i in reversed(range(len(numeros))):
            otros = list(numeros)
            otros[i] = str(int(otros[i]) + delta)
            candidatas.append(" ".join(otros))
    if len(numeros) == 1:
        candidatas += [str(int(numeros[0]) * 2), str(-int(numeros[0]))]
    rng.shuffle(candidatas)
    return candidatas


def ajustar_opciones(snippet: SnippetGenerado, opciones: int, rng: random.Random) -> SnippetGenerado:
    """El snippet con exactamente `opciones` opciones (correcta incluida).

    Se queda con los primeros distractores de la plantilla (los más verosímiles); si no alcanzan y la
    respuesta es numérica, completa con valores cercanos. Si aun así faltan, ValueError.
    """
    vistos = {snippet.salida_correcta}
    elegidos: list[str] = []
    for d in [*snippet.distractores, *_variantes_numericas(snippet.salida_correcta, rng)]:
        if len(elegidos) == opciones - 1:
            break
        if d not in vistos and d.strip():
            vistos.add(d)
            elegidos.append(d)
    if len(elegidos) < opciones - 1:
        raise ValueError(f"la plantilla '{snippet.plantilla}' no produce {opciones} opciones distintas "
                         f"(como máximo {len(elegidos) + 1})")
    return replace(snippet, distractores=elegidos)


def sintetizar(planta: str, cantidad: int = 5, semilla: int | None = None,
               opciones: int = 4) -> list[SnippetGenerado]:
    """Genera `cantidad` snippets verificados con la plantilla indicada, cada uno con `opciones` opciones."""
    if GCC is None:
        raise RuntimeError("gcc no está disponible: daedalus lo necesita para verificar las respuestas")
    if planta not in PLANTILLAS:
        raise KeyError(f"Plantilla desconocida: '{planta}'. Disponibles: {', '.join(sorted(PLANTILLAS))}")
    if not OPCIONES_MIN <= opciones <= OPCIONES_MAX:
        raise ValueError(f"la cantidad de opciones debe estar entre {OPCIONES_MIN} y {OPCIONES_MAX}")

    generador = PLANTILLAS[planta][1]
    rng = random.Random(semilla)
    resultados: list[SnippetGenerado] = []
    intentos = 0
    while len(resultados) < cantidad and intentos < cantidad * 10:
        intentos += 1
        snippet = generador(rng)
        if any(s.codigo == snippet.codigo for s in resultados):
            continue  # variante repetida: no aporta como ítem de examen
        resultados.append(ajustar_opciones(snippet, opciones, rng))
    return resultados


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------

def _bloque_codigo(codigo: str) -> str:
    # Sin líneas vacías internas: los parsers GIFT cortan bloques por líneas
    # en blanco y el código rompería la pregunta.
    limpio = "\n".join(l for l in codigo.rstrip("\n").splitlines() if l.strip())
    return "```c\n" + limpio + "\n```"


def _titulos_unicos(snippets: list[SnippetGenerado]) -> list[str]:
    """Los títulos, numerados cuando se repiten (en GIFT el título identifica la pregunta)."""
    vistos: dict[str, int] = {}
    titulos = []
    for s in snippets:
        vistos[s.titulo] = vistos.get(s.titulo, 0) + 1
        # «n2», no «#2»: en GIFT el # abre la retroalimentación y colisiona en el título.
        titulos.append(s.titulo if vistos[s.titulo] == 1 else f"{s.titulo} n{vistos[s.titulo]}")
    return titulos


def exportar_gift(snippets: list[SnippetGenerado]) -> str:
    """Serializa los snippets como banco GIFT (selección múltiple) en formato `[markdown]`.

    Cada plantilla va en la categoría `sintetizados/<plantilla>`, para elegirla desde un pool.
    """
    bloques = []
    categoria = None
    for s, titulo in zip(snippets, _titulos_unicos(snippets), strict=True):
        if s.plantilla != categoria:
            categoria = s.plantilla
            bloques.append(f"$CATEGORY: sintetizados/{categoria}")
        cuerpo = [f"={_texto_gift(op)}" if op == s.salida_correcta else f"~{_texto_gift(op)}"
                  for op in s.opciones]
        bloque = (
            "// daedalus: sintetizado y verificado con gcc\n"
            f"::{_titulo_gift(titulo)}:: [markdown]{_texto_gift(s.enunciado)}\n"
            f"{_bloque_codigo(s.codigo)}\n"
            "{\n" + "\n".join(cuerpo) + "\n}"
        )
        bloques.append(bloque)
    return "\n\n".join(bloques) + "\n"


def exportar_xml(snippets: list[SnippetGenerado]) -> str:
    """Serializa los snippets como banco Moodle XML (multichoice)."""
    preguntas = []
    for s, titulo in zip(snippets, _titulos_unicos(snippets), strict=True):
        opciones_xml = []
        for op in s.opciones:
            fraccion = "100" if op == s.salida_correcta else "0"
            opciones_xml.append(
                f'  <answer fraction="{fraccion}" format="html">\n'
                f'    <text><![CDATA[{saxutils.escape(op)}]]></text>\n'
                f'  </answer>'
            )
        preguntas.append(
            '<question type="multichoice">\n'
            f'  <name><text><![CDATA[{saxutils.escape(titulo)}]]></text></name>\n'
            '  <questiontext format="html">\n'
            f'    <text><![CDATA[<p>{saxutils.escape(s.enunciado)}</p><pre>{saxutils.escape(s.codigo)}</pre>]]></text>\n'
            '  </questiontext>\n'
            f'{chr(10).join(opciones_xml)}\n'
            '</question>'
        )
    cuerpo = "\n".join(preguntas)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n{cuerpo}\n</quiz>\n'


# Los dos puntos van en ancho completo: en el título cortarían el `::` que lo delimita, y en el
# resto del texto GIFT les da significado (Moodle y otros lectores los toman como separadores).
# Al mostrar la pregunta, alucard los normaliza (NFKC) y se ven como `:`.
DOS_PUNTOS = "\uff1a"


def _sin_dos_puntos(texto: str) -> str:
    return texto.replace(":", DOS_PUNTOS)


def _titulo_gift(titulo: str) -> str:
    """El título sin los caracteres que colisionan en GIFT: `:` en ancho completo y `#` como `n`
    delante de un número («#3» → «n3», referencia a número) o en ancho completo en otro lugar."""
    import re

    titulo = re.sub(r"#(?=\d)", "n", titulo)
    return _sin_dos_puntos(titulo).replace("#", "\uff03")


def _texto_gift(texto: str) -> str:
    """Texto de enunciado u opción: dos puntos en ancho completo y caracteres especiales escapados."""
    return _escape_gift(_sin_dos_puntos(texto))


def _escape_gift(texto: str) -> str:
    out = texto.replace('\\', '\\\\')
    for ch in ('=', '#', '{', '}', '~'):
        out = out.replace(ch, '\\' + ch)
    return out

