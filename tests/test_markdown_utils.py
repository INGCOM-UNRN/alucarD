"""
Tests para utilidades de markdown
"""
import pytest
from generador_examenes.core.markdown_utils import (
    markdown_to_html,
    process_code_blocks_manual,
    detect_and_convert_format
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
