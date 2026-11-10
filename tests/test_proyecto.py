"""alucard.toml: la configuración del curso, con prioridad línea de comandos > YAML > toml > defecto."""

import json
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


def _segunda_definicion(definicion: Path, nombre: str = "recuperatorio") -> Path:
    otra = definicion.with_stem(nombre)
    otra.write_text(definicion.read_text(encoding="utf-8"), encoding="utf-8")
    return otra


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


def test_generar_sin_d_toma_la_definicion_y_la_salida_del_toml(tmp_path, monkeypatch):
    _proyecto(tmp_path, 'definicion = "examenes/def.yaml"\ninput_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    monkeypatch.chdir(tmp_path / "examenes")  # el toml se busca hacia arriba y sus rutas son relativas a él
    assert _correr(monkeypatch, "generar") == 0
    assert len(list((tmp_path / "salida").glob("examen_tema_*.html"))) == 1


def test_varias_definiciones_del_toml_salen_en_subcarpetas(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'definicion = ["examenes/def.yaml", "examenes/recuperatorio.yaml"]\n'
                                     'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar") == 0
    for nombre in ("def", "recuperatorio"):
        assert (tmp_path / "salida" / nombre / "examen_tema_01.html").is_file()
        assert (tmp_path / "salida" / nombre / "informe.md").is_file()
    assert not list((tmp_path / "salida").glob("*.html"))


def test_d_repetido_manda_sobre_el_toml(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'definicion = "no/existe.yaml"\ninput_banco = ["bancos/b.txt"]\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    salida = tmp_path / "cli"
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(otra), "-o", str(salida)) == 0
    assert {d.name for d in salida.iterdir()} == {"def", "recuperatorio"}


def test_la_misma_definicion_dos_veces_es_una_sola(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(definicion)) == 0
    assert (tmp_path / "salida" / "examen_tema_01.html").is_file()


def test_una_definicion_inexistente_frena_antes_de_escribir(tmp_path, monkeypatch, capsys):
    _proyecto(tmp_path, 'definicion = ["examenes/def.yaml", "falta.yaml"]\n'
                        'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar") == 1
    assert "falta.yaml" in capsys.readouterr().err
    assert not (tmp_path / "salida").exists()


def test_dos_definiciones_con_el_mismo_nombre_son_un_error(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    (tmp_path / "otra").mkdir()
    gemela = tmp_path / "otra" / "def.yaml"
    gemela.write_text(definicion.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(gemela)) == 1
    assert "misma subcarpeta" in capsys.readouterr().err
    assert not (tmp_path / "salida").exists()


def test_si_una_falla_las_demas_se_generan(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    rota = _segunda_definicion(definicion, "a_rota")
    rota.write_text("nombre_examen: sin el resto\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(rota), "-d", str(definicion)) == 1
    assert (tmp_path / "salida" / "def" / "examen_tema_01.html").is_file()
    assert "fallaron 1 de 2" in capsys.readouterr().err


def test_json_de_varias_es_un_solo_documento(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(otra), "--json") == 0
    examenes = json.loads(capsys.readouterr().out)["examenes"]
    assert [Path(e["output_dir"]).name for e in examenes] == ["def", "recuperatorio"]


def test_validar_sin_d_revisa_las_del_toml_y_no_escribe(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'definicion = ["examenes/def.yaml", "examenes/recuperatorio.yaml"]\n'
                                     'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "validar") == 0
    assert capsys.readouterr().out.count("Validación exitosa") == 2
    assert not (tmp_path / "salida").exists()


def test_alucard_a_secas_no_genera_lo_del_toml(tmp_path, monkeypatch):
    _proyecto(tmp_path, 'definicion = "examenes/def.yaml"\ninput_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        _correr(monkeypatch)
    assert not (tmp_path / "salida").exists()


def test_ortografia_no_acepta_varias_definiciones(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        _correr(monkeypatch, "ortografia", "-d", str(definicion), "-d", str(otra))


def test_watch_mira_todas_las_definiciones(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    vistas = {}

    def vigilar(rutas, accion, excluir=()):
        vistas.update(rutas=set(rutas()), excluir=list(excluir))
        return accion()

    monkeypatch.setattr("generador_examenes.core.vigilancia.vigilar", vigilar)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(otra), "--watch") == 0
    assert {definicion, otra} <= vistas["rutas"]
    assert tmp_path / "salida" in vistas["excluir"]


def test_subdirectorio_del_yaml_dentro_de_la_salida_del_toml(tmp_path, monkeypatch):
    _proyecto(tmp_path, 'definicion = "examenes/def.yaml"\ninput_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
              'subdirectorio: "parcial1/teoria"\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar") == 0
    assert (tmp_path / "salida" / "parcial1" / "teoria" / "examen_tema_01.html").is_file()


def test_examen_compuesto_agrupa_sus_partes(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'definicion = ["examenes/def.yaml", "examenes/practica.yaml"]\n'
                                     'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
                           'subdirectorio: "parcial1/teoria"\n')
    practica = _segunda_definicion(definicion, "practica")
    practica.write_text(practica.read_text(encoding="utf-8").replace("teoria", "practica"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar") == 0
    assert {d.name for d in (tmp_path / "salida" / "parcial1").iterdir()} == {"teoria", "practica"}


def test_el_subdirectorio_se_suma_a_o(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
                           'subdirectorio: "teoria"\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-o", str(tmp_path / "cli")) == 0
    assert (tmp_path / "cli" / "teoria" / "examen_tema_01.html").is_file()


def test_dos_definiciones_con_el_mismo_subdirectorio_son_un_error(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
                           'subdirectorio: "parcial1/"\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(otra)) == 1
    assert "parcial1" in capsys.readouterr().err
    assert not (tmp_path / "salida").exists()


@pytest.mark.parametrize("subdirectorio", ["../afuera", "/tmp/afuera", "a/../../afuera"])
def test_el_subdirectorio_no_sale_de_la_salida(tmp_path, monkeypatch, subdirectorio):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\noutput_dir = "salida"\n',
                           f'subdirectorio: "{subdirectorio}"\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion)) == 1
    assert not (tmp_path / "salida").exists()


def test_iniciar_deja_listo_generar_sin_opciones(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "iniciar") == 0
    assert _correr(monkeypatch, "validar") == 0
    assert _correr(monkeypatch, "generar") == 0
    assert len(list((tmp_path / "output").glob("examen_tema_*.html"))) == 2
    assert "alucard generar" in (tmp_path / "README_PROYECTO.md").read_text(encoding="utf-8")


def test_balance_check_toma_los_bancos_del_toml(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "balance-check", "-d", str(definicion), "-n", "1", "--umbral", "1") == 0


def test_build_toma_los_bancos_del_toml(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "build", "-d", str(definicion), "-n", "1", "-f", "html", "--umbral", "1",
                   "-o", str(tmp_path / "o")) == 0


def test_accessible_agranda_la_letra_y_sube_el_contraste(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\n[estilo]\ntamano = 10\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "--accessible", "-o", str(tmp_path / "a")) == 0
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-o", str(tmp_path / "n")) == 0
    accesible = (tmp_path / "a" / "examen_tema_01.html").read_text(encoding="utf-8")
    comun = (tmp_path / "n" / "examen_tema_01.html").read_text(encoding="utf-8")
    assert "font-size: 14pt" in accesible and "font-size: 10pt" in comun and accesible != comun


def test_accessible_no_achica_una_letra_mas_grande(tmp_path, monkeypatch):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\n[estilo]\ntamano = 16\n')
    monkeypatch.chdir(tmp_path)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "--accessible", "-o", str(tmp_path / "a")) == 0
    assert "font-size: 16pt" in (tmp_path / "a" / "examen_tema_01.html").read_text(encoding="utf-8")


def test_si_typst_falla_en_una_de_varias_definiciones_el_codigo_es_1(tmp_path, monkeypatch, capsys):
    definicion = _proyecto(tmp_path, 'input_banco = ["bancos/b.txt"]\nformato = ["pdf"]\n')
    otra = _segunda_definicion(definicion)
    monkeypatch.chdir(tmp_path)
    _typst_roto(monkeypatch)
    assert _correr(monkeypatch, "generar", "-d", str(definicion), "-d", str(otra)) == 1
    assert "fallaron 2 de 2" in capsys.readouterr().err
