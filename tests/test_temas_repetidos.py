"""Dos temas con las mismas preguntas quedan avisados: en el resumen de generar y validar y en el informe."""

import json
import sys

import pytest

from generador_examenes.__main__ import main
from generador_examenes.core.logic import temas_con_mismas_preguntas
from generador_examenes.core.models import (
    ConfiguracionExamen,
    DefinicionExamen,
    Opcion,
    PoolConfig,
    Pregunta,
    SeccionExamen,
)


def _p(id_, opciones=("sí", "no")):
    return Pregunta(id=id_, tipo="seleccion_multiple", nombre=id_, categoria="a", enunciado_html="x",
                    opciones=[Opcion(texto_html=t, es_correcta=i == 0) for i, t in enumerate(opciones)])


def _tema(*preguntas):
    return {"secciones": [{"nombre": "S", "preguntas": list(preguntas)}]}


def _definicion(sortear=False):
    return DefinicionExamen(nombre_examen="P", institucion="I", materia="M", configuracion_examen=ConfiguracionExamen(sortear_por_tema=sortear),
                            secciones_examen=[SeccionExamen(nombre="S", pools=[PoolConfig()])])


def test_temas_distintos_no_avisan():
    assert temas_con_mismas_preguntas([_tema(_p("a")), _tema(_p("b"))], _definicion()) == []


def test_mismas_preguntas_en_otro_orden():
    avisos = temas_con_mismas_preguntas([_tema(_p("a"), _p("b")), _tema(_p("b"), _p("a")), _tema(_p("c"))],
                                        _definicion())
    assert avisos == ["los temas 1 y 2 tienen las mismas preguntas (cambia sólo el orden): para que cada "
                      "tema tenga otras, usá sortear_por_tema."]


def test_con_sorteo_dice_que_faltan_preguntas():
    avisos = temas_con_mismas_preguntas([_tema(_p("a")), _tema(_p("a", ("no", "sí")))], _definicion(sortear=True))
    assert len(avisos) == 1 and "no tienen preguntas suficientes" in avisos[0]


def test_temas_identicos_y_otro_con_el_orden_cambiado():
    a, b = _p("a"), _p("b")
    avisos = temas_con_mismas_preguntas([_tema(a, b), _tema(b, a), _tema(a, b)], _definicion())
    assert avisos[0].startswith("los temas 1 y 3 son idénticos")
    assert avisos[1].startswith("los temas 1, 2 y 3 tienen las mismas preguntas")


def test_todos_identicos_no_repite_el_aviso_del_orden():
    a = _p("a")
    avisos = temas_con_mismas_preguntas([_tema(a), _tema(a)], _definicion())
    assert len(avisos) == 1 and "idénticos" in avisos[0]


def test_sin_comparar_orden_solo_el_conjunto():
    a = _p("a")
    avisos = temas_con_mismas_preguntas([_tema(a), _tema(a)], _definicion(), comparar_orden=False)
    assert avisos == ["los temas 1 y 2 tienen las mismas preguntas (puede cambiar sólo el orden): para que "
                      "cada tema tenga otras, usá sortear_por_tema."]


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / "b.gift").write_text("".join(f"::q{i}::Pregunta {i} {{T}}\n\n" for i in range(4)), encoding="utf-8")

    def definicion(cantidad, temas=3, **config):
        d = tmp_path / "d.yaml"
        config_yaml = "{" + ", ".join(f"{k}: {json.dumps(v)}" for k, v in config.items()) + "}"
        d.write_text(f"""nombre_examen: "P"
institucion: "I"
materia: "M"
numero_temas: {temas}
configuracion_examen: {config_yaml}
input_banco: ["{tmp_path / 'b.gift'}"]
secciones_examen:
  - nombre: "A"
    pools:
      - cantidad: {cantidad}
""", encoding="utf-8")
        return d
    return definicion


def _correr(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["alucard", *argv])
    return main()


def test_generar_avisa_y_el_informe_lo_asienta(proyecto, tmp_path, monkeypatch, capsys):
    salida = tmp_path / "out"
    assert _correr(monkeypatch, "generar", "-d", str(proyecto(4, sortear_por_tema=True)), "-o", str(salida)) == 0
    out = "".join(capsys.readouterr())
    assert "los temas 1, 2 y 3 tienen las mismas preguntas (cambia sólo el orden)" in out
    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert "> ⚠ Los temas 1, 2 y 3 tienen las mismas preguntas" in informe


def test_generar_con_temas_que_difieren_no_avisa(proyecto, tmp_path, monkeypatch, capsys):
    assert _correr(monkeypatch, "generar", "-d", str(proyecto(1, temas=2, sortear_por_tema=True)),
                   "-o", str(tmp_path / "out")) == 0
    assert "mismas preguntas" not in "".join(capsys.readouterr())


def test_un_solo_tema_no_avisa(proyecto, tmp_path, monkeypatch, capsys):
    assert _correr(monkeypatch, "generar", "-d", str(proyecto(4, temas=1)), "-o", str(tmp_path / "out")) == 0
    assert "mismas preguntas" not in "".join(capsys.readouterr())


def test_generar_con_temas_identicos(proyecto, tmp_path, monkeypatch, capsys):
    definicion = proyecto(4, temas=2, mezclar_preguntas_dentro_seccion=False,
                          mezclar_opciones_dentro_pregunta=False)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-o", str(tmp_path / "out")) == 0
    assert "los temas 1 y 2 son idénticos" in "".join(capsys.readouterr())


def test_validar_avisa(proyecto, monkeypatch, capsys):
    assert _correr(monkeypatch, "validar", "-d", str(proyecto(4, sortear_por_tema=True))) == 0
    assert "(puede cambiar sólo el orden)" in "".join(capsys.readouterr())
