"""Formato final de un banco sintetizado con voight (el dueño del formato de los bancos del ecosistema).

Después de escribir el banco se corren, en orden:

1. `voight fix code-indent`: la indentación del código con · (un punto por espacio);
2. `voight fix code-chars --to-fullwidth`: los símbolos del código en ancho completo (＃, （, ｛…),
   para que GIFT no interprete `{`, `}`, `=`, `~`, `#` ni `:` del código;
3. `voight fix format`: el formato de GIFT o Moodle XML de la cátedra.

alucard lee el resultado (normaliza el ancho completo y las marcas · y ↵ al mostrar la pregunta).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

PASOS = (
    ("fix", "code-indent"),
    ("fix", "code-chars", "--to-fullwidth"),
    ("fix", "format"),
)
INSTALAR = "uv tool install git+https://github.com/INGCOM-UNRN/voight"


def formatear(ruta: Path, voight: Optional[str] = None, timeout: int = 120) -> Optional[str]:
    """Corre los tres pasos sobre `ruta`. Devuelve None si salió bien, o por qué no."""
    ejecutable = voight or shutil.which("voight")
    if ejecutable is None:
        return f"voight no está instalado: el banco queda sin su formato ({INSTALAR})"
    for paso in PASOS:
        comando = [ejecutable, *paso, str(ruta)]
        try:
            res = subprocess.run(comando, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return f"`voight {' '.join(paso)}` no terminó en {timeout} s"
        except OSError as e:
            return f"no se pudo correr voight: {e}"
        if res.returncode != 0:
            detalle = (res.stderr or res.stdout).strip().splitlines()[-1:] or ["sin detalle"]
            return f"`voight {' '.join(paso)}` falló: {detalle[0]}"
    return None
