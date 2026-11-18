"""Cuando la generación falla, el error dice qué filtro vació el pool y queda un informe.md."""

import sys

import pytest

from generador_examenes.__main__ import main
from generador_examenes.core.informe import por_que_no_alcanza
from generador_examenes.core.models import PoolConfig, Pregunta


def _p(id_, categoria="General", etiquetas=(), tipo="verdadero_falso", fuente="t.gift"):
    return Pregunta(id=id_, tipo=tipo, nombre=id_, categoria=categoria, enunciado_html="x",
                    etiquetas=list(etiquetas), fuente_banco=fuente)


BANCO = {p.id: p for p in [_p("a", "punteros", ["memoria"]), _p("b", "punteros/arreglos"), _p("c", "listas")]}


@pytest.mark.parametrize("pool, esperado", [
    (PoolConfig(categoria="Punteros/listas", cantidad=1), "¿Quisiste decir «punteros»"),
    (PoolConfig(categoria="punteos", cantidad=1), "¿Quisiste decir «punteros»"),
    (PoolConfig(categoria="pilas", cantidad=1), "Categorías que hay: «listas», «punteros»"),
    (PoolConfig(etiquetas=["memora"], cantidad=1), "¿Quisiste decir «memoria»?"),
    (PoolConfig(tipos=["desarrollo"], cantidad=1), "Tipos que hay: verdadero_falso (3)"),
    (PoolConfig(banco="t.gif", cantidad=1), "¿Quisiste decir «t.gift»?"),
    (PoolConfig(categoria="listas", cantidad=2), "El filtro categoría «listas» deja 1 de 3."),
    (PoolConfig(preguntas_fijadas=["a", "zz"], cantidad=2), "No existen en el banco: zz."),
])
def test_dice_que_filtro_vacio_el_pool_y_que_hay_parecido(pool, esperado):
    assert esperado in por_que_no_alcanza(pool, BANCO, pool.cantidad)


def test_sin_categorias_sugiere_category_o_banco_toml():
    banco = {"a": _p("a"), "b": _p("b")}
    texto = por_que_no_alcanza(PoolConfig(categoria="punteros", cantidad=1), banco, 1)
    assert "Ninguna pregunta tiene categoría" in texto and "banco.toml" in texto


def _proyecto(tmp_path, banco, categoria="Punteros/listas"):
    definicion = tmp_path / "def.yaml"
    definicion.write_text(f"""nombre_examen: "P"
institucion: "I"
materia: "M"
configuracion_examen: {{}}
input_banco: ["{banco}"]
secciones_examen:
  - nombre: "A"
    pools:
      - categoria: "{categoria}"
        cantidad: 1
  - nombre: "B"
    pools:
      - categoria: "punteros"
        cantidad: 1
""", encoding="utf-8")
    return definicion


def _generar(monkeypatch, definicion, salida, *extra):
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion), "-o", str(salida), *extra])
    return main()


@pytest.fixture
def carpeta(tmp_path):
    raiz = tmp_path / "bancos"
    (raiz / "punteros").mkdir(parents=True)
    (raiz / "punteros" / "t.gift").write_text("::a::Uno {T}\n\n::b::Dos {F}\n", encoding="utf-8")
    (raiz / "banco.toml").write_text('categoria = "carpeta"\n', encoding="utf-8")
    return raiz


def test_un_pool_vacio_deja_el_informe_con_el_diagnostico(carpeta, tmp_path, monkeypatch, capsys):
    salida = tmp_path / "out"
    assert _generar(monkeypatch, _proyecto(tmp_path, carpeta), salida) == 1
    err = capsys.readouterr().err
    assert "¿Quisiste decir «punteros»?" in err
    assert f"diagnóstico: {salida / 'informe.md'}" in err

    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert "(falló)" in informe and "corrida anterior" in informe
    assert "| A | 1 | Pool(cat:Punteros/listas, cant:1) | 0 | 1 | ✗ |" in informe
    assert "| B | 1 | Pool(cat:punteros, cant:1) | 2 | 1 | ✓ |" in informe
    assert "- **A, pool 1** (pide 1, hay 0): El filtro categoría «Punteros/listas» deja 0 de 2." in informe
    assert "## Categorías del banco" in informe and "| punteros | 2 |" in informe
    assert "carpeta con 1 banco(s)" in informe


def test_una_carpeta_sin_bancos_tambien_deja_el_informe(tmp_path, monkeypatch):
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    salida = tmp_path / "out"
    assert _generar(monkeypatch, _proyecto(tmp_path, vacia), salida) == 1
    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert "No se cargaron preguntas" in informe
    assert "carpeta sin bancos .gift ni .xml" in informe and "El banco no tiene preguntas." in informe


def test_un_banco_toml_invalido_deja_el_error_una_vez(carpeta, tmp_path, monkeypatch):
    (carpeta / "banco.toml").write_text('categoria = "x"\n', encoding="utf-8")
    salida = tmp_path / "out"
    assert _generar(monkeypatch, _proyecto(tmp_path, carpeta), salida) == 1
    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert informe.count("categoria es") == 1


def test_validar_no_escribe_el_informe(carpeta, tmp_path, monkeypatch):
    salida = tmp_path / "output"
    monkeypatch.chdir(tmp_path)                 # la salida por omisión, ./output
    monkeypatch.setattr(sys, "argv", ["alucard", "validar", "-d", str(_proyecto(tmp_path, carpeta))])
    assert main() == 1
    assert not (salida / "informe.md").exists()


def test_el_informe_de_una_generacion_buena_lista_las_categorias(carpeta, tmp_path, monkeypatch):
    salida = tmp_path / "out"
    assert _generar(monkeypatch, _proyecto(tmp_path, carpeta, categoria="punteros"), salida) == 0
    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert "(falló)" not in informe and "| punteros | 2 |" in informe
