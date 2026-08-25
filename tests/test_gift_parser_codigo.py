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
