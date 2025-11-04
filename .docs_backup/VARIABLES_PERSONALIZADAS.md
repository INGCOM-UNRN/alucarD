# Variables Personalizadas en Plantillas

Las **variables personalizadas** permiten definir contenido adicional en la configuración YAML que puede ser utilizado en las plantillas HTML/PDF sin estar directamente relacionado con la estructura del examen.

## Características

✨ **Flexibles**: Define cualquier variable que necesites
🔄 **F-Strings**: Soporta interpolación de variables con formato Python
📚 **Contextuales**: Accede a campos de la definición del examen
🔗 **Referenciables**: Las variables pueden referenciar otras variables
📅 **Fecha/Hora**: Variables automáticas de fecha y hora disponibles

## Configuración Básica

### En el archivo YAML

```yaml
nombre_examen: "Parcial I"
institucion: "Universidad Nacional"
materia: "Matemáticas"
fecha: "2025-11-20"
idioma: "es"

configuracion_examen:
  # ... configuración normal ...

# Sección de variables personalizadas
variables_personalizadas:
  profesor: "Dr. García"
  aula: "Aula 301"
  email: "garcia@universidad.edu"
```

### En la plantilla Jinja2

```html
<div class="info-adicional">
  <p>Profesor: {{ variables.profesor }}</p>
  <p>Aula: {{ variables.aula }}</p>
  <p>Contacto: {{ variables.email }}</p>
</div>
```

## Variables con F-Strings

Las variables pueden usar f-strings para interpolar valores:

### Campos de la Definición Disponibles

- `{nombre_examen}`: Nombre del examen
- `{institucion}`: Institución
- `{materia}`: Materia/asignatura
- `{fecha}`: Fecha del examen
- `{duracion_minutos}`: Duración en minutos
- `{idioma}`: Código de idioma

### Variables de Fecha/Hora Automáticas

- `{fecha_actual}`: Fecha actual (formato YYYY-MM-DD)
- `{anio_actual}`: Año actual
- `{mes_actual}`: Mes actual (1-12)
- `{dia_actual}`: Día actual (1-31)

### Ejemplo Completo

```yaml
variables_personalizadas:
  # Variable simple
  profesor: "Dr. García"
  
  # Variable con f-string usando campos
  titulo_completo: "{nombre_examen} de {materia}"
  
  # Variable con fecha actual
  periodo: "Año Académico {anio_actual}"
  
  # Variable compuesta (referencia otras variables)
  encabezado: "{titulo_completo} - {profesor}"
```

**Resultado evaluado:**
```
profesor: "Dr. García"
titulo_completo: "Parcial I de Matemáticas"
periodo: "Año Académico 2025"
encabezado: "Parcial I de Matemáticas - Dr. García"
```

## Casos de Uso

### 1. Información del Profesor

```yaml
variables_personalizadas:
  profesor: "Dra. María Rodríguez"
  departamento: "Departamento de Física"
  email: "mrodriguez@universidad.edu"
  telefono: "+54 11 1234-5678"
  horario_consulta: "Martes 14:00-16:00"
  
  # Variable compuesta
  contacto_completo: "{profesor} ({departamento}) | {email}"
```

**Uso en plantilla:**
```html
<div class="info-profesor">
  <h3>Información del Docente</h3>
  <p><strong>Profesor:</strong> {{ variables.profesor }}</p>
  <p><strong>Departamento:</strong> {{ variables.departamento }}</p>
  <p><strong>Contacto:</strong> {{ variables.email }}</p>
  <p><strong>Horario de Consulta:</strong> {{ variables.horario_consulta }}</p>
</div>
```

### 2. Encabezados y Pies de Página

```yaml
variables_personalizadas:
  encabezado: "{institucion} | {materia}"
  pie_pagina: "{profesor} - {materia} - {periodo}"
  periodo: "2do Cuatrimestre {anio_actual}"
  copyright: "© {anio_actual} {institucion}"
```

**Uso en plantilla:**
```html
<header>
  <h1>{{ variables.encabezado }}</h1>
</header>

<footer>
  <p>{{ variables.pie_pagina }}</p>
  <small>{{ variables.copyright }}</small>
</footer>
```

### 3. Instrucciones Personalizadas

```yaml
variables_personalizadas:
  instrucciones_entrega: |
    Al finalizar, entregue su examen al profesor {profesor}
    en el {aula}. Asegúrese de escribir su nombre completo
    y número de estudiante en todas las hojas.
  
  materiales_permitidos: |
    - Calculadora científica no programable
    - Tabla de fórmulas (1 hoja)
    - Lápiz, goma, regla
  
  nota_importante: "Este examen tiene una duración de {duracion_minutos} minutos"
```

**Uso en plantilla:**
```html
<div class="instrucciones-especiales">
  <h3>Instrucciones de Entrega</h3>
  <p>{{ variables.instrucciones_entrega }}</p>
  
  <h3>Materiales Permitidos</h3>
  <pre>{{ variables.materiales_permitidos }}</pre>
  
  <div class="nota-importante">
    {{ variables.nota_importante }}
  </div>
</div>
```

### 4. Metadatos y Versionado

```yaml
variables_personalizadas:
  version_examen: "v2.1"
  fecha_creacion: "Creado el {fecha_actual}"
  ultima_revision: "Revisión: 2025-11-15"
  comision: "Comisión A"
  
  metadata: "Versión {version_examen} | {fecha_creacion} | {comision}"
```

### 5. Información Administrativa

```yaml
variables_personalizadas:
  codigo_materia: "INFO-101"
  plan_estudios: "Plan 2023"
  creditos: "6 créditos"
  carrera: "Licenciatura en Informática"
  
  info_administrativa: "{codigo_materia} - {materia} ({creditos})"
  contexto_academico: "{carrera} | {plan_estudios}"
```

## Ejemplos de Plantillas

### Plantilla Base con Variables

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ definicion.nombre_examen }}</title>
</head>
<body>
    <!-- Encabezado con variables personalizadas -->
    <header class="exam-header">
        <div class="institution">{{ variables.encabezado }}</div>
        <h1>{{ definicion.nombre_examen }}</h1>
        <div class="exam-info">
            <p>{{ variables.info_administrativa }}</p>
            <p>{{ variables.contexto_academico }}</p>
        </div>
    </header>
    
    <!-- Información del estudiante -->
    <div class="student-info">
        <p><strong>Estudiante:</strong> _________________________</p>
        <p><strong>Legajo:</strong> _________________________</p>
        <p><strong>Fecha:</strong> {{ definicion.fecha }}</p>
    </div>
    
    <!-- Instrucciones con variables -->
    <div class="instructions">
        <h2>Instrucciones</h2>
        <p>{{ definicion.instrucciones_generales }}</p>
        <div class="custom-instructions">
            <p>{{ variables.nota_importante }}</p>
            <div>{{ variables.materiales_permitidos }}</div>
        </div>
    </div>
    
    <!-- Contenido del examen -->
    {% for seccion in secciones %}
    <div class="section">
        <h2>{{ seccion.nombre }}</h2>
        <!-- ... preguntas ... -->
    </div>
    {% endfor %}
    
    <!-- Pie de página con variables -->
    <footer class="exam-footer">
        <div class="professor-info">
            <p>{{ variables.informacion_contacto }}</p>
        </div>
        <div class="metadata">
            <p>{{ variables.pie_pagina }}</p>
            <small>{{ variables.copyright }}</small>
        </div>
    </footer>
</body>
</html>
```

## Validación y Errores

### Manejo de Errores

Si una variable referencia un campo que no existe, se mantiene el valor original:

```yaml
variables_personalizadas:
  valida: "Profesor: {profesor}"  # OK
  invalida: "Campo: {no_existe}"  # Mantiene "{no_existe}"
```

**Log de warning:**
```
[WARNING] No se pudo evaluar variable 'invalida': 'no_existe'. Usando valor original.
```

### Orden de Evaluación

Las variables se evalúan en el orden en que aparecen en el YAML. Esto permite que variables posteriores referencien anteriores:

```yaml
variables_personalizadas:
  nombre: "Dr. García"           # 1º
  titulo: "Profesor {nombre}"    # 2º - puede usar 'nombre'
  completo: "{titulo} - 2025"    # 3º - puede usar 'titulo'
```

## Integración con Wizard

El wizard también soporta variables personalizadas:

```bash
generador-examenes --wizard mi_examen.yaml
```

El asistente preguntará si deseas agregar variables personalizadas y te guiará en su configuración.

## Mejores Prácticas

### ✅ Hacer

1. **Nombres Descriptivos**: Usa nombres claros para tus variables
   ```yaml
   profesor_titular: "Dr. García"
   ```

2. **Agrupar Lógicamente**: Agrupa variables relacionadas
   ```yaml
   profesor: "Dr. García"
   email_profesor: "garcia@uni.edu"
   horario_profesor: "Lunes 14:00"
   ```

3. **Usar F-Strings**: Aprovecha la interpolación
   ```yaml
   titulo: "{nombre_examen} - {materia} ({anio_actual})"
   ```

4. **Documentar**: Comenta variables complejas
   ```yaml
   # Información de contacto completa del profesor
   contacto: "{profesor} | {email} | {telefono}"
   ```

### ❌ Evitar

1. **Nombres Genéricos**: No uses nombres ambiguos
   ```yaml
   var1: "algo"  # ❌ Malo
   profesor: "Dr. García"  # ✅ Bueno
   ```

2. **Referencias Circulares**: No crees ciclos
   ```yaml
   a: "{b}"  # ❌ Malo si b referencia a
   b: "{a}"
   ```

3. **Sobreescribir Campos**: No uses nombres de campos existentes
   ```yaml
   nombre_examen: "Otro nombre"  # ❌ Confuso
   titulo_personalizado: "..."  # ✅ Mejor
   ```

## Ejemplos Avanzados

### Múltiples Idiomas

```yaml
variables_personalizadas:
  # Español
  instruccion_es: "Tiempo: {duracion_minutos} minutos"
  
  # Inglés
  instruccion_en: "Time: {duracion_minutos} minutes"
  
  # Variable condicional (en plantilla)
  # {% if definicion.idioma == 'es' %}
  #   {{ variables.instruccion_es }}
  # {% else %}
  #   {{ variables.instruccion_en }}
  # {% endif %}
```

### Formateo Avanzado

```yaml
variables_personalizadas:
  duracion_horas: "2"
  duracion_texto: "Duración total: {duracion_horas} horas ({duracion_minutos} minutos)"
  
  puntaje_total: "100"
  nota_aprobacion: "60"
  criterio: "Aprobación: {nota_aprobacion}/{puntaje_total} puntos"
```

## Ver También

- [README.md](README.md) - Documentación principal
- [EJEMPLOS.md](EJEMPLOS.md) - Ejemplos de uso
- [WIZARD.md](WIZARD.md) - Asistente de configuración
- Plantillas en `templates/` - Ver ejemplos de uso real
