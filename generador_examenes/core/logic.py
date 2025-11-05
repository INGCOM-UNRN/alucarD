"""
Lógica de orquestación del generador de exámenes
"""
import random
import logging
import base64
from pathlib import Path
from typing import Dict, List, Any
from copy import deepcopy
import re

from generador_examenes.core.models import (
    Pregunta, DefinicionExamen, SeccionExamen, PoolConfig, ConfiguracionExamen
)
from generador_examenes.parsers import obtener_parser


logger = logging.getLogger(__name__)


def normalizar_categoria(categoria: str) -> str:
    """
    Normaliza una categoría para comparación consistente.
    
    Convierte separadores (/, \\) a formato estándar y elimina espacios.
    
    Args:
        categoria: Categoría a normalizar (ej: "$course$/Math/Algebra")
        
    Returns:
        Categoría normalizada (ej: "$course$/math/algebra")
    """
    if not categoria:
        return ""
    
    # Convertir backslashes a forward slashes
    categoria = categoria.replace("\\", "/")
    
    # Eliminar espacios extras alrededor de slashes
    categoria = re.sub(r'\s*/\s*', '/', categoria)
    
    # Eliminar espacios al inicio y final
    categoria = categoria.strip()
    
    # Normalizar a minúsculas para comparación case-insensitive
    categoria = categoria.lower()
    
    # Eliminar slashes duplicados
    categoria = re.sub(r'/+', '/', categoria)
    
    # Eliminar slash final si existe
    categoria = categoria.rstrip('/')
    
    return categoria


def categoria_coincide(pregunta_cat: str, filtro_cat: str) -> bool:
    """
    Verifica si una categoría de pregunta coincide con un filtro.
    
    Soporta:
    - Coincidencia exacta: "Math/Algebra" == "Math/Algebra"
    - Subcategorías: "Math/Algebra/Linear" coincide con filtro "Math/Algebra"
    - Wildcards: "Math/*" coincide con cualquier subcategoría de Math
    
    Args:
        pregunta_cat: Categoría de la pregunta
        filtro_cat: Categoría del filtro
        
    Returns:
        True si hay coincidencia
    """
    if not filtro_cat:
        return True
    
    # Normalizar ambas categorías
    pregunta_norm = normalizar_categoria(pregunta_cat)
    filtro_norm = normalizar_categoria(filtro_cat)
    
    # Coincidencia exacta
    if pregunta_norm == filtro_norm:
        return True
    
    # Si el filtro termina en /*, permite solo UN nivel de subcategorías
    if filtro_norm.endswith('/*'):
        prefijo = filtro_norm[:-2]  # Quitar /*
        if pregunta_norm.startswith(prefijo + '/'):
            # Verificar que solo haya un nivel más (sin más slashes)
            resto = pregunta_norm[len(prefijo)+1:]  # Lo que viene después del prefijo/
            return '/' not in resto
        return False
    
    # Si el filtro termina en **, permite cualquier nivel de subcategorías
    if filtro_norm.endswith('/**'):
        prefijo = filtro_norm[:-3]  # Quitar /**
        return pregunta_norm.startswith(prefijo + '/') or pregunta_norm == prefijo
    
    # Verificar si la pregunta es subcategoría del filtro
    # Ej: pregunta "Math/Algebra/Linear" coincide con filtro "Math/Algebra"
    if pregunta_norm.startswith(filtro_norm + '/'):
        return True
    
    return False


def cargar_bancos(rutas_bancos: List[Path]) -> Dict[str, Pregunta]:
    """
    Carga múltiples bancos de preguntas y los combina en uno solo
    
    Args:
        rutas_bancos: Lista de rutas a archivos de bancos
        
    Returns:
        Diccionario combinado de todas las preguntas {id: Pregunta}
    """
    banco_completo = {}
    
    for ruta in rutas_bancos:
        logger.info(f"Cargando banco: {ruta}")
        
        try:
            parser = obtener_parser(ruta)
            preguntas = parser.parse(ruta)
            
            # Combinar preguntas, verificando duplicados
            for id_pregunta, pregunta in preguntas.items():
                if id_pregunta in banco_completo:
                    logger.warning(f"Pregunta duplicada encontrada: {pregunta} - sobrescribiendo")
                banco_completo[id_pregunta] = pregunta
            
        except Exception as e:
            logger.error(f"Error cargando banco {ruta}: {e}")
            raise
    
    logger.info(f"Total de preguntas cargadas: {len(banco_completo)}")
    return banco_completo


def procesar_imagenes(banco: Dict[str, Pregunta], path_imagenes: Path | None) -> None:
    """
    Procesa las imágenes en las preguntas, convirtiéndolas a base64
    
    Args:
        banco: Diccionario de preguntas a procesar (se modifica in-place)
        path_imagenes: Directorio donde buscar imágenes
    """
    if not path_imagenes:
        logger.debug("No se especificó directorio de imágenes")
        return
    
    if not path_imagenes.exists():
        logger.warning(f"Directorio de imágenes no existe: {path_imagenes}")
        return
    
    logger.info(f"Procesando imágenes desde: {path_imagenes}")
    
    for pregunta in banco.values():
        # Procesar enunciado
        pregunta.enunciado_html = _embeber_imagenes_en_html(
            pregunta.enunciado_html, 
            path_imagenes
        )
        
        # Procesar opciones
        for opcion in pregunta.opciones:
            opcion.texto_html = _embeber_imagenes_en_html(
                opcion.texto_html,
                path_imagenes
            )


def _embeber_imagenes_en_html(html: str, path_imagenes: Path) -> str:
    """Convierte referencias file:// a imágenes base64 embebidas"""
    
    # Buscar src="file://..." o src="ruta_relativa.jpg"
    pattern = r'src=["\']([^"\']+)["\']'
    
    def reemplazar_src(match):
        src_original = match.group(1)
        
        # Si ya es base64, dejarlo como está
        if src_original.startswith('data:'):
            return match.group(0)
        
        # Limpiar file:// si existe
        ruta_archivo = src_original.replace('file://', '')
        
        # Buscar archivo
        archivo_img = path_imagenes / Path(ruta_archivo).name
        
        if not archivo_img.exists():
            logger.warning(f"Imagen no encontrada: {archivo_img}")
            # Placeholder para imagen faltante
            return 'src="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'100\'%3E%3Crect fill=\'%23ddd\' width=\'100\' height=\'100\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' dominant-baseline=\'middle\' text-anchor=\'middle\'%3E?%3C/text%3E%3C/svg%3E"'
        
        try:
            # Leer y convertir a base64
            with open(archivo_img, 'rb') as f:
                img_data = f.read()
            
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Determinar mime type
            ext = archivo_img.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            return f'src="data:{mime_type};base64,{img_base64}"'
            
        except Exception as e:
            logger.warning(f"Error procesando imagen {archivo_img}: {e}")
            return match.group(0)
    
    return re.sub(pattern, reemplazar_src, html)


def construir_pool_examen(
    definicion: DefinicionExamen, 
    banco: Dict[str, Pregunta]
) -> Dict[str, Any]:
    """
    Construye el pool de preguntas según la definición del examen
    
    Args:
        definicion: Definición del examen con secciones y pools
        banco: Banco completo de preguntas disponibles
        
    Returns:
        Diccionario con estructura del examen y preguntas seleccionadas
    """
    logger.info(f"Construyendo pool de examen: {definicion}")
    
    secciones_examen = []
    
    for idx, seccion_def in enumerate(definicion.secciones_examen, 1):
        logger.info(f"Procesando {seccion_def} ({idx}/{len(definicion.secciones_examen)})")
        
        preguntas_seccion = []
        
        for pool_idx, pool in enumerate(seccion_def.pools, 1):
            logger.debug(f"  Pool {pool_idx}/{len(seccion_def.pools)}")
            preguntas_pool = _filtrar_preguntas_pool(pool, banco)
            preguntas_seccion.extend(preguntas_pool)
        
        secciones_examen.append({
            'nombre': seccion_def.nombre,
            'instrucciones': seccion_def.instrucciones,
            'preguntas': preguntas_seccion,
            'layout': seccion_def.layout
        })
        
        puntaje_total = sum(p.puntaje for p in preguntas_seccion)
        logger.info(
            f"✓ Sección '{seccion_def.nombre}': {len(preguntas_seccion)} preguntas, {puntaje_total} puntos"
        )
    
    return {'secciones': secciones_examen}


def _filtrar_preguntas_pool(pool: PoolConfig, banco: Dict[str, Pregunta]) -> List[Pregunta]:
    """
    Filtra y selecciona preguntas según la configuración del pool
    """
    logger.debug(f"Filtrando preguntas para: {pool}")
    
    # Empezar con todas las preguntas del banco
    candidatas = list(banco.values())
    
    # Filtro 1: Preguntas fijadas
    if pool.preguntas_fijadas:
        fijadas = [banco[id_p] for id_p in pool.preguntas_fijadas if id_p in banco]
        logger.debug(f"  → {len(fijadas)} preguntas fijadas seleccionadas")
        if logger.isEnabledFor(logging.DEBUG):
            for p in fijadas[:3]:
                logger.debug(f"    • {p}")
        return fijadas
    
    # Filtro 2: Categoría o categorías (soporta categorías anidadas)
    if pool.categoria:
        candidatas = [p for p in candidatas if categoria_coincide(p.categoria, pool.categoria)]
        logger.debug(f"  → Filtro categoría '{pool.categoria}': {len(candidatas)} candidatas")
    elif pool.categorias:
        # Filtrar por múltiples categorías (OR lógico)
        candidatas = [
            p for p in candidatas 
            if any(categoria_coincide(p.categoria, cat) for cat in pool.categorias)
        ]
        logger.debug(f"  → Filtro categorías {pool.categorias}: {len(candidatas)} candidatas")
    
    # Filtro 3: Tipos
    if pool.tipos:
        candidatas = [p for p in candidatas if p.tipo in pool.tipos]
        logger.debug(f"  → Filtro tipos {pool.tipos}: {len(candidatas)} candidatas")
    
    # Filtro 4: Etiquetas (debe tener al menos una de las etiquetas)
    if pool.etiquetas:
        candidatas = [
            p for p in candidatas 
            if any(tag in p.etiquetas for tag in pool.etiquetas)
        ]
        logger.debug(f"  → Filtro etiquetas {pool.etiquetas}: {len(candidatas)} candidatas")
    
    # Verificar cantidad
    cantidad_solicitada = pool.cantidad if pool.cantidad else len(candidatas)
    
    if len(candidatas) < cantidad_solicitada:
        mensaje = (
            f"Preguntas insuficientes: se solicitaron {cantidad_solicitada}, "
            f"pero solo hay {len(candidatas)} disponibles"
        )
        
        if pool.accion_si_insuficiente == "error":
            raise ValueError(mensaje)
        elif pool.accion_si_insuficiente == "advertir":
            logger.warning(mensaje)
            cantidad_solicitada = len(candidatas)
        elif pool.accion_si_insuficiente == "usar_todas":
            cantidad_solicitada = len(candidatas)
    
    # Seleccionar preguntas (aún sin mezclar, eso se hace en mezclar_examen)
    seleccionadas = candidatas[:cantidad_solicitada]
    
    # Aplicar puntaje fijo si está especificado
    if pool.puntaje_fijo_por_pregunta:
        for pregunta in seleccionadas:
            pregunta.puntaje = pool.puntaje_fijo_por_pregunta
    
    logger.debug(f"  → {len(seleccionadas)} preguntas seleccionadas del pool")
    if logger.isEnabledFor(logging.DEBUG):
        for p in seleccionadas[:3]:
            logger.debug(f"    • {p}")
        if len(seleccionadas) > 3:
            logger.debug(f"    ... y {len(seleccionadas) - 3} más")
    
    return seleccionadas


def mezclar_examen(
    examen_data: Dict[str, Any], 
    semilla: int, 
    config: ConfiguracionExamen
) -> Dict[str, Any]:
    """
    Mezcla las preguntas y opciones del examen según la configuración
    
    Args:
        examen_data: Datos del examen con secciones y preguntas
        semilla: Semilla para el generador aleatorio
        config: Configuración de mezclado
        
    Returns:
        Nuevo diccionario con el examen mezclado
    """
    logger.debug(f"Mezclando examen con semilla {semilla}")
    
    # Crear copia profunda para no modificar el original
    examen_mezclado = deepcopy(examen_data)
    
    # Configurar generador aleatorio
    rng = random.Random(semilla)
    
    for seccion in examen_mezclado['secciones']:
        # Mezclar preguntas dentro de la sección
        if config.mezclar_preguntas_dentro_seccion:
            rng.shuffle(seccion['preguntas'])
        
        # Mezclar opciones dentro de cada pregunta
        if config.mezclar_opciones_dentro_pregunta:
            for pregunta in seccion['preguntas']:
                if pregunta.tipo in ['seleccion_multiple', 'verdadero_falso']:
                    rng.shuffle(pregunta.opciones)
    
    return examen_mezclado


def calcular_puntaje_total(examen_data: Dict[str, Any]) -> float:
    """
    Calcula el puntaje total del examen
    
    Args:
        examen_data: Datos del examen
        
    Returns:
        Puntaje total
    """
    total = 0.0
    
    for seccion in examen_data.get('secciones', []):
        for pregunta in seccion.get('preguntas', []):
            total += pregunta.puntaje
    
    return total
