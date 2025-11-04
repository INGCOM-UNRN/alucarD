# Categorías Anidadas en alucarD

alucarD soporta categorías jerárquicas (anidadas) para organizar preguntas de forma estructurada, similar al sistema de categorías de Moodle.

## Formato de Categorías

Las categorías pueden organizarse jerárquicamente usando barras (`/`) como separador:

```
Matemáticas
Matemáticas/Álgebra
Matemáticas/Álgebra/Lineal
Matemáticas/Álgebra/Lineal/Vectores
Matemáticas/Geometría
Física
Física/Mecánica
```

### Formatos Soportados

```yaml
# Formato simple
categoria: "Matemáticas"

# Formato anidado con /
categoria: "Matemáticas/Álgebra"

# Formato Moodle
categoria: "$course$/top/Matemáticas/Álgebra"

# También se aceptan backslashes (se convierten automáticamente)
categoria: "Matemáticas\\Álgebra"
```

## Filtrado de Categorías

### 1. Coincidencia Exacta

```yaml
pools:
  - categoria: "Matemáticas/Álgebra"
    cantidad: 5
```

Selecciona preguntas de la categoría **exacta** `Matemáticas/Álgebra`.

### 2. Subcategorías (por defecto)

```yaml
pools:
  - categoria: "Matemáticas/Álgebra"
    cantidad: 10
```

Selecciona preguntas de `Matemáticas/Álgebra` **y todas sus subcategorías**:
- `Matemáticas/Álgebra` ✅
- `Matemáticas/Álgebra/Lineal` ✅
- `Matemáticas/Álgebra/Lineal/Vectores` ✅
- `Matemáticas/Geometría` ❌ (diferente rama)

### 3. Wildcard Simple (`/*`)

```yaml
pools:
  - categoria: "Matemáticas/*"
    cantidad: 10
```

Selecciona solo subcategorías **de primer nivel** bajo `Matemáticas`:
- `Matemáticas/Álgebra` ✅
- `Matemáticas/Geometría` ✅
- `Matemáticas/Álgebra/Lineal` ❌ (segundo nivel)

### 4. Wildcard Recursivo (`/**`)

```yaml
pools:
  - categoria: "Matemáticas/**"
    cantidad: 20
```

Selecciona **todas las subcategorías** en cualquier nivel bajo `Matemáticas`:
- `Matemáticas` ✅
- `Matemáticas/Álgebra` ✅
- `Matemáticas/Álgebra/Lineal` ✅
- `Matemáticas/Álgebra/Lineal/Vectores` ✅
- `Matemáticas/Geometría` ✅

## Ejemplos Prácticos

### Ejemplo 1: Examen por Niveles

```yaml
secciones_examen:
  - nombre: "Sección A - Básico"
    pools:
      - categoria: "Matemáticas/Básico/**"
        cantidad: 10
        
  - nombre: "Sección B - Avanzado"
    pools:
      - categoria: "Matemáticas/Avanzado/**"
        cantidad: 10
```

### Ejemplo 2: Combinar Múltiples Categorías

```yaml
secciones_examen:
  - nombre: "Álgebra y Geometría"
    pools:
      - categoria: "Matemáticas/Álgebra"
        cantidad: 5
      - categoria: "Matemáticas/Geometría"
        cantidad: 5
```

### Ejemplo 3: Categorías de Moodle

```yaml
secciones_examen:
  - nombre: "Programación"
    pools:
      - categoria: "$course$/top/Programación/Python"
        cantidad: 10
      - categoria: "$course$/top/Programación/Java"
        cantidad: 5
```

### Ejemplo 4: Selección por Rama Completa

```yaml
secciones_examen:
  - nombre: "Todo de Física"
    pools:
      - categoria: "Física/**"
        cantidad: 20
```

## Características

### Case-Insensitive

Las categorías **no distinguen mayúsculas/minúsculas**:

```yaml
# Estos son equivalentes:
categoria: "Matemáticas/Álgebra"
categoria: "matemáticas/álgebra"
categoria: "MATEMÁTICAS/ÁLGEBRA"
```

### Normalización Automática

El sistema normaliza automáticamente:
- Espacios extras: `"Math / Algebra "` → `"math/algebra"`
- Backslashes: `"Math\\Algebra"` → `"math/algebra"`
- Slashes dobles: `"Math//Algebra"` → `"math/algebra"`
- Slash final: `"Math/Algebra/"` → `"math/algebra"`

### Compatible con Parsers

Ambos parsers (GIFT y Moodle XML) extraen y preservan categorías jerárquicas:

**GIFT:**
```gift
$CATEGORY: Matemáticas/Álgebra/Lineal

::Pregunta 1::¿Qué es un vector? {
=Magnitud con dirección
~Solo magnitud
}
```

**Moodle XML:**
```xml
<question type="category">
  <category>
    <text>$course$/Matemáticas/Álgebra/Lineal</text>
  </category>
</question>
```

## Casos de Uso

### 1. Organización por Tema

```
Examen/
├── Tema 1/
│   ├── Básico
│   └── Avanzado
├── Tema 2/
│   ├── Básico
│   └── Avanzado
└── Tema 3/
    ├── Básico
    └── Avanzado
```

```yaml
pools:
  - categoria: "Examen/Tema 1/**"
    cantidad: 10
```

### 2. Organización por Dificultad

```
Matemáticas/
├── Fácil/
├── Medio/
└── Difícil/
```

```yaml
pools:
  - categoria: "Matemáticas/Fácil"
    cantidad: 5
  - categoria: "Matemáticas/Medio"
    cantidad: 3
  - categoria: "Matemáticas/Difícil"
    cantidad: 2
```

### 3. Organización Mixta

```
Programación/
├── Python/
│   ├── Básico/
│   │   ├── Variables
│   │   └── Operadores
│   └── Avanzado/
│       ├── OOP
│       └── Decoradores
└── Java/
    ├── Básico/
    └── Avanzado/
```

```yaml
pools:
  - categoria: "Programación/Python/Básico/**"
    cantidad: 10
  - categoria: "Programación/Python/Avanzado/**"
    cantidad: 5
```

## Compatibilidad con Moodle

Las categorías anidadas siguen el mismo formato que Moodle:

- Separador: `/` (forward slash)
- Prefijo opcional: `$course$/`
- Case-insensitive en Moodle (respetado aquí)

Esto permite **importar bancos de Moodle directamente** sin modificar categorías.

## Logging y Debugging

Usa `--debug` para ver el filtrado de categorías:

```bash
generador-examenes -d def.yaml -i banco.txt --debug
```

Output:
```
DEBUG: Filtro categoría 'Matemáticas/Álgebra': 15 candidatas
DEBUG: Categorías encontradas:
  - Matemáticas/Álgebra (3 preguntas)
  - Matemáticas/Álgebra/Lineal (8 preguntas)
  - Matemáticas/Álgebra/Lineal/Vectores (4 preguntas)
```

## Migración desde Versiones Anteriores

Si usabas categorías simples sin jerarquía, todo sigue funcionando igual:

```yaml
# Esto sigue funcionando
pools:
  - categoria: "Matemáticas"
    cantidad: 10
```

Para aprovechar categorías anidadas, simplemente usa `/` en tus categorías:

```yaml
# Nueva forma
pools:
  - categoria: "Matemáticas/Álgebra"
    cantidad: 10
```

## Mejores Prácticas

1. **Usa estructura jerárquica consistente**
   ```
   Materia/Tema/Subtema/Concepto
   ```

2. **No uses nombres muy largos**
   ```
   ✅ Math/Algebra/Linear
   ❌ Mathematics/Advanced_Algebra_Level_2/Linear_Algebra_Vectors
   ```

3. **Usa Case consistente en tus bancos**
   ```
   ✅ Math/Algebra, Math/Geometry
   ❌ Math/Algebra, math/GEOMETRY
   ```

4. **Documenta tu jerarquía**
   Mantén un documento con tu estructura de categorías.

5. **Combina con etiquetas**
   ```yaml
   pools:
     - categoria: "Math/Algebra"
       etiquetas: ["facil"]
       cantidad: 5
   ```

## Limitaciones

- No hay límite en la profundidad de anidamiento
- Los nombres de categorías no pueden contener `/` o `\` (son separadores)
- El wildcard `*` solo se soporta al final (`Math/*`, no `*/Algebra`)
