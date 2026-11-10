"""
Parser para formato GIFT (General Import Format Template)
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from generador_examenes.core.models import Pregunta, Opcion
from generador_examenes.parsers.base import BaseParser
from generador_examenes.core.markdown_utils import detect_and_convert_format
from generador_examenes.tablas import proteger_comentarios


def _sin_parrafo(html: str) -> str:
    """Una opción es texto en línea: sin el <p> que agrega Markdown cuando es un solo párrafo."""
    m = re.fullmatch(r"\s*<p>(.*)</p>\s*", html, re.DOTALL)
    return m.group(1) if m and "<p>" not in m.group(1) else html


logger = logging.getLogger(__name__)


def _extraer_bloque_respuestas(texto: str):
    """Localiza el bloque de respuestas GIFT dentro de una pregunta.

    El bloque de respuestas es el ULTIMO grupo balanceado de llaves del texto
    (todo lo anterior puede ser el enunciado, incluyendo codigo C con sus
    propias llaves). Respeta los escapes con barra invertida.

    Devuelve una tupla (antes, contenido, despues) o None si no hay un grupo
    de llaves que cierre al final del texto.
    """
    texto = texto.rstrip()
    if not texto.endswith('}'):
        return None

    # Marcar posiciones de caracteres escapados (\X -> X es literal)
    escapados = set()
    i = 0
    n = len(texto)
    while i < n:
        if texto[i] == '\\':
            escapados.add(i + 1)
            i += 2
        else:
            i += 1

    profundidad = 0
    for j in range(n - 1, -1, -1):
        if j in escapados:
            continue
        ch = texto[j]
        if ch == '}':
            profundidad += 1
        elif ch == '{':
            profundidad -= 1
            if profundidad == 0:
                return texto[:j], texto[j + 1:-1], ''
    return None



# Marcas de GIFT: `=` correcta, `~` incorrecta, `#` retroalimentación. Escapadas con `\` son texto
# (`\=`, `\~`, `\#`, `\{`, `\}`, `\:`), como en `p->sig \=\= NULL`.
_MARCA = re.compile(r'(?<!\\)([=~])')
_RETRO = re.compile(r'(?<!\\)#')
_ESCAPE = re.compile(r'\\([=~#{}:])')
# En el enunciado, lo mismo, salvo adentro de un bloque de código (una tabla no lo es) o de una
# fórmula: en LaTeX `\{` y `\:` tienen su propio sentido.
_ESCAPE_ENUNCIADO = re.compile(r'(?P<intacto>```(?!tabla).*?```|\$\$.*?\$\$|(?<![\\$\w])\$[^$\n]+\$)|\\(?P<marca>[=~#{}:])',
                               re.S)
_VERDADERO_FALSO = re.compile(r'(?:T|F|TRUE|FALSE)\s*(?:#.*)?', re.I | re.S)

# Los metadatos van en un comentario, en el mismo párrafo que la pregunta, sin `:`:
# `// [tag, punteros, facil] [category, Tipos]`. `[tag:x]`, el formato de Moodle, se sigue leyendo.
_ES_COMENTARIO = re.compile(r'\s*//')
_METADATOS = re.compile(r'\[(?:tag|category)[:,]', re.I)
# Por dónde se puede partir la pregunta en el PDF. En el texto queda como un comentario de HTML.
_CORTE = re.compile(r'\s*//\s*\[(corte)\]\s*$', re.I)
_MARCA_DEL_PDF = r'<!--corte-->'
_TAG = re.compile(r'\[tag(?P<separador>[:,])(?P<tags>(?:\\\]|[^\]<>`\x00-\x1f])+)\]', re.I)
_CATEGORIA = re.compile(r'\[category[:,]\s*(.+?)\s*\]', re.I)
# El tamaño del espacio de un desarrollo: `{}` es el ensayo de Moodle y no admite parámetros, así que
# viaja como etiqueta.
_TAMANO = re.compile(r'desarrollo-(cero|chico|pequeno|mediano|grande|pagina|página)', re.I)
# La sintaxis anterior, que Moodle no entiende: lo que sigue a las respuestas lo toma como texto de la
# pregunta y `{desarrollo}` como respuesta corta. Se sigue leyendo; `lint-gift --fix` la migra.
_SINTAXIS_VIEJA = re.compile(
    r'^[ \t]*//.*$'
    r'|[ \t]*\[(?P<clave>tags?|category):\s*(?P<valor>[^\]\n]+?)\s*\][ \t]*'
    r'|(?P<desarrollo>\{\s*desarrollo(?::(?P<tamano>\w+))?\s*\})',
    re.I | re.M)


def sintaxis_vieja(contenido: str) -> list[re.Match]:
    """Los `[tags: …]`, `[category: …]` y `{desarrollo…}` de un banco, sin mirar los comentarios."""
    return [m for m in _SINTAXIS_VIEJA.finditer(contenido) if m.group('clave') or m.group('desarrollo')]


def _desescapar(texto: str) -> str:
    return _ESCAPE.sub(r'\1', texto)


def _desescapar_enunciado(texto: str) -> str:
    def desescapar(m: re.Match) -> str:
        intacto = m.group('intacto')
        if intacto is None:
            return m.group('marca')
        # En el código también vale `\:`, como en Moodle; en una fórmula es un espacio de LaTeX.
        return intacto.replace('\\:', ':') if intacto.startswith('```') else intacto

    return _ESCAPE_ENUNCIADO.sub(desescapar, texto)

class GiftParser(BaseParser):
    """Parser para archivos en formato GIFT de Moodle"""
    
    @staticmethod
    def get_supported_extensions() -> list[str]:
        return ['.txt', '.gift']
    
    def parse(self, filepath: Path) -> Dict[str, Pregunta]:
        """
        Parsea un archivo GIFT y retorna un diccionario de preguntas
        
        Formato GIFT básico:
        // [tag, tag1, tag2]
        ::nombre_pregunta::enunciado {opciones}
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
        
        logger.info(f"Parseando archivo GIFT: {filepath}")
        
        preguntas = {}
        banco_nombre = filepath.name
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if sintaxis_vieja(content):
                logger.warning(f"[{banco_nombre}] Usa [tags: …], [category: …] o {{desarrollo}}, que Moodle no "
                               "entiende: migralo con `alucard lint-gift --fix`.")

            # Dividir en bloques de preguntas (separadas por líneas en blanco)
            bloques = self._dividir_bloques(proteger_comentarios(content))
            
            for i, (bloque, categoria) in enumerate(bloques):
                try:
                    pregunta = self._parsear_bloque(bloque, i, banco_nombre, categoria)
                    if pregunta:
                        preguntas[pregunta.id] = pregunta
                except Exception as e:
                    logger.warning(f"[{banco_nombre}] Error en bloque {i+1}: {e}")
                    continue
            
            logger.info(f"✓ [{filepath.name}] {len(preguntas)} preguntas cargadas correctamente de {len(bloques)} bloques procesados")
            
        except Exception as e:
            raise ValueError(f"Error leyendo archivo GIFT: {e}") from e
        
        return preguntas
    
    def _dividir_bloques(self, content: str) -> list[tuple[str, str]]:
        """
        Divide el contenido en bloques de preguntas con su categoría.
        
        Returns:
            Lista de tuplas (bloque_texto, categoria_actual)
        """
        # Eliminar comentarios (líneas que empiezan con //), salvo los que llevan metadatos
        lines = [line for line in content.split('\n')
                 if not _ES_COMENTARIO.match(line) or _METADATOS.search(line) or _CORTE.match(line)]

        bloques = []
        bloque_actual: List[str] = []
        categoria_actual = "General"
        linea_previa_vacia = False

        def inicia_pregunta(linea: str) -> bool:
            """Una línea en blanco sólo corta bloque si la siguiente inicia pregunta.

            Esto preserva bloques de código (C, etc.) dentro del enunciado,
            que suelen contener líneas vacías.
            """
            s = linea.lstrip()
            return s.startswith('::') or s.startswith('$CATEGORY:') or \
                (s.startswith('//') and not _CORTE.match(linea)) or \
                s.startswith('[markdown]') or s.startswith('[html]')

        for line in lines:
            stripped = line.strip()

            # Detectar cambio de categoría
            if stripped.startswith('$CATEGORY:'):
                # Guardar bloque actual si existe antes de cambiar categoría
                if bloque_actual:
                    bloques.append(('\n'.join(bloque_actual), categoria_actual))
                    bloque_actual = []

                # Actualizar categoría actual
                categoria_actual = stripped[10:].strip()  # Remover "$CATEGORY:"
                linea_previa_vacia = False
                continue

            # Procesar líneas de contenido
            if stripped == '':
                linea_previa_vacia = True
            else:
                if linea_previa_vacia and bloque_actual and inicia_pregunta(line):
                    bloques.append(('\n'.join(bloque_actual), categoria_actual))
                    bloque_actual = []
                bloque_actual.append(line)
                linea_previa_vacia = False
        
        # Agregar último bloque si existe
        if bloque_actual:
            bloques.append(('\n'.join(bloque_actual), categoria_actual))
        
        return bloques
    
    def _parsear_bloque(self, bloque: str, indice: int, banco_nombre: Optional[str] = None, categoria_actual: str = "General") -> Pregunta | None:
        """
        Parsea un bloque individual de pregunta GIFT.
        
        Args:
            bloque: Texto del bloque de pregunta
            indice: Índice del bloque
            banco_nombre: Nombre del archivo de banco
            categoria_actual: Categoría aplicada a esta pregunta desde $CATEGORY
        """
        lineas = bloque.split('\n')
        comentarios = '\n'.join(linea for linea in lineas if _ES_COMENTARIO.match(linea))
        bloque = '\n'.join(f'\n<!--{marca.group(1).lower()}-->\n' if (marca := _CORTE.match(linea)) else linea
                           for linea in lineas if _CORTE.match(linea) or not _ES_COMENTARIO.match(linea))
        # Una marca arriba del título o después de las respuestas no corta nada.
        bloque = re.sub(rf'^(?:\s*{_MARCA_DEL_PDF})+|(?:{_MARCA_DEL_PDF}\s*)+$', '', bloque.strip()).strip()
        if not bloque:
            return None

        # Extraer nombre de pregunta ::nombre::
        nombre_match = re.match(r'^::(.+?)::', bloque)
        nombre = nombre_match.group(1) if nombre_match else f"pregunta_{indice + 1}"
        
        # Remover el nombre del bloque
        if nombre_match:
            bloque = bloque[nombre_match.end():].strip()
        
        etiquetas = [tag.strip().replace('\\]', ']') for m in _TAG.finditer(comentarios)
                     for tag in (m['tags'].split(',') if m['separador'] == ',' else [m['tags']])]
        tamano = next((m.group(1).lower() for m in map(_TAMANO.fullmatch, etiquetas) if m), None)
        etiquetas = [tag for tag in etiquetas if not _TAMANO.fullmatch(tag)]

        # Sintaxis anterior: [tags: tag1, tag2]
        tags_match = re.search(r'\[tags?:\s*(.+?)\]', bloque, re.IGNORECASE)
        if tags_match:
            etiquetas += [tag.strip() for tag in tags_match.group(1).split(',')]
            bloque = bloque[:tags_match.start()] + bloque[tags_match.end():]
        
        # Extraer formato [markdown] o [html]
        formato = 'plain'
        format_match = re.search(r'\[(markdown|html|moodle_auto_format)\]', bloque, re.IGNORECASE)
        if format_match:
            formato = format_match.group(1).lower()
            bloque = bloque[:format_match.start()] + bloque[format_match.end():]
        
        # Usar categoría actual por defecto, pero permitir override con `// [category, nombre]`
        categoria_comentario = _CATEGORIA.search(comentarios)
        categoria = categoria_comentario.group(1) if categoria_comentario else categoria_actual
        cat_match = _CATEGORIA.search(bloque)
        if cat_match:
            categoria = cat_match.group(1).strip()
            bloque = bloque[:cat_match.start()] + bloque[cat_match.end():]
        
        # Buscar el bloque de respuestas: el último grupo balanceado de llaves
        # (tolera código C embebido en el enunciado, con sus propias llaves).
        partes = _extraer_bloque_respuestas(bloque.strip())
        if not partes:
            logger.warning(f"[{banco_nombre}] Pregunta '{nombre}' omitida: no se encontraron opciones entre {{ }}. Revisar formato GIFT.")
            return None
        
        enunciado, opciones_str, _sobrante = partes
        enunciado = enunciado.strip()
        opciones_str = re.sub(_MARCA_DEL_PDF, '', opciones_str).strip()
        # Convertir el enunciado según el formato
        enunciado = detect_and_convert_format(_desescapar_enunciado(enunciado), formato)
        
        # Determinar tipo de pregunta y parsear opciones
        tamano_desarrollo = None
        if opciones_str.lower() in ['', 'desarrollo', 'desarrollo:pequeno', 'desarrollo:mediano', 'desarrollo:grande']:
            # Pregunta de desarrollo: `{}`, el ensayo de Moodle
            tipo = "desarrollo"
            opciones = []
            tamano_desarrollo = opciones_str.split(':')[1].lower() if ':' in opciones_str else tamano
        elif _VERDADERO_FALSO.fullmatch(opciones_str):
            # Verdadero/Falso: {T}, {F}, {TRUE} o {FALSE}; {TAD} o {FIFO} son respuestas cortas
            tipo = "verdadero_falso"
            opciones = self._parsear_verdadero_falso(opciones_str)
        elif '~' in _MARCA.findall(opciones_str):
            # Selección múltiple: tiene opciones incorrectas. Sólo con `=` son las respuestas
            # aceptadas de una respuesta corta: {=opaco =tipo opaco}
            tipo = "seleccion_multiple"
            opciones = self._parsear_seleccion_multiple(opciones_str, formato)
        elif opciones_str.startswith('#'):
            # Numérica
            tipo = "numerica"
            opciones = []
        else:
            # Respuesta corta o ensayo
            tipo = "respuesta_corta"
            opciones = self._parsear_respuesta_corta(opciones_str, formato)
        
        pregunta = Pregunta(
            id=f"gift_{indice + 1}_{nombre.replace(' ', '_')}",
            tipo=tipo,  # type: ignore[arg-type]  # pydantic valida el literal
            nombre=nombre,
            categoria=categoria,
            enunciado_html=enunciado,
            puntaje=1.0,
            opciones=opciones,
            etiquetas=etiquetas,
            tamano_desarrollo=tamano_desarrollo,  # type: ignore[arg-type]  # pydantic valida el literal
            fuente_banco=banco_nombre
        )
        
        return pregunta
    
    def _parsear_seleccion_multiple(self, opciones_str: str, formato: str = 'plain') -> list[Opcion]:
        """Parsea opciones de selección múltiple"""
        opciones = []
        
        # Dividir por = (correcta) o ~ (incorrecta); `\=` y `\~` son parte del texto.
        partes = _MARCA.split(opciones_str)
        
        for i in range(1, len(partes), 2):
            if i + 1 < len(partes):
                marcador = partes[i]
                texto = partes[i + 1].strip()
                
                # Remover retroalimentación si existe (después de un # sin escapar)
                texto = _desescapar(_RETRO.split(texto)[0].strip())

                es_correcta = (marcador == '=')
                
                if texto:
                    # Convertir el texto según el formato
                    texto_html = _sin_parrafo(detect_and_convert_format(texto, formato))
                    opciones.append(Opcion(
                        texto_html=texto_html,
                        es_correcta=es_correcta
                    ))
        
        return opciones
    
    def _parsear_verdadero_falso(self, opciones_str: str) -> list[Opcion]:
        """Parsea opciones de verdadero/falso"""
        es_verdadero = opciones_str.strip().upper().startswith('T')
        
        return [
            Opcion(texto_html="Verdadero", es_correcta=es_verdadero),
            Opcion(texto_html="Falso", es_correcta=not es_verdadero)
        ]
    
    def _parsear_respuesta_corta(self, opciones_str: str, formato: str = 'plain') -> list[Opcion]:
        """Parsea opciones de respuesta corta"""
        opciones = []
        
        # En respuesta corta, las respuestas correctas empiezan con =
        partes = _MARCA.split(opciones_str)
        respuestas = [partes[i + 1] for i in range(1, len(partes) - 1, 2) if partes[i] == '=']

        for respuesta in respuestas:
            texto = _desescapar(_RETRO.split(respuesta)[0].strip())
            if texto:
                # Convertir el texto según el formato
                texto_html = detect_and_convert_format(texto, formato)
                opciones.append(Opcion(
                    texto_html=texto_html,
                    es_correcta=True
                ))
        
        # Si no hay respuestas marcadas, considerar todo el contenido
        if not opciones:
            texto_html = detect_and_convert_format(opciones_str.strip(), formato)
            opciones.append(Opcion(
                texto_html=texto_html,
                es_correcta=True
            ))
        
        return opciones
