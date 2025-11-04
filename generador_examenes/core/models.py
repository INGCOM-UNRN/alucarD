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
    
    def __str__(self) -> str:
        texto_preview = self.texto_html[:50] + "..." if len(self.texto_html) > 50 else self.texto_html
        marca = "✓" if self.es_correcta else "✗"
        return f"[{marca}] {texto_preview}"
    
    def __repr__(self) -> str:
        return f"Opcion(correcta={self.es_correcta}, texto='{self.texto_html[:30]}...')"


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
    
    def __str__(self) -> str:
        nombre_preview = self.nombre[:60] + "..." if len(self.nombre) > 60 else self.nombre
        etiquetas_str = f" [{', '.join(self.etiquetas)}]" if self.etiquetas else ""
        return f"[{self.tipo}] {nombre_preview} (cat: {self.categoria}, pts: {self.puntaje}){etiquetas_str}"
    
    def __repr__(self) -> str:
        return f"Pregunta(id='{self.id}', tipo='{self.tipo}', cat='{self.categoria}', opciones={len(self.opciones)})"


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
    
    def __str__(self) -> str:
        filtros = []
        if self.categoria:
            filtros.append(f"cat:{self.categoria}")
        if self.tipos:
            filtros.append(f"tipos:{','.join(self.tipos)}")
        if self.etiquetas:
            filtros.append(f"tags:{','.join(self.etiquetas)}")
        if self.preguntas_fijadas:
            filtros.append(f"fijadas:{len(self.preguntas_fijadas)}")
        
        filtros_str = ", ".join(filtros) if filtros else "sin filtros"
        cant_str = f"cant:{self.cantidad}" if self.cantidad else "todas"
        return f"Pool({filtros_str}, {cant_str})"
    
    def __repr__(self) -> str:
        return f"PoolConfig(categoria={self.categoria}, tipos={self.tipos}, cantidad={self.cantidad})"


class SeccionExamen(BaseModel):
    """Configuración de una sección del examen"""
    nombre: str
    instrucciones: Optional[str] = None
    pools: List[PoolConfig]
    layout: Literal["default", "compact-2col", "compact-3col", "compact-4col"] = "default"
    
    def __str__(self) -> str:
        layout_str = f", layout:{self.layout}" if self.layout != "default" else ""
        return f"Sección '{self.nombre}' ({len(self.pools)} pools{layout_str})"
    
    def __repr__(self) -> str:
        return f"SeccionExamen(nombre='{self.nombre}', pools={len(self.pools)}, layout='{self.layout}')"


class ConfiguracionExamen(BaseModel):
    """Configuración global del examen"""
    mezclar_preguntas_dentro_seccion: bool = True
    mezclar_opciones_dentro_pregunta: bool = True
    generar_clave_profesor: bool = True
    
    def __str__(self) -> str:
        flags = []
        if self.mezclar_preguntas_dentro_seccion:
            flags.append("mezcla_preguntas")
        if self.mezclar_opciones_dentro_pregunta:
            flags.append("mezcla_opciones")
        if self.generar_clave_profesor:
            flags.append("con_clave")
        return f"Config({', '.join(flags)})"
    
    def __repr__(self) -> str:
        return f"ConfiguracionExamen(mezcla_p={self.mezclar_preguntas_dentro_seccion}, mezcla_o={self.mezclar_opciones_dentro_pregunta}, clave={self.generar_clave_profesor})"


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
    variables_personalizadas: Dict[str, str] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        fecha_str = f" ({self.fecha})" if self.fecha else ""
        duracion_str = f" - {self.duracion_minutos}min" if self.duracion_minutos else ""
        vars_str = f" +{len(self.variables_personalizadas)} vars" if self.variables_personalizadas else ""
        return f"'{self.nombre_examen}'{fecha_str}{duracion_str} - {self.materia} ({self.institucion}) - {len(self.secciones_examen)} secciones{vars_str}"
    
    def __repr__(self) -> str:
        return f"DefinicionExamen(nombre='{self.nombre_examen}', secciones={len(self.secciones_examen)})"
    
    def evaluar_variables_personalizadas(self) -> Dict[str, Any]:
        """
        Evalúa las variables personalizadas, procesando f-strings.
        
        Las variables pueden referenciar:
        - Campos de la definición: {nombre_examen}, {institucion}, etc.
        - Otras variables personalizadas ya evaluadas
        - Variables de Python estándar: fecha actual, etc.
        
        Returns:
            Diccionario con variables evaluadas
        """
        from datetime import datetime
        
        # Contexto base con campos de la definición
        contexto = {
            'nombre_examen': self.nombre_examen,
            'institucion': self.institucion,
            'materia': self.materia,
            'fecha': self.fecha,
            'duracion_minutos': self.duracion_minutos,
            'idioma': self.idioma,
            # Variables útiles
            'fecha_actual': datetime.now().strftime('%Y-%m-%d'),
            'anio_actual': datetime.now().year,
            'mes_actual': datetime.now().month,
            'dia_actual': datetime.now().day,
        }
        
        # Evaluar variables personalizadas (orden de definición importa)
        variables_evaluadas = {}
        for key, valor_template in self.variables_personalizadas.items():
            try:
                # Evaluar f-string con contexto actual
                valor_evaluado = valor_template.format(**contexto, **variables_evaluadas)
                variables_evaluadas[key] = valor_evaluado
            except (KeyError, ValueError) as e:
                # Si falla, mantener el valor original
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"No se pudo evaluar variable '{key}': {e}. Usando valor original.")
                variables_evaluadas[key] = valor_template
        
        return variables_evaluadas
