# Manual de Uso y Referencia Técnica: alucarD

> **ALUCARD** — Sistema profesional de generación y maquetación de exámenes impresos basado en Typst y bancos GIFT/Moodle XML.
> **Versión:** `5.0.0` · **CLIs principales:** `generador-examenes`, `alucard`, `gift-linter`

---

## 1. Arquitectura y Propósito Pedagógico

`alucarD` es el generador canónico de exámenes y evaluaciones impresas de la cátedra de Programación 1 (UNRN). Integra la compilación de variantes dinámicas en C, la ingesta de bancos de preguntas (GIFT y Moodle XML) y la renderización de alta fidelidad tipográfica mediante Typst y WeasyPrint.

### Alcance Funcional (Qué cubre)
- Generación automatizada de exámenes y parciales institucionales en formatos Typst, PDF y HTML.
- Síntesis de variantes numéricas y lógicas de enunciados mediante semillas reproducibles (`--semilla`).
- Diseño y renderizado de plantillas de examen con hojas de respuestas y descriptores OMR (Optical Mark Recognition).
- Modos accesibles con letra grande (`--accessible`) y empaquetado para imprenta (`--bundle-print`).
- Linting y formateo in-place de archivos de preguntas en formato GIFT (`gift-linter`).
- Auditoría ortográfica y gramatical vía LanguageTool integrada.
- Diagnóstico del entorno y dependencias del sistema (`generador-examenes doctor`).

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Calificación masiva de entregas de código fuente en C (delegado a `dredd`).
- Mantenimiento masivo y reestructuración de árboles de categorías de preguntas (delegado a `moodle-toolbox`).
- Curaduría pedagógica y balance de guías de trabajos prácticos (delegado a `deckard`).

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.11`.
- **Typst:** `>= 0.11` (motor de maquetación vectorial para PDF).
- **GCC:** Requerido para la síntesis de código C con GCC y verificación de variantes.
- **LanguageTool:** Servidor local (puerto 8081) o API pública para auditoría gramatical.

### Instalación vía `uv tool`
```bash
uv tool install --editable /home/mrtin/dev/tools/alucarD
```

### Verificación del Entorno
```bash
generador-examenes doctor
```
Diagnostica la presencia y versiones de `gcc`, `typst`, `weasyprint`, `pypdf` y la conectividad con el servidor LanguageTool.

---

## 3. Guía Integral de Comandos (CLI)

`alucarD` provee dos ejecutables principales:
1. `generador-examenes` (alias `alucard`): Generación, validación y exportación de exámenes.
2. `gift-linter`: Validación sintáctica y auto-corrección de bancos de preguntas en formato GIFT.

---

### CLI 1: `generador-examenes`

#### Opciones Principales de Generación

| Opción / Bandera | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `-d`, `--definicion` | `<path>` | `Requerido` | Ruta al archivo de definición YAML del examen. |
| `-i`, `--input-banco` | `<path>` | `None` | Ruta(s) a los archivos de banco de preguntas (anula lo definido en el YAML). |
| `-o`, `--output-dir` | `<path>` | `./output` | Directorio de salida para los exámenes y soluciones generadas. |
| `-p`, `--path-images` | `<path>` | `None` | Directorio de imágenes referenciadas en las preguntas. |
| `-n`, `--numero-temas` | `<int>` | `1` | Cantidad de temas/variantes independientes a generar. |
| `-s`, `--semilla` | `<int>` | `42` | Semilla pseudo-aleatoria para reproducibilidad matemática. |
| `-f`, `--formato` | `<str>` | `html` | Formato(s) de salida: `pdf`, `html` o ambos (`html,pdf`). |
| `-t`, `--template` | `<path>` | `None` | Ruta a plantilla Typst personalizada (`.typ` o `.typ.j2`). |
| `--omr` | `flag` | `False` | Genera hoja de respuestas OMR de lectura óptica y descriptor JSON de corrección. |
| `--accessible` | `flag` | `False` | Genera versión adaptada para accesibilidad (fuente ampliada y alto contraste). |
| `--bundle-print` | `flag` | `False` | Concatena todos los temas generados en un único archivo PDF listo para imprenta. |
| `--validate` | `flag` | `False` | Valida la coherencia de la definición y bancos sin escribir archivos en disco. |
| `--json` | `flag` | `False` | Emite el resultado y metadata de los exámenes en formato JSON. |
| `--md`, `--output-md` | `<path>` | `None` | Genera un reporte detallado en Markdown. |

#### Opciones de Control de Calidad y Ortografía

| Opción | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--spellcheck` | `flag` | `False` | Audita ortografía y gramática de las preguntas con LanguageTool. |
| `--lt-server` | `<str>` | `http://localhost:8081` | URL del servidor LanguageTool. |
| `--lt-lang` | `<str>` | `es-AR` | Código de idioma para LanguageTool. |
| `--lt-fix` | `flag` | `False` | Aplica correcciones ortográficas automáticas in-place. |
| `--audit-typography` | `flag` | `False` | Audita líneas huérfanas y legibilidad tipográfica en bloques de código. |

#### Ejemplos de Invocación

1. **Generar 3 temas de examen en PDF con hoja de respuestas OMR:**
   ```bash
   generador-examenes -d examen_parcial.yaml -f pdf -n 3 --omr -o ./dist
   ```

2. **Validar definición YAML sin generar archivos:**
   ```bash
   generador-examenes -d examen_parcial.yaml --validate
   ```

3. **Generar versión accesible con letra grande y paquete único para imprenta:**
   ```bash
   generador-examenes -d examen_parcial.yaml -f pdf -n 4 --accessible --bundle-print
   ```

4. **Auditar ortografía en español rioplatense:**
   ```bash
   generador-examenes -d examen_parcial.yaml --spellcheck --lt-lang es-AR
   ```

---

### Subcomando: `generador-examenes doctor`

Verifica la disponibilidad y salud del toolchain de soporte.

```bash
generador-examenes doctor
```

Salida esperada:
- `GCC`: OK (necesario para compilación y trazado de código C).
- `Typst`: OK (compilador de documentos PDF de alta velocidad).
- `LanguageTool`: OK (conectividad con servidor local o público).
- `WeasyPrint / pypdf`: OK (librerías de renderizado y manipulación PDF).

---

### CLI 2: `gift-linter`

Valida la sintaxis de archivos de preguntas en formato GIFT, detecta errores de marcado y permite corregirlos automáticamente.

#### Opciones
| Opción | Descripción |
| :--- | :--- |
| `FILES...` | Uno o más archivos `.gift` a auditar. |
| `--fix` | Corrige problemas comunes de sintaxis y espaciado directamente en los archivos. |

#### Ejemplos
```bash
# Validar sintaxis de un banco GIFT
gift-linter bancos/preguntas_c.gift

# Auto-corregir todos los archivos del directorio bancos/
gift-linter bancos/*.gift --fix
```

---

## 4. Formatos de Salida y Contratos de Integración

### Descriptor OMR para Autograding
Al activar `--omr`, `alucarD` genera junto con cada tema un archivo JSON con la clave de respuestas exactas para su posterior procesamiento automático mediante lectores ópticos o scripts de corrección:
```json
{
  "tema": 1,
  "respuestas_correctas": ["A", "C", "D", "B", "A"],
  "puntajes": [2.0, 2.0, 2.0, 2.0, 2.0]
}
```

### Integración con Dredd
Los exámenes y evaluaciones que integran código C son auditados previamente con `daedalus` y formateados para su inclusión en la rúbrica docente de Dredd.

---

## 5. Diagnóstico y Códigos de Salida

| Código | Significado |
| :---: | :--- |
| `0` | Examen generado o validado con éxito. |
| `1` | Error en la definición YAML, pregunta no encontrada en el banco o syntax error en GIFT. |
| `2` | Faltan binarios indispensables del sistema (`typst`, `gcc`). |