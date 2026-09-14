"""
Utilidad compartida de manejo de errores de uso de CLI.

Se extrajo a su propio módulo para poder ser importada tanto desde
``__main__.py`` (parseo/validación de opciones Typer) como desde
``cli_commands.py`` (validaciones de negocio equivalentes a las que
antes hacía ``ArgumentParser.error``), evitando un import circular.
"""
from rich.console import Console

console = Console()


def usage_error(message: str) -> None:
    """Equivalente a ``ArgumentParser.error``: reporta y sale con código 2.

    Se implementa con ``SystemExit`` (en vez de una excepción propia) para
    que no quede capturada por los ``except Exception`` de la lógica de
    negocio circundante, preservando el contrato histórico de la CLI
    (antes basada en argparse) donde este error atraviesa cualquier bloque
    try/except intermedio.
    """
    console.print(f"[red]generador-examenes: error: {message}[/red]")
    raise SystemExit(2)
