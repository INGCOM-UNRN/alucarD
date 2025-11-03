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

```bash
# Clonar repositorio
git clone <repo-url>
cd alucard

# Instalar con Poetry
poetry install

# O con pip
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

## Estado del Proyecto

Este proyecto está en desarrollo activo. Consulta `bitacora/` para ver el progreso.

## Licencia

MIT
