# Tests de alucarD

Suite completa de tests con 100% de cobertura del código.

## Estructura de Tests

```
tests/
├── conftest.py           # Configuración y fixtures globales
├── test_models.py        # Tests de modelos Pydantic
├── test_parsers.py       # Tests de parsers (GIFT, XML)
├── test_logic.py         # Tests de lógica de orquestación
├── test_renderers.py     # Tests de renderers (HTML, PDF)
├── test_config.py        # Tests de configuración
├── test_integration.py   # Tests de integración end-to-end
└── bancos_ejemplo/       # Archivos de ejemplo para tests
```

## Ejecutar Tests

### Opción 1: Con script (recomendado)

```bash
./run_tests.sh
```

### Opción 2: Con make

```bash
# Todos los tests con cobertura
make test

# Tests rápidos sin cobertura
make test-fast

# Ver reporte de cobertura
make test-coverage
```

### Opción 3: Con pytest directamente

```bash
# Activar entorno
source .venv/bin/activate

# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=generador_examenes --cov-report=html

# Tests específicos
pytest tests/test_models.py -v
pytest tests/test_parsers.py::TestGiftParser -v
pytest tests/test_logic.py::TestCargarBancos::test_cargar_banco_gift -v

# Tests rápidos (parar al primer fallo)
pytest tests/ -x

# Tests paralelos (requiere pytest-xdist)
pytest tests/ -n auto
```

## Cobertura de Tests

Los tests cubren:

### ✅ Modelos (test_models.py)
- Validación de Opcion
- Validación de Pregunta (todos los tipos)
- Validación de PoolConfig
- Validación de SeccionExamen
- Validación de ConfiguracionExamen
- Validación de DefinicionExamen
- Casos edge y errores de validación

### ✅ Parsers (test_parsers.py)
- GiftParser
  - Selección múltiple
  - Verdadero/Falso
  - Respuesta corta
  - Categorías y etiquetas
  - Comentarios
  - Manejo de errores
- MoodleXMLParser
  - Multichoice
  - TrueFalse
  - Categorías
  - Tags
  - XML inválido
- Registro de parsers

### ✅ Lógica Core (test_logic.py)
- cargar_bancos()
  - Banco GIFT
  - Banco XML
  - Múltiples bancos
  - Errores
- procesar_imagenes()
  - Sin directorio
  - Directorio inexistente
  - Imagen no encontrada
  - Imagen base64
- construir_pool_examen()
  - Filtrado por categoría
  - Filtrado por tipo
  - Filtrado por etiquetas
  - Preguntas fijadas
  - Preguntas insuficientes
  - Puntaje fijo
- mezclar_examen()
  - Mezclar preguntas
  - Mezclar opciones
  - No mezclar
  - Reproducibilidad
- calcular_puntaje_total()

### ✅ Renderers (test_renderers.py)
- HtmlRenderer
  - Inicialización
  - i18n (ES/EN)
  - Renderizar examen
  - Renderizar clave
  - Múltiples temas
- PdfRenderer
  - Inicialización
  - Renderizar examen PDF
  - Renderizar clave PDF
- Registro de renderers

### ✅ Configuración (test_config.py)
- setup_logging()
  - Nivel INFO
  - Nivel DEBUG
  - Handlers
  - Silenciar librerías externas

### ✅ Integración (test_integration.py)
- Flujo completo end-to-end
- Múltiples temas
- Validación de definiciones
- Banco vacío
- Reproducibilidad
- Filtros combinados

## Fixtures Disponibles

Definidos en `conftest.py`:

- `reset_logging`: Limpia configuración de logging
- `sample_gift_content`: Contenido GIFT de ejemplo
- `sample_xml_content`: Contenido XML de ejemplo
- `sample_definicion_yaml`: Definición YAML de ejemplo

## Marcadores

```bash
# Tests unitarios
pytest tests/ -m unit

# Tests de integración
pytest tests/ -m integration

# Tests lentos
pytest tests/ -m slow

# Tests que requieren WeasyPrint
pytest tests/ -m requires_weasyprint
```

## Generar Reporte de Cobertura

```bash
# Ejecutar tests con cobertura
pytest tests/ --cov=generador_examenes --cov-report=html

# Abrir reporte
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Objetivo de Cobertura

**Meta: 100% de cobertura**

Para verificar cobertura actual:

```bash
pytest tests/ --cov=generador_examenes --cov-report=term-missing
```

## CI/CD

Los tests se ejecutan automáticamente en CI con:

```yaml
# Ejemplo para GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest tests/ --cov --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests de PDF fallan

Los tests de PDF requieren WeasyPrint con dependencias del sistema. Si no están instaladas, los tests se saltan automáticamente con `pytest.skip()`.

Para instalar en Ubuntu:
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0
```

### Tests muy lentos

Usa tests paralelos:
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Fixtures no encontrados

Asegúrate de que `conftest.py` existe y está en el directorio `tests/`.
