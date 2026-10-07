#!/usr/bin/env python3
"""
Visor de Árbol de Categorías de Bancos de Preguntas

Genera una página HTML interactiva mostrando la jerarquía de categorías
de uno o más bancos de preguntas con contadores y botones para copiar nombres.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class CategoryNode:
    """Representa un nodo en el árbol de categorías."""
    
    def __init__(self, name: str, full_path: str):
        self.name = name
        self.full_path = full_path
        self.count = 0
        self.type_counts: Dict[str, int] = defaultdict(int)
        self.children: Dict[str, CategoryNode] = {}
        
    def add_question(self, question_type: Optional[str] = None):
        """Incrementa el contador de preguntas y por tipo."""
        self.count += 1
        if question_type:
            self.type_counts[question_type] += 1
        
    def add_child(self, name: str, full_path: str) -> 'CategoryNode':
        """Agrega un nodo hijo."""
        if name not in self.children:
            self.children[name] = CategoryNode(name, full_path)
        return self.children[name]
        
    def to_dict(self) -> dict:
        """Convierte el nodo a diccionario para serialización."""
        return {
            'name': self.name,
            'full_path': self.full_path,
            'count': self.count,
            'type_counts': dict(self.type_counts),
            'children': {k: v.to_dict() for k, v in self.children.items()}
        }


def build_category_tree(banco_preguntas: Dict) -> CategoryNode:
    """
    Construye un árbol de categorías a partir de un banco de preguntas.
    
    Args:
        banco_preguntas: Diccionario de preguntas {id: Pregunta}
        
    Returns:
        Nodo raíz del árbol de categorías
    """
    root = CategoryNode("(raíz)", "")
    
    for pregunta in banco_preguntas.values():
        categoria = pregunta.categoria or "Sin categoría"
        question_type = pregunta.tipo
        
        # Dividir la categoría en partes
        if '/' in categoria:
            parts = [p.strip() for p in categoria.split('/') if p.strip()]
        else:
            parts = [categoria]
            
        # Construir la ruta en el árbol
        current = root
        full_path = ""
        
        for part in parts:
            if full_path:
                full_path += "/" + part
            else:
                full_path = part
                
            current = current.add_child(part, full_path)
            current.add_question(question_type)
    
    return root


def generate_html_tree(banco_paths: List[Path], output_path: Path) -> Path:
    """
    Genera un archivo HTML con el árbol de categorías de los bancos.
    
    Args:
        banco_paths: Lista de rutas a archivos de banco de preguntas
        output_path: Ruta donde guardar el HTML
        
    Returns:
        Ruta del archivo HTML generado
    """
    from generador_examenes.parsers import obtener_parser
    
    # Cargar todos los bancos
    all_questions = {}
    banco_info = []
    
    for banco_path in banco_paths:
        try:
            parser = obtener_parser(banco_path)
            preguntas = parser.parse(banco_path)
            
            all_questions.update(preguntas)
            banco_info.append({
                'path': str(banco_path),
                'name': banco_path.name,
                'count': len(preguntas),
                'tipo': banco_path.suffix
            })
            
            logger.info(f"✓ Cargado banco: {banco_path.name} ({len(preguntas)} preguntas)")
            
        except Exception as e:
            logger.error(f"✗ Error cargando {banco_path}: {e}")
            continue
    
    if not all_questions:
        raise ValueError("No se pudieron cargar preguntas de ningún banco")
    
    # Construir árbol
    tree = build_category_tree(all_questions)
    
    # Generar HTML
    html_content = generate_html_content(tree, banco_info, len(all_questions))
    
    # Guardar archivo
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding='utf-8')
    
    logger.info(f"✓ Árbol de categorías generado: {output_path}")
    
    return output_path


@lru_cache(maxsize=1)
def _plantillas() -> Environment:
    # El HTML vive en plantillas/arbol_categorias.html.j2 (N-ALUCARD-03: antes era un f-string de 526
    # líneas en esta función). autoescape: los nombres de los bancos se escapan.
    return Environment(
        loader=FileSystemLoader(Path(__file__).parent / "plantillas"),
        autoescape=True,
        keep_trailing_newline=True,
    )


def generate_html_content(tree: CategoryNode, banco_info: List[dict], total_questions: int) -> str:
    """Genera el contenido HTML completo con la plantilla plantillas/arbol_categorias.html.j2."""
    # «</» dentro del <script> lo cerraría antes de tiempo (una categoría llamada «</script>…»).
    tree_json = json.dumps(tree.to_dict(), ensure_ascii=False, indent=2).replace("</", "<\\/")
    return _plantillas().get_template("arbol_categorias.html.j2").render(
        tree_json=tree_json, banco_info=banco_info, total_questions=total_questions
    )


def main_category_viewer(banco_paths: List[Path], output_path: Optional[Path] = None) -> Path:
    """
    Función principal para generar el visor de categorías.
    
    Args:
        banco_paths: Lista de rutas a archivos de banco de preguntas
        output_path: Ruta donde guardar el HTML (opcional)
        
    Returns:
        Ruta del archivo HTML generado
    """
    if output_path is None:
        output_path = Path("output/category_tree.html")
    
    return generate_html_tree(banco_paths, output_path)
