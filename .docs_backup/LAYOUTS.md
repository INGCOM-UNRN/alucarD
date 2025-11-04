# Layouts de Secciones

alucarD soporta **múltiples layouts** para acomodar diferentes densidades de texto y optimizar el uso de papel en impresiones.

## 📐 Layouts Disponibles

### 1️⃣ Layout `default` - Análisis de Código

**Ideal para:** Preguntas con enunciados extensos (código, análisis, lecturas)

**Características:**
- Enunciado ocupa 2/3 del ancho
- Opciones en columna derecha (1/3 del ancho)
- Mayor espacio para contenido complejo
- Perfecto para bloques de código con syntax highlighting

**Configuración:**
```yaml
secciones_examen:
  - nombre: "Análisis de Código"
    layout: default  # o simplemente omitir, es el valor por defecto
    pools:
      - cantidad: 10
```

**Distribución visual:**
```
┌─────────────────────────────────────┬──────────────┐
│                                     │              │
│  Pregunta 1                         │  □ a) Op. 1  │
│                                     │  □ b) Op. 2  │
│  [Enunciado extenso con código]     │  □ c) Op. 3  │
│  def ejemplo():                     │  □ d) Op. 4  │
│      return "valor"                 │              │
│                                     │              │
│                                     │              │
└─────────────────────────────────────┴──────────────┘
```

---

### 2️⃣ Layout `compact-2col` - Dos Columnas

**Ideal para:** Preguntas teóricas con opciones moderadamente largas

**Características:**
- Pregunta arriba, opciones abajo
- Opciones distribuidas en **2 columnas**
- Reduce espacio vertical significativamente
- Mantiene buena legibilidad

**Configuración:**
```yaml
secciones_examen:
  - nombre: "Conceptos Teóricos"
    layout: compact-2col
    pools:
      - cantidad: 15
```

**Distribución visual:**
```
┌──────────────────────────────────────────────────────┐
│  Pregunta 2                                          │
│  ¿Cuál es la definición correcta de...?             │
│                                                      │
│  □ a) Opción 1          □ c) Opción 3               │
│  □ b) Opción 2          □ d) Opción 4               │
└──────────────────────────────────────────────────────┘
```

**Ahorro de papel:** ~30-40% vs layout default

---

### 3️⃣ Layout `compact-3col` - Tres Columnas (Máxima Densidad)

**Ideal para:** Preguntas cortas con opciones breves

**Características:**
- Pregunta arriba, opciones abajo
- Opciones distribuidas en **3 columnas**
- **Máxima densidad** - mínimo uso de papel
- Optimizado para texto corto
- Fuentes ligeramente reducidas

**Configuración:**
```yaml
secciones_examen:
  - nombre: "Respuestas Rápidas"
    layout: compact-3col
    pools:
      - cantidad: 25
```

**Distribución visual:**
```
┌──────────────────────────────────────────────────────┐
│  Pregunta 3                                          │
│  ¿Cuál es correcto?                                  │
│                                                      │
│  □ a) Op 1    □ c) Op 3    □ e) Op 5                │
│  □ b) Op 2    □ d) Op 4    □ f) Op 6                │
└──────────────────────────────────────────────────────┘
```

**Ahorro de papel:** ~50-60% vs layout default

---

## 🎨 Estilos para Pantalla e Impresión

Todos los layouts incluyen estilos optimizados tanto para **visualización en pantalla** como para **impresión en papel**.

### 📺 En Pantalla

- Bordes y colores para mejor visualización
- Spacing generoso para lectura cómoda
- Syntax highlighting con colores
- Interactividad visual

### 🖨️ En Impresión

- Bordes simplificados (ahorro de tinta)
- Spacing reducido (ahorro de papel)
- Código en blanco y negro
- Fuentes optimizadas para legibilidad
- Page breaks inteligentes

**Optimizaciones automáticas al imprimir:**
```css
/* Layouts compactos en impresión */
- Padding reducido (0.3em vs 1em)
- Margins menores (0.5em vs 1.5em)
- Bordes más delgados (0.5px vs 1px)
- Checkbox más pequeños (10px vs 15px)
- Line-height reducido (1.2 vs 1.6)
```

---

## 📊 Comparativa de Layouts

| Layout | Preguntas/Página* | Uso de Papel | Legibilidad | Ideal Para |
|--------|-------------------|--------------|-------------|------------|
| `default` | 3-5 | 100% | ⭐⭐⭐⭐⭐ | Código, análisis |
| `compact-2col` | 6-10 | 60-70% | ⭐⭐⭐⭐ | Teoría, conceptos |
| `compact-3col` | 12-20 | 40-50% | ⭐⭐⭐ | Respuestas cortas |

\* Aproximado, depende del contenido

---

## 🔧 Uso Avanzado

### Mezclar Layouts en un Mismo Examen

Puedes usar diferentes layouts por sección según el tipo de contenido:

```yaml
nombre_examen: "Examen Parcial - Programación"
institucion: "UNRN"
materia: "Algoritmos"

secciones_examen:
  # Sección 1: Código (default)
  - nombre: "Parte 1: Análisis de Algoritmos"
    layout: default  # enunciados extensos
    instrucciones: "Analiza cada algoritmo cuidadosamente"
    pools:
      - cantidad: 5
        tipos: ["seleccion_multiple"]
  
  # Sección 2: Teoría (2 columnas)
  - nombre: "Parte 2: Conceptos Fundamentales"
    layout: compact-2col  # opciones moderadas
    instrucciones: "Responde cada pregunta de teoría"
    pools:
      - cantidad: 10
        tipos: ["seleccion_multiple"]
  
  # Sección 3: Definiciones (3 columnas)
  - nombre: "Parte 3: Definiciones Rápidas"
    layout: compact-3col  # máxima densidad
    instrucciones: "Selecciona la definición correcta"
    pools:
      - cantidad: 15
        tipos: ["seleccion_multiple"]
```

**Ventajas:**
- Optimización automática según tipo de contenido
- Reduce páginas totales del examen
- Mantiene legibilidad donde importa
- Ahorro significativo de papel

---

## 💡 Mejores Prácticas

### Cuándo usar cada layout

#### ✅ Usa `default` para:
- Preguntas con bloques de código largos
- Análisis de algoritmos complejos
- Lecturas extensas
- Diagramas o tablas anchas
- Contenido que requiere espacio horizontal

#### ✅ Usa `compact-2col` para:
- Preguntas teóricas estándar
- Definiciones con explicaciones
- Opciones de longitud media (1-2 líneas)
- Balance entre densidad y legibilidad
- Exámenes de conceptos

#### ✅ Usa `compact-3col` para:
- Preguntas muy cortas (1 línea)
- Opciones breves (palabras o frases cortas)
- Listas de términos
- Verdadero/Falso con justificación
- Quizzes rápidos

### ⚠️ Evitar

- **No uses `compact-3col`** con código extenso
- **No uses `default`** si todas tus preguntas son cortas
- **No mezcles** código largo con layout compacto
- **No uses `compact-3col`** con opciones de varias líneas

---

## 📏 Dimensiones y Espaciado

### Layout Default
```css
grid-template-columns: 2fr 1fr;  /* 2/3 + 1/3 */
gap: 20px;
padding: 1em;
margin-bottom: 1.5em;
border: 1px solid #555;
```

### Layout Compact-2col
```css
display: block;
padding: 0.5em;
margin-bottom: 1em;

.options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.3em;
}
```

### Layout Compact-3col
```css
display: block;
padding: 0.5em;
margin-bottom: 0.8em;
font-size: 0.95em;

.options {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.2em;
}
```

---

## 🎯 Ejemplo Completo

Ver `examenes_prueba/examen_06_layouts.yaml` para un ejemplo funcional con los 3 layouts.

**Generar ejemplo:**
```bash
generador-examenes \
  -d examenes_prueba/examen_06_layouts.yaml \
  -i bancos/*.xml bancos/*.gift \
  -o output/demo_layouts \
  -n 1
```

**Resultado:**
- Parte 1: 5 preguntas con layout default
- Parte 2: 10 preguntas con layout 2 columnas
- Parte 3: 15 preguntas con layout 3 columnas
- Total: 30 preguntas en ~4-5 páginas (vs 8-10 con layout default)

---

## 📈 Impacto Ambiental

### Ahorro de Papel por Examen

**Ejemplo:** Examen de 30 preguntas para 40 estudiantes

| Layout | Páginas/Examen | Total Páginas | Ahorro |
|--------|----------------|---------------|--------|
| Solo `default` | 10 | 400 | - |
| Mixto (ejemplo) | 5 | 200 | **50%** |
| Solo `compact-3col` | 4 | 160 | **60%** |

**Impacto anual** (10 exámenes, 100 estudiantes):
- Default: 10,000 páginas
- Mixto: 5,000 páginas → **Ahorro: 5,000 páginas/año** 🌳

---

## 🔍 FAQ

**¿Puedo cambiar el layout después de crear el YAML?**
✅ Sí, solo edita el campo `layout` en cada sección.

**¿El layout afecta la generación de claves?**
✅ No, las claves mantienen el mismo layout que el examen.

**¿Los layouts son responsive?**
✅ Sí, se adaptan automáticamente al tamaño de página.

**¿Funcionan en PDF?**
✅ Sí, al generar PDF mantienen los estilos de impresión.

**¿Puedo crear layouts personalizados?**
⚠️ Actualmente no, pero puedes modificar las plantillas CSS.

---

## 🛠️ Personalización Avanzada

Si necesitas ajustar los estilos, edita:
```
templates/base_examen.html.j2
```

Busca las secciones:
- `/* --- Layout Default --- */`
- `/* --- Layout Compact-2col --- */`
- `/* --- Layout Compact-3col --- */`
- `@media print { ... }`

---

**Versión:** 5.3.0  
**Fecha:** 2025-11-04  
**Documentación completa:** [README.md](README.md)
