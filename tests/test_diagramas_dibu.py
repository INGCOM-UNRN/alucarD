"""Integración con dibu: tipos y themes que informa el binario, theme activo de un examen y la
caché de bancos, que depende de cómo se dibujan los diagramas."""
from __future__ import annotations

import contextvars
from pathlib import Path

import pytest

from generador_examenes import diagramas
from generador_examenes.core import cache_bancos
from generador_examenes.core.markdown_utils import markdown_to_html

FONDO_OSCURO = 'fill="#0f172a"'
pytestmark = pytest.mark.skipif(diagramas.binario_dibu() is None, reason="sin binario dibu")


def _en_contexto(funcion):
    """Corre `funcion` en un contexto propio, como `alucard generar`, para no fijar el theme global."""
    return contextvars.copy_context().run(funcion)


def test_tipos_y_themes_salen_del_binario():
    tipos = diagramas.tipos_disponibles()
    assert len(tipos) >= 70 and {"karnaugh", "cpu_scheduling", "distribution", "circuit"} <= set(tipos)
    assert set(diagramas.TIPOS) <= set(tipos)
    assert diagramas.temas_disponibles() == ("ink", "color", "high-contrast", "dark")


@pytest.mark.parametrize("bloque", [
    {"type": "truth_table", "expr": "A·B + C"},
    {"type": "karnaugh", "vars": ["A", "B", "C"], "minterms": [1, 3, 5, 7]},
    {"type": "cpu_scheduling", "algorithm": "rr", "quantum": 2,
     "processes": [{"name": "A", "burst": 3}, {"name": "B", "arrival": 1, "burst": 2}]},
    {"type": "subnetting", "network": "10.0.0.0/24", "count": 4},
    {"type": "distribution", "dist": "normal", "interval": [-1, 1]},
    {"type": "circuit", "source": "V = 10", "network": {"series": ["R1 = 10", "R2 = 20"]}},
])
def test_tipos_nuevos_se_dibujan(bloque):
    svg = diagramas.renderizar(bloque)
    assert svg.startswith("<svg") and 'class="estructura"' in svg


def test_theme_activo_y_prioridades():
    bloque = {"type": "array", "values": [1, 2]}

    def con_tema():
        diagramas.fijar_tema("dark")
        oscuro = diagramas.renderizar(bloque)
        explicito = diagramas.renderizar(bloque, theme="ink")           # el de la llamada manda
        propio = diagramas.renderizar({**bloque, "inkSaver": True})      # y el del bloque, sobre todo
        return oscuro, explicito, propio

    oscuro, explicito, propio = _en_contexto(con_tema)
    assert FONDO_OSCURO in oscuro and FONDO_OSCURO not in explicito and FONDO_OSCURO not in propio
    # Fuera del contexto, el theme por omisión sigue siendo el de tinta.
    assert diagramas.tema_activo() is None
    assert FONDO_OSCURO not in diagramas.renderizar(bloque)


def test_theme_desde_archivo(tmp_path: Path):
    (tmp_path / "tema.yaml").write_text('extends: ink\ncolors:\n  background: "#fafaf9"\n', encoding="utf-8")
    tema = diagramas.resolver_tema("tema.yaml", tmp_path)
    assert tema == {"extends": "ink", "colors": {"background": "#fafaf9"}}
    assert 'fill="#fafaf9"' in diagramas.renderizar({"type": "array", "values": [1]}, theme=tema)
    assert diagramas.resolver_tema("dark") == "dark"
    with pytest.raises(diagramas.ErrorDiagrama):
        diagramas.resolver_tema("no-existe.yaml", tmp_path)


def test_markdown_con_theme_y_tipos_nuevos():
    texto = "¿Cuántas burbujas hay?\n\n```estructura\ntype: pipeline\ninstructions:\n  - lw $t0, 0($s0)\n  - add $t1, $t0, $t2\n```\n"

    def html_oscuro():
        diagramas.fijar_tema("dark")
        return markdown_to_html(texto)

    html = _en_contexto(html_oscuro)
    assert "<svg" in html and FONDO_OSCURO in html and "estructura-error" not in html


def test_cache_de_bancos_depende_del_theme(tmp_path: Path):
    banco = tmp_path / "b.gift"
    banco.write_text("::p::¿Sí?{T}\n", encoding="utf-8")
    sin_tema = cache_bancos.clave(banco)

    def con_tema():
        diagramas.fijar_tema("high-contrast")
        return cache_bancos.clave(banco)

    assert _en_contexto(con_tema) != sin_tema
    assert cache_bancos.clave(banco) == sin_tema
    assert diagramas.huella_dibu() in diagramas.huella_render()


@pytest.mark.parametrize("estilo, esperado, ausente", [
    # tema_diagramas elige el theme de dibu.
    ({"tema_diagramas": "dark"}, FONDO_OSCURO, None),
    # Con alto contraste se dibuja con high-contrast: también los rellenos claros (#f8fafc, que el
    # reemplazo de grises no toca) quedan en blanco.
    ({"alto_contraste": True}, 'fill="#ffffff"', "#f8fafc"),
])
def test_generar_usa_el_theme_del_estilo(tmp_path: Path, estilo, esperado, ausente):
    import subprocess
    import sys

    import yaml

    banco = tmp_path / "banco.gift"
    banco.write_text(
        "// [tag, t]\n::p1::[markdown]¿Qué función es?\n```estructura\ntype: truth_table\nexpr: A + B\n```\n"
        "{\n=OR\n~AND\n}\n", encoding="utf-8")
    definicion = {
        "nombre_examen": "P", "institucion": "I", "materia": "M", "fecha": "2026-12-01",
        "input_banco": [str(banco)], "output_dir": str(tmp_path / "out"), "formato": ["html"],
        "estilo": estilo, "configuracion_examen": {},
        "secciones_examen": [{"nombre": "S", "pools": [{"etiquetas": ["t"], "cantidad": 1}]}],
    }
    (tmp_path / "def.yaml").write_text(yaml.safe_dump(definicion, allow_unicode=True), encoding="utf-8")
    env = {"ALUCARD_SIN_CACHE": "1", "HOME": str(tmp_path), "PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin"}
    proc = subprocess.run([sys.executable, "-m", "generador_examenes", "generar", "-d", str(tmp_path / "def.yaml")],
                          capture_output=True, text=True, cwd=tmp_path, env=env, timeout=300)
    assert proc.returncode == 0, proc.stderr[-2000:]
    html = next((tmp_path / "out").rglob("examen_tema_01.html")).read_text(encoding="utf-8")
    assert "<svg" in html and esperado in html
    if ausente:
        assert ausente not in html


def test_leer_bloques_entiende_blank_de_dibu():
    """`!blank X` llega a dibu como "X.blank": lo usa para calcular y lo dibuja en blanco."""
    from generador_examenes.diagramas import leer_bloques

    b = leer_bloques(
        "type: heap\nvalues: [50, !blank 40, !blank \"007\", x.blank]\nextra: !blank [1, true]\nobj: !blank {a: 2}"
    )[0]
    assert b["values"] == [50, "40.blank", "007.blank", "x.blank"]
    assert b["extra"] == ["1.blank", "true.blank"]
    assert b["obj"] == {"a": "2.blank"}
