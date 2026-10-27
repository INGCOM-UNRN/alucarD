"""Las plantillas PDF reciben el HTML de las preguntas convertido a marcado Typst (Ola 14)."""

from generador_examenes.generators.typst_markup import html_a_typst, largo_visible


def test_html_a_typst():
    texto = html_a_typst('<p>¿Qué hace <code>x *= 2</code>? Ver http://a.b/c #1</p>'
                         '<pre><code class="language-c">int *p = &amp;x; // ok\n</code></pre><p><strong>Nota</strong></p>')
    assert '#raw("x *= 2")' in texto
    assert "http:\\/\\/a.b\\/c \\#1" in texto
    assert '#raw(block: true, lang: "c", "int *p = &x; // ok")' in texto
    assert "#strong[Nota]" in texto and "<p>" not in texto
    assert largo_visible("<p>12</p>") == 2 and largo_visible("<pre>x</pre>") == 1000
