# Guía de Instalación - alucarD

## Requisitos

- Python 3.10 o superior
- pip o poetry para gestión de dependencias

## Instalación con pip

```bash
# Clonar el repositorio
git clone <repo-url>
cd alucard

# Instalar dependencias
pip install pydantic pyyaml jinja2 weasyprint

# Instalar el paquete en modo desarrollo
pip install -e .
```

## Instalación con Poetry

```bash
# Clonar el repositorio
git clone <repo-url>
cd alucard

# Instalar con Poetry
poetry install

# Activar el entorno virtual
poetry shell
```

## Verificación de la Instalación

```bash
# Verificar que el comando está disponible
generador-examenes --help

# O ejecutar como módulo
python -m generador_examenes --help
```

## Dependencias del Sistema

Para generar PDFs, WeasyPrint requiere algunas librerías del sistema:

### Ubuntu/Debian
```bash
sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### macOS
```bash
brew install cairo pango gdk-pixbuf libffi
```

### Windows
Las dependencias suelen instalarse automáticamente con pip. Si hay problemas, consulta la [documentación de WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

## Prueba Rápida

```bash
# Ir al directorio de tests
cd tests/bancos_ejemplo

# Validar la definición
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  --validate

# Generar examen de prueba
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  -o ../../output \
  -n 2 \
  -f html
```

## Troubleshooting

### Error: "No module named 'pydantic'"
Instala las dependencias: `pip install pydantic pyyaml jinja2 weasyprint`

### Error al generar PDF
1. Verifica que WeasyPrint esté instalado: `pip show weasyprint`
2. Instala las dependencias del sistema (ver arriba)
3. Si persiste el error, genera solo HTML: `-f html`

### Error: "Parser not found"
Verifica que los archivos de banco tengan la extensión correcta:
- `.txt` o `.gift` para formato GIFT
- `.xml` para formato Moodle XML
