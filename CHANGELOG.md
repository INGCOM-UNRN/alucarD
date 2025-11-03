# Changelog

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
