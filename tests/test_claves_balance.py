"""Completitud (QoL #7) y balance (QoL #20) de la clave de respuestas."""

import random

from generador_examenes.core.logic import auditar_claves, balancear_claves, letras_correctas
from generador_examenes.core.models import Opcion, Pregunta


def _pregunta(i, correcta=0, n=4, tipo="seleccion_multiple"):
    return Pregunta(id=f"p{i}", tipo=tipo, nombre=f"P{i}", categoria="c", enunciado_html="?",
                    opciones=[Opcion(texto_html=str(k), es_correcta=(k == correcta)) for k in range(n)])


def test_pregunta_sin_correcta():
    examen = {"secciones": [{"nombre": "S1", "preguntas": [_pregunta(1), _pregunta(2, correcta=-1)]}]}
    assert auditar_claves(examen) == ["'p2' (S1) no tiene ninguna opción correcta."]


def test_balance_rompe_las_rachas():
    examen = {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i) for i in range(12)]}]}
    assert letras_correctas(examen) == ["A"] * 12
    remezcladas = balancear_claves(examen, random.Random(1))
    letras = letras_correctas(examen)
    assert remezcladas > 0
    racha = max_racha = 1
    for a, b in zip(letras, letras[1:], strict=False):
        racha = racha + 1 if a == b else 1
        max_racha = max(max_racha, racha)
    assert max_racha <= 3
    assert len(letras) == 12 and not auditar_claves(examen)


def test_balance_es_reproducible():
    def armar():
        return {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i) for i in range(8)]}]}
    a, b = armar(), armar()
    balancear_claves(a, random.Random(7))
    balancear_claves(b, random.Random(7))
    assert letras_correctas(a) == letras_correctas(b)
