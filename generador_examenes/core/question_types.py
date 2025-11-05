"""
Definiciones y utilidades para tipos de preguntas

Este módulo centraliza la lógica relacionada con los diferentes tipos de
preguntas soportados por el sistema.
"""
from typing import Dict, List, Literal
from enum import Enum


# Tipos de preguntas soportados
TipoPregunta = Literal[
    "seleccion_multiple",
    "verdadero_falso", 
    "respuesta_corta",
    "ensayo",
    "emparejamiento",
    "numerica",
    "desarrollo"
]


class QuestionType(str, Enum):
    """Enum para tipos de preguntas con metadatos"""
    SELECCION_MULTIPLE = "seleccion_multiple"
    VERDADERO_FALSO = "verdadero_falso"
    RESPUESTA_CORTA = "respuesta_corta"
    ENSAYO = "ensayo"
    EMPAREJAMIENTO = "emparejamiento"
    NUMERICA = "numerica"
    DESARROLLO = "desarrollo"
    
    @property
    def display_name(self) -> str:
        """Nombre legible del tipo de pregunta"""
        names = {
            "seleccion_multiple": "Selección Múltiple",
            "verdadero_falso": "Verdadero/Falso",
            "respuesta_corta": "Respuesta Corta",
            "ensayo": "Ensayo",
            "emparejamiento": "Emparejamiento",
            "numerica": "Numérica",
            "desarrollo": "Desarrollo"
        }
        return names.get(self.value, self.value.replace("_", " ").title())
    
    @property
    def requires_options(self) -> bool:
        """Indica si el tipo de pregunta requiere opciones de respuesta"""
        return self.value in ["seleccion_multiple", "verdadero_falso", "emparejamiento"]
    
    @property
    def supports_partial_credit(self) -> bool:
        """Indica si el tipo de pregunta soporta puntos parciales"""
        return self.value in ["seleccion_multiple", "numerica", "emparejamiento"]
    
    @property
    def typical_points(self) -> float:
        """Puntaje típico sugerido para este tipo de pregunta"""
        points_map = {
            "seleccion_multiple": 2.0,
            "verdadero_falso": 1.0,
            "respuesta_corta": 3.0,
            "ensayo": 5.0,
            "emparejamiento": 4.0,
            "numerica": 2.0,
            "desarrollo": 10.0
        }
        return points_map.get(self.value, 1.0)
    
    @property
    def ideal_time_minutes(self) -> float:
        """Tiempo ideal sugerido en minutos para resolver este tipo de pregunta"""
        time_map = {
            "seleccion_multiple": 1.5,
            "verdadero_falso": 0.5,
            "respuesta_corta": 2.0,
            "ensayo": 5.0,
            "emparejamiento": 3.0,
            "numerica": 2.0,
            "desarrollo": 15.0
        }
        return time_map.get(self.value, 2.0)
    
    @classmethod
    def from_moodle_type(cls, moodle_type: str) -> "QuestionType":
        """Convierte un tipo de Moodle al tipo interno"""
        mapping = {
            "multichoice": cls.SELECCION_MULTIPLE,
            "truefalse": cls.VERDADERO_FALSO,
            "shortanswer": cls.RESPUESTA_CORTA,
            "essay": cls.DESARROLLO,
            "matching": cls.EMPAREJAMIENTO,
            "numerical": cls.NUMERICA
        }
        return mapping.get(moodle_type, cls.SELECCION_MULTIPLE)
    
    @classmethod
    def to_moodle_type(cls, tipo: "QuestionType") -> str:
        """Convierte el tipo interno a tipo Moodle"""
        mapping = {
            cls.SELECCION_MULTIPLE: "multichoice",
            cls.VERDADERO_FALSO: "truefalse",
            cls.RESPUESTA_CORTA: "shortanswer",
            cls.DESARROLLO: "essay",
            cls.ENSAYO: "essay",
            cls.EMPAREJAMIENTO: "matching",
            cls.NUMERICA: "numerical"
        }
        return mapping.get(tipo, "multichoice")


class QuestionTypeRegistry:
    """Registro central de tipos de preguntas y sus características"""
    
    def __init__(self):
        self._types: Dict[str, QuestionType] = {}
        self._initialize_default_types()
    
    def _initialize_default_types(self):
        """Inicializa los tipos de preguntas por defecto"""
        for tipo in QuestionType:
            self._types[tipo.value] = tipo
    
    def get_type(self, tipo_str: str) -> QuestionType:
        """Obtiene un tipo de pregunta por su string"""
        if tipo_str not in self._types:
            raise ValueError(f"Tipo de pregunta no soportado: {tipo_str}")
        return self._types[tipo_str]
    
    def is_valid_type(self, tipo_str: str) -> bool:
        """Verifica si un tipo de pregunta es válido"""
        return tipo_str in self._types
    
    def get_all_types(self) -> List[str]:
        """Obtiene lista de todos los tipos soportados"""
        return list(self._types.keys())
    
    def get_types_requiring_options(self) -> List[str]:
        """Obtiene tipos que requieren opciones"""
        return [t.value for t in self._types.values() if t.requires_options]
    
    def estimate_exam_duration(self, question_counts: Dict[str, int]) -> float:
        """
        Estima la duración de un examen basado en cantidad de preguntas por tipo
        
        Args:
            question_counts: Dict con {tipo_pregunta: cantidad}
            
        Returns:
            Duración estimada en minutos
        """
        total_minutes = 0.0
        for tipo_str, count in question_counts.items():
            if tipo_str in self._types:
                tipo = self._types[tipo_str]
                total_minutes += tipo.ideal_time_minutes * count
        
        # Agregar 10% de buffer
        return total_minutes * 1.1


# Singleton global del registro
_registry = QuestionTypeRegistry()


def get_question_type_registry() -> QuestionTypeRegistry:
    """Obtiene la instancia global del registro de tipos de preguntas"""
    return _registry


def is_valid_question_type(tipo: str) -> bool:
    """Helper para validar si un tipo de pregunta es válido"""
    return _registry.is_valid_type(tipo)


def get_display_name(tipo: str) -> str:
    """Helper para obtener el nombre legible de un tipo de pregunta"""
    try:
        question_type = _registry.get_type(tipo)
        return question_type.display_name
    except ValueError:
        return tipo.replace("_", " ").title()


def requires_options(tipo: str) -> bool:
    """Helper para verificar si un tipo requiere opciones"""
    try:
        question_type = _registry.get_type(tipo)
        return question_type.requires_options
    except ValueError:
        return False
