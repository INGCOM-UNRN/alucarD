# Ejemplos de Uso - alucarD

## Ejemplo 1: Generación Básica

```bash
generador-examenes \
  -d definicion.yaml \
  -i banco_preguntas.txt \
  -o ./examenes_generados \
  -n 3 \
  -f html
```

Esto genera 3 versiones de examen en formato HTML.

## Ejemplo 2: Múltiples Bancos y Formatos

```bash
generador-examenes \
  -d mi_examen.yaml \
  -i banco1.txt banco2.xml banco3.gift \
  -o ./output \
  -n 5 \
  -f html pdf
```

Genera 5 versiones en HTML y PDF usando preguntas de 3 bancos diferentes.

## Ejemplo 3: Validación Antes de Generar

```bash
generador-examenes \
  -d examen_final.yaml \
  -i preguntas.txt \
  --validate
```

Valida la definición sin generar archivos. Útil para verificar que hay suficientes preguntas.

## Ejemplo 4: Con Imágenes

```bash
generador-examenes \
  -d examen_con_imagenes.yaml \
  -i banco.txt \
  -p ./imagenes \
  -o ./output \
  -f html pdf
```

Las imágenes en `./imagenes` serán embebidas automáticamente en base64.

## Ejemplo 5: Semilla Personalizada

```bash
generador-examenes \
  -d definicion.yaml \
  -i banco.txt \
  -s 12345 \
  -n 10
```

Usa semilla 12345 para generar 10 temas reproducibles.

## Ejemplo 6: Modo Debug

```bash
generador-examenes \
  -d definicion.yaml \
  -i banco.txt \
  --debug
```

Activa logging detallado para depuración.

## Estructura de Definición YAML

```yaml
nombre_examen: "Examen Final de Programación"
institucion: "Universidad XYZ"
materia: "Programación Avanzada"
fecha: "2024-06-15"
duracion_minutos: 120
idioma: "es"

instrucciones_generales: |
  - Lee todas las preguntas antes de comenzar
  - Responde con claridad
  - Tiempo total: 2 horas

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  - nombre: "Sección A - Teoría"
    instrucciones: "Responde las siguientes preguntas teóricas"
    pools:
      # Seleccionar 10 preguntas de selección múltiple con etiquetas específicas
      - tipos: ["seleccion_multiple"]
        etiquetas: ["teoria", "conceptos"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
        accion_si_insuficiente: "advertir"
  
  - nombre: "Sección B - Práctica"
    pools:
      # Preguntas específicas obligatorias
      - preguntas_fijadas: 
          - "pregunta_clave_1"
          - "pregunta_clave_2"
          - "pregunta_clave_3"
  
  - nombre: "Sección C - Verdadero/Falso"
    pools:
      # Todas las preguntas de tipo verdadero/falso
      - tipos: ["verdadero_falso"]
        cantidad: 15
        puntaje_fijo_por_pregunta: 1.0
        accion_si_insuficiente: "usar_todas"
```

## Ejemplo con Categorías Anidadas

```yaml
nombre_examen: "Examen de Matemáticas por Jerarquía"
institucion: "Universidad XYZ"
materia: "Matemáticas"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  generar_clave_profesor: true

secciones_examen:
  - nombre: "Álgebra Completo"
    instrucciones: "Todas las preguntas de álgebra"
    pools:
      # Incluye Álgebra y todas sus subcategorías
      - categoria: "Matemáticas/Álgebra"
        cantidad: 10
  
  - nombre: "Solo Geometría Básica"
    pools:
      # Solo subcategorías directas de Geometría
      - categoria: "Matemáticas/Geometría/*"
        cantidad: 5
  
  - nombre: "Todo Matemáticas"
    pools:
      # Todas las categorías bajo Matemáticas (cualquier nivel)
      - categoria: "Matemáticas/**"
        cantidad: 15
```

Ver **CATEGORIAS.md** para documentación completa de categorías anidadas.

## Formato GIFT (banco_preguntas.txt)

```
// Comentario: preguntas de programación

::Pregunta 1::¿Qué es Python? {
=Un lenguaje de programación
~Un tipo de serpiente
~Un framework web
~Una base de datos
} [tags: python, basico]

::Pregunta 2::Python es interpretado. {T} [tags: python]

::Pregunta 3::¿Qué devuelve len([1,2,3])? {
=3
~4
~2
~Error
} [tags: python, listas]
```

## Formato Moodle XML (banco_preguntas.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta sobre OOP</text></name>
    <questiontext format="html">
      <text><![CDATA[¿Qué es encapsulamiento?]]></text>
    </questiontext>
    <defaultgrade>2.0</defaultgrade>
    <answer fraction="100">
      <text>Ocultar detalles de implementación</text>
    </answer>
    <answer fraction="0">
      <text>Crear muchas clases</text>
    </answer>
    <tags>
      <tag><text>oop</text></tag>
      <tag><text>conceptos</text></tag>
    </tags>
  </question>
</quiz>
```

## Filtros Disponibles en Pools

### Por Categoría
```yaml
pools:
  - categoria: "Algebra"
    cantidad: 5
```

### Por Tipo de Pregunta
```yaml
pools:
  - tipos: ["seleccion_multiple", "verdadero_falso"]
    cantidad: 10
```

### Por Etiquetas
```yaml
pools:
  - etiquetas: ["facil", "basico"]
    cantidad: 15
```

### Combinados
```yaml
pools:
  - categoria: "Matematicas"
    tipos: ["seleccion_multiple"]
    etiquetas: ["algebra", "facil"]
    cantidad: 8
    puntaje_fijo_por_pregunta: 2.5
```

## Acciones si Insuficientes Preguntas

- `error`: Detiene la ejecución (por defecto)
- `advertir`: Muestra warning y usa las disponibles
- `usar_todas`: Usa todas sin advertir

```yaml
pools:
  - cantidad: 20
    accion_si_insuficiente: "usar_todas"
```

## Tips

1. **Validar primero**: Usa `--validate` antes de generar
2. **Semilla fija**: Usa la misma semilla para reproducir versiones
3. **Etiquetas claras**: Usa tags descriptivos en tus preguntas
4. **Prueba incremental**: Empieza con pocos temas y formatos
5. **HTML primero**: Si PDF falla, genera HTML y convierte después
