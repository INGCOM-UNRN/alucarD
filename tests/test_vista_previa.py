"""alucard ver: una pregunta (o un banco) sola, como sale en el examen."""

import sys
from pathlib import Path

from generador_examenes.__main__ import main
from generador_examenes.cli_commands import preguntas_por_linea

BANCO = """// Banco de prueba
::suma:: [markdown]¿Cuánto es 2+2?
{
=4
~3
}

::abb:: [markdown]¿Cuál es la raíz?
```estructura
type: tree
variant: bst
insert: [5, 3, 8]
```
{
=5
~3
}
"""


def _banco(tmp_path: Path) -> Path:
    ruta = tmp_path / "banco.gift"
    ruta.write_text(BANCO, encoding="utf-8")
    return ruta


def _ver(monkeypatch, *argumentos) -> int:
    monkeypatch.setattr(sys, "argv", ["alucard", "ver", *argumentos, "--no-abrir"])
    return main()


def test_ubica_la_pregunta_de_una_linea(tmp_path):
    assert preguntas_por_linea(_banco(tmp_path)) == [(2, "suma"), (8, "abb")]


def test_una_pregunta_por_titulo_con_su_diagrama(tmp_path, monkeypatch):
    banco, salida = _banco(tmp_path), tmp_path / "vp"
    assert _ver(monkeypatch, str(banco), "-q", "abb", "-o", str(salida)) == 0
    html = (salida / "examen_tema_01.html").read_text(encoding="utf-8")
    assert "¿Cuál es la raíz?" in html and "<svg" in html
    assert "¿Cuánto es 2+2?" not in html


def test_por_linea_y_con_clave(tmp_path, monkeypatch):
    banco, salida = _banco(tmp_path), tmp_path / "vp"
    assert _ver(monkeypatch, str(banco), "-l", "4", "--clave", "-o", str(salida)) == 0
    assert "¿Cuánto es 2+2?" in (salida / "examen_tema_01.html").read_text(encoding="utf-8")
    assert (salida / "clave_tema_01.html").exists()


def test_una_pregunta_que_no_existe_lista_las_que_hay(tmp_path, monkeypatch, capsys):
    assert _ver(monkeypatch, str(_banco(tmp_path)), "-q", "zzz", "-o", str(tmp_path / "vp")) == 1
    assert "ninguna pregunta se llama «zzz» (hay: suma, abb)" in capsys.readouterr().err
