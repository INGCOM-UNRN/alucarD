# alucarD - Generador de Exámenes

Sistema de generación de exámenes basado en plantillas, YAML y bancos Moodle/GIFT.

## Características

- ✅ **Validación con Pydantic**: Parseo seguro de definiciones YAML
- ✅ **Templating con Jinja2**: Salidas HTML/PDF personalizables
- ✅ **Arquitectura de Plugins**: Extensible vía clases base abstractas
- ✅ **Multiformato**: Lee XML/GIFT, genera HTML/PDF
- ✅ **Internacionalización**: Soporte para múltiples idiomas

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

## Estado del Proyecto

✅ **Implementación completada** - 100% funcional con tests completos. Consulta `bitacora/` para ver el progreso.

## Licencia

MIT
