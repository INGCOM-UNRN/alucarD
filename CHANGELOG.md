# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [5.11.0] - 2026-09-28

### Agregado

- **cli**: cumplir el contrato de línea de comandos de LINEAMIENTOS §3.2 (N-ECO-04) (`f61b796`)

### Documentación

- agregar el texto de la licencia GPL-3.0-or-later que declara pyproject (N-ECO-06) (`f66ea3b`)
- **readme**: enlazar COMPLIANCE_REPORT y descripcion en su ubicación actual (N-ECO-17) (`230b6b1`)
- incorporar manual de uso integral y referencia tecnica (alucarD) (`8712b94`)

### Mantenimiento

- **calidad**: verificar errores de Python y dependencias vulnerables (N-ECO-08, N-ECO-13) (`28b9315`)
- **deps**: mover las dependencias de desarrollo a dependency-groups (N-ECO-07) (`e951848`)
- **deps**: quitar las cotas superiores que fijaban versiones vulnerables (N-ALUCARD-01) (`4a120f2`)

## [5.10.1] - 2025-11-06

### 🐛 Correcciones

#### Parser GIFT - Soporte para $CATEGORY
- ✅ **Directiva `$CATEGORY:`** ahora procesada correctamente
- ✅ **Categorías aplicadas** a todas las preguntas siguientes
- ✅ **Jerarquía completa** en explorador de categorías
- ✅ **Compatible con** formato Moodle GIFT estándar
- ✅ **Mantiene soporte** para `[category: nombre]` inline

**Problema resuelto**: El explorador de categorías mostraba todas las preguntas bajo "General" en lugar de la estructura jerárquica correcta definida con `$CATEGORY:` en archivos GIFT.

**Impacto**: El explorador de categorías ahora muestra correctamente la estructura completa de categorías anidadas (ej: `$course$/top/programacion_1/arrays/arreglos`).

### 📂 Commits
- `a00d4af` - Corrige parser GIFT para soportar formato estándar $CATEGORY

---

## [5.10.0] - 2025-11-06

### ✨ Nuevas Funcionalidades

#### 📋 Configuraciones de Ejemplo
- ✅ **5 configuraciones YAML completas** en `examenes_prueba/`
  - `ejemplo_1_basico.yaml`: Configuración mínima
  - `ejemplo_2_mixto.yaml`: Múltiples layouts y tipos
  - `ejemplo_3_analisis_codigo.yaml`: Layout para código extenso
  - `ejemplo_4_categorias.yaml`: Filtrado avanzado por categorías
  - `ejemplo_5_completo.yaml`: Todas las características disponibles
- ✅ **Demuestran** variables personalizadas, layouts, filtros, etiquetas
- ✅ **Validadas** con bancos reales del proyecto

#### 🔧 Linter GIFT Mejorado
- ✅ **Validación mejorada** con nombre de pregunta en errores
- ✅ **Detecta** formato incorrecto de tags y categorías
- ✅ **Verifica** opciones vacías o sin marcadores válidos
- ✅ **Preserva** bloques de código markdown durante formateo
- ✅ **Normaliza** espacios alrededor de componentes GIFT
- ✅ **Mensajes** de error más descriptivos y contextualizados

### 🐛 Mejoras

#### 📝 Logging Mejorado
- ✅ **Nombre de banco** incluido en warnings del parser GIFT
- ✅ **Conteo de bloques** procesados en mensajes de éxito
- ✅ **Errores contextualizados** con información del archivo fuente
- ✅ **Facilita debugging** de bancos problemáticos

#### 📚 Documentación Consolidada
- ✅ **README.md** y **CHANGELOG.md** como documentación principal
- ✅ **Archivos antiguos** movidos a `.docs_backup/old_root/`
- ✅ **Sección de ejemplos** agregada al README
- ✅ **Reducción de redundancia** en documentación

### 📂 Commits
- `e270712` - Mejora mensajes de logging con información más detallada
- `[hash]` - Agrega 5 configuraciones de ejemplo para verificar funcionalidad
- `7f8dad7` - Consolida documentación: mueve archivos redundantes a backup
- `58c5cee` - Mejora linter GIFT con validaciones adicionales y mejor formato

---

## [5.9.1] - 2025-11-06

### 🐛 Corregido

#### Explorador de Categorías - Clasificación por Tipos
- ✅ **Agregado desglose por tipos de pregunta** en el árbol de categorías
- ✅ **Visualización mejorada** mostrando conteo por tipo (Sel. Múltiple, V/F, Desarrollo, etc.)
- ✅ **Ejemplo de salida**: "15 preguntas (10 Sel. Múltiple | 3 V/F | 2 Desarrollo)"
- ✅ **Estilos CSS** para badges de tipos con formato compacto
- ✅ **Labels traducidos** en español para mejor legibilidad

#### Cambios Técnicos
- Agregado `type_counts: Dict[str, int]` a clase `CategoryNode`
- Método `add_question()` ahora acepta parámetro `question_type`
- Actualizado `build_category_tree()` para pasar tipo de pregunta
- JavaScript del viewer con diccionario `typeLabels` para traducciones
- Nuevo estilo CSS `.type-breakdown` para mostrar desglose inline

---

## [5.9.0] - 2025-11-05

### ✨ Agregado - Explorador de Categorías

#### Nueva Herramienta: Visor de Árbol de Categorías
- ✅ **Generación HTML interactiva** del árbol de categorías de bancos
- ✅ **Visualización jerárquica** con estructura de árbol expandible/colapsable
- ✅ **Contadores de preguntas** por categoría y subcategoría
- ✅ **Botones de copiado** para nombres de categorías al portapapeles
- ✅ **Búsqueda en tiempo real** para filtrar categorías
- ✅ **Interfaz moderna** con gradientes, sombras y animaciones
- ✅ **Responsive design** adaptado a diferentes tamaños de pantalla
- ✅ **Estadísticas globales** de total de preguntas y bancos cargados
- ✅ **Controles de navegación**: Expandir/colapsar todo
- ✅ **Atajos de teclado**: Presiona `/` para enfocar búsqueda

#### Integración en CLI
```bash
# Uso básico
generador-examenes --category-tree bancos/teorico.gift

# Múltiples bancos
generador-examenes --category-tree bancos/*.xml bancos/*.txt

# Con directorio de salida custom
generador-examenes --category-tree bancos/*.xml -o reportes
```

#### Características Técnicas
- **Módulo nuevo**: `generador_examenes/config/category_tree_viewer.py`
- **Estructura de árbol**: Clase `CategoryNode` para representación jerárquica
- **Parser integrado**: Usa el sistema de parsers existente (GIFT, XML)
- **Generación HTML**: Template completo con CSS y JavaScript embebidos
- **Tooltips visuales**: Notificaciones toast al copiar categorías
- **Colores codificados**: Badges para contadores y tipos de archivo

#### Beneficios para el Usuario
1. **Descubrimiento**: Explora qué categorías existen en tus bancos
2. **Planificación**: Ve cuántas preguntas hay disponibles por tema
3. **Configuración rápida**: Copia nombres exactos para tu YAML
4. **Documentación**: Exporta estructura de bancos para referencia
5. **Debugging**: Verifica organización y conteos de preguntas

### 🔧 Modificado
- 📝 **README.md**: Agregada sección "Explorador de Categorías"
- 📝 **CLI (__main__.py)**: Nuevo argumento `--category-tree`
- 📝 **Documentación**: Ejemplos de uso del visor de categorías

### 📊 Estadísticas
- **Tests totales**: 253 (sin cambios)
- **Tests pasando**: 253/253 (100%)
- **Cobertura**: 72% (nueva funcionalidad sin tests por ahora)
- **Líneas de código**: +400 (nuevo módulo category_tree_viewer)

---

## [5.8.0] - 2025-11-05

### ✨ Agregado

#### Mejoras de CSS para Impresión
- ✅ **Optimización de bloques de código**: Bordes simples, fondo blanco, mejor legibilidad
- ✅ **Modo B/N mejorado**: Eliminación completa de colores en impresión para ahorro de tinta
- ✅ **Guardas de markdown**: Estilos específicos para código con bordes simples
- ✅ **Reducción de espacio**: Padding y márgenes optimizados para papel

#### Logging Mejorado
- ✅ **Campo `fuente_banco`**: Agregado a modelo `Pregunta` para trazabilidad
- ✅ **Método `__str__` mejorado**: Más información en logs (banco origen, opciones, tags)
- ✅ **Método `__str__` para `PoolConfig`**: Información detallada de filtros y configuración
- ✅ **Logs con checkmarks**: Uso de ✓ para indicar operaciones exitosas

#### Soporte para Múltiples Categorías
- ✅ **Campo `categorias`**: Lista de categorías en `PoolConfig` (OR lógico)
- ✅ **Filtrado mejorado**: Soporte para `categoria` (single) o `categorias` (multiple)
- ✅ **Wizard actualizado**: Opción para seleccionar múltiples categorías

#### Wizard Mejorado
- ✅ **Selección de layouts**: Interfaz para elegir layout por sección
- ✅ **Descripción de layouts**: Info de densidad y páginas por layout
- ✅ **Soporte categorías múltiples**: Configuración de varias categorías por pool

#### Configuraciones de Exámenes de Prueba
- ✅ **5 exámenes completos** en `examenes_prueba/`:
  - `examen_01_mixto_basico.yaml`: Mixto con 3 secciones y 3 layouts
  - `examen_02_codigo_intensivo.yaml`: Análisis de código profundo
  - `examen_03_compacto_multiple.yaml`: 10 temas con layouts compactos
  - `examen_04_desarrollo_puro.yaml`: Solo preguntas de desarrollo
  - `examen_05_layouts_mixtos.yaml`: Demostración de todos los layouts
- ✅ **Variables personalizadas**: Uso extensivo de f-strings
- ✅ **Configuración completa**: Todos los parámetros en YAML

#### Documentación Consolidada
- ✅ **README.md**: Sección de especificación técnica agregada
- ✅ **Arquitectura de plugins**: Documentación de parsers y renderers
- ✅ **Flujo de ejecución**: Diagrama completo del pipeline
- ✅ **Modelos Pydantic**: Estructura de datos documentada
- ✅ **Limpieza de docs**: Eliminados archivos redundantes, solo README y CHANGELOG

### 🔧 Modificado
- 📝 **Parsers**: `gift_parser.py` y `moodle_parser.py` agregan `fuente_banco` automáticamente
- 📝 **Logic**: Función `_filtrar_preguntas_pool` soporta `categorias` múltiples
- 📝 **Models**: `Pregunta.fuente_banco` agregado como campo opcional

### 🗑️ Eliminado
- 🧹 **Documentación redundante**: 17 archivos markdown consolidados en README.md y CHANGELOG.md
- 🧹 **Backups**: Archivos movidos a `.docs_backup/` para referencia

### 📊 Estadísticas
- **Tests totales**: 253 (sin cambios)
- **Tests pasando**: 253/253 (100%)
- **Cobertura**: 77% (sin cambios)
- **Exámenes de prueba**: 5 configuraciones completas
- **Líneas de documentación**: -15K (consolidación)

---

## [5.7.0] - 2025-11-05

### ✨ Agregado - Configuración en YAML con CLI Override

#### Nueva Funcionalidad: Configuración Completa en YAML
- ✅ **Campos de generación en YAML**: Ahora se puede especificar toda la configuración en el YAML
  - `input_banco`: Lista de rutas a bancos de preguntas
  - `output_dir`: Directorio de salida (default: "./output")
  - `path_images`: Directorio de imágenes (opcional)
  - `numero_temas`: Número de temas a generar (default: 1)
  - `semilla`: Semilla aleatoria (default: 42)
  - `formato`: Lista de formatos de salida (default: ["html"])
- ✅ **CLI Override**: Argumentos de línea de comandos sobrescriben valores del YAML
- ✅ **Uso simplificado**: Ejecutar con solo `-d archivo.yaml` si todo está en el YAML
- ✅ **Backward compatible**: Sigue funcionando con CLI tradicional

#### Ejemplo de Uso
```bash
# Solo con YAML (si todo está configurado)
generador-examenes -d mi_examen.yaml

# Override de opciones específicas
generador-examenes -d mi_examen.yaml -n 5  # Genera 5 temas en vez de lo configurado
generador-examenes -d mi_examen.yaml -f pdf  # Genera PDF en vez de HTML
generador-examenes -d mi_examen.yaml -o ./mis_examenes  # Cambia directorio de salida
```

#### Ejemplo de YAML Completo
```yaml
# Configuración tradicional
nombre_examen: "Parcial de Programación"
institucion: "Universidad Nacional"
materia: "Programación 1"

# Nueva configuración de generación (opcional)
input_banco:
  - "bancos/codigo.xml"
  - "bancos/teorico.gift"
output_dir: "./output"
numero_temas: 3
semilla: 42
formato:
  - "html"
  - "pdf"

secciones_examen:
  - nombre: "Sección 1"
    pools:
      - cantidad: 10
```

### 🔧 Arreglado
- 🐛 Tests actualizados para soportar nueva funcionalidad

### 📊 Estadísticas
- **Tests totales**: 253 (sin cambios)
- **Tests pasando**: 253/253 (100%)
- **Cobertura**: 77% (sin cambios)

---

## [5.6.0] - 2025-11-05

### ✨ Agregado - Modularización de Tipos de Preguntas

#### Nuevo Módulo: `question_types.py`
- ✅ **Enum `QuestionType`** con metadatos completos de cada tipo
- ✅ **Propiedades por tipo**:
  - `display_name`: Nombre legible ("Selección Múltiple", "Verdadero/Falso", etc.)
  - `requires_options`: Indica si requiere opciones de respuesta
  - `supports_partial_credit`: Soporte para puntos parciales
  - `typical_points`: Puntaje sugerido típico
  - `ideal_time_minutes`: Tiempo sugerido para resolver
- ✅ **Conversión Moodle**: Métodos `from_moodle_type()` y `to_moodle_type()`
- ✅ **Registry Pattern**: `QuestionTypeRegistry` para gestión centralizada
- ✅ **Estimación de duración**: `estimate_exam_duration()` basado en tipos y cantidades
- ✅ **Funciones helper**: `is_valid_question_type()`, `get_display_name()`, `requires_options()`

#### Tests
- ✅ **24 nuevos tests** con 100% cobertura del módulo
- ✅ Tests de propiedades, conversiones, registry y helpers
- ✅ Tests de integración con estimación de duración

### 📊 Estadísticas
- **Tests totales**: 253 (↑22 desde 231)
- **Cobertura**: 77% (↑1% desde 76%)
- **Líneas de código**: +420 en nuevos módulos

### 📚 Documentación
- ✅ **COMPLIANCE_REPORT.md**: Reporte completo de cumplimiento con `descripcion.md`
  - 100% cumplimiento confirmado
  - 11 mejoras adicionales documentadas
  - Estado: PRODUCCIÓN READY
- ✅ **Sección "Documentación Adicional"** agregada a README
- ✅ **Documentación consolidada**: Eliminados 4 archivos redundantes
- ✅ **Enlaces cruzados**: Referencias entre documentos principales

### 🔧 Arreglado
- 🐛 Badges de README actualizados con estadísticas correctas (253 tests, 77% coverage)

---

## [5.5.0] - 2025-11-05

### ✨ Agregado - Preguntas de Desarrollo

#### Nuevo Tipo de Pregunta: Desarrollo
- ✅ **Tipo `desarrollo`** agregado a modelo `Pregunta`
- ✅ **Tres tamaños configurables**: `pequeno` (4-6 líneas), `mediano` (8-10 líneas), `grande` (14-16 líneas)
- ✅ **Renderizado visual**: Cajas rectangulares en blanco para que el alumno escriba
- ✅ **Adaptación a layouts**: Se ajusta a default, compact-2col, compact-3col y compact-4col
- ✅ **Optimización de impresión**: Tamaños reducidos automáticamente para ahorrar papel

#### Soporte en Parsers
- ✅ **Parser GIFT**: Formato `{desarrollo}`, `{desarrollo:pequeno}`, `{desarrollo:mediano}`, `{desarrollo:grande}`
- ✅ **Parser Moodle XML**: Mapeo automático de tipo `essay` a `desarrollo`
- ✅ **Detección de tamaño**: Mapeo desde `responseformat` en XML (noinline→pequeno, plain→mediano, editor→grande)

#### Estilos CSS
- ✅ **Clase `.desarrollo-box`** con variantes por tamaño
- ✅ **Estilos de pantalla**: Fondo gris claro, bordes definidos
- ✅ **Estilos de impresión**: Fondo blanco, padding reducido, bordes conservados
- ✅ **Adaptación a layouts**: Reglas específicas para layouts compactos

#### Banco de Preguntas y Ejemplos
- ✅ **Banco `desarrollo.gift`**: 10 preguntas de ejemplo con diferentes tamaños
- ✅ **Examen de verificación**: `examen_layouts_verificacion.yaml` con 7 secciones probando todos los layouts
- ✅ **Documentación completa**: Sección en README.md con ejemplos y uso

### 🔧 Arreglado

#### CSS de Layouts
- 🐛 **Posicionamiento de opciones**: Reglas `grid-column` y `grid-row` limitadas solo a layout default
- 🐛 **Layouts compactos**: Ahora muestran correctamente opciones en columnas debajo del enunciado
- 🐛 **Herencia no deseada**: Eliminada interferencia entre reglas CSS de diferentes layouts

---

## [5.4.0] - 2025-11-04

### ✨ Agregado

#### Variables Personalizadas Mejoradas
- ✅ **Evaluación automática** de variables personalizadas con f-strings
- ✅ **Paso a plantillas**: Variables ahora disponibles en `base_examen.html.j2` y `clave_profesor.html.j2`
- ✅ **Contexto enriquecido**: Variables automáticas de fecha (`fecha_actual`, `anio_actual`, etc.)
- ✅ **Composición de variables**: Referencias entre variables personalizadas
- ✅ **Interpolación flexible**: Acceso a todos los campos de `DefinicionExamen`

#### Configuraciones de Examen de Prueba
- ✅ **5 configuraciones completas** en `examenes_prueba/`:
  - `parcial1_basico.yaml` - Layout compact-2col y compact-3col
  - `parcial2_codigo.yaml` - Análisis de código con layout default
  - `final_completo.yaml` - 3 secciones con layouts mixtos
  - `recuperatorio_mixto.yaml` - Todas las configuraciones combinadas
  - `quiz_rapido.yaml` - Evaluación rápida con compact-4col
- ✅ **Casos de uso reales** para validación de funcionalidad
- ✅ **Diferentes layouts** y configuraciones por archivo

### 🎨 Mejorado

#### CSS de Impresión para Bloques de Código
- 🖨️ **Optimización de espacio**: Line-height reducido (1.4 → 1.3)
- 🖨️ **Mayor legibilidad**: Font-size ajustado (0.9em → 0.8em)
- 🖨️ **Mejor contraste**: Fondo gris suave (#f9f9f9) con borde oscuro
- 🖨️ **Word-wrap mejorado**: `white-space: pre-wrap` y `word-wrap: break-word`
- 🖨️ **Márgenes compactos**: Padding reducido (0.8em → 0.4em)
- 🖨️ **Fuente monoespaciada**: 'Courier New', 'Courier' para código
- 🖨️ **Reducción de párrafos**: Márgenes de párrafo minimizados (0.2em)

#### Mensajes de Logging
- 📊 **Más informativos**: Nombres de archivo en logs de generación
- 📊 **Formato mejorado**: `✓ Examen HTML generado: examen_tema_01.html (tema 1)`
- 📊 **Consistencia**: Uso de símbolos ✓ para operaciones exitosas
- 📊 **Información contextual**: Número de tema incluido en mensajes

### 🔧 Arreglado
- 🐛 Variables personalizadas no se pasaban a templates HTML/PDF
- 🐛 CSS de código en impresión era demasiado espacioso

---

## [5.3.0] - 2025-11-04

### 🎨 Agregado - Layouts de Secciones

#### Sistema de Layouts Múltiples
- ✨ **4 layouts optimizados** para diferentes densidades de contenido:
  
  **Layout `default` (Análisis de Código):**
  - Enunciado: 2/3 ancho, Opciones: 1/3 columna derecha
  - 3-5 preguntas por página
  - Ideal para código extenso y análisis
  
  **Layout `compact-2col` (Dos Columnas):**
  - Enunciado arriba, opciones en 2 columnas abajo
  - 6-10 preguntas por página
  - Ahorro: 30-40% papel
  - Ideal para preguntas teóricas
  
  **Layout `compact-3col` (Tres Columnas):**
  - Enunciado arriba, opciones en 3 columnas abajo
  - 12-20 preguntas por página
  - Ahorro: 50-60% papel
  - Ideal para respuestas cortas
  
  **Layout `compact-4col` (Cuatro Columnas - Máxima Densidad):**
  - Enunciado arriba, opciones en 4 columnas abajo
  - 20-30 preguntas por página
  - Ahorro: 60-70% papel
  - Ideal para Verdadero/Falso

- 🎨 **Layouts mezclables** por sección en el mismo examen
- 📐 **Campo `layout`** en `SeccionExamen` con validación Pydantic
- 🎨 **CSS Grid** para layouts flexibles y responsive
- 📊 **Comparativa visual** y mejores prácticas documentadas

#### Optimización para Impresión
- 🖨️ **Estilos específicos @media print** para layouts compactos:
  - Padding reducido: 1em → 0.3em
  - Margins menores: 1.5em → 0.5em
  - Bordes más delgados: 1px → 0.5px
  - Checkbox más pequeños: 15px → 10px
  - Line-height reducido: 1.6 → 1.2
  - Font-size ajustado: 1em → 0.85em

- 📄 **Page breaks inteligentes** para mantener preguntas completas
- 💾 **Ahorro de tinta** con bordes simplificados
- 📏 **Márgenes optimizados** por layout

---

## [5.2.0] - 2025-11-03

### ✨ Agregado - Asistente Interactivo (Wizard)

#### Funcionalidad del Wizard
- 🧙 **Asistente completo** para crear/editar configuraciones YAML
- 📝 **Modo creación**: Crea nuevas configuraciones desde cero
- ✏️ **Modo edición**: Modifica configuraciones existentes
- 🎨 **Interfaz Rich**: Experiencia visual mejorada con colores y tablas
- ✅ **Validación en tiempo real**: Verifica datos mientras se ingresan
- 📊 **Vista previa**: Resumen completo antes de guardar

#### Flujo del Wizard
1. **Información Básica**
   - Nombre del examen, institución, materia
   - Fecha y duración
   - Instrucciones generales

2. **Configuración de Examen**
   - Mezclar preguntas/opciones
   - Generar clave de profesor
   - Incluir metadata de debug

3. **Secciones del Examen**
   - Agregar/editar secciones
   - Configurar nombre, instrucciones, layout
   - Múltiples secciones soportadas

4. **Pools de Preguntas**
   - Configurar filtros por categoría
   - Tipos de preguntas
   - Etiquetas (tags)
   - Cantidad y puntaje

5. **Variables Personalizadas** (opcional)
   - Definir variables custom
   - Usar f-strings
   - Referencias entre variables

#### Uso
```bash
# Crear nueva configuración
generador-examenes --wizard

# Editar configuración existente
generador-examenes --wizard mi_examen.yaml
```

---

## [5.1.0] - 2025-11-02

### ✨ Agregado - Variables Personalizadas

#### Sistema de Variables
- 🎨 **Variables personalizadas** en configuración YAML
- 🔄 **F-strings**: Interpolación con formato Python `{variable}`
- 📚 **Contexto automático**: Acceso a campos de `DefinicionExamen`
- 🔗 **Composición**: Variables pueden referenciar otras variables
- 📅 **Variables de fecha**: `fecha_actual`, `anio_actual`, `mes_actual`, `dia_actual`

#### Variables Disponibles en Contexto
```python
{
    'nombre_examen': str,
    'institucion': str,
    'materia': str,
    'fecha': str,
    'duracion_minutos': int,
    'idioma': str,
    'fecha_actual': str,
    'anio_actual': int,
    'mes_actual': int,
    'dia_actual': int
}
```

#### Ejemplos de Uso
```yaml
variables_personalizadas:
  profesor: "Dr. García"
  titulo_completo: "{nombre_examen} de {materia}"
  periodo: "Segundo Cuatrimestre {anio_actual}"
  pie_pagina: "{materia} - {profesor} - {periodo}"
```

#### Método en DefinicionExamen
- ✅ `evaluar_variables_personalizadas()`: Evalúa todas las variables
- ✅ **Manejo de errores**: Mantiene valor original si falla evaluación
- ✅ **Logging**: Advertencias para variables que no se pueden evaluar

---

## [5.0.0] - 2025-11-01

### 🎉 Versión Mayor - Refactorización Completa

#### Arquitectura de Plugins
- ✨ **BaseParser ABC**: Clase base para parsers de entrada
- ✨ **BaseRenderer ABC**: Clase base para renderers de salida
- ✨ **Registro automático**: Parsers y renderers se registran automáticamente
- ✨ **Extensible**: Fácil agregar nuevos formatos

#### Validación con Pydantic
- ✅ **Modelos completos**: `Pregunta`, `Opcion`, `PoolConfig`, `SeccionExamen`, `DefinicionExamen`
- ✅ **Validación automática**: Type checking y constraints
- ✅ **Mensajes de error claros**: Detalla problemas de validación
- ✅ **Métodos `__str__` y `__repr__`**: Logging informativo

#### Sistema de Categorías
- 🗂️ **Categorías anidadas**: Organización jerárquica tipo Moodle
- 🔍 **Wildcards**: `*` (un nivel) y `**` (múltiples niveles)
- 🎯 **Filtrado flexible**: Por categoría exacta o subcategorías
- 📊 **Normalización**: Case-insensitive, manejo de separadores

#### Procesamiento de Markdown
- 📝 **Formato `[markdown]`**: Detección automática en GIFT
- 🎨 **Pygments**: Syntax highlighting para código
- 💻 **Múltiples lenguajes**: Python, Java, C++, JavaScript, etc.
- 🔧 **Configuración**: Estilo, numeración de líneas

#### Sistema de Logging
- 📊 **Niveles configurables**: DEBUG, INFO, WARNING, ERROR
- 🐛 **Modo debug**: `--debug` para troubleshooting
- 📝 **Contexto rico**: Módulo, función, mensaje
- ✅ **Logs estructurados**: Fácil parsing y análisis

#### CLI Mejorado
- 🖥️ **argparse**: Interfaz de línea de comandos robusta
- 📚 **Help detallado**: Descripción de cada argumento
- ✅ **Validación de entrada**: Verifica archivos y directorios
- 🎯 **Modo validación**: `--validate` sin generar archivos

#### Internacionalización
- 🌍 **i18n completo**: Español (es) e Inglés (en)
- 📁 **Archivos JSON**: Fácil agregar nuevos idiomas
- 🎨 **Templates**: Uso de variables de idioma en Jinja2
- 🔧 **Extensible**: Sistema simple para agregar traducciones

---

## [4.0.0] - 2025-10-28

### 🎨 Agregado - Templates Jinja2

#### Sistema de Plantillas
- ✨ **Jinja2**: Motor de plantillas flexible
- 📁 **Directorio `templates/`**: Plantillas separadas del código
- 🎨 **Personalizable**: Modifica apariencia sin tocar Python
- 📄 **Múltiples plantillas**: `base_examen.html.j2`, `clave_profesor.html.j2`

#### CSS Optimizado
- 🎨 **Estilos modernos**: CSS Grid y Flexbox
- 📱 **Responsive**: Se adapta a diferentes tamaños
- 🖨️ **Print-friendly**: Estilos específicos para impresión
- 🎨 **Syntax highlighting**: Colores para código

---

## [3.0.0] - 2025-10-20

### ✨ Agregado - Generación PDF

#### WeasyPrint
- 📄 **PDF desde HTML**: Conversión de calidad
- 🎨 **CSS aplicado**: Mantiene estilos visuales
- 📏 **Page breaks**: Inteligentes para preguntas
- 🖨️ **Print-ready**: Listo para imprimir

---

## [2.0.0] - 2025-10-15

### ✨ Agregado - Parser Moodle XML

#### Soporte XML
- 📦 **Parser completo**: Lee archivos XML de Moodle
- 🏷️ **Extracción de tags**: Lee etiquetas de preguntas
- 📁 **Categorías**: Extrae y respeta jerarquía
- 🔧 **Robusto**: Manejo de errores y validación

---

## [1.0.0] - 2025-10-01

### 🎉 Versión Inicial

#### Funcionalidad Básica
- ✅ **Parser GIFT**: Lee archivos GIFT
- ✅ **Generación HTML**: Crea exámenes en HTML
- ✅ **Mezcla aleatoria**: Preguntas y opciones
- ✅ **Múltiples temas**: Genera N versiones
- ✅ **Clave de respuestas**: Para profesores
- ✅ **CLI básico**: Interfaz de línea de comandos

---

## Formato de Versionado

El proyecto sigue **Semantic Versioning** (SemVer):

- **MAJOR** (X.0.0): Cambios incompatibles en la API
- **MINOR** (0.X.0): Nuevas funcionalidades compatibles
- **PATCH** (0.0.X): Correcciones de bugs

### Tipos de Cambios

- **✨ Agregado**: Nuevas funcionalidades
- **🔧 Arreglado**: Correcciones de bugs
- **🎨 Mejorado**: Mejoras a funcionalidad existente
- **🗑️ Deprecado**: Funcionalidad que se eliminará
- **🚫 Eliminado**: Funcionalidad eliminada
- **🔒 Seguridad**: Correcciones de seguridad

---

## Próximas Versiones (Roadmap)

### [5.8.0] - Planificado
- 🔄 **Importar desde Banco**: Wizard para importar preguntas
- 📊 **Estadísticas**: Análisis de dificultad y uso
- 🎨 **Temas visuales**: Múltiples estilos CSS
- 📋 **Plantillas de configuración**: Templates predefinidos de YAML

### [6.0.0] - Futuro
- 🌐 **API REST**: Servicio web para generación
- 📱 **Interfaz Web**: UI web completa
- 🔐 **Autenticación**: Sistema de usuarios
- 💾 **Base de datos**: Storage persistente

---

**Para más detalles sobre cada versión, consulta los commits del repositorio.**
