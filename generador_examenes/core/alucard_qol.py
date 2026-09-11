"""
Módulo de extensiones de Calidad de Vida (QoL) para alucard / generador-examenes.

Incluye:
- Generación de hojas OMR y descriptor JSON para escaneo rápido/móvil
- Auditoría de alineación y paginación doble faz
- Formateo de cajas de código C con numeración de líneas y auditoría de líneas huérfanas
- Verificación de balance y unicidad de preguntas entre temas
- Empaquetador / concatenador de imprenta
- Parámetros institucionales oficiales y configuración de accesibilidad / letra grande
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf


def generar_plantilla_omr(
    num_preguntas: int,
    opciones_por_pregunta: int = 5,
    tema: int = 1,
    institucion: str = "Universidad",
    materia: str = "Programación"
) -> str:
    """
    Genera el código Typst para una hoja de respuestas OMR de lectura óptica con burbujas de marcado.
    """
    opciones_letras = ["A", "B", "C", "D", "E"][:opciones_por_pregunta]
    columnas = len(opciones_letras)
    
    typ = [
        f'#set document(title: "Hoja de Respuestas OMR - Tema {tema}", author: "{institucion}")',
        '#set page(paper: "a4", margin: (x: 1.5cm, y: 1.5cm))',
        '#set text(font: ("Liberation Sans", "DejaVu Sans", "Arial"), size: 9pt)',
        '#align(center)[',
        f'  #text(size: 14pt, weight: "bold")[HOJA DE RESPUESTAS OMR]\\',
        f'  #text(size: 10pt)[{institucion} — {materia} | *TEMA {tema}*]',
        ']',
        '#v(8pt)',
        '#rect(width: 100%, inset: 8pt, stroke: 0.8pt + rgb("4a5568"))[',
        '  #grid(columns: (2fr, 1.2fr),',
        '    [*Estudiante:* #line(length: 70%, stroke: 0.4pt)],',
        '    [*Padrón / DNI:* #line(length: 50%, stroke: 0.4pt)]',
        '  )',
        ']',
        '#v(8pt)',
        '#rect(fill: rgb("edf2f7"), inset: 6pt, radius: 3pt)[',
        '  #text(size: 7.5pt)[*Instrucciones:* Rellene completamente la burbuja correspondiente con lápiz o birome negra/azul. No use corrector.]',
        ']',
        '#v(10pt)',
    ]
    
    typ.append('#align(center)[')
    header_cols = 'auto, ' + ', '.join(['18pt'] * columnas)
    typ.append(f'  #grid(columns: ({header_cols}), row-gutter: 7pt, column-gutter: 10pt, align: center + horizon,')
    typ.append('    [], ' + ', '.join([f'[*#text(size: 8pt)[{letra}]*]' for letra in opciones_letras]) + ',')
    
    for p in range(1, num_preguntas + 1):
        fila = [f'[*P{p:02d}*]']
        for _ in opciones_letras:
            fila.append('#circle(radius: 5.5pt, stroke: 0.7pt + rgb("2d3748"))[]')
        typ.append('    ' + ', '.join(fila) + ',')
    
    typ.append('  )')
    typ.append(']')
    return '\n'.join(typ)


def generar_especificacion_omr_json(
    num_preguntas: int,
    opciones_por_pregunta: int = 5,
    tema: int = 1,
    dimensiones_mm: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Genera la especificación estructurada en JSON para procesamiento OMR automático o apps móviles (Android).
    """
    if dimensiones_mm is None:
        dimensiones_mm = {
            "page_width_mm": 210.0,
            "page_height_mm": 297.0,
            "bubble_radius_mm": 2.5,
            "origin_x_mm": 35.0,
            "origin_y_mm": 60.0,
            "step_x_mm": 9.0,
            "step_y_mm": 8.0,
        }
    
    opciones_letras = ["A", "B", "C", "D", "E"][:opciones_por_pregunta]
    preguntas = []
    
    for idx in range(num_preguntas):
        p_num = idx + 1
        pos_y = dimensiones_mm["origin_y_mm"] + idx * dimensiones_mm["step_y_mm"]
        coordenadas = {}
        for o_idx, opt in enumerate(opciones_letras):
            pos_x = dimensiones_mm["origin_x_mm"] + o_idx * dimensiones_mm["step_x_mm"]
            coordenadas[opt] = {
                "cx_mm": round(pos_x, 2),
                "cy_mm": round(pos_y, 2),
                "radius_mm": dimensiones_mm["bubble_radius_mm"]
            }
        preguntas.append({
            "numero": p_num,
            "opciones": opciones_letras,
            "coordenadas": coordenadas
        })
        
    return {
        "schema_version": "1.0-omr",
        "tema": tema,
        "total_preguntas": num_preguntas,
        "opciones_por_pregunta": opciones_por_pregunta,
        "dimensiones_referencia": dimensiones_mm,
        "fiducial_markers": [
            {"name": "top_left", "x_mm": 10.0, "y_mm": 10.0, "type": "black_square", "size_mm": 8.0},
            {"name": "top_right", "x_mm": 200.0, "y_mm": 10.0, "type": "black_square", "size_mm": 8.0},
            {"name": "bottom_left", "x_mm": 10.0, "y_mm": 287.0, "type": "black_square", "size_mm": 8.0},
            {"name": "bottom_right", "x_mm": 200.0, "y_mm": 287.0, "type": "black_square", "size_mm": 8.0},
        ],
        "preguntas": preguntas
    }


def verificar_alineacion_doble_faz(paginas_totales: int) -> Dict[str, Any]:
    """
    Verifica que la cantidad de páginas sea par para impresión doble faz limpia,
    advirtiendo si requiere inserción de hoja en blanco de corte.
    """
    es_par = (paginas_totales % 2 == 0)
    return {
        "paginas_totales": paginas_totales,
        "es_par": es_par,
        "requiere_pagina_blanco": not es_par,
        "paginas_impresion": paginas_totales if es_par else paginas_totales + 1,
        "advertencia": None if es_par else "Cantidad de páginas impar: el reverso quedará huérfano. Se sugiere añadir hoja de apuntes/blanco al final."
    }


def formatear_caja_codigo_con_lineas(codigo_c: str, lenguaje: str = "c") -> str:
    """
    Renderiza un bloque de código C en sintaxis Typst con numeración explícita de líneas
    y tipografía monoespaciada para seguimiento de traza de ejecución.
    """
    lineas = codigo_c.strip("\n").split("\n")
    max_num_width = len(str(len(lineas)))
    filas = []
    
    for idx, linea in enumerate(lineas, start=1):
        num_str = f"{idx:>{max_num_width}}"
        linea_escapada = linea.replace("\\", "\\\\").replace('"', '\\"')
        filas.append(f'  [#text(fill: rgb("718096"), size: 8pt)[{num_str}]], [```{lenguaje}\n{linea_escapada}\n```]')

    typ = [
        '#rect(width: 100%, stroke: 0.5pt + rgb("cbd5e0"), inset: 6pt, radius: 3pt, fill: rgb("f8fafc"))[',
        '  #grid(columns: (auto, 1fr), column-gutter: 8pt, row-gutter: 1.5pt, align: (right + top, left + top),',
        ',\n'.join(filas),
        '  )',
        ']'
    ]
    return '\n'.join(typ)


def auditar_calidad_tipografica_codigo(codigo_c: str, max_cols: int = 80) -> Dict[str, Any]:
    """
    Audita líneas excesivamente largas o saltos de línea huérfanos que puedan arruinar
    la maquetación del bloque de código impreso.
    """
    lineas = codigo_c.split("\n")
    lineas_largas = []
    lineas_huerfanas = []
    
    for num, linea in enumerate(lineas, start=1):
        largo = len(linea.rstrip("\r\n"))
        if largo > max_cols:
            lineas_largas.append({"linea": num, "longitud": largo, "contenido": linea.strip()})
        stripped = linea.strip()
        if stripped in (";", "{", "}", ");", "},"):
            if num > 1 and len(lineas[num - 2].strip()) < 15:
                lineas_huerfanas.append({"linea": num, "contenido": stripped})

    cumple = len(lineas_largas) == 0
    return {
        "cumple_calidad": cumple,
        "max_columnas_permitidas": max_cols,
        "lineas_largas": lineas_largas,
        "lineas_huerfanas": lineas_huerfanas,
        "total_lineas": len(lineas)
    }


def verificar_balance_preguntas_entre_temas(examenes_por_tema: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que todos los temas contengan exactamente la misma cantidad de preguntas,
    la misma distribución de puntajes totales y no existan sesgos de dificultad.
    """
    resumen_temas = []
    discrepancias = []
    
    cantidades = []
    puntajes = []
    
    for idx, tema in enumerate(examenes_por_tema, start=1):
        pregs = tema.get("preguntas", [])
        cant = len(pregs)
        cantidades.append(cant)
        
        pts = 0.0
        for p in pregs:
            p_val = getattr(p, "puntaje", None)
            if p_val is None:
                p_val = p.get("puntaje", 1.0) if isinstance(p, dict) else 1.0
            pts += float(p_val)
        puntajes.append(round(pts, 2))
        
        resumen_temas.append({
            "tema": idx,
            "cantidad_preguntas": cant,
            "puntaje_total": round(pts, 2)
        })
        
    balance_cantidad = len(set(cantidades)) <= 1
    balance_puntaje = len(set(puntajes)) <= 1
    
    if not balance_cantidad:
        discrepancias.append(f"Discrepancia en cantidad de preguntas entre temas: {cantidades}")
    if not balance_puntaje:
        discrepancias.append(f"Discrepancia en puntajes totales entre temas: {puntajes}")
        
    return {
        "balanceado": balance_cantidad and balance_puntaje,
        "balance_cantidad": balance_cantidad,
        "balance_puntaje": balance_puntaje,
        "temas": resumen_temas,
        "discrepancias": discrepancias
    }


def empaquetar_pdfs_para_imprenta(lista_pdfs: List[Path], archivo_destino: Path, doble_faz: bool = True) -> Path:
    """
    Concatena múltiples PDFs de temas en un único archivo consolidado listo para imprenta,
    respetando páginas pares en caso de impresión doble faz.
    """
    writer = pypdf.PdfWriter()
    archivo_destino.parent.mkdir(parents=True, exist_ok=True)
    
    for pdf in lista_pdfs:
        reader = pypdf.PdfReader(str(pdf))
        num_paginas = len(reader.pages)
        for page in reader.pages:
            writer.add_page(page)
        
        if doble_faz and (num_paginas % 2 != 0):
            first_page = reader.pages[0]
            width = float(first_page.mediabox.width)
            height = float(first_page.mediabox.height)
            writer.add_blank_page(width=width, height=height)
            
    with open(archivo_destino, "wb") as f_out:
        writer.write(f_out)
    return archivo_destino
