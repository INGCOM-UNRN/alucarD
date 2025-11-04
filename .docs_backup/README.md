# alucarD - Generador de Exámenes 🎓

**Sistema profesional de generación de exámenes** basado en plantillas YAML, con soporte para bancos Moodle/GIFT, múltiples layouts y optimización para impresión.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-228%20passing-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-76%25-green.svg)](htmlcov/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Características Principales

### ⚡ Core Features
- ✅ **Asistente Interactivo (Wizard)**: Crea/edita configuraciones YAML con interfaz guiada
- ✅ **Múltiples Layouts**: 3 layouts optimizados para diferentes tipos de contenido
- ✅ **Variables Personalizadas**: Sistema de variables con f-strings y composición
- ✅ **Validación con Pydantic**: Parseo seguro de definiciones YAML
- ✅ **Templating con Jinja2**: Salidas HTML/PDF personalizables
- ✅ **Arquitectura de Plugins**: Extensible vía clases base abstractas

### 📐 Layouts de Secciones
- **`default`**: Enunciado extenso + opciones laterales (ideal para código)
  - 3-5 preguntas/página | Uso: 100%
- **`compact-2col`**: Enunciado arriba + 2 columnas de opciones
  - 6-10 preguntas/página | Ahorro: 30-40% papel
- **`compact-3col`**: Enunciado arriba + 3 columnas de opciones
  - 12-20 preguntas/página | Ahorro: 50-60% papel

### 📝 Formato y Procesamiento
- ✅ **Multiformato**: Lee XML/GIFT, genera HTML/PDF
- ✅ **Categorías Anidadas**: Organización jerárquica con wildcards (`Math/**`)
- ✅ **Filtrado Avanzado**: Por categoría, tipo, etiquetas
- ✅ **Resaltado de Código**: Syntax highlighting con Pygments
- ✅ **Markdown Support**: Formato `[markdown]` con código embebido
- ✅ **Internacionalización**: ES/EN con sistema extensible

### 🖨️ Optimización para Impresión
- ✅ **CSS @media print**: Estilos automáticos para papel
- ✅ **Modo B/N**: Código en blanco y negro (ahorro de tinta)
- ✅ **Page Breaks**: Inteligentes para mantener preguntas completas
- ✅ **Márgenes Optimizados**: 1.5cm en impresión vs 2cm en pantalla
- ✅ **Fuentes Legibles**: Tamaños y espaciado optimizados

### 🧪 Calidad y Testing
- ✅ **228 Tests**: Suite completa con pytest
- ✅ **76% Coverage**: Cobertura de código
- ✅ **5 Exámenes de Prueba**: Validación en escenarios reales
- ✅ **CI Ready**: Configurado para integración continua

---

## 🚀 Instalación

### Opción 1: Setup Automático con UV (⚡ Recomendado)

```bash
# Linux/macOS
./setup.sh

# Windows PowerShell
.\setup.ps1
```

**UV** es ~10-100x más rápido que pip/Poetry. Ver [GUIA_UV.md](GUIA_UV.md) para detalles.

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

Ver [INSTALACION.md](INSTALACION.md) para más opciones.

---

## 💡 Inicio Rápido

### 1️⃣ Crear Configuración con Wizard

```bash
generador-examenes --wizard mi_examen.yaml
```

El asistente interactivo te guía paso a paso:
- Información básica del examen
- Configuración de secciones
- Pools de preguntas
- Variables personalizadas
- Vista previa antes de guardar

### 2️⃣ Generar Examen

```bash
generador-examenes \
  -d mi_examen.yaml \
  -i bancos/preguntas.xml \
  -n 3 \
  -f html pdf
```

**Parámetros:**
- `-d`: Definición YAML del examen
- `-i`: Banco(s) de preguntas (XML/GIFT)
- `-n`: Número de temas a generar
- `-f`: Formatos de salida (html, pdf)

### 3️⃣ Resultado

```
output/mi_examen/
├── examen_tema_01.html
├── examen_tema_01.pdf
├── clave_tema_01.html
├── clave_tema_01.pdf
├── examen_tema_02.html
├── ...
```

---

## 📐 Layouts - Optimización de Papel

### Ejemplo: Examen con Múltiples Layouts

```yaml
nombre_examen: "Parcial de Programación"
institucion: "UNRN - Sede Andina"
materia: "Algoritmos y Estructuras de Datos"

secciones_examen:
  # Código extenso: layout default
  - nombre: "Parte 1: Análisis de Algoritmos"
    layout: default
    pools:
      - cantidad: 5
        tipos: ["seleccion_multiple"]
  
  # Teoría: layout compacto 2 columnas
  - nombre: "Parte 2: Conceptos Fundamentales"
    layout: compact-2col
    pools:
      - cantidad: 10
  
  # Definiciones: layout ultra-compacto 3 columnas
  - nombre: "Parte 3: Definiciones Rápidas"
    layout: compact-3col
    pools:
      - cantidad: 15
```

**Ahorro estimado:** 50% de papel vs solo layout default

### Comparativa Visual

| Layout | Distribución | Preguntas/Pág | Ahorro |
|--------|--------------|---------------|--------|
| `default` | 2/3 + 1/3 horizontal | 3-5 | - |
| `compact-2col` | Arriba + 2 cols | 6-10 | 30-40% |
| `compact-3col` | Arriba + 3 cols | 12-20 | 50-60% |

---

## 🔧 Variables Personalizadas

Sistema de variables con **f-strings** y **composición**:

```yaml
variables_personalizadas:
  # Variables simples
  profesor: "Prof. García"
  aula: "Aula 301"
  
  # F-strings con interpolación
  info_completa: "{nombre_examen} de {materia}"
  
  # Variables de fecha automáticas
  anio: "{anio_actual}"
  fecha: "{fecha_actual}"
  
  # Composición de variables
  titulo: "Examen: {info_completa} ({fecha})"
```

**Variables automáticas disponibles:**
- `{anio_actual}`: 2025
- `{mes_actual}`: Noviembre
- `{dia_actual}`: 4
- `{fecha_actual}`: 2025-11-04
- `{nombre_examen}`, `{materia}`, `{institucion}`: Del YAML

Hasta **22 variables** por examen. Ver [VARIABLES_PERSONALIZADAS.md](VARIABLES_PERSONALIZADAS.md).

---

## 📝 Formato Markdown con Código

Incluye código con syntax highlighting:

```markdown
[markdown]¿Qué imprime este código?

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(5))
```
```

**Resultado:**
- **Pantalla**: Colores con Pygments
- **Impresión**: Blanco/negro (ahorra tinta)
- **Lenguajes**: Python, C, C++, Java, JavaScript, Go, Rust, SQL, etc.

Ver [RESUMEN_MARKDOWN.md](RESUMEN_MARKDOWN.md) para detalles.

---

## 📂 Estructura del Proyecto

```
alucard/
├── generador_examenes/        # Paquete principal
│   ├── __main__.py            # CLI con argparse
│   ├── core/
│   │   ├── models.py          # Modelos Pydantic
│   │   ├── logic.py           # Lógica de construcción
│   │   └── markdown_utils.py  # Procesamiento Markdown
│   ├── parsers/
│   │   ├── gift_parser.py     # Parser GIFT
│   │   └── moodle_parser.py   # Parser Moodle XML
│   ├── generators/
│   │   ├── html_renderer.py   # Renderizador HTML
│   │   └── pdf_renderer.py    # Renderizador PDF
│   └── config/
│       ├── exam_wizard.py     # Asistente interactivo
│       └── logging_config.py  # Configuración de logs
├── templates/                 # Plantillas Jinja2
│   └── base_examen.html.j2    # Template con 3 layouts
├── i18n/                      # Internacionalización
│   ├── es.json                # Español
│   └── en.json                # Inglés
├── tests/                     # Suite de tests
│   ├── test_layouts.py        # Tests de layouts
│   ├── test_variables_personalizadas.py
│   ├── test_markdown_utils.py
│   └── ...
├── bancos/                    # Bancos de ejemplo
│   ├── codigo.xml
│   ├── algoritmos.xml
│   └── teorico.gift
├── examenes_prueba/           # 5 configuraciones de prueba
│   ├── examen_01_basico.yaml
│   ├── examen_06_layouts.yaml
│   └── README.md
└── output/                    # Exámenes generados
```

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Examen Básico

```yaml
nombre_examen: "Quiz de Python"
institucion: "UNRN"
materia: "Programación 1"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true

secciones_examen:
  - nombre: "Conceptos Básicos"
    pools:
      - cantidad: 10
        tipos: ["seleccion_multiple"]
```

```bash
generador-examenes -d quiz.yaml -i banco.gift -n 1
```

### Ejemplo 2: Examen con Categorías Jerárquicas

```yaml
secciones_examen:
  - nombre: "Matemáticas - Todos los Niveles"
    pools:
      - cantidad: 20
        categorias: ["Math/**"]  # Recursivo
  
  - nombre: "Solo Álgebra Avanzada"
    pools:
      - cantidad: 10
        categorias: ["Math/Algebra/Advanced"]
```

### Ejemplo 3: Examen Multi-Materia

```yaml
secciones_examen:
  - nombre: "Programación"
    pools:
      - cantidad: 15
        categorias: ["Programming/**"]
        tipos: ["seleccion_multiple"]
  
  - nombre: "Algoritmos"
    pools:
      - cantidad: 10
        categorias: ["Algorithms/**"]
        tipos: ["verdadero_falso"]
```

Ver [EJEMPLOS.md](EJEMPLOS.md) y [EJEMPLOS_AVANZADOS.md](EJEMPLOS_AVANZADOS.md) para más casos.

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
make test

# Con cobertura
make test-coverage

# Tests específicos
pytest tests/test_layouts.py -v

# O directamente
./run_tests.sh
```

### Métricas

- **228 tests** pasando
- **76% coverage**
- **0 fallos** en suite completa
- Tests para:
  - Parsers (GIFT, Moodle XML)
  - Renderers (HTML, PDF)
  - Layouts (3 tipos)
  - Variables personalizadas
  - Markdown y código
  - Categorías anidadas
  - Wizard interactivo
  - Integración end-to-end

Ver [tests/README.md](tests/README.md) para detalles.

---

## 📖 Documentación Completa

### 🚀 Inicio Rápido
- **[QUICKSTART_UV.md](QUICKSTART_UV.md)** - Instalación y primer examen en 3 pasos
- **[INSTALACION.md](INSTALACION.md)** - Guía completa (Poetry, UV, pip)
- **[GUIA_UV.md](GUIA_UV.md)** - Gestor UV en profundidad

### 📖 Guías de Uso
- **[WIZARD.md](WIZARD.md)** - Asistente interactivo paso a paso
- **[EJEMPLOS.md](EJEMPLOS.md)** - Ejemplos básicos comentados
- **[EJEMPLOS_AVANZADOS.md](EJEMPLOS_AVANZADOS.md)** - 10 casos avanzados

### ⚙️ Características Específicas
- **[LAYOUTS.md](LAYOUTS.md)** - 3 layouts con comparativas y mejores prácticas
- **[VARIABLES_PERSONALIZADAS.md](VARIABLES_PERSONALIZADAS.md)** - Variables con f-strings
- **[CATEGORIAS.md](CATEGORIAS.md)** - Categorías anidadas y wildcards
- **[RESUMEN_MARKDOWN.md](RESUMEN_MARKDOWN.md)** - Markdown y syntax highlighting

### 📋 Técnica
- **[README_PROYECTO.md](README_PROYECTO.md)** - Arquitectura del sistema
- **[RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md)** - Diseño y decisiones
- **[descripcion.md](descripcion.md)** - Especificación original

### ✅ Verificación
- **[INFORME_CUMPLIMIENTO.md](INFORME_CUMPLIMIENTO.md)** - 52/52 requisitos cumplidos
- **[VERIFICACION_EXAMENES_PRUEBA.md](VERIFICACION_EXAMENES_PRUEBA.md)** - 5 exámenes verificados
- **[VERIFICACION_FINAL.md](VERIFICACION_FINAL.md)** - Validación final
- **[tests/README.md](tests/README.md)** - Guía de tests
- **[examenes_prueba/README.md](examenes_prueba/README.md)** - Exámenes de ejemplo

### 📝 Desarrollo
- **[ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)** - Estado actual
- **[PROYECTO_COMPLETADO.md](PROYECTO_COMPLETADO.md)** - Resumen de finalización
- **[SESION_2025-11-04.md](SESION_2025-11-04.md)** - Bitácora detallada
- **[RESUMEN_TRABAJO.md](RESUMEN_TRABAJO.md)** - Trabajo realizado
- **[bitacora/](bitacora/)** - Registro de implementación

---

## 🎓 Casos de Uso Reales

### Universidad: Examen Parcial
```yaml
# 30 preguntas, 3 layouts diferentes
# Ahorra 50% papel vs layout único
nombre_examen: "Parcial I - Programación"
secciones_examen:
  - nombre: "Análisis de Código"
    layout: default
    pools: [cantidad: 5]
  
  - nombre: "Teoría"
    layout: compact-2col
    pools: [cantidad: 10]
  
  - nombre: "Definiciones"
    layout: compact-3col
    pools: [cantidad: 15]
```

**Resultado:** 5 páginas vs 10 páginas (50% menos papel)

### Instituto: Evaluación Diagnóstica
```yaml
# Quiz rápido con máxima densidad
nombre_examen: "Diagnóstico Inicial"
secciones_examen:
  - nombre: "Conocimientos Previos"
    layout: compact-3col
    pools: [cantidad: 30]
```

**Resultado:** 2-3 páginas para 30 preguntas

### Capacitación: Certificación
```yaml
# Múltiples temas con categorías
nombre_examen: "Examen de Certificación"
secciones_examen:
  - nombre: "Nivel Básico"
    pools:
      - cantidad: 10
        categorias: ["Basico/**"]
  
  - nombre: "Nivel Intermedio"
    pools:
      - cantidad: 15
        categorias: ["Intermedio/**"]
  
  - nombre: "Nivel Avanzado"
    pools:
      - cantidad: 10
        categorias: ["Avanzado/**"]
```

---

## 🌳 Impacto Ambiental

### Ahorro de Papel con Layouts

**Ejemplo Real:**
- Examen: 30 preguntas
- Estudiantes: 40
- Frecuencia: 10 exámenes/año

| Layout | Pág/Examen | Total Pág/Año | Ahorro |
|--------|------------|---------------|--------|
| Solo `default` | 10 | 4,000 | - |
| Mixto optimizado | 5 | 2,000 | **50%** |
| Solo `compact-3col` | 4 | 1,600 | **60%** |

**Impacto:** Hasta **2,400 páginas/año ahorradas** 🌳

---

## 🛠️ Comandos Útiles

```bash
# Crear configuración interactiva
generador-examenes --wizard examen.yaml

# Validar definición
generador-examenes -d examen.yaml -i banco.xml --validate

# Generar con debug
generador-examenes -d examen.yaml -i banco.xml --debug

# Generar múltiples temas
generador-examenes -d examen.yaml -i banco.xml -n 10

# Generar solo HTML
generador-examenes -d examen.yaml -i banco.xml -f html

# Usar múltiples bancos
generador-examenes -d examen.yaml -i banco1.xml banco2.gift -n 5

# Ver ayuda
generador-examenes --help
```

---

## 📊 Estado del Proyecto

✅ **Versión:** 5.3.0  
✅ **Estado:** Producción  
✅ **Tests:** 228 pasando (76% coverage)  
✅ **Documentación:** 100% completa  
✅ **Requisitos:** 52/52 cumplidos  

### Próximas Mejoras
- 🔄 Generación de PDFs optimizados
- 🌐 Más idiomas (PT, FR, DE)
- 📊 Estadísticas de exámenes
- 🎨 Temas visuales personalizables
- 🔌 API REST para integración

---

## 🤝 Contribuir

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

**Requisitos:**
- Tests para nueva funcionalidad
- Documentación actualizada
- Código con type hints
- Seguir estilo PEP 8

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 👥 Autores

**alucarD Team**

---

## 🙏 Agradecimientos

- **Pydantic** - Validación de datos
- **Jinja2** - Sistema de templates
- **Pygments** - Syntax highlighting
- **Rich** - Interfaz de terminal
- **pytest** - Framework de testing
- **UV** - Gestor de paquetes rápido

---

## 📞 Soporte

- 📧 Email: support@alucard.dev
- 🐛 Issues: [GitHub Issues](../../issues)
- 💬 Discussions: [GitHub Discussions](../../discussions)
- 📚 Docs: [Wiki](../../wiki)

---

**¡Gracias por usar alucarD! 🎓**
