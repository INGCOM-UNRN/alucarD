"""Diagnóstico de dependencias del sistema para alucarD (ALUCARD-D0401).

Verifica los binarios y módulos de Python de los que depende alucarD en
tiempo de ejecución: ``gcc`` (compilación del sintetizador de preguntas de
C), Typst (binario o módulo `typst`, el único motor de PDF: sin él no se
genera ninguno), pypdf (empaquetado para imprenta) y, de forma informativa,
la conectividad con la API pública de LanguageTool.

Sigue el contrato de LINEAMIENTOS §3.3: la lógica vive en `core/` sin
depender de `typer` ni escribir directamente a stdout, aceptando un
objeto `rich.console.Console` opcional para integrarse con la CLI.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


def chequear_binario(comando: str, args_version: str = "--version") -> Dict[str, Any]:
    """Verifica si un binario del sistema está disponible en el venv o en el PATH."""
    import os
    import sys
    from pathlib import Path

    junto_python = Path(sys.executable).parent / (f"{comando}.exe" if os.name == "nt" else comando)
    if junto_python.is_file() and os.access(junto_python, os.X_OK):
        ruta = str(junto_python)
    else:
        ruta = shutil.which(comando)
    if not ruta:
        return {"disponible": False, "version": None, "ruta": None}
    try:
        res = subprocess.run(
            [ruta, args_version], capture_output=True, text=True, timeout=5
        )
        salida = (res.stdout or res.stderr).strip().splitlines()
        version = salida[0] if salida else "Detectada"
    except Exception:
        version = "Detectada"
    return {"disponible": True, "version": version, "ruta": ruta}


def chequear_modulo_python(nombre_modulo: str) -> Dict[str, Any]:
    """Verifica si un módulo de Python está instalado, sin importarlo."""
    spec = importlib.util.find_spec(nombre_modulo)
    if spec is None:
        return {"disponible": False, "version": None, "importable": False}
    try:
        modulo = importlib.import_module(nombre_modulo)
        return {"disponible": True, "version": getattr(modulo, "__version__", "Detectado"), "importable": True}
    except Exception:
        return {"disponible": True, "version": "Detectado (no se pudo importar)", "importable": False}


def chequear_conectividad_languagetool(timeout: float = 3.0) -> Dict[str, Any]:
    """Verifica de forma informativa el acceso a la API pública de LanguageTool.

    No es un requisito bloqueante: `--spellcheck` degrada con un mensaje
    de error si el servicio no está disponible, pero no impide el resto
    de las funcionalidades de alucarD.
    """
    url = "https://api.languagetool.org/v2/languages"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return {"disponible": resp.status == 200, "detalle": f"HTTP {resp.status}"}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"disponible": False, "detalle": str(exc)}


def diagnosticar() -> List[Dict[str, Any]]:
    """Estado de cada requisito (sin imprimir nada), en el formato común de doctor."""
    chequeos: List[Dict[str, Any]] = []

    gcc_info = chequear_binario("gcc")
    chequeos.append({
        "nombre": "gcc", "requerido": True, "ok": gcc_info["disponible"],
        "detalle": f"{gcc_info['version']} ({gcc_info['ruta']})" if gcc_info["disponible"] else "No encontrado en $PATH",
        "proposito": "Compilación del sintetizador de preguntas de C (alucard sintetizar)",
        "sugerencia": "" if gcc_info["disponible"] else "sudo apt install build-essential  (Fedora: sudo dnf install gcc)",
    })

    import os
    dibu_cmd = os.environ.get("ALUCARD_DIBU") or os.environ.get("DIBU_BIN") or "dibu"
    dibu_info = chequear_binario(dibu_cmd)
    chequeos.append({
        "nombre": "dibu", "requerido": True, "ok": dibu_info["disponible"],
        "detalle": f"{dibu_info['version']} ({dibu_info['ruta']})" if dibu_info["disponible"] else "No encontrado en $PATH",
        "proposito": "Render de diagramas SVG de los bloques ```estructura / ```statics",
        "sugerencia": "" if dibu_info["disponible"] else "uv sync  (o) ALUCARD_DIBU / DIBU_BIN",
    })

    typst_bin = chequear_binario("typst")
    typst_mod = chequear_modulo_python("typst")
    # Un módulo instalado que no se puede importar no compila nada.
    typst_ok = typst_bin["disponible"] or typst_mod["importable"]
    if typst_mod["importable"]:
        detalle_typst = f"módulo Python {typst_mod['version']}"
    elif typst_bin["disponible"]:
        detalle_typst = f"binario {typst_bin['version']} ({typst_bin['ruta']})"
    else:
        detalle_typst = ("El módulo Python no se puede importar y no hay binario en $PATH" if typst_mod["disponible"]
                         else "Ni binario en $PATH ni módulo Python instalado")
    chequeos.append({
        "nombre": "typst", "requerido": True, "ok": typst_ok, "detalle": detalle_typst,
        "proposito": "Render de exámenes en PDF (obligatorio: es el único motor)",
        "sugerencia": "" if typst_ok else "pip install typst  (o) sudo snap install typst / cargo install typst-cli",
    })

    for modulo, proposito, sugerencia in (
        ("pypdf", "Empaquetado de PDFs para imprenta (--bundle-print)", "pip install pypdf"),
        ("segno", "Códigos QR de los exámenes con carátula OMR (alucard omr)", "uv sync"),
        ("jsonschema", "Validación del manifiesto omr-layout/2 (alucard omr)", "uv sync"),
    ):
        info = chequear_modulo_python(modulo)
        chequeos.append({
            "nombre": modulo, "requerido": True, "ok": info["disponible"],
            "detalle": str(info["version"]) if info["disponible"] else "Módulo no instalado",
            "proposito": proposito, "sugerencia": "" if info["disponible"] else sugerencia,
        })

    from generador_examenes.plantuml import comando as comando_plantuml

    plantuml = comando_plantuml()
    chequeos.append({
        "nombre": "plantuml", "requerido": False, "ok": plantuml is not None,
        "detalle": " ".join(plantuml) if plantuml else "No encontrado en $PATH",
        "proposito": "Diagramas de los bloques ```plantuml",
        "sugerencia": "" if plantuml else "sudo dnf install plantuml  (o) ALUCARD_PLANTUML / PLANTUML_JAR",
    })

    pdftoppm = shutil.which("pdftoppm")
    chequeos.append({
        "nombre": "pdftoppm", "requerido": False, "ok": pdftoppm is not None,
        "detalle": pdftoppm or "No encontrado en $PATH",
        "proposito": "Rasterizar carátulas OMR (alucard omr verify-geometry)",
        "sugerencia": "" if pdftoppm else "sudo dnf install poppler-utils  (o) sudo apt install poppler-utils",
    })

    lt_info = chequear_conectividad_languagetool()
    chequeos.append({
        "nombre": "LanguageTool (API pública)", "requerido": False, "ok": lt_info["disponible"],
        "detalle": lt_info["detalle"], "proposito": "Auditoría ortográfica (--spellcheck)",
        "sugerencia": "" if lt_info["disponible"] else "Sin conectividad: --spellcheck fallará hasta configurar --lt-server local",
    })
    return chequeos


def informe_json(chequeos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sobre JSON común de `doctor --json` (schema_version 1.0.0)."""
    from generador_examenes import __version__

    return {
        "schema_version": "1.0.0",
        "herramienta": "alucard",
        "version": __version__,
        "ok": all(c["ok"] for c in chequeos if c["requerido"]),
        "chequeos": chequeos,
    }


def ejecutar_diagnostico_doctor(console: Optional[Console] = None) -> bool:
    """Ejecuta el diagnóstico completo e imprime una tabla con el resultado.

    Retorna ``True`` si todos los requisitos obligatorios (gcc, Typst y
    pypdf) están disponibles; ``False`` en caso contrario,
    indicando cómo instalar lo faltante.
    """
    cons = console or Console()
    tabla = Table(title="🏥 Diagnóstico de alucarD (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle", style="dim")
    tabla.add_column("Acción sugerida", style="yellow")

    chequeos = diagnosticar()
    for c in chequeos:
        if c["ok"]:
            estado, accion = "[bold green]✓ OK[/bold green]", c["proposito"]
        elif c["requerido"]:
            estado, accion = "[bold red]✗ Faltante[/bold red]", c["sugerencia"]
        else:
            estado, accion = "[yellow]! Opcional[/yellow]", c["sugerencia"]
        tabla.add_row(c["nombre"], estado, c["detalle"], accion)

    cons.print(tabla)
    todo_ok = all(c["ok"] for c in chequeos if c["requerido"])
    if todo_ok:
        cons.print("[bold green]✓ Todos los requisitos obligatorios están disponibles.[/bold green]")
    else:
        cons.print(
            "[bold red]✗ Faltan requisitos obligatorios. Revisá las acciones sugeridas arriba.[/bold red]"
        )
    return todo_ok
