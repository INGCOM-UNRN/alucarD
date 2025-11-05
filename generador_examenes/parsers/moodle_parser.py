"""
Parser para formato Moodle XML
"""
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict
from generador_examenes.core.models import Pregunta, Opcion
from generador_examenes.parsers.base import BaseParser
from generador_examenes.core.markdown_utils import detect_and_convert_format


logger = logging.getLogger(__name__)


class MoodleXMLParser(BaseParser):
    """Parser para archivos XML de Moodle"""
    
    @staticmethod
    def get_supported_extensions() -> list[str]:
        return ['.xml']
    
    def parse(self, filepath: Path) -> Dict[str, Pregunta]:
        """
        Parsea un archivo XML de Moodle y retorna un diccionario de preguntas
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
        
        logger.info(f"Parseando archivo Moodle XML: {filepath}")
        
        preguntas = {}
        banco_nombre = filepath.name
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Buscar todas las preguntas en el XML
            for i, question_elem in enumerate(root.findall('.//question')):
                try:
                    pregunta = self._parsear_pregunta(question_elem, i, banco_nombre)
                    if pregunta:
                        preguntas[pregunta.id] = pregunta
                except Exception as e:
                    logger.warning(f"Error parseando pregunta {i}: {e}")
                    continue
            
            logger.info(f"✓ {len(preguntas)} preguntas cargadas de {filepath.name}")
            
        except ET.ParseError as e:
            raise ValueError(f"Error parseando XML: {e}")
        except Exception as e:
            raise ValueError(f"Error procesando archivo Moodle XML: {e}")
        
        return preguntas
    
    def _parsear_pregunta(self, question_elem: ET.Element, indice: int, banco_nombre: str = None) -> Pregunta | None:
        """Parsea un elemento question del XML"""
        
        # Obtener tipo de pregunta
        tipo_moodle = question_elem.get('type', '')
        
        # Ignorar categorías y preguntas no soportadas
        if tipo_moodle in ['category', 'description']:
            return None
        
        # Mapear tipos de Moodle a nuestros tipos
        tipo_map = {
            'multichoice': 'seleccion_multiple',
            'truefalse': 'verdadero_falso',
            'shortanswer': 'respuesta_corta',
            'essay': 'desarrollo',
            'matching': 'emparejamiento',
            'numerical': 'numerica'
        }
        
        tipo = tipo_map.get(tipo_moodle, 'respuesta_corta')
        
        # Para preguntas tipo desarrollo, detectar tamaño desde responseformat
        tamano_desarrollo = None
        if tipo == 'desarrollo':
            responseformat = question_elem.find('responseformat')
            if responseformat is not None and responseformat.text:
                # Moodle usa: editor, editorfilepicker, plain, monospaced, noinline
                # Mapear a nuestros tamaños: pequeno, mediano, grande
                format_map = {
                    'noinline': 'pequeno',
                    'plain': 'mediano', 
                    'editor': 'grande',
                    'editorfilepicker': 'grande',
                    'monospaced': 'mediano'
                }
                tamano_desarrollo = format_map.get(responseformat.text, 'mediano')
            else:
                tamano_desarrollo = 'mediano'
        
        # Extraer nombre
        name_elem = question_elem.find('name/text')
        nombre = name_elem.text if name_elem is not None and name_elem.text else f"pregunta_{indice + 1}"
        
        # Extraer enunciado con formato
        questiontext_elem = question_elem.find('questiontext/text')
        questiontext_format = question_elem.find('questiontext')
        format_attr = questiontext_format.get('format', 'html') if questiontext_format is not None else 'html'
        
        enunciado = ""
        if questiontext_elem is not None and questiontext_elem.text:
            enunciado = detect_and_convert_format(questiontext_elem.text, format_attr)
        
        # Extraer categoría
        categoria = "General"
        # Buscar en el contexto del archivo si hay categoría definida
        category_elem = question_elem.find('.//category')
        if category_elem is not None:
            cat_text = category_elem.find('text')
            if cat_text is not None and cat_text.text:
                # Las categorías en Moodle vienen como $course$/Top/Subcategory
                categoria = cat_text.text.split('/')[-1] if '/' in cat_text.text else cat_text.text
        
        # Extraer etiquetas (tags)
        etiquetas = []
        tags_elem = question_elem.find('tags')
        if tags_elem is not None:
            for tag in tags_elem.findall('tag'):
                tag_text = tag.find('text')
                if tag_text is not None and tag_text.text:
                    etiquetas.append(tag_text.text)
        
        # Extraer puntaje por defecto
        defaultgrade_elem = question_elem.find('defaultgrade')
        puntaje = float(defaultgrade_elem.text) if defaultgrade_elem is not None and defaultgrade_elem.text else 1.0
        
        # Parsear opciones según el tipo
        opciones = []
        if tipo == 'seleccion_multiple':
            opciones = self._parsear_opciones_multichoice(question_elem)
        elif tipo == 'verdadero_falso':
            opciones = self._parsear_opciones_truefalse(question_elem)
        elif tipo in ['respuesta_corta', 'numerica']:
            opciones = self._parsear_opciones_shortanswer(question_elem)
        
        # Extraer retroalimentación general
        generalfeedback_elem = question_elem.find('generalfeedback/text')
        retroalimentacion_general = generalfeedback_elem.text if generalfeedback_elem is not None and generalfeedback_elem.text else None
        
        pregunta = Pregunta(
            id=f"moodle_{indice + 1}_{nombre.replace(' ', '_')}",
            tipo=tipo,
            nombre=nombre,
            categoria=categoria,
            enunciado_html=enunciado,
            puntaje=puntaje,
            opciones=opciones,
            etiquetas=etiquetas,
            retroalimentacion_general=retroalimentacion_general,
            tamano_desarrollo=tamano_desarrollo,
            fuente_banco=banco_nombre
        )
        
        return pregunta
    
    def _parsear_opciones_multichoice(self, question_elem: ET.Element) -> list[Opcion]:
        """Parsea opciones de selección múltiple"""
        opciones = []
        
        for answer_elem in question_elem.findall('answer'):
            # Obtener texto de la opción
            text_elem = answer_elem.find('text')
            if text_elem is None or not text_elem.text:
                continue
            
            # Obtener formato de la respuesta
            format_attr = answer_elem.get('format', 'html')
            texto = detect_and_convert_format(text_elem.text, format_attr)
            
            # Obtener fracción (>0 es correcta)
            fraction = float(answer_elem.get('fraction', '0'))
            es_correcta = fraction > 0
            
            # Obtener retroalimentación de la opción
            feedback_elem = answer_elem.find('feedback/text')
            feedback_format_elem = answer_elem.find('feedback')
            feedback_format = feedback_format_elem.get('format', 'html') if feedback_format_elem is not None else 'html'
            retroalimentacion = None
            if feedback_elem is not None and feedback_elem.text:
                retroalimentacion = detect_and_convert_format(feedback_elem.text, feedback_format)
            
            opciones.append(Opcion(
                texto_html=texto,
                es_correcta=es_correcta,
                retroalimentacion=retroalimentacion
            ))
        
        return opciones
    
    def _parsear_opciones_truefalse(self, question_elem: ET.Element) -> list[Opcion]:
        """Parsea opciones de verdadero/falso"""
        # Buscar cuál es la respuesta correcta
        es_verdadero = False
        
        for answer_elem in question_elem.findall('answer'):
            text_elem = answer_elem.find('text')
            if text_elem is not None and text_elem.text:
                fraction = float(answer_elem.get('fraction', '0'))
                if fraction > 0:
                    # true o 1 significa verdadero
                    es_verdadero = text_elem.text.lower() in ['true', '1', 'verdadero']
                    break
        
        return [
            Opcion(texto_html="Verdadero", es_correcta=es_verdadero),
            Opcion(texto_html="Falso", es_correcta=not es_verdadero)
        ]
    
    def _parsear_opciones_shortanswer(self, question_elem: ET.Element) -> list[Opcion]:
        """Parsea opciones de respuesta corta o numérica"""
        opciones = []
        
        for answer_elem in question_elem.findall('answer'):
            text_elem = answer_elem.find('text')
            if text_elem is None or not text_elem.text:
                continue
            
            # Obtener formato de la respuesta
            format_attr = answer_elem.get('format', 'html')
            texto = detect_and_convert_format(text_elem.text, format_attr)
            
            # En respuesta corta, todas las respuestas con fracción > 0 son correctas
            fraction = float(answer_elem.get('fraction', '0'))
            es_correcta = fraction > 0
            
            if es_correcta:
                opciones.append(Opcion(
                    texto_html=texto,
                    es_correcta=True
                ))
        
        return opciones
