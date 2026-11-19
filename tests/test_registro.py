"""Registro de exámenes tomados (`alucard-examen/1`): guardar, no repetir en el cuatrimestre, resultados y
calidad de las preguntas."""

import csv
import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from generador_examenes.__main__ import main
from generador_examenes.core import registro
from generador_examenes.core.models import Opcion, Pregunta


def _mc(id_, enunciado="¿Cuál?", opciones=(("a", True), ("b", False))):
    return Pregunta(id=id_, tipo="seleccion_multiple", nombre=id_, categoria="c", enunciado_html=enunciado,
                    opciones=[Opcion(texto_html=t, es_correcta=c) for t, c in opciones])


def test_la_huella_es_el_contenido_y_no_el_id_ni_el_orden():
    a = _mc("x", opciones=(("a", True), ("b", False)))
    assert registro.huella(a) == registro.huella(_mc("otro_id", opciones=(("b", False), ("a", True))))
    assert registro.huella(a) == registro.huella(_mc("x", enunciado="  ¿Cuál?\n"))
    assert registro.huella(a) != registro.huella(_mc("x", enunciado="¿Cuál es?"))
    assert registro.huella(a) != registro.huella(_mc("x", opciones=(("a", False), ("b", True))))


@pytest.mark.parametrize("dia, cuatri", [(date(2026, 3, 10), "2026-1C"), (date(2026, 7, 31), "2026-1C"),
                                         (date(2026, 8, 1), "2026-2C"), (date(2026, 12, 20), "2026-2C")])
def test_cuatrimestre_de_la_fecha(dia, cuatri):
    assert registro.cuatrimestre_de(dia) == cuatri


def test_de_donde_sale_cada_dato_del_registro(tmp_path):
    from generador_examenes.core.models import RegistroDefinicion

    curso = SimpleNamespace(ruta=tmp_path / "alucard.toml", registro={"cuatrimestre": "2026-1C", "repetidas": "avisar"})
    sin = SimpleNamespace(registro=None, fecha="2026-09-01")
    cfg = registro.configuracion(sin, tmp_path / "parcial1.yaml", curso)
    assert (cfg.id, cfg.cuatrimestre, cfg.repetidas, cfg.carpeta) == ("parcial1", "2026-1C", "avisar", tmp_path / "registro")
    propio = SimpleNamespace(registro=RegistroDefinicion(id="p1", cuatrimestre="2026-2C"), fecha=None)
    assert registro.configuracion(propio, tmp_path / "x.yaml", curso).archivo == tmp_path / "registro/2026-2C/p1.json"
    assert registro.configuracion(propio, tmp_path / "x.yaml", curso, "2027-1C", "rec").archivo.parts[-2:] == ("2027-1C", "rec.json")
    vacio = SimpleNamespace(ruta=None, registro={})
    assert registro.configuracion(sin, tmp_path / "x.yaml", vacio).cuatrimestre == "2026-2C"   # por la fecha
    with pytest.raises(registro.ErrorRegistro):
        registro.configuracion(sin, tmp_path / "x.yaml", vacio, id_="con espacio")


# --- De punta a punta ------------------------------------------------------------------------------------

def _definicion(carpeta: Path, nombre: str, mc=3, vf=1, extra=""):
    (carpeta / f"{nombre}.yaml").write_text(f"""nombre_examen: "{nombre}"
institucion: "I"
materia: "M"
fecha: "2026-09-10"
numero_temas: 2
configuracion_examen: {{}}
{extra}
secciones_examen:
  - nombre: "A"
    pools:
      - tipos: ["seleccion_multiple"]
        cantidad: {mc}
      - tipos: ["verdadero_falso"]
        cantidad: {vf}
""", encoding="utf-8")
    return carpeta / f"{nombre}.yaml"


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    (tmp_path / "alucard.toml").write_text('input_banco = ["banco.gift"]\n[registro]\ncuatrimestre = "2026-2C"\n',
                                           encoding="utf-8")
    preguntas = [f"::q{i}::¿Pregunta {i}? {{=bien{i} ~mal{i}a ~mal{i}b ~mal{i}c}}" for i in range(8)]
    preguntas += ["::vf1::El cielo es verde. {F}", "::vf2::El agua moja. {T}"]
    (tmp_path / "banco.gift").write_text("\n\n".join(preguntas) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["alucard", *argv])
    return main()


def _ids(ruta: Path) -> set[str]:
    return set(json.loads(ruta.read_text(encoding="utf-8"))["preguntas"])


def test_guardar_escribe_un_registro_valido_y_no_genera_archivos(proyecto, monkeypatch, capsys):
    _definicion(proyecto, "parcial1")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0
    ruta = proyecto / "registro" / "2026-2C" / "parcial1.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert registro.problemas(datos) == []
    assert datos["schema"] == "alucard-examen/1" and datos["revision"] == 1 and len(datos["temas"]) == 2
    assert datos["definicion"]["contenido"]["nombre_examen"] == "parcial1"
    for tema in datos["temas"]:
        preguntas = [p for s in tema["secciones"] for p in s["preguntas"]]
        assert [p["orden"] for p in preguntas] == [1, 2, 3, 4]
        for p in preguntas:
            opciones = datos["preguntas"][p["id"]]["opciones"]
            assert sorted(p["opciones"]) == list(range(len(opciones)))      # una permutación del banco
            correctas = [chr(65 + i) for i, idx in enumerate(p["opciones"]) if opciones[idx]["es_correcta"]]
            assert p["correctas"] == correctas
    assert not (proyecto / "output").exists()
    assert "Registro:" in capsys.readouterr().out


def test_el_segundo_examen_no_repite_y_el_primero_se_vuelve_a_guardar_igual(proyecto, monkeypatch, capsys):
    _definicion(proyecto, "parcial1")
    _definicion(proyecto, "parcial2")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial2.yaml") == 0
    uno, dos = (proyecto / "registro/2026-2C/parcial1.json"), (proyecto / "registro/2026-2C/parcial2.json")
    assert not _ids(uno) & _ids(dos)
    assert "quedaron afuera" in "".join(capsys.readouterr())
    antes = json.loads(uno.read_text(encoding="utf-8"))
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0     # no se excluye a sí mismo
    despues = json.loads(uno.read_text(encoding="utf-8"))
    assert despues["revision"] == 2 and despues["temas"] == antes["temas"] and despues["registrado"] == antes["registrado"]


def test_sin_preguntas_libres_el_error_nombra_el_registro(proyecto, monkeypatch, capsys):
    _definicion(proyecto, "parcial1", vf=2)
    _definicion(proyecto, "parcial2")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0
    assert _cli(monkeypatch, "validar", "-d", "parcial2.yaml") == 1
    salida = "".join(capsys.readouterr())
    assert "El registro dejó afuera" in salida and "repetidas: avisar" in salida


def test_con_repetidas_avisar_se_usa_y_se_avisa(proyecto, monkeypatch, capsys):
    _definicion(proyecto, "parcial1", vf=2)
    _definicion(proyecto, "parcial2", extra="registro: {repetidas: avisar}")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial2.yaml") == 0
    salida = "".join(capsys.readouterr())
    assert "ya salió en parcial1 (2026-2C)" in salida


def test_otro_cuatrimestre_no_cuenta(proyecto, monkeypatch):
    _definicion(proyecto, "parcial1", vf=2)
    _definicion(proyecto, "parcial2")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml", "--cuatrimestre", "2026-1C") == 0
    assert _cli(monkeypatch, "validar", "-d", "parcial2.yaml") == 0


def test_una_pregunta_fijada_se_queda_con_aviso(proyecto, monkeypatch, capsys):
    _definicion(proyecto, "parcial1", vf=2)
    (proyecto / "parcial2.yaml").write_text("""nombre_examen: "p2"
institucion: "I"
materia: "M"
configuracion_examen: {}
secciones_examen:
  - nombre: "A"
    pools:
      - preguntas_fijadas: ["gift_9_vf1"]
        cantidad: 1
""", encoding="utf-8")
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial2.yaml") == 0
    assert "está fijada en un pool y ya salió en parcial1" in "".join(capsys.readouterr())
    assert _ids(proyecto / "registro/2026-2C/parcial2.json") == {"gift_9_vf1"}


def test_generar_con_registrar(proyecto, monkeypatch):
    _definicion(proyecto, "parcial1")
    assert _cli(monkeypatch, "generar", "-d", "parcial1.yaml", "-o", "out", "--registrar") == 0
    assert (proyecto / "out" / "examen_tema_01.html").exists()
    assert (proyecto / "registro/2026-2C/parcial1.json").exists()


# --- Resultados -----------------------------------------------------------------------------------------

def _registro_guardado(proyecto, monkeypatch, nombre="parcial1"):
    _definicion(proyecto, nombre)
    assert _cli(monkeypatch, "registro", "guardar", "-d", f"{nombre}.yaml") == 0
    ruta = proyecto / "registro" / "2026-2C" / f"{nombre}.json"
    return ruta, json.loads(ruta.read_text(encoding="utf-8"))


def _escribir_csv(ruta: Path, filas: list[list]):
    with ruta.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(filas)


def _correctas_y_vf(datos, tema):
    preguntas = [p for s in datos["temas"][tema - 1]["secciones"] for p in s["preguntas"]]
    return preguntas, [datos["preguntas"][p["id"]]["tipo"] for p in preguntas]


def test_importar_letras_vf_puntajes_y_blancos(proyecto, monkeypatch, capsys):
    ruta, datos = _registro_guardado(proyecto, monkeypatch)
    preguntas, tipos = _correctas_y_vf(datos, 1)
    fila = []
    for p, tipo in zip(preguntas, tipos, strict=True):
        if tipo == "verdadero_falso":
            fila.append("F")                         # vf1 es falsa, vf2 verdadera: depende de cuál salió
        else:
            fila.append(p["correctas"][0])
    fila[-1 if tipos[-1] != "verdadero_falso" else 0] = ""     # una en blanco
    _escribir_csv(proyecto / "r.csv", [["estudiante", "tema", "ausente", "1", "2", "3", "4"],
                                       ["E1", "1", "", *fila], ["E2", "2", "si", "", "", "", ""]])
    assert _cli(monkeypatch, "registro", "resultados", "parcial1", "r.csv") == 0
    resultados = json.loads(ruta.read_text(encoding="utf-8"))["resultados"]
    e1, e2 = resultados["estudiantes"]
    assert e2["ausente"] and e2["respuestas"] == {}
    assert sum(r["omitida"] for r in e1["respuestas"].values()) == 1
    assert all(r["opcion"] or r["omitida"] for r in e1["respuestas"].values())
    assert _cli(monkeypatch, "registro", "resultados", "parcial1", "r.csv") == 1      # ya tiene: --forzar
    assert "--forzar" in capsys.readouterr().err


@pytest.mark.parametrize("celda, mensaje", [("Z", "tiene 4 opciones"), ("9", "fuera de 0 a 1"), ("hola", "no es una letra")])
def test_resultados_invalidos(proyecto, monkeypatch, capsys, celda, mensaje):
    _registro_guardado(proyecto, monkeypatch)
    datos = json.loads((proyecto / "registro/2026-2C/parcial1.json").read_text(encoding="utf-8"))
    preguntas, tipos = _correctas_y_vf(datos, 1)
    columna = str(next(p["orden"] for p, t in zip(preguntas, tipos, strict=True) if t == "seleccion_multiple"))
    _escribir_csv(proyecto / "r.csv", [["estudiante", "tema", columna], ["E1", "1", celda]])
    assert _cli(monkeypatch, "registro", "resultados", "parcial1", "r.csv") == 1
    err = capsys.readouterr().err
    assert mensaje in err and "falta la columna" in err


def test_volver_a_guardar_con_resultados(proyecto, monkeypatch, capsys):
    ruta, _ = _registro_guardado(proyecto, monkeypatch)
    _escribir_csv(proyecto / "r.csv", [["estudiante", "tema", "ausente"], ["E1", "1", "si"]])
    assert _cli(monkeypatch, "registro", "resultados", "parcial1", "r.csv") == 0
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml") == 0            # mismas preguntas
    assert json.loads(ruta.read_text(encoding="utf-8"))["resultados"] is not None
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml", "-s", "7") == 1  # otras preguntas
    assert "ya tiene resultados" in capsys.readouterr().err
    assert _cli(monkeypatch, "registro", "guardar", "-d", "parcial1.yaml", "-s", "7", "--forzar") == 0
    assert json.loads(ruta.read_text(encoding="utf-8"))["resultados"] is None


# --- Calidad --------------------------------------------------------------------------------------------

def _sintetico(respuestas_por_estudiante: list[dict[str, str]]) -> dict:
    """Un registro de un tema con una pregunta de opciones por clave de las respuestas (A es la correcta)."""
    ids = list(respuestas_por_estudiante[0])
    opciones = [{"texto_html": t, "es_correcta": i == 0} for i, t in enumerate(("bien", "mal1", "mal2", "mal3"))]
    preguntas = {q: {"huella": "sha256:" + str(i) * 64, "nombre": q, "tipo": "seleccion_multiple", "categoria": "c",
                     "etiquetas": [], "fuente_banco": None, "enunciado_html": q, "opciones": opciones}
                 for i, q in enumerate(ids)}
    tema = {"tema": 1, "semilla": 1, "secciones": [{"nombre": "A", "preguntas": [
        {"orden": n, "id": q, "puntaje": 1.0, "opciones": [0, 1, 2, 3], "correctas": ["A"]}
        for n, q in enumerate(ids, 1)]}]}
    estudiantes = [{"estudiante": f"E{i}", "tema": 1, "ausente": False,
                    "respuestas": {q: {"opcion": letra or None, "puntaje": 1.0 if letra == "A" else 0.0,
                                       "omitida": not letra} for q, letra in r.items()}}
                   for i, r in enumerate(respuestas_por_estudiante)]
    return {"id": "x", "cuatrimestre": "2026-2C", "preguntas": preguntas, "temas": [tema],
            "resultados": {"importado": "2026-11-19T10:00:00", "fuente": "r.csv", "estudiantes": estudiantes}}


def test_dificultad_discriminacion_y_diagnosticos():
    # p1 la aciertan los que aciertan el resto; p4, los que fallan todo lo demás.
    filas = [{"p1": "A", "p2": "A", "p3": "A", "p4": "B"}] * 6 + [{"p1": "B", "p2": "B", "p3": "B", "p4": "A"}] * 6
    analisis, temas = registro.analizar([_sintetico(filas)])
    por = {a.id: a for a in analisis}
    assert por["p1"].dificultad == 0.5 and por["p1"].discriminacion == pytest.approx(1.0) and por["p1"].indice_d == 1.0
    assert por["p4"].discriminacion == pytest.approx(-1.0) and por["p4"].indice_d == -1.0
    assert any("negativa" in d for d in por["p4"].diagnostico)
    assert not any("negativa" in d for d in por["p1"].diagnostico)
    assert any("«mal3» casi no se elige" in d for d in por["p1"].diagnostico)
    assert {o["texto"]: o["elegida"] for o in por["p1"].opciones}["mal1"] == 0.5
    assert temas[0]["estudiantes"] == 12 and temas[0]["alfa"] is not None


def test_fácil_omitida_y_pocos_datos():
    filas = [{"p1": "A", "p2": "", "p3": "A"}] * 4 + [{"p1": "A", "p2": "A", "p3": "B"}]
    por = {a.id: a for a in registro.analizar([_sintetico(filas)])[0]}
    assert any("muy fácil" in d for d in por["p1"].diagnostico)
    assert por["p2"].omision == 0.8 and any("en blanco" in d for d in por["p2"].diagnostico)
    assert por["p1"].diagnostico[0].startswith("pocos datos")


def test_la_misma_pregunta_en_dos_examenes_se_suma():
    a, b = _sintetico([{"p1": "A", "p2": "A", "p3": "A"}] * 3), _sintetico([{"p1": "B", "p2": "A", "p3": "A"}] * 3)
    b["id"] = "y"
    p1 = next(x for x in registro.analizar([a, b])[0] if x.id == "p1")
    assert p1.n == 6 and p1.dificultad == 0.5 and p1.examenes == ["x", "y"]


def test_cli_analizar_listar_y_usadas(proyecto, monkeypatch, capsys):
    _, datos = _registro_guardado(proyecto, monkeypatch)
    assert _cli(monkeypatch, "registro", "analizar") == 1                   # sin resultados
    preguntas, _ = _correctas_y_vf(datos, 1)
    filas = [["estudiante", "tema", *[str(p["orden"]) for p in preguntas]]]
    filas += [[f"E{i}", "1", *[p["correctas"][0] if i % 2 else "" for p in preguntas]] for i in range(6)]
    _escribir_csv(proyecto / "r.csv", filas)
    assert _cli(monkeypatch, "registro", "resultados", "parcial1", "r.csv") == 0
    assert _cli(monkeypatch, "registro", "analizar", "-o", "calidad.md") == 0
    assert "# Calidad de las preguntas" in (proyecto / "calidad.md").read_text(encoding="utf-8")
    capsys.readouterr()
    assert _cli(monkeypatch, "registro", "listar", "--json") == 0
    assert json.loads(capsys.readouterr().out)[0]["estudiantes"] == 6
    assert _cli(monkeypatch, "registro", "usadas", "--json") == 0
    assert {f["nombre"] for f in json.loads(capsys.readouterr().out)} == {datos["preguntas"][q]["nombre"] for q in datos["preguntas"]}


def test_un_registro_que_no_cumple_el_esquema_se_avisa(proyecto, monkeypatch, capsys):
    (proyecto / "registro" / "2026-2C").mkdir(parents=True)
    (proyecto / "registro" / "2026-2C" / "roto.json").write_text('{"schema": "otro"}', encoding="utf-8")
    assert _cli(monkeypatch, "registro", "listar") == 0
    assert "no cumple alucard-examen/1" in capsys.readouterr().err
