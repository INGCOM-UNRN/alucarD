"""
Renderizador HTML usando Jinja2
"""
import json
import logging
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, Template
from generador_examenes.core.models import DefinicionExamen
from generador_examenes.generators.base import BaseRenderer


logger = logging.getLogger(__name__)


class HtmlRenderer(BaseRenderer):
    """Renderizador para generar archivos HTML"""
    
    def __init__(self, templates_dir: Path | None = None):
        """
        Inicializa el renderizador HTML
        
        Args:
            templates_dir: Directorio de plantillas (por defecto usa ./templates)
        """
        if templates_dir is None:
            # Buscar directorio templates relativo al paquete
            templates_dir = Path(__file__).parent.parent.parent / 'templates'
        
        if not templates_dir.exists():
            raise ValueError(f"Directorio de plantillas no encontrado: {templates_dir}")
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.debug(f"HtmlRenderer inicializado con templates: {templates_dir}")
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        return ['html']
    
    def _cargar_i18n(self, idioma: str) -> dict:
        """Carga el archivo de internacionalización"""
        i18n_dir = Path(__file__).parent.parent.parent / 'i18n'
        i18n_file = i18n_dir / f"{idioma}.json"
        
        if not i18n_file.exists():
            logger.warning(f"Archivo i18n no encontrado: {i18n_file}, usando 'es'")
            i18n_file = i18n_dir / "es.json"
        
        with open(i18n_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def renderizar_examen(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza un examen en formato HTML
        
        Args:
            examen_data: Diccionario con 'secciones' del examen
            definicion: Definición del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo HTML generado
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar traducciones
        i18n = self._cargar_i18n(definicion.idioma)
        
        # Evaluar variables personalizadas
        variables = definicion.evaluar_variables_personalizadas()
        
        # Cargar plantilla
        template = self.env.get_template('base_examen.html.j2')
        
        # Preparar contexto
        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n,
            'variables': variables
        }
        
        # Renderizar
        html_content = template.render(**contexto)
        
        # Guardar archivo
        output_file = output_dir / f"examen_tema_{tema + 1:02d}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Examen HTML generado: {output_file.name} (tema {tema + 1})")
        return output_file
    
    def renderizar_clave(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza la clave de respuestas en formato HTML
        
        Args:
            examen_data: Diccionario con 'secciones' del examen
            definicion: Definición del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo HTML de clave generado
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar traducciones
        i18n = self._cargar_i18n(definicion.idioma)
        
        # Evaluar variables personalizadas
        variables = definicion.evaluar_variables_personalizadas()
        
        # Cargar plantilla
        template = self.env.get_template('clave_profesor.html.j2')
        
        # Preparar contexto
        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n,
            'variables': variables
        }
        
        # Renderizar
        html_content = template.render(**contexto)
        
        # Guardar archivo
        output_file = output_dir / f"clave_tema_{tema + 1:02d}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Clave HTML generada: {output_file.name} (tema {tema + 1})")
        return output_file
