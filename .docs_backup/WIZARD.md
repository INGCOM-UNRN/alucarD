# Asistente de Configuración (Wizard)

El **Wizard** es un asistente interactivo que facilita la creación y edición de archivos YAML de configuración de exámenes.

## Características

✨ **Interfaz Interactiva**: Guía paso a paso con prompts claros
📝 **Creación desde Cero**: Crea nuevas configuraciones fácilmente
✏️ **Edición**: Modifica configuraciones existentes
🎨 **Interfaz Rica**: Usa Rich para una experiencia visual mejorada
✅ **Validación**: Verifica entrada de datos en tiempo real
📊 **Resumen Visual**: Muestra vista previa antes de guardar

## Uso Básico

### Crear Nueva Configuración

```bash
generador-examenes --wizard
```

El asistente te pedirá:
- Nombre del archivo YAML a crear
- Información básica del examen
- Configuración de parámetros
- Secciones y pools de preguntas

### Editar Configuración Existente

```bash
generador-examenes --wizard mi_examen.yaml
```

Cargará la configuración existente y permitirá modificarla.

## Flujo del Asistente

### 1. Información Básica

El wizard solicita:

- **Nombre del examen**: "Parcial I", "Examen Final", etc.
- **Institución**: Universidad, escuela, etc.
- **Materia**: Nombre de la asignatura
- **Fecha** (opcional): Formato YYYY-MM-DD
- **Duración** (opcional): En minutos
- **Instrucciones generales** (opcional): Texto multilínea
- **Idioma**: `es` (español) o `en` (inglés)

**Ejemplo:**
```
Nombre del examen: Parcial de Matemáticas I
Institución: Universidad Nacional
Materia: Álgebra Lineal
Fecha (YYYY-MM-DD): 2025-11-15
Duración en minutos: 120
Idioma (es/en): es
```

### 2. Configuración del Examen

Opciones de comportamiento:

- **¿Mezclar preguntas dentro de cada sección?**: Aleatoriza orden de preguntas
- **¿Mezclar opciones de cada pregunta?**: Aleatoriza orden de opciones
- **¿Generar clave de respuestas?**: Crea documento con respuestas correctas

### 3. Secciones del Examen

Para cada sección:

#### 3.1 Configuración de Sección

- **Nombre**: Identificador de la sección
- **Instrucciones** (opcional): Específicas de la sección

#### 3.2 Configuración de Pools

Cada sección puede tener múltiples pools de preguntas. Para cada pool:

**Opciones de filtrado:**

1. **Por Categoría**
   ```
   Tipo de filtro: categoria
   Categoría: Matemáticas/Álgebra/**
   Cantidad de preguntas: 10
   ```

2. **Por Tipos**
   ```
   Tipo de filtro: tipos
   Tipos (separados por coma): seleccion_multiple, verdadero_falso
   Cantidad de preguntas: 5
   ```

3. **Por Etiquetas**
   ```
   Tipo de filtro: etiquetas
   Etiquetas (separadas por coma): facil, basico
   Cantidad de preguntas: 8
   ```

4. **Preguntas Fijadas**
   ```
   Tipo de filtro: fijadas
   IDs de preguntas (separados por coma): p001, p002, p003
   ```

5. **Sin Filtro**
   ```
   Tipo de filtro: ninguno
   Cantidad de preguntas: 15
   ```

**Acción si faltan preguntas:**
- `error`: Detiene generación con error
- `advertir`: Muestra advertencia y continúa con las disponibles
- `usar_todas`: Usa todas las preguntas disponibles sin advertir

### 4. Resumen y Guardado

Antes de guardar, el wizard muestra:

- Tabla con información básica
- Configuración de parámetros
- Resumen de secciones y pools
- Vista previa del YAML generado

Confirma para guardar o descarta los cambios.

## Ejemplos Completos

### Ejemplo 1: Examen Simple

```bash
generador-examenes --wizard
```

**Configuración:**
- Nombre: "Quiz Rápido"
- 1 sección con 10 preguntas de selección múltiple
- Sin mezclar opciones

**YAML Generado:**
```yaml
nombre_examen: Quiz Rápido
institucion: Mi Escuela
materia: Matemáticas
idioma: es
configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: false
  generar_clave_profesor: true
secciones_examen:
  - nombre: Sección Única
    pools:
      - tipos: [seleccion_multiple]
        cantidad: 10
        accion_si_insuficiente: advertir
```

### Ejemplo 2: Examen Multi-Sección

**YAML Generado:**
```yaml
nombre_examen: Examen Final de Programación
institucion: Universidad Tecnológica
materia: Programación 1
fecha: '2025-12-10'
duracion_minutos: 180
idioma: es
configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
secciones_examen:
  - nombre: 'Parte 1: Teoría'
    instrucciones: Responda todas las preguntas teóricas
    pools:
      - categoria: Programacion/Teoria/**
        tipos: [seleccion_multiple]
        cantidad: 15
        accion_si_insuficiente: advertir
  
  - nombre: 'Parte 2: Práctica'
    instrucciones: Analice y responda sobre el código
    pools:
      - etiquetas: [codigo, practico]
        cantidad: 10
        accion_si_insuficiente: usar_todas
  
  - nombre: 'Parte 3: Avanzado'
    pools:
      - categoria: Programacion/**
        etiquetas: [avanzado, dificil]
        tipos: [seleccion_multiple, ensayo]
        cantidad: 5
        accion_si_insuficiente: error
```

### Ejemplo 3: Examen con Preguntas Fijadas

**Uso:** Para incluir preguntas específicas obligatorias

```yaml
nombre_examen: Evaluación Diagnóstica
institucion: Colegio Nacional
materia: Ciencias
idioma: es
configuracion_examen:
  mezclar_preguntas_dentro_seccion: false
  mezclar_opciones_dentro_pregunta: false
  generar_clave_profesor: true
secciones_examen:
  - nombre: Preguntas Obligatorias
    pools:
      - preguntas_fijadas:
          - pregunta_fundamental_1
          - pregunta_fundamental_2
          - pregunta_fundamental_3
  
  - nombre: Preguntas Variables
    pools:
      - categoria: Ciencias/**
        cantidad: 7
        accion_si_insuficiente: usar_todas
```

## Consejos de Uso

### 📌 Mejores Prácticas

1. **Nombres Descriptivos**: Usa nombres claros para secciones y categorías
2. **Graduar Dificultad**: Organiza secciones de fácil a difícil
3. **Balance de Puntos**: Distribuye puntaje equilibradamente
4. **Prueba tu Configuración**: Valida con `--validate` antes de generar

### ⚡ Atajos

- **Ctrl+C**: Cancela el wizard en cualquier momento
- **Enter**: Acepta valores por defecto
- **Instrucciones multilínea**: Línea vacía para terminar

### 🔍 Validación Posterior

Después de crear con el wizard, valida:

```bash
generador-examenes -d mi_examen.yaml \
  -i bancos/mi_banco.xml \
  --validate
```

### 🎯 Flujo Recomendado

1. Usa `--wizard` para crear configuración inicial
2. Valida con `--validate`
3. Genera un tema de prueba (`-n 1`)
4. Revisa el resultado
5. Ajusta configuración si es necesario
6. Genera temas finales (`-n 3`)

## Integración con Workflow

### Inicializar Proyecto + Wizard

```bash
# 1. Inicializar estructura
generador-examenes --init

# 2. Configurar examen con wizard
generador-examenes --wizard definicion_mi_examen.yaml

# 3. Validar
generador-examenes -d definicion_mi_examen.yaml \
  -i bancos/banco_ejemplo.txt \
  --validate

# 4. Generar exámenes
generador-examenes -d definicion_mi_examen.yaml \
  -i bancos/banco_ejemplo.txt \
  -n 3 -f html pdf
```

## Troubleshooting

### El wizard no inicia

**Error:** `ImportError: No module named 'rich'`

**Solución:**
```bash
pip install rich
# o
uv pip install rich
```

### No puedo editar YAML existente

**Error:** Archivo no se carga

**Solución:** Verifica que el YAML sea válido:
```bash
python -c "import yaml; yaml.safe_load(open('mi_examen.yaml'))"
```

### Caracteres extraños en terminal

**Solución:** Asegúrate de usar una terminal con soporte UTF-8

## Ventajas del Wizard

✅ **Rápido**: Crea configuraciones en minutos
✅ **Sin Errores**: Validación integrada previene errores sintácticos
✅ **Educativo**: Aprende la estructura YAML mientras creas
✅ **Visual**: Rich proporciona feedback inmediato
✅ **Flexible**: Crea desde cero o edita existentes

## Comparación

| Método | Pros | Contras |
|--------|------|---------|
| **Wizard** | Rápido, guiado, sin errores | Terminal interactiva requerida |
| **Manual** | Control total, versionable | Requiere conocer sintaxis YAML |
| **Copiar** | Rápido para casos similares | Requiere plantilla base |

## Ver También

- [INSTALACION.md](INSTALACION.md) - Instalación inicial
- [EJEMPLOS.md](EJEMPLOS.md) - Ejemplos de uso
- [EJEMPLOS_AVANZADOS.md](EJEMPLOS_AVANZADOS.md) - Casos avanzados
- [README.md](README.md) - Documentación principal
