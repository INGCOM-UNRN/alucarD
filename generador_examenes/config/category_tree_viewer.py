#!/usr/bin/env python3
"""
Visor de Árbol de Categorías de Bancos de Preguntas

Genera una página HTML interactiva mostrando la jerarquía de categorías
de uno o más bancos de preguntas con contadores y botones para copiar nombres.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class CategoryNode:
    """Representa un nodo en el árbol de categorías."""
    
    def __init__(self, name: str, full_path: str):
        self.name = name
        self.full_path = full_path
        self.count = 0
        self.children: Dict[str, CategoryNode] = {}
        
    def add_question(self):
        """Incrementa el contador de preguntas."""
        self.count += 1
        
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
            current.add_question()
    
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


def generate_html_content(tree: CategoryNode, banco_info: List[dict], total_questions: int) -> str:
    """Genera el contenido HTML completo."""
    
    tree_json = json.dumps(tree.to_dict(), ensure_ascii=False, indent=2)
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Árbol de Categorías - alucarD</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            padding: 2rem;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }}
        
        .banco-list {{
            list-style: none;
            margin-top: 0.5rem;
        }}
        
        .banco-list li {{
            padding: 0.25rem 0;
            font-size: 0.9rem;
            color: #666;
        }}
        
        .banco-list .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            margin-left: 0.5rem;
        }}
        
        .tree-container {{
            padding: 2rem;
        }}
        
        .search-box {{
            margin-bottom: 2rem;
            position: relative;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }}
        
        .search-box::before {{
            content: "🔍";
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.2rem;
        }}
        
        .tree {{
            list-style: none;
        }}
        
        .tree-node {{
            margin: 0.5rem 0;
        }}
        
        .node-content {{
            display: flex;
            align-items: center;
            padding: 0.75rem;
            background: #f8f9fa;
            border-radius: 6px;
            transition: all 0.2s;
            cursor: pointer;
        }}
        
        .node-content:hover {{
            background: #e9ecef;
            transform: translateX(4px);
        }}
        
        .node-content.has-children {{
            font-weight: 600;
        }}
        
        .expand-icon {{
            margin-right: 0.5rem;
            font-size: 1rem;
            transition: transform 0.2s;
            user-select: none;
        }}
        
        .expand-icon.expanded {{
            transform: rotate(90deg);
        }}
        
        .category-name {{
            flex: 1;
            font-size: 1rem;
            color: #333;
        }}
        
        .question-count {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}
        
        .copy-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        .copy-btn:hover {{
            background: #218838;
            transform: scale(1.05);
        }}
        
        .copy-btn:active {{
            transform: scale(0.95);
        }}
        
        .copy-btn.copied {{
            background: #007bff;
        }}
        
        .children {{
            margin-left: 2rem;
            border-left: 2px solid #e9ecef;
            padding-left: 1rem;
            display: none;
        }}
        
        .children.expanded {{
            display: block;
        }}
        
        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #28a745;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            display: none;
            animation: slideIn 0.3s;
            z-index: 1000;
        }}
        
        .toast.show {{
            display: block;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        .controls {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .btn {{
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 600;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .hidden {{
            opacity: 0.3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 alucarD - Árbol de Categorías</h1>
            <p>Explora y copia nombres de categorías para tu configuración YAML</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total de Preguntas</h3>
                <div class="value">{total_questions}</div>
            </div>
            <div class="stat-card">
                <h3>Bancos Cargados</h3>
                <div class="value">{len(banco_info)}</div>
                <ul class="banco-list">
                    {"".join(f'<li>📄 {b["name"]} <span class="badge">{b["count"]} preguntas</span></li>' for b in banco_info)}
                </ul>
            </div>
        </div>
        
        <div class="tree-container">
            <div class="controls">
                <button class="btn btn-primary" onclick="expandAll()">Expandir Todo</button>
                <button class="btn btn-secondary" onclick="collapseAll()">Colapsar Todo</button>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Buscar categoría..." oninput="filterTree()">
            </div>
            
            <ul class="tree" id="categoryTree"></ul>
        </div>
    </div>
    
    <div class="toast" id="toast">
        <span id="toastMessage"></span>
    </div>
    
    <script>
        const treeData = {tree_json};
        
        function createTreeNode(node, level = 0) {{
            if (level === 0 && node.name === '(raíz)') {{
                // Skip root node, render only children
                let html = '';
                for (const child of Object.values(node.children)) {{
                    html += createTreeNode(child, 0);
                }}
                return html;
            }}
            
            const hasChildren = Object.keys(node.children).length > 0;
            const expandIcon = hasChildren ? '<span class="expand-icon">▶</span>' : '<span class="expand-icon" style="opacity:0">▶</span>';
            
            let html = '<li class="tree-node" data-path="' + node.full_path.toLowerCase() + '">';
            html += '<div class="node-content' + (hasChildren ? ' has-children' : '') + '" onclick="toggleNode(this)">';
            html += expandIcon;
            html += '<span class="category-name">' + node.name + '</span>';
            
            if (node.count > 0) {{
                html += '<span class="question-count">' + node.count + ' pregunta' + (node.count !== 1 ? 's' : '') + '</span>';
            }}
            
            if (node.full_path) {{
                html += '<button class="copy-btn" onclick="copyCategory(event, \'' + node.full_path.replace(/'/g, "\\\\'") + '\')">📋 Copiar</button>';
            }}
            
            html += '</div>';
            
            if (hasChildren) {{
                html += '<ul class="children">';
                for (const child of Object.values(node.children)) {{
                    html += createTreeNode(child, level + 1);
                }}
                html += '</ul>';
            }}
            
            html += '</li>';
            
            return html;
        }}
        
        function renderTree() {{
            const container = document.getElementById('categoryTree');
            container.innerHTML = createTreeNode(treeData);
        }}
        
        function toggleNode(element) {{
            const children = element.nextElementSibling;
            if (children && children.classList.contains('children')) {{
                children.classList.toggle('expanded');
                const icon = element.querySelector('.expand-icon');
                if (icon) {{
                    icon.classList.toggle('expanded');
                }}
            }}
        }}
        
        function expandAll() {{
            document.querySelectorAll('.children').forEach(el => el.classList.add('expanded'));
            document.querySelectorAll('.expand-icon').forEach(el => el.classList.add('expanded'));
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.children').forEach(el => el.classList.remove('expanded'));
            document.querySelectorAll('.expand-icon').forEach(el => el.classList.remove('expanded'));
        }}
        
        function copyCategory(event, categoryPath) {{
            event.stopPropagation();
            
            navigator.clipboard.writeText(categoryPath).then(() => {{
                showToast('✓ Copiado: ' + categoryPath);
                
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✓ Copiado';
                btn.classList.add('copied');
                
                setTimeout(() => {{
                    btn.innerHTML = originalText;
                    btn.classList.remove('copied');
                }}, 2000);
            }}).catch(err => {{
                showToast('✗ Error al copiar: ' + err.message);
            }});
        }}
        
        function showToast(message) {{
            const toast = document.getElementById('toast');
            const toastMessage = document.getElementById('toastMessage');
            
            toastMessage.textContent = message;
            toast.classList.add('show');
            
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 3000);
        }}
        
        function filterTree() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const nodes = document.querySelectorAll('.tree-node');
            
            if (!searchTerm) {{
                nodes.forEach(node => node.classList.remove('hidden'));
                collapseAll();
                return;
            }}
            
            nodes.forEach(node => {{
                const path = node.getAttribute('data-path');
                const matches = path.includes(searchTerm);
                
                if (matches) {{
                    node.classList.remove('hidden');
                    // Expand parents
                    let parent = node.parentElement;
                    while (parent && parent.classList.contains('children')) {{
                        parent.classList.add('expanded');
                        const prevSibling = parent.previousElementSibling;
                        if (prevSibling) {{
                            const icon = prevSibling.querySelector('.expand-icon');
                            if (icon) icon.classList.add('expanded');
                        }}
                        parent = parent.parentElement.parentElement;
                    }}
                }} else {{
                    node.classList.add('hidden');
                }}
            }});
        }}
        
        // Initialize tree
        renderTree();
        
        // Add keyboard shortcut
        document.addEventListener('keydown', (e) => {{
            if (e.key === '/' && e.target.tagName !== 'INPUT') {{
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html


def main_category_viewer(banco_paths: List[Path], output_path: Path = None) -> Path:
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
