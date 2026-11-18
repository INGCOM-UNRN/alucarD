"""Caché de los bancos ya leídos."""

import logging

import pytest

from generador_examenes.core import cache_bancos
from generador_examenes.core.logic import cargar_bancos


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

