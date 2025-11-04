# Exámenes de Prueba - Verificación del Sistema

Este directorio contiene **5 configuraciones de exámenes** diseñadas para verificar el funcionamiento general de la herramienta **alucarD**.

## 📋 Exámenes Incluidos

### 1️⃣ Examen Básico (`examen_01_basico.yaml`)

**Propósito:** Verificar funcionalidad básica de generación

**Características:**
- ✅ Configuración simple y directa
- ✅ Una sola sección
- ✅ Variables personalizadas básicas
- ✅ 10 preguntas de selección múltiple

**Bancos utilizados:**
- `codigo.xml` - Preguntas de código
- `algoritmos.xml` - Preguntas de algoritmos

**Detalles:**
```yaml
Duración: 60 minutos
Secciones: 1
Preguntas: 10
Variables: 5 (profesor, aula, departamento, periodo, pie_pagina)
```

**Verifica:**
- ✅ Carga de bancos XML
- ✅ Filtrado simple por tipo
- ✅ Variables personalizadas básicas
- ✅ Generación de clave de profesor

---

### 2️⃣ Examen de Algoritmos (`examen_02_algoritmos.yaml`)

**Propósito:** Verificar múltiples secciones y acción ante preguntas insuficientes

**Características:**
- ✅ Dos secciones con diferentes cantidades
- ✅ Combinación de bancos XML y GIFT
- ✅ Diferentes estrategias ante falta de preguntas
- ✅ Variables personalizadas con f-strings

**Bancos utilizados:**
- `algoritmos.xml`
- `teorico.gift`

**Detalles:**
```yaml
Duración: 90 minutos
Secciones: 2
  - Parte 1: 20 preguntas (usar_todas)
  - Parte 2: 15 preguntas (advertir)
Variables: 6 con interpolación
```

**Verifica:**
- ✅ Múltiples secciones
- ✅ Parseo GIFT y XML combinados
- ✅ Estrategia `usar_todas` vs `advertir`
- ✅ F-strings en variables: `{nombre_examen} de {materia}`

---

### 3️⃣ Examen Integral (`examen_03_completo.yaml`)

**Propósito:** Verificar examen complejo con múltiples características

**Características:**
- ✅ Tres secciones con diferentes puntajes
- ✅ Instrucciones multilínea elaboradas
- ✅ Variables personalizadas complejas
- ✅ Información de contacto completa

**Bancos utilizados:**
- `codigo.xml`
- `algoritmos.xml`

**Detalles:**
```yaml
Duración: 120 minutos
Secciones: 3
  - Parte 1: 8 preguntas (25 puntos)
  - Parte 2: 10 preguntas (40 puntos)
  - Parte 3: 12 preguntas (35 puntos)
Variables: 10 con composición compleja
```

**Verifica:**
- ✅ Instrucciones elaboradas
- ✅ Variables compuestas (referencian otras variables)
- ✅ Distribución de puntajes
- ✅ Contacto y horarios de consulta

---

### 4️⃣ Evaluación Mixta (`examen_04_mixto.yaml`)

**Propósito:** Verificar balance entre teoría y práctica

**Características:**
- ✅ Tres secciones con pesos diferentes
- ✅ Uso de todos los bancos disponibles
- ✅ Variables con información administrativa
- ✅ Mayor cantidad de preguntas

**Bancos utilizados:**
- `teorico.gift` (mayoría)
- `codigo.xml`
- `algoritmos.xml`

**Detalles:**
```yaml
Duración: 90 minutos
Secciones: 3
  - Parte 1: 25 preguntas teóricas (40%)
  - Parte 2: 8 preguntas de código (30%)
  - Parte 3: 15 preguntas de algoritmos (30%)
Variables: 8 con info administrativa
```

**Verifica:**
- ✅ Uso extensivo del banco GIFT
- ✅ Variables con metadatos (comisión, turno)
- ✅ Distribución de pesos por sección
- ✅ Mayor volumen de preguntas

---

### 5️⃣ Examen Final Personalizado (`examen_05_personalizado.yaml`)

**Propósito:** Verificar funcionalidades avanzadas y personalización máxima

**Características:**
- ✅ Cuatro secciones con progresión de dificultad
- ✅ **22 variables personalizadas** (máximo nivel)
- ✅ Variables categorizadas (docente, examen, administrativa)
- ✅ Instrucciones muy elaboradas
- ✅ Metadatos completos

**Bancos utilizados:**
- Todos los bancos disponibles

**Detalles:**
```yaml
Duración: 150 minutos
Secciones: 4
  - Parte 1: Sintaxis (10 preguntas, 20 puntos)
  - Parte 2: Estructuras (5 preguntas, 25 puntos)
  - Parte 3: Funciones (8 preguntas, 25 puntos)
  - Parte 4: Algoritmos (20 preguntas, 30 puntos)
Variables: 22 con categorización completa
```

**Variables personalizadas incluyen:**
- 👤 Información del docente (5 variables)
- 📝 Información del examen (4 variables)
- 🏛️ Información administrativa (4 variables)
- 🔗 Variables compuestas (9 variables)

**Verifica:**
- ✅ Máxima cantidad de variables personalizadas
- ✅ Variables con categorización lógica
- ✅ F-strings complejos y anidados
- ✅ Examen largo con múltiples secciones
- ✅ Uso completo de todas las características

---

## 🚀 Generación de Exámenes

### Generar un examen específico

```bash
# Examen 1 - Básico
generador-examenes \
  -d examenes_prueba/examen_01_basico.yaml \
  -i bancos/codigo.xml bancos/algoritmos.xml \
  -o output/prueba_01 \
  -n 3 \
  -f html

# Examen 5 - Personalizado (todos los bancos)
generador-examenes \
  -d examenes_prueba/examen_05_personalizado.yaml \
  -i bancos/codigo.xml bancos/algoritmos.xml bancos/teorico.gift \
  -o output/prueba_05 \
  -n 2 \
  -f html pdf
```

### Generar todos los exámenes

```bash
#!/bin/bash
for i in {01..05}; do
  echo "Generando examen ${i}..."
  generador-examenes \
    -d examenes_prueba/examen_${i}_*.yaml \
    -i bancos/*.xml bancos/*.gift \
    -o output/prueba_${i} \
    -n 2 \
    -f html
done
```

## 📊 Resultados Esperados

Cada examen genera:
- ✅ 2 archivos HTML de examen (2 temas diferentes)
- ✅ 2 archivos HTML de clave (respuestas correctas)
- ✅ Total: 4 archivos por examen

**Para los 5 exámenes:**
- 📄 10 exámenes HTML
- 🔑 10 claves HTML
- 📦 Total: 20 archivos

## ✅ Verificación de Funcionalidades

### Por Examen

| Examen | Funcionalidad Principal Verificada |
|--------|------------------------------------|
| 1 - Básico | Configuración mínima funcional |
| 2 - Algoritmos | Múltiples secciones + GIFT |
| 3 - Completo | Variables compuestas |
| 4 - Mixto | Balance teoría/práctica |
| 5 - Personalizado | Todas las características |

### Checklist Global

- ✅ Parseo de bancos XML (Moodle)
- ✅ Parseo de bancos GIFT
- ✅ Validación con Pydantic
- ✅ Variables personalizadas simples
- ✅ Variables con f-strings
- ✅ Variables compuestas (referenciando otras)
- ✅ Variables automáticas (fecha, año)
- ✅ Múltiples secciones
- ✅ Mezcla de preguntas
- ✅ Mezcla de opciones
- ✅ Generación de clave profesor
- ✅ Instrucciones multilínea
- ✅ Estrategias ante preguntas insuficientes
- ✅ Renderizado HTML
- ✅ Internacionalización (español)

## 🎯 Casos de Uso Demostrados

### 1. Quiz Rápido
→ **Examen 1** (60 min, 10 preguntas, 1 sección)

### 2. Examen Parcial
→ **Examen 2 o 3** (90-120 min, 2-3 secciones)

### 3. Examen Final
→ **Examen 5** (150 min, 4 secciones, completo)

### 4. Evaluación Mixta
→ **Examen 4** (teoría + práctica balanceado)

## 📈 Estadísticas

```
Total de configuraciones: 5
Total de secciones: 13
Total de preguntas configuradas: ~175
Total de bancos utilizados: 3
  - codigo.xml: 15 preguntas
  - algoritmos.xml: 50 preguntas
  - teorico.gift: 1,494 preguntas
Variables personalizadas: 51 (total entre todos)
```

## 🔍 Validación

Para validar sin generar:

```bash
generador-examenes \
  -d examenes_prueba/examen_05_personalizado.yaml \
  -i bancos/*.xml bancos/*.gift \
  --validate
```

## 📝 Notas

1. **Banco teorico.gift** contiene muchas preguntas sin opciones (preguntas abiertas), que son ignoradas automáticamente por el parser
2. Las **variables personalizadas** son completamente opcionales
3. La **estrategia `usar_todas`** es útil cuando el pool es pequeño
4. Los **f-strings** permiten composición poderosa de variables

## 🎓 Aprendizaje

Estos exámenes sirven como:
- ✅ **Ejemplos** de configuración
- ✅ **Tests** de funcionalidad
- ✅ **Templates** para crear nuevos exámenes
- ✅ **Documentación** práctica del sistema

---

**Fecha de creación:** 2025-11-04  
**Versión de alucarD:** 5.0.0  
**Estado:** ✅ Todos los exámenes generados exitosamente
