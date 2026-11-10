"""
Utilidades para procesamiento de markdown con syntax highlighting
"""
import re
import unicodedata
from typing import Optional
import markdown
from markdown.extensions import fenced_code, codehilite
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, ClassNotFound
from pygments.formatters import HtmlFormatter
import logging

from generador_examenes.diagramas import expandir_en_markdown, reponer_svgs
from generador_examenes.matematica import expandir_formulas, reponer_formulas
from generador_examenes.plantuml import expandir_plantuml
from generador_examenes.tablas import expandir_tablas

logger = logging.getLogger(__name__)


# NFKC los reduce a un carácter común y cambia el sentido: `O(n²)` sería `O(n2)` y `O(2ⁿ)`, `O(2n)`.
_SIN_NORMALIZAR = ("<super>", "<sub>", "<fraction>")


def normalizar_fullwidth(text: str) -> str:
    """
    Normaliza caracteres fullwidth a su equivalente ASCII tradicional.
    Los caracteres fullwidth son comunes en texto copiado de ciertas fuentes
    y pueden causar problemas en el resaltado de sintaxis.
    
    Args:
        text: Texto que puede contener caracteres fullwidth
        
    Returns:
        Texto con caracteres normalizados
    """
    if not text:
        return ""
    
    # Normalizar usando NFKC (Normalization Form KC - Compatibility Decomposition)
    # Esto convierte caracteres fullwidth a su equivalente halfwidth/ASCII. Los superíndices,
    # subíndices y fracciones quedan como están.
    intactos = {c for c in set(text) if unicodedata.decomposition(c).startswith(_SIN_NORMALIZAR)}
    if intactos:
        trozos = re.split("([" + re.escape("".join(sorted(intactos))) + "])", text)
        normalized = "".join(t if i % 2 else unicodedata.normalize('NFKC', t) for i, t in enumerate(trozos))
    else:
        normalized = unicodedata.normalize('NFKC', text)
    
    # El ↵ de voight marca el final de una línea que igual termina en un salto real: se quita. Sólo
    # se vuelve un salto cuando no lo hay (el código pegado en una sola línea). Antes cada ↵ sumaba un
    # salto más y el código salía a doble espacio.
    normalized = re.sub(r'↵\r?\n?', '\n', normalized)
    
    return normalized


_SEPARADOR_TABLA = re.compile(r"\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*")
_VALLA = re.compile(r"\s*(```|~~~)")


_RAYA_PARA_COMPLETAR = re.compile(r"(`[^`]*`)|_{3,}")


def _raya_literal(m: re.Match) -> str:
    """`________` en una celda es una raya para completar: Markdown la tomaría por negrita e itálica."""
    return m.group(1) or m.group(0).replace("_", "\\_")


def separar_tablas(text: str) -> str:
    """Aparta las tablas `| a | b |` del texto que las rodea con renglones en blanco.

    Markdown sólo reconoce una tabla como bloque propio, y en un GIFT un renglón en blanco corta la
    pregunta para Moodle: las tablas sin bloque ```tabla pueden ir pegadas al texto. El código no se toca.
    """
    lineas = text.split("\n")
    salida: list[str] = []
    valla = None
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        marca = _VALLA.match(linea)
        if marca and valla in (None, marca.group(1)):
            valla = None if valla else marca.group(1)
        elif (not valla and "|" in linea and i + 1 < len(lineas) and "|" in lineas[i + 1]
              and _SEPARADOR_TABLA.fullmatch(lineas[i + 1])):
            if salida and salida[-1].strip():
                salida.append("")
            while i < len(lineas) and "|" in lineas[i]:
                salida.append(_RAYA_PARA_COMPLETAR.sub(_raya_literal, lineas[i]))
                i += 1
            if i < len(lineas) and lineas[i].strip():
                salida.append("")
            continue
        salida.append(linea)
        i += 1
    return "\n".join(salida)


def _expandir_bloques(text: str) -> tuple[str, dict[str, str]]:
    """Cambia los bloques que no son código por marcadores; devuelve el texto y el HTML de cada uno."""
    text, bloques = expandir_en_markdown(text)
    text, diagramas = expandir_plantuml(text)
    text, tablas = expandir_tablas(text, markdown_to_html)
    return text, bloques | diagramas | tablas


def markdown_to_html(text: str, saltos_de_linea: bool = True) -> str:
    """
    Convierte texto markdown a HTML con syntax highlighting para bloques de código.
    
    Args:
        text: Texto en formato markdown
        saltos_de_linea: cada salto de línea es un <br> (nl2br); False para Markdown
            envuelto a mano, como los enunciados de deckard
        
    Returns:
        HTML generado con syntax highlighting aplicado
    """
    if not text:
        return ""
    
    # Normalizar caracteres fullwidth antes de procesar
    text = normalizar_fullwidth(text)
    # Los bloques ```estructura y ```plantuml pasan a diagramas SVG y los ```tabla, a tablas
    text, diagramas = _expandir_bloques(text)
    # Las fórmulas $...$ pasan a MathML después de Markdown, que si no se comería sus `_` y `*`
    text, formulas = expandir_formulas(text)
    text = separar_tablas(text)

    # Configurar extensiones de markdown con syntax highlighting
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'codehilite',
            'tables',
        ] + (['nl2br'] if saltos_de_linea else []),
        extension_configs={
            'codehilite': {
                'guess_lang': True,
                'css_class': 'highlight',
                'noclasses': True,  # Usar estilos inline
                'pygments_style': 'colorful'
            }
        }
    )
    
    # Convertir markdown a HTML
    html = md.convert(text)
    
    return reponer_formulas(reponer_svgs(html, diagramas), formulas)


def process_code_blocks_manual(text: str) -> str:
    """
    Procesa bloques de código manualmente con triple backticks
    para mayor control sobre el syntax highlighting.
    
    Args:
        text: Texto que puede contener bloques de código con ```
        
    Returns:
        Texto con bloques de código convertidos a HTML
    """
    # Normalizar caracteres fullwidth antes de procesar
    text = normalizar_fullwidth(text)
    text, diagramas = _expandir_bloques(text)

    # Pattern para bloques de código con lenguaje especificado: ```language\ncode\n```
    pattern_with_lang = r'```(\w+)\n(.*?)```'
    
    def replace_code_block(match):
        language = match.group(1)
        code = match.group(2)
        
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
            except:
                # Si no se puede determinar el lexer, usar texto plano
                from pygments.lexers import TextLexer
                lexer = TextLexer()
        
        formatter = HtmlFormatter(
            noclasses=True,
            style='colorful',
            cssclass='highlight'
        )
        
        highlighted = highlight(code, lexer, formatter)
        return highlighted
    
    # Reemplazar bloques con lenguaje
    text = re.sub(pattern_with_lang, replace_code_block, text, flags=re.DOTALL)
    
    # Pattern para bloques sin lenguaje: ```\ncode\n```
    pattern_no_lang = r'```\n(.*?)```'
    
    def replace_code_block_no_lang(match):
        code = match.group(1)
        
        try:
            lexer = guess_lexer(code)
        except:
            from pygments.lexers import TextLexer
            lexer = TextLexer()
        
        formatter = HtmlFormatter(
            noclasses=True,
            style='colorful',
            cssclass='highlight'
        )
        
        highlighted = highlight(code, lexer, formatter)
        return highlighted
    
    text = re.sub(pattern_no_lang, replace_code_block_no_lang, text, flags=re.DOTALL)
    
    return reponer_svgs(text, diagramas)


def detect_and_convert_format(text: str, format_hint: Optional[str] = None) -> str:
    """
    Detecta el formato del texto y lo convierte a HTML si es necesario.
    
    Args:
        text: Texto a procesar
        format_hint: Pista sobre el formato ('markdown', 'html', 'plain', etc.)
        
    Returns:
        HTML procesado
    """
    if not text:
        return ""
    
    # Si el formato es markdown, convertir
    if format_hint == 'markdown':
        return markdown_to_html(text)
    
    # Si ya es HTML o no se especifica, devolver tal cual
    # pero procesar las fórmulas y los bloques de código si los hay
    text = normalizar_fullwidth(text)
    text, formulas = expandir_formulas(text, delimitadores_latex=True)
    if '```' in text:
        text = process_code_blocks_manual(text)

    return reponer_formulas(text, formulas)
