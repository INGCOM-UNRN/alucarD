# alucarD - Generador de Exámenes

Sistema de generación de exámenes basado en plantillas, YAML y bancos Moodle/GIFT.

## Características

- ✅ **Validación con Pydantic**: Parseo seguro de definiciones YAML
- ✅ **Templating con Jinja2**: Salidas HTML/PDF personalizables
- ✅ **Arquitectura de Plugins**: Extensible vía clases base abstractas
- ✅ **Multiformato**: Lee XML/GIFT, genera HTML/PDF
- ✅ **Categorías Anidadas**: Organización jerárquica con wildcards (`Math/**`)
- ✅ **Filtrado Avanzado**: Por categoría, tipo, etiquetas
- ✅ **Internacionalización**: Soporte para múltiples idiomas
- ✅ **100% Testeado**: Suite completa con cobertura total

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

## Documentación

- 📖 [README.md](README.md) - Este archivo
- 🚀 [QUICKSTART_UV.md](QUICKSTART_UV.md) - Inicio rápido (3 pasos)
- 📚 [INSTALACION.md](INSTALACION.md) - Guía de instalación
- 💡 [EJEMPLOS.md](EJEMPLOS.md) - Ejemplos básicos de uso
- 🎓 [EJEMPLOS_AVANZADOS.md](EJEMPLOS_AVANZADOS.md) - 10 casos de uso avanzados
- 📁 [CATEGORIAS.md](CATEGORIAS.md) - Guía de categorías anidadas
- 🔧 [GUIA_UV.md](GUIA_UV.md) - Guía completa de UV
- 📋 [RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md) - Documentación técnica
- 🧪 [tests/README.md](tests/README.md) - Documentación de tests

## Estado del Proyecto

✅ **Implementación completada** - 100% funcional con tests completos. Consulta `bitacora/` para ver el progreso.

## Licencia

MIT
