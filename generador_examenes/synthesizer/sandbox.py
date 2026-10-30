"""Compilación y ejecución de snippets C en un directorio temporal.

Tres formas de verificar la respuesta de una plantilla:

- `compilar_y_ejecutar`: la salida del programa (delega en daedalus si está).
- `diagnosticos`: los avisos de gcc con `-Wall -Wextra -fanalyzer`, para los
  programas con comportamiento indefinido (no se ejecutan).
- `memoria_sin_liberar`: los bytes y bloques que quedan sin liberar al terminar,
  con `malloc`/`calloc`/`realloc`/`free` envueltos (no hace falta valgrind ni ASan).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

GCC = shutil.which("gcc")

_FLAGS = ["-std=c11", "-Wall", "-Wextra", "-O0"]

# Envoltorio de la memoria dinámica: se incluye con -include antes del programa.
_ARNES_MEMORIA = r"""
#include <stdio.h>
#include <stdlib.h>
#define ALUCARD_MAX 4096
static void *alucard_bloques[ALUCARD_MAX];
static size_t alucard_tamanos[ALUCARD_MAX];
static void alucard_registrar(void *p, size_t n) {
    for (size_t i = 0; p != NULL && i < ALUCARD_MAX; i++) {
        if (alucard_bloques[i] == NULL) { alucard_bloques[i] = p; alucard_tamanos[i] = n; return; }
    }
}
static size_t alucard_quitar(void *p) {
    for (size_t i = 0; p != NULL && i < ALUCARD_MAX; i++) {
        if (alucard_bloques[i] == p) { alucard_bloques[i] = NULL; return alucard_tamanos[i]; }
    }
    return 0;
}
static void alucard_informe(void) {
    size_t bytes = 0, bloques = 0;
    for (size_t i = 0; i < ALUCARD_MAX; i++) {
        if (alucard_bloques[i] != NULL) { bytes += alucard_tamanos[i]; bloques++; }
    }
    fprintf(stderr, "ALUCARD_MEMORIA %zu %zu\n", bytes, bloques);
}
__attribute__((constructor)) static void alucard_inicio(void) { atexit(alucard_informe); }
__attribute__((unused)) static void *alucard_malloc(size_t n) {
    void *p = malloc(n); alucard_registrar(p, n); return p;
}
__attribute__((unused)) static void *alucard_calloc(size_t c, size_t n) {
    void *p = calloc(c, n); alucard_registrar(p, c * n); return p;
}
__attribute__((unused)) static void *alucard_realloc(void *viejo, size_t n) {
    size_t anterior = alucard_quitar(viejo);
    void *p = realloc(viejo, n);
    if (p != NULL) { alucard_registrar(p, n); } else { alucard_registrar(viejo, anterior); }
    return p;
}
__attribute__((unused)) static void alucard_free(void *p) { alucard_quitar(p); free(p); }
#define malloc(n) alucard_malloc(n)
#define calloc(c, n) alucard_calloc(c, n)
#define realloc(p, n) alucard_realloc(p, n)
#define free(p) alucard_free(p)
"""


def _gcc() -> str:
    if GCC is None:
        raise RuntimeError("gcc no está disponible en el PATH")
    return GCC


def _compilar_fuente(fuente: Path, binario: Path, timeout: int) -> tuple[bool, str]:
    """Compila delegando en daedalus (extra `ecosistema`) con fallback a GCC."""
    try:
        from daedalus.core.compiler import compilar_archivos
    except ImportError:
        pass  # sin el extra `ecosistema`: gcc directo
    else:
        res = compilar_archivos([fuente], binario_salida=binario, timeout=timeout)
        if not res.exito:
            return False, f"compilación falló:\n{res.stderr_crudo.strip()}"
        return True, ""

    compilar = subprocess.run(
        [_gcc(), *_FLAGS, "-Werror", "-o", str(binario), str(fuente)],
        capture_output=True, text=True, check=False, timeout=timeout,
    )
    if compilar.returncode != 0:
        return False, f"compilación falló:\n{compilar.stderr.strip()}"
    return True, ""


def compilar_y_ejecutar(codigo: str, timeout_compilado: int = 20,
                        timeout_ejecucion: int = 5,
                        flags_extra: list[str] | None = None) -> tuple[bool, str]:
    """Compila y ejecuta un snippet C en un directorio temporal.

    Devuelve ``(True, stdout)`` si el programa termina con éxito; ``False`` y
    el diagnóstico en caso contrario. Sin `flags_extra` delega la compilación
    en daedalus; con ellos (p. ej. para callar un aviso que es justamente lo que
    la pregunta enseña) compila con gcc directo.
    """
    with tempfile.TemporaryDirectory(prefix="daedalus-") as tmp:
        fuente = Path(tmp) / "snippet.c"
        binario = Path(tmp) / "snippet.bin"
        fuente.write_text(codigo, encoding="utf-8")

        if flags_extra is None:
            ok, err = _compilar_fuente(fuente, binario, timeout_compilado)
        else:
            res = subprocess.run(
                [_gcc(), *_FLAGS, "-Werror", *flags_extra, "-o", str(binario), str(fuente)],
                capture_output=True, text=True, check=False, timeout=timeout_compilado,
            )
            ok, err = res.returncode == 0, f"compilación falló:\n{res.stderr.strip()}"
        if not ok:
            return False, err

        ejecutar = subprocess.run(
            [str(binario)],
            capture_output=True, text=True, check=False, timeout=timeout_ejecucion,
        )
        if ejecutar.returncode != 0:
            return False, f"ejecución falló (rc={ejecutar.returncode}):\n{ejecutar.stderr.strip()}"

        return True, ejecutar.stdout.rstrip("\n")


def diagnosticos(codigo: str, timeout: int = 60) -> set[str]:
    """Los avisos de gcc (`-Wall -Wextra -fanalyzer`) del snippet, por nombre: {"uninitialized", "analyzer-use-after-free"…}.

    El programa no se ejecuta: sirve para verificar plantillas con comportamiento indefinido.
    """
    with tempfile.TemporaryDirectory(prefix="daedalus-") as tmp:
        fuente = Path(tmp) / "snippet.c"
        fuente.write_text(codigo, encoding="utf-8")
        res = subprocess.run(
            [_gcc(), *_FLAGS, "-fanalyzer", "-c", "-o", str(Path(tmp) / "snippet.o"), str(fuente)],
            capture_output=True, text=True, check=False, timeout=timeout,
        )
    if "unrecognized command-line option '-fanalyzer'" in res.stderr:
        raise RuntimeError("estas plantillas necesitan gcc 10 o posterior (-fanalyzer)")
    if res.returncode != 0 and "error:" in res.stderr:
        raise RuntimeError(f"compilación falló:\n{res.stderr.strip()}")
    return set(re.findall(r"\[-W([a-z-]+)(?:=\d*)?\]", res.stderr))


def memoria_sin_liberar(codigo: str, timeout_compilado: int = 20,
                        timeout_ejecucion: int = 5) -> tuple[str, int, int]:
    """Ejecuta el snippet contando la memoria dinámica: ``(stdout, bytes sin liberar, bloques sin liberar)``."""
    with tempfile.TemporaryDirectory(prefix="daedalus-") as tmp:
        fuente = Path(tmp) / "snippet.c"
        arnes = Path(tmp) / "alucard_memoria.h"
        binario = Path(tmp) / "snippet.bin"
        fuente.write_text(codigo, encoding="utf-8")
        arnes.write_text(_ARNES_MEMORIA, encoding="utf-8")
        res = subprocess.run(
            [_gcc(), *_FLAGS, "-Werror", "-include", str(arnes), "-o", str(binario), str(fuente)],
            capture_output=True, text=True, check=False, timeout=timeout_compilado,
        )
        if res.returncode != 0:
            raise RuntimeError(f"compilación falló:\n{res.stderr.strip()}")
        ejecutar = subprocess.run([str(binario)], capture_output=True, text=True, check=False, timeout=timeout_ejecucion)
    if ejecutar.returncode != 0:
        raise RuntimeError(f"ejecución falló (rc={ejecutar.returncode}):\n{ejecutar.stderr.strip()}")
    m = re.search(r"ALUCARD_MEMORIA (\d+) (\d+)", ejecutar.stderr)
    if m is None:
        raise RuntimeError("no se obtuvo el informe de memoria del programa")
    return ejecutar.stdout.rstrip("\n"), int(m.group(1)), int(m.group(2))
