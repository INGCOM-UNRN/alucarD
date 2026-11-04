"""Pruebas de robustez del parser GIFT: código embebido y llaves balanceadas."""

from pathlib import Path

from generador_examenes.parsers.gift_parser import (
    GiftParser,
    _extraer_bloque_respuestas,
)


def test_helper_encuentra_ultimo_grupo_balanceado():
    antes, contenido, sobrante = _extraer_bloque_respuestas("texto {con {llaves} adentro} {=a~b}")
    assert antes.strip().endswith("adentro}")
    assert contenido == "=a~b"
    assert sobrante == ""


def test_helper_respeta_llaves_escapadas():
    antes, contenido, _ = _extraer_bloque_respuestas(r"¿Signo \{literal\}? {\=x~y}")
    assert "\\{literal\\}" in antes
    assert contenido == r"\=x~y"


def test_helper_devuelve_none_sin_bloque_final():
    assert _extraer_bloque_respuestas("solo texto con {llaves} sueltas") is None
    assert _extraer_bloque_respuestas("sin llaves") is None


def test_parsea_pregunta_con_codigo_c_y_lineas_vacias(tmp_path):
    """El código C con llaves y líneas en blanco no rompe la extracción."""
    banco = tmp_path / "codigo.gift"
    banco.write_text(
        """::Traza:: ¿Qué imprime?

```c
#include <stdio.h>

int main(void) {
    int v[] = {10, 20, 30};
    int *p = v;
    p += 1;
    printf("%d\\n", *p);
    return 0;
}
```
{
=20
~10
~30
}
""",
        encoding="utf-8",
    )

    preguntas = GiftParser().parse(banco)
    assert len(preguntas) == 1
    pregunta = next(iter(preguntas.values()))
    correctas = [o.texto_html for o in pregunta.opciones if o.es_correcta]
    assert correctas == ["20"]
    # el enunciado conserva el código íntegro (el parser lo convierte a HTML
    # con resaltado: se comparan los tags removidos)
    import re
    texto_plano = re.sub(r"<[^>]+>", "", pregunta.enunciado_html)
    assert "int main(void)" in texto_plano
    assert "p += 1;" in texto_plano


def test_regresion_banco_clasico_sin_codigo(tmp_path):
    """Las preguntas tradicionales de una línea siguen parseando igual."""
    banco = tmp_path / "clasico.gift"
    banco.write_text(
        """::P1:: ¿Capital de Francia? {
=París
~Londres
}

::P2:: El cielo es azul. {T}
""",
        encoding="utf-8",
    )

    preguntas = GiftParser().parse(banco)
    assert len(preguntas) == 2
    valores = list(preguntas.values())
    assert any(o.es_correcta and o.texto_html == "París" for o in valores[0].opciones)


def test_opciones_markdown_sin_parrafo(tmp_path):
    """Las opciones son texto en línea: el Markdown no las envuelve en <p>."""
    banco = tmp_path / "banco.gift"
    banco.write_text("::p:: [markdown]¿Cuál es un puntero constante? {\n=`int *const p`\n~`const int *p`\n}\n",
                     encoding="utf-8")
    opciones = next(iter(GiftParser().parse(banco).values())).opciones
    assert [o.texto_html for o in opciones] == ["<code>int *const p</code>", "<code>const int *p</code>"]


def test_marcas_escapadas_son_parte_de_la_opcion(tmp_path):
    r"""`\=`, `\~` y `\#` en una opción son texto, no una opción ni una retroalimentación nuevas."""
    banco = tmp_path / "escapes.gift"
    banco.write_text(
        "::corte:: [markdown]¿Cuándo se detiene el recorrido?\n"
        "{\n"
        "    =`p->sig \\=\\= HEAD`#bien\n"
        "    ~`p->sig !\\= NULL`\n"
        "    ~`x \\~ y` y `\\#define`\n"
        "    ~`FRENTE \\= 3`\n"
        "}\n",
        encoding="utf-8",
    )
    (pregunta,) = GiftParser().parse(banco).values()
    textos = [o.texto_html for o in pregunta.opciones]
    assert len(textos) == 4 and [o.es_correcta for o in pregunta.opciones] == [True, False, False, False]
    assert "p-&gt;sig == HEAD" in textos[0] and "bien" not in textos[0]
    assert "!= NULL" in textos[1]
    assert "x ~ y" in textos[2] and "#define" in textos[2]
    assert "FRENTE = 3" in textos[3]


def test_respuesta_corta_con_igual_escapado(tmp_path):
    banco = tmp_path / "corta.gift"
    banco.write_text("::c:: ¿Operador de igualdad en C? {=\\=\\= =eq}\n", encoding="utf-8")
    (pregunta,) = GiftParser().parse(banco).values()
    assert [o.texto_html for o in pregunta.opciones] == ["==", "eq"]
