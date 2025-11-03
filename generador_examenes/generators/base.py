"""
Clase base abstracta para renderizadores de exámenes
"""
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path
from generador_examenes.core.models import DefinicionExamen


class BaseRenderer(ABC):
    """
    Clase base abstracta que define la interfaz para todos los renderizadores.
    Los renderizadores concretos deben implementar los métodos de renderizado.
    """
    
    @abstractmethod
    def renderizar_examen(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza un examen completo
        
        Args:
            examen_data: Datos del examen mezclado y listo para renderizar
            definicion: Definición completa del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo generado
        """
        pass
    
    @abstractmethod
    def renderizar_clave(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza la clave de respuestas para el profesor
        
        Args:
            examen_data: Datos del examen con respuestas correctas
            definicion: Definición completa del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo de clave generado
        """
        pass
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        """
        Retorna la lista de formatos de salida soportados por este renderer
        
        Returns:
            Lista de formatos (ej: ['html', 'pdf'])
        """
        return []
