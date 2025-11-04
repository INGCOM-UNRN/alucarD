alucarD: Sistema de Generación de Exámenes
=================================================================

0. Forma de trabajo.
--------------------

Trabaja de forma gradual, centrandote en un modulo a la vez, genera archivos para llevar registro de
lo implementado, lo en trabajo y lo pendiente dentro de la carpeta ./bitacora en archivos separados
para no perder pisada de lo que hay que hacer.

Crea commits en el repositorio de forma atómica a cambios que se puedan describir puntualmente.

1\. Objetivo Principal
----------------------

Actúa como un **arquitecto de software y programador Python senior**. Tu tarea es diseñar y estructurar una **herramienta empaquetada** para la generación de exámenes.

Esta herramienta debe ser:

-   **Validada:** Usando **Pydantic** para un parseo seguro de las definiciones YAML.

-   **Personalizable (Templating):** Usando **Jinja2** para que las salidas HTML y PDF sean totalmente personalizables sin tocar el código Python.

-   **Extensible:** Usando una arquitectura de plugins (Clases Base Abstractas) para permitir que otros desarrolladores añadan nuevos formatos de entrada (parsers) y salida (renderers).

-   **Multiformato:** Capaz de leer múltiples bancos de preguntas (XML, GIFT) y generar salidas en HTML y PDF (vía **WeasyPrint**).

2\. Estructura del Proyecto (Empaquetado)
-----------------------------------------

El proyecto debe estar estructurado como un paquete Python instalable (`pyproject.toml`) y seguir las mejores prácticas de modularidad.

```
generador_examenes/
├── generador_examenes/
│   ├── __main__.py         # Punto de entrada principal (maneja CLI)
│   ├── core/
│   │   ├── logic.py        # Orquestador de selección y filtrado
│   │   └── models.py       # Modelos Pydantic para validar definicion.yaml
│   ├── parsers/
│   │   ├── __init__.py     # Registra los plugins de parsers
│   │   ├── base.py         # Define `BaseParser` (ABC)
│   │   ├── gift_parser.py  # Implementa BaseParser para GIFT
│   │   └── moodle_parser.py # Implementa BaseParser para Moodle XML
│   ├── generators/
│   │   ├── __init__.py     # Registra los plugins de renderers
│   │   ├── base.py         # Define `BaseRenderer` (ABC)
│   │   ├── html_renderer.py # Implementa BaseRenderer para HTML
│   │   └── pdf_renderer.py  # Implementa BaseRenderer para PDF (usa WeasyPrint)
│   └── config/
│       └── logging_config.py # Configuración de logging
│
├── templates/                # Directorio de plantillas Jinja2
│   ├── base_examen.html.j2   # Plantilla principal
│   └── clave_profesor.html.j2 # Plantilla para la clave
│
├── i18n/                     # Archivos de internacionalización
│   ├── en.json
│   └── es.json
│
├── tests/                    # Pruebas unitarias
│   ├── test_parsers.py
│   ├── test_logic.py
│   └── bancos_ejemplo/
│       ├── banco_test.xml
│       └── banco_test.txt
│
└── pyproject.toml            # Definición del proyecto y dependencias

```

### 2.1. Ejemplo de `pyproject.toml` (Dependencias)

```
[tool.poetry]
name = "generador-examenes"
version = "5.0.0"
description = "Generador de exámenes basado en plantillas, YAML y bancos Moodle/GIFT."
authors = ["Tu Nombre <tu@email.com>"]

[tool.poetry.dependencies]
python = "^3.10"
pydantic = "^2.0"
pyyaml = "^6.0"
jinja2 = "^3.1"
weasyprint = "^60.0" # Para la generación de PDF

[tool.poetry.dev-dependencies]
pytest = "^7.0"

[tool.poetry.scripts]
generador-examenes = "generador_examenes.__main__:main"

```

3\. Formatos de Entrada y Parsers (Plugin ABC)
----------------------------------------------

La herramienta debe usar una Clase Base Abstracta `BaseParser` (definida en `parsers/base.py`). Los parsers `MoodleXMLParser` y `GiftParser` implementarán esta clase.

-   **Extracción de Datos:** Los parsers deben extraer: `tipo`, `nombre`, `categoria`, `enunciado_html`, `puntaje`, `opciones` y, crucialmente, **`etiquetas` (tags)** (ej. de `[tags: tema1, dificil]` en GIFT o un campo `<tags>` en Moodle).

-   **Manejo de Errores:** (Sin cambios, usar `logging.warning` para preguntas omitidas).

### 3.1. Modelo de Datos Interno (Contrato)

El archivo `core/models.py` definirá el modelo de datos interno que *todos* los parsers deben producir. Usar Pydantic para esto asegura la consistencia.

```
# En core/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class Opcion(BaseModel):
    texto_html: str
    es_correcta: bool
    retroalimentacion: str | None = None

class Pregunta(BaseModel):
    nombre: str = Field(..., description="Nombre único de la pregunta, usado como ID")
    tipo: Literal["multichoice", "truefalse", "shortanswer", "matching", "essay"]
    categoria: str
    enunciado_html: str
    opciones: List[Opcion] = []
    puntaje: float = 1.0
    etiquetas: List[str] = []
    fuente_banco: str = Field(..., description="Nombre del archivo de banco de donde provino")

```

4\. Estructura del Archivo de Definición (Validación Pydantic)
--------------------------------------------------------------

### 4.1. Validación del Esquema (Pydantic)

El módulo `core/models.py` también definirá los modelos Pydantic (ej. `PoolConfig`, `SeccionConfig`, `ExamenConfig`) que mapean la estructura del YAML. Al cargar `definicion.yaml`, debe ser validado contra estos modelos.

### 4.2. Ejemplo de `definicion.yaml` (v5.0 Completo)

Se añaden todas las claves relevantes para una configuración completa.

```
configuracion_examen:
  titulo_examen: "Examen Final de Programación I"
  subtitulo: "Departamento de Ingeniería"
  logo_path: "logo_universidad.png"
  idioma: 'es' # NUEVO: Controla i18n (default: 'en')

  # --- Configuración de Generación ---
  layout_preguntas: '2-columnas'
  mostrar_puntaje: true
  generar_hoja_respuestas_alumno: true
  generar_clave_profesor: true # NUEVO: Genera un archivo con las respuestas correctas.

  # --- Configuración de Mezcla ---
  mezclar_todas_las_secciones: false

secciones_examen:
  - titulo: "Sección A: Conceptos Clave (Tags)"
    instrucciones: "Marque la única respuesta correcta."
    mezclar_preguntas_seccion: true
    pool:
      - # Selección por etiquetas de múltiples bancos
        banco: 'banco_basico.xml' # NUEVO: Solo busca en este banco
        etiquetas: ['tema1', 'fundamental'] # NUEVO: Filtra por tags
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0 # Sobrescribe el puntaje del banco

  - titulo: "Sección B: Avanzado (Fijados + Aleatorios)"
    instrucciones: "Responda o complete según corresponda."
    mezclar_preguntas_seccion: false
    pool:
      - # Pool 1: Preguntas fijas (busca en todos los bancos)
        preguntas_fijadas:
          - "Logo de Python"
          - "Heliocentrismo"
      - # Pool 2: Aleatorias de categoría y banco específico
        banco: 'banco_avanzado.xml' # NUEVO: Solo busca en este banco
        categoria: '$course$/top/programacion1/avanzado'
        tipos: ['shortanswer', 'essay'] # Filtra por tipo
        cantidad: 8
        accion_si_insuficiente: 'usar_disponibles' # 'fallar' (default) o 'usar_disponibles'

```

5\. Comportamiento del Script y Argumentos (CLI)
------------------------------------------------

El script `__main__.py` usará `argparse` para definir la interfaz de línea de comandos.

-   `--init`: (Opcional) Genera `definicion_ejemplo.yaml`, `templates/` (con plantillas base) y `i18n/` (con `en.json`, `es.json`).

-   `--validate`: (Opcional) Valida el YAML contra los bancos, imprime un resumen detallado de preguntas por sección y puntajes, y sale.

-   `-i, --input_banco`: (Requerido para `validate` y `generate`) **Acepta múltiples argumentos** (usando `nargs='+'`). Ruta a los archivos XML o GIFT. (Ej. `-i banco1.xml -i banco2.txt`).

-   `-d, --definicion`: (Requerido para `validate` y `generate`) Ruta al archivo de definición `definicion.yaml`.

-   `-p, --path_images`: (Opcional) Ruta al directorio que contiene los archivos de imagen. Si no se provee, se busca relativo al `input_banco`.

-   `-o, --output_dir`: (Opcional) Directorio de salida. Default: `./examenes_generados`.

-   `-n, --numero_temas`: (Opcional) Número de temas a generar. Default: `1`.

-   `-s, --semilla`: (Opcional) Semilla pseudo-aleatoria (entero) para la generación de temas. Default: `42`.

-   `-f, --formato`: (Opcional) Formato(s) de salida. Default: `html`. Se pueden especificar múltiples (Ej. `-f html pdf`). Opciones: `['html', 'pdf']`.

-   `--debug`: (Opcional) Activa el logging a nivel `DEBUG` para depuración.

6\. Lógica de Generación (Orquestación)
---------------------------------------

El script `__main__.py` orquesta el flujo, delegando la lógica pesada a `core/logic.py`.

1.  **Inicio:** `main()` parsea los argumentos (CLI).

2.  **Configurar Logging:** Llama a `config.logging_config.setup_logging(debug=args.debug)`.

3.  **Modo de Operación:**

    -   Si `args.init`: Ejecutar lógica de inicialización (crear archivos de ejemplo) y salir.

    -   **Cargar Definición:** Cargar `args.definicion` y validarlo con los modelos Pydantic de `core/models.py`. Si falla, imprimir error de validación y salir.

    -   **Cargar Bancos:** Llamar a `core.logic.cargar_bancos(args.input_banco)`:

        -   Itera sobre cada ruta de `input_banco`.

        -   Detecta el `BaseParser` (plugin) apropiado según la extensión.

        -   Llama a `parser.parse(ruta_archivo)`.

        -   Combina todas las preguntas (instancias del modelo `Pregunta`) en un único diccionario maestro: `banco_completo: Dict[str, Pregunta]`.

    -   **Embeber Imágenes:** Llamar a `core.logic.procesar_imagenes(banco_completo, args.path_images)`. Esta función itera sobre `banco_completo`, busca `src="file://..."`, encuentra el archivo, lo convierte a `base64` y reemplaza el `src`. Si no lo encuentra, emite un `WARNING` y usa un placeholder.

    -   **Construir Pool de Examen:** Llamar a `core.logic.construir_pool_examen(definicion, banco_completo)`:

        -   Esta es la función más crítica. Itera sobre `secciones_examen` y cada `pool` dentro de ellas.

        -   Aplica el filtrado en cascada: `banco`, `preguntas_fijadas`, `categoria`, `tipos`, `etiquetas`.

        -   Maneja la lógica de `cantidad`, `accion_si_insuficiente`.

        -   Aplica `puntaje_fijo_por_pregunta` si se especifica.

        -   Devuelve una estructura de datos `ExamenParaGenerar` que contiene la lista final de secciones y preguntas (ya filtradas, pero aún no mezcladas).

    -   **Modo Validación:** Si `args.validate`:

        -   Imprime un resumen formateado del `ExamenParaGenerar` (cuántas preguntas por sección, puntaje total) y sale.

    -   **Modo Generación (Bucle de Temas):**

        -   Para `i` en `range(args.numero_temas)`:

            -   `semilla_tema = args.semilla + i`

            -   Llamar a `core.logic.mezclar_examen(examen_para_generar, semilla_tema, definicion.configuracion_examen)` para mezclar preguntas y opciones.

            -   Para `formato` en `args.formato`:

                -   Detectar el `BaseRenderer` (plugin) apropiado (ej. `HtmlRenderer`, `PdfRenderer`).

                -   Llamar a `renderer.renderizar_examen(examen_mezclado, definicion, args.output_dir, tema=i)`.

                -   Si `generar_clave_profesor` es `True`, llamar también a `renderer.renderizar_clave(...)`.

7\. Generación y Renderizado de Salida (Jinja2/WeasyPrint)
----------------------------------------------------------

Definido en `generators/base.py` y sus implementaciones.

-   `BaseRenderer` (ABC): Define métodos como `renderizar_examen` y `renderizar_clave`.

-   `HtmlRenderer`:

    -   Inicializa un entorno `Jinja2` apuntando al directorio `templates/`.

    -   Carga el archivo `i18n/{idioma}.json` y lo pasa al contexto de la plantilla.

    -   Renderiza `base_examen.html.j2` o `clave_profesor.html.j2` con los datos del examen y el JSON de idioma.

-   `PdfRenderer`:

    -   **Reutiliza `HtmlRenderer`** para generar el HTML completo en memoria.

    -   Usa `WeasyPrint` para convertir esa string HTML en un archivo PDF, aplicando el CSS de la plantilla (especialmente `page-break-before: always;` en las secciones para una impresión limpia).

8\. Configuración de Logging
----------------------------

El archivo `config/logging_config.py` debe:

-   Definir una función `setup_logging(debug: bool)`:

-   Configurar un `StreamHandler` (consola).

-   Establecer el nivel en `logging.INFO` si `debug` es `False`, y `logging.DEBUG` si `debug` es `True`.

-   Formatear los mensajes para incluir Nivel, Módulo y Mensaje (ej. `[INFO] [parsers.gift_parser] 15 preguntas cargadas de banco.txt`).

9\. Librerías Clave Recomendadas
--------------------------------

Listado explícito de dependencias principales que el `pyproject.toml` debe gestionar:

-   **`pydantic`**: Para la validación de YAML y los modelos de datos internos (`Pregunta`).

-   **`pyyaml`**: Para cargar el archivo `definicion.yaml`.

-   **`jinja2`**: Para el motor de plantillas HTML.

-   **`weasyprint`**: Para la conversión de HTML a PDF.

-   **`pytest`**: Para el desarrollo y ejecución de pruebas unitarias (`tests/`).
