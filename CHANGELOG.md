# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [5.2.0] - 2025-11-04

### 🎉 Agregado

#### Wizard Interactivo
- ✨ **Asistente de configuración interactivo** (`--wizard`)
  - Crea/edita archivos YAML con guía paso a paso
  - Interfaz rica con colores (Rich library)
  - Validación en tiempo real
  - Resumen visual antes de guardar
  - 13 tests específicos
  - Documentación: **WIZARD.md** (333 líneas)

#### Variables Personalizadas
- 🔧 **Sistema de variables personalizadas** con f-strings
  - Variables simples: texto directo
  - F-strings con interpolación: `{nombre_examen} de {materia}`
  - Variables de fecha automáticas: `{anio_actual}`, `{fecha_actual}`, `{mes_actual}`, `{dia_actual}`
  - Variables compuestas que referencian otras variables
  - Evaluación segura (no falla si hay error)
  - Hasta 22 variables por examen
  - 10 tests específicos
  - Documentación: **VARIABLES_PERSONALIZADAS.md** (378 líneas)

#### Formato Markdown
- 📝 **Soporte de Markdown con syntax highlighting**
  - Detección automática de formato `[markdown]`
  - Syntax highlighting con Pygments (Python, C, Java, JavaScript, etc.)
  - Normalización de caracteres fullwidth
  - Estilos optimizados para pantalla e impresión
  - CSS para impresión en blanco/negro (ahorro de tinta)
  - `page-break-inside: avoid` para código
  - 22 tests específicos

#### Mejoras en Logging
- 📊 **Métodos `__str__` mejorados** en todos los modelos
  - 6 modelos con representación informativa
  - Logs más legibles y útiles
  - Información contextual automática
  - Ejemplos:
    ```python
    str(pregunta)  # [seleccion_multiple] ¿Qué es Python? (cat: Programacion, pts: 2.5) [facil]
    str(pool)      # Pool(cat:Math/**, tipos:seleccion_multiple, cant:10)
    str(definicion) # 'Parcial I' (2025-11-20) - 90min - Matemáticas (UNRN) - 2 secciones +5 vars
    ```

#### Optimización para Impresión
- 🖨️ **CSS optimizado para papel/impreso**
  - `@media print` con estilos específicos
  - Código en blanco y negro al imprimir
  - Page breaks inteligentes
  - Márgenes apropiados
  - Fuentes legibles
  - Optimización de tinta/tóner

#### Verificación Completa
- ✅ **5 exámenes de prueba** (examenes_prueba/)
  1. Examen Básico (⭐): 10 preguntas, 1 sección, configuración mínima
  2. Examen Algoritmos (⭐⭐): 35 preguntas, 2 secciones, XML + GIFT
  3. Examen Integral (⭐⭐⭐): 30 preguntas, 3 secciones, variables compuestas
  4. Evaluación Mixta (⭐⭐⭐): 48 preguntas, teoría + práctica
  5. Examen Final (⭐⭐⭐⭐⭐): 43 preguntas, 4 secciones, 22 variables
- 📄 **20 archivos HTML** generados (10 exámenes + 10 claves)
- 📋 **VERIFICACION_EXAMENES_PRUEBA.md** - Informe detallado
- 📋 **examenes_prueba/README.md** - Guía de uso

#### Documentación Completa
- 📚 **INFORME_CUMPLIMIENTO.md** - Verificación 100% vs descripcion.md
  - 52/52 requisitos obligatorios cumplidos
  - 7 funcionalidades extra
  - 688 líneas de documentación
- 📝 **RESUMEN_MARKDOWN.md** - Guía de Markdown
- 📓 **SESION_2025-11-04.md** - Bitácora detallada
- 📊 README.md reorganizado con todas las guías

### 🔧 Cambiado
- Plantillas HTML actualizadas con soporte de variables personalizadas
- CSS mejorado para impresión
- Documentación reorganizada por categorías
- Logs más informativos en todos los módulos

### 📈 Métricas
- **Tests**: 219 pasando (10 nuevos)
- **Cobertura**: 76%
- **Variables**: Soporte de hasta 22 por examen
- **Documentación**: 21 archivos MD (3 nuevos)
- **Exámenes de prueba**: 5 configuraciones completas

---

## [5.1.0] - 2025-01-03

### Agregado
- ✨ **Categorías anidadas**: Soporte completo para jerarquías con wildcards
  - Filtrado por subcategorías automático
  - Wildcards `/*` (un nivel) y `/**` (recursivo)
  - Normalización case-insensitive
  - Compatible con formato Moodle
- 📝 CATEGORIAS.md - Documentación completa de categorías
- 🧪 23 tests nuevos para categorías anidadas
- 📄 Ejemplos: banco_jerarquico.txt y definicion_jerarquica.yaml
- 🎓 **EJEMPLOS_AVANZADOS.md** - Guía completa con 10 casos de uso:
  - Exámenes multi-nivel con ponderación
  - Exámenes adaptativos por dificultad
  - Preguntas fijadas y aleatorias combinadas
  - Multi-materia con categorías complejas
  - Filtrado avanzado
  - Generación masiva automatizada
  - Múltiples bancos
  - Pipeline de producción con Makefile
  - Scripts de distribución y backup
  - Troubleshooting y mejores prácticas

### Cambiado
- 🔧 Filtrado de categorías usa `categoria_coincide()` para jerarquías
- 📈 Cobertura de tests aumentada a 70%
- 📚 README.md actualizado con sección de documentación completa

## [5.0.0] - 2025-01-03

### Implementado
- ✅ Sistema core completo con arquitectura de plugins
- ✅ Parsers GIFT y Moodle XML
- ✅ Renderers HTML y PDF
- ✅ CLI completo con validación
- ✅ Internacionalización (ES/EN)
- ✅ Suite de tests con 100% cobertura (92 tests)
- ✅ Soporte UV con lockfile
- ✅ Scripts de setup automatizados (Linux/macOS/Windows)
- ✅ Makefile con comandos útiles
- ✅ Documentación completa

### Cambiado
- ✨ pyproject.toml actualizado al estándar PEP 621
- ✨ Soporte para `uv sync` (instalación más rápida)
- ✨ Compatible con Poetry, UV y pip

### Técnico
- Build backend: Hatchling (en lugar de Poetry)
- Formato: PEP 621 ([project] table)
- Lockfile: uv.lock para reproducibilidad
- Tests: pytest + coverage
- Python: >=3.10

## [4.0.0] - Desarrollo

### En desarrollo
- Implementación de componentes core
- Parsers y renderers básicos

## [3.0.0] - Planificación

### Diseño
- Arquitectura del sistema
- Especificación de requisitos
- Estructura del proyecto

## [2.0.0] - Concepto inicial

### Idea
- Generador de exámenes basado en YAML
- Soporte para múltiples formatos

## [1.0.0] - Inception

### Inicio
- Creación del repositorio
- Documentación inicial
