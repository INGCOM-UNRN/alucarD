"""informe.md: qué se eligió, de dónde y por qué quedó afuera cada consigna."""

import sys
from pathlib import Path

from generador_examenes.__main__ import main
from generador_examenes.core.informe import motivo_fuera
from generador_examenes.core.models import PoolConfig, Pregunta


def _consigna(id_, tema="listas", minutos=20):
    return Pregunta(id=id_, tipo="consigna_practica", nombre=id_, categoria=f"consignas/{tema}",
                    enunciado_html="x", metadata={"minutos": minutos})


def test_motivo_de_cada_filtro():
    pool = PoolConfig(categorias=["consignas/listas"], tipos=["consigna_practica"], minutos_max=30)
    assert motivo_fuera(_consigna("ok"), pool) is None
    assert motivo_fuera(_consigna("larga", minutos=45), pool) == "45 min, fuera de [0, 30]"
    assert motivo_fuera(_consigna("sin", minutos=None), pool) == "no tiene minutos estimados"
    assert motivo_fuera(_consigna("otra", tema="pilas"), pool) == "categoría consignas/pilas"


def _ejercicio(raiz: Path, id_, tema, minutos, publicar=True):
    d = raiz / tema / id_
    d.mkdir(parents=True)
    (d / "ejercicio.yaml").write_text(f"id: {id_}\ntitulo: {id_}\ntema: {tema}\nminutos_estimados: {minutos}\n"
                                      f"publicar: {'true' if publicar else 'false'}\n", encoding="utf-8")
    (d / "enunciado.md").write_text("Hacer algo.\n", encoding="utf-8")


def test_informe_de_una_generacion(tmp_path, monkeypatch):
    consignas = tmp_path / "consignas"
    _ejercicio(consignas, "corta", "listas", 20)
    _ejercicio(consignas, "larga", "listas", 90)
    _ejercicio(consignas, "borrador", "listas", 10, publicar=False)
    banco = tmp_path / "b.txt"
    banco.write_text("::P1::¿2+2?{=4 ~3 ~5}\n\n::P2::Test2{T}\n", encoding="utf-8")
    definicion = tmp_path / "def.yaml"
    definicion.write_text(f"""nombre_examen: "Parcial"
institucion: "UNRN"
materia: "Programación"
configuracion_examen:
  generar_clave_profesor: false
input_banco: ["{banco}"]
input_consignas: ["{consignas}"]
secciones_examen:
  - nombre: "Teoría"
    pools:
      - tipos: [seleccion_multiple]
        cantidad: 1
  - nombre: "Práctica"
    pools:
      - tipos: [consigna_practica]
        cantidad: 1
        minutos_max: 30
""", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion), "-o", str(tmp_path / "out"),
                                      "-n", "2"])
    assert main() == 0
    informe = (tmp_path / "out" / "informe.md").read_text(encoding="utf-8")
    assert "| Teoría | 1 |" in informe and "| Práctica | 1 |" in informe
    assert "| Práctica | corta | consigna_practica | consignas/listas |" in informe
    assert "**Tema 2:**" in informe
    assert "- «larga» (deckard:larga): 90 min, fuera de [0, 30]" in informe
    assert "- «borrador» (deckard:borrador): publicar: false" in informe


def test_inventario_por_categoria_y_tipo_y_pools():
    from generador_examenes.core.informe import inventario
    from generador_examenes.core.models import DefinicionExamen

    preguntas = {
        "1": Pregunta(id="1", tipo="seleccion_multiple", nombre="a", categoria="teoria", enunciado_html="x"),
        "2": Pregunta(id="2", tipo="verdadero_falso", nombre="b", categoria="teoria", enunciado_html="x"),
        "3": _consigna("c"),
    }
    definicion = DefinicionExamen(nombre_examen="P", institucion="I", materia="M", configuracion_examen={},
                                  secciones_examen=[{"nombre": "T", "pools": [{"categoria": "teoria", "cantidad": 2}]},
                                                    {"nombre": "C", "pools": [{"tipos": ["consigna_practica"],
                                                                               "cantidad": 3}]}])
    texto, alcanza = inventario(preguntas, definicion)
    fila = next(l for l in texto.splitlines() if l.startswith("teoria"))
    assert fila.split() == ["teoria", "2", "1", "1"]
    assert "✓ T, pool 1: pide 2, hay 2" in texto
    assert "✗ C, pool 1: pide 3, hay 1" in texto and not alcanza


def test_categorias_resumen_con_la_definicion(tmp_path, monkeypatch, capsys):
    banco = tmp_path / "b.txt"
    banco.write_text("::P1::¿2+2?{=4 ~3 ~5}\n", encoding="utf-8")
    definicion = tmp_path / "def.yaml"
    definicion.write_text(f"""nombre_examen: "P"
institucion: "I"
materia: "M"
configuracion_examen: {{}}
input_banco: ["{banco}"]
secciones_examen:
  - nombre: "A"
    pools:
      - cantidad: 2
""", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alucard", "categorias", "--resumen", "-d", str(definicion)])
    assert main() == 1
    assert "✗ A, pool 1: pide 2, hay 1" in capsys.readouterr().out
