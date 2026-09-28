"""alucarD funciona sin myst-tools ni daedalus instalados (N-ECO-01).

Antes, sin esas herramientas en el entorno, alucarD las buscaba con
sys.path.insert en las carpetas hermanas del monorepo: instalado desde git
la integración se perdía sin aviso. Ahora llegan con los extras
`languagetool` y `ecosistema`; sin ellos el CLI arranca, la síntesis compila
con gcc directo y --spellcheck explica cómo instalar el extra.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import generador_examenes

BLOQUEAR = (
    "import sys\n"
    "for m in ('myst_tools', 'myst_tools.languagetool_checker', 'daedalus', 'daedalus.core', "
    "'daedalus.core.compiler'):\n"
    "    sys.modules[m] = None\n"
)


def _correr(codigo: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", BLOQUEAR + codigo],
        capture_output=True, text=True, timeout=120, cwd=cwd,
    )


def test_ningun_modulo_busca_carpetas_hermanas():
    paquete = Path(generador_examenes.__file__).parent
    ocultos = [str(p.relative_to(paquete)) for p in paquete.rglob("*.py")
               if "sys.path.insert" in p.read_text(encoding="utf-8")]
    assert ocultos == []


def test_la_ayuda_funciona_sin_myst_tools_ni_daedalus():
    resultado = _correr(
        "sys.argv = ['alucard', '--help']\n"
        "from generador_examenes.__main__ import main\n"
        "main()\n"
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "--spellcheck" in resultado.stdout


def test_spellcheck_sin_myst_tools_explica_el_extra(tmp_path):
    banco = Path(__file__).parent / "bancos_ejemplo" / "banco_test.txt"
    resultado = _correr(
        f"sys.argv = ['alucard', '--spellcheck', '-i', {str(banco)!r}]\n"
        "from generador_examenes.__main__ import main\n"
        "sys.exit(main())\n",
        cwd=tmp_path,
    )
    salida = resultado.stdout + resultado.stderr
    assert resultado.returncode == 1
    assert "extra languagetool" in salida
    assert "Traceback" not in salida


@pytest.mark.skipif(shutil.which("gcc") is None, reason="requiere gcc en el PATH")
def test_la_sintesis_sin_daedalus_compila_con_gcc():
    resultado = _correr(
        "from generador_examenes.synthesizer import compilar_y_ejecutar\n"
        "ok, salida = compilar_y_ejecutar('#include <stdio.h>\\nint main(void) { printf(\"%d\", 6 * 7); return 0; }\\n')\n"
        "print(ok, salida)\n"
    )
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "True 42"
