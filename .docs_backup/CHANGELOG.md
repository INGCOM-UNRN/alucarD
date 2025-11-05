# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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

### [5.5.0] - Planificado
- 🔄 **Importar desde Banco**: Wizard para importar preguntas
- 📊 **Estadísticas**: Análisis de dificultad y uso
- 🎨 **Temas visuales**: Múltiples estilos CSS

### [6.0.0] - Futuro
- 🌐 **API REST**: Servicio web para generación
- 📱 **Interfaz Web**: UI web completa
- 🔐 **Autenticación**: Sistema de usuarios
- 💾 **Base de datos**: Storage persistente

---

**Para más detalles sobre cada versión, consulta los commits del repositorio.**
