"""
Modelos de datos usando Pydantic para validación de estructuras
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional


class Opcion(BaseModel):
    """Modelo para una opción de pregunta de selección múltiple"""
    texto_html: str
    es_correcta: bool
    retroalimentacion: Optional[str] = None


class Pregunta(BaseModel):
    """Modelo para una pregunta del banco"""
    id: str
    tipo: Literal["seleccion_multiple", "verdadero_falso", "respuesta_corta", "ensayo", "emparejamiento", "numerica"]
    nombre: str
    categoria: str
    enunciado_html: str
    puntaje: float = 1.0
    opciones: List[Opcion] = Field(default_factory=list)
    etiquetas: List[str] = Field(default_factory=list)
    retroalimentacion_general: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PoolConfig(BaseModel):
    """Configuración de un pool de preguntas para una sección"""
    banco: Optional[str] = None
    preguntas_fijadas: List[str] = Field(default_factory=list)
    categoria: Optional[str] = None
    tipos: List[str] = Field(default_factory=list)
    etiquetas: List[str] = Field(default_factory=list)
    cantidad: Optional[int] = None
    accion_si_insuficiente: Literal["error", "advertir", "usar_todas"] = "error"
    puntaje_fijo_por_pregunta: Optional[float] = None


class SeccionExamen(BaseModel):
    """Configuración de una sección del examen"""
    nombre: str
    instrucciones: Optional[str] = None
    pools: List[PoolConfig]


class ConfiguracionExamen(BaseModel):
    """Configuración global del examen"""
    mezclar_preguntas_dentro_seccion: bool = True
    mezclar_opciones_dentro_pregunta: bool = True
    generar_clave_profesor: bool = True


class DefinicionExamen(BaseModel):
    """Modelo principal para la definición del examen en YAML"""
    nombre_examen: str
    institucion: str
    materia: str
    fecha: Optional[str] = None
    duracion_minutos: Optional[int] = None
    instrucciones_generales: Optional[str] = None
    idioma: str = "es"
    configuracion_examen: ConfiguracionExamen
    secciones_examen: List[SeccionExamen]
