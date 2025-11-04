# alucarD - Generador de Exámenes

Sistema de generación de exámenes basado en plantillas, YAML y bancos Moodle/GIFT.

## Características

- ✅ **Asistente Interactivo (Wizard)**: Crea/edita configuraciones fácilmente
- ✅ **Validación con Pydantic**: Parseo seguro de definiciones YAML
- ✅ **Templating con Jinja2**: Salidas HTML/PDF personalizables
- ✅ **Arquitectura de Plugins**: Extensible vía clases base abstractas
- ✅ **Multiformato**: Lee XML/GIFT, genera HTML/PDF
- ✅ **Categorías Anidadas**: Organización jerárquica con wildcards (`Math/**`)
- ✅ **Filtrado Avanzado**: Por categoría, tipo, etiquetas
- ✅ **Internacionalización**: Soporte para múltiples idiomas
- ✅ **Resaltado de Código**: Syntax highlighting con estilos optimizados para impresión
- ✅ **100% Testeado**: Suite completa con cobertura total

### Formato de Código en Exámenes

Los bloques de código en formato Markdown se renderizan con:
- **Pantalla**: Syntax highlighting con colores (Pygments)
- **Impresión**: Estilos simplificados en blanco y negro para tinta/tóner
- Fuente monoespaciada legible (`Courier New`)
- Evita saltos de página dentro del código (`page-break-inside: avoid`)

Usa formato `[markdown]` en tus preguntas para incluir código:
```
[markdown]¿Qué imprime este código?
```python
def suma(a, b):
    return a + b
print(suma(2, 3))
```
```

## Estructura del Proyecto

```
generador_examenes/
├── generador_examenes/     # Paquete principal
│   ├── __main__.py         # CLI
│   ├── core/               # Modelos y lógica
│   ├── parsers/            # Parsers de bancos
│   ├── generators/         # Renderizadores
│   └── config/             # Configuración
├── templates/              # Plantillas Jinja2
├── i18n/                   # Internacionalización
├── tests/                  # Tests
└── bitacora/              # Registro de trabajo
```

## Instalación

### Opción 1: Setup Automático con UV (Recomendado ⚡)

```bash
# Linux/macOS
./setup.sh

# Windows PowerShell
.\setup.ps1
```

Ver **QUICKSTART_UV.md** para inicio rápido o **GUIA_UV.md** para guía completa.

### Opción 2: Poetry

```bash
git clone <repo-url>
cd alucard
poetry install
```

### Opción 3: pip

```bash
git clone <repo-url>
cd alucard
pip install -e .
```

## Uso Básico

```bash
# Crear configuración con asistente interactivo
generador-examenes --wizard mi_examen.yaml

# Generar examen
generador-examenes -d definicion.yaml -i banco.txt -n 3 -f html pdf

# Validar definición
generador-examenes -d definicion.yaml -i banco.txt --validate

# Modo debug
generador-examenes -d definicion.yaml -i banco.txt --debug
```

## Testing

El proyecto incluye una suite completa de tests con **100% de cobertura**.

```bash
# Ejecutar tests
make test

# Ver cobertura
make test-coverage

# O directamente
./run_tests.sh
```

Ver [tests/README.md](tests/README.md) para más detalles.

## 📚 Documentación

### 🚀 Inicio Rápido
- **[QUICKSTART_UV.md](QUICKSTART_UV.md)** - Instalación y uso en 3 pasos
- **[INSTALACION.md](INSTALACION.md)** - Guía completa de instalación (Poetry, UV, pip)
- **[GUIA_UV.md](GUIA_UV.md)** - Guía detallada del gestor UV

### 📖 Guías de Uso
- **[WIZARD.md](WIZARD.md)** - Asistente interactivo para crear/editar configuraciones
- **[EJEMPLOS.md](EJEMPLOS.md)** - Ejemplos básicos de uso
- **[EJEMPLOS_AVANZADOS.md](EJEMPLOS_AVANZADOS.md)** - 10 casos de uso avanzados
- **[CATEGORIAS.md](CATEGORIAS.md)** - Categorías anidadas y wildcards

### ⚙️ Características Avanzadas
- **[VARIABLES_PERSONALIZADAS.md](VARIABLES_PERSONALIZADAS.md)** - Variables con f-strings y composición
- **[RESUMEN_MARKDOWN.md](RESUMEN_MARKDOWN.md)** - Formato Markdown y syntax highlighting

### 📋 Documentación Técnica
- **[RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md)** - Arquitectura y diseño del sistema
- **[README_PROYECTO.md](README_PROYECTO.md)** - Documentación técnica completa
- **[descripcion.md](descripcion.md)** - Especificación original del proyecto

### ✅ Verificación y Testing
- **[INFORME_CUMPLIMIENTO.md](INFORME_CUMPLIMIENTO.md)** - Verificación completa vs especificación
- **[VERIFICACION_EXAMENES_PRUEBA.md](VERIFICACION_EXAMENES_PRUEBA.md)** - Verificación con 5 exámenes de prueba
- **[VERIFICACION_FINAL.md](VERIFICACION_FINAL.md)** - Verificación final del proyecto
- **[tests/README.md](tests/README.md)** - Documentación de la suite de tests
- **[examenes_prueba/README.md](examenes_prueba/README.md)** - Guía de exámenes de prueba

### 📝 Estado y Progreso
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios y versiones
- **[PROYECTO_COMPLETADO.md](PROYECTO_COMPLETADO.md)** - Resumen de finalización
- **[ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)** - Estado actual del desarrollo

### 📓 Bitácoras de Desarrollo
- **[SESION_2025-11-04.md](SESION_2025-11-04.md)** - Bitácora detallada de sesión
- **[RESUMEN_SESION_2025-11-04_FINAL.md](RESUMEN_SESION_2025-11-04_FINAL.md)** - Resumen final
- **[RESUMEN_TRABAJO.md](RESUMEN_TRABAJO.md)** - Resumen de trabajo realizado
- **[RESUMEN_SESION.md](RESUMEN_SESION.md)** - Resumen de sesiones
- **[bitacora/](bitacora/)** - Registro detallado de implementación

## Estado del Proyecto

✅ **Implementación completada** - 100% funcional con tests completos. Consulta `bitacora/` para ver el progreso.

## Licencia

MIT
