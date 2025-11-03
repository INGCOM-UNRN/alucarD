"""
Clase base abstracta para parsers de bancos de preguntas
"""
from abc import ABC, abstractmethod
from typing import Dict
from pathlib import Path
from generador_examenes.core.models import Pregunta


class BaseParser(ABC):
    """
    Clase base abstracta que define la interfaz para todos los parsers.
    Los parsers concretos deben implementar el método parse().
    """
    
    @abstractmethod
    def parse(self, filepath: Path) -> Dict[str, Pregunta]:
        """
        Parsea un archivo de banco de preguntas y retorna un diccionario
        de preguntas indexadas por ID.
        
        Args:
            filepath: Ruta al archivo del banco de preguntas
            
        Returns:
            Diccionario con preguntas {id: Pregunta}
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el formato del archivo es inválido
        """
        pass
    
    @staticmethod
    def get_supported_extensions() -> list[str]:
        """
        Retorna la lista de extensiones de archivo soportadas por este parser
        
        Returns:
            Lista de extensiones (ej: ['.txt', '.gift'])
        """
        return []
