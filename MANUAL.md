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
- Mantenimiento masivo y reestructuración de árboles de categorías de preguntas (delegado a `voight`).
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
uv tool install "generador-examenes[ecosistema,languagetool] @ git+https://github.com/INGCOM-UNRN/alucarD"
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

### CLI 1: `alucard`

Cada tarea es un comando. Las formas anteriores (`--init`, `--wizard`, `--category-tree`,
`--spellcheck`, `--validate` y generar sin comando) siguen andando, con un aviso.

| Comando | Qué hace |
| :--- | :--- |
| `alucard generar -d YAML` | Genera los temas (HTML y/o PDF), con claves, OMR e imprenta si se piden. |
| `alucard validar -d YAML` | Valida la definición y sus pools sin escribir archivos. |
| `alucard ortografia -d YAML` | Revisa ortografía y gramática con LanguageTool. |
| `alucard categorias BANCO…` | Árbol HTML de categorías de bancos o carpetas de consignas. |
| `alucard asistente YAML` | Asistente interactivo para crear o editar una definición. |
| `alucard iniciar` | Crea un proyecto de ejemplo en la carpeta actual. |
| `alucard build`, `balance-check`, `lint-gift`, `sintetizar`, `diagrama`, `doctor` | Ver sus secciones. |

#### Vista previa de una pregunta: `alucard ver`

Para ver cómo queda una pregunta sin generar el examen entero:

```bash
alucard ver bancos/estructuras.gift -q abb-preorden      # por título (o parte) o id
alucard ver bancos/estructuras.gift -l 40 -f pdf --clave  # la pregunta de esa línea, en PDF y con la clave
alucard ver bancos/estructuras.gift                       # todo el banco
```

Sale en `output/vista_previa/` (`-o` la cambia) con los diagramas e imágenes (`-p`) igual que en el
examen, y se abre con el visor del sistema (`--no-abrir` lo evita; sin entorno gráfico, muestra la
ruta). Si el título no existe, lista los que hay.

#### Informe de la generación (`informe.md`)

Junto a los temas, `alucard generar` deja un `informe.md` con:

- cada pool, cuántas preguntas podía elegir y cuántas eligió;
- las preguntas elegidas, con su sección, tipo, categoría, banco y puntaje;
- el orden de cada tema (los temas comparten preguntas y cambian el orden);
- las consignas prácticas que no podían entrar, con el filtro que las dejó afuera (categoría, tipo,
  etiquetas, minutos) o `publicar: false`.

#### Mientras se escribe: `--watch`

`alucard generar -d parcial.yaml --watch` (o `-w`) genera y vuelve a generar cada vez que se guarda
la definición, el `alucard.toml`, un banco, una consigna, una imagen o la plantilla. La carpeta de
salida no se mira, así lo generado no dispara otra vuelta. `alucard ver BANCO -q titulo -w` hace lo
mismo con la vista previa: la abre la primera vez y después la regenera (el visor la recarga).
Ctrl+C termina.

#### Configuración del curso: `alucard.toml`

Lo que se repite en cada corrida va en un `alucard.toml` (lo crea `alucard iniciar`). alucard lo
busca desde la carpeta de la definición hacia arriba, sin salir del repositorio git; las rutas son
relativas al archivo. La línea de comandos manda sobre la definición YAML, y la definición sobre
`alucard.toml`.

```toml
input_banco = ["bancos/teoria.gift", "bancos/sintetizados"]
output_dir = "output"
path_images = "imagenes"
numero_temas = 2
semilla = 2026
formato = ["pdf"]

[ortografia]
servidor = "http://localhost:8081"
idioma = "es-AR"
ignorar_reglas = ["WHITESPACE_RULE"]
palabras = ["malloc", "struct", "GIFT"]
```

Con eso, `alucard generar -d parcial.yaml` alcanza.

#### Opciones de `alucard generar`

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
| `--json` | `flag` | `False` | Emite el resultado y metadata de los exámenes en formato JSON. |
| `--md`, `--output-md` | `<path>` | `None` | Genera un reporte detallado en Markdown. |

#### Opciones de `alucard ortografia` (y de calidad)

| Opción | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--lt-server` | `<str>` | `http://localhost:8081` | URL del servidor LanguageTool. |
| `--lt-lang` | `<str>` | `es-AR` | Código de idioma para LanguageTool. |
| `--lt-fix` | `flag` | `False` | Aplica correcciones ortográficas automáticas in-place. |
| `--audit-typography` | `flag` | `False` | Audita líneas huérfanas y legibilidad tipográfica en bloques de código. |

#### Ejemplos de Invocación

1. **Generar 3 temas de examen en PDF con hoja de respuestas OMR:**
   ```bash
   alucard generar -d examen_parcial.yaml -f pdf -n 3 --omr -o ./dist
   ```

2. **Validar definición YAML sin generar archivos:**
   ```bash
   alucard validar -d examen_parcial.yaml
   ```

3. **Generar versión accesible con letra grande y paquete único para imprenta:**
   ```bash
   alucard generar -d examen_parcial.yaml -f pdf -n 4 --accessible --bundle-print
   ```

4. **Auditar ortografía en español rioplatense:**
   ```bash
   alucard ortografia -d examen_parcial.yaml --lt-lang es-AR
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

### Subcomando: `alucard sintetizar`

Genera un banco GIFT (o Moodle XML) de preguntas de opción múltiple sobre código C. gcc verifica
cada respuesta: no se calcula a mano. Las plantillas están en
`generador_examenes/synthesizer/plantillas.py`, una función por plantilla registrada en `PLANTILLAS`.

| Plantilla | Pregunta | Cómo se verifica la respuesta |
| :--- | :--- | :--- |
| `precedencia` | ¿Qué imprime una expresión aritmética? | Se ejecuta. |
| `traza-punteros` | ¿Qué imprime `*p` después de `p += k`? | Se ejecuta. |
| `recursion` | ¿Qué devuelve una suma recursiva? | Se ejecuta. |
| `incrementos` | `i++` frente a `++i`. | Se ejecuta. |
| `array-decay` | `sizeof` de un arreglo en `main`, en un parámetro y en una expresión. | Se ejecuta (el enunciado dice el tamaño de `int` y de los punteros de la plataforma). |
| `punteros-salvajes` | ¿Qué ocurre? Puntero sin inicializar, o la variante correcta. | `gcc -fanalyzer` tiene que señalar el defecto; la variante correcta compila sin avisos y se ejecuta. |
| `punteros-colgantes` | ¿Qué ocurre? Uso tras `free`, dirección de una local, doble `free`, o la variante correcta. | Ídem. |
| `fugas-malloc` | ¿Cuántos bytes quedan sin liberar? | Se ejecuta con `malloc`/`calloc`/`realloc`/`free` envueltos que cuentan la memoria. |

```bash
alucard sintetizar                                   # lista las plantillas
alucard sintetizar fugas-malloc -c 6 --opciones 5    # output/sintetizados_fugas-malloc.gift
alucard sintetizar array-decay -f xml -s 7 -o bancos/
```

| Opción | Por omisión | Qué hace |
| :--- | :--- | :--- |
| `-c`, `--cantidad` | `5` | Preguntas a generar (variantes distintas). |
| `--opciones` | `4` | Opciones por pregunta, la correcta incluida (2 a 8). Se usan los distractores más verosímiles de la plantilla; en las respuestas numéricas se completan con valores cercanos. |
| `-f`, `--formato` | `gift` | `gift` o `xml`. |
| `-o`, `--output-dir` | `output` | Carpeta del banco. |
| `-s`, `--semilla` | `42` | La misma semilla genera el mismo banco. |
| `--json` | | El resultado, con cada pregunta, como JSON. |

El GIFT declara `[markdown]` en cada pregunta, así que el código en línea de enunciados y opciones
se ve como código, y pone cada plantilla en la categoría `sintetizados/<plantilla>` (un pool la elige
con `categoria: "sintetizados/fugas-malloc"`). Las plantillas de comportamiento indefinido necesitan gcc 10 o posterior.

### Diagramas de estructuras de datos (statics)

Las preguntas (GIFT `[markdown]`, Markdown) y los enunciados de las consignas de deckard pueden
incluir diagramas de arreglos, listas enlazadas, pilas, colas y árboles. Se escriben en un bloque de
código `estructura`, en YAML o JSON, con el formato de bloques de
statics (`estructuras.html`): un bloque exportado de statics se pega tal cual. alucarD lo
dibuja como SVG, en línea en el HTML y como imagen en el PDF de Typst, sin navegador ni dependencias
nuevas.

````text
::lista-01:: [markdown]¿Qué valor se obtiene con `cabeza->sig->sig->dato`?
```estructura
type: linked_list
variant: singly
values: [10, 20, 30, 40]
addresses: [0x3B20, 0x7E10, 0x2140, 0x9A80]
```
{
=`30`
~`20`
~`40`
}
````

| `type` | Variantes (`variant`) | Claves principales |
| :--- | :--- | :--- |
| `array` | | `values`, `capacity`, `pointers` (`"p:0, q:3"`), `showIndices`, `showAddresses`, `showOffsets`, `baseAddr`, `typeSize`, `blankValues`, `blankAddrs` |
| `linked_list` | `singly`, `doubly`, `circular`, `circular_doubly` | `values` (hasta 7), `addresses`, `headLabel`, `drawArrows`, `blankValues`, `blankNextAddrs` |
| `stack` | `layout: vertical_multi` para varios pasos | `values` (desde la base), `capacity`, `topIndex`, `topLabel`, `traceLabels`, `showAddresses`, `blankValues`, `blankPointers` |
| `queue` | `linear`, `circular` | `values`, `capacity`, `frontIndex`, `rearIndex`, `showPanel` (circular), `blankValues`, `blankPointers` |
| `tree` | `binary`, `bst`, `avl`, `heap` | Nodos con `values` (por niveles, `""` = sin nodo), `insert` (inserciones de ABB; con `avl`, rebalancea) o `root` (anidado: `value`, `left`, `right`). Además `nodeStyle: struct` (nodos con `*izq`/`*der`), `nullLeaves`, `highlight`, `blankValues`, `showBalance`/`blankBalance` (AVL), `showArray` (montículo) |

Los árboles son de alucarD, porque statics no los tiene. El AVL muestra el factor de balance de cada
nodo, calculado sobre el árbol que resulta de las inserciones. El montículo muestra el índice de cada
nodo y el arreglo debajo. Con `blank*`, el diagrama sale con los casilleros vacíos para que el alumno
los complete.

Cuidados:

- En GIFT, el bloque no puede tener renglones en blanco (separan preguntas). Conviene usar YAML en
  bloque y no `{...}`, para no confundir las llaves con las de las respuestas.
- Por omisión, los diagramas usan la paleta de ahorro de tinta de statics (negro); `inkSaver: false`
  en el bloque usa la de color.
- Un bloque inválido no corta la generación: el examen muestra «Diagrama inválido» con el motivo.

`alucard diagrama` dibuja un archivo suelto: un bloque, una lista de bloques o un documento de
statics. Escribe un SVG por bloque y saltea los que no son estructuras (texto, tablas de traza):

```bash
alucard diagrama ~/dev/tools/statics/ejercicio_pila.json -o diagramas/
alucard diagrama arbol.yaml --color
```

### `alucard lint-gift` (antes `gift-linter`)

Valida bancos GIFT: el formato de cada pregunta, los bloques ```` ```estructura ```` y, con
`--compilar`, el código C. Cada problema lleva su línea y el título de su pregunta.

- **Diagramas:** un bloque que no se puede dibujar (tipo desconocido, datos inválidos), uno con un
  renglón en blanco (GIFT corta la pregunta ahí) o con llaves (abren las respuestas).
- **Código (`--compilar`):** los bloques ```` ```c ```` que son programas completos (tienen `main`)
  pasan por `gcc -fsyntax-only -std=c11`, ya decodificados (el código de un GIFT viene escapado o en
  caracteres de ancho completo, como el de los sintetizados). Los fragmentos se saltean.

| Opción | Descripción |
| :--- | :--- |
| `ARCHIVOS...` | Uno o más bancos `.gift`. |
| `--fix` | Corrige problemas comunes de sintaxis y espaciado en el lugar. |
| `--compilar` | Compila el código C de las preguntas. |

```bash
alucard lint-gift bancos/*.gift                       # formato y diagramas
alucard lint-gift sintetizados/*.gift --compilar      # además, que el código compile
alucard lint-gift bancos/*.gift --fix
```

### Consignas prácticas y repositorios externos

Además de los bancos GIFT/XML (`input_banco` / `-i`), la definición puede sumar:

```yaml
# Consignas prácticas de deckard del proyecto (las crea alucard iniciar en consignas/)
input_consignas: ["consignas"]

# Repositorios de la misma computadora que complementan el banco del proyecto
repositorios_externos:
  - ruta: "~/dev/tools/enunciados"   # repositorio de enunciados: usa su banco/
    tipo: deckard                    # auto (por omisión) | preguntas | deckard
    nombre: enunciados               # etiqueta repo:enunciados
    incluir_no_publicados: false     # consignas con publicar: false
  - ruta: "~/catedra/preguntas"      # todos los .gift/.txt/.xml de la carpeta
    tipo: preguntas
```

Cada consigna es una pregunta `consigna_practica` con id `deckard:<id>`, categoría
`consignas/<tema>` y etiquetas `<tags del ejercicio>`, `<tema>`, `bloom:<n>` y `repo:<nombre>`:
los pools la eligen con los filtros de siempre (`tipos`, `categoria`, `etiquetas`,
`preguntas_fijadas`) y con los de tiempo requerido:

```yaml
pools:
  - tipos: ["consigna_practica"]
    categoria: "consignas/punteros"
    minutos_min: 15              # minutos estimados del ejercicio
    minutos_max: 40
    presupuesto_minutos: 60      # suma máxima de las consignas elegidas
    cantidad: 2
```

Con un filtro de tiempo, las preguntas sin tiempo estimado (las de GIFT/XML) quedan afuera del pool.

**Sorteo.** Cada pool sortea qué preguntas entran (por `cantidad` o por `presupuesto_minutos`) con
la semilla del examen (`semilla` / `-s`): la misma semilla da el mismo examen, y cambiarla cambia
las consignas elegidas. `configuracion_examen.sortear_preguntas: false` toma las primeras que pasan
los filtros. Los temas (`-n`) comparten las preguntas y cambian su orden y el de las opciones.

**Comandos.** Todos usan las fuentes de la definición:

```bash
alucard build -d parcial.yaml                         # sin -i: input_banco + consignas + repositorios
alucard build --consignas consignas --repositorio ~/dev/tools/enunciados   # sin YAML
alucard balance-check -d parcial.yaml --repositorio ~/catedra/preguntas
alucard categorias ~/dev/tools/enunciados        # una carpeta: repositorio de preguntas o de consignas
alucard categorias bancos/teoria.gift -d parcial.yaml   # suma las fuentes de la definición
alucard ortografia -d parcial.yaml                  # también las consignas que los pools pueden elegir
```

`-i` reemplaza al `input_banco` de la definición; `--consignas` y `--repositorio` (repetibles) se
suman a `input_consignas` y `repositorios_externos`. El asistente (`alucard asistente`) pregunta por las
fuentes y ofrece pools de consignas con tema, filtros de tiempo y renglones para resolver.

**Presentación.** `configuracion_examen.presentacion_consignas` fija qué muestra el examen de
cada consigna; cada pool puede cambiar sólo algunas claves en `presentacion`:

| Clave | Por omisión | Qué hace |
| :--- | :--- | :--- |
| `titulo` | `true` | El título del ejercicio. |
| `metadatos` | `false` | Tema, nivel de Bloom y minutos estimados. |
| `enunciado` | `true` | El enunciado (el MyST de deckard se pasa a Markdown común). |
| `secciones_excluidas` | `[]` | Secciones del enunciado a omitir, por su título o parte de él (`"Contrato"`, `"Criterios"`). |
| `funciones` | `false` | Tabla con las firmas de las funciones. |
| `cabecera` | `false` | El archivo `.h` del ejercicio. |
| `pistas` | `0` | Cuántas pistas mostrar. |
| `espacio_respuesta` | `true` | Renglones para resolver debajo de la consigna. |
| `lineas` | `20` | Cuántos renglones. |
| `solucion_en_clave` | `true` | La solución de la cátedra en la clave del profesor. |

### Ejemplo completo: parcial práctico

Un segundo parcial de 120 minutos y 10 puntos que combina las tres fuentes: preguntas
GIFT del proyecto, una consigna local fija y consignas sorteadas del repositorio de
enunciados. Se arma sobre un proyecto creado con `alucard iniciar`:

```text
parcial2/
├── bancos/punteros.gift          # preguntas de opción múltiple y V/F
├── consignas/sumar-pares/        # la crea alucard iniciar: ejercicio.yaml, enunciado.md, solucion.c
└── parcial_practico.yaml
```

Las preguntas del banco usan `[markdown]` para que el código en línea salga como código en el papel:

```text
$CATEGORY: teoria/punteros

::p-01:: [markdown]Si `int x = 5; int *p = &x;`, ¿qué vale `*p`? {
=5
~La dirección de `x`
~La dirección de `p`
~No está definido
}

::p-03:: [markdown]Desreferenciar un puntero `NULL` es comportamiento indefinido. {T}

::p-06:: [markdown]Después de `free(p)`, `p` vale `NULL` automáticamente. {F}
```

`parcial_practico.yaml`:

```yaml
nombre_examen: "Segundo parcial — práctico"
institucion: "UNRN Andina"
materia: "Programación 1"
fecha: "2026-11-12"
duracion_minutos: 120
instrucciones_generales: |
  Resolvé en C11. Cada función debe respetar la firma indicada.
  No se permite usar bibliotecas fuera de la estándar.
idioma: "es"
numero_temas: 3                  # los temas comparten consignas; cambia el orden
semilla: 20261112                # fija qué consignas salen sorteadas
formato: ["pdf"]

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  sortear_preguntas: true
  # Lo que se imprime de cada consigna, salvo que el pool diga otra cosa.
  presentacion_consignas:
    titulo: true
    metadatos: false
    enunciado: true
    # Fuera del papel: la autoevaluación, el contrato (ya está la tabla de
    # funciones) y las ayudas con pseudocódigo (:::{tip} Ayuda …).
    secciones_excluidas: ["Criterios de Aceptación", "Contrato", "Ayuda"]
    funciones: true
    cabecera: false
    pistas: 0
    espacio_respuesta: true
    lineas: 25
    solucion_en_clave: true

input_banco: ["bancos/punteros.gift"]
input_consignas: ["consignas"]
repositorios_externos:
  - ruta: "~/dev/tools/enunciados"
    tipo: deckard
    nombre: enunciados

secciones_examen:
  # 4 × 0.5 = 2 puntos, ~10 minutos
  - nombre: "Parte 1 — Conceptos"
    instrucciones: "Marcá la respuesta correcta."
    layout: compact-2col
    pools:
      - categoria: "teoria/punteros"
        cantidad: 4
        puntaje_fijo_por_pregunta: 0.5

  # La misma consigna en todos los temas, con una pista y poco espacio; 1 punto, 20 minutos
  - nombre: "Parte 2 — Calentamiento"
    instrucciones: "Resolvé la función en el espacio indicado."
    pools:
      - preguntas_fijadas: ["deckard:sumar-pares"]
        puntaje_fijo_por_pregunta: 1
        presentacion:
          pistas: 1
          lineas: 12

  # Dos consignas sorteadas de 20 a 35 minutos, que entre las dos no pasen de 60; 2 × 2.5 = 5 puntos
  - nombre: "Parte 3 — Punteros y cadenas"
    instrucciones: "Resolvé las funciones pedidas; podés usar funciones auxiliares."
    pools:
      - tipos: ["consigna_practica"]
        categorias: ["consignas/punteros", "consignas/cadenas"]
        etiquetas: ["repo:enunciados"]
        minutos_min: 20
        minutos_max: 35
        presupuesto_minutos: 60
        cantidad: 2
        puntaje_fijo_por_pregunta: 2.5
        presentacion:
          metadatos: true          # tema, Bloom y tiempo estimado, para que administren el tiempo
          lineas: 30

  # Se resuelve en máquina: enunciado completo con ayudas, la cabecera .h y sin renglones; 2 puntos, ≤ 30 minutos
  - nombre: "Parte 4 — Memoria dinámica (en máquina)"
    instrucciones: "Resolvé en la computadora y entregá el .c por el campus."
    pools:
      - tipos: ["consigna_practica"]
        categoria: "consignas/memoria_dinamica"
        minutos_max: 30
        cantidad: 1
        puntaje_fijo_por_pregunta: 2
        presentacion:
          cabecera: true
          secciones_excluidas: []  # reemplaza la lista general: se ve todo el enunciado
          espacio_respuesta: false
```

Qué muestra cada parte:

| Parte | Fuente | Recurso |
| :--- | :--- | :--- |
| 1 | Banco GIFT del proyecto | Pool por `categoria`, en dos columnas. |
| 2 | `consignas/` local | `preguntas_fijadas` con el id `deckard:<id>`; la presentación del pool suma una pista y achica el espacio. |
| 3 | Repositorio de enunciados | Sorteo entre dos temas, filtrado por `repo:enunciados`, con tiempo mínimo, máximo y presupuesto; muestra los metadatos. |
| 4 | Repositorio de enunciados | Consigna para la computadora: con cabecera, sin espacio de respuesta y sin excluir secciones. |

La presentación del pool cambia sólo las claves que declara. Una lista, como
`secciones_excluidas`, reemplaza a la general completa, no se suma a ella.

Flujo de trabajo:

```bash
cd parcial2
alucard categorias ~/dev/tools/enunciados       # output/category_tree.html: temas y consignas disponibles
alucard validar -d parcial_practico.yaml          # puntajes y cantidad de preguntas por parte
alucard ortografia -d parcial_practico.yaml        # ortografía del banco y de las consignas elegibles
alucard balance-check -d parcial_practico.yaml       # reparto de la letra correcta entre temas
alucard -d parcial_practico.yaml                     # output/examen_tema_0{1,2,3}.pdf y clave_tema_0{1,2,3}.pdf
alucard -d parcial_practico.yaml -s 7 -o recuperatorio   # mismo esquema, otras consignas
```

La clave de cada tema trae la respuesta de las preguntas cerradas y la solución de la cátedra
(`solucion.c`) de cada consigna. Con otra semilla (`-s`) las Partes 1, 3 y 4 sortean de nuevo entre
lo que cumple los mismos filtros, y la Parte 2, que es fija, no cambia. Así se arma el recuperatorio
con el mismo esquema.
Antes de imprimir conviene revisar las consignas que salieron. Los filtros garantizan el tema y el
tiempo, pero no la calidad de cada enunciado.

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