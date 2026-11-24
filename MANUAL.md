# Manual de Uso y Referencia Técnica: alucarD

> **ALUCARD** — Sistema profesional de generación y maquetación de exámenes impresos basado en Typst y bancos GIFT/Moodle XML.
> **Versión:** `5.11.0` · **CLI principal:** `alucard` (alias de compatibilidad: `generador-examenes`, `gift-linter`)

---

## 1. Arquitectura y Propósito Pedagógico

`alucarD` es el generador canónico de exámenes y evaluaciones impresas de la cátedra de Programación 1 (UNRN). Integra la compilación de variantes dinámicas en C, la ingesta de bancos de preguntas (GIFT y Moodle XML) y la renderización de alta fidelidad tipográfica mediante Typst.

### Alcance Funcional (Qué cubre)
- Generación automatizada de exámenes y parciales institucionales en formatos Typst, PDF y HTML.
- Síntesis de variantes numéricas y lógicas de enunciados mediante semillas reproducibles (`--semilla`).
- Diseño y renderizado de plantillas de examen con hojas de respuestas y descriptores OMR (Optical Mark Recognition).
- Modos accesibles con letra grande (`--accessible`) y empaquetado para imprenta (`--bundle-print`).
- Linting y formateo in-place de archivos de preguntas en formato GIFT (`alucard lint-gift`).
- Auditoría ortográfica y gramatical vía LanguageTool integrada.
- Diagnóstico del entorno y dependencias del sistema (`alucard doctor`).

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
alucard doctor
```
Diagnostica la presencia y versiones de `gcc`, `typst`, `pypdf` y la conectividad con el servidor LanguageTool. Typst es obligatorio: es el único motor de PDF, y sin él `doctor` sale con 1.

---

## 3. Guía Integral de Comandos (CLI)

`alucarD` expone un único ejecutable principal (`alucard`) que agrupa todos los subcomandos. Los nombres históricos `generador-examenes` y `gift-linter` se mantienen como alias de compatibilidad (`gift-linter` equivale a `alucard lint-gift`).

---

### CLI: `alucard`

Cada tarea es un comando. Las formas anteriores (`--init`, `--wizard`, `--category-tree`,
`--spellcheck`, `--validate` y generar sin comando) siguen andando, con un aviso.

| Comando | Qué hace |
| :--- | :--- |
| `alucard generar [-d YAML…]` | Genera los temas (HTML y/o PDF), con claves, OMR e imprenta si se piden. Sin `-d`, los exámenes de `alucard.toml`. |
| `alucard validar -d YAML` | Valida la definición y sus pools sin escribir archivos. |
| `alucard ortografia -d YAML` | Revisa ortografía y gramática con LanguageTool. |
| `alucard categorias BANCO…` | Árbol HTML de categorías de bancos o carpetas de consignas. |
| `alucard asistente YAML` | Asistente interactivo para crear o editar una definición. |
| `alucard iniciar` | Crea un proyecto de ejemplo en la carpeta actual. |
| `alucard ver` | Vista previa de una pregunta (o de un banco) como sale en el examen, con sus diagramas. |
| `alucard registro guardar\|listar\|usadas\|resultados\|analizar` | Registro de exámenes tomados: no repetir preguntas en el cuatrimestre y analizar la calidad de cada una. Ver [Registro de exámenes tomados](#registro-de-exámenes-tomados-alucard-registro). |
| `alucard omr build\|validate\|preview-curve\|calibration-sheet\|verify-geometry` | Exámenes con carátula OMR para la app Escáner OMR. Ver [Exámenes con carátula OMR](#exámenes-con-carátula-omr-alucard-omr). |
| `alucard build`, `balance-check`, `lint-gift`, `sintetizar`, `repartir`, `diagramas-md`, `diagrama`, `doctor` | Ver sus secciones. |

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

#### Inventario del banco: `alucard categorias --resumen`

```bash
alucard categorias --resumen bancos/*.gift          # preguntas por categoría y tipo
alucard categorias --resumen -d parcial.yaml        # con los bancos de la definición y sus pools
```

Muestra en la terminal cuántas preguntas hay en cada categoría, por tipo, y con `-d` si cada pool
tiene las que pide (✓ alcanza, ! no alcanza pero el pool usa todas o advierte, ✗ no alcanza: el
examen no se puede generar). Sale con 1 si algún pool no alcanza, así sirve en un script o en CI.
Si hay [ids repetidos](#ids-repetidos), los lista al final.
Sin bancos toma los de la definición (o los del `alucard.toml`). Sin `--resumen`, `categorias`
arma el árbol HTML.

#### Informe de la generación (`informe.md`)

Junto a los temas, `alucard generar` deja un `informe.md` con:

- cada pool, cuántas preguntas podía elegir y cuántas eligió;
- las preguntas elegidas, con su sección, tipo, categoría, banco y puntaje;
- el orden de cada tema (los temas comparten preguntas y cambian el orden);
- las consignas prácticas que no podían entrar, con el filtro que las dejó afuera (categoría, tipo,
  etiquetas, minutos) o `publicar: false`;
- las categorías del banco, con cuántas preguntas tiene cada una, y sus etiquetas;
- los [ids repetidos](#ids-repetidos), si hay: qué pregunta quedó y cuál se descartó, con sus archivos.

**Si la generación falla** después de leer los bancos (un pool sin preguntas suficientes, un banco
vacío, un `banco.toml` mal escrito, una clave incompleta), el `informe.md` se escribe igual, con
«(falló)» en el título, para ver qué se cargó en lugar de adivinarlo. Trae:

- el error;
- cada pool con cuántas preguntas podía elegir y cuántas pide (✓ alcanza, ✗ no alcanza);
- por qué no alcanzan: el filtro que dejó menos preguntas de las que se piden y qué hay parecido en
  el banco (`¿Quisiste decir «punteros»?`, las categorías, etiquetas o tipos que sí hay o, si ninguna
  pregunta tiene categoría, cómo ponérsela con `$CATEGORY:` o un `banco.toml`);
- cada ruta de `input_banco` (si no existe, o cuántos bancos tiene la carpeta) y cuántas preguntas
  salieron de cada banco;
- las categorías del banco y los ids repetidos.

Los temas que haya en la carpeta siguen siendo los de la corrida anterior. El resumen del final
indica dónde quedó el diagnóstico:

```text
Error: el examen falló: su carpeta sigue con lo de la corrida anterior.
  ✗ parcial.yaml: Preguntas insuficientes en la sección «A», pool 1: se solicitaron 1, pero solo hay 0
    disponibles con Pool(cat:Punteros/listas, cant:1). El filtro categoría «Punteros/listas» deja 0 de 2.
    ¿Quisiste decir «punteros»? …
    diagnóstico: output/informe.md
```

Con `--json` y varias definiciones, la ruta va en `informe` del resultado de cada examen. `alucard validar` no escribe
archivos: da el mismo mensaje de error, pero sin el informe.

Con [`debug_candidatas`](#debug_candidatas) también deja `candidatas.txt`, con todas las preguntas que
cada pool podía elegir.

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
definicion = ["parcial1.yaml", "recuperatorio.yaml"]   # o una sola: definicion = "parcial.yaml"
input_banco = ["bancos/teoria.gift", "bancos/sintetizados"]   # archivos o carpetas (.gift y .xml, con sus subcarpetas)
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
diccionario = "diccionario.txt"   # más palabras, una por renglón (# comenta)
```

Con eso, `alucard generar` alcanza, y `alucard validar` revisa las mismas definiciones. Sin `-d`,
el `alucard.toml` se busca desde la carpeta actual; con `-d`, sólo se generan las que se nombran
(`-d` se repite: `alucard generar -d parcial1.yaml -d parcial2.yaml`).

Con más de una definición, cada examen sale en una subcarpeta de la salida con el nombre de su YAML
(`output/parcial1/`, `output/recuperatorio/`), porque los archivos se llaman igual en todos. Una
definición elige otra carpeta con `subdirectorio`, relativa a la salida, que sirve para agrupar las
partes de un examen compuesto y vale también cuando se genera sola:

```yaml
# teoria.yaml: sale en output/parcial1/teoria/
subdirectorio: "parcial1/teoria"
```

Dos definiciones que caen en la misma carpeta son un error, y `subdirectorio` no puede ser absoluto
ni salir de la salida con `..`. Si una falla, las demás se generan igual y el comando
sale con 1; con `--json`, el resultado de cada una va en `examenes`, con su `motivo` y sus `avisos`.

Lo último que muestra `generar` es un resumen de lo que no salió bien, para que no se pierda entre los
renglones del log. Un examen que falló deja en su carpeta lo de la corrida anterior:

```text
======================================================================
Error: fallaron 1 de 10: su carpeta sigue con lo de la corrida anterior.
  ✗ parcial_3.yaml: configuracion_examen.espacio_desarrollo: Input should be 'cero', 'chico', ...
Revisá antes de imprimir (1):
  ! parcial_1.yaml: debug_consignas está activo: el examen muestra de qué pregunta salió cada una; ...
======================================================================
```

Los avisos no cambian el código de salida. Son un diagrama o una fórmula inválidos, `debug_consignas` activo
y, en el PDF, lo que el armado no pudo acomodar: un renglón de código que no entra en el ancho y se parte,
una fórmula o una tabla que se salen, o una parte de una pregunta más alta que una página. Cada uno
dice en qué pregunta y en qué temas. Los mide Typst con la plantilla de alucard; una plantilla propia (`-t`) no
los informa, y tampoco el binario `typst` sin la librería de Python.
Sin nada que informar, con varios exámenes dice `✓ 10 de 10 exámenes generados.`

Las `palabras` y las del `diccionario` son el
diccionario de la cátedra: `alucard ortografia` no las marca, y se suman a las de
`--lt-ignore-words`.

#### Estilo del examen: `[estilo]`

La tipografía, el encabezado y el pie de página, el logotipo y el contraste del examen y de la clave,
en HTML y en PDF. Van en `[estilo]` de `alucard.toml` y, para un examen en particular, en `estilo`
de la definición YAML, que manda clave por clave. Sin nada, el examen sale como siempre.

```toml
[estilo]
fuente = ["Liberation Serif", "DejaVu Serif"]   # texto, en orden de preferencia (una o varias)
fuente_codigo = "DejaVu Sans Mono"               # bloques y fragmentos de código
tamano = 10.5                                    # puntos (de 7 a 16; 10 por omisión)
encabezado = { izquierda = "{institucion}", derecha = "{materia} | Tema {tema}" }
pie = { izquierda = "{examen} — {fecha}", derecha = "Página {pagina} de {paginas}" }
logo = "logo.png"                                # PNG, JPG, GIF o SVG
logo_posicion = "derecha"                        # "izquierda" (por omisión) o "derecha"
logo_alto_mm = 12                                # de 4 a 30
alto_contraste = true
nombre_en_hojas = true                           # renglón para el nombre en cada hoja
```

| Clave | Por omisión | Qué hace |
| :--- | :--- | :--- |
| `fuente` | Liberation Sans (PDF), Arial (HTML) | Familias del texto; la primera instalada gana. |
| `fuente_codigo` | DejaVu Sans Mono (PDF), Courier New (HTML) | Familias del código. |
| `tamano` | `10` (PDF), el del navegador (HTML) | Tamaño del texto, en puntos. |
| `encabezado`, `pie` | institución, materia y tema arriba; examen y página abajo | Franjas superior e inferior de cada página, con `izquierda`, `centro` y `derecha`. Un texto solo va al centro. |
| `logo` | — | Logotipo en el encabezado. Relativo al archivo que lo nombra (`alucard.toml` o la definición). |
| `logo_posicion`, `logo_alto_mm` | `izquierda`, `12` | Dónde y de qué alto; si es alto, el margen superior crece. |
| `alto_contraste` | `false` | Todo el texto en negro, sin grises (también en los diagramas y en el código, sin resaltado), y bordes negros. |
| `tema_diagramas` | `ink` (o `high-contrast` con `alto_contraste`) | Theme de dibu para los diagramas: `ink`, `color`, `high-contrast`, `dark`, un archivo YAML/JSON (relativo a la definición) o `{extends, colors, typography}`. Ver [Themes de los diagramas](#themes-de-los-diagramas). |
| `nombre_en_hojas` | `true` | En el PDF del examen, un renglón «Apellido y Nombre» debajo del encabezado de cada página impar desde la 3: cada hoja nueva impresa a doble faz. La primera ya tiene el cuadro de datos. Con logotipo, el margen superior crece 7 mm para que entre. No sale en la clave ni en HTML. |

En el encabezado y el pie se puede escribir `{institucion}`, `{materia}`, `{examen}`, `{fecha}`,
`{tema}`, `{pagina}` y `{paginas}`; un marcador desconocido es un error de la definición. En HTML
(que no tiene páginas) las franjas aparecen sólo si se configuraron, y la parte que usa `{pagina}` o
`{paginas}` se omite. Un logotipo que no existe o en otro formato frena la generación antes de
escribir nada. La vista previa (`alucard ver`) usa el estilo del curso.

#### Opciones de `alucard generar`

| Opción / Bandera | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `-d`, `--definicion` | `<path>` | `definicion` del toml | Definición YAML del examen; se repite para generar varios. |
| `-i`, `--input-banco` | `<path>` | `None` | Bancos de preguntas: archivos o carpetas, con sus subcarpetas (ver [Bancos en una carpeta](#bancos-en-una-carpeta)). Se repite; anula lo definido en el YAML. |
| `-o`, `--output-dir` | `<path>` | `output_dir` del YAML o del toml; si no, `./output` | Directorio de salida para los exámenes y soluciones generadas. |
| `-p`, `--path-images` | `<path>` | `None` | Directorio de imágenes referenciadas en las preguntas. |
| `-n`, `--numero-temas` | `<int>` | `1` | Cantidad de temas/variantes independientes a generar. |
| `-s`, `--semilla` | `<int>` | `42` | Semilla pseudo-aleatoria para reproducibilidad matemática. |
| `-f`, `--formato` | `<str>` | `html` | Formato(s) de salida: `pdf`, `html` o ambos (`html,pdf`). |
| `-t`, `--template` | `<path>` | `None` | Ruta a plantilla Typst personalizada (`.typ` o `.typ.j2`). |
| `--registrar` | `flag` | `False` | Anota el examen generado en el registro de exámenes tomados (ver [Registro](#registro-de-exámenes-tomados-alucard-registro)). Con `--cuatrimestre`, `--registro-id` y `--forzar`. |
| `--omr` | `flag` | `False` | Genera hoja de respuestas OMR de lectura óptica y descriptor JSON de corrección. |
| `--accessible` | `flag` | `False` | Edición accesible: letra de 14 puntos (o la del `[estilo]`, si es más grande) y alto contraste, con los títulos y, en el PDF, los diagramas en proporción. |
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

### Subcomando: `alucard doctor`

Verifica la disponibilidad y salud del toolchain de soporte.

```bash
alucard doctor
```

Salida esperada:
- `GCC`: OK (necesario para compilación y trazado de código C).
- `Typst`: OK (el único motor de PDF; si una pregunta no compila, `alucard generar` dice cuál y sale con 1).
- `LanguageTool`: OK (conectividad con servidor local o público).
- `pypdf`: OK (empaquetado de los PDF para imprenta).

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
| `--muestra` | | Muestra una pregunta de ejemplo, con la correcta marcada, sin escribir el banco. |
| `--voight` / `--sin-voight` | `--voight` | Formatea el banco con voight (ver abajo). |

El GIFT declara `[markdown]` en cada pregunta, así que el código en línea de enunciados y opciones
se ve como código, y pone cada plantilla en la categoría `sintetizados/<plantilla>` (un pool la elige
con `categoria: "sintetizados/fugas-malloc"`). Las plantillas de comportamiento indefinido necesitan gcc 10 o posterior.

`alucard sintetizar` sin plantilla lista cada una con qué pregunta y cómo se verifica su respuesta.

En el GIFT, los dos puntos del título, del enunciado y de las opciones van en ancho completo (`：`):
en el título cortarían el `::` que lo delimita, y en el resto GIFT les da significado. Al mostrar la
pregunta, alucard los normaliza y se ven como `:`; `alucard ver -q "Punteros colgantes: free"`
encuentra el título igual. Tampoco se usa `#` en el título (en GIFT abre la retroalimentación): las preguntas con el
mismo título se numeran `n2`, `n3`…, y un `#` delante de un número pasa a `n`.

Después de escribir el banco, alucard le da el formato de voight, en este orden:

```bash
voight fix code-indent banco.gift                   # indentación del código con ·
voight fix code-chars --to-fullwidth banco.gift     # símbolos del código en ancho completo
voight fix format banco.gift                        # formato GIFT/XML de la cátedra
```

Sin voight instalado (`uv tool install git+https://github.com/INGCOM-UNRN/voight`) el banco queda
sin ese formato y se avisa; `--sin-voight` lo saltea.

#### Agregar una plantilla al sintetizador

Las plantillas están en `generador_examenes/synthesizer/plantillas.py`. Una plantilla es una función
`(rng: random.Random) -> SnippetGenerado`:

1. **Armar el programa** con parámetros sacados de `rng` (los valores al azar van en el código, no
   en el enunciado). `_programa(cuerpo, antes, includes)` arma un `main` con sus `#include`.
2. **Verificar la respuesta, nunca calcularla a mano**, con uno de los tres modos:
   - traza: `_ejecutar(codigo)` compila y ejecuta, y su salida es la respuesta;
   - comportamiento indefinido: `_diagnostico(...)` exige que `gcc -fanalyzer` señale el defecto
     (o, en la variante correcta, que no haya avisos y se ejecute);
   - memoria: `memoria_sin_liberar(codigo)` cuenta los bytes que quedan reservados.
3. **Distractores** del más al menos verosímil (errores típicos de los alumnos): el sintetizador
   toma los primeros que necesita según `--opciones`; en respuestas numéricas completa con valores
   cercanos.
4. **Título neutro** con `_huella(codigo)`: no puede adelantar la respuesta.
5. **Registrarla** en `PLANTILLAS` (nombre → descripción y función) y en `VERIFICACION` (cómo se
   verifica), y sumar una prueba en `tests/test_synthesizer.py` que genere varias semillas y revise
   que la correcta sea la que dio gcc.

Probala con `alucard sintetizar <nombre> --muestra` antes de generar el banco.

### Fórmulas matemáticas

Las preguntas (en GIFT, Markdown y Moodle XML) y los enunciados de las consignas admiten fórmulas en
LaTeX: `$O(n \log n)$` o `$ O(n \log n) $` en línea y `$$ ... $$` aparte. En el HTML salen como MathML,
que los navegadores dibujan sin JavaScript ni conexión, con el LaTeX como texto alternativo para los
lectores de pantalla; en el PDF, como matemática de Typst. No hace falta tener LaTeX instalado.

````text
::suma-01:: [markdown]¿Cuánto vale $\sum_{i=1}^{4} i$?
{
=`10`
~$\frac{4}{2}$
}
````

Se entiende lo habitual: `^`, `_`, `\frac`, `\binom`, `\sqrt`, `\sum`, `\prod`, `\int`, `\log` y las
demás funciones, letras griegas, operadores, relaciones, flechas, conjuntos, `\lceil`, `\lfloor`,
`\left…\right`, `\text`, `\mathbf`, `\mathbb`, `\mathcal`, acentos (`\bar`, `\hat`, `\vec`…), espacios y los
entornos `cases`, `aligned`, `array` y las matrices (`matrix`, `pmatrix`, `bmatrix`, `vmatrix`).

Cuidados:

- No son fórmula `$100 y $200`, `$ 5 y $ 6` ni `$(CC) -o $(TARGET)`: los espacios de adentro tienen que
  ser parejos y el `$` que cierra no va seguido de un número. Un signo pesos se escribe `\$`. Lo que está
  entre comillas invertidas o en un bloque de código no se toca.
- En una opción de GIFT, el `=` de una fórmula se escribe `\=`, como en cualquier opción. En el
  enunciado no hace falta. Las llaves de `\frac{a}{b}` van tal cual.
- Un comando que alucard no conoce no corta la generación: la fórmula sale como código, `alucard
  generar` avisa en qué pregunta y `alucard lint-gift` lo marca como error.
- En Moodle XML con formato HTML también valen `\(...\)` y `\[...\]`.

### Diagramas de estructuras de datos y algoritmos (statics)

Las preguntas (GIFT `[markdown]`, Markdown) y los enunciados de las consignas de deckard pueden
incluir diagramas de arreglos, matrices, listas enlazadas, pilas, la pila y el árbol de llamadas,
colas, árboles, structs, TADs, complejidad, flujo, costos y trazas, los de control de procesos
(ver [Control de procesos](#control-de-procesos)), los de química (ver [Química](#química)) y los de
computación, señales, probabilidad y circuitos (ver [Computación, señales, probabilidad y
circuitos](#computación-señales-probabilidad-y-circuitos)). Se escriben en un bloque de
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
| `matrix` | `static` (por omisión), `dynamic`, `jagged`, `flat` | `values` (lista de filas, o plana con `cols`), `rows`, `cols`, `name`, `elementType`, `showIndices`, `showAddresses`, `baseAddr`, `typeSize`, `highlight` (`"1,2; 0,0"` o `[[1, 2]]`), `highlightRows`, `highlightCols`, `blankValues`, `blankAddrs`. Estática: `showLinear` (la matriz en memoria, fila por fila). Dinámica (`int **m`): filas de largo propio y `null` para un puntero a NULL; `rowAddresses`. Dentada (`jagged`): además `showLengths` (por omisión, el arreglo de largos), `lengths`, `lengthsName`, `blankLengths` o `sentinel` (un centinela al final de cada fila). Plana (`flat`, `int *m`): `showCoords`, `showFormula`, `showLogical`; hasta 24 celdas |
| `linked_list` | `singly`, `doubly`, `circular`, `circular_doubly` | `values` (hasta 7; `[]` es la lista vacía), `addresses`, `headLabel`, `pointers` (cursores: `"ant:0, actual:1"`), `drawArrows`, `blankValues`, `blankNextAddrs` |
| `stack` | `layout: vertical_multi` para varios pasos | `values` (desde la base), `capacity`, `topIndex`, `topLabel`, `traceLabels`, `showAddresses`, `blankValues`, `blankPointers` |
| `call_stack` | | `frames` (de `main` hacia el tope; cada uno con `function`, `params`, `vars`, `returnTo`, `returns`, `popped`), `pointers` (`"1.p -> 0.x"`), `steps` (`label` + `frames`, la pila en varios momentos), `showAddresses`, `baseAddr`, `typeSize`, `showTypes`, `blankValues`, `blankAddrs` |
| `call_tree` | | `root` (`call`, `returns`, `children`, `blank`; hasta 40 llamadas), `showOrder`, `highlight`, `levelCosts`, `total`, `blankReturns`, `blankCalls`, `blankLevelCosts`, `blankTotal` |
| `queue` | `linear`, `circular` | `values`, `capacity`, `frontIndex`, `rearIndex`, `showPanel` (circular), `blankValues`, `blankPointers` |
| `tree` | `binary`, `bst`, `avl`, `heap` | Nodos con `values` (por niveles, `""` = sin nodo), `insert` (inserciones de ABB; con `avl`, rebalancea) o `root` (anidado: `value`, `left`, `right`). Además `nodeStyle: struct` (nodos con `*izq`/`*der`), `nullLeaves`, `highlight`, `blankValues`, `showBalance`/`blankBalance` (AVL), `showArray` (montículo) |
| `struct` | `layout` (por omisión), `opaque` | `fields` (`"char nombre[8]"`, `"int edad = 30"` o `{name, type, value, size, align, blank}`; hasta 16), `name`, `typedef`. Disposición: `packed`, `showAddresses`, `baseAddr`, `blankOffsets`, `blankSizes`, `blankPadding`, `blankSizeof`, `blankValues`. Opaco: `operations`, `variable`, `header`, `source`, `client`, `hidden` |
| `adt` | | `name`, `operations` (texto o `{signature, kind, pre, post, blank}`), `invariant`, `representations` (`{name, fields}`), `client`, `blankOperations`, `blankKinds` |
| `complexity` | `growth` (por omisión), `classes` | Curvas: `curves` (`1`, `log n`, `sqrt n`, `n`, `n log n`, `n^2`, `n^3`, `2^n`, `n!`, también como `O(n²)`, o `{label, points}` para mediciones), `maxN`, `maxY`, `xLabel`, `yLabel`, `blankLabels` (rotula A, B, C…). Clases: `classes` (de la más chica a la más grande), `items`, `blankClasses` |
| `flowchart` | | `steps` (texto, `{io}`, `{step}`, `{if, then, else}`, `{while, do}`, `{for, do}`; cada uno con `blank`), `start`, `end` (`false` los quita), `blankValues` |
| `cost_table` | | `lines` (`[código, costo, veces]` o `{code, cost, times}`), `total`, `blankCosts`, `blankTimes`, `blankTotal` |
| `trace_table` | `stack` (sólo cambia los rótulos por omisión) | De statics: `operations`, `capacity`, `pointerHeader`, `pointerLabel`, `showIndexHeader`. De variables: `columns`, `rows` (`null` o una fila corta quedan para completar), `rowCount`, `operations` y `operationHeader` (primera columna), `blankValues` |

Las matrices y los árboles son de alucarD, porque statics no los tiene. La matriz estática muestra
la declaración (`int m[3][4]`) y, con `showAddresses`, la dirección de cada celda en orden de filas;
`showLinear` la dibuja además como está en memoria, una fila detrás de la otra. La dinámica dibuja el
puntero, el arreglo de punteros a filas y cada fila por separado. El máximo es 10 filas por 10
columnas: una matriz más grande, o `rows`/`cols` fuera de 1 a 10, es un error y no se dibuja.

La dentada (`jagged`) es la dinámica con filas de distinto largo y cómo se sabe dónde termina cada
una: por omisión dibuja a la izquierda el arreglo de largos (`size_t largos[n]`, calculado de las
filas o fijado con `lengths`); con `sentinel` agrega al final de cada fila una celda centinela (por
ejemplo `'\0'` en un arreglo de cadenas, o `-1`).

La plana (`flat`) es un solo `malloc` de `F * C` elementos: dibuja el puntero y el bloque contiguo con
su índice `[k]` y, debajo, la celda `(i,j)` que le corresponde; una raya marca dónde empieza cada fila.
Para preguntar la conversión, `showIndices: false` o `showCoords: false` quita uno de los dos, y
`showFormula: false` quita `m[i * C + j]`. `showLogical` agrega la matriz como la piensa el programa.

````text
::plana-01:: [markdown]¿Qué índice de `m` corresponde a la fila 1, columna 2?
```estructura
type: matrix
variant: flat
values: [[1, 2, 3], [4, 5, 6]]
showIndices: false
showFormula: false
highlight: "1,2"
```
{
=`5`
~`4`
~`6`
}
````

#### Stack, heap y estructuras cabecera

Para mostrar dónde vive cada cosa, `linked_list` y `matrix` (`dynamic` y `jagged`) aceptan:

| Clave | En | Qué hace |
| :--- | :--- | :--- |
| `zones` | ambos | Enmarca el stack y el heap. `true` usa esos títulos; con `stack` y `heap` se eligen otros (`stack: "Stack: main"`). |
| `header` | `linked_list` | Una estructura cabecera en lugar de `HEAD`: `name`, `type` y `fields`. |
| `nodeType` | `linked_list` | Rotula cada nodo `@N1 (nodo_t)` en lugar de `Dir: @N1`. |
| `owner` | `matrix` | Una estructura dueña de la matriz, en lugar del puntero: `name`, `type` y `fields`. Los largos pasan al heap. |
| `lengthsType` | `matrix` | Tipo de los largos, por omisión `size_t`. |
| `lengthsAddr` | `matrix` | Dirección de los largos, con `owner`. |

Cada campo de `fields` es un valor (`"cant = 4"`) o un puntero (`"primero -> 0"`), o `{name, value, to}`.
En una lista, un puntero va al nodo de esa posición, desde 0. En una matriz va a `rows` (el arreglo de
punteros a filas) o a `lengths` (los largos).

Las direcciones pueden ser simbólicas: en una lista, cualquier texto en `addresses`; en una matriz,
`baseAddr` y `rowAddresses` que empiecen con `@`. En YAML van entre comillas, porque `@` está reservado.

````text
::cabecera-01:: [markdown]¿Qué imprime `printf("%d", l.ultimo->dato)`?
```estructura
type: linked_list
values: [12, 25, 8]
addresses: ["@N1", "@N2", "@N3"]
nodeType: nodo_t
zones: true
header:
  name: l
  type: lista_t
  fields: ["primero -> 0", "ultimo -> 2", "cant = 3"]
```
{
=`8`
~`12`
~`25`
}
````

Una matriz dentada dentro de una estructura, con los largos y las filas en el heap:

```yaml
type: matrix
variant: jagged
name: filas
values: [[4, 8], [10, 20, 30, 40], [9]]
showAddresses: true
baseAddr: "@F"
rowAddresses: ["@R0", "@R1", "@R2"]
lengthsType: int
lengthsAddr: "@L"
zones: true
owner:
  name: d
  type: dentada_t
  fields: ["cant_filas = 3", "largos -> lengths", "filas -> rows"]
```

#### Structs y tipos opacos

`struct` calcula los offsets, el relleno y el `sizeof` como gcc en 64 bits (`char` 1, `short` 2, `int` y
`float` 4, `long`, `double`, `size_t` y punteros 8, y los `intN_t`). Para otro tipo, como un struct
anidado, se escribe con `size` y `align`. Con `packed`, sin relleno. `blankPadding` saca las filas de
relleno, así el alumno las deduce de los offsets.

````text
```estructura
type: struct
name: struct persona
typedef: persona_t
fields: ["char inicial", "int edad", "char *nombre", "short codigo"]
blankOffsets: true
blankSizeof: true
```
````

`variant: opaque` muestra qué ve cada archivo: el `.h` con el `typedef` y las operaciones, el cliente
con un puntero y el `.c` con los campos. Con `hidden: true` los campos no aparecen (no hace falta
`fields`), que es lo que ve el cliente.

````text
```estructura
type: struct
variant: opaque
name: struct pila
typedef: pila_t
operations: ["pila_t pila_crear(size_t capacidad)", "void pila_destruir(pila_t p)"]
fields: ["int *datos", "size_t tope"]
```
````

`adt` dibuja un TAD: el cliente, la tabla de operaciones con su clase, precondición y poscondición, el
invariante y las representaciones posibles.

````text
```estructura
type: adt
name: Pila
operations:
  - {signature: "pila_t pila_crear(size_t n)", kind: constructor, post: "pila vacía"}
  - {signature: "bool pila_apilar(pila_t p, int x)", kind: modificador, pre: "p != NULL"}
invariant: "0 <= tope <= capacidad"
representations:
  - {name: Arreglo, fields: ["int *datos", "size_t tope"]}
  - {name: Lista enlazada, fields: ["nodo_t *cabeza"]}
```
````

#### Algoritmos y su análisis

`complexity` dibuja curvas de crecimiento. Con `blankLabels` salen rotuladas A, B, C… en el orden de
`curves`, para asociarlas con su clase; una curva con `points` son mediciones, para clasificarlas. Las
que se salen del gráfico se cortan en `maxY`. `variant: classes` dibuja conjuntos anidados: por
omisión los órdenes comunes, y con `classes` cualquier jerarquía, como `[P, NP, EXPTIME]`.

````text
```estructura
type: complexity
curves: [n^2, n, 2^n, log n]
blankLabels: true
```
````

````text
```estructura
type: complexity
variant: classes
items:
  "O(log n)": [búsqueda binaria]
  "O(n)": [búsqueda lineal]
```
````

`flowchart` arma el diagrama de flujo a partir de la estructura del algoritmo; cada paso con
`blank: true` sale vacío para completar.

````text
```estructura
type: flowchart
steps:
  - {io: "leer v, n"}
  - "max = v[0]"
  - i = 1
  - while: i < n
    do:
      - if: "v[i] > max"
        then: ["max = v[i]"]
      - i = i + 1
  - {io: "escribir max"}
```
````

`cost_table` es el análisis línea por línea (la sangría del código se respeta) y `trace_table`, la
prueba de escritorio: las filas que faltan y los `null` quedan para completar. También dibuja las
tablas de traza de statics, con `operations` y `capacity`.

````text
```estructura
type: cost_table
lines:
  - ["for (i = 0; i < n; i++)", c1, n + 1]
  - ["    s += v[i];", c2, n]
total: "(c1 + c2) n + c1"
blankTimes: true
```
````

````text
```estructura
type: trace_table
columns: [i, "v[i]", suma]
rows:
  - [0, 3, 3]
  - [1, 5, null]
rowCount: 4
```
````

`call_tree` dibuja las llamadas de una función recursiva: `showOrder` numera en qué orden se hacen,
`highlight` marca los subproblemas repetidos y `levelCosts` suma el costo de cada nivel, para resolver
una recurrencia con `total`. La pila de esas llamadas en un momento dado es `call_stack`.

````text
```estructura
type: call_tree
showOrder: true
highlight: ["fib(1)"]
root:
  call: fib(3)
  returns: 2
  children:
    - {call: fib(2), returns: 1, children: [{call: fib(1), returns: 1}, {call: fib(0), returns: 0}]}
    - {call: fib(1), returns: 1}
```
````

La pila de llamadas (`call_stack`) dibuja los marcos de activación desde `main` (abajo) hasta el
tope, que se resalta. Las variables van como `{x: 5, p: "&x"}`, como `"x = 5"` o como
`{name, value, type, addr, size, blank}`. Los parámetros se marcan en negrita y figuran en el título
del marco. Con `showAddresses`, la primera variable de `main` está en `baseAddr` (por omisión
`0x7FFC`) y las siguientes bajan: 8 bytes si el tipo es un puntero, `typeSize` (4) si no, o `size`.
`pointers` traza flechas de una variable a otra, citando el marco por su índice desde `main` o por el
nombre de la función (el más alto, si hay recursión). Con `steps`, la pila aparece en varios
momentos, uno al lado del otro y alineados en la base, para seguir cómo cambia; un marco con
`popped: true` y `returns` es el que acaba de retornar y se dibuja punteado. Hasta 10 marcos y 8 pasos.

````text
```estructura
type: call_stack
title: factorial(3)
steps:
  - label: "fact(3) llama a fact(2)"
    frames:
      - {function: main, vars: {r: "?"}}
      - {function: fact, params: {n: 3}}
      - {function: fact, params: {n: 2}}
  - label: "fact(1) devuelve 1"
    frames:
      - {function: main, vars: {r: "?"}}
      - {function: fact, params: {n: 3}}
      - {function: fact, params: {n: 2}}
      - {function: fact, params: {n: 1}, returns: 1, popped: true}
```
````

````text
```estructura
type: call_stack
showAddresses: true
showTypes: true
frames:
  - function: main
    vars: [{name: a, value: 3, type: int}, {name: b, value: 7, type: int}]
  - function: intercambiar
    params: [{name: x, value: "&a", type: int *}, {name: y, value: "&b", type: int *}]
    vars: ["aux = 3"]
pointers: "1.x -> 0.a; 1.y -> 0.b"
```
````

Ejemplos:

````text
::matriz-01:: [markdown]¿Qué dirección tiene `m[1][2]`?
```estructura
type: matrix
values: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
baseAddr: 0x1000
showAddresses: true
blankAddrs: true
highlight: "1,2"
```
{
=`0x1018`
~`0x1024`
~`0x1014`
}
````

````text
```estructura
type: matrix
variant: dynamic
values:
  - [1, 2, 3]
  - [4]
  - null
```
````

````text
```estructura
type: matrix
variant: jagged
elementType: char
name: palabras
values: [[h, o, l, a], [s, i]]
sentinel: "'\\0'"
```
````

Los árboles AVL muestran el factor de balance de cada
nodo, calculado sobre el árbol que resulta de las inserciones. El montículo muestra el índice de cada
nodo y el arreglo debajo. Con `blank*`, el diagrama sale con los casilleros vacíos para que el alumno
los complete.

Cuidados:

- En GIFT, el bloque no puede tener renglones en blanco (separan preguntas). Conviene usar YAML en
  bloque y no `{...}`, para no confundir las llaves con las de las respuestas.
- En YAML, un texto con corchetes, llaves, `:` o `#` va entre comillas: `"max = v[0]"`, `"v[i]"`.
- Por omisión, los diagramas usan la paleta de ahorro de tinta de statics (negro); `inkSaver: false`
  en el bloque usa la de color, y `theme:` en el bloque, cualquier theme (ver
  [Themes de los diagramas](#themes-de-los-diagramas)).
- Un bloque inválido no corta la generación: el examen muestra «Diagrama inválido» con el motivo.

#### Control de procesos

Nueve tipos para evaluar y ejemplificar los temas de una asignatura de control de procesos. Las
cuentas las hace alucarD sin dependencias nuevas: simula la respuesta temporal, evalúa la respuesta
en frecuencia, calcula raíces y márgenes. Así, lo que dice el dibujo coincide con la teoría.

| `type` | Qué dibuja | Claves principales |
| :--- | :--- | :--- |
| `block_diagram` | Diagrama de bloques | `forward` (bloques en serie: texto, o `label`, `out` (la señal de salida), `blank`; o `loop` para un lazo interno, en cascada), `feedback` (bloques de realimentación; `[]` es unitaria; sin la clave, lazo abierto), `sign` (`-` o `+`), `input`, `output`, `error`, `measured`, `disturbance` (`at`: antes de qué bloque entra, `label`, `block`, `sign`), `blankSigns` |
| `time_response` | Respuesta temporal | `system`, `systems` (para comparar, cada uno con `label`) o `closedLoop`; `data` (puntos medidos `[t, y]`); `input` (`step`, `ramp`, `impulse`), `amplitude`, `tEnd`, `disturbance` (`at`, `amplitude`, `where`: `output` o `input`), `annotations` (`final`, `overshoot`, `peak`, `rise`, `settling`, `tau`, `delay`, `tangent`, o `all`), `settlingBand` (0,02 o 0,05), `showInput`, `yMin`, `yMax`, `blankAnnotations` |
| `bode` | Magnitud y fase | `system`, `systems` o `closedLoop` (dibuja el lazo abierto L(s)), `wMin`, `wMax`, `asymptotes`, `margins` (MG, MF, ω180, ωc), `show` (`both`, `magnitude`, `phase`), `blankMargins` |
| `nyquist` | Diagrama de Nyquist | `system`, `systems` o `closedLoop`, `wMin`, `wMax`, `limit` (radio máximo), `unitCircle`, `showNegative` (ω negativas, punteadas) |
| `pole_zero` | Polos y ceros en el plano s | `poles`, `zeros` (o `system`, o `closedLoop`: los del lazo cerrado), `dampingLines` (ζ constantes), `wnCircles` (ωn constantes), `showValues`, `blank` (sólo los ejes, para ubicarlos), `xRange`, `yRange` |
| `root_locus` | Lugar de las raíces | `system` o `closedLoop` (el lazo abierto), `kMax`, `asymptotes`, `showCrossing` (Kcrít y ωcrít), `marks` (ganancias marcadas ■), `dampingLines`, `blankMarks` |
| `instrumentation` | P&ID con símbolos ISA-5.1 | `equipment` (`id`, `kind`: `tank`, `vessel`, `reactor`, `column`, `pump`, `control_valve`, `valve`, `heat_exchanger`; `at: [x, y]` en la grilla, `label`, `size`, `level`, `orientation: v`), `instruments` (`id`, `tag`: `"LIC 101"`, `at`, `location`: `field`, `panel`, `panel_back`, `dcs`, `plc`; `blank`), `lines` (`from`, `to`: un id o `[x, y]`; `kind`: `process`, `electric`, `pneumatic`, `data`, `capillary`; `via`, `route` (`hv` o `vh`), `label`, `arrow`), `grid` (px por unidad), `legend` |
| `ladder` | Diagrama escalera (PLC) | `rungs` (cada uno con `logic` y `comment`). En `logic`: contactos `no` (o `na`), `nc`, `p`, `n`; salidas `coil`, `ncoil`, `set`, `reset`; temporizadores `ton`, `tof`, `tp` y contadores `ctu`, `ctd` con `preset`; `or` (ramas en paralelo, cada una una lista); `label` (descripción) y `blank` en cada uno. El escalón termina en sus salidas |
| `grafcet` | GRAFCET | `steps` en orden: `step` (número, `initial`, `actions`, `blank`), `transition` (la receptividad, `blank`), `or` y `and` (divergencias en O y en Y: listas de secuencias); `loop` (vuelve a la etapa inicial; por omisión, sí) |

**Sistemas.** `system`, cada elemento de `systems` y las partes de `closedLoop` se escriben de
cualquiera de estas formas, todas con `delay` (el tiempo muerto) opcional:

| Forma | Es | Ejemplo |
| :--- | :--- | :--- |
| `num`, `den` | Coeficientes en s, de la mayor potencia a la menor | `num: [1]`, `den: [1, 3, 2]` |
| `gain`, `tau` | Primer orden, K / (τs + 1) | `gain: 2`, `tau: 5`, `delay: 1` |
| `gain`, `zeta`, `wn` | Segundo orden, K ωn² / (s² + 2ζωn s + ωn²) | `zeta: 0.3`, `wn: 2` |
| `k`, `poles`, `zeros` | Ganancia, polos y ceros; `[re, im]` es un par complejo | `k: 10`, `poles: [0, -1, [-2, 3]]` |
| `kp`, `ki`, `kd` | Un controlador PID (sólo como `controller`) | `kp: 1.2`, `ki: 0.25` |

`closedLoop` tiene:

- `plant`, la planta;
- `controller`, que por omisión es 1;
- `feedback`, el sensor, que por omisión es 1;
- `sign`, que por omisión es `-`.

En el tiempo, el lazo se simula con su tiempo muerto, y un PID se simula discreto, con el derivativo
filtrado. En frecuencia, Bode, Nyquist y el lugar de las raíces usan el lazo abierto L(s) = C·G·H.

```estructura
type: time_response
title: Curva de reacción
system:
  gain: 2
  tau: 5
  delay: 1
annotations: [final, tangent]
blankAnnotations: true
```

```estructura
type: block_diagram
input: "R(s)"
output: "Y(s)"
forward:
  - label: "Gc(s)"
    out: "U(s)"
  - "Gp(s)"
disturbance:
  at: 1
  label: "D(s)"
feedback: ["H(s)"]
```

En GIFT, el YAML del bloque se escribe sin llaves, en forma de bloque (como arriba): las llaves son
de las respuestas. En la escalera, YAML lee `no:` como `false`; alucarD lo entiende igual, y `na:`
también vale.

#### Química

Veintiún tipos para evaluar y ejemplificar química general, inorgánica, orgánica, fisicoquímica y
analítica. Las cuentas las hace alucarD (`generador_examenes/quimica.py`, sin dependencias nuevas):

- el pH de cada punto de una titulación, por balance de cargas;
- las configuraciones electrónicas, con las excepciones del Cr y el Cu y los cationes de transición;
- el llenado de los orbitales moleculares, con o sin mezcla s-p;
- la cinética, la pila con Nernst y la densidad de una celda unidad.

Así, el pH de la equivalencia, el orden de enlace o la E de la pila que muestra el dibujo salen de la
teoría.

| `type` | Qué dibuja | Claves principales |
| :--- | :--- | :--- |
| `molecule` | Fórmula de Lewis o esqueletal | `atoms` (`id`, `el`, `at: [x, y]` en largos de enlace, o `from` + `angle` (y `length`, `bond`); `charge`, `lonePairs`, `radical`, `note` (δ+), `show`, `blank`), `rings` (`size`, `center`, `start`, `ids`, `aromatic`, `kekule`; dos anillos que comparten vértices se fusionan), `bonds` (`[a, b, orden]` o `{from, to, order: 1, 2, 3, 1.5, 0.5, stereo: wedge o hash, dashed, blank}`), `arrows` (flechas curvas de mecanismo: `from` y `to`, un átomo o un enlace `[a, b]`; `bend`, `half` para un electrón), `skeletal`, `bondLength`, `caption` |
| `reaction` | Ecuación o mecanismo | `steps`: fórmulas, `"+"`, moléculas (como `molecule`), `{arrow: "->", "<=>", "<->" (resonancia) o "=>" (retrosíntesis), above, below, blank}` y `{blank: true, width}` (un producto para completar); `maxWidth` |
| `vsepr` | Geometría molecular (TRePEV) | `central`, `ligands` y `lonePairs` (la geometría sale de los pares) o `geometry` (`linear`, `trigonal_planar`, `bent_trigonal`, `tetrahedral`, `trigonal_pyramidal`, `bent`, `trigonal_bipyramidal`, `seesaw`, `t_shaped`, `linear_tbp`, `octahedral`, `square_pyramidal`, `square_planar`); `showAngle`, `showHybridization`, `blank` (`true` o una lista de `axe`, `name`, `angle`, `hybridization`) |
| `orbitals` | Casilleros u orbitales moleculares | `kind: atomic` (por omisión): `element`, `charge`, `core` (`[Ar]` y la capa de valencia), `showConfig`, `showUnpaired`, `blank`, `blankConfig`. `kind: molecular`: `atoms` (`[O, O]`, `[C, O]`; de H a Ne), `charge`, `blankElectrons`, `blankBondOrder`, `blankMagnetism`, `blank` |
| `energy_profile` | Perfil de energía | `states` (`label`, `energy`, `ts` para un estado de transición), `catalyzed` (otro camino, punteado), `annotations` (`Ea` de cada etapa y `dH`), `unit`, `showEnergies`, `showRateDetermining`, `blankAnnotations` |
| `titration` | Curva de titulación | `analyte` (`kind`: `strong_acid`, `strong_base`, `weak_acid`, `weak_base`; `conc`, `volume`, `pKa` (uno o una lista) o `pKb`, `charge` de la forma agregada: `-2` para el carbonato), `titrant` (`conc`, `name`), `vMax`, `annotations` (`equivalence`, `half`, `initial`), `indicator` (`name`, `range`), `data` (puntos medidos), `blankAnnotations` |
| `speciation` | Fracciones α en función del pH | `pKa` (lista), `species` (por omisión H₃A, H₂A⁻…), `blankPKa`, `blankSpecies` |
| `kinetics` | Cinética | `order` (0, 1, 2), `k`, `A0`, o `curves` (varias, para comparar); `plot: linear` (la recta de cada orden, con su pendiente) o `arrhenius` (`Ea` en kJ/mol, `A`, `T: [T1, T2]`); `model: consecutive` (`k1`, `k2`: A → B → C, con t máx) o `reversible` (`kf`, `kb`); `annotations: [halfLife]`, `showProduct`, `tEnd`, `blankAnnotations` |
| `phase_diagram` | Diagrama de fases | `substance` (`water`, `co2`) o `triple` y `critical` (`[T en K, P en atm]`), `meltingSlope`, `normalMelting`, `normalBoiling`, `normalSublimation`; `scale` (`schematic`, por omisión, o `log`), `atm` (la recta de 1 atm), `points` (`T`, `P`, `label`), `supercritical`, `blankRegions`, `blankPoints`. `kind: eutectic`: `components`, `meltingA`, `meltingB`, `eutectic: [x %, T]`, `cooling` (una composición) |
| `heating_curve` | Curva de calentamiento | `substance: water` o `cpSolid`, `cpLiquid`, `cpGas` (J/g·K), `melting`, `boiling` (°C), `hFusion`, `hVaporization` (J/g); `mass` (g), `from`, `to`; `showHeat`, `showTotal`, `blankHeat`, `blankPhases` |
| `spectrum` | Espectros | `kind: ir` (`peaks`: `at` en cm⁻¹, `depth`, `width`, `broad`, `label`), `nmr` (`signals`: `shift`, `integration`, `multiplicity` (s, d, t, q…) o `neighbors` (regla n + 1), `J`, `label`; `MHz`, `tms`), `c13` (`signals`: `shift`, `label`), `uv` (`bands`: `at` en nm, `absorbance`, `width`) y `ms` (`peaks`: `mz`, `intensity`, `label`); `blankLabels` |
| `galvanic_cell` | Pila | `halfCells`: dos semiceldas `{couple: "Zn^2+/Zn", E0, n, conc, electrode, solution, reaction}` (el ánodo es la de menor E°, a la izquierda); `saltBridge`, `showIons`, `showNotation`, `showDeltaG`; `blankPolarity`, `blankReactions`, `blankPotential`, `blankFlow`, `blankNotation` |
| `unit_cell` | Celda unidad | `lattice` (`sc`, `bcc`, `fcc`, `nacl`, `cscl`), `element` o `species`, `a` (pm) y `molarMass` (g/mol) para la densidad; `blank` (`true` o una lista de `z`, `coordination`, `packing`, `density`) |

**Química orgánica.** Para estereoquímica y conformaciones (las estructuras y los mecanismos son
`molecule` y `reaction`):

| `type` | Qué dibuja | Claves principales |
| :--- | :--- | :--- |
| `newman` | Proyección de Newman | `front` y `back` (los tres sustituyentes de cada carbono), `dihedral` (el diedro entre el primero de adelante y el primero de atrás: 180 anti, 60 gauche, 0 eclipsada), `start`, `axis`; nombra la conformación; `blank`, `blankName`, `blankDihedral` |
| `chair` | Silla del ciclohexano | `substituents` (`position` de 1 a 6, `group`, `axial`, `blank`), `flip` (la inversión del anillo: los axiales pasan a ecuatoriales); dice si es cis o trans y, con valores A conocidos (CH₃ 7,3 kJ/mol, tBu 21…), cuál silla es más estable y por cuánto; `blank`, `blankRelation`, `blankStability` |
| `fischer` | Proyección de Fischer | `top`, `bottom` y `centers` (de arriba hacia abajo: `left`, `right`, `blank` (`left`, `right` o `true`), `priorities`: los lugares `top`, `right`, `bottom`, `left` de mayor a menor prioridad); con un solo centro, R/S sale de las reglas CIP para los grupos comunes (OH, NH₂, CHO, COOH, CH₂OH, CH₃, halógenos…); la serie D/L, del último centro; `showConfig`, `blankConfig`, `blankSeries`, `blank` |

**Química inorgánica.** Además de `orbitals` y `unit_cell`:

| `type` | Qué dibuja | Claves principales |
| :--- | :--- | :--- |
| `crystal_field` | Desdoblamiento del campo cristalino | `geometry` (`octahedral`, `tetrahedral`, `square_planar`), `electrons` (los d) o `metal` y `oxidation`, `spin` (`high`, `low`) o `ligand` (de la serie espectroquímica: desde el NH₃, campo fuerte), `complex` (la fórmula, de título); calcula el llenado, los desapareados, μ de solo espín y la EECC; `blankElectrons`, `blank`, `blankConfig`, `blankSpin`, `blankUnpaired`, `blankMoment`, `blankCFSE` |
| `complex` | Complejo de coordinación | `geometry`, `metal`, `ligands` (en orden: arriba, abajo, izquierda, derecha, adelante, atrás; en el cuadrado plano: izquierda, derecha, adelante, atrás), `charge`, `oxidation` (si un ligando no es de la tabla); calcula la fórmula, el estado de oxidación, la coordinación, los electrones d y el isómero (cis/trans, fac/mer); `blank` (`true` o una lista de `formula`, `oxidation`, `coordination`, `d`, `isomer`) |
| `latimer` | Diagrama de Latimer | `species`, `oxidation` y `potentials` (de la más oxidada a la más reducida), `compute` (pares de índices: el E° entre dos especies cualesquiera, Σ nE° / Σ n), `showDisproportionation`; `blankPotentials` (índices), `blankComputed`, `blankDisproportionation` |
| `frost` | Diagrama de Frost | las mismas claves que `latimer`: N·E° de cada especie respecto del estado 0; `showDisproportionation` marca las que quedan por encima de la recta entre sus vecinas; `blankLabels` |
| `born_haber` | Ciclo de Born-Haber | `start`, `steps` (`to`, `dH`, `label`, `blank`: de los elementos a los iones gaseosos), `formation` (ΔHf), `product`; la energía de red sale por la ley de Hess; `blankLattice` |

**Fórmulas.** En los rótulos, un número que sigue a un símbolo o a un paréntesis queda como subíndice
(`H2SO4`, `[Cu(NH3)4]`), lo que sigue a `^` como superíndice (`SO4^2-`, `Fe^3+`, `e^-`) y `_` fuerza
un subíndice (`K_a`, `pK_a1`, `σ^*_{2p}`, `S_N`). Un número al principio o después de un espacio es un
coeficiente (`2 H2O`), y `\2` es un dígito común (`S_N\2`). Los títulos de los diagramas de química
también aceptan fórmulas.

```yaml
type: titration
title: CH3COOH 0,1 M con NaOH 0,1 M
analyte: {kind: weak_acid, pKa: 4.76, conc: 0.1, volume: 25}
titrant: {conc: 0.1, name: NaOH}
indicator: {name: fenolftaleína, range: [8.2, 10]}
blankAnnotations: true        # el pH de la equivalencia y el pKa quedan para completar
```

Una curva de titulación marca solo los puntos de equivalencia que tienen un salto visible. Por eso, en
la del H₃PO₄ no aparece el tercero. En la semiequivalencia, el dibujo muestra el pH calculado, que
con un pKa bajo (el primero del fosfórico) ya no es igual al pKa.

#### Computación, señales, probabilidad y circuitos

Veintiséis tipos que parten de los datos del problema: alucarD (con dibu) calcula la solución, así
que la misma pregunta se puede variar cambiando los datos. Todos admiten `blank: true`, que dibuja
el enunciado con los casilleros de la respuesta vacíos.

| Área | Tipos y qué calculan |
|---|---|
| Sistemas digitales | `truth_table` (tabla de verdad, columnas intermedias con `steps`, Σm/ΠM con `canonical`), `karnaugh` (de 2 a 4 variables, agrupamientos mínimos, SOP o POS, indiferentes), `logic_circuit` (compuertas a partir de la expresión) |
| Arquitectura | `pipeline` (5 etapas, riesgos RAW, burbujas y CPI, con o sin `forwarding`), `ieee754` (campos de bits y pasos, de un valor o de los `bits`), `cache` (directa o asociativa, LRU/FIFO, aciertos y fallos forzosos, de capacidad y de conflicto) |
| Sistemas operativos | `cpu_scheduling` (FCFS, SJF, SRTF, RR, prioridad: Gantt y tiempos), `page_table` (traducción de direcciones), `page_replacement` (FIFO, LRU, OPT y reloj) |
| Redes y bases de datos | `subnetting` (VLSM o subredes iguales), `transaction_schedule` (conflictos, grafo de precedencia y serializabilidad) |
| Estructuras y algoritmos | `heap`, `hash_table` (encadenamiento, sondeo lineal, cuadrático y doble), `avl` (rotaciones), `bplus_tree`, `dp_table` (LCS, edición, mochila, monedas), `dijkstra`, `turing` |
| Señales | `signal` (continua o discreta, por expresión), `convolution` (paso a paso), `fourier` (DFT y series), `sampling` (aliasing y Nyquist) |
| Probabilidad | `distribution` (normal, uniforme, exponencial, t, χ², binomial, Poisson, geométrica, con el área y la probabilidad exacta), `venn` (2 o 3 conjuntos) |
| Circuitos | `circuit` (serie y paralelo, impedancia equivalente y corriente), `phasor` |

Las claves de cada tipo están en el README de dibu. En un banco GIFT se escriben en YAML en bloque,
sin llaves: en vez de `- { name: P1, burst: 8 }`, cada proceso en sus renglones:

```estructura
type: cpu_scheduling
algorithm: rr
quantum: 3
processes:
  - name: A
    burst: 5
  - name: B
    arrival: 1
    burst: 3
blank: true
```

#### Themes de los diagramas

Cada diagrama se dibuja con un theme de dibu: una paleta (fondo, trazos, rellenos, acento y textos)
y una tipografía. Los presets son `ink` (el de siempre, para imprimir), `color`, `high-contrast`
(todo negro sobre blanco) y `dark` (fondo oscuro, para pantallas).

- Para todo el examen, `tema_diagramas` en `[estilo]` de `alucard.toml` o en `estilo` de la
  definición. Con `alto_contraste` (o `--accessible`) y sin `tema_diagramas`, se usa `high-contrast`.
- Para un diagrama, `theme:` en el bloque, que manda sobre el del examen (`inkSaver` también).
- Un theme propio parte de un preset y cambia sólo lo que dice:

```yaml
# tema_unrn.yaml, junto a la definición: estilo.tema_diagramas = "tema_unrn.yaml"
extends: ink
colors:
  accentPrimary: "#1b365d"
  fillHighlight: "#dbe7f3"
typography:
  scale: 1.1          # letra más grande; los diagramas se acomodan
```

`alucard diagrama` dibuja un archivo suelto: un bloque, una lista de bloques o un documento de
statics. Escribe un SVG por bloque y saltea los que no son diagramas (texto, recortables):

```bash
alucard diagrama ~/dev/tools/statics/ejercicio_pila.json -o diagramas/
alucard diagrama arbol.yaml --color
alucard diagrama arbol.yaml --theme dark          # o --theme tema_unrn.yaml
```

`alucard diagramas-md` deja los diagramas de los Markdown como SVG versionados, para que los publique
quien no tiene alucarD (el sitio de enunciados, con `deckard export myst`). Cada bloque ```` ```estructura ````
de `<dir>/*.md` queda en `<dir>/diagramas/estructura-<hash>.svg`, donde `<hash>` son los 12 primeros
dígitos del SHA-1 del cuerpo del bloque sin espacios al principio ni al final; los SVG que ya no usa
ningún bloque se borran. Si escribe o borra algo termina con código 1; `--verificar` no escribe.

Como hook de pre-commit, en el repositorio que tiene los Markdown:

```yaml
repos:
  - repo: https://github.com/INGCOM-UNRN/alucarD
    rev: <commit>
    hooks:
      - id: alucard-diagramas
        files: ^banco/.*\.md$
```

### Saltos de página

En el PDF, una pregunta que entra en una página no se parte. Para las más largas:

- **`// [corte]`:** un renglón con esta marca, entre dos partes del enunciado, dice por dónde se puede
  cortar. Es un punto posible, no un salto: si la pregunta entra, sigue entera en la página. Moodle lo
  descarta, como cualquier comentario. En Moodle XML y en un enunciado Markdown se escribe `<!--corte-->`. `voight unify` y
  `voight tree collect` sacan las marcas del banco fusionado: para el PDF, generá desde los archivos originales.
- **Encabezados:** una pregunta que no entra en una página se corta además por sus encabezados
  (`####`) y antes de las opciones, sin marcas.
- **Si una parte tampoco entra**, se parte por donde toque, para que el texto no se encime.

```gift
::analisis::[markdown]Dado el siguiente código
```c
int main(void) ｛ return 0; ｝
```
// [corte]
#### 1. Análisis conceptual
Explicá qué hace el programa.
{}
```

Para que cada pregunta de desarrollo vaya en su propia hoja, con el resto de la hoja para responder:

```yaml
configuracion_examen:
  desarrollo_en_hoja_separada: true
```

### Espacio de las preguntas de desarrollo

Cada pregunta de desarrollo deja un recuadro con renglones para responder. La opción general vale para todo el
examen, y una pregunta pide otro espacio con una etiqueta, que manda sobre la general:

```yaml
configuracion_examen:
  espacio_desarrollo: grande
  forzar_espacio_desarrollo: false   # true: `grande` para todas, aunque pidan otro
```

```gift
// [tag, desarrollo-pagina]
::demostracion::Demostrá que el algoritmo termina.
{}
```

| Espacio | Etiqueta | En el PDF, con letra de 10 |
| :--- | :--- | :--- |
| `cero` | `desarrollo-cero` | Sin recuadro: sólo el enunciado. |
| `chico` | `desarrollo-chico` | 3 renglones, unos 1,7 cm. |
| `mediano` | `desarrollo-mediano` | 7 renglones, unos 4 cm. Es el valor por omisión. |
| `grande` | `desarrollo-grande` | 15 renglones, unos 8,5 cm. |
| `pagina` | `desarrollo-pagina` | La pregunta en su propia hoja, y el resto de la hoja para responder. |

Los renglones miden 16 pt, como los de las consignas prácticas, y la letra del examen cambia cuántos
entran. En HTML son los mismos, salvo `pagina`, que trae 30 y salta de hoja al imprimir. `pequeno` es el nombre anterior de `chico` y se sigue leyendo; `página`, con tilde, también.

Con `forzar_espacio_desarrollo: true`, la opción general vale para todas y las etiquetas no cuentan: así
un mismo banco puede salir sin recuadros en un examen y con ellos en otro.

`desarrollo_en_hoja_separada: true` es `pagina` para todas y manda sobre las dos opciones.
En Moodle XML el tamaño viaja en las mismas etiquetas; `responseformat` no cuenta, porque es el editor
de Moodle. Una pregunta sin etiqueta toma `espacio_desarrollo`.

### Números de línea en el código

Los bloques de código pueden llevar números de línea, en el PDF y en el HTML, para todo el examen o de a
uno. La marca va en un renglón justo antes del bloque y, como es un comentario, Moodle la descarta:

````gift
::traza::[markdown]¿Qué línea provoca el error?
// [numerar]
```c
int *p = NULL;
*p = 3;
```
{=La 2 ~La 1}
````

```yaml
configuracion_examen:
  numerar_codigo: true     # todos los bloques de los enunciados y de las opciones
```

Con `numerar_codigo: true`, `// [sin-numerar]` deja afuera un bloque, y la marca del bloque siempre manda
sobre la opción general. En Moodle XML y en un enunciado Markdown se escribe `<!--numerar-->` o
`<!--sin-numerar-->`. La marca vale para el bloque que le sigue, no para toda la pregunta, y arriba del título
no hace nada. La clave numera igual que el examen, salvo la solución de una consigna práctica.

### Tablas en las preguntas

Las tablas van en un bloque ```` ```tabla ````, con sintaxis Markdown y sin HTML. Las opciones de
presentación van en comentarios, entre corchetes: varias por renglón, en los renglones que hagan falta.

````gift
::traza::[markdown]Completá lo que imprime cada paso
```tabla
// [centrado] [ancho, 80%] [columnas, auto, 1fr, 1fr]
// [alinear, izquierda, centro, centro] [sombrear-encabezado]
| Paso | Valor | Salida |
|---|---|---|
| `[M1]` |  | No aplicable. |
| `[M2]` | `base = ` ________ |  |
```
{}
````

Moodle descarta los comentarios y, si se importa el GIFT directo, muestra el bloque como código, sin
chocar con la sintaxis de GIFT. `voight unify … -o banco.xml` lo convierte en una tabla HTML. Las
opciones valen para el PDF; el HTML siempre muestra la tabla con bordes.

| Opción | Efecto en el PDF |
| :--- | :--- |
| `[centrado]`, `[izquierda]`, `[derecha]` | Dónde va la tabla. Se nota si es más angosta que la página. |
| `[ancho, 80%]` | Ancho de la tabla, en `%`, `cm`, `mm`, `pt` o `em`. Las columnas se reparten ese ancho. |
| `[columnas, auto, 2fr, 30%]` | Ancho de cada columna: `auto`, una fracción o una medida. |
| `[alinear, izquierda, centro, derecha]` | Alineación del texto de cada columna. |
| `[alto, 3em]` | Alto de las celdas vacías, para escribir. |
| `[relleno, 8pt]` | Margen interno de las celdas. |
| `[letra, 0.85em]` | Tamaño de la letra. |
| `[bordes, todos]`, `[bordes, horizontales]`, `[bordes, ninguno]` | Qué líneas se dibujan. |
| `[sombrear-encabezado]`, `[cebra]` | Fondo gris en el encabezado, o en una de cada dos filas. |
| `[sin-encabezado]` | No imprime la primera fila. |

Una opción desconocida, o una lista que no coincide con las columnas, es error en `lint-gift` y en
`alucard generar`, y la tabla sale como un aviso.

- **Celda vacía:** es para completar a mano. Sin `[columnas]`, su columna toma el ancho que sobra, así
  que no hacen falta `&nbsp;`.
- **Completar al lado de un texto:** con `________` en la celda.
- **Un `|` adentro de una celda:** `\|`, o en código. Una fórmula `$|x|$` no necesita escaparlo.

Una tabla sin el bloque también se lee, pegada al texto o no, pero no admite opciones y choca con GIFT.

### Diagramas PlantUML

Un bloque ```` ```plantuml ```` dibuja un diagrama con [PlantUML](https://plantuml.com). Las opciones
van en comentarios al principio del bloque; `@startuml` y `@enduml` son optativos, y otros tipos
(`@startmindmap`, `@startsalt`…) se escriben con su propio inicio.

````gift
::clases::[markdown]Observá el diagrama.
```plantuml
// [centrado] [ancho, 60%] [alt, La lista apunta a su primer nodo]
class Lista {
  +agregar(x: int)
}

Lista --> Nodo : cabeza
```
¿Qué relación hay entre las clases?
{=Asociación ~Herencia}
````

| Opción | Efecto |
| :--- | :--- |
| `[centrado]`, `[izquierda]`, `[derecha]` | Dónde va el diagrama. Por omisión, centrado. |
| `[escala, 0.7]` | Tamaño del dibujo: `1` es el natural, que crece con la letra del examen. Es lo que hay que tocar para achicar o agrandar un diagrama. |
| `[ancho, 60%]`, `[alto, 5cm]` | Límites, en `%`, `cm`, `mm`, `pt` o `em`: achican un diagrama grande, pero uno chico queda como está. Nunca pasa del ancho de la página. |
| `[letra, 12]` | Tamaño de la letra del diagrama, en puntos. |
| `[color]` | Conserva los colores. Por omisión sale en blanco y negro, porque un examen se imprime. |
| `[tema, plain]` | Tema de PlantUML. También conserva los colores. |
| `[alt, texto]` | Texto alternativo. Por omisión, «diagrama». |

`configuracion_examen.escala_plantuml` cambia el tamaño de todos los diagramas del examen, salvo los que
traen su `[escala]`.

Una opción desconocida o inválida y un diagrama que no compila salen como un aviso en la pregunta;
`alucard generar` dice en cuál y `lint-gift` los informa con su línea.

Igual que un ```` ```estructura ````, el bloque no se importa en Moodle sin preprocesar, así que adentro
valen `:`, llaves y renglones en blanco. `voight unify … -o banco.xml` lo pasa a una imagen, con las
mismas opciones.

Lo dibuja el programa `plantuml` del `PATH`; otro se indica con `ALUCARD_PLANTUML` (el comando) o
`PLANTUML_JAR` (el `.jar`, con `java`). `alucard doctor` dice cuál encontró. Cada dibujo queda en
`~/.cache/alucard/plantuml/`, así que Java arranca una sola vez por diagrama.

### `alucard lint-gift` (antes `gift-linter`)

Valida bancos GIFT: el formato de cada pregunta, que se puedan importar en Moodle, los bloques
```` ```estructura ```` y, con `--compilar`, el código C. Cada problema lleva su línea y el título de
su pregunta.

- **Moodle:** ver [Compatibilidad con Moodle](#compatibilidad-con-moodle).
- **Diagramas:** un bloque que no se puede dibujar (tipo desconocido, datos inválidos), uno con un
  renglón en blanco (GIFT corta la pregunta ahí) o con llaves (abren las respuestas).
- **Código (`--compilar`):** los bloques ```` ```c ```` que son programas completos (tienen `main`)
  pasan por `gcc -fsyntax-only -std=c11`, ya decodificados (el código de un GIFT viene escapado o en
  caracteres de ancho completo, como el de los sintetizados). Los fragmentos se saltean.

| Opción | Descripción |
| :--- | :--- |
| `ARCHIVOS...` | Uno o más bancos `.gift`, o carpetas: se revisan los `.gift` de sus subcarpetas. |
| `--fix` | Deja el banco compatible con Moodle, en el lugar. |
| `--compilar` | Compila el código C de las preguntas. |

```bash
alucard lint-gift bancos/*.gift                       # formato y diagramas
alucard lint-gift sintetizados/*.gift --compilar      # además, que el código compile
alucard lint-gift bancos --fix                        # toda la carpeta, con sus subcarpetas
```

#### Compatibilidad con Moodle

Un banco GIFT se importa en Moodle tal cual, salvo las preguntas con bloques ```` ```estructura ````
o ```` ```plantuml ```` o fórmulas `$...$`, que hay que preprocesar: `voight unify … -o banco.xml` las pasa a imágenes. Moodle toma como texto de la pregunta lo que siga a las respuestas, así que
todo lo propio de alucard va en comentarios, en el mismo párrafo que la pregunta (sin renglones en
blanco en el medio; uno separado no se aplica, igual que en Moodle):

```gift
$CATEGORY: tipos/structs

// [tag, structs, padding] [category, tipos/relleno]
::offset-campo::[markdown]¿En qué offset queda el campo `b`? {
=`4`
~`1`
}

// Criterio (2 puntos): la fuga pierde memoria accesible; el colgante apunta a memoria liberada.
// [tag, desarrollo-grande, punteros]
::fuga-vs-colgante::Explicá la diferencia entre una fuga y un puntero colgante. {}
```

- **Etiquetas:** `[tag, punteros, facil]`, con una o varias, sin `:`. Moodle ignora el comentario, así
  que un GIFT importado directo llega sin etiquetas; `voight convert gift-to-xml` las pasa al XML.
  `[tag:nombre]`, el formato que exporta Moodle, se lee, pero es error en `lint-gift` y `--fix` lo cambia.
- **Categoría de una sola pregunta:** `[category, ruta]`. Moodle la ignora; para que la tome, usá `$CATEGORY:`.
- **Criterio de corrección:** el resto del comentario pegado arriba de la pregunta va a la clave del
  profesor, debajo de la respuesta, sin las `//` ni los renglones que sólo separan (`// =====`). Un
  comentario separado por un renglón en blanco no se toma.
- **Desarrollo:** `{}`, la pregunta de ensayo de Moodle. El tamaño va en la etiqueta
  `desarrollo-cero`, `-chico`, `-mediano`, `-grande` o `-pagina`, que alucard no cuenta como etiqueta
  para filtrar. Ver [Espacio de las preguntas de desarrollo](#espacio-de-las-preguntas-de-desarrollo).
- **Dos puntos:** las preguntas no usan `:` en el título, el enunciado, las opciones ni el código,
  porque GIFT les da significado. Se escriben en ancho completo (`：`), que alucard muestra como `:`, o
  escapados (`\:`). Quedan exentos los bloques ```` ```estructura ````, las
  fórmulas, los comentarios, `$CATEGORY:` y las respuestas numéricas (`{#3:2}`).

`[tags: a, b]`, `[category: x]` y `{desarrollo:grande}` se siguen leyendo con un aviso, pero son error
en `lint-gift`. `--fix` los migra y pasa los `:` a ancho completo; sin cambiar lo que se imprime.

### Justificación en las preguntas de selección múltiple

Para pedir que el alumno explique la opción que marcó, `configuracion_examen.lineas_justificacion`
agrega debajo de cada pregunta de selección múltiple una sección «Justificación» con esa cantidad de
renglones, en el HTML y en el PDF. Con `0` (por omisión) no hay sección. Cada pool puede cambiar la
cantidad con su propio `lineas_justificacion` (`0` la quita en ese pool); el resto de los tipos de
pregunta (verdadero/falso, consignas, desarrollo) no cambia. El título sale del idioma del examen
(«Justificación», «Justification») o de `titulo_justificacion`.

```yaml
configuracion_examen:
  lineas_justificacion: 3                     # de 0 a 60
  titulo_justificacion: "Justificá tu respuesta"

secciones_examen:
  - nombre: "Parte 1"
    pools:
      - categoria: "estructuras/listas"
        cantidad: 2
      - categoria: "estructuras/pila-de-llamadas"
        cantidad: 2
        lineas_justificacion: 6               # más lugar para trazar la pila
      - categoria: "estructuras/arreglos"
        cantidad: 2
        lineas_justificacion: 0               # sin justificación
```

### Bancos en una carpeta

En lugar de nombrar cada archivo, `input_banco` (y `-i`) acepta una carpeta: alucard carga todos los
`.gift` y `.xml` que encuentra en ella y en sus subcarpetas. Archivos y carpetas se pueden mezclar.

```text
bancos/
├── unidad1/
│   ├── teoria.gift
│   └── codigo.xml
├── unidad2/
│   └── teoria.gift
├── borrador.txt        # no se lee: dentro de una carpeta sólo cuentan .gift y .xml
└── .viejos/            # no se lee: se saltean las carpetas ocultas
    └── teoria.gift
```

```yaml
# En la definición (o en alucard.toml, con las rutas relativas a ese archivo)
input_banco:
  - "bancos"                    # los tres bancos de arriba
  - "extra/banco_ejemplo.txt"   # un .txt se lee sólo si se lo nombra
```

```bash
alucard generar -d parcial.yaml -i bancos        # -i reemplaza al input_banco de la definición
alucard generar -d parcial.yaml -i bancos -i extra/repaso.gift   # -i se repite
```

Reglas de la carga:

- **Sin repetir.** Un archivo que aparece por su carpeta y también nombrado aparte se carga una sola vez.
- **Ids.** Los ids de las preguntas tienen que ser únicos entre todos los archivos: si dos repiten un
  id, queda la del último que se carga y la otra se descarta. Queda asentado: ver
  [Ids repetidos](#ids-repetidos).
- **Carpeta vacía.** Una carpeta sin `.gift` ni `.xml` no es un error; `generar` lo avisa.
- **Categorías y etiquetas.** Sin un `banco.toml`, la carpeta no cambia la categoría de las
  preguntas (sigue siendo la del `$CATEGORY:` del GIFT o la `<category>` del XML) ni sus etiquetas.
  Con uno, salen de las carpetas: ver [Categorías y etiquetas por carpeta](#categorías-y-etiquetas-por-carpeta).
- **Caché.** Lo que se leyó de cada banco queda guardado: ver [Caché de los bancos](#caché-de-los-bancos).

**El filtro `banco` de un pool.** Para las preguntas que vienen de una carpeta, su banco es la ruta
del archivo dentro de esa carpeta (`unidad1/teoria.gift`). El filtro compara el final de la ruta,
así que puede ser tan preciso como haga falta:

```yaml
pools:
  - banco: "unidad1/teoria.gift"   # sólo el de unidad1
    cantidad: 3
  - banco: "teoria.gift"           # los dos teoria.gift, el de unidad1 y el de unidad2
    cantidad: 2
  - banco: "codigo.xml"
    cantidad: 1
```

Las carpetas valen también en `alucard lint-gift bancos` (revisa sus `.gift`), en `alucard categorias bancos`
y en los `-i` de `ver`, `build` y `balance-check`. Con `--watch`, un archivo nuevo dentro de la carpeta
dispara otra generación.

#### Ids repetidos

El id de una pregunta GIFT sale de su posición en el archivo y de su nombre (`gift_1_a` es la
primera, `::a::`); el de una de Moodle XML, igual (`moodle_1_a`), y el de una consigna, de su
`ejercicio.yaml` (`deckard:<id>`). Por eso dos bancos armados con la misma plantilla, como
`unidad1/teoria.gift` y `unidad2/teoria.gift`, pueden repetir ids aunque el texto sea distinto.

Cuando dos preguntas tienen el mismo id, queda la del último banco que se carga (las rutas en el orden
en que se nombran y, dentro de una carpeta, en orden alfabético; los bancos antes que las consignas
y los repositorios externos) y la otra no puede salir en el examen. No frena la generación, pero
queda asentado en:

- el **resumen del final** de `alucard generar` y `validar`, entre lo que hay que revisar antes de
  imprimir (y en `avisos` con `--json`):

  ```text
  Revisá antes de imprimir (1):
    ! parcial.yaml: id repetido gift_1_a («a»): queda la de bancos/unidad2/teoria.gift, se descarta la de bancos/unidad1/teoria.gift
  ```

- el **`informe.md`**, en la sección «Ids repetidos», con una fila por id: la pregunta, el archivo de
  la que queda y el de la descartada;
- el **inventario** (`alucard categorias --resumen`), al final, porque la descartada no cuenta en los
  totales.

Para resolverlo, cambiá el nombre (`::a::`) de una de las dos o su lugar en el archivo.

#### Categorías y etiquetas por carpeta

Si las carpetas ya ordenan las preguntas por tema, no hace falta repetir ese orden con `$CATEGORY:` y
`[tag, …]` en cada archivo: un `banco.toml` en la carpeta del banco le dice a alucard que lo tome de
la estructura.

```toml
# bancos/banco.toml
categoria = "prefijo"            # de dónde sale la categoría (ver la tabla)
etiquetas = true                 # cada carpeta del camino, una etiqueta
incluir_archivo = false          # el nombre del archivo, sin extensión, cuenta como una carpeta más
agregar_etiquetas = ["parcial1"] # etiquetas fijas para todo lo que hay debajo
```

| `categoria` | `bancos/punteros/arreglos/practica.gift` con `$CATEGORY: $course$/Top/Repaso` | Sin `$CATEGORY` |
| :--- | :--- | :--- |
| `archivo` (por omisión) | `$course$/Top/Repaso` | `General` |
| `carpeta` | `punteros/arreglos` | `punteros/arreglos` |
| `prefijo` | `punteros/arreglos/Repaso` | `punteros/arreglos` |
| `si_falta` | `$course$/Top/Repaso` | `punteros/arreglos` |

Con `etiquetas = true`, esa pregunta suma `punteros` y `arreglos` a las suyas. Con
`incluir_archivo = true`, el archivo cuenta como un nivel más: categoría `punteros/arreglos/practica`
y etiqueta `practica`. La carpeta nombrada en `input_banco` no cuenta (es la raíz), así que un banco
que está directamente en ella conserva su categoría (salvo con `incluir_archivo`) y sólo suma
`agregar_etiquetas`. `prefijo` descarta el
contexto de Moodle (`$course$`, `Top`, `Default`) antes de colgar la categoría del archivo debajo de la
carpeta.

Un `banco.toml` vale para su carpeta y todo lo que tiene adentro. Uno en una subcarpeta cambia sólo
las claves que escribe, para ese subárbol:

```text
bancos/
├── banco.toml                  # categoria = "carpeta", agregar_etiquetas = ["parcial1"]
├── punteros/teoria.gift        # categoría punteros, etiqueta parcial1
└── importados/
    ├── banco.toml              # categoria = "archivo": estos ya traen su $CATEGORY de Moodle
    └── moodle.xml              # su propia categoría, etiqueta parcial1
```

Los pools filtran con lo que queda, como con cualquier categoría o etiqueta:

```yaml
pools:
  - categoria: "punteros"         # punteros/… y todas sus subcarpetas
    cantidad: 2
  - etiquetas: ["arreglos"]
    cantidad: 1
```

Un archivo nombrado directamente (no a través de su carpeta) no usa `banco.toml`. Una clave
desconocida o un valor inválido es un error con el nombre del `banco.toml`, para que un nombre mal
escrito no pase en silencio. Los `repositorios_externos` de preguntas también lo usan. Para ver cómo quedaron las categorías:
`alucard categorias bancos`.

#### Caché de los bancos

Leer un banco grande lleva tiempo (el Markdown, el código y los diagramas de cada pregunta), así que
alucard guarda lo leído de cada `.gift` y `.xml` en `~/.cache/alucard/bancos/` y la próxima vez lo
toma de ahí si el archivo no cambió. No hay que hacer nada para usarlo ni para invalidarlo:

- La clave es el **contenido** del archivo, no su fecha: editarlo lo vuelve a leer, y un `git checkout`
  que no cambia el texto no.
- Actualizar alucard (o cambiar su código) descarta lo guardado.
- `banco.toml` no entra en el caché: las categorías y etiquetas por carpeta se aplican en cada corrida,
  así que cambiarlo vale enseguida.
- Los avisos del banco (una pregunta omitida, la sintaxis vieja de GIFT) se repiten aunque salga del
  caché.
- Lo que no se usa en 60 días se borra solo.

| Variable de entorno | Qué hace |
| :--- | :--- |
| `ALUCARD_SIN_CACHE=1` | No usa el caché: lee siempre los bancos y no guarda nada. |
| `ALUCARD_CACHE_DIR` | Otra carpeta para el caché (por omisión, `$XDG_CACHE_HOME/alucard/bancos`). |

Para vaciarlo, alcanza con borrar la carpeta: `rm -r ~/.cache/alucard/bancos`.

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
  - ruta: "~/catedra/preguntas"      # todos los .gift y .xml de la carpeta
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

**Otra pregunta en cada tema.** Con `sortear_por_tema: true`, cada tema toma otras preguntas: en
`configuracion_examen` vale para todos los pools, y en un pool sólo para él, que es lo que conviene si el
resto del examen debe ser igual para todos. Los temas recorren las candidatas en orden, así que se usan
todas antes de repetir: con 4 candidatas y 8 temas, cada pregunta sale en 2 temas.

```yaml
pools:
  - categoria: "analisis/parcial_3_diagramas"
    cantidad: 1
    sortear_por_tema: true
    puntaje_fijo_por_pregunta: 20.0
```

Sin puntaje fijo, los temas pueden sumar distinto; `generar` lo avisa.

**Temas con las mismas preguntas.** `generar` avisa, en el resumen del final (y en `avisos` con
`--json`) y en la sección «Orden de cada tema» del `informe.md`, cuando dos o más temas salen con las
mismas preguntas:

```text
Revisá antes de imprimir (2):
  ! parcial.yaml: los temas 1 y 3 son idénticos: mismas preguntas, en el mismo orden y con las mismas opciones. …
  ! parcial.yaml: los temas 1, 2 y 3 tienen las mismas preguntas (cambia sólo el orden): para que cada tema tenga otras, usá sortear_por_tema.
```

- **Idénticos** son los temas con las mismas preguntas, en el mismo orden y con las opciones en el
  mismo orden: pasa con `mezclar_preguntas_dentro_seccion` y `mezclar_opciones_dentro_pregunta`
  apagadas, o con preguntas sin opciones y una sola por sección.
- **Mismas preguntas en otro orden** es lo que pasa siempre sin `sortear_por_tema`. Con
  `sortear_por_tema`, quiere decir que los pools que sortean no tienen candidatas suficientes para
  que cada tema tenga otras: hay que sumar preguntas al banco o bajar la cantidad.

`validar` compara las preguntas de cada tema, pero no su orden, que se sortea al generar.

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
| `lineas` | `20` | Cuántos renglones; `0`, ninguno. |
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

### Registro de exámenes tomados: `alucard registro`

Cada examen que se toma se puede anotar en un registro: un JSON por examen, con la definición tal
como estaba, cada pregunta con su contenido y el orden de preguntas y opciones de cada tema. Con eso:

- **No se repiten preguntas en el cuatrimestre.** `generar` y `validar` dejan afuera las preguntas
  que ya salieron en otro examen registrado del mismo cuatrimestre.
- **Se cruzan datos.** `alucard registro usadas` muestra en qué exámenes salió cada pregunta.
- **Se mide la calidad de cada pregunta.** Con los resultados importados, `alucard registro analizar`
  calcula su dificultad, su discriminación, las omisiones y cómo funcionan los distractores, sumando
  todos los exámenes en que salió.

Registrar es explícito, porque un examen se arma de a poco y sólo cuenta como tomado la versión que
se guarda:

```bash
alucard validar -d parcial1.yaml                 # se itera sobre la definición
alucard registro guardar -d parcial1.yaml        # la versión que se toma (o: alucard generar --registrar)
alucard registro resultados parcial1 notas.csv   # después del examen
alucard registro analizar -o calidad.md          # todas las preguntas con resultados
alucard registro listar
alucard registro usadas --cuatrimestre 2026-2C
```

`registro guardar` arma el examen igual que `generar` con las mismas opciones (`-n`, `-s`, `-i`): las
mismas preguntas, en el mismo orden y con las mismas opciones. No genera archivos. Volver a guardarlo
lo reemplaza y sube su `revision`. Si el examen ya tiene resultados, se conservan si las preguntas no
cambiaron; si cambiaron, hace falta `--forzar` y los resultados se descartan.

**Dónde y con qué nombre.** Cada examen va en `<carpeta>/<cuatrimestre>/<id>.json`, un archivo por
examen, para versionarlo en git sin conflictos.

| Dato | De dónde sale, en orden |
| :--- | :--- |
| carpeta | `carpeta` de `[registro]` en `alucard.toml`; si no, `registro/` junto al `alucard.toml` (o a la definición). `--carpeta` en `listar`, `usadas`, `resultados` y `analizar`. |
| cuatrimestre | `--cuatrimestre`, `registro.cuatrimestre` de la definición, `cuatrimestre` de `[registro]`. Si no está en ninguno, sale de la `fecha` del examen (o de hoy): `2026-1C` de enero a julio, `2026-2C` de agosto a diciembre. |
| id | `--registro-id`, `registro.id` de la definición o el nombre del archivo de la definición (`parcial1`). |

```toml
[registro]
carpeta = "registro"
cuatrimestre = "2026-2C"
repetidas = "evitar"         # "evitar" (por omisión), "avisar" o "permitir"
```

**Preguntas repetidas.** Una pregunta es la misma si tiene el mismo `id` o la misma huella. La huella
se calcula sobre el contenido: el tipo, el enunciado y las opciones, sin importar su orden. Así, cambiarle
el nombre o moverla de banco no la esconde. Lo que pasa con una pregunta que ya salió en el cuatrimestre
depende de `repetidas`:

| `repetidas` | Qué pasa |
| :--- | :--- |
| `evitar` | Queda afuera de los pools. Si un pool se queda sin preguntas, el error lo dice. Una pregunta fijada (`preguntas_fijadas`) se queda igual, con un aviso. |
| `avisar` | Se puede elegir, y cada una que sale queda en el resumen («Revisá antes de imprimir»). |
| `permitir` | No se mira el registro. |

A un examen ya registrado sólo lo restringen los exámenes registrados antes que él. Así, volver a
guardar `parcial1` da las mismas preguntas aunque después se haya registrado `parcial2` con otras.
Otros cuatrimestres no cuentan.

**Resultados.** `alucard registro resultados <id> <archivo.csv>` lee un CSV con una fila por
estudiante:

| Columna | Qué lleva |
| :--- | :--- |
| `estudiante` (o `student_id`, `legajo`) | Quién es. |
| `tema` | El número de tema que rindió. |
| `ausente` | Opcional: `si` si no se presentó. |
| `1`, `2`… (o el id de la pregunta) | Una por pregunta, con su número en el tema. Va la letra marcada (`A`, `B`…; `V` o `F` en verdadero o falso), el puntaje obtenido (en desarrollos y consignas) o nada si la dejó en blanco. |

```csv
estudiante,tema,ausente,1,2,3,4
C001,1,,B,A,V,2.5
C002,2,,D,,F,1
C003,1,si,,,,
```

Una letra que la pregunta no tiene, un puntaje fuera de rango o una columna que falta frenan la
importación, con la fila. Para reemplazar resultados ya importados hace falta `--forzar`.

**Calidad de las preguntas.** `alucard registro analizar` (con `--cuatrimestre`, `--examen`, `-o` o
`--json`) suma cada pregunta en todos los exámenes en que salió y calcula:

| Medida | Qué es | Cuándo avisa |
| :--- | :--- | :--- |
| Dificultad | Puntaje medio sobre el máximo (1 = todos bien). | Más de 0,90 (muy fácil) o menos de 0,20 (muy difícil). |
| Discriminación | Correlación entre la pregunta y el resto del examen (ítem-resto). | Menos de 0,20, y negativa: a los que mejor les fue les va peor en esta, así que hay que revisar la clave. |
| D | Dificultad en el 27 % al que mejor le fue menos en el 27 % al que peor le fue. | — |
| Omisión | Cuántos la dejaron en blanco. | Más del 25 %. |
| Opciones | Cuántos eligieron cada opción. | Un distractor que elige menos del 5 % no funciona. Uno que atrae a los que mejor les fue sugiere una clave o una redacción ambigua. |

Con menos de 10 respuestas, el análisis avisa que es orientativo. Para cada tema calcula además el
alfa de Cronbach, que mide la confiabilidad del examen.

**El formato `alucard-examen/1`.** Se valida con su JSON Schema
(`generador_examenes/core/esquemas/alucard-examen-1.schema.json`) al leerlo y al escribirlo:

```json
{
  "schema": "alucard-examen/1", "id": "parcial1", "cuatrimestre": "2026-2C", "revision": 2,
  "registrado": "2026-09-01T10:00:00.000000", "actualizado": "2026-09-08T18:30:00.000000", "alucard": "5.11.0",
  "examen": {"nombre": "Parcial 1", "institucion": "UNRN", "materia": "Programación I", "fecha": "2026-09-10", "duracion_minutos": 120},
  "definicion": {"archivo": "parcial1.yaml", "sha256": "…", "contenido": {"…": "la definición YAML tal como estaba"}},
  "generacion": {"semilla": 42, "numero_temas": 2, "bancos": ["bancos"], "repetidas": "evitar", "excluidas": ["gift_3_q2"]},
  "preguntas": {
    "gift_1_q0": {"huella": "sha256:…", "nombre": "q0", "tipo": "seleccion_multiple", "categoria": "punteros",
                  "etiquetas": [], "fuente_banco": "teoria.gift", "enunciado_html": "<p>…</p>",
                  "opciones": [{"texto_html": "…", "es_correcta": true}, {"texto_html": "…", "es_correcta": false}]}
  },
  "temas": [
    {"tema": 1, "semilla": 42, "secciones": [{"nombre": "Teoría", "preguntas": [
      {"orden": 1, "id": "gift_1_q0", "puntaje": 2.0, "opciones": [1, 0], "correctas": ["B"]}]}]}
  ],
  "resultados": {"importado": "2026-09-12T09:00:00", "fuente": "notas.csv", "estudiantes": [
    {"estudiante": "C001", "tema": 1, "ausente": false,
     "respuestas": {"gift_1_q0": {"opcion": "B", "puntaje": 2.0, "omitida": false}}}]}
}
```

- `preguntas` tiene cada pregunta una sola vez, con sus opciones en el orden del banco.
- En cada tema, `opciones` dice qué opción del banco quedó en cada letra: `[1, 0]` es «A es la
  segunda del banco, B la primera».
- `correctas` son las letras correctas de ese tema.
- `resultados` es `null` hasta que se importan.

### Exámenes con carátula OMR: `alucard omr`

Implementa [`OMR_SPEC.md`](OMR_SPEC.md): un examen por estudiante cuya página 1 lleva una franja que
corrige la app Android **Escáner OMR**. La franja tiene:

- cuatro fiduciales ArUco;
- una fila de burbujas por ejercicio de la rúbrica;
- las cifras de la nota final y la marca de ausente;
- un QR con el `STUDENT_ID` interno del estudiante (nunca el DNI ni el legajo).

En la SPEC el programa se llama `omr-gen`. Acá sus subcomandos van debajo de `alucard omr`, porque
`alucard build` ya existe.

```bash
alucard omr validate --config exam.yaml --roster inscriptos.csv
alucard omr preview-curve --config exam.yaml
alucard omr build --config exam.yaml --roster inscriptos.csv --questions bancos/ --out dist/PROG1-2026-P1/
alucard omr calibration-sheet --manifest dist/PROG1-2026-P1/layout_OMR5E_v7.json --out layout_test.pdf
alucard omr verify-geometry --pdf dist/PROG1-2026-P1/examenes_PROG1-2026-P1.pdf \
  --manifest dist/PROG1-2026-P1/layout_OMR5E_v7.json --todas
```

**`exam.yaml`** (o `exam.json`) tiene las claves de la SPEC (§3.1): `exam_id`, `title`, `layout_id`,
`layout_version`, `variants`, `cloud_sync_default`, `grade_scale`, `grade_map` y `rubric`. alucard
suma dos claves para el enunciado:

| Clave | Qué hace |
| :--- | :--- |
| `definicion` | Una definición de examen de alucard (relativa a `exam.yaml`). Cada variante es un tema de esa definición: A es el tema 1, B el 2, con la semilla de la definición. |
| `seed` | La semilla del sorteo (por omisión, la de la definición, la de `alucard.toml` o 42). |

Sin `definicion`, el enunciado tiene una pregunta por ejercicio de la rúbrica, en su orden. Es la del
banco que tiene la etiqueta con el `id` del ejercicio (`// [tag, ej1]`), y si hay varias, cada
variante toma otra. Con `--questions`, los bancos (archivos o carpetas) reemplazan al `input_banco`
de la definición.

**Validación (§3.3).** `validate` y `build` revisan todas las reglas y listan cada problema en su
renglón; con alguno, salen con 1. Además de las reglas de la SPEC, alucard pide:

- que `min` y `max` sean enteros y que la fila de unidades tenga hasta 11 burbujas;
- que `step` sea `null`, `0.5` o `0.25`;
- que el QR de la carátula entre en 47 caracteres.

`validate --roster` también revisa la nómina.

**Nómina (`inscriptos.csv`).** Las columnas `legajo,apellido,nombre` son obligatorias; `student_id` y
`variante` son opcionales.

- Al que no trae `student_id` le toca el siguiente libre de `C001`…`C999`, en el orden de la nómina.
- Las variantes que faltan se reparten en ronda.
- El legajo y el `student_id` no pueden repetirse.

**Lote (§8).** Todo va en `--out` (por omisión, `dist/<exam_id>/`):

| Archivo | Qué es |
| :--- | :--- |
| `examenes_<exam_id>.pdf` | Un examen por estudiante, en A4 exacto. Ver la lista de abajo. |
| `roster_<exam_id>.csv` | `student_id,legajo,apellido,nombre,variante`, UTF-8 con BOM. **Sólo docentes.** |
| `layout_<layout_id>_v<version>.json` y `.sha256` | El manifiesto `omr-layout/2`, validado con su JSON Schema. |
| `config_qr_<exam_id>.pdf` y `.svg` | La hoja docente: el QR `OMRCFG2:` (más el respaldo `OMRCFG/2` cuando alcanza), la rúbrica, el `sha256` del manifiesto y la tabla porcentaje → nota. **Lleva la `hmac_key`.** |
| `layout_test_<layout_id>.pdf` | La hoja de calibración: en cada fila, las burbujas rellenas al 0, 25, 50 y 100 %. |
| `build_<exam_id>.log` | Lo generado, con el `sha256` del manifiesto y de cada archivo. |

Cada examen de `examenes_<exam_id>.pdf`:

- en la página 1, la franja y el nombre ya escrito;
- desde la página 2, el QR `EXAM_ID/STUDENT_ID/P<n>` en el pie;
- un número par de páginas, así cada carátula cae en el frente de una hoja impresa a doble faz.

La `hmac_key` se genera una vez y queda en `.hmac_key` (permisos 600). Así, regenerar el lote no
invalida las carátulas ya impresas ni la sesión de la app; `--nueva-clave` la cambia. Un
`.gitignore` en la salida deja fuera del repositorio la clave, la nómina, la hoja docente y la planilla.
`--qr-config-mode compact` usa el QR compacto como principal. No alcanza, y `build` sale con 1, si:

- la escala no es de 1 a 10;
- el redondeo no es `half_up`;
- un ejercicio tiene etiquetas propias;
- `cloud_sync_default` está activo.

**Modo planilla (`--modo planilla`).** Las burbujas no ocupan lugar en las hojas de los estudiantes.
El docente carga las notas en una planilla aparte y la digitaliza con la misma app:

```bash
alucard omr build --config exam.yaml --roster inscriptos.csv --out dist/P1/ --modo planilla
alucard omr verify-geometry --pdf dist/P1/planilla_P1.pdf --manifest dist/P1/layout_OMR5E_v7.json --todas
```

- `examenes_<exam_id>.pdf` sale sin franja ni QR de pie. Cada examen conserva el nombre del
  estudiante y su `VARIANTE`, porque la nómina asigna la variante de cada uno. El encabezado vuelve a
  estar en la página 1.
- `planilla_<exam_id>.pdf` tiene, por estudiante y en el orden de la nómina, el mismo marco que la
  carátula: los cuatro ArUco, las burbujas del manifiesto, el QR `V/EXAM_ID/STUDENT_ID/…` con su `CHK`,
  y el nombre con el `STUDENT_ID` y la variante. Como el marco y el QR no cambian, la app lo lee igual
  que una carátula. El manifiesto, la hoja docente y la de calibración tampoco cambian.
- En cada hoja entran tantos marcos como permite el alto del marco: 3 con el mínimo de 55 mm y 2 con
  los 74 mm del ejemplo de la SPEC. `--por-hoja N` pone como mucho N.
- Entre marco y marco quedan 22 mm y una línea de corte (✂). Se escanea un marco por vez. Si la
  cámara toma también los marcadores del marco vecino y la app se confunde, recortá la planilla por
  las líneas, o generala con `--por-hoja 1`.

`verify-geometry` reconoce las páginas con varios marcos. Junta cada marcador 0 con los 1, 2 y 3 que
están donde los pone el manifiesto y verifica cada marco por separado: informa «página 1, marco 2».

El QR `OMRCFG2:` lleva el manifiesto entero, y con la rúbrica de ejemplo de la SPEC sale en versión
28-M. Por eso la hoja docente lo imprime con 0,5 mm por módulo, unos 65 mm de lado.

**Curva (§5).** `preview-curve`, y `build` antes de compilar, imprimen la nota y la condición en los
puntos de §5: 0 %, 30 %, justo antes de cada umbral y en él, los puntos medios y 100 %. La nota
redondeada nunca cruza un umbral que el porcentaje no alcanzó: con 59,9 %, 3,99 queda en 3,9.

**Geometría (§11.2).** `verify-geometry` hace estos pasos, sin OpenCV:

1. rasteriza la página a 300 DPI con `pdftoppm` (poppler-utils);
2. detecta los cuatro ArUco y decodifica su matriz;
3. rectifica el marco con una homografía;
4. mide el centro del contorno de cada burbuja contra su lugar en el manifiesto.

Sale con 1 si alguna burbuja queda a 0,3 mm o más (`--tolerancia`). Por omisión revisa la página 1;
`--todas` revisa cada página con carátula (o con marcos de la planilla), y `--pagina N` revisa la que se le indique.
`alucard doctor` dice si está `pdftoppm`.

El corpus sintético de §11.4 (marcas simuladas, perspectiva, ruido) corre el módulo OMR de la app
Android, que no es parte de alucard.

### Entregar los temas con uatu

alucarD arma exámenes para imprimir. Si el examen se rinde en la computadora, `alucard repartir` deja
listo el tema de cada estudiante; cifrarlo y liberarlo a la hora es de `uatu-admin paquetes`:

```bash
alucard build -d parcial.yaml -n 3 -o temas
alucard repartir temas --padron padron.txt -o repartidos
uatu-admin paquetes sellar repartidos --key-id prof-lead-2026
```

`padron.txt` tiene un usuario de GitHub por línea. El sorteo reparte los temas en partes iguales y
depende de `-s`. Las claves de corrección no se copian, y `repartidos.asignacion.csv` queda fuera de
la carpeta para que no se selle con los exámenes: corregís con ese archivo.

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

## 6. Referencia de configuración

Todas las claves de la definición YAML y de `alucard.toml`. Lo que no se escribe toma el valor de
la columna **Por omisión**. Una clave desconocida en el YAML se ignora sin aviso, así que un nombre
mal escrito no da error: conviene revisar con `alucard validar`.

**Quién manda.** La línea de comandos, después la definición YAML, después `alucard.toml` y, al final,
el valor por omisión. `estilo` se combina clave por clave.

**Rutas.** Las de `alucard.toml` son relativas a ese archivo, igual que `logo` a su archivo. Las demás
rutas del YAML son relativas a la carpeta desde la que se ejecuta alucard.

### Definición del examen (YAML)

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `nombre_examen` | texto | **obligatoria** | Título del examen. |
| `institucion` | texto | **obligatoria** | Institución, en el encabezado. |
| `materia` | texto | **obligatoria** | Materia, en el encabezado. |
| `configuracion_examen` | sección | **obligatoria** (puede ir vacía: `{}`) | Ver [`configuracion_examen`](#configuracion_examen). |
| `secciones_examen` | lista | **obligatoria** | Ver [`secciones_examen`](#secciones_examen). |
| `fecha` | texto | — | Fecha, en el encabezado. |
| `duracion_minutos` | entero | — | Duración, en el encabezado. |
| `instrucciones_generales` | texto | — | Recuadro de instrucciones al principio. |
| `idioma` | texto | `es` | Textos fijos del examen: `es` o `en`. |
| `variables_personalizadas` | diccionario | `{}` | Textos con `{nombre_examen}`, `{fecha_actual}`, `{anio_actual}` y otros campos. Sólo el HTML muestra `profesor` y `aula`. |
| `estilo` | sección | `{}` | Ver [`estilo`](#estilo). Se suma al `[estilo]` del curso. |
| `input_banco` | lista de rutas | la del toml | Bancos `.gift` y `.xml`, o carpetas con sus subcarpetas (ver [Bancos en una carpeta](#bancos-en-una-carpeta)). `-i` la reemplaza. |
| `input_consignas` | lista de rutas | — | Carpetas de consignas prácticas de deckard. `--consignas` se suma. |
| `repositorios_externos` | lista | `[]` | Ver [`repositorios_externos`](#repositorios_externos). `--repositorio` se suma. |
| `output_dir` | ruta | la del toml; si no, `./output` | Carpeta de salida. `-o` la reemplaza. |
| `subdirectorio` | ruta | — | Subcarpeta de este examen dentro de la salida. No puede ser absoluta ni usar `..`. |
| `path_images` | ruta | la del toml | Carpeta de las imágenes de las preguntas. `-p` la reemplaza. |
| `numero_temas` | entero | el del toml; si no, `1` | Cuántos temas generar. `-n` lo reemplaza. |
| `semilla` | entero | la del toml; si no, `42` | Semilla del sorteo: la misma da el mismo examen. `-s` la reemplaza. |
| `formato` | lista | la del toml; si no, `["html"]` | `html`, `pdf` o ambos. `-f` lo reemplaza. |
| `registro` | sección | — | `id`, `cuatrimestre` y `repetidas` (`evitar`, `avisar` o `permitir`) de este examen en el registro de exámenes tomados. Ver [Registro](#registro-de-exámenes-tomados-alucard-registro). |

#### `configuracion_examen`

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `mezclar_preguntas_dentro_seccion` | booleano | `true` | Cada tema ordena distinto las preguntas de una sección. |
| `mezclar_opciones_dentro_pregunta` | booleano | `true` | Cada tema ordena distinto las opciones. |
| `generar_clave_profesor` | booleano | `true` | Genera la clave de cada tema. |
| `sortear_preguntas` | booleano | `true` | Cada pool sortea qué preguntas entran; `false` toma las primeras que pasan los filtros. |
| `sortear_por_tema` | booleano | `false` | Cada tema toma otras preguntas de cada pool. Sin esto, los temas comparten las preguntas. |
| `lineas_justificacion` | entero, 0 a 60 | `0` | Renglones para justificar cada pregunta de selección múltiple. |
| `titulo_justificacion` | texto | el del idioma | Título de esos renglones. |
| `espacio_desarrollo` | `cero`, `chico`, `mediano`, `grande` o `pagina` | `mediano` | Espacio de las preguntas de desarrollo que no piden otro. Ver [Espacio de las preguntas de desarrollo](#espacio-de-las-preguntas-de-desarrollo). |
| `forzar_espacio_desarrollo` | booleano | `false` | `espacio_desarrollo` vale también para las preguntas que piden otro con su etiqueta. |
| `desarrollo_en_hoja_separada` | booleano | `false` | Todas las preguntas de desarrollo en su propia hoja. Manda sobre `espacio_desarrollo` y `forzar_espacio_desarrollo`. |
| `escala_plantuml` | número, hasta 4 | `1` | Tamaño de los diagramas PlantUML que no traen su `[escala]`. |
| `numerar_codigo` | booleano | `false` | Números de línea en todos los bloques de código, salvo los que dicen `// [sin-numerar]`. Ver [Números de línea en el código](#números-de-línea-en-el-código). |
| `debug_consignas` | `titulo` o `id` | el del toml | Muestra junto a cada pregunta cuál salió del banco. Ver [`debug_consignas`](#debug_consignas). |
| `debug_candidatas` | booleano | el del toml | Deja `candidatas.txt` con cada pregunta que cada pool podía elegir. Ver [`debug_candidatas`](#debug_candidatas). |
| `presentacion_consignas` | sección | ver abajo | Ver [`presentacion_consignas`](#presentacion_consignas). |

#### `presentacion_consignas`

Va en `configuracion_examen` y, con sólo las claves que cambian, en `presentacion` de un pool.

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `titulo` | booleano | `true` | El título del ejercicio. |
| `metadatos` | booleano | `false` | Tema, nivel de Bloom y minutos estimados. |
| `enunciado` | booleano | `true` | El enunciado. |
| `secciones_excluidas` | lista | `[]` | Secciones del enunciado a omitir, por su título o parte de él. |
| `funciones` | booleano | `false` | Tabla con las firmas de las funciones. |
| `cabecera` | booleano | `false` | El archivo `.h` del ejercicio. |
| `pistas` | entero | `0` | Cuántas pistas mostrar. |
| `espacio_respuesta` | booleano | `true` | Renglones para resolver. |
| `lineas` | entero, 0 a 200 | `20` | Cuántos renglones. Con `0`, ninguno, igual que `espacio_respuesta: false`. |
| `solucion_en_clave` | booleano | `true` | La solución de la cátedra en la clave. |

#### `secciones_examen`

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `nombre` | texto | **obligatoria** | Título de la sección. |
| `pools` | lista | **obligatoria** | De dónde salen sus preguntas. Ver [`pools`](#pools). |
| `instrucciones` | texto | — | Indicaciones debajo del título. |
| `layout` | `default`, `compact-2col`, `compact-3col` o `compact-4col` | `default` | Columnas de la sección. Sólo vale en HTML: el PDF va siempre a una columna. |

#### `pools`

Los filtros se combinan: una pregunta tiene que pasarlos todos.

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `banco` | texto | — | Sólo las de ese archivo. Compara el final de la ruta: `teoria.gift` vale para `unidad1/teoria.gift`. |
| `categoria` | texto | — | Esa categoría y sus subcategorías; `Math/*` también vale. |
| `categorias` | lista | `[]` | Cualquiera de esas categorías. Se ignora si hay `categoria`. |
| `tipos` | lista | `[]` | Cualquiera de esos tipos: `seleccion_multiple`, `verdadero_falso`, `respuesta_corta`, `ensayo`, `emparejamiento`, `numerica`, `desarrollo` o `consigna_practica`. |
| `etiquetas` | lista | `[]` | Las que tengan al menos una de esas etiquetas. |
| `preguntas_fijadas` | lista | `[]` | Ids de preguntas exactas. Con ella no se aplican los demás filtros ni el sorteo, y un id que no existe se saltea. |
| `cantidad` | entero | todas | Cuántas preguntas toma. |
| `accion_si_insuficiente` | `error`, `advertir` o `usar_todas` | `error` | Qué hacer si hay menos que `cantidad`: frenar, seguir con un aviso o seguir sin aviso. |
| `puntaje_fijo_por_pregunta` | número | el de la pregunta | Puntaje de cada pregunta del pool. |
| `minutos_min`, `minutos_max` | entero | — | Tiempo estimado de la consigna. Las preguntas sin tiempo estimado quedan afuera. |
| `presupuesto_minutos` | entero | — | Suma máxima de minutos de lo elegido. |
| `presentacion` | sección | la del examen | Cambia parte de [`presentacion_consignas`](#presentacion_consignas) para este pool. |
| `lineas_justificacion` | entero, 0 a 60 | la del examen | Renglones de justificación de este pool. |
| `sortear_por_tema` | booleano | la del examen | Cada tema toma otras preguntas de este pool. |

#### `repositorios_externos`

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `ruta` | ruta | **obligatoria** | Carpeta del repositorio. |
| `tipo` | `auto`, `preguntas` o `deckard` | `auto` | Qué contiene. `auto` es `deckard` si encuentra un `ejercicio.yaml`. |
| `nombre` | texto | nombre de la carpeta | Para la etiqueta `repo:<nombre>`. |
| `incluir_no_publicados` | booleano | `false` | Suma las consignas con `publicar: false`. |

#### `estilo`

Va en `estilo` de la definición y en `[estilo]` de `alucard.toml`. Más detalle en
[Estilo del examen](#estilo-del-examen-estilo).

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `fuente` | texto o lista | Liberation Sans (PDF), Arial (HTML) | Familias del texto; gana la primera instalada. |
| `fuente_codigo` | texto o lista | DejaVu Sans Mono (PDF), Courier New (HTML) | Familias del código. |
| `tamano` | número, 7 a 16 | `10` (PDF) | Puntos del texto. |
| `encabezado`, `pie` | texto o `izquierda`, `centro` y `derecha` | institución, materia y tema; examen y página | Franjas de cada página. Un texto solo va al centro. Admiten `{institucion}`, `{materia}`, `{examen}`, `{fecha}`, `{tema}`, `{pagina}` y `{paginas}`. |
| `logo` | ruta | — | PNG, JPG, GIF o SVG. |
| `logo_posicion` | `izquierda` o `derecha` | `izquierda` | Dónde va el logotipo. |
| `logo_alto_mm` | número, 4 a 30 | `12` | Alto del logotipo. |
| `alto_contraste` | booleano | `false` | Texto negro, sin grises, y bordes negros. |
| `tema_diagramas` | texto o tabla | `ink` (`high-contrast` con `alto_contraste`) | Theme de dibu para los diagramas: `ink`, `color`, `high-contrast`, `dark`, un archivo YAML/JSON o `{extends, colors, typography}`. |
| `nombre_en_hojas` | booleano | `true` | Renglón para el nombre en las páginas impares desde la 3 (PDF del examen). |

### Configuración del curso (`alucard.toml`)

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `definicion` | texto o lista | — | Los exámenes de `alucard generar` y `alucard validar` sin `-d`. |
| `input_banco` | texto o lista | — | Bancos o carpetas, si el YAML no los dice. |
| `output_dir` | ruta | — | Carpeta de salida, si el YAML no la dice. |
| `path_images` | ruta | — | Carpeta de imágenes, si el YAML no la dice. |
| `numero_temas` | entero | — | Temas, si el YAML no lo dice. |
| `semilla` | entero | — | Semilla, si el YAML no la dice. |
| `formato` | texto o lista | — | `html`, `pdf` o ambos, si el YAML no lo dice. |
| `debug_consignas` | `"titulo"`, `"id"`, `true` o `false` | `false` | Muestra junto a cada pregunta cuál salió del banco. `true` es `"titulo"`. |
| `debug_candidatas` | booleano | `false` | Deja `candidatas.txt` con cada pregunta que cada pool podía elegir. |

#### `[ortografia]`

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `servidor` | texto | API pública | Servidor de LanguageTool. |
| `idioma` | texto | `es-AR` | Idioma para LanguageTool. |
| `ignorar_reglas` | lista | `[]` | Reglas que no se informan. |
| `palabras` | lista | `[]` | Diccionario de la cátedra. |
| `diccionario` | ruta | — | Más palabras, una por renglón; `#` comenta. |

#### `[estilo]`

Las mismas claves que [`estilo`](#estilo). La definición manda clave por clave.

#### `[registro]`

| Clave | Tipo | Por omisión | Qué hace |
| :--- | :--- | :--- | :--- |
| `carpeta` | ruta | `registro/` junto al `alucard.toml` | Dónde van los exámenes registrados. |
| `cuatrimestre` | texto | el de la fecha del examen | Cuatrimestre de los exámenes que se registran, como `2026-2C`. |
| `repetidas` | `"evitar"`, `"avisar"` o `"permitir"` | `"evitar"` | Qué pasa con una pregunta que ya salió en el cuatrimestre. |

`registro:` de la definición manda clave por clave. Ver [Registro](#registro-de-exámenes-tomados-alucard-registro).

### `debug_consignas`

Para revisar qué salió en cada tema: el examen muestra, junto a «Pregunta N.», el título o el id de la
pregunta del banco. Vale para todas las preguntas, también las consignas prácticas con `titulo: false`.
Además, cada página del examen y de la clave lleva una marca de agua «Debug», gris y en diagonal, debajo
del texto; para que se vea, las preguntas y las instrucciones salen sin su fondo.

```toml
debug_consignas = "titulo"   # o "id"
```

Un examen lo cambia con `configuracion_examen.debug_consignas`, y `debug_consignas: null` lo apaga para
ese examen. La clave con `"id"` también lo muestra; con `"titulo"` no hace falta, porque ya lleva el
título. `alucard generar` avisa mientras esté activo, para que no se
imprima por error: el título de una pregunta puede dar pistas sobre la respuesta.

### `debug_candidatas`

Para revisar los pools: además de los temas, `alucard generar` deja en la carpeta de salida un
`candidatas.txt` con cada pregunta que cada pool podía elegir, en el orden de los bancos. Cada una va
como `banco:id`, con su comentario de etiquetas en el renglón de abajo, escrito como en un GIFT. Los
renglones con `#` dicen de qué sección y pool son, cuántas candidatas tenía y cuántas salieron.

```toml
debug_candidatas = true
```

```text
# Sección «B. Análisis de código», pool 1: Pool(cat:analisis/parcial_3_diagramas, tipos:[desarrollo], cant:1, pts:20.0)
# 10 candidatas, 4 salieron
analisis.gift:gift_51_analisis-p3-lista-diagrama-v1
// [tag, desarrollo-grande, analisis, parcial_3, listas, tda, memoria_dinamica, tema_a] [category, analisis/parcial_3_diagramas]
```

El banco es el nombre del archivo, o su ruta dentro de la carpeta de `input_banco`; el de una consigna
práctica es su carpeta. Un examen lo cambia con `configuracion_examen.debug_candidatas`. No toca el
examen, así que se puede dejar activo junto con `debug_consignas` o sin él.
