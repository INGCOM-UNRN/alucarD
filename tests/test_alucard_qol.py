"""Tests para las mejoras QoL de ALUCARD."""

from pathlib import Path
from generador_examenes.core.space_calibrator import calibrar_espacio_desarrollo
from generador_examenes.core.learning_objectives import auditar_cobertura_objetivos
from generador_examenes.core.answer_matrix import generar_matriz_respuestas_temas
from generador_examenes.core.attendance import generar_acta_asistencia
from generador_examenes.core.readability import auditar_legibilidad_imprenta
from generador_examenes.core.moodle_export import exportar_a_moodle_xml


def test_space_calibrator():
    p1 = {"enunciado": "Implemente la funcion insertar_nodo", "tipo": "desarrollo"}
    p2 = {"enunciado": "Explique brevemente que es un TDA", "tipo": "desarrollo"}
    
    calib1 = calibrar_espacio_desarrollo(p1)
    calib2 = calibrar_espacio_desarrollo(p2)
    assert calib1["lineas_sugeridas"] >= 14
    assert calib2["lineas_sugeridas"] >= 6


def test_learning_objectives():
    preguntas = [
        {"enunciado": "Utilice malloc y punteros para crear una estructura."},
        {"enunciado": "Escriba un bucle for que recorra la lista."},
    ]
    res = auditar_cobertura_objetivos(preguntas)
    assert res["objetivos_cubiertos"] >= 2
    assert res["porcentaje_cobertura"] > 0


def test_answer_matrix():
    temas = [
        {"preguntas": [{"respuesta_correcta": "A"}, {"respuesta_correcta": "C"}]},
        {"preguntas": [{"respuesta_correcta": "B"}, {"respuesta_correcta": "A"}]},
    ]
    matriz = generar_matriz_respuestas_temas(temas)
    assert "Tema 1" in matriz
    assert "Tema 2" in matriz
    assert "`A`" in matriz


def test_attendance_sheet(tmp_path: Path):
    alumnos = [
        {"padron": "1001", "nombre": "Perez, Juan", "tema": "Tema A"},
        {"padron": "1002", "nombre": "Gomez, Maria", "tema": "Tema B"},
    ]
    out = tmp_path / "asistencia.md"
    res = generar_acta_asistencia("Parcial 1", alumnos, out)
    assert out.is_file()
    assert "Perez, Juan" in res


def test_readability_audit():
    ok_cfg = {"font_size": 10.0, "margin_mm": 15.0}
    bad_cfg = {"font_size": 7.0, "margin_mm": 5.0}

    assert auditar_legibilidad_imprenta(ok_cfg)["apto_imprenta"] is True
    assert auditar_legibilidad_imprenta(bad_cfg)["apto_imprenta"] is False


def test_moodle_export(tmp_path: Path):
    examen = {
        "nombre": "Final Cátedra",
        "secciones": [
            {
                "preguntas": [
                    {"titulo": "P1", "enunciado": "Explique stack", "puntaje": 2.0}
                ]
            }
        ]
    }
    out_xml = tmp_path / "cuestionario.xml"
    res = exportar_a_moodle_xml(examen, out_xml)
    assert res.is_file()
    txt = res.read_text(encoding="utf-8")
    assert "<quiz>" in txt
    assert "Explique stack" in txt
