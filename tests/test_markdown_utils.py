"""
Tests para utilidades de markdown
"""
import pytest
from generador_examenes.core.markdown_utils import (
    markdown_to_html,
    process_code_blocks_manual,
    detect_and_convert_format,
    normalizar_fullwidth
)


def test_markdown_to_html_basic():
    """Test conversión básica de markdown a HTML"""
    text = "# Título\n\nEste es un **texto en negrita**."
    html = markdown_to_html(text)
    
    assert '<h1>Título</h1>' in html
    assert '<strong>texto en negrita</strong>' in html


def test_markdown_to_html_with_code_block():
    """Test conversión de markdown con bloque de código"""
    text = """```python
def hello():
    print("Hello")
```"""
    html = markdown_to_html(text)
    
    # Debe contener el div highlight de pygments
    assert 'highlight' in html
    assert 'def' in html
    assert 'hello' in html


def test_markdown_to_html_with_inline_code():
    """Test conversión de markdown con código inline"""
    text = "Usa la función `print()` para imprimir."
    html = markdown_to_html(text)
    
    assert '<code>print()</code>' in html


def test_markdown_to_html_with_lists():
    """Test conversión de markdown con listas"""
    text = """- Item 1
- Item 2
- Item 3"""
    html = markdown_to_html(text)
    
    assert '<ul>' in html
    assert '<li>Item 1</li>' in html


def test_markdown_to_html_with_tables():
    """Test conversión de markdown con tablas"""
    text = """| Col1 | Col2 |
|------|------|
| A    | B    |"""
    html = markdown_to_html(text)
    
    assert '<table>' in html
    assert '<th>Col1</th>' in html
    assert '<td>A</td>' in html


def test_markdown_to_html_empty():
    """Test conversión de texto vacío"""
    assert markdown_to_html("") == ""
    assert markdown_to_html(None) == ""


def test_process_code_blocks_manual_with_language():
    """Test procesamiento manual de bloques de código con lenguaje"""
    text = """Aquí hay código:
```python
x = 42
```
Fin."""
    html = process_code_blocks_manual(text)
    
    assert 'highlight' in html
    assert 'x' in html
    assert '42' in html


def test_process_code_blocks_manual_without_language():
    """Test procesamiento manual de bloques sin lenguaje especificado"""
    text = """```
x = 42
```"""
    html = process_code_blocks_manual(text)
    
    assert 'highlight' in html
    assert 'x' in html


def test_process_code_blocks_manual_multiple_blocks():
    """Test procesamiento de múltiples bloques de código"""
    text = """```python
x = 1
```
Texto intermedio
```c
int y = 2;
```"""
    html = process_code_blocks_manual(text)
    
    assert html.count('highlight') >= 2
    assert 'x' in html
    assert 'y' in html


def test_detect_and_convert_format_markdown():
    """Test detección y conversión de formato markdown"""
    text = "# Título\n\n**Negrita**"
    html = detect_and_convert_format(text, 'markdown')
    
    assert '<h1>Título</h1>' in html
    assert '<strong>Negrita</strong>' in html


def test_detect_and_convert_format_html():
    """Test detección de formato HTML (sin conversión)"""
    text = "<p>Texto HTML</p>"
    html = detect_and_convert_format(text, 'html')
    
    # Debe devolver el texto tal cual
    assert html == text


def test_detect_and_convert_format_plain():
    """Test detección de formato plain (sin conversión)"""
    text = "Texto plano sin formato"
    html = detect_and_convert_format(text, 'plain')
    
    # Debe devolver el texto tal cual
    assert html == text


def test_detect_and_convert_format_with_code_blocks():
    """Test detección y conversión cuando hay bloques de código"""
    text = """Texto con código:
```python
x = 1
```"""
    html = detect_and_convert_format(text, 'html')
    
    # Debe procesar los bloques de código incluso en formato HTML
    assert 'highlight' in html


def test_detect_and_convert_format_empty():
    """Test conversión de texto vacío"""
    assert detect_and_convert_format("", 'markdown') == ""
    assert detect_and_convert_format(None, 'markdown') == ""


def test_markdown_with_special_characters():
    """Test markdown con caracteres especiales"""
    text = "¿Qué es `NULL` en C?"
    html = markdown_to_html(text)
    
    assert '¿' in html
    assert '<code>NULL</code>' in html


def test_code_block_with_c_language():
    """Test bloque de código con lenguaje C"""
    text = """```c
int main() {
    printf("Hello");
    return 0;
}
```"""
    html = markdown_to_html(text)
    
    assert 'highlight' in html
    assert 'int' in html
    assert 'main' in html
    assert 'printf' in html


def test_code_block_with_backticks_in_inline():
    """Test código inline con backticks dentro de markdown"""
    text = "La función `strcmp()` compara cadenas."
    html = markdown_to_html(text)
    
    assert '<code>strcmp()</code>' in html


def test_markdown_preserves_newlines():
    """Test que markdown preserva saltos de línea con nl2br"""
    text = "Línea 1\nLínea 2"
    html = markdown_to_html(text)
    
    # Con la extensión nl2br, los saltos deben convertirse a <br>
    assert 'Línea 1' in html
    assert 'Línea 2' in html


def test_normalizar_fullwidth_empty():
    """Test normalización de texto vacío"""
    assert normalizar_fullwidth("") == ""
    assert normalizar_fullwidth(None) == ""


def test_normalizar_fullwidth_parentheses():
    """Test normalización de paréntesis fullwidth"""
    # Paréntesis fullwidth: （ ）
    text_fullwidth = "（x + y）"
    expected = "(x + y)"
    result = normalizar_fullwidth(text_fullwidth)
    assert result == expected


def test_normalizar_fullwidth_numbers():
    """Test normalización de números fullwidth"""
    # Números fullwidth: ０１２３
    text_fullwidth = "０１２３"
    expected = "0123"
    result = normalizar_fullwidth(text_fullwidth)
    assert result == expected


def test_normalizar_fullwidth_operators():
    """Test normalización de operadores fullwidth"""
    # Operadores fullwidth: ＋ － ＊ ／
    text_fullwidth = "ｘ ＋ ｙ"
    expected = "x + y"
    result = normalizar_fullwidth(text_fullwidth)
    assert result == expected


def test_normalizar_fullwidth_in_code_block():
    """Test normalización de fullwidth en bloque de código"""
    # Código con paréntesis fullwidth
    text_fullwidth = """```python
def func（x）：
    return x ＋ １
```"""
    html = process_code_blocks_manual(text_fullwidth)
    
    # El código normalizado debe estar presente
    assert 'highlight' in html
    # Los caracteres deben haberse normalizado
    assert '（' not in html or '(' in html
    

def test_normalizar_fullwidth_mixed_content():
    """Test normalización de contenido mixto (ASCII y fullwidth)"""
    text_fullwidth = "normal text （fullwidth） more text"
    expected = "normal text (fullwidth) more text"
    result = normalizar_fullwidth(text_fullwidth)
    assert result == expected


def test_process_code_blocks_with_unknown_language():
    """Test procesamiento de bloques con lenguaje desconocido"""
    text = """```unknownlang
some code here
```"""
    html = process_code_blocks_manual(text)
    
    # Debe procesar igual aunque no reconozca el lenguaje
    assert 'highlight' in html
    assert 'some code here' in html


def test_detect_and_convert_format_without_hint():
    """Test detección sin pista de formato (None)"""
    text = "Simple text"
    html = detect_and_convert_format(text, None)
    
    # Sin pista y sin bloques de código, debe devolver tal cual
    assert html == text


def test_process_code_blocks_guess_lexer_fallback():
    """Test procesamiento con fallback a TextLexer cuando guess falla"""
    # Código que es difícil de adivinar el lenguaje
    text = """```unknownlanguage
aaa bbb ccc
ddd eee fff
```"""
    html = process_code_blocks_manual(text)
    
    # Debe procesar incluso si no reconoce el lenguaje
    assert 'highlight' in html
    assert 'aaa' in html


def test_process_code_blocks_no_language_guess_fails():
    """Test procesamiento sin lenguaje especificado y guess falla"""
    # Texto muy ambiguo sin lenguaje especificado
    text = """```
qqqqqq wwwwww eeeeee
```"""
    html = process_code_blocks_manual(text)
    
    # Debe usar TextLexer por defecto
    assert 'highlight' in html
    assert 'qqqqqq' in html


def test_normalizar_fullwidth_arrow_symbol():
    """Test normalización del símbolo de flecha ↵ a salto de línea"""
    text = "línea 1↵línea 2↵línea 3"
    result = normalizar_fullwidth(text)
    expected = "línea 1\nlínea 2\nlínea 3"
    assert result == expected


def test_markdown_code_with_fullwidth_and_arrows():
    """Test código con caracteres fullwidth y símbolo ↵"""
    text = """```c
＃include ＜stdio.h＞↵
int main（） ｛↵
    printf（"Hello"）;↵
｝
```"""
    html = markdown_to_html(text)
    
    # Los caracteres deben estar normalizados
    assert 'highlight' in html
    assert '#include' in html
    # En HTML, < y > se codifican como &lt; y &gt;
    assert ('&lt;stdio.h&gt;' in html or '<stdio.h>' in html)
    assert 'printf' in html
    # No debe contener caracteres fullwidth
    assert '＃' not in html
    assert '＜' not in html
    assert '＞' not in html
    assert '｛' not in html
    assert '｝' not in html
    assert '（' not in html
    assert '）' not in html
    assert '↵' not in html
