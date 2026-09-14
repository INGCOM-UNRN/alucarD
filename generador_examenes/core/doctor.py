"""Diagnóstico de dependencias del sistema para alucarD (ALUCARD-D0401).

Verifica los binarios y módulos de Python de los que depende alucarD en
tiempo de ejecución: ``gcc`` (compilación del sintetizador de preguntas de
C), Typst (binario o módulo `typst`, motor primario de PDF), WeasyPrint
(fallback de PDF), pypdf (empaquetado para imprenta) y, de forma
informativa, la conectividad con la API pública de LanguageTool.

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
from typing import Any, Dict, Optional

from rich.console import Console
from rich.table import Table


def chequear_binario(comando: str, args_version: str = "--version") -> Dict[str, Any]:
    """Verifica si un binario del sistema está disponible en el PATH."""
    ruta = shutil.which(comando)
    if not ruta:
        return {"disponible": False, "version": None, "ruta": None}
    try:
        res = subprocess.run(
            [comando, args_version], capture_output=True, text=True, timeout=5
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
        return {"disponible": False, "version": None}
    try:
        modulo = importlib.import_module(nombre_modulo)
        version = getattr(modulo, "__version__", "Detectado")
    except Exception:
        version = "Detectado (no se pudo importar)"
    return {"disponible": True, "version": version}


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


def ejecutar_diagnostico_doctor(console: Optional[Console] = None) -> bool:
    """Ejecuta el diagnóstico completo e imprime una tabla con el resultado.

    Retorna ``True`` si todos los requisitos obligatorios (gcc y al menos
    un mecanismo de compilación de Typst) están disponibles; ``False`` en
    caso contrario, indicando cómo instalar lo faltante en Ubuntu/Debian.
    """
    cons = console or Console()
    todo_ok = True

    tabla = Table(title="🏥 Diagnóstico de alucarD (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle", style="dim")
    tabla.add_column("Acción sugerida", style="yellow")

    # gcc: obligatorio, usado por el sintetizador de preguntas de C.
    gcc_info = chequear_binario("gcc")
    if gcc_info["disponible"]:
        tabla.add_row(
            "gcc", "[bold green]✓ OK[/bold green]",
            f"{gcc_info['version']} ([cyan]{gcc_info['ruta']}[/cyan])",
            "Compilación del sintetizador de preguntas de C (--sintetizar)",
        )
    else:
        todo_ok = False
        tabla.add_row(
            "gcc", "[bold red]✗ Faltante[/bold red]", "[dim]No encontrado en $PATH[/dim]",
            "sudo apt install build-essential  (Fedora: sudo dnf install gcc)",
        )

    # typst: obligatorio (binario o módulo Python), motor primario de PDF.
    typst_bin = chequear_binario("typst")
    typst_mod = chequear_modulo_python("typst")
    if typst_bin["disponible"] or typst_mod["disponible"]:
        if typst_mod["disponible"]:
            detalle = f"módulo Python {typst_mod['version']}"
        else:
            detalle = f"binario {typst_bin['version']} ([cyan]{typst_bin['ruta']}[/cyan])"
        tabla.add_row(
            "typst", "[bold green]✓ OK[/bold green]", detalle,
            "Render de exámenes en PDF (motor primario)",
        )
    else:
        todo_ok = False
        tabla.add_row(
            "typst", "[bold red]✗ Faltante[/bold red]",
            "[dim]Ni binario en $PATH ni módulo Python instalado[/dim]",
            "pip install typst  (o) sudo snap install typst / cargo install typst-cli",
        )

    # weasyprint: obligatorio (fallback de PDF cuando no hay plantilla Typst).
    weasyprint_mod = chequear_modulo_python("weasyprint")
    if weasyprint_mod["disponible"]:
        tabla.add_row(
            "weasyprint", "[bold green]✓ OK[/bold green]", str(weasyprint_mod["version"]),
            "Fallback de render PDF cuando no hay plantilla Typst",
        )
    else:
        todo_ok = False
        tabla.add_row(
            "weasyprint", "[bold red]✗ Faltante[/bold red]", "[dim]Módulo no instalado[/dim]",
            "pip install weasyprint  (requiere libpango/libcairo del sistema)",
        )

    # pypdf: obligatorio, usado para el empaquetado de imprenta (--bundle-print).
    pypdf_mod = chequear_modulo_python("pypdf")
    if pypdf_mod["disponible"]:
        tabla.add_row(
            "pypdf", "[bold green]✓ OK[/bold green]", str(pypdf_mod["version"]),
            "Empaquetado de PDFs para imprenta (--bundle-print)",
        )
    else:
        todo_ok = False
        tabla.add_row(
            "pypdf", "[bold red]✗ Faltante[/bold red]", "[dim]Módulo no instalado[/dim]",
            "pip install pypdf",
        )

    # LanguageTool: opcional/informativo, usado por --spellcheck.
    lt_info = chequear_conectividad_languagetool()
    if lt_info["disponible"]:
        tabla.add_row(
            "LanguageTool (API pública)", "[bold green]✓ OK[/bold green]", lt_info["detalle"],
            "Auditoría ortográfica (--spellcheck)",
        )
    else:
        tabla.add_row(
            "LanguageTool (API pública)", "[yellow]! Opcional[/yellow]", lt_info["detalle"],
            "Sin conectividad: --spellcheck fallará hasta configurar --lt-server local",
        )

    cons.print(tabla)
    if todo_ok:
        cons.print("[bold green]✓ Todos los requisitos obligatorios están disponibles.[/bold green]")
    else:
        cons.print(
            "[bold red]✗ Faltan requisitos obligatorios. Revisá las acciones sugeridas arriba.[/bold red]"
        )
    return todo_ok
