"""alucard.toml: la configuración del curso, con prioridad línea de comandos > YAML > toml > defecto."""

import sys
from pathlib import Path

import pytest

from generador_examenes.__main__ import main
from generador_examenes.config import proyecto

BANCO = "::P1::Test{=Si ~No}\n::P2::Test2{T}\n"


def _proyecto(tmp_path: Path, toml: str, definicion: str = "") -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "bancos").mkdir()
    (tmp_path / "bancos" / "b.txt").write_text(BANCO, encoding="utf-8")
    (tmp_path / "alucard.toml").write_text(toml, encoding="utf-8")
    d = tmp_path / "examenes"
    d.mkdir()
    (d / "def.yaml").write_text(f"""nombre_examen: "Prueba"
institucion: "UNRN"
materia: "Programación"
configuracion_examen:
  generar_clave_profesor: false
secciones_examen:
  - nombre: "A"
    pools:
      - cantidad: 1
{definicion}""", encoding="utf-8")
    return d / "def.yaml"


def test_busca_hacia_arriba_y_resuelve_rutas(tmp_path):
    _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\nformato = "pdf"\n'
                        '[ortografia]\npalabras = ["malloc"]\n')
    conf = proyecto.cargar(tmp_path / "examenes")
    assert conf.ruta == tmp_path / "alucard.toml"
    assert conf.input_banco == [tmp_path / "bancos" / "b.txt"]
    assert conf.output_dir == tmp_path / "salida" and conf.formato == ["pdf"]
    assert conf.palabras == ["malloc"]


def test_no_sale_del_repositorio(tmp_path):
    (tmp_path / "alucard.toml").write_text("semilla = 1\n", encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    assert proyecto.cargar(repo).ruta is None


def test_un_toml_roto_dice_cual(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "alucard.toml").write_text("semilla = \n", encoding="utf-8")
    with pytest.raises(ValueError, match="alucard.toml"):
        proyecto.cargar(tmp_path)


def test_generar_con_lo_del_toml(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\nnumero_temas = 2\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion)])
    assert main() == 0
    assert len(list((tmp_path / "salida").glob("*.html"))) == 2


def test_la_definicion_y_la_linea_de_comandos_mandan(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\nnumero_temas = 3\n',
                           "numero_temas: 1\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(definicion), "-o", str(tmp_path / "cli")])
    assert main() == 0
    assert not (tmp_path / "salida").exists()
    assert len(list((tmp_path / "cli").glob("*.html"))) == 1


def _correr(monkeypatch, *argumentos: str) -> int:
    monkeypatch.setattr(sys, "argv", ["alucard", *argumentos])
    return main()


def _typst_roto(monkeypatch):
    from generador_examenes.generators import pdf_renderer

    def compilar(*_a, **_k):
        raise RuntimeError("Typst no está instalado (ni la librería de Python ni el binario)")

    monkeypatch.setattr(pdf_renderer, "compilar_typst_a_pdf", compilar)


def test_si_typst_falla_generar_sale_con_error_y_sin_pdf(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\nformato = ["pdf"]\n')
    monkeypatch.chdir(tmp_path)
    _typst_roto(monkeypatch)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-o", str(tmp_path / "o")) == 1
    assert not list((tmp_path / "o").glob("*.pdf"))
    assert "Generación completada" not in capsys.readouterr().out


def test_si_typst_falla_la_vista_previa_lo_dice(tmp_path, monkeypatch, capsys):
    (tmp_path / "b.gift").write_text(BANCO, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _typst_roto(monkeypatch)
    assert _correr(monkeypatch, "ver", "b.gift", "-f", "pdf", "--no-abrir", "-o", str(tmp_path / "v")) == 1
    assert "Error: Typst no pudo compilar" in capsys.readouterr().err


def test_html_no_depende_de_typst(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\nformato = ["html"]\n')
    monkeypatch.chdir(tmp_path)
    _typst_roto(monkeypatch)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-o", str(tmp_path / "o")) == 0
