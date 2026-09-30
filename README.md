# alucarD - Generador de Exámenes 🎓

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

**Sistema profesional de generación de exámenes** basado en plantillas YAML, con soporte para bancos Moodle/GIFT, múltiples layouts y optimización para impresión.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-297%20passing-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-71%25-green.svg)](htmlcov/)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)

---

## 🎯 Alcance

### Qué cubre
- Generación automatizada de exámenes y parciales institucionales en formatos Typst y PDF.
- Síntesis de variantes numéricas y lógicas de enunciados mediante semillas reproducibles.
- Diseño y renderizado de plantillas de examen con hojas de respuestas y descriptores OMR (Optical Mark Recognition).
- Linting y validación de archivos de preguntas en formato GIFT.

### Qué no cubre (Límites y Delegación)
- Calificación masiva de entregas de código de software (delegado a `dredd`).
- Repositorio, mantenimiento masivo y conversión bidireccional entre formatos de bancos Moodle (delegado a `moodle-toolbox`; alucarD incorpora parsers nativos directos exclusivamente para la ingesta y maquetación de exámenes a partir de archivos GIFT y Moodle XML).
- Curaduría y balance de guías de trabajos prácticos (delegado a `deckard`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux (x86_64 / arm64) o Windows (MSYS2 UCRT64 / WSL). Python >= 3.11.

### Dependencias Externas y Binarios
- `typst` (>= 0.11), `gcc` (para compilación de variantes de código C).

### Integración en el Ecosistema
- CLI `alucard`, `generador-examenes`, `gift-linter`. Subcomando `doctor` (`generador-examenes doctor`) para verificar gcc, Typst, WeasyPrint, pypdf y conectividad con LanguageTool.

---

## 📑 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Instalación](#-instalación)
  - [Setup Automático con UV](#opción-1-setup-automático-con-uv--recomendado)
  - [Instalación con Poetry](#opción-2-poetry)
  - [Instalación con pip](#opción-3-pip)
- [Inicio Rápido](#-inicio-rápido)
- [Asistente Interactivo (Wizard)](#-asistente-interactivo-wizard)
- [Configuración de Exámenes](#-configuración-de-exámenes)
- [Layouts y Optimización](#-layouts-y-optimización-de-impresión)
- [Variables Personalizadas](#-variables-personalizadas)
- [Categorías y Filtros](#-categorías-y-filtros)
- [Formatos de Banco](#-formatos-de-banco-de-preguntas)
- [Ejemplos Prácticos](#-ejemplos-prácticos)
- [Testing y Calidad](#-testing-y-calidad)
- [Arquitectura](#-arquitectura)
- [Documentación Adicional](#-documentación-adicional)
- [Contribuir](#-contribuir)

---

## 🌟 Características Principales

### ⚡ Core Features
- ✅ **Asistente Interactivo (Wizard)**: Crea/edita configuraciones YAML con interfaz guiada
- ✅ **Múltiples Layouts**: 4 layouts optimizados para diferentes tipos de contenido
- ✅ **Variables Personalizadas**: Sistema de variables con f-strings y composición
- ✅ **Validación con Pydantic**: Parseo seguro de definiciones YAML
- ✅ **Templating con Jinja2**: Salidas HTML/PDF personalizables
- ✅ **Arquitectura de Plugins**: Extensible vía clases base abstractas
- ✅ **Sintetizador `daedalus`** (nuevo): genera preguntas paramétricas de C cuya respuesta correcta se verifica compilando y ejecutando el snippet con GCC

### 📐 Layouts de Secciones
- **`default`**: Enunciado extenso (2/3) + opciones laterales (1/3)
  - 3-5 preguntas/página | Ideal para análisis de código
- **`compact-2col`**: Enunciado arriba + 2 columnas de opciones
  - 6-10 preguntas/página | Ahorro: 30-40% papel
- **`compact-3col`**: Enunciado arriba + 3 columnas de opciones
  - 12-20 preguntas/página | Ahorro: 50-60% papel
- **`compact-4col`**: Enunciado arriba + 4 columnas de opciones
  - 20-30 preguntas/página | Ahorro: 60-70% papel | Ideal para V/F

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
- ✅ **253 Tests**: Suite completa con pytest
- ✅ **77% Coverage**: Cobertura de código
- ✅ **6 Exámenes de Prueba**: Validación en escenarios reales
- ✅ **CI Ready**: Configurado para integración continua

---

## 🚀 Instalación

### Opción 1: Setup Automático con UV (⚡ Recomendado)

**UV** es ~10-100x más rápido que pip/Poetry.

#### Linux / macOS
```bash
./setup.sh
source .venv/bin/activate
```

#### Windows PowerShell
```powershell
.\setup.ps1
.\.venv\Scripts\Activate.ps1
```

### Opción 2: Instalación Global como Herramienta CLI con `uv tool`

Puedes instalar **alucarD** globalmente usando `uv tool` directamente desde el repositorio o directorio local:

```bash
# Desde el directorio local del repositorio
uv tool install .

# O forzar actualización/reinstalación
uv tool install . --force
```

Una vez instalado con `uv tool`, tendrás disponibles globalmente los ejecutables:
```bash
alucard --help
generador-examenes --help
gift-linter --help
```

O ejecutarlo directamente sin instalar usando `uvx` / `uv tool run`:
```bash
uv tool run --from . alucard -d definicion_ejemplo.yaml
```

### Opción 3: Poetry
```bash
git clone <repo-url>
cd alucard
poetry install
poetry shell
```

### Opción 4: pip
```bash
git clone <repo-url>
cd alucard
pip install -e .
```

### Verificar Instalación
```bash
generador-examenes --help
# o también:
alucard --help
```

---

## 💡 Inicio Rápido

### 1️⃣ Inicializar Proyecto
```bash
generador-examenes --init
```

Esto crea:
- `templates/` - Plantillas Jinja2
- `i18n/` - Archivos de idioma
- `bancos/` - Bancos de preguntas
- `output/` - Exámenes generados
- `definicion_ejemplo.yaml` - Configuración de ejemplo
- `README_PROYECTO.md`

### 2️⃣ Explorar Categorías del Banco
```bash
# Genera un árbol HTML interactivo con todas las categorías
generador-examenes --category-tree bancos/mi_banco.gift
# Abre output/category_tree.html en tu navegador
```

Esto te ayuda a:
- Ver la estructura jerárquica de categorías
- Conocer cuántas preguntas hay por categoría y tipo
- Copiar nombres de categorías al portapapeles para el YAML

### 2️⃣b Sintetizar Preguntas de C con `daedalus`

Genera bancos de preguntas de análisis de código (trazas de punteros,
precedencia de operadores, recursión, incrementos) cuya **respuesta correcta se
verifica compilando y ejecutando el snippet con GCC** — cero erratas en la clave.

```bash
# Ver las plantillas disponibles
generador-examenes --listar-sintetizadores

# Sintetizar 5 preguntas de aritmética de punteros (banco GIFT)
generador-examenes --sintetizar traza-punteros -n 8 -s 42 -o output/

# También en formato Moodle XML
generador-examenes --sintetizar recursion --cantidad 4 --formato-banco xml

# El banco generado se usa directo en un examen:
generador-examenes -d examen.yaml -i output/sintetizados_traza-punteros.gift -n 3
```

Cada pregunta incluye el snippet C en un bloque de código, la salida correcta
(ejecutada de verdad) y distractores verosímiles basados en errores típicos:
precedencia mal interpretada, off-by-one en punteros, post vs pre-incremento.

### 3️⃣ Crear Configuración con Wizard
```bash
generador-examenes --wizard mi_examen.yaml
```

El asistente interactivo te guía:
- Información básica del examen
- Configuración de secciones y layouts
- Pools de preguntas con filtros
- Variables personalizadas
- Vista previa antes de guardar

### 4️⃣ Usar Ejemplos de Configuración

El proyecto incluye 5 configuraciones de ejemplo listas para usar:

```bash
# Ejemplo 1: Básico - Configuración mínima
generador-examenes -d examenes_prueba/ejemplo_1_basico.yaml

# Ejemplo 2: Mixto - Múltiples layouts y tipos
generador-examenes -d examenes_prueba/ejemplo_2_mixto.yaml

# Ejemplo 3: Análisis de código - Layout para código extenso
generador-examenes -d examenes_prueba/ejemplo_3_analisis_codigo.yaml

# Ejemplo 4: Por categorías - Filtrado avanzado
generador-examenes -d examenes_prueba/ejemplo_4_categorias.yaml

# Ejemplo 5: Completo - Todas las características
generador-examenes -d examenes_prueba/ejemplo_5_completo.yaml
```

### 5️⃣ Validar Configuración

**Opción A: Todo en YAML (más simple)**
```bash
# Si el YAML incluye input_banco, solo necesitas:
generador-examenes -d mi_examen.yaml --validate
```

**Opción B: Especificar bancos por CLI**
```bash
generador-examenes -d mi_examen.yaml \
  -i bancos/banco1.txt bancos/banco2.xml \
  --validate
```

### 4️⃣ Explorar Categorías de Bancos

Antes de crear tu configuración, puedes explorar las categorías disponibles en tus bancos:

```bash
# Generar árbol interactivo de categorías
generador-examenes --category-tree bancos/*.xml bancos/*.gift

# Especificar directorio de salida
generador-examenes --category-tree bancos/*.xml -o output
```

Esto genera un HTML interactivo con:
- 🌳 Árbol jerárquico de categorías
- 📊 Contador de preguntas por categoría
- 📋 Botones para copiar nombres de categorías
- 🔍 Búsqueda en tiempo real
- 🎨 Interfaz moderna y responsive

### 5️⃣ Generar Exámenes

**Opción A: Configuración completa en YAML**
```bash
# Si tu YAML incluye input_banco, numero_temas, formato, etc:
generador-examenes -d mi_examen_completo.yaml

# Override específico (ej: generar 5 temas en vez de lo configurado)
generador-examenes -d mi_examen_completo.yaml -n 5

# Cambiar formato a PDF
generador-examenes -d mi_examen_completo.yaml -f pdf
```

**Opción B: CLI tradicional**
```bash
# Especificar todo por línea de comandos
generador-examenes -d mi_examen.yaml \
  -i bancos/banco1.txt bancos/banco2.xml \
  -o output \
  -n 3 \
  -f html

# Generar en PDF
generador-examenes -d mi_examen.yaml \
  -i bancos/*.txt \
  -n 5 \
  -f pdf
```

> **💡 Tip**: Las opciones de CLI siempre tienen prioridad sobre las del YAML, permitiendo overrides rápidos.

---

## 🌳 Explorador de Categorías

Antes de crear tu configuración YAML, puedes explorar visualmente las categorías de tus bancos de preguntas.

### Características

🌳 **Árbol Jerárquico**: Visualiza la estructura completa de categorías
📊 **Contadores**: Ve cuántas preguntas hay en cada categoría
📋 **Copiar Rápido**: Botones para copiar nombres al portapapeles
🔍 **Búsqueda**: Filtra categorías en tiempo real
🎨 **Interfaz Moderna**: Diseño responsive y atractivo
⌨️ **Atajos de Teclado**: Presiona `/` para buscar

### Uso

```bash
# Un solo banco
generador-examenes --category-tree bancos/teorico.gift

# Múltiples bancos
generador-examenes --category-tree bancos/*.xml bancos/*.txt

# Especificar directorio de salida
generador-examenes --category-tree bancos/*.xml -o mis_reportes
```

El comando genera un archivo `category_tree.html` que puedes abrir en tu navegador. Usa los botones "Copiar" para obtener el nombre exacto de cada categoría y pegarlo en tu configuración YAML.

---

## 🧙 Asistente Interactivo (Wizard)

El wizard facilita la creación y edición de configuraciones YAML.

### Características

✨ **Interfaz Interactiva**: Prompts guiados paso a paso
📝 **Creación/Edición**: Crea nuevos o modifica existentes
🎨 **Interfaz Rica**: Experiencia visual mejorada con Rich
✅ **Validación**: Verifica datos en tiempo real
📊 **Vista Previa**: Resumen antes de guardar

### Uso

#### Crear Nueva Configuración
```bash
generador-examenes --wizard
```

#### Editar Configuración Existente
```bash
generador-examenes --wizard examenes_prueba/parcial1_basico.yaml
```

### Flujo del Wizard

1. **Información Básica**
   - Nombre del examen
   - Institución
   - Materia
   - Fecha y duración

2. **Configuración de Examen**
   - Mezclar preguntas
   - Mezclar opciones
   - Generar clave

3. **Secciones**
   - Nombre y descripción
   - Layout (default, compact-2col, 3col, 4col)
   - Instrucciones

4. **Pools de Preguntas**
   - Filtros por categoría
   - Tipos de preguntas
   - Etiquetas (tags)
   - Cantidad y puntaje

5. **Variables Personalizadas** (opcional)
   - Profesor, aula, comisión
   - Variables con f-strings
   - Composición de variables

---

## 📋 Configuración de Exámenes

### Estructura del YAML

```yaml
nombre_examen: "Parcial I - Programación"
institucion: "Universidad Nacional"
materia: "Programación 1"
fecha: "2025-11-20"
duracion_minutos: 90
instrucciones_generales: |
  Lee cuidadosamente cada pregunta.
  Marca una sola respuesta por pregunta.
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

# Variables personalizadas (opcional)
variables_personalizadas:
  profesor: "Dr. Juan Pérez"
  aula: "Aula 301"
  comision: "Comisión A"
  titulo_completo: "{nombre_examen} | {materia}"
  periodo: "Segundo Cuatrimestre {anio_actual}"

# Configuración de generación (opcional, puede overridearse por CLI)
input_banco:
  - "bancos/codigo.xml"
  - "bancos/teorico.gift"
output_dir: "./output"
path_images: null  # Opcional
numero_temas: 3    # Número de versiones a generar
semilla: 42        # Para reproducibilidad
formato:
  - "html"
  - "pdf"

secciones_examen:
  - nombre: "Parte 1: Conceptos Básicos"
    instrucciones: "Selecciona la respuesta correcta"
    layout: "compact-2col"  # default, compact-2col, compact-3col, compact-4col
    pools:
      - tipos: ["seleccion_multiple"]
        cantidad: 15
        accion_si_insuficiente: usar_todas
  
  - nombre: "Parte 2: Análisis de Código"
    instrucciones: "Analiza el código y responde"
    layout: "default"
    pools:
      - categoria: "Programacion/Codigo/**"
        tipos: ["seleccion_multiple"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 5.0
```

### Configuración de Generación en YAML (Nuevo en v5.7.0)

Ahora puedes incluir opciones de generación directamente en el YAML:

```yaml
# Configuración de generación (todas opcionales)
input_banco:                    # Lista de bancos de preguntas
  - "bancos/teoria.gift"
  - "bancos/practica.xml"
  
output_dir: "./examenes"        # Directorio de salida (default: "./output")

path_images: "./imagenes"       # Directorio de imágenes (opcional)

numero_temas: 5                 # Número de versiones (default: 1)

semilla: 123                    # Semilla aleatoria (default: 42)

formato:                        # Formatos de salida (default: ["html"])
  - "html"
  - "pdf"
```

**Ventajas:**
- ✅ Menos argumentos en CLI
- ✅ Configuración reproducible
- ✅ Fácil de versionar en Git
- ✅ CLI override para casos especiales

**Ejemplo de uso:**
```bash
# Con configuración completa en YAML
generador-examenes -d examen.yaml

# Override de opciones específicas
generador-examenes -d examen.yaml -n 10      # Genera 10 temas
generador-examenes -d examen.yaml -f pdf     # Solo PDF
generador-examenes -d examen.yaml -o ./test  # Directorio diferente
```

### Configuración de Pools

Los pools definen cómo seleccionar preguntas del banco:

```yaml
pools:
  # Pool 1: Por tipo
  - tipos: ["seleccion_multiple", "verdadero_falso"]
    cantidad: 10
    
  # Pool 2: Por categoría
  - categoria: "Matematicas/Algebra/**"
    cantidad: 5
    puntaje_fijo_por_pregunta: 2.0
    
  # Pool 3: Por etiquetas
  - etiquetas: ["dificil", "importante"]
    cantidad: 8
    accion_si_insuficiente: advertir
    
  # Pool 4: Preguntas fijas
  - preguntas_fijadas:
      - "Pregunta sobre Python"
      - "Pregunta sobre Listas"
    
  # Pool 5: De banco específico
  - banco: "banco_avanzado.xml"
    categoria: "Avanzado/**"
    tipos: ["seleccion_multiple"]
    cantidad: 10
```

### Opciones de Pool

- **`banco`**: Filtrar solo de este archivo de banco
- **`categoria`**: Categoría Moodle (soporta wildcards `*` y `**`)
- **`tipos`**: Lista de tipos de pregunta
- **`etiquetas`**: Tags de las preguntas
- **`cantidad`**: Número de preguntas a seleccionar
- **`preguntas_fijadas`**: IDs específicos de preguntas
- **`puntaje_fijo_por_pregunta`**: Sobrescribe puntaje del banco
- **`accion_si_insuficiente`**: `error`, `advertir`, `usar_todas`

---

## 📐 Layouts y Optimización de Impresión

### Layouts Disponibles

#### `default` - Layout para Análisis de Código
```
┌─────────────────────────────────────────┐
│ Pregunta 1 (5 pts)           │ a) Op1  │
│                              │ b) Op2  │
│ def funcion():               │ c) Op3  │
│     # código extenso...      │ d) Op4  │
│     return resultado         │         │
└─────────────────────────────────────────┘
```
- **Uso**: Código extenso, análisis, diagramas
- **Densidad**: 3-5 preguntas/página
- **Ahorro**: Baseline (0%)

#### `compact-2col` - Dos Columnas
```
┌─────────────────────────────┐
│ Pregunta 1 (2 pts)          │
│ ¿Qué es Python?             │
│ a) Lenguaje │ c) Snake      │
│ b) Framework│ d) Librería   │
└─────────────────────────────┘
```
- **Uso**: Preguntas teóricas, opciones cortas
- **Densidad**: 6-10 preguntas/página
- **Ahorro**: 30-40% papel

#### `compact-3col` - Tres Columnas
```
┌───────────────────────────┐
│ Pregunta 1 (1 pt)         │
│ Capital de Francia?       │
│ a) París  │b) Londres │c) Roma │
│ d) Madrid │e) Berlín  │f) Oslo │
└───────────────────────────┘
```
- **Uso**: Opciones muy cortas, vocabulario
- **Densidad**: 12-20 preguntas/página
- **Ahorro**: 50-60% papel

#### `compact-4col` - Cuatro Columnas
```
┌─────────────────────────┐
│ Pregunta 1 (1 pt)       │
│ 2 + 2 = ?               │
│ a) 3 │b) 4 │c) 5 │d) 6  │
└─────────────────────────┘
```
- **Uso**: Verdadero/Falso, respuestas muy breves
- **Densidad**: 20-30 preguntas/página
- **Ahorro**: 60-70% papel

### Mejores Prácticas por Contenido

| Tipo de Contenido | Layout Recomendado | Preguntas/Página |
|-------------------|-------------------|------------------|
| Código Python/Java | `default` | 3-5 |
| Análisis de algoritmos | `default` | 3-5 |
| Conceptos teóricos | `compact-2col` | 6-10 |
| Definiciones cortas | `compact-3col` | 12-20 |
| Verdadero/Falso | `compact-4col` | 20-30 |
| Vocabulario | `compact-3col` | 12-20 |
| Fórmulas matemáticas | `compact-2col` | 6-10 |

### Ejemplo de Mezcla de Layouts

```yaml
secciones_examen:
  - nombre: "Análisis de Código"
    layout: "default"  # Código extenso
    pools:
      - tipos: ["seleccion_multiple"]
        cantidad: 5
  
  - nombre: "Conceptos Teóricos"
    layout: "compact-2col"  # Preguntas medianas
    pools:
      - tipos: ["seleccion_multiple"]
        cantidad: 15
  
  - nombre: "Verificación Rápida"
    layout: "compact-4col"  # V/F compacto
    pools:
      - tipos: ["verdadero_falso"]
        cantidad: 20
```

### Optimización de Impresión

El sistema aplica automáticamente estilos CSS específicos para impresión:

**En Pantalla:**
- Márgenes: 2cm
- Padding generoso
- Bordes y colores

**Al Imprimir:**
- Márgenes: 1.5cm
- Padding reducido (0.3-0.5em)
- Bordes delgados (0.5px)
- Código en B/N
- Font-size optimizado
- Line-height compacto

---

## 🎨 Variables Personalizadas

Las variables personalizadas permiten agregar contenido flexible a las plantillas sin modificar el código.

### Características

✨ **Flexibles**: Define cualquier variable
🔄 **F-Strings**: Interpolación con formato Python
📚 **Contextuales**: Accede a campos de la definición
🔗 **Referenciables**: Variables pueden referenciar otras
📅 **Fecha/Hora**: Variables automáticas disponibles

### Variables Disponibles Automáticamente

```python
{
    'nombre_examen': ...,
    'institucion': ...,
    'materia': ...,
    'fecha': ...,
    'duracion_minutos': ...,
    'idioma': ...,
    'fecha_actual': '2025-11-04',
    'anio_actual': 2025,
    'mes_actual': 11,
    'dia_actual': 4
}
```

### Ejemplos de Variables

```yaml
variables_personalizadas:
  # Simples
  profesor: "Dr. Juan Pérez"
  email_contacto: "juan.perez@unrn.edu.ar"
  aula: "Aula 301"
  departamento: "Informática"
  
  # Con f-strings
  titulo_completo: "{nombre_examen} de {materia}"
  ubicacion: "{institucion} - {aula}"
  periodo_academico: "Segundo Cuatrimestre {anio_actual}"
  
  # Compuestas (referencian otras)
  encabezado_principal: "{institucion} | {materia}"
  informacion_contacto: "Profesor: {profesor} | Email: {email_contacto}"
  
  # Con fecha actual
  fecha_generacion: "Generado el {fecha_actual}"
  copyright: "© {anio_actual} {institucion}"
  
  # Para pie de página
  pie_pagina: "{materia} - {profesor} - {periodo_academico}"
  
  # Notas
  nota_importante: "Duración: {duracion_minutos} minutos | Fecha: {fecha}"
  firma_profesor: "_______________\n{profesor}\n{departamento}"
```

### Uso en Plantillas

En tus plantillas Jinja2 (`templates/base_examen.html.j2`):

```jinja
{% if variables and variables.get('profesor') %}
<div class="info"><strong>Profesor:</strong> {{ variables.profesor }}</div>
{% endif %}

{% if variables and variables.get('aula') %}
<div class="info"><strong>Aula:</strong> {{ variables.aula }}</div>
{% endif %}

<footer>{{ variables.pie_pagina }}</footer>
```

---

## 🗂️ Categorías y Filtros

### Sistema de Categorías

Las categorías organizan preguntas jerárquicamente:

```
$course$/
├── Programacion/
│   ├── Teoria/
│   │   ├── Conceptos
│   │   └── Historia
│   └── Codigo/
│       ├── Python
│       └── Java
└── Matematicas/
    ├── Algebra
    └── Calculo
```

### Wildcards

- **`*`**: Un nivel de subcategorías
- **`**`**: Cualquier nivel de subcategorías

```yaml
# Ejemplos
categoria: "Programacion/Teoria"          # Solo Teoria
categoria: "Programacion/Teoria/*"        # Conceptos, Historia
categoria: "Programacion/**"              # Todo Programacion
categoria: "**"                          # Todo el banco
```

### Filtrado por Etiquetas (Tags)

```yaml
pools:
  - etiquetas: ["dificil"]              # Preguntas difíciles
  - etiquetas: ["importante", "final"]   # Con al menos un tag
```

### Filtrado por Tipo

Tipos soportados:
- `seleccion_multiple` - Pregunta con múltiples opciones
- `verdadero_falso` - Pregunta de V/F
- `respuesta_corta` - Respuesta breve
- `desarrollo` - Pregunta de respuesta extensa (ver sección Preguntas de Desarrollo)
- `emparejamiento` - Relacionar conceptos
- `numerica` - Respuesta numérica

```yaml
pools:
  - tipos: ["seleccion_multiple"]
  - tipos: ["verdadero_falso", "seleccion_multiple"]
  - tipos: ["desarrollo"]
```

### Filtros Combinados

```yaml
pools:
  - banco: "banco_avanzado.xml"
    categoria: "Programacion/Python/**"
    tipos: ["seleccion_multiple"]
    etiquetas: ["dificil", "examen"]
    cantidad: 10
```

---

## 📦 Formatos de Banco de Preguntas

### Formato GIFT

Formato de texto plano de Moodle:

```gift
// Comentario

::Pregunta 1::¿Cuál es la capital de Francia? {
=París
~Londres
~Berlín
~Madrid
} [tags: geografia, facil]

::Pregunta 2::Python es un lenguaje de programación. {T} [tags: programacion]

::Pregunta 3::¿Qué significa HTML? {
=HyperText Markup Language
~High Tech Modern Language
~Home Tool Markup Language
} [tags: web, html]
```

### Formato Moodle XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta sobre Python</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>¿Qué es Python?</p>]]></text>
    </questiontext>
    <answer fraction="100" format="html">
      <text><![CDATA[<p>Lenguaje de programación</p>]]></text>
    </answer>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>Un framework</p>]]></text>
    </answer>
    <tags>
      <tag><text>programacion</text></tag>
      <tag><text>python</text></tag>
    </tags>
  </question>
</quiz>
```

### Markdown en Preguntas

Formato `[markdown]` para preguntas con código:

```gift
::Análisis de Código::[markdown]¿Qué imprime este código?

\`\`\`python
def suma(a, b):
    return a + b

print(suma(2, 3))
\`\`\`

{
=5
~6
~23
~Error
} [tags: python, codigo]
```

### Preguntas de Desarrollo

Las preguntas de desarrollo permiten al alumno escribir respuestas extensas. Se renderizan como rectángulos en blanco donde el estudiante puede escribir.

#### Formato GIFT

```gift
::Concepto de Recursión::Define qué es la recursión y da un ejemplo. {desarrollo:mediano} [tags: conceptos]

::Análisis de Algoritmo::Analiza el siguiente algoritmo... {desarrollo:grande} [tags: algoritmos]

::Diferencia Simple::¿Cuál es la diferencia entre X e Y? {desarrollo:pequeno} [tags: basico]
```

**Tamaños disponibles:**
- `{desarrollo:pequeno}` - Espacio pequeño (~4-6 líneas)
- `{desarrollo:mediano}` - Espacio mediano (~8-10 líneas) [default]
- `{desarrollo:grande}` - Espacio grande (~14-16 líneas)

#### Formato Moodle XML

En Moodle XML, las preguntas tipo `essay` se mapean automáticamente a `desarrollo`:

```xml
<question type="essay">
  <name><text>Análisis de Código</text></name>
  <questiontext format="html">
    <text><![CDATA[<p>Explica cómo funciona...</p>]]></text>
  </questiontext>
  <responseformat>editor</responseformat> <!-- grande -->
</question>
```

**Mapeo de tamaños:**
- `noinline` → pequeno
- `plain`, `monospaced` → mediano
- `editor`, `editorfilepicker` → grande

#### Uso en Configuración YAML

```yaml
secciones_examen:
  - nombre: "Parte 3: Desarrollo"
    layout: "default"
    instrucciones: "Responde con claridad y fundamenta tus respuestas"
    pools:
      - tipos: ["desarrollo"]
        etiquetas: ["conceptos"]
        cantidad: 3
```

#### Comportamiento en Layouts

Las preguntas de desarrollo se adaptan al layout de la sección:
- **default**: Espacio completo, tamaño según configuración
- **compact-2col/3col/4col**: Espacio ajustado pero legible

En impresión, los tamaños se optimizan automáticamente para ahorrar papel manteniendo legibilidad.

---

## 🎯 Ejemplos Prácticos

### Ejemplo 1: Examen Básico

```yaml
nombre_examen: "Quiz Semanal"
institucion: "Mi Universidad"
materia: "Programación 1"
duracion_minutos: 30
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  - nombre: "Conceptos Básicos"
    layout: "compact-3col"
    pools:
      - tipos: ["seleccion_multiple"]
        cantidad: 10
```

### Ejemplo 2: Examen con Múltiples Secciones

```yaml
nombre_examen: "Parcial Integrador"
institucion: "Universidad Nacional"
materia: "Estructuras de Datos"
fecha: "2025-11-20"
duracion_minutos: 120
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

variables_personalizadas:
  profesor: "Dr. García"
  aula: "Lab 3"

secciones_examen:
  - nombre: "Parte 1: Teoría"
    layout: "compact-2col"
    instrucciones: "40 puntos - 40 minutos"
    pools:
      - categoria: "Teoria/**"
        tipos: ["seleccion_multiple"]
        cantidad: 20
        puntaje_fijo_por_pregunta: 2.0
  
  - nombre: "Parte 2: Código"
    layout: "default"
    instrucciones: "60 puntos - 80 minutos"
    pools:
      - categoria: "Practica/Codigo/**"
        tipos: ["seleccion_multiple"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 6.0
```

### Ejemplo 3: Examen Final Completo

Ver: `examenes_prueba/final_completo.yaml`

### Ejemplo 4: Quiz Rápido

Ver: `examenes_prueba/quiz_rapido.yaml`

### Ejemplo 5: Recuperatorio

Ver: `examenes_prueba/recuperatorio_mixto.yaml`

---

## 🧪 Testing y Calidad

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=generador_examenes --cov-report=html

# Tests específicos
pytest tests/test_parsers.py
pytest tests/test_logic.py -v
```

### Estructura de Tests

```
tests/
├── test_parsers.py          # Tests de parsers GIFT/XML
├── test_logic.py            # Tests de lógica de negocio
├── test_models.py           # Tests de modelos Pydantic
├── test_generators.py       # Tests de renderizado
├── test_markdown_utils.py   # Tests de Markdown
└── bancos_ejemplo/          # Datos de prueba
    ├── banco_test.txt
    └── banco_test.xml
```

### Validación de Exámenes de Prueba

```bash
# Validar todas las configuraciones de prueba
for config in examenes_prueba/*.yaml; do
    echo "Validando $config"
    generador-examenes -d "$config" \
        -i bancos/*.xml bancos/*.txt bancos/*.gift \
        --validate
done
```

### Métricas de Calidad

- **228 tests** pasando
- **76% cobertura** de código
- **0 errores** de linting
- **Type hints** completos
- **Docstrings** en todas las funciones públicas

---

## 🏗️ Arquitectura

### Estructura del Proyecto

```
generador_examenes/
├── __main__.py              # CLI principal
├── core/
│   ├── logic.py            # Orquestación y filtrado
│   ├── models.py           # Modelos Pydantic
│   └── markdown_utils.py   # Procesamiento Markdown
├── parsers/                # Plugins de entrada
│   ├── base.py            # BaseParser ABC
│   ├── gift_parser.py     # Parser GIFT
│   └── moodle_parser.py   # Parser XML Moodle
├── generators/             # Plugins de salida
│   ├── base.py            # BaseRenderer ABC
│   ├── html_renderer.py   # Generador HTML
│   └── pdf_renderer.py    # Generador PDF
└── config/
    ├── logging_config.py   # Configuración de logs
    └── exam_wizard.py      # Asistente interactivo

templates/                   # Plantillas Jinja2
├── base_examen.html.j2
└── clave_profesor.html.j2

i18n/                       # Internacionalización
├── es.json
└── en.json
```

### Flujo de Ejecución

```
1. CLI (__main__.py)
   ↓
2. Validar YAML (Pydantic models)
   ↓
3. Cargar Bancos (Parsers)
   ↓
4. Construir Pool (Logic)
   ↓
5. Mezclar Preguntas (Logic)
   ↓
6. Renderizar (Generators)
   ↓
7. Guardar HTML/PDF
```

### Extensibilidad

#### Agregar Nuevo Parser

```python
# parsers/mi_parser.py
from generador_examenes.parsers.base import BaseParser

class MiParser(BaseParser):
    @staticmethod
    def get_supported_extensions() -> list[str]:
        return ['.miformat']
    
    def parse(self, filepath: Path) -> Dict[str, Pregunta]:
        # Tu lógica aquí
        return preguntas_dict
```

#### Agregar Nuevo Renderer

```python
# generators/mi_renderer.py
from generador_examenes.generators.base import BaseRenderer

class MiRenderer(BaseRenderer):
    @staticmethod
    def get_supported_formats() -> list[str]:
        return ['miformat']
    
    def renderizar_examen(self, examen_data, definicion, output_dir, tema):
        # Tu lógica aquí
        pass
```

---

## 📚 Documentación Adicional

Este proyecto incluye documentación completa y detallada:

### Documentos Principales

1. **[README.md](README.md)** - Este archivo: Guía completa de uso
2. **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios y versiones
3. **[COMPLIANCE_REPORT.md](.docs_backup/COMPLIANCE_REPORT.md)** - Verificación de cumplimiento con especificaciones
4. **[descripcion.md](.docs_backup/descripcion.md)** - Especificaciones técnicas originales del proyecto

### Documentación en el Código

- **Docstrings**: Todas las clases y funciones públicas documentadas (Google Style)
- **Type Hints**: Tipado completo en todas las funciones
- **Comentarios**: Explicaciones en lógica compleja

### Tests como Documentación

Los tests sirven como documentación viva del comportamiento esperado:
- `tests/test_parsers.py` - Ejemplos de uso de parsers
- `tests/test_logic.py` - Flujos de filtrado y construcción
- `tests/test_integration.py` - Escenarios end-to-end
- `tests/test_layouts.py` - Comportamiento de layouts

### Exámenes de Ejemplo

El directorio `examenes_prueba/` contiene 6 configuraciones completas que sirven como ejemplos prácticos:
1. `examen_01_basico.yaml` - Configuración mínima
2. `examen_02_algoritmos.yaml` - Filtrado por categoría
3. `examen_03_completo.yaml` - Uso avanzado
4. `examen_04_mixto.yaml` - Múltiples layouts
5. `examen_05_personalizado.yaml` - Variables personalizadas
6. `examen_06_layouts.yaml` - Demostración de layouts

Cada uno incluye comentarios explicativos en YAML.

### Reportes de Verificación

- **COMPLIANCE_REPORT.md**: Verificación punto por punto del cumplimiento con `descripcion.md`
  - ✅ 100% cumplimiento confirmado
  - ✅ 11 mejoras adicionales documentadas
  - ✅ 231 tests, 76% cobertura
  - ✅ Estado: PRODUCCIÓN READY

---

## 🏗️ Especificación Técnica

### Arquitectura de Plugins

El proyecto utiliza **Clases Base Abstractas (ABC)** para extensibilidad:

#### Parsers (Entrada)
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, filepath: Path) -> Dict[str, Pregunta]:
        """Parsea archivo y retorna diccionario de preguntas"""
        pass
```

**Implementaciones**:
- `GiftParser`: Formato GIFT de Moodle (.txt, .gift)
- `MoodleParser`: Formato XML de Moodle (.xml)

**Agregar nuevo parser**:
1. Heredar de `BaseParser`
2. Implementar método `parse()`
3. Registrar en `parsers/__init__.py`

#### Renderers (Salida)
```python
class BaseRenderer(ABC):
    @abstractmethod
    def renderizar_examen(self, datos_examen: Dict, 
                         definicion: DefinicionExamen, 
                         output_dir: Path, tema: int):
        """Genera archivo de examen"""
        pass
```

**Implementaciones**:
- `HtmlRenderer`: Genera HTML con Jinja2
- `PdfRenderer`: Genera PDF usando WeasyPrint (reutiliza HTML)

**Agregar nuevo renderer**:
1. Heredar de `BaseRenderer`
2. Implementar métodos de renderizado
3. Registrar en `generators/__init__.py`

### Flujo de Ejecución

```
1. CLI Args Parse (argparse)
   ↓
2. Load YAML (pyyaml + pydantic)
   ↓
3. Validar Definición (Pydantic models)
   ↓
4. Cargar Bancos (BaseParser plugins)
   ↓
5. Procesar Imágenes (base64 embedding)
   ↓
6. Filtrar Preguntas (categorías/tags/tipos)
   ↓
7. Construir Pool (selección + puntajes)
   ↓
8. Mezclar (random con semilla)
   ↓
9. Renderizar (BaseRenderer plugins)
   ↓
10. Guardar Archivos (HTML/PDF)
```

### Modelos Pydantic

```python
# Modelo de entrada (YAML)
DefinicionExamen
  ├── ConfiguracionExamen
  ├── List[SeccionExamen]
  │   └── List[PoolConfig]
  └── Dict[str, str] variables_personalizadas

# Modelo de datos interno
Pregunta
  ├── id: str
  ├── tipo: Literal[tipos]
  ├── categoria: str
  ├── enunciado_html: str
  ├── puntaje: float
  ├── List[Opcion]
  ├── List[etiquetas]
  └── fuente_banco: str
```

### Dependencias Core

| Librería | Versión | Propósito |
|----------|---------|-----------|
| **pydantic** | ≥2.10 | Validación de YAML |
| **pyyaml** | ≥6.0 | Parseo YAML |
| **jinja2** | ≥3.1 | Templating HTML |
| **weasyprint** | ≥63.0 | Generación PDF |
| **pygments** | ≥2.18 | Syntax highlighting |
| **rich** | ≥13.9 | CLI interactiva |

### Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=generador_examenes --cov-report=html

# Tests específicos
pytest tests/test_parsers.py -v
pytest tests/test_logic.py -k filtrado
```

**Coverage Target**: > 70% para features críticas

---

## 🤝 Contribuir

### Guía de Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

- **PEP 8**: Estilo de código Python
- **Type Hints**: Todas las funciones públicas
- **Docstrings**: Formato Google Style
- **Tests**: Cobertura > 70% para nuevas features

### Reportar Issues

Al reportar un issue, incluye:
- Versión de Python
- Versión de alucarD
- Pasos para reproducir
- Output esperado vs real
- Logs relevantes

---

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Programas del sistema: `typst`.

| Sistema | `typst` |
|:--|:--|
| Debian / Ubuntu | binario de https://github.com/typst/typst/releases |
| Fedora | binario de https://github.com/typst/typst/releases |
| Windows | `winget install --id Typst.Typst` |
| macOS | `brew install typst` |

### Opciones de `alucard`

| Opción | Descripción |
|:--|:--|
| `--init` | Inicializar proyecto con archivos de ejemplo |
| `--wizard` | Asistente interactivo para crear/editar configuración de examen |
| `--category-tree` | Generar árbol HTML de categorías de uno o más bancos de preguntas |
| `--sintetizar` | Generar un banco de preguntas de C con daedalus (sintetizador verificado con gcc). Ver plantillas disponibles con --listar-sintetizadores |
| `--listar-sintetizadores` | Lista las plantillas disponibles del sintetizador daedalus |
| `--cantidad` | Cantidad de preguntas a sintetizar (default: 5) [por defecto: 5] |
| `--formato-banco` | Formato del banco generado por daedalus: gift\|xml (default: gift) [por defecto: gift] |
| `--definicion`, `-d` | Ruta al archivo de definición YAML del examen |
| `--input-banco`, `-i` | Ruta(s) a los archivos de banco de preguntas (override de YAML) |
| `--output-dir`, `-o` | Directorio de salida para los exámenes generados (override de YAML, default: ./output) |
| `--path-images`, `-p` | Ruta al directorio de imágenes referenciadas en las preguntas (override de YAML) |
| `--numero-temas`, `-n` | Número de temas/versiones a generar (override de YAML, default: 1) |
| `--semilla`, `-s` | Semilla pseudo-aleatoria para generación (override de YAML, default: 42) |
| `--formato`, `-f` | Formato(s) de salida: html y/o pdf (override de YAML, default: html) |
| `--template`, `--typst-template`, `-t` | Ruta a una plantilla Typst personalizada (.typ / .typ.j2) para generación de PDF |
| `--spellcheck`, `--languagetool` | Auditar ortografía y gramática de las preguntas del examen o banco usando LanguageTool |
| `--lt-server` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública) |
| `--lt-username` | Usuario / email de LanguageTool Premium |
| `--lt-api-key` | API Key / Token de LanguageTool Premium |
| `--lt-premium` | Forzar uso de la API LanguageTool Premium |
| `--lt-lang` | Código de idioma para LanguageTool (default: es-AR) [por defecto: es-AR] |
| `--lt-ignore-rules` | Reglas de LanguageTool a ignorar separadas por comas |
| `--lt-ignore-words` | Palabras personalizadas a ignorar separadas por comas |
| `--lt-fix` | Aplica correcciones ortográficas automáticas |
| `--md`, `--output-md` | Genera reporte de auditoría en formato Markdown |
| `--json` | Emite salida estructurada en formato JSON |
| `--validate` | Validar la definición sin generar archivos |
| `--debug` | Activar modo debug con logging detallado |
| `--omr` | Generar hoja de respuestas OMR de lectura óptica y descriptor JSON |
| `--accessible`, `--large-text` | Generar versión con letra grande y contraste adaptado para accesibilidad |
| `--bundle-print`, `--empaquetar-imprenta` | Empaquetar y concatenar los PDFs de todos los temas en un único archivo para imprenta |
| `--audit-typography` | Auditar calidad tipográfica y líneas huérfanas en bloques de código de preguntas |

### Comandos de `alucard`

| Comando | Descripción |
|:--|:--|
| `alucard lint-gift` | Revisa (y con --fix corrige) bancos de preguntas GIFT (antes, el ejecutable gift-linter). |
| `alucard doctor` | Diagnostica gcc, Typst, WeasyPrint, pypdf y conectividad LanguageTool. |

Ayuda de cada comando: `alucard <comando> -h`.

<!-- p1:referencia:fin -->

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para detalles.

---

## 🙏 Agradecimientos

- [Moodle](https://moodle.org/) - Formato GIFT y XML
- [Jinja2](https://jinja.palletsprojects.com/) - Motor de plantillas
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Validación de datos
- [Rich](https://rich.readthedocs.io/) - Interfaz CLI
- [WeasyPrint](https://weasyprint.org/) - Generación de PDF
- [Pygments](https://pygments.org/) - Syntax highlighting

---

## 📧 Contacto

**Mantenedor**: [Tu Nombre]  
**Email**: tu@email.com  
**Repositorio**: https://github.com/tu-usuario/alucard

---

**Hecho con ❤️ para facilitar la creación de exámenes académicos**
