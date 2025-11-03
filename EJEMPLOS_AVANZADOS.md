# Ejemplos de Uso Avanzado - alucarD

Guía completa de casos de uso avanzados con el generador de exámenes alucarD.

## Tabla de Contenidos

1. [Exámenes Multi-nivel con Ponderación](#1-exámenes-multi-nivel-con-ponderación)
2. [Examen Adaptativo por Dificultad](#2-examen-adaptativo-por-dificultad)
3. [Examen con Preguntas Fijadas y Aleatorias](#3-examen-con-preguntas-fijadas-y-aleatorias)
4. [Examen Multi-materia con Categorías Anidadas](#4-examen-multi-materia-con-categorías-anidadas)
5. [Examen con Filtrado Complejo](#5-examen-con-filtrado-complejo)
6. [Generación Masiva de Exámenes](#6-generación-masiva-de-exámenes)
7. [Examen con Múltiples Bancos](#7-examen-con-múltiples-bancos)
8. [Examen Tipo Parcial con Secciones Temáticas](#8-examen-tipo-parcial-con-secciones-temáticas)
9. [Examen Final Comprehensivo](#9-examen-final-comprehensivo)
10. [Pipeline de Producción Automatizado](#10-pipeline-de-producción-automatizado)

---

## 1. Exámenes Multi-nivel con Ponderación

Crear exámenes que evalúan diferentes niveles de conocimiento con puntajes diferenciados.

### definicion_multinivel.yaml

```yaml
nombre_examen: "Examen de Programación - Evaluación por Niveles"
institucion: "Instituto Tecnológico Superior"
materia: "Programación Orientada a Objetos"
fecha: "2024-12-20"
duracion_minutos: 180
instrucciones_generales: |
  Este examen evalúa conocimientos en tres niveles de complejidad.
  Cada nivel tiene diferente ponderación.
  
  Nivel Básico: 30% (1 punto c/u)
  Nivel Intermedio: 40% (2 puntos c/u)
  Nivel Avanzado: 30% (3 puntos c/u)
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  incluir_metadata_debug: true

secciones_examen:
  # Nivel Básico - 15 preguntas × 1 punto = 15 puntos
  - nombre: "Parte 1 - Conocimientos Fundamentales"
    instrucciones: |
      Conceptos básicos de POO.
      Tiempo sugerido: 45 minutos
    pools:
      - categoria: "POO/Conceptos/Básico"
        tipos: ["seleccion_multiple", "verdadero_falso"]
        cantidad: 15
        puntaje_fijo_por_pregunta: 1.0
        accion_si_insuficiente: "advertir"
  
  # Nivel Intermedio - 10 preguntas × 2 puntos = 20 puntos
  - nombre: "Parte 2 - Aplicación de Conceptos"
    instrucciones: |
      Aplicación práctica de POO.
      Tiempo sugerido: 60 minutos
    pools:
      - categoria: "POO/Aplicaciones/Intermedio"
        tipos: ["seleccion_multiple"]
        etiquetas: ["codigo", "analisis"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
        accion_si_insuficiente: "advertir"
  
  # Nivel Avanzado - 5 preguntas × 3 puntos = 15 puntos
  - nombre: "Parte 3 - Diseño y Análisis"
    instrucciones: |
      Diseño de soluciones complejas.
      Tiempo sugerido: 75 minutos
    pools:
      - categoria: "POO/Diseño/Avanzado"
        tipos: ["seleccion_multiple"]
        etiquetas: ["diseño", "patrones", "arquitectura"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 3.0
        accion_si_insuficiente: "error"
```

### Ejecutar:

```bash
# Generar 5 versiones diferentes
generador-examenes \
  -d definicion_multinivel.yaml \
  -i banco_poo.txt \
  -n 5 \
  -s 12345 \
  -o examenes_multinivel/ \
  --debug

# Validar primero
generador-examenes \
  -d definicion_multinivel.yaml \
  -i banco_poo.txt \
  --validate
```

**Total:** 30 preguntas, 50 puntos (15+20+15)

---

## 2. Examen Adaptativo por Dificultad

Examen que progresa en dificultad basándose en etiquetas.

### definicion_adaptativo.yaml

```yaml
nombre_examen: "Evaluación Diagnóstica Adaptativa"
institucion: "Centro de Capacitación Profesional"
materia: "Matemáticas"
fecha: "2024-12-20"
duracion_minutos: 90

configuracion_examen:
  mezclar_preguntas_dentro_seccion: false  # Mantener orden de dificultad
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  # Fase 1: Calentamiento
  - nombre: "Fase 1 - Diagnóstico Inicial"
    instrucciones: "Preguntas básicas para establecer nivel base"
    pools:
      - categoria: "Matemáticas/**"
        etiquetas: ["facil", "diagnostico"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 1.0
        accion_si_insuficiente: "usar_todas"
  
  # Fase 2: Nivel estándar
  - nombre: "Fase 2 - Evaluación Estándar"
    instrucciones: "Preguntas de dificultad media"
    pools:
      - categoria: "Matemáticas/**"
        etiquetas: ["medio"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
        accion_si_insuficiente: "advertir"
  
  # Fase 3: Desafío
  - nombre: "Fase 3 - Nivel Avanzado"
    instrucciones: "Preguntas desafiantes para evaluación completa"
    pools:
      - categoria: "Matemáticas/**"
        etiquetas: ["dificil", "desafio"]
        cantidad: 8
        puntaje_fijo_por_pregunta: 3.0
        accion_si_insuficiente: "advertir"
  
  # Fase 4: Bonus
  - nombre: "Fase 4 - Bonus (Opcional)"
    instrucciones: "Preguntas extra para puntos adicionales"
    pools:
      - categoria: "Matemáticas/**"
        etiquetas: ["experto", "olimpiada"]
        cantidad: 2
        puntaje_fijo_por_pregunta: 5.0
        accion_si_insuficiente: "usar_todas"
```

### Ejecutar:

```bash
generador-examenes \
  -d definicion_adaptativo.yaml \
  -i banco_mates.txt banco_olimpiada.txt \
  -n 10 \
  -f html pdf \
  -o diagnosticos/
```

---

## 3. Examen con Preguntas Fijadas y Aleatorias

Combinar preguntas obligatorias específicas con selección aleatoria.

### definicion_mixto.yaml

```yaml
nombre_examen: "Examen Parcial - Bases de Datos"
institucion: "Universidad Nacional"
materia: "Bases de Datos Relacionales"
fecha: "2024-12-20"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  # Preguntas obligatorias clave
  - nombre: "Parte 1 - Conceptos Esenciales (Obligatorias)"
    instrucciones: "Estas preguntas evalúan conceptos fundamentales"
    pools:
      # Pool de preguntas fijadas
      - preguntas_fijadas:
          - "normalizacion_3fn"
          - "acid_properties"
          - "primary_key_def"
          - "join_types"
          - "transaction_concept"
        # Las preguntas fijadas no se mezclan entre sí
  
  # Preguntas aleatorias de SQL
  - nombre: "Parte 2 - SQL Básico"
    instrucciones: "Consultas SELECT básicas"
    pools:
      - categoria: "SQL/Consultas/Básico"
        tipos: ["seleccion_multiple"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
  
  # Mezcla de fijadas y aleatorias
  - nombre: "Parte 3 - Diseño de Bases de Datos"
    pools:
      # Primero una pregunta obligatoria
      - preguntas_fijadas:
          - "er_diagram_reading"
      # Luego preguntas aleatorias del mismo tema
      - categoria: "Diseño/ER"
        cantidad: 3
        puntaje_fijo_por_pregunta: 3.0
        accion_si_insuficiente: "usar_todas"
  
  # SQL Avanzado completamente aleatorio
  - nombre: "Parte 4 - SQL Avanzado"
    pools:
      - categoria: "SQL/**"
        etiquetas: ["join", "subquery", "agregacion"]
        cantidad: 6
        puntaje_fijo_por_pregunta: 3.0
```

### Ejecutar:

```bash
# Generar con semilla fija para reproducibilidad
generador-examenes \
  -d definicion_mixto.yaml \
  -i banco_bd.txt \
  -n 8 \
  -s 2024 \
  -o parciales_bd/
```

---

## 4. Examen Multi-materia con Categorías Anidadas

Examen que cubre múltiples materias usando jerarquías complejas.

### definicion_multimateria.yaml

```yaml
nombre_examen: "Examen Integral - Ingeniería de Software"
institucion: "Facultad de Ingeniería"
materia: "Evaluación Comprehensiva"
fecha: "2024-12-20"
duracion_minutos: 240

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  # Sección 1: Fundamentos (varias materias básicas)
  - nombre: "Fundamentos de Computación"
    pools:
      - categoria: "Algoritmos/Básico"
        cantidad: 3
      - categoria: "Estructuras/Básico"
        cantidad: 3
      - categoria: "POO/Básico"
        cantidad: 3
      - categoria: "Bases_Datos/Básico"
        cantidad: 3
  
  # Sección 2: Desarrollo de Software (categorías anidadas)
  - nombre: "Desarrollo y Diseño"
    pools:
      # Todo lo de patrones de diseño
      - categoria: "POO/Patrones/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      # Arquitecturas
      - categoria: "Arquitectura/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
  
  # Sección 3: Bases de Datos (todos los niveles)
  - nombre: "Gestión de Datos"
    pools:
      # SQL de cualquier nivel
      - categoria: "Bases_Datos/SQL/**"
        cantidad: 6
      # Diseño de cualquier nivel
      - categoria: "Bases_Datos/Diseño/**"
        cantidad: 4
  
  # Sección 4: Calidad y Pruebas
  - nombre: "Aseguramiento de Calidad"
    pools:
      - categoria: "Testing/**"
        etiquetas: ["unitario", "integracion"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      - categoria: "QA/**"
        cantidad: 3
        puntaje_fijo_por_pregunta: 2.0
  
  # Sección 5: Gestión de Proyectos
  - nombre: "Gestión y Metodologías"
    pools:
      # Metodologías ágiles
      - categoria: "Metodologias/Agiles/**"
        cantidad: 4
      # Gestión tradicional
      - categoria: "Metodologias/Tradicionales/**"
        cantidad: 3
      # DevOps
      - categoria: "DevOps/**"
        cantidad: 3
  
  # Sección 6: Integración (lo más difícil de todo)
  - nombre: "Casos Integrados"
    instrucciones: "Problemas que requieren conocimiento transversal"
    pools:
      - categoria: "POO/Avanzado"
        etiquetas: ["integracion", "caso_estudio"]
        cantidad: 2
        puntaje_fijo_por_pregunta: 5.0
      - categoria: "Arquitectura/Avanzado"
        etiquetas: ["integracion", "diseño_complejo"]
        cantidad: 2
        puntaje_fijo_por_pregunta: 5.0
```

### Ejecutar:

```bash
# Usar múltiples bancos
generador-examenes \
  -d definicion_multimateria.yaml \
  -i banco_poo.txt banco_bd.txt banco_testing.txt banco_agil.txt \
  -n 5 \
  -o examen_integral/ \
  -f html pdf
```

---

## 5. Examen con Filtrado Complejo

Uso avanzado de filtros combinados para selección precisa.

### definicion_filtros_complejos.yaml

```yaml
nombre_examen: "Evaluación Especializada - Data Science"
institucion: "Academia de Ciencia de Datos"
materia: "Machine Learning Avanzado"
fecha: "2024-12-20"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  # Filtro 1: Categoría + Tipo específico
  - nombre: "Fundamentos Teóricos"
    pools:
      - categoria: "ML/Teoria/**"
        tipos: ["seleccion_multiple"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
  
  # Filtro 2: Categoría + Etiquetas específicas
  - nombre: "Algoritmos Supervisados"
    pools:
      - categoria: "ML/Supervisado/**"
        etiquetas: ["clasificacion", "regresion"]
        cantidad: 8
        puntaje_fijo_por_pregunta: 2.5
  
  # Filtro 3: Categoría específica + múltiples etiquetas (OR)
  - nombre: "Deep Learning"
    pools:
      - categoria: "ML/DeepLearning/CNN"
        etiquetas: ["vision", "arquitecturas"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 3.0
      - categoria: "ML/DeepLearning/RNN"
        etiquetas: ["secuencias", "nlp"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 3.0
  
  # Filtro 4: Wildcard + tipo + etiquetas
  - nombre: "Evaluación y Métricas"
    pools:
      - categoria: "ML/*/Evaluacion"
        tipos: ["seleccion_multiple"]
        etiquetas: ["metricas", "validacion"]
        cantidad: 6
        puntaje_fijo_por_pregunta: 2.0
  
  # Filtro 5: Múltiples pools del mismo tema
  - nombre: "Casos Prácticos"
    pools:
      # Básicos
      - categoria: "ML/Practico/Basico"
        etiquetas: ["codigo", "implementacion"]
        cantidad: 3
        puntaje_fijo_por_pregunta: 2.0
      # Intermedios
      - categoria: "ML/Practico/Intermedio"
        etiquetas: ["codigo", "implementacion"]
        cantidad: 2
        puntaje_fijo_por_pregunta: 3.0
      # Avanzados
      - categoria: "ML/Practico/Avanzado"
        etiquetas: ["codigo", "implementacion", "optimizacion"]
        cantidad: 2
        puntaje_fijo_por_pregunta: 4.0
  
  # Filtro 6: Categoría amplia con restricciones
  - nombre: "Preguntas Especiales"
    pools:
      - categoria: "ML/**"
        tipos: ["verdadero_falso"]
        etiquetas: ["mitos", "conceptos_erroneos"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 1.0
        accion_si_insuficiente: "usar_todas"
```

### Ejecutar:

```bash
generador-examenes \
  -d definicion_filtros_complejos.yaml \
  -i banco_ml.txt banco_dl.txt \
  -n 3 \
  -s 42 \
  -o ml_exams/
```

---

## 6. Generación Masiva de Exámenes

Script para generar múltiples exámenes con diferentes configuraciones.

### script_generacion_masiva.sh

```bash
#!/bin/bash
# Script para generar exámenes masivos

BANCO_DIR="./bancos"
OUTPUT_BASE="./examenes_2024"
DEFINICIONES_DIR="./definiciones"

# Función para generar exámenes
generar_examen() {
    local def=$1
    local num_versiones=$2
    local semilla=$3
    local grupo=$4
    
    echo "Generando $num_versiones versiones de $def..."
    
    generador-examenes \
        -d "$DEFINICIONES_DIR/$def" \
        -i $BANCO_DIR/*.txt \
        -n $num_versiones \
        -s $semilla \
        -o "$OUTPUT_BASE/$grupo/" \
        -f html pdf \
        --debug > "$OUTPUT_BASE/$grupo/log_generacion.txt" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Generado exitosamente: $grupo"
    else
        echo "❌ Error generando: $grupo"
        return 1
    fi
}

# Crear estructura de directorios
mkdir -p "$OUTPUT_BASE"/{grupo_A,grupo_B,grupo_C,parcial1,parcial2,final}

# Generar exámenes por grupo
echo "=== Generación Masiva de Exámenes ==="
echo ""

# Grupo A: 30 estudiantes → 30 versiones
generar_examen "parcial1.yaml" 30 1000 "grupo_A"

# Grupo B: 25 estudiantes → 25 versiones
generar_examen "parcial1.yaml" 25 2000 "grupo_B"

# Grupo C: 28 estudiantes → 28 versiones
generar_examen "parcial1.yaml" 28 3000 "grupo_C"

# Parciales adicionales
generar_examen "parcial2.yaml" 30 4000 "parcial2"

# Examen final (más versiones por seguridad)
generar_examen "final.yaml" 50 5000 "final"

echo ""
echo "=== Resumen ==="
echo "Total de archivos generados:"
find "$OUTPUT_BASE" -name "*.pdf" | wc -l
find "$OUTPUT_BASE" -name "*.html" | wc -l

# Generar índice
cat > "$OUTPUT_BASE/indice.txt" << EOF
Índice de Exámenes Generados
=============================
Fecha: $(date)

Grupo A: 30 versiones
Grupo B: 25 versiones
Grupo C: 28 versiones
Parcial 2: 30 versiones
Final: 50 versiones

Total: 163 versiones
EOF

echo "✅ Generación masiva completada"
```

### Uso:

```bash
chmod +x script_generacion_masiva.sh
./script_generacion_masiva.sh
```

---

## 7. Examen con Múltiples Bancos

Combinar preguntas de diferentes fuentes.

### definicion_multi_banco.yaml

```yaml
nombre_examen: "Examen Comprehensivo - Full Stack"
institucion: "Bootcamp de Desarrollo Web"
materia: "Desarrollo Full Stack"
fecha: "2024-12-20"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true

secciones_examen:
  # Frontend (del banco de frontend)
  - nombre: "Frontend Development"
    pools:
      - categoria: "Frontend/HTML/**"
        cantidad: 5
      - categoria: "Frontend/CSS/**"
        cantidad: 5
      - categoria: "Frontend/JavaScript/**"
        cantidad: 8
      - categoria: "Frontend/React/**"
        cantidad: 7
  
  # Backend (del banco de backend)
  - nombre: "Backend Development"
    pools:
      - categoria: "Backend/NodeJS/**"
        cantidad: 8
      - categoria: "Backend/Express/**"
        cantidad: 5
      - categoria: "Backend/APIs/**"
        cantidad: 7
  
  # Bases de Datos (del banco de BD)
  - nombre: "Databases"
    pools:
      - categoria: "Bases_Datos/SQL/**"
        cantidad: 6
      - categoria: "Bases_Datos/NoSQL/**"
        cantidad: 4
      - categoria: "Bases_Datos/ORM/**"
        cantidad: 3
  
  # DevOps (del banco de DevOps)
  - nombre: "Deployment & DevOps"
    pools:
      - categoria: "DevOps/Git/**"
        cantidad: 4
      - categoria: "DevOps/CI_CD/**"
        cantidad: 3
      - categoria: "DevOps/Docker/**"
        cantidad: 3
  
  # Integración (preguntas que requieren conocimiento de múltiples áreas)
  - nombre: "Proyecto Integrado"
    instrucciones: "Preguntas que integran frontend, backend y BD"
    pools:
      - categoria: "Proyectos/FullStack/**"
        etiquetas: ["integracion", "arquitectura"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 5.0
        accion_si_insuficiente: "usar_todas"
```

### Ejecutar con múltiples bancos:

```bash
generador-examenes \
  -d definicion_multi_banco.yaml \
  -i \
    bancos/frontend_moodle.xml \
    bancos/backend_gift.txt \
    bancos/database.xml \
    bancos/devops.txt \
    bancos/proyectos.txt \
  -n 10 \
  -o fullstack_exams/ \
  -f html pdf
```

---

## 8. Examen Tipo Parcial con Secciones Temáticas

Examen universitario típico con múltiples temas.

### definicion_parcial_universidad.yaml

```yaml
nombre_examen: "Primer Parcial - Algoritmos y Estructuras de Datos"
institucion: "Universidad Tecnológica Nacional"
materia: "Algoritmos y Estructuras de Datos"
docente: "Prof. García, María"
fecha: "2024-12-20"
duracion_minutos: 120
instrucciones_generales: |
  INSTRUCCIONES GENERALES:
  
  1. El examen consta de 5 secciones temáticas
  2. Cada sección tiene un valor específico
  3. Lea cuidadosamente cada pregunta
  4. Las preguntas de selección múltiple tienen una sola respuesta correcta
  5. No se admiten consultas durante el examen
  6. Entregue la hoja de respuestas al finalizar
  
  ¡ÉXITOS!

idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  incluir_metadata_debug: false

secciones_examen:
  # Tema 1: Complejidad Algorítmica (20%)
  - nombre: "I. Análisis de Complejidad"
    instrucciones: |
      Valor: 20 puntos
      Preguntas sobre notación Big-O, análisis de tiempo y espacio.
    pools:
      - categoria: "Algoritmos/Complejidad/**"
        tipos: ["seleccion_multiple"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
        accion_si_insuficiente: "error"
  
  # Tema 2: Estructuras Lineales (20%)
  - nombre: "II. Estructuras de Datos Lineales"
    instrucciones: |
      Valor: 20 puntos
      Arrays, Listas Enlazadas, Pilas, Colas.
    pools:
      - categoria: "Estructuras/Lineales/Arrays"
        cantidad: 3
        puntaje_fijo_por_pregunta: 2.0
      - categoria: "Estructuras/Lineales/Listas"
        cantidad: 3
        puntaje_fijo_por_pregunta: 2.0
      - categoria: "Estructuras/Lineales/Pilas"
        cantidad: 2
        puntaje_fijo_por_pregunta: 2.0
      - categoria: "Estructuras/Lineales/Colas"
        cantidad: 2
        puntaje_fijo_por_pregunta: 2.0
  
  # Tema 3: Árboles (25%)
  - nombre: "III. Árboles"
    instrucciones: |
      Valor: 25 puntos
      Árboles binarios, BST, AVL, recorridos.
    pools:
      - categoria: "Estructuras/Arboles/Binarios"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.5
      - categoria: "Estructuras/Arboles/BST"
        cantidad: 3
        puntaje_fijo_por_pregunta: 2.5
      - categoria: "Estructuras/Arboles/AVL"
        cantidad: 2
        puntaje_fijo_por_pregunta: 2.5
  
  # Tema 4: Ordenamiento (20%)
  - nombre: "IV. Algoritmos de Ordenamiento"
    instrucciones: |
      Valor: 20 puntos
      Bubble, Quick, Merge, Heap Sort.
    pools:
      - categoria: "Algoritmos/Ordenamiento/**"
        tipos: ["seleccion_multiple"]
        cantidad: 10
        puntaje_fijo_por_pregunta: 2.0
        accion_si_insuficiente: "advertir"
  
  # Tema 5: Búsqueda y Grafos (15%)
  - nombre: "V. Búsqueda y Grafos"
    instrucciones: |
      Valor: 15 puntos
      Búsqueda binaria, BFS, DFS.
    pools:
      - categoria: "Algoritmos/Busqueda/**"
        cantidad: 4
        puntaje_fijo_por_pregunta: 2.5
      - categoria: "Estructuras/Grafos/Basico"
        cantidad: 2
        puntaje_fijo_por_pregunta: 2.5
```

### Ejecutar:

```bash
# Validar primero
generador-examenes \
  -d definicion_parcial_universidad.yaml \
  -i banco_algoritmos.txt \
  --validate

# Generar 40 versiones (para curso de 40 alumnos)
generador-examenes \
  -d definicion_parcial_universidad.yaml \
  -i banco_algoritmos.txt \
  -n 40 \
  -s 20241220 \
  -o parcial1_algo/ \
  -f pdf
```

---

## 9. Examen Final Comprehensivo

Examen final que cubre todo el curso con ponderación especial.

### definicion_final_comprehensivo.yaml

```yaml
nombre_examen: "EXAMEN FINAL - Ingeniería de Software"
institucion: "Facultad de Ingeniería - UBA"
materia: "Ingeniería de Software II"
carrera: "Ingeniería en Sistemas de Información"
docentes:
  - "Prof. Titular: Dr. Martínez, Juan"
  - "Prof. Adjunto: Ing. López, Ana"
fecha: "2024-12-20"
duracion_minutos: 180
instrucciones_generales: |
  EXAMEN FINAL - INGENIERÍA DE SOFTWARE II
  =========================================
  
  Este examen evalúa los conocimientos adquiridos durante todo el cuatrimestre.
  
  ESTRUCTURA:
  • Parte I: Conceptos Fundamentales (25%)
  • Parte II: Análisis y Diseño (30%)
  • Parte III: Implementación (25%)
  • Parte IV: Calidad y Pruebas (20%)
  
  PUNTAJE TOTAL: 100 puntos
  APROBACIÓN: 60 puntos
  
  IMPORTANTE:
  - No se permiten materiales de consulta
  - Tiempo: 3 horas
  - Entregar hoja de respuestas al finalizar
  
  ¡Mucha suerte!

idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  incluir_metadata_debug: false

secciones_examen:
  # PARTE I: Fundamentos (25 puntos)
  - nombre: "PARTE I - Fundamentos de Ingeniería de Software"
    instrucciones: |
      Valor: 25 puntos
      Conceptos teóricos fundamentales del curso.
      Tiempo sugerido: 40 minutos
    pools:
      # Procesos de software
      - categoria: "IS/Procesos/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      
      # Metodologías
      - categoria: "IS/Metodologias/**"
        tipos: ["seleccion_multiple"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      
      # Requisitos
      - categoria: "IS/Requisitos/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 1.0
  
  # PARTE II: Análisis y Diseño (30 puntos)
  - nombre: "PARTE II - Análisis y Diseño"
    instrucciones: |
      Valor: 30 puntos
      UML, patrones de diseño, arquitectura.
      Tiempo sugerido: 50 minutos
    pools:
      # UML
      - categoria: "IS/UML/**"
        cantidad: 6
        puntaje_fijo_por_pregunta: 2.0
      
      # Patrones de diseño (preguntas clave fijas)
      - preguntas_fijadas:
          - "patron_singleton"
          - "patron_factory"
          - "patron_observer"
      
      # Más patrones aleatorios
      - categoria: "IS/Patrones/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      
      # Arquitectura
      - categoria: "IS/Arquitectura/**"
        cantidad: 4
        puntaje_fijo_por_pregunta: 3.0
  
  # PARTE III: Implementación (25 puntos)
  - nombre: "PARTE III - Implementación y Código"
    instrucciones: |
      Valor: 25 puntos
      Codificación, refactoring, buenas prácticas.
      Tiempo sugerido: 45 minutos
    pools:
      # Código limpio
      - categoria: "IS/Codigo/CleanCode/**"
        etiquetas: ["buenas_practicas"]
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      
      # Refactoring
      - categoria: "IS/Codigo/Refactoring/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 2.0
      
      # SOLID
      - categoria: "IS/Principios/SOLID/**"
        cantidad: 5
        puntaje_fijo_por_pregunta: 1.0
  
  # PARTE IV: Calidad y Pruebas (20 puntos)
  - nombre: "PARTE IV - Aseguramiento de Calidad"
    instrucciones: |
      Valor: 20 puntos
      Testing, QA, mantenimiento.
      Tiempo sugerido: 35 minutos
    pools:
      # Testing
      - categoria: "IS/Testing/**"
        tipos: ["seleccion_multiple"]
        cantidad: 8
        puntaje_fijo_por_pregunta: 2.0
      
      # Calidad
      - categoria: "IS/Calidad/**"
        cantidad: 4
        puntaje_fijo_por_pregunta: 1.0
```

### Ejecutar:

```bash
# Generar con múltiples formatos
generador-examenes \
  -d definicion_final_comprehensivo.yaml \
  -i banco_is_completo.txt banco_patrones.txt banco_testing.txt \
  -n 50 \
  -s 2024FIN \
  -o final_is2/ \
  -f html pdf

# Verificar puntajes totales
grep -r "Puntaje Total" final_is2/*.html | head -5
```

---

## 10. Pipeline de Producción Automatizado

Sistema completo de generación, validación y distribución.

### Makefile

```makefile
# Makefile para automatizar generación de exámenes

# Variables
PYTHON := python3
GEN := generador-examenes
BANCO_DIR := bancos
DEF_DIR := definiciones
OUT_DIR := examenes_generados
LOG_DIR := logs

# Fechas y versiones
DATE := $(shell date +%Y%m%d)
SEMESTER := 2024_2

# Colores para output
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m

.PHONY: all clean validate generate distribute report

all: clean validate generate report

# Limpiar outputs previos
clean:
	@echo "$(CYAN)Limpiando directorios...$(NC)"
	rm -rf $(OUT_DIR)/*
	rm -rf $(LOG_DIR)/*
	mkdir -p $(OUT_DIR) $(LOG_DIR)

# Validar todas las definiciones
validate:
	@echo "$(CYAN)Validando definiciones...$(NC)"
	@for def in $(DEF_DIR)/*.yaml; do \
		echo "Validando $$def..."; \
		$(GEN) -d $$def -i $(BANCO_DIR)/*.txt --validate || exit 1; \
	done
	@echo "$(GREEN)✓ Todas las definiciones son válidas$(NC)"

# Generar exámenes
generate: validate
	@echo "$(CYAN)Generando exámenes...$(NC)"
	$(MAKE) parcial1
	$(MAKE) parcial2
	$(MAKE) final
	$(MAKE) recuperatorio
	@echo "$(GREEN)✓ Todos los exámenes generados$(NC)"

# Parcial 1
parcial1:
	@echo "$(CYAN)Generando Parcial 1...$(NC)"
	@mkdir -p $(OUT_DIR)/parcial1
	$(GEN) \
		-d $(DEF_DIR)/parcial1.yaml \
		-i $(BANCO_DIR)/unidad1.txt $(BANCO_DIR)/unidad2.txt \
		-n 35 \
		-s $(DATE)01 \
		-o $(OUT_DIR)/parcial1/ \
		-f pdf html \
		> $(LOG_DIR)/parcial1.log 2>&1

# Parcial 2
parcial2:
	@echo "$(CYAN)Generando Parcial 2...$(NC)"
	@mkdir -p $(OUT_DIR)/parcial2
	$(GEN) \
		-d $(DEF_DIR)/parcial2.yaml \
		-i $(BANCO_DIR)/unidad3.txt $(BANCO_DIR)/unidad4.txt \
		-n 35 \
		-s $(DATE)02 \
		-o $(OUT_DIR)/parcial2/ \
		-f pdf html \
		> $(LOG_DIR)/parcial2.log 2>&1

# Final
final:
	@echo "$(CYAN)Generando Final...$(NC)"
	@mkdir -p $(OUT_DIR)/final
	$(GEN) \
		-d $(DEF_DIR)/final.yaml \
		-i $(BANCO_DIR)/*.txt \
		-n 50 \
		-s $(DATE)99 \
		-o $(OUT_DIR)/final/ \
		-f pdf html \
		> $(LOG_DIR)/final.log 2>&1

# Recuperatorio
recuperatorio:
	@echo "$(CYAN)Generando Recuperatorio...$(NC)"
	@mkdir -p $(OUT_DIR)/recuperatorio
	$(GEN) \
		-d $(DEF_DIR)/recuperatorio.yaml \
		-i $(BANCO_DIR)/*.txt \
		-n 30 \
		-s $(DATE)88 \
		-o $(OUT_DIR)/recuperatorio/ \
		-f pdf html \
		> $(LOG_DIR)/recuperatorio.log 2>&1

# Distribuir a carpetas por estudiante
distribute: generate
	@echo "$(CYAN)Organizando exámenes por estudiante...$(NC)"
	$(PYTHON) scripts/distribuir_examenes.py $(OUT_DIR)

# Generar reporte
report:
	@echo "$(CYAN)Generando reporte...$(NC)"
	@echo "================================" > $(LOG_DIR)/reporte.txt
	@echo "REPORTE DE GENERACIÓN" >> $(LOG_DIR)/reporte.txt
	@echo "Fecha: $(DATE)" >> $(LOG_DIR)/reporte.txt
	@echo "Semestre: $(SEMESTER)" >> $(LOG_DIR)/reporte.txt
	@echo "================================" >> $(LOG_DIR)/reporte.txt
	@echo "" >> $(LOG_DIR)/reporte.txt
	@echo "Parcial 1:" >> $(LOG_DIR)/reporte.txt
	@find $(OUT_DIR)/parcial1 -name "*.pdf" | wc -l | \
		xargs -I {} echo "  PDFs generados: {}" >> $(LOG_DIR)/reporte.txt
	@echo "Parcial 2:" >> $(LOG_DIR)/reporte.txt
	@find $(OUT_DIR)/parcial2 -name "*.pdf" | wc -l | \
		xargs -I {} echo "  PDFs generados: {}" >> $(LOG_DIR)/reporte.txt
	@echo "Final:" >> $(LOG_DIR)/reporte.txt
	@find $(OUT_DIR)/final -name "*.pdf" | wc -l | \
		xargs -I {} echo "  PDFs generados: {}" >> $(LOG_DIR)/reporte.txt
	@echo "Recuperatorio:" >> $(LOG_DIR)/reporte.txt
	@find $(OUT_DIR)/recuperatorio -name "*.pdf" | wc -l | \
		xargs -I {} echo "  PDFs generados: {}" >> $(LOG_DIR)/reporte.txt
	@cat $(LOG_DIR)/reporte.txt
	@echo "$(GREEN)✓ Reporte generado en $(LOG_DIR)/reporte.txt$(NC)"

# Test rápido (solo 2 versiones)
test:
	@echo "$(CYAN)Generación de prueba...$(NC)"
	$(GEN) \
		-d $(DEF_DIR)/parcial1.yaml \
		-i $(BANCO_DIR)/*.txt \
		-n 2 \
		-o test_output/ \
		--debug

# Ayuda
help:
	@echo "$(CYAN)Comandos disponibles:$(NC)"
	@echo "  make all          - Proceso completo"
	@echo "  make clean        - Limpiar outputs"
	@echo "  make validate     - Validar definiciones"
	@echo "  make generate     - Generar todos los exámenes"
	@echo "  make parcial1     - Solo parcial 1"
	@echo "  make parcial2     - Solo parcial 2"
	@echo "  make final        - Solo final"
	@echo "  make distribute   - Organizar por estudiante"
	@echo "  make report       - Generar reporte"
	@echo "  make test         - Generación de prueba"
```

### Script de distribución (scripts/distribuir_examenes.py)

```python
#!/usr/bin/env python3
"""
Script para distribuir exámenes generados en carpetas por estudiante
"""
import sys
import shutil
from pathlib import Path
import re

def extraer_tema(filename):
    """Extrae número de tema del nombre de archivo"""
    match = re.search(r'tema_(\d+)', filename)
    return match.group(1) if match else None

def distribuir_examenes(output_dir):
    """Organiza exámenes en carpetas por estudiante"""
    output_path = Path(output_dir)
    
    # Crear carpeta de distribución
    dist_dir = output_path / "distribuidos"
    dist_dir.mkdir(exist_ok=True)
    
    # Procesar cada tipo de examen
    for examen_tipo in ['parcial1', 'parcial2', 'final', 'recuperatorio']:
        examen_dir = output_path / examen_tipo
        
        if not examen_dir.exists():
            continue
        
        print(f"Procesando {examen_tipo}...")
        
        # Agrupar por tema
        for pdf in examen_dir.glob("*.pdf"):
            tema = extraer_tema(pdf.name)
            
            if tema:
                # Crear carpeta para el tema
                tema_dir = dist_dir / examen_tipo / f"tema_{tema}"
                tema_dir.mkdir(parents=True, exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(pdf, tema_dir / pdf.name)
                
                # Copiar HTML también si existe
                html = pdf.with_suffix('.html')
                if html.exists():
                    shutil.copy2(html, tema_dir / html.name)
        
        print(f"✓ {examen_tipo} distribuido")
    
    print(f"\n✓ Exámenes distribuidos en: {dist_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python distribuir_examenes.py <output_dir>")
        sys.exit(1)
    
    distribuir_examenes(sys.argv[1])
```

### Uso del pipeline:

```bash
# Ejecutar pipeline completo
make all

# Solo validar
make validate

# Solo generar parcial 1
make parcial1

# Generar y distribuir
make generate distribute

# Test rápido
make test

# Ver ayuda
make help
```

---

## Mejores Prácticas

### 1. Organización de Bancos

```
bancos/
├── por_materia/
│   ├── matematicas.txt
│   ├── fisica.txt
│   └── quimica.txt
├── por_nivel/
│   ├── basico.txt
│   ├── intermedio.txt
│   └── avanzado.txt
└── especiales/
    ├── olimpiadas.txt
    └── recuperatorios.txt
```

### 2. Versionado de Definiciones

```yaml
# Incluir metadata en definiciones
metadata:
  version: "1.2.0"
  autor: "Prof. García"
  fecha_creacion: "2024-01-15"
  ultima_modificacion: "2024-03-20"
  changelog:
    - "v1.2.0: Agregada sección de casos prácticos"
    - "v1.1.0: Ajustados puntajes de sección 3"
    - "v1.0.0: Versión inicial"
```

### 3. Scripts de Backup

```bash
#!/bin/bash
# backup_examenes.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_$DATE"

mkdir -p "$BACKUP_DIR"

# Copiar bancos, definiciones y exámenes generados
cp -r bancos/ "$BACKUP_DIR/"
cp -r definiciones/ "$BACKUP_DIR/"
cp -r examenes_generados/ "$BACKUP_DIR/"

# Comprimir
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✓ Backup creado: $BACKUP_DIR.tar.gz"
```

### 4. Validación Pre-generación

```bash
#!/bin/bash
# validate_all.sh

echo "Validando todas las definiciones..."

ERRORS=0

for def in definiciones/*.yaml; do
    echo -n "Validando $(basename $def)... "
    
    if generador-examenes -d "$def" -i bancos/*.txt --validate 2>&1 | grep -q "válida"; then
        echo "✓"
    else
        echo "✗ ERROR"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo "✓ Todas las definiciones son válidas"
    exit 0
else
    echo ""
    echo "✗ $ERRORS definiciones con errores"
    exit 1
fi
```

---

## Troubleshooting

### Error: Preguntas insuficientes

```yaml
# Solución 1: Usar accion_si_insuficiente
pools:
  - categoria: "Math/**"
    cantidad: 100
    accion_si_insuficiente: "usar_todas"  # O "advertir"

# Solución 2: Ampliar el filtro
pools:
  - categoria: "Math/**"  # En lugar de "Math/Algebra/Linear"
    cantidad: 50
```

### Error: Categoría no encontrada

```bash
# Verificar categorías disponibles con --debug
generador-examenes -d def.yaml -i banco.txt --debug | grep "categoria"

# Listar todas las categorías del banco
generador-examenes -d def.yaml -i banco.txt --validate --debug 2>&1 | grep "Categoría"
```

### Rendimiento lento

```bash
# Para muchos exámenes, usar semillas consecutivas
for i in {1..100}; do
    generador-examenes -d def.yaml -i banco.txt -n 1 -s $i -o "out/tema_$i/" &
done
wait
```

---

## Recursos Adicionales

- Ver **CATEGORIAS.md** para guía completa de categorías anidadas
- Ver **EJEMPLOS.md** para ejemplos básicos
- Ver **GUIA_UV.md** para configuración del entorno
- Ver **tests/bancos_ejemplo/** para bancos de ejemplo

---

**Fecha:** 2024-12-20  
**Versión:** 5.1.0  
**Autor:** Equipo alucarD
