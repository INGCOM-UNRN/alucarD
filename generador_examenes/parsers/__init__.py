"""
Módulo parsers - Parsers para diferentes formatos de bancos de preguntas
"""
from pathlib import Path
from typing import Dict, Type
from generador_examenes.parsers.base import BaseParser
from generador_examenes.parsers.gift_parser import GiftParser
from generador_examenes.parsers.moodle_parser import MoodleXMLParser


# Registro de parsers disponibles
PARSERS_REGISTRY: Dict[str, Type[BaseParser]] = {}


def registrar_parser(parser_class: Type[BaseParser]) -> None:
    """Registra un parser en el registro global"""
    for ext in parser_class.get_supported_extensions():
        PARSERS_REGISTRY[ext.lower()] = parser_class


def obtener_parser(filepath: Path) -> BaseParser:
    """
    Obtiene el parser apropiado según la extensión del archivo
    
    Args:
        filepath: Ruta al archivo
        
    Returns:
        Instancia del parser apropiado
        
    Raises:
        ValueError: Si no hay parser para la extensión
    """
    extension = filepath.suffix.lower()
    
    if extension not in PARSERS_REGISTRY:
        raise ValueError(
            f"No hay parser disponible para la extensión '{extension}'. "
            f"Extensiones soportadas: {list(PARSERS_REGISTRY.keys())}"
        )
    
    parser_class = PARSERS_REGISTRY[extension]
    return parser_class()


# Registrar parsers al importar el módulo
registrar_parser(GiftParser)
registrar_parser(MoodleXMLParser)


__all__ = [
    'BaseParser',
    'GiftParser', 
    'MoodleXMLParser',
    'PARSERS_REGISTRY',
    'registrar_parser',
    'obtener_parser'
]
