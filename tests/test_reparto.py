"""`alucard repartir`: el tema de cada estudiante, en la carpeta que sella uatu (Ola 47)."""

from collections import Counter

import pytest

from generador_examenes.__main__ import main
from generador_examenes.core.reparto import RepartoError, asignar, leer_padron, repartir


def _temas(tmp_path, cantidad=3):
    carpeta = tmp_path / "temas"
    carpeta.mkdir()
    for i in range(1, cantidad + 1):
        (carpeta / f"examen_tema_{i:02}.pdf").write_bytes(f"tema {i}".encode())
        (carpeta / f"clave_tema_{i:02}.pdf").write_bytes(b"respuestas")
    return carpeta


def _padron(tmp_path, texto="ana\nBeto  # recursante\n\ncarla\ndiego\n"):
    ruta = tmp_path / "padron.txt"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_padron_normaliza_y_valida(tmp_path):
    assert leer_padron(_padron(tmp_path)) == ["ana", "beto", "carla", "diego"]
    for malo in ("ana\nana\n", "ana_p\n", "../x\n", "# nada\n"):
        with pytest.raises(RepartoError):
            leer_padron(_padron(tmp_path, malo))


def test_temas_en_partes_iguales_y_reproducible(tmp_path):
    temas = sorted(_temas(tmp_path).glob("examen_*"))
    usuarios = [f"u{i}" for i in range(10)]
    reparto = asignar(usuarios, temas, 7)
    cantidades = Counter(reparto.values()).values()
    assert max(cantidades) - min(cantidades) <= 1
    assert reparto == asignar(list(reversed(usuarios)), temas, 7), "no depende del orden del padrón"
    assert reparto != asignar(usuarios, temas, 8)


def test_repartir_copia_el_tema_y_nunca_la_clave(tmp_path):
    salida = tmp_path / "repartidos"
    res = repartir(_temas(tmp_path), _padron(tmp_path), salida, 1)
    assert sorted(p.name for p in salida.iterdir()) == ["ana", "beto", "carla", "diego"]
    for usuario, tema in res.asignacion.items():
        numero = tema.split("_")[-1].split(".")[0]
        assert [p.name for p in (salida / usuario).iterdir()] == ["examen.pdf"]
        assert (salida / usuario / "examen.pdf").read_bytes() == f"tema {int(numero)}".encode()
    assert res.registro == tmp_path / "repartidos.asignacion.csv"
    assert res.registro.read_text(encoding="utf-8").startswith("usuario,tema\nana,examen_tema_")


def test_no_mezcla_con_un_reparto_viejo(tmp_path):
    salida = tmp_path / "repartidos"
    (salida / "viejo").mkdir(parents=True)
    with pytest.raises(RepartoError, match="no está vacía"):
        repartir(_temas(tmp_path), _padron(tmp_path), salida, 1)


def test_sin_temas(tmp_path):
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    with pytest.raises(RepartoError, match="no tiene temas"):
        repartir(vacia, _padron(tmp_path), tmp_path / "s", 1)


def _correr(monkeypatch, args):
    monkeypatch.setattr("sys.argv", ["alucard", *args])
    try:
        return main() or 0
    except SystemExit as salida:
        return salida.code or 0


def test_cli_informa_y_sale_con_el_codigo_correcto(tmp_path, monkeypatch, capsys):
    temas = _temas(tmp_path)
    padron = _padron(tmp_path)
    salida = tmp_path / "repartidos"
    assert _correr(monkeypatch, ["repartir", str(temas), "--padron", str(padron), "-o", str(salida)]) == 0
    assert "4 examen(es)" in capsys.readouterr().out
    assert _correr(monkeypatch, ["repartir", str(temas), "--padron", str(padron), "-o", str(salida)]) == 1
    assert "no está vacía" in capsys.readouterr().err
