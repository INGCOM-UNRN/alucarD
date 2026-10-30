"""Consignas prácticas de deckard, repositorios externos y filtros por tiempo requerido."""
import sys
from pathlib import Path

import pytest
import yaml

from generador_examenes.core import logic
from generador_examenes.core.consignas import (
    cargar_consignas,
    cargar_fuentes_complementarias,
    cargar_repositorio,
    detectar_tipo,
    myst_a_markdown,
    presentacion_efectiva,
    presentar_consigna,
    quitar_secciones,
)
from generador_examenes.core.models import (
    ConfiguracionExamen,
    DefinicionExamen,
    PoolConfig,
    PresentacionConsigna,
    RepositorioExterno,
    SeccionExamen,
)

ENUNCIADO = """Escribir la función pedida.

:::{tip} Ayuda
:class: dropdown
```{code-block} c
:linenos:
int x = 0;
```
:::

### 📋 Contrato de las Funciones

```c
int sumar(int a, int b);
```

### 🎯 Criterios de Aceptación

- [ ] Compila.
"""


def _consigna(raiz: Path, eid: str, tema: str, minutos: int, **extra) -> Path:
    d = raiz / tema / eid
    d.mkdir(parents=True)
    datos = {"id": eid, "titulo": f"Título {eid}", "tema": tema, "bloom": 3, "minutos_estimados": minutos,
             "tags": ["practica"], "pistas": ["Primera pista.", "Segunda pista."],
             "funciones": [{"nombre": "sumar", "retorno": "int", "parametros": "int a, int b", "descripcion": "Suma."}],
             **extra}
    (d / "ejercicio.yaml").write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    (d / "enunciado.md").write_text(ENUNCIADO, encoding="utf-8")
    (d / "solucion.c").write_text("int sumar(int a, int b) { return a + b; }\n", encoding="utf-8")
    (d / f"{eid}.h").write_text("int sumar(int a, int b);\n", encoding="utf-8")
    return d


@pytest.fixture()
def repo_deckard(tmp_path) -> Path:
    """Un repositorio de enunciados: <repo>/banco/<tema>/<id>/."""
    banco = tmp_path / "enunciados" / "banco"
    _consigna(banco, "corta", "funciones", 10)
    _consigna(banco, "media", "funciones", 25)
    _consigna(banco, "larga", "punteros", 50)
    _consigna(banco, "prototipo", "punteros", 15, publicar=False)
    return tmp_path / "enunciados"


def test_carga_consignas_de_un_repositorio_de_enunciados(repo_deckard):
    consignas = cargar_consignas(repo_deckard)
    assert sorted(consignas) == ["deckard:corta", "deckard:larga", "deckard:media"]
    c = consignas["deckard:media"]
    assert c.tipo == "consigna_practica"
    assert c.categoria == "consignas/funciones"
    assert {"practica", "funciones", "bloom:3", "repo:enunciados"} <= set(c.etiquetas)
    assert c.metadata["minutos"] == 25
    assert c.metadata["cabecera_nombre"] == "media.h"
    assert "deckard:prototipo" in cargar_consignas(repo_deckard, incluir_no_publicados=True)


def test_repositorio_externo_detecta_el_tipo(repo_deckard, tmp_path):
    preguntas = tmp_path / "preguntas"
    (preguntas / "sub").mkdir(parents=True)
    (preguntas / "sub" / "teoria.gift").write_text("::P1:: ¿2+2? {=4 ~3 ~5}\n", encoding="utf-8")
    assert detectar_tipo(repo_deckard) == "deckard"
    assert detectar_tipo(preguntas) == "preguntas"

    banco = cargar_repositorio(RepositorioExterno(ruta=str(preguntas), nombre="catedra"))
    assert len(banco) == 1
    assert "repo:catedra" in next(iter(banco.values())).etiquetas

    with pytest.raises(FileNotFoundError):
        cargar_repositorio(RepositorioExterno(ruta=str(tmp_path / "no-existe")))


def test_fuentes_complementarias_locales_y_externas(repo_deckard, tmp_path):
    local = tmp_path / "consignas"
    _consigna(local, "propia", "lazos", 15)
    banco = cargar_fuentes_complementarias([str(local)], [RepositorioExterno(ruta=str(repo_deckard), tipo="deckard")])
    assert "deckard:propia" in banco and "deckard:corta" in banco


def test_myst_a_markdown_deja_markdown_comun():
    md = myst_a_markdown(ENUNCIADO)
    assert ":::" not in md and ":class:" not in md and ":linenos:" not in md
    assert "**Ayuda**" in md
    assert "```c\nint x = 0;\n```" in md


def test_myst_a_markdown_omite_directivas_excluidas():
    md = myst_a_markdown(ENUNCIADO, excluir=["ayuda"])
    assert "Ayuda" not in md and "int x = 0;" not in md
    assert md.startswith("Escribir la función pedida.")
    assert "Contrato de las Funciones" in md


def test_quitar_secciones():
    md = quitar_secciones(ENUNCIADO, ["criterios"])
    assert "Criterios" not in md and "Compila." not in md
    assert "Contrato de las Funciones" in md


def test_presentacion_configurable(repo_deckard):
    c = cargar_consignas(repo_deckard)["deckard:corta"]

    completa = presentar_consigna(c, PresentacionConsigna(
        metadatos=True, funciones=True, cabecera=True, pistas=1, lineas=7, secciones_excluidas=["Contrato"]))
    html = completa.enunciado_html
    assert "<strong>Título corta</strong>" in html
    assert "Tiempo estimado: 10 min" in html
    assert "<table>" in html and "sumar" in html
    assert "corta.h" in html
    assert "Primera pista." in html and "Segunda pista." not in html
    assert "Contrato de las Funciones" not in html
    assert completa.lineas_respuesta == 7
    assert "return a + b" in completa.metadata["solucion_c_clave"]

    minima = presentar_consigna(c, PresentacionConsigna(
        titulo=False, enunciado=False, espacio_respuesta=False, solucion_en_clave=False))
    assert minima.enunciado_html == ""
    assert minima.lineas_respuesta == 0
    assert minima.metadata["solucion_c_clave"] == ""
    assert c.enunciado_html == ""  # el banco no se modifica


def test_la_presentacion_del_pool_cambia_solo_lo_que_declara():
    general = PresentacionConsigna(metadatos=True, lineas=30)
    efectiva = presentacion_efectiva(general, PresentacionConsigna(lineas=5))
    assert efectiva.metadatos is True and efectiva.lineas == 5


def _definicion(pools, presentacion=None) -> DefinicionExamen:
    return DefinicionExamen(
        nombre_examen="P", institucion="I", materia="M",
        configuracion_examen=ConfiguracionExamen(presentacion_consignas=presentacion or PresentacionConsigna()),
        secciones_examen=[SeccionExamen(nombre="S", pools=pools)],
    )


def test_filtros_por_tiempo_y_presupuesto(repo_deckard):
    banco = cargar_consignas(repo_deckard)

    def elegidas(**kw):
        examen = logic.construir_pool_examen(_definicion([PoolConfig(**kw)]), banco)
        return sorted(p.metadata["ejercicio_id"] for p in examen["secciones"][0]["preguntas"])

    assert elegidas(minutos_max=30) == ["corta", "media"]
    assert elegidas(minutos_min=20) == ["larga", "media"]
    assert elegidas(minutos_min=20, minutos_max=30) == ["media"]
    assert elegidas(presupuesto_minutos=40) == ["corta", "media"]
    assert elegidas(categoria="consignas/punteros") == ["larga"]


def test_filtro_de_tiempo_deja_afuera_lo_que_no_tiene_estimacion(repo_deckard, tmp_path):
    gift = tmp_path / "t.gift"
    gift.write_text("::P1:: ¿2+2? {=4 ~3}\n", encoding="utf-8")
    banco = {**logic.cargar_bancos([gift]), **cargar_consignas(repo_deckard)}
    examen = logic.construir_pool_examen(_definicion([PoolConfig(minutos_max=100)]), banco)
    assert all(p.tipo == "consigna_practica" for p in examen["secciones"][0]["preguntas"])


def test_pool_aplica_la_presentacion(repo_deckard):
    banco = cargar_consignas(repo_deckard)
    definicion = _definicion([PoolConfig(preguntas_fijadas=["deckard:corta"], presentacion=PresentacionConsigna(lineas=4))],
                             presentacion=PresentacionConsigna(metadatos=True, lineas=30))
    pregunta = logic.construir_pool_examen(definicion, banco)["secciones"][0]["preguntas"][0]
    assert pregunta.lineas_respuesta == 4
    assert "Tiempo estimado" in pregunta.enunciado_html


def test_html_del_examen_y_de_la_clave(repo_deckard, tmp_path):
    from generador_examenes.generators.html_renderer import HtmlRenderer

    banco = cargar_consignas(repo_deckard)
    definicion = _definicion([PoolConfig(preguntas_fijadas=["deckard:corta"], presentacion=PresentacionConsigna(lineas=6))])
    examen = logic.construir_pool_examen(definicion, banco)
    renderer = HtmlRenderer()
    texto = renderer.renderizar_examen(examen, definicion, tmp_path, 0).read_text(encoding="utf-8")
    assert texto.count('class="renglon"') == 6
    clave = renderer.renderizar_clave(examen, definicion, tmp_path, 0).read_text(encoding="utf-8")
    assert "return" in clave and "sumar" in clave


def test_init_crea_consignas_y_la_definicion_las_usa(tmp_path, monkeypatch):
    from generador_examenes.__main__ import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["generador-examenes", "--init"])
    assert main() == 0
    assert (tmp_path / "consignas" / "sumar-pares" / "ejercicio.yaml").is_file()
    definicion = DefinicionExamen(**yaml.safe_load((tmp_path / "definicion_ejemplo.yaml").read_text(encoding="utf-8")))
    assert definicion.input_consignas == ["consignas"]
    banco = cargar_fuentes_complementarias(definicion.input_consignas, definicion.repositorios_externos)
    seccion = definicion.secciones_examen[1]
    examen = logic.construir_pool_examen(
        definicion.model_copy(update={"secciones_examen": [seccion]}), banco)
    assert examen["secciones"][0]["preguntas"][0].lineas_respuesta == 25


# ---------------------------------------------------------------------------
# Sorteo con la semilla del examen
# ---------------------------------------------------------------------------

@pytest.fixture()
def banco_grande(tmp_path):
    raiz = tmp_path / "muchas"
    for i in range(12):
        _consigna(raiz, f"c{i:02d}", "lazos", 10 + i)
    return cargar_consignas(raiz)


def _elegidas(definicion, banco, semilla=None):
    examen = logic.construir_pool_examen(definicion, banco, semilla)
    return [p.metadata["ejercicio_id"] for s in examen["secciones"] for p in s["preguntas"]]


def test_sorteo_reproducible_y_distinto_con_otra_semilla(banco_grande):
    definicion = _definicion([PoolConfig(cantidad=3)])
    primera = _elegidas(definicion, banco_grande, 7)
    assert primera == _elegidas(definicion, banco_grande, 7)
    otras = {tuple(sorted(_elegidas(definicion, banco_grande, s))) for s in range(10)}
    assert len(otras) > 1
    # sin semilla explícita, la de la definición
    assert _elegidas(definicion, banco_grande) == _elegidas(definicion, banco_grande, definicion.semilla)


def test_sorteo_no_depende_del_orden_de_carga(banco_grande):
    definicion = _definicion([PoolConfig(cantidad=4)])
    invertido = dict(reversed(list(banco_grande.items())))
    assert _elegidas(definicion, banco_grande, 3) == _elegidas(definicion, invertido, 3)


def test_sin_sorteo_entran_las_primeras(banco_grande):
    definicion = _definicion([PoolConfig(cantidad=3)])
    definicion.configuracion_examen.sortear_preguntas = False
    assert _elegidas(definicion, banco_grande, 7) == ["c00", "c01", "c02"]


def test_el_presupuesto_tambien_se_sortea(banco_grande):
    definicion = _definicion([PoolConfig(presupuesto_minutos=40)])
    for semilla in range(5):
        elegidas = _elegidas(definicion, banco_grande, semilla)
        assert sum(banco_grande[f"deckard:{e}"].metadata["minutos"] for e in elegidas) <= 40
    assert len({tuple(sorted(_elegidas(definicion, banco_grande, s))) for s in range(10)}) > 1


# ---------------------------------------------------------------------------
# Comandos con input_consignas y repositorios_externos
# ---------------------------------------------------------------------------

def _alucard(monkeypatch, capsys, args):
    from generador_examenes.__main__ import main

    monkeypatch.setattr(sys, "argv", ["alucard", *args])
    try:
        codigo = main()
    except SystemExit as salida:
        codigo = salida.code
    captura = capsys.readouterr()
    return codigo or 0, captura.out + captura.err


def _yaml_con_fuentes(tmp_path, repo_deckard) -> Path:
    local = tmp_path / "consignas"
    _consigna(local, "propia", "lazos", 15)
    ruta = tmp_path / "examen.yaml"
    ruta.write_text(yaml.safe_dump({
        "nombre_examen": "P", "institucion": "I", "materia": "M",
        "configuracion_examen": {"generar_clave_profesor": True},
        "input_consignas": [str(local)],
        "repositorios_externos": [{"ruta": str(repo_deckard), "nombre": "enunciados"}],
        "secciones_examen": [{"nombre": "Práctica", "pools": [{"tipos": ["consigna_practica"], "cantidad": 2}]}],
    }, allow_unicode=True), encoding="utf-8")
    return ruta


def test_generacion_sin_input_banco(monkeypatch, capsys, tmp_path, repo_deckard):
    definicion = _yaml_con_fuentes(tmp_path, repo_deckard)
    codigo, salida = _alucard(monkeypatch, capsys, ["-d", str(definicion), "-o", str(tmp_path / "out"), "-f", "html"])
    assert codigo == 0, salida
    assert (tmp_path / "out" / "examen_tema_01.html").is_file()


def test_build_y_balance_check_con_las_fuentes_de_la_definicion(monkeypatch, capsys, tmp_path, repo_deckard):
    definicion = _yaml_con_fuentes(tmp_path, repo_deckard)
    codigo, salida = _alucard(monkeypatch, capsys, ["build", "-d", str(definicion), "-f", "html", "-o", str(tmp_path / "b")])
    assert codigo == 0, salida
    assert (tmp_path / "b" / "examen_tema_01.html").is_file()
    codigo, salida = _alucard(monkeypatch, capsys, ["balance-check", "-d", str(definicion), "--json"])
    assert codigo == 0, salida


def test_build_sin_yaml_con_consignas_y_repositorio(monkeypatch, capsys, tmp_path, repo_deckard):
    local = tmp_path / "locales"
    _consigna(local, "propia", "lazos", 15)
    codigo, salida = _alucard(monkeypatch, capsys, [
        "build", "--consignas", str(local), "--repositorio", str(repo_deckard), "-f", "html", "-o", str(tmp_path / "b")])
    assert codigo == 0, salida
    html = (tmp_path / "b" / "examen_tema_01.html").read_text(encoding="utf-8")
    assert "Título propia" in html and "Título corta" in html


def test_build_sin_ninguna_fuente_es_error_de_uso(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    codigo, salida = _alucard(monkeypatch, capsys, ["build"])
    assert codigo == 2, salida


def test_category_tree_con_carpeta_y_definicion(monkeypatch, capsys, tmp_path, repo_deckard):
    import json

    preguntas = tmp_path / "preguntas"
    preguntas.mkdir()
    (preguntas / "t.gift").write_text("::P1:: ¿2+2? {=4 ~3}\n", encoding="utf-8")
    definicion = _yaml_con_fuentes(tmp_path, repo_deckard)
    codigo, salida = _alucard(monkeypatch, capsys, [
        "--category-tree", str(preguntas), "-d", str(definicion), "-o", str(tmp_path / "arbol"), "--json"])
    assert codigo == 0, salida
    datos, _ = json.JSONDecoder().raw_decode(salida[salida.index("{"):])
    assert datos["total_preguntas"] == 1 + 1 + 3  # gift + consigna local + repo (sin el prototipo)


def test_spellcheck_revisa_tambien_las_consignas(monkeypatch, capsys, tmp_path, repo_deckard):
    from generador_examenes.core import languagetool_checker

    revisadas = []

    def analizar(pregunta, **_opciones):
        revisadas.append((pregunta.id, pregunta.enunciado_html))
        return []

    monkeypatch.setattr(languagetool_checker, "analizar_pregunta_languagetool", analizar)
    definicion = _yaml_con_fuentes(tmp_path, repo_deckard)
    codigo, salida = _alucard(monkeypatch, capsys, ["--spellcheck", "-d", str(definicion)])
    assert codigo == 0, salida
    textos = dict(revisadas)
    assert set(textos) == {"deckard:propia", "deckard:corta", "deckard:media", "deckard:larga"}
    assert "Escribir la función pedida" in textos["deckard:corta"]
    assert "Segunda pista." in textos["deckard:corta"]


def test_wizard_fuentes_y_pool_de_consignas():
    from unittest.mock import patch

    from generador_examenes.config.exam_wizard import ExamWizard

    wizard = ExamWizard()
    with patch("generador_examenes.config.exam_wizard.Prompt.ask") as ask, \
         patch("generador_examenes.config.exam_wizard.Confirm.ask") as confirm, \
         patch("generador_examenes.config.exam_wizard.console"):
        ask.side_effect = ["bancos/teoria.gift", "consignas", "~/dev/tools/enunciados", "deckard", "enunciados"]
        confirm.side_effect = [True, False]
        wizard._configurar_fuentes()
    assert wizard.config["input_banco"] == ["bancos/teoria.gift"]
    assert wizard.config["input_consignas"] == ["consignas"]
    assert wizard.config["repositorios_externos"] == [
        {"ruta": "~/dev/tools/enunciados", "tipo": "deckard", "nombre": "enunciados"}]

    with patch("generador_examenes.config.exam_wizard.Prompt.ask") as ask, \
         patch("generador_examenes.config.exam_wizard.IntPrompt.ask") as int_ask, \
         patch("generador_examenes.config.exam_wizard.Confirm.ask") as confirm, \
         patch("generador_examenes.config.exam_wizard.console"):
        ask.side_effect = ["consignas", "punteros", "advertir"]
        confirm.return_value = True
        int_ask.side_effect = [15, 40, 60, 25, 2]
        pool = wizard._configurar_pool()
    assert pool == {
        "tipos": ["consigna_practica"], "categoria": "consignas/punteros", "minutos_min": 15, "minutos_max": 40,
        "presupuesto_minutos": 60, "presentacion": {"lineas": 25}, "cantidad": 2, "accion_si_insuficiente": "advertir",
    }
    PoolConfig(**pool)
    assert "min:15-40" in wizard._describir_pool(pool)
