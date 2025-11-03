"""
Utilidades para procesamiento de markdown con syntax highlighting
"""
import re
import unicodedata
import markdown
from markdown.extensions import fenced_code, codehilite
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, ClassNotFound
from pygments.formatters import HtmlFormatter
import logging

logger = logging.getLogger(__name__)


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
    # Esto convierte caracteres fullwidth a su equivalente halfwidth/ASCII
    normalized = unicodedata.normalize('NFKC', text)
    
    return normalized


def markdown_to_html(text: str) -> str:
    """
    Convierte texto markdown a HTML con syntax highlighting para bloques de código.
    
    Args:
        text: Texto en formato markdown
        
    Returns:
        HTML generado con syntax highlighting aplicado
    """
    if not text:
        return ""
    
    # Configurar extensiones de markdown con syntax highlighting
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'nl2br'
        ],
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
    
    return html


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
    
    return text


def detect_and_convert_format(text: str, format_hint: str = None) -> str:
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
    # pero procesar bloques de código si los hay
    if '```' in text:
        return process_code_blocks_manual(text)
    
    return text
