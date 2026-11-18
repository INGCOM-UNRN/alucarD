"""Categorías y etiquetas por carpeta (`banco.toml`) y caché de los bancos ya leídos."""

import logging

import pytest

from generador_examenes.core import cache_bancos
from generador_examenes.core.carpetas_banco import categoria
from generador_examenes.core.logic import candidatas_pool, cargar_bancos
from generador_examenes.core.models import PoolConfig


def escribir(raiz, archivos):
    for ruta, texto in archivos.items():
        archivo = raiz / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(texto, encoding="utf-8")


@pytest.fixture
def arbol(tmp_path):
    raiz = tmp_path / "bancos"
    escribir(raiz, {
        "punteros/teoria.gift": "::a::Texto {T}\n",
        "punteros/arreglos/practica.gift": "$CATEGORY: $course$/Top/Repaso\n\n::b::Texto {T}\n",
        "listas/teoria.gift": "// [tag, facil]\n::c::Texto {T}\n",
        "suelto.gift": "::d::Texto {T}\n",
    })
    return raiz


def por_nombre(banco):
    return {p.nombre: p for p in banco.values()}


# --- banco.toml -----------------------------------------------------------------------------------

def test_sin_banco_toml_las_carpetas_no_cambian_nada(arbol):
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "General" and preguntas["a"].etiquetas == []
    assert preguntas["b"].categoria == "$course$/Top/Repaso"


def test_categoria_carpeta_y_etiquetas(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\netiquetas = true\n'})
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "punteros" and preguntas["a"].etiquetas == ["punteros"]
    assert preguntas["b"].categoria == "punteros/arreglos"
    assert preguntas["b"].etiquetas == ["punteros", "arreglos"]
    assert preguntas["c"].etiquetas == ["facil", "listas"]
    # En la raíz no hay carpetas: queda lo del archivo.
    assert preguntas["d"].categoria == "General" and preguntas["d"].etiquetas == []


def test_prefijo_antepone_la_carpeta_sin_el_contexto_de_moodle(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "prefijo"\n'})
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "punteros"
    assert preguntas["b"].categoria == "punteros/arreglos/Repaso"


def test_si_falta_respeta_la_categoria_del_archivo(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "si_falta"\n'})
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "punteros"
    assert preguntas["b"].categoria == "$course$/Top/Repaso"


def test_incluir_archivo_suma_el_nombre_del_archivo(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\netiquetas = true\nincluir_archivo = true\n'})
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "punteros/teoria"
    assert preguntas["d"].categoria == "suelto" and preguntas["d"].etiquetas == ["suelto"]


def test_un_banco_toml_mas_adentro_cambia_solo_su_subarbol(arbol):
    escribir(arbol, {
        "banco.toml": 'categoria = "carpeta"\nagregar_etiquetas = ["parcial1"]\n',
        "punteros/arreglos/banco.toml": 'categoria = "archivo"\netiquetas = true\n',
    })
    preguntas = por_nombre(cargar_bancos([arbol]))
    assert preguntas["a"].categoria == "punteros" and preguntas["a"].etiquetas == ["parcial1"]
    assert preguntas["b"].categoria == "$course$/Top/Repaso"
    assert preguntas["b"].etiquetas == ["punteros", "arreglos", "parcial1"]


def test_los_pools_filtran_por_las_categorias_y_etiquetas_de_carpeta(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\netiquetas = true\n'})
    banco = cargar_bancos([arbol])
    por_categoria = PoolConfig(nombre="p", cantidad=1, puntos_por_pregunta=1, categoria="punteros")
    por_etiqueta = PoolConfig(nombre="q", cantidad=1, puntos_por_pregunta=1, etiquetas=["arreglos"])
    assert {p.nombre for p in candidatas_pool(por_categoria, banco)} == {"a", "b"}
    assert {p.nombre for p in candidatas_pool(por_etiqueta, banco)} == {"b"}


def test_un_archivo_nombrado_directamente_no_usa_banco_toml(arbol):
    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\netiquetas = true\n'})
    pregunta, = cargar_bancos([arbol / "punteros" / "teoria.gift"]).values()
    assert pregunta.categoria == "General" and pregunta.etiquetas == []


@pytest.mark.parametrize("contenido, mensaje", [
    ('categoria = "otra"\n', "categoria es"),
    ("etiquetas = 1\n", "etiquetas es true o false"),
    ('agregar_etiquetas = "x"\n', "agregar_etiquetas es una lista"),
    ("categorias = true\n", "claves desconocidas: categorias"),
    ("categoria = \n", "banco.toml"),
])
def test_un_banco_toml_mal_escrito_es_un_error_con_su_nombre(arbol, contenido, mensaje):
    escribir(arbol, {"punteros/banco.toml": contenido})
    with pytest.raises(ValueError, match=mensaje):
        cargar_bancos([arbol])


@pytest.mark.parametrize("propia, carpetas, modo, esperada", [
    ("Punteros", ["u1"], "archivo", "Punteros"),
    ("Punteros", [], "carpeta", "Punteros"),
    ("$course$/Default/Punteros", ["u1"], "prefijo", "u1/Punteros"),
    ("", ["u1", "x"], "si_falta", "u1/x"),
])
def test_categoria(propia, carpetas, modo, esperada):
    assert categoria(propia, carpetas, modo) == esperada


def test_un_repositorio_externo_de_preguntas_usa_su_banco_toml(arbol):
    from generador_examenes.core.consignas import cargar_repositorio
    from generador_examenes.core.models import RepositorioExterno

    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\n'})
    preguntas = por_nombre(cargar_repositorio(RepositorioExterno(ruta=str(arbol), nombre="cat")))
    assert preguntas["b"].categoria == "punteros/arreglos"
    assert preguntas["b"].fuente_banco == "punteros/arreglos/practica.gift"
    assert "repo:cat" in preguntas["b"].etiquetas


# --- caché ----------------------------------------------------------------------------------------

def contar_parseos(monkeypatch):
    from generador_examenes.parsers.gift_parser import GiftParser

    llamadas = []
    original = GiftParser.parse

    def parse(self, ruta):
        llamadas.append(ruta.name)
        return original(self, ruta)

    monkeypatch.setattr(GiftParser, "parse", parse)
    return llamadas


def test_un_banco_sin_cambios_sale_del_cache(arbol, monkeypatch):
    llamadas = contar_parseos(monkeypatch)
    primera = cargar_bancos([arbol])
    assert len(llamadas) == 4
    segunda = cargar_bancos([arbol])
    assert len(llamadas) == 4
    assert {k: v.model_dump() for k, v in primera.items()} == {k: v.model_dump() for k, v in segunda.items()}


def test_editar_el_banco_lo_vuelve_a_parsear(arbol, monkeypatch):
    llamadas = contar_parseos(monkeypatch)
    cargar_bancos([arbol])
    escribir(arbol, {"suelto.gift": "::d::Otro texto {T}\n"})
    banco = cargar_bancos([arbol])
    assert llamadas.count("suelto.gift") == 2
    assert "Otro texto" in por_nombre(banco)["d"].enunciado_html


def test_las_reglas_de_carpeta_no_quedan_en_el_cache(arbol):
    cargar_bancos([arbol])
    escribir(arbol, {"banco.toml": 'categoria = "carpeta"\n'})
    assert por_nombre(cargar_bancos([arbol]))["a"].categoria == "punteros"
    (arbol / "banco.toml").unlink()
    assert por_nombre(cargar_bancos([arbol]))["a"].categoria == "General"


def test_el_cache_repite_los_avisos_del_parser(tmp_path, monkeypatch, caplog):
    banco = tmp_path / "roto.gift"
    banco.write_text("::a::Sin opciones\n", encoding="utf-8")
    llamadas = contar_parseos(monkeypatch)
    for _ in range(2):
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            assert cargar_bancos([banco]) == {}
        assert "omitida" in caplog.text
    assert len(llamadas) == 1


def test_sin_cache_siempre_parsea(arbol, monkeypatch):
    monkeypatch.setenv("ALUCARD_SIN_CACHE", "1")
    llamadas = contar_parseos(monkeypatch)
    cargar_bancos([arbol])
    cargar_bancos([arbol])
    assert len(llamadas) == 8
    assert not list(cache_bancos.carpeta().glob("*.json"))


def test_una_entrada_ilegible_se_vuelve_a_parsear(arbol, monkeypatch):
    cargar_bancos([arbol])
    for entrada in cache_bancos.carpeta().glob("*.json"):
        entrada.write_text("{roto", encoding="utf-8")
    llamadas = contar_parseos(monkeypatch)
    assert len(cargar_bancos([arbol])) == 4
    assert len(llamadas) == 4


# --- ids repetidos --------------------------------------------------------------------------------

@pytest.fixture
def repetidos_en_carpetas(tmp_path):
    """Dos `teoria.gift` con la misma primera pregunta: el id (gift_1_a) choca."""
    raiz = tmp_path / "bancos"
    escribir(raiz, {"u1/teoria.gift": "::a::Uno {T}\n", "u2/teoria.gift": "::a::Dos {T}\n\n::b::Otra {F}\n"})
    return raiz


def test_los_ids_repetidos_quedan_anotados(repetidos_en_carpetas, caplog):
    repetidos = []
    with caplog.at_level(logging.WARNING):
        banco = cargar_bancos([repetidos_en_carpetas], repetidos)
    r, = repetidos
    assert r.id == "gift_1_a" and r.nombre == "a"
    assert r.queda.endswith("u2/teoria.gift") and r.descartada.endswith("u1/teoria.gift")
    assert "Dos" in banco["gift_1_a"].enunciado_html
    assert "id repetido gift_1_a" in caplog.text and "se descarta la de" in caplog.text


def test_los_ids_repetidos_se_anotan_aunque_salgan_del_cache(repetidos_en_carpetas):
    cargar_bancos([repetidos_en_carpetas])
    repetidos = []
    cargar_bancos([repetidos_en_carpetas], repetidos)
    assert [r.id for r in repetidos] == ["gift_1_a"]


def _definicion(tmp_path, banco):
    definicion = tmp_path / "def.yaml"
    definicion.write_text(f"""nombre_examen: "P"
institucion: "I"
materia: "M"
configuracion_examen:
  generar_clave_profesor: false
input_banco: ["{banco}"]
secciones_examen:
  - nombre: "A"
    pools:
      - cantidad: 1
""", encoding="utf-8")
    return definicion


def test_generar_avisa_los_ids_repetidos_y_los_deja_en_el_informe(repetidos_en_carpetas, tmp_path, monkeypatch, capsys):
    import sys

    from generador_examenes.__main__ import main

    salida = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(_definicion(tmp_path, repetidos_en_carpetas)),
                                      "-o", str(salida)])
    assert main() == 0                      # un aviso, no un error
    err = capsys.readouterr().err
    assert "Revisá antes de imprimir (1):" in err and "id repetido gift_1_a" in err
    informe = (salida / "informe.md").read_text(encoding="utf-8")
    assert "## Ids repetidos" in informe
    fila = next(linea for linea in informe.splitlines() if linea.startswith("| gift_1_a |"))
    assert "u2/teoria.gift" in fila and "u1/teoria.gift" in fila


def test_el_informe_no_tiene_la_seccion_sin_repetidos(arbol, tmp_path, monkeypatch):
    import sys

    from generador_examenes.__main__ import main

    salida = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["alucard", "generar", "-d", str(_definicion(tmp_path, arbol)), "-o", str(salida)])
    assert main() == 0
    assert "Ids repetidos" not in (salida / "informe.md").read_text(encoding="utf-8")


def test_el_inventario_muestra_los_ids_repetidos(repetidos_en_carpetas, monkeypatch, capsys):
    import sys

    from generador_examenes.__main__ import main

    monkeypatch.setattr(sys, "argv", ["alucard", "categorias", "--resumen", str(repetidos_en_carpetas)])
    main()
    out = capsys.readouterr().out
    assert "! Ids repetidos (1)" in out and "id repetido gift_1_a" in out
