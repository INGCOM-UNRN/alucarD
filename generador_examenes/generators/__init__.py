"""
Módulo generators - Renderizadores para diferentes formatos de salida
"""
from typing import Dict, Type
from generador_examenes.generators.base import BaseRenderer
from generador_examenes.generators.html_renderer import HtmlRenderer
from generador_examenes.generators.pdf_renderer import PdfRenderer


# Registro de renderizadores disponibles
RENDERERS_REGISTRY: Dict[str, Type[BaseRenderer]] = {}


def registrar_renderer(renderer_class: Type[BaseRenderer]) -> None:
    """Registra un renderer en el registro global"""
    for fmt in renderer_class.get_supported_formats():
        RENDERERS_REGISTRY[fmt.lower()] = renderer_class


def obtener_renderer(formato: str) -> BaseRenderer:
    """
    Obtiene el renderer apropiado según el formato solicitado
    
    Args:
        formato: Formato de salida ('html', 'pdf', etc.)
        
    Returns:
        Instancia del renderer apropiado
        
    Raises:
        ValueError: Si no hay renderer para el formato
    """
    formato = formato.lower()
    
    if formato not in RENDERERS_REGISTRY:
        raise ValueError(
            f"No hay renderer disponible para el formato '{formato}'. "
            f"Formatos soportados: {list(RENDERERS_REGISTRY.keys())}"
        )
    
    renderer_class = RENDERERS_REGISTRY[formato]
    return renderer_class()


# Registrar renderers al importar el módulo
registrar_renderer(HtmlRenderer)
registrar_renderer(PdfRenderer)


__all__ = [
    'BaseRenderer',
    'HtmlRenderer',
    'PdfRenderer',
    'RENDERERS_REGISTRY',
    'registrar_renderer',
    'obtener_renderer'
]
