"""La opción correcta se reparte entre las letras, sin rachas (Ola 14, QoL #20)."""

import random

from generador_examenes.core.logic import asignar_posiciones_correctas, letras_correctas
from generador_examenes.core.models import Opcion, Pregunta


def _pregunta(i, n=4):
    return Pregunta(id=f"p{i}", tipo="seleccion_multiple", nombre=f"P{i}", categoria="c", enunciado_html="?",
                    opciones=[Opcion(texto_html=str(k), es_correcta=(k == 0)) for k in range(n)])


def test_asignar_posiciones_reparte_la_correcta_y_no_hace_rachas():
    examen = {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i) for i in range(12)]}]}
    uso = asignar_posiciones_correctas(examen, random.Random(3))
    assert sorted(uso.values()) == [3, 3, 3, 3]
    letras = letras_correctas(examen)
    assert all(not (a == b == c == d) for a, b, c, d in zip(letras, letras[1:], letras[2:], letras[3:], strict=False))
    assert all(len(p.opciones) == 4 for p in examen["secciones"][0]["preguntas"])


def test_el_uso_global_balancea_entre_temas():
    uso: dict = {}
    for semilla in range(2):
        examen = {"secciones": [{"nombre": "S", "preguntas": [_pregunta(i) for i in range(6)]}]}
        asignar_posiciones_correctas(examen, random.Random(semilla), uso_global=uso)
    assert sorted(uso.values()) == [3, 3, 3, 3]
