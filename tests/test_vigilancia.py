"""--watch: volver a generar cuando cambia una fuente, nunca por lo que se genera."""

from pathlib import Path
from types import SimpleNamespace

from generador_examenes.cli_commands import fuentes_de_generacion
from generador_examenes.core.vigilancia import huella, vigilar


def test_huella_de_carpetas_sin_la_salida(tmp_path):
    (tmp_path / "bancos").mkdir()
    (tmp_path / "bancos" / "a.gift").write_text("x", encoding="utf-8")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "examen.html").write_text("y", encoding="utf-8")
    h = huella([tmp_path], excluir=[tmp_path / "output"])
    assert [p.name for p in h] == ["a.gift"]


def test_vuelve_a_generar_solo_si_cambia_algo(tmp_path):
    banco = tmp_path / "banco.gift"
    banco.write_text("uno", encoding="utf-8")
    corridas = []
    cambios = iter([None, "dos", None])

    def dormir(_segundos):
        nuevo = next(cambios)
        if nuevo:
            banco.write_text(nuevo, encoding="utf-8")

    codigo = vigilar(lambda: [banco], lambda: corridas.append(1) or 0, vueltas=3, dormir=dormir)
    assert codigo == 0 and len(corridas) == 2  # la primera y la del cambio


def test_las_fuentes_salen_de_la_definicion_y_del_toml(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "alucard.toml").write_text('path_images = "img"\noutput_dir = "salida"\n', encoding="utf-8")
    definicion = tmp_path / "def.yaml"
    definicion.write_text("input_banco: [b.gift]\ninput_consignas: [consignas]\n", encoding="utf-8")
    args = SimpleNamespace(definicion=definicion, input_banco=None, path_images=None, output_dir=None,
                           typst_template=None)
    rutas, salida = fuentes_de_generacion(args)
    assert {Path(r).name for r in rutas} == {"def.yaml", "alucard.toml", "b.gift", "consignas", "img"}
    assert salida == [tmp_path / "salida"]
