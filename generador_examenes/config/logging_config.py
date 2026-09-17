"""
Configuración del sistema de logging
"""
import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """
    Configura el sistema de logging de la aplicación
    
    Args:
        debug: Si es True, establece nivel DEBUG; si no, nivel INFO
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Configurar formato
    formatter = logging.Formatter(
        '[%(levelname)s] [%(name)s] %(message)s'
    )
    
    # Configurar handler para consola (en stderr para preservar stdout para pipes y --json)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # Silenciar logs excesivamente verbosos de librerías externas
    logging.getLogger('weasyprint').setLevel(logging.WARNING)
    logging.getLogger('fontTools').setLevel(logging.WARNING)
