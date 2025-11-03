"""
Renderizador PDF usando WeasyPrint
"""
import logging
from pathlib import Path
from typing import Any
from generador_examenes.core.models import DefinicionExamen
from generador_examenes.generators.base import BaseRenderer
from generador_examenes.generators.html_renderer import HtmlRenderer


logger = logging.getLogger(__name__)


class PdfRenderer(BaseRenderer):
    """Renderizador para generar archivos PDF vía WeasyPrint"""
    
    def __init__(self, templates_dir: Path | None = None):
        """
        Inicializa el renderizador PDF
        
        Args:
            templates_dir: Directorio de plantillas (por defecto usa ./templates)
        """
        # El PDF renderer reutiliza el HTML renderer internamente
        self.html_renderer = HtmlRenderer(templates_dir)
        
        try:
            from weasyprint import HTML
            self.HTML = HTML
            logger.debug("WeasyPrint importado correctamente")
        except ImportError:
            raise ImportError(
                "WeasyPrint no está instalado. "
                "Instálalo con: pip install weasyprint"
            )
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        return ['pdf']
    
    def renderizar_examen(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza un examen en formato PDF
        
        Args:
            examen_data: Diccionario con 'secciones' del examen
            definicion: Definición del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo PDF generado
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Primero generar HTML en memoria usando el HTML renderer
        logger.debug(f"Generando HTML para PDF del tema {tema + 1}")
        
        # Cargar plantilla y renderizar HTML
        from jinja2 import Environment, FileSystemLoader
        import json
        
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Cargar traducciones
        i18n_dir = Path(__file__).parent.parent.parent / 'i18n'
        i18n_file = i18n_dir / f"{definicion.idioma}.json"
        if not i18n_file.exists():
            i18n_file = i18n_dir / "es.json"
        
        with open(i18n_file, 'r', encoding='utf-8') as f:
            i18n = json.load(f)
        
        template = env.get_template('base_examen.html.j2')
        
        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }
        
        html_content = template.render(**contexto)
        
        # Convertir HTML a PDF
        output_file = output_dir / f"examen_tema_{tema + 1:02d}.pdf"
        
        logger.debug(f"Convirtiendo HTML a PDF: {output_file}")
        html_doc = self.HTML(string=html_content, base_url=str(templates_dir))
        html_doc.write_pdf(str(output_file))
        
        logger.info(f"Examen PDF generado: {output_file}")
        return output_file
    
    def renderizar_clave(
        self, 
        examen_data: Any, 
        definicion: DefinicionExamen, 
        output_dir: Path, 
        tema: int
    ) -> Path:
        """
        Renderiza la clave de respuestas en formato PDF
        
        Args:
            examen_data: Diccionario con 'secciones' del examen
            definicion: Definición del examen
            output_dir: Directorio de salida
            tema: Número del tema
            
        Returns:
            Path al archivo PDF de clave generado
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar HTML para la clave
        logger.debug(f"Generando HTML de clave para PDF del tema {tema + 1}")
        
        from jinja2 import Environment, FileSystemLoader
        import json
        
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Cargar traducciones
        i18n_dir = Path(__file__).parent.parent.parent / 'i18n'
        i18n_file = i18n_dir / f"{definicion.idioma}.json"
        if not i18n_file.exists():
            i18n_file = i18n_dir / "es.json"
        
        with open(i18n_file, 'r', encoding='utf-8') as f:
            i18n = json.load(f)
        
        template = env.get_template('clave_profesor.html.j2')
        
        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }
        
        html_content = template.render(**contexto)
        
        # Convertir HTML a PDF
        output_file = output_dir / f"clave_tema_{tema + 1:02d}.pdf"
        
        logger.debug(f"Convirtiendo clave HTML a PDF: {output_file}")
        html_doc = self.HTML(string=html_content, base_url=str(templates_dir))
        html_doc.write_pdf(str(output_file))
        
        logger.info(f"Clave PDF generada: {output_file}")
        return output_file
