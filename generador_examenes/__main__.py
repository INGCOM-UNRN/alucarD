"""
Punto de entrada principal de la aplicación
"""
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional
import shutil

import typer
from yutani.cli import CONTEXTO, TyperConErrores, opcion_version
from yutani.textos import traducir

from generador_examenes import __version__, cli_commands
from generador_examenes.cli_errors import usage_error as _usage_error

# Contrato de línea de comandos del ecosistema (-h/--help, --version/-v, errores de datos como
# mensajes) y ayuda de Typer/Click en español, desde yutani (N-ECO-14). No usa crear_app porque
# el callback de la app raíz tiene las opciones del modo principal.
traducir()
app = TyperConErrores(context_settings=dict(CONTEXTO), add_completion=False, pretty_exceptions_enable=False)

# Último código de salida (0/1) reportado por el modo ejecutado, para que
# main() lo devuelva como valor de retorno. Los errores de uso de CLI
# (--definicion faltante, etc.) no pasan por acá: se reportan con
# SystemExit(2), que se propaga sin capturar hasta el llamador de main(),
# igual que hacía ArgumentParser.error() en la implementación previa.
_ultimo_codigo_salida = {"code": 0}


def inicializar_proyecto():
    """
    Crea estructura de directorios y archivos de ejemplo para un nuevo proyecto
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Crear directorios
    dirs_crear = ['templates', 'i18n', 'bancos', 'consignas', 'output']
    for dir_name in dirs_crear:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            logger.info(f"✓ Directorio creado: {dir_name}/")
        else:
            logger.info(f"  Directorio ya existe: {dir_name}/")
    
    # Copiar plantillas desde el paquete instalado
    import generador_examenes
    package_dir = Path(generador_examenes.__file__).parent
    
    # Copiar templates
    template_src = package_dir / 'templates'
    if template_src.exists():
        for template_file in template_src.glob('*.j2'):
            dest = Path('templates') / template_file.name
            if not dest.exists():
                shutil.copy(template_file, dest)
                logger.info(f"✓ Plantilla copiada: {template_file.name}")
            else:
                logger.info(f"  Plantilla ya existe: {template_file.name}")
    
    # Copiar archivos i18n
    i18n_src = package_dir / 'i18n'
    if i18n_src.exists():
        for i18n_file in i18n_src.glob('*.json'):
            dest = Path('i18n') / i18n_file.name
            if not dest.exists():
                shutil.copy(i18n_file, dest)
                logger.info(f"✓ Archivo i18n copiado: {i18n_file.name}")
            else:
                logger.info(f"  Archivo i18n ya existe: {i18n_file.name}")
    
    # Crear definicion_ejemplo.yaml
    definicion_ejemplo = Path('definicion_ejemplo.yaml')
    if not definicion_ejemplo.exists():
        contenido_definicion = """nombre_examen: "Examen de Ejemplo"
institucion: "Mi Institución"
materia: "Mi Materia"
fecha: "2024-01-01"
duracion_minutos: 60
instrucciones_generales: |
  Lee cuidadosamente cada pregunta antes de responder.
  Marca la respuesta correcta en cada caso.
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  incluir_metadata_debug: false
  # Renglones para justificar cada pregunta de selección múltiple (0: sin justificación);
  # cada pool puede cambiarlos con su propio `lineas_justificacion`.
  lineas_justificacion: 0
  # Espacio de las preguntas de desarrollo: cero, chico, mediano, grande o pagina. Una pregunta
  # pide otro con la etiqueta `desarrollo-grande`, `desarrollo-cero`, etc.
  espacio_desarrollo: mediano
  # true: ese espacio vale también para las preguntas que piden otro con su etiqueta.
  forzar_espacio_desarrollo: false
  # Cada pregunta de desarrollo en su propia hoja, con el resto de la hoja para responder.
  desarrollo_en_hoja_separada: false
  # Números de línea en todos los bloques de código; `// [numerar]` antes de un bloque lo hace para ese solo.
  numerar_codigo: false
  # titulo_justificacion: "Justificá tu respuesta"
  # Qué se muestra de cada consigna práctica (deckard); cada pool puede cambiar parte en `presentacion`.
  presentacion_consignas:
    titulo: true
    metadatos: false            # tema, nivel de Bloom y minutos estimados
    enunciado: true
    secciones_excluidas: ["Criterios de Aceptación"]   # secciones del enunciado que no van al papel
    funciones: true             # tabla con las firmas
    cabecera: false             # el archivo .h
    pistas: 0                   # cuántas pistas mostrar
    espacio_respuesta: true
    lineas: 20                  # renglones para resolver
    solucion_en_clave: true

# Carpeta de este examen dentro de la salida de alucard.toml; sirve para agrupar las partes de un
# examen compuesto (parcial1/teoria, parcial1/practica). Sin ella y con varias definiciones en el
# toml, el examen sale en una carpeta con el nombre de este archivo.
# subdirectorio: "parcial1/teoria"

# Consignas prácticas de deckard del proyecto (consignas/<tema>/<id>/ejercicio.yaml)
input_consignas: ["consignas"]

# Repositorios de la misma computadora que complementan los bancos del proyecto:
# carpetas de preguntas GIFT/XML o bancos de consignas deckard (tipo auto|preguntas|deckard).
# repositorios_externos:
#   - ruta: "~/dev/tools/enunciados"       # repositorio de enunciados (usa su banco/)
#     tipo: deckard
#     nombre: enunciados                   # etiqueta repo:enunciados para filtrar
#   - ruta: "~/catedra/preguntas"
#     tipo: preguntas

secciones_examen:
  - nombre: "Sección 1 - Preguntas de Ejemplo"
    instrucciones: "Selecciona la respuesta correcta"
    pools:
      - cantidad: 2               # el banco de ejemplo trae 2 de selección múltiple
        tipos: ["seleccion_multiple"]

  - nombre: "Sección 2 - Consigna Práctica"
    instrucciones: "Resolvé en C la consigna en el espacio indicado"
    pools:
      - tipos: ["consigna_practica"]
        cantidad: 1
        minutos_max: 30           # filtros opcionales por tiempo requerido
        # minutos_min: 10
        # presupuesto_minutos: 45 # suma máxima de minutos de las consignas elegidas
        presentacion:
          lineas: 25
"""
        definicion_ejemplo.write_text(contenido_definicion, encoding='utf-8')
        logger.info(f"✓ Archivo creado: definicion_ejemplo.yaml")
    else:
        logger.info(f"  Archivo ya existe: definicion_ejemplo.yaml")
    
    # Crear banco de ejemplo
    banco_ejemplo = Path('bancos') / 'banco_ejemplo.gift'
    if not banco_ejemplo.exists():
        contenido_banco = """// Banco de preguntas de ejemplo en formato GIFT
// Las etiquetas van en un comentario pegado a la pregunta, que Moodle ignora.

// [tag, geografia, facil]
::Pregunta 1:: ¿Cuál es la capital de Francia? {
=París
~Londres
~Berlín
~Madrid
}

::Pregunta 2:: Python es un lenguaje de programación {T}

::Pregunta 3:: ¿Qué significa HTML? {
=HyperText Markup Language
~High Tech Modern Language
~Home Tool Markup Language
}
"""
        banco_ejemplo.write_text(contenido_banco, encoding='utf-8')
        logger.info(f"✓ Banco de ejemplo creado: bancos/banco_ejemplo.gift")
    else:
        logger.info(f"  Banco ya existe: bancos/banco_ejemplo.gift")
    
    # Crear consigna práctica de ejemplo (formato deckard)
    consigna_ejemplo = Path('consignas') / 'sumar-pares'
    if not consigna_ejemplo.exists():
        consigna_ejemplo.mkdir(parents=True)
        (consigna_ejemplo / 'ejercicio.yaml').write_text("""id: sumar-pares
titulo: Suma de los pares de un arreglo
tema: arreglos
bloom: 3
minutos_estimados: 20
tags: [arreglos, lazos]
pistas:
  - Recorré el arreglo una sola vez acumulando en una variable.
  - Un número es par si el resto de dividirlo por 2 es 0.
funciones:
  - nombre: sumar_pares
    retorno: int
    parametros: const int arreglo[], size_t cantidad
    descripcion: Suma de los elementos pares del arreglo.
""", encoding='utf-8')
        (consigna_ejemplo / 'enunciado.md').write_text("""Escribir la función `sumar_pares`, que devuelve la suma de los elementos pares de un arreglo de enteros. Si el arreglo está vacío, devuelve 0.

### Ejemplos

- `{1, 2, 3, 4}` → `6`
- `{}` → `0`

### Criterios de Aceptación

- Compila sin advertencias con `-Wall -Wextra`.
""", encoding='utf-8')
        (consigna_ejemplo / 'solucion.c').write_text("""#include <stddef.h>

int sumar_pares(const int arreglo[], size_t cantidad)
{
    int suma = 0;
    for (size_t i = 0; i < cantidad; i++)
    {
        if (arreglo[i] % 2 == 0)
        {
            suma += arreglo[i];
        }
    }
    return suma;
}
""", encoding='utf-8')
        logger.info("✓ Consigna práctica de ejemplo creada: consignas/sumar-pares/")
    else:
        logger.info("  Consigna ya existe: consignas/sumar-pares/")

    # Configuración del curso: lo que se repite en cada corrida (la línea de comandos y la
    # definición mandan sobre esto).
    configuracion = Path('alucard.toml')
    if not configuracion.exists():
        configuracion.write_text('''# Configuración del curso para alucard (la línea de comandos y la definición YAML mandan).
# Los exámenes de `alucard generar` y `alucard validar`. Con varios, cada uno sale en
# output/<nombre del YAML>/ o en el `subdirectorio` que diga su definición.
definicion = ["definicion_ejemplo.yaml"]
input_banco = ["bancos/banco_ejemplo.gift"]
output_dir = "output"
numero_temas = 2
semilla = 2026
formato = ["html"]
# debug_consignas = "titulo"     # para revisar: muestra de qué pregunta salió cada una ("titulo" o "id")
# debug_candidatas = true        # para revisar los pools: candidatas.txt con cada pregunta que podía salir

[ortografia]
idioma = "es-AR"
# Palabras de la cátedra que LanguageTool no debe marcar.
palabras = ["malloc", "struct", "printf"]

# Tipografía, encabezado y pie, logotipo y contraste del examen y de la clave (descomentá lo que uses).
[estilo]
# fuente = ["Liberation Serif", "DejaVu Serif"]
# fuente_codigo = "DejaVu Sans Mono"
# tamano = 10.5
# encabezado = { izquierda = "{institucion}", derecha = "{materia} | Tema {tema}" }
# pie = { izquierda = "{examen}", derecha = "Página {pagina} de {paginas}" }
# logo = "logo.png"              # PNG, JPG, GIF o SVG, relativo a este archivo
# logo_posicion = "izquierda"    # o "derecha"
# logo_alto_mm = 12
alto_contraste = false           # true: texto negro, sin grises, y bordes negros
''', encoding='utf-8')
        logger.info("✓ Configuración del curso creada: alucard.toml")

    # Crear README
    readme = Path('README_PROYECTO.md')
    if not readme.exists():
        contenido_readme = """# Proyecto de Generación de Exámenes

Este proyecto usa **alucarD** (generador-examenes) para crear exámenes personalizados.

## Estructura de Directorios

```
.
├── bancos/              # Bancos de preguntas (GIFT o Moodle XML)
├── consignas/           # Consignas prácticas en formato deckard (<id>/ejercicio.yaml)
├── templates/           # Plantillas Jinja2 personalizables
├── i18n/                # Archivos de internacionalización
├── output/              # Exámenes generados
├── alucard.toml         # Definiciones, bancos, salida, temas y formato del curso
└── definicion_ejemplo.yaml  # Ejemplo de definición de examen
```

## Uso Rápido

### 1. Validar la definición

```bash
alucard validar
```

### 2. Generar exámenes

```bash
alucard generar
```

Las definiciones, los bancos y la carpeta de salida salen de `alucard.toml`. Para más de un examen,
sumá sus YAML a `definicion`. Las opciones mandan sobre el archivo: `alucard generar -n 3 -f pdf`.

## Siguientes Pasos

1. Edita `definicion_ejemplo.yaml` y `alucard.toml` con tu configuración
2. Agrega tus bancos de preguntas en `bancos/` y tus consignas prácticas en `consignas/`
   (o sumá repositorios de la computadora con `repositorios_externos` en la definición)
3. Personaliza las plantillas en `templates/` (opcional)
4. Genera tus exámenes con el comando anterior

## Documentación

Para más información, consulta la documentación oficial de alucarD.
"""
        readme.write_text(contenido_readme, encoding='utf-8')
        logger.info(f"✓ README creado: README_PROYECTO.md")
    else:
        logger.info(f"  README ya existe: README_PROYECTO.md")
    
    print("\n" + "="*60)
    print("✓ INICIALIZACIÓN COMPLETADA")
    print("="*60)
    print("\nArchivos y directorios creados:")
    print("  - templates/          (plantillas HTML)")
    print("  - i18n/               (archivos de idioma)")
    print("  - bancos/             (bancos de preguntas)")
    print("  - consignas/          (consignas prácticas deckard)")
    print("  - output/             (exámenes generados)")
    print("  - definicion_ejemplo.yaml")
    print("  - alucard.toml          (definiciones, bancos, salida, temas y formato del curso)")
    print("  - banco_ejemplo.gift")
    print("  - README_PROYECTO.md")
    print("\nPróximos pasos:")
    print("  1. Edita definicion_ejemplo.yaml con tu configuración")
    print("  2. Agrega tus bancos de preguntas en bancos/")
    print("  3. Validá: alucard validar")
    print("  4. Generá los temas: alucard generar -n 3")
    print()


@app.callback(invoke_without_command=True)
def _cli(
    ctx: typer.Context,
    version: bool = opcion_version("alucard", __version__),  # noqa: ARG001
    init: bool = typer.Option(False, "--init", hidden=True, help="Inicializar proyecto con archivos de ejemplo"),
    wizard: Optional[Path] = typer.Option(
        None, "--wizard", metavar="YAML", hidden=True,
        help="Asistente interactivo para crear/editar configuración de examen",
    ),
    category_tree: Optional[List[Path]] = typer.Option(
        None, "--category-tree", metavar="BANCO", hidden=True,
        help="Generar árbol HTML de categorías de uno o más bancos (archivos, o carpetas de preguntas o consignas deckard; con -d, también las fuentes de la definición)",
    ),
    definicion: Optional[List[Path]] = typer.Option(
        None, "-d", "--definicion",
        help="Definición YAML del examen; repetila para varios exámenes, cada uno en su subcarpeta "
             "(sin -d: la clave definicion de alucard.toml)",
    ),
    input_banco: Optional[List[Path]] = typer.Option(
        None, "-i", "--input-banco",
        help="Ruta(s) a los bancos de preguntas: archivos o carpetas, con sus subcarpetas "
             "(tiene prioridad sobre el YAML)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output-dir",
        help="Directorio de salida para los exámenes generados (tiene prioridad sobre el YAML y alucard.toml; si no está en ninguno: ./output)",
    ),
    path_images: Optional[Path] = typer.Option(
        None, "-p", "--path-images",
        help="Ruta al directorio de imágenes referenciadas en las preguntas (tiene prioridad sobre el YAML)",
    ),
    numero_temas: Optional[int] = typer.Option(
        None, "-n", "--numero-temas",
        help="Número de temas/versiones a generar (tiene prioridad sobre el YAML; si no está en ninguno: 1)",
    ),
    semilla: Optional[int] = typer.Option(
        None, "-s", "--semilla",
        help="Semilla pseudo-aleatoria para generación (tiene prioridad sobre el YAML; si no está en ninguno: 42)",
    ),
    formato: Optional[List[str]] = typer.Option(
        None, "-f", "--formato",
        help="Formato(s) de salida: html y/o pdf (tiene prioridad sobre el YAML; si no está en ninguno: html)",
    ),
    typst_template: Optional[Path] = typer.Option(
        None, "-t", "--template", "--typst-template",
        help="Ruta a una plantilla Typst personalizada (.typ / .typ.j2) para generación de PDF",
    ),
    spellcheck: bool = typer.Option(
        False, "--spellcheck", "--languagetool", hidden=True,
        help="Auditar ortografía y gramática de las preguntas del examen o banco usando LanguageTool",
    ),
    lt_server: Optional[str] = typer.Option(
        None, "--lt-server", help="URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública)",
    ),
    lt_username: Optional[str] = typer.Option(None, "--lt-username", help="Usuario / email de LanguageTool Premium"),
    lt_api_key: Optional[str] = typer.Option(None, "--lt-api-key", help="API Key / Token de LanguageTool Premium"),
    lt_premium: bool = typer.Option(False, "--lt-premium", help="Forzar uso de la API LanguageTool Premium"),
    lt_lang: str = typer.Option("es-AR", "--lt-lang", help="Código de idioma para LanguageTool."),
    lt_ignore_rules: Optional[str] = typer.Option(
        None, "--lt-ignore-rules", help="Reglas de LanguageTool a ignorar separadas por comas",
    ),
    lt_ignore_words: Optional[str] = typer.Option(
        None, "--lt-ignore-words", help="Palabras personalizadas a ignorar separadas por comas",
    ),
    lt_fix: bool = typer.Option(False, "--lt-fix", help="Aplica correcciones ortográficas automáticas"),
    output_md: Optional[Path] = typer.Option(
        None, "--md", "--output-md", help="Genera reporte de auditoría en formato Markdown",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emite salida estructurada en formato JSON"),
    validate: bool = typer.Option(False, "--validate", hidden=True, help="Validar la definición sin generar archivos"),
    debug: bool = typer.Option(False, "--debug", help="Activar modo debug con logging detallado"),
    omr: bool = typer.Option(
        False, "--omr", help="Generar hoja de respuestas OMR de lectura óptica y descriptor JSON",
    ),
    accessible: bool = typer.Option(
        False, "--accessible", "--large-text",
        help="Generar versión con letra grande y contraste adaptado para accesibilidad",
    ),
    bundle_print: bool = typer.Option(
        False, "--bundle-print", "--empaquetar-imprenta",
        help="Empaquetar y concatenar los PDFs de todos los temas en un único archivo para imprenta",
    ),
    audit_typography: bool = typer.Option(
        False, "--audit-typography",
        help="Auditar calidad tipográfica y líneas huérfanas en bloques de código de preguntas",
    ),
    registrar: bool = typer.Option(
        False, "--registrar",
        help="Anotar el examen generado en el registro de exámenes tomados (como `alucard registro guardar`)",
    ),
    cuatrimestre: Optional[str] = typer.Option(
        None, "--cuatrimestre",
        help="Cuatrimestre del registro, como 2026-2C (por omisión, el de registro:, [registro] o la fecha del examen)",
    ),
    registro_id: Optional[str] = typer.Option(
        None, "--registro-id", help="Id del examen en el registro (por omisión, el nombre del archivo de la definición)",
    ),
    forzar: bool = typer.Option(
        False, "--forzar", help="Reemplazar un registro con resultados aunque cambien las preguntas (los descarta)",
    ),
    vigilar: bool = typer.Option(
        False, "--watch", "-w",
        help="Volver a generar cada vez que cambia la definición, un banco, una consigna o una imagen (Ctrl+C termina)",
    ),
    show_completion: bool = typer.Option(
        False, "--show-completion",
        help="Show completion for the current shell, to copy it or customize the installation.",
    ),
    install_completion: bool = typer.Option(
        False, "--install-completion", help="Install completion for the current shell.",
    ),
) -> None:
    """Generador de exámenes basado en plantillas YAML y bancos Moodle/GIFT."""
    if ctx.invoked_subcommand is not None:
        # Se invocó un subcomando explícito (p. ej. `doctor`); no ejecutar
        # el modo principal.
        return
    valores = {k: v for k, v in locals().items() if k in _PARAMETROS}
    # Las opciones que en realidad son comandos siguen andando, con aviso (QoL: CLI coherente).
    for opcion, comando in _OPCIONES_COMANDO.items():
        if valores.get(opcion):
            print(f"Aviso: {comando[0]} pasó a ser un comando: usá «alucard {comando[1]}». "
                  "La opción sigue andando por ahora.", file=sys.stderr)
    _ejecutar(valores)


# Opciones del modo raíz que son comandos: opción → (cómo se escribía, comando nuevo).
_OPCIONES_COMANDO = {
    "init": ("--init", "iniciar"),
    "wizard": ("--wizard", "asistente YAML"),
    "category_tree": ("--category-tree", "categorias BANCO…"),
    "spellcheck": ("--spellcheck", "ortografia -d YAML"),
    "validate": ("--validate", "validar -d YAML"),
}


def _ejecutar(valores: dict) -> None:
    """El modo principal con los valores de las opciones (los que falten toman su valor por defecto)."""
    args = SimpleNamespace(**{**_DEFECTOS, **valores})

    # -d se repite en generar y validar; los demás modos trabajan con una sola definición.
    d = args.definicion
    args.definiciones = list(d) if isinstance(d, (list, tuple)) else [d] if d else []
    args.definicion = args.definiciones[0] if args.definiciones else None
    if len(args.definiciones) > 1 and (getattr(args, "spellcheck", False) or args.category_tree):
        _usage_error("este comando acepta una sola definición (-d)")

    if args.formato:
        for fmt in args.formato:
            if fmt not in ("html", "pdf"):
                _usage_error(f"argumento -f/--formato: valor inválido: '{fmt}' (elegir entre 'html', 'pdf')")

    if getattr(args, 'show_completion', False) or getattr(args, 'install_completion', False):
        _ultimo_codigo_salida["code"] = cli_commands.ejecutar_completion(args)
        return

    # Configurar logging
    from generador_examenes.config.logging_config import setup_logging
    setup_logging(debug=args.debug)

    import logging
    logger = logging.getLogger(__name__)

    if args.init:
        codigo = cli_commands.ejecutar_init(args, logger)
    elif args.wizard is not None:
        codigo = cli_commands.ejecutar_wizard(args, logger)
    elif getattr(args, 'spellcheck', False):
        codigo = cli_commands.ejecutar_spellcheck(args, logger)
    elif args.category_tree:
        codigo = cli_commands.ejecutar_category_tree(args, logger)
    else:
        codigo = cli_commands.ejecutar_generacion(args, logger)

    _ultimo_codigo_salida["code"] = codigo


_PARAMETROS = [n for n in inspect.signature(_cli).parameters if n not in ("ctx", "version")]
_DEFECTOS = {
    n: (p.default.default if hasattr(p.default, "default") else p.default)
    for n, p in inspect.signature(_cli).parameters.items() if n in _PARAMETROS
}
# Las listas de Typer llegan como None cuando no se pasan.
_DEFECTOS = {n: (None if v is ... else v) for n, v in _DEFECTOS.items()}

_OPCIONES_LT = [n for n in _PARAMETROS if n.startswith("lt_")]
_OPCIONES_GENERAR = [
    "definicion", "input_banco", "output_dir", "path_images", "numero_temas", "semilla", "formato",
    "typst_template", "json_output", "debug", "omr", "accessible", "bundle_print", "audit_typography",
    "registrar", "cuatrimestre", "registro_id", "forzar", "vigilar",
]


def _comando_de_opciones(nombre: str, opciones: List[str], fijos: dict, ayuda: str, destino=None) -> None:
    """Registra `alucard <nombre>` con las mismas opciones (nombre, tipo, ayuda) que el modo raíz."""
    firma = inspect.signature(_cli)
    parametros = [firma.parameters[n] for n in opciones]

    def comando(**valores):
        _ejecutar({**valores, **fijos})

    comando.__signature__ = firma.replace(parameters=parametros)  # type: ignore[attr-defined]
    comando.__annotations__ = {n: _cli.__annotations__[n] for n in opciones if n in _cli.__annotations__}
    comando.__doc__ = ayuda
    comando.__name__ = f"_comando_{nombre}"
    (destino or app).command(nombre)(comando)


# usar_curso: sólo estos comandos toman las definiciones del alucard.toml; `alucard` a secas no genera.
_comando_de_opciones("generar", _OPCIONES_GENERAR, {"usar_curso": True},
                     "Genera los temas de una o más definiciones YAML (HTML y/o PDF, claves, OMR). "
                     "Sin -d, las de alucard.toml.")
_comando_de_opciones("validar", ["definicion", "input_banco", "json_output", "debug"],
                     {"validate": True, "usar_curso": True},
                     "Valida una o más definiciones y sus pools sin generar archivos. Sin -d, las de alucard.toml.")
registro_app = typer.Typer(context_settings=dict(CONTEXTO), add_completion=False, no_args_is_help=True,
                           help="Registro de exámenes tomados: preguntas usadas en el cuatrimestre y calidad de cada pregunta.")
app.add_typer(registro_app, name="registro")
_comando_de_opciones("guardar", ["definicion", "input_banco", "numero_temas", "semilla", "cuatrimestre", "registro_id",
                                 "forzar", "json_output", "debug"],
                     {"solo_registrar": True, "usar_curso": True},
                     "Guarda en el registro el examen tal como lo arma `generar` con las mismas opciones (preguntas, "
                     "orden y opciones de cada tema), sin generar archivos. Volver a guardarlo lo reemplaza.",
                     destino=registro_app)
_comando_de_opciones("ortografia", ["definicion", "input_banco", *_OPCIONES_LT, "output_md", "json_output", "debug"],
                     {"spellcheck": True},
                     "Revisa ortografía y gramática de las preguntas con LanguageTool.")


@app.command("iniciar")
def _iniciar() -> None:
    """Crea un proyecto de ejemplo en la carpeta actual (definición, banco y plantillas)."""
    _ejecutar({"init": True})


@app.command("asistente")
def _asistente(yaml: Path = typer.Argument(..., help="Definición YAML a crear o editar.")) -> None:
    """Asistente interactivo para crear o editar la definición de un examen."""
    _ejecutar({"wizard": yaml})


@app.command("categorias")
def _categorias(
    bancos: Optional[List[Path]] = typer.Argument(
        None, help="Bancos (archivos, o carpetas de preguntas o consignas deckard); sin ellos, los de la definición."),
    definicion: Optional[Path] = typer.Option(None, "-d", "--definicion",
                                              help="Suma las fuentes de la definición (y con --resumen, revisa sus pools)."),
    resumen: bool = typer.Option(False, "--resumen",
                                 help="Tabla en la terminal: preguntas por categoría y tipo, y si cada pool tiene las que pide."),
) -> None:
    """Árbol HTML de las categorías de uno o más bancos; con --resumen, el inventario en la terminal."""
    if not bancos:
        if definicion is None:
            _usage_error("indicá uno o más bancos, o una definición con -d")
            return
        bancos = cli_commands.bancos_de_definicion(definicion)
    if resumen:
        _ultimo_codigo_salida["code"] = cli_commands.ejecutar_inventario(bancos, definicion)
        return
    _ejecutar({"category_tree": bancos, "definicion": definicion})


def _cargar_definicion(definicion: Optional[Path], bancos: List[Path], titulo: Optional[str], materia: str,
                       institucion: str, consignas: Optional[List[Path]] = None,
                       repositorios: Optional[List[Path]] = None):
    """La definición del YAML o, sin él, una con todas las preguntas de los bancos, consignas y repositorios."""
    import yaml

    from generador_examenes.core.balance import definicion_implicita
    from generador_examenes.core.models import DefinicionExamen

    if definicion is None:
        if not bancos and not consignas and not repositorios:
            _usage_error("Se requiere -d/--definicion, o al menos un -i/--input-banco, --consignas o --repositorio")
        datos = definicion_implicita(bancos, titulo, materia, institucion, consignas or [], repositorios or [])
    else:
        datos = yaml.safe_load(definicion.read_text(encoding="utf-8"))
        if consignas:
            datos["input_consignas"] = [*(datos.get("input_consignas") or []), *map(str, consignas)]
        if repositorios:
            datos["repositorios_externos"] = [*(datos.get("repositorios_externos") or []),
                                              *({"ruta": str(r)} for r in repositorios)]
    return DefinicionExamen(**datos), datos


_AYUDA_CONSIGNAS = "Carpeta de consignas prácticas deckard (se suma a input_consignas). Repetible."
_AYUDA_REPOSITORIO = ("Repositorio externo de la computadora: carpeta de bancos GIFT/XML o de consignas deckard "
                      "(se suma a repositorios_externos, tipo auto). Repetible.")


@app.command("ver")
def _ver(
    banco: Path = typer.Argument(..., exists=True, dir_okay=False, help="Banco GIFT o Moodle XML."),
    pregunta: Optional[str] = typer.Option(None, "--pregunta", "-q",
                                           help="Título (o parte) o id de la pregunta; sin esto, todo el banco."),
    linea: Optional[int] = typer.Option(None, "--linea", "-l", min=1,
                                        help="GIFT: la pregunta que contiene esa línea del archivo."),
    formato: str = typer.Option("html", "-f", "--formato", help="html o pdf."),
    output_dir: Path = typer.Option(Path("output/vista_previa"), "-o", "--output-dir", help="Dónde dejarla."),
    path_images: Optional[Path] = typer.Option(None, "-p", "--path-images", help="Imágenes de las preguntas."),
    clave: bool = typer.Option(False, "--clave", help="También la versión con las respuestas correctas."),
    abrir: bool = typer.Option(True, "--abrir/--no-abrir", help="Abrirla con el visor del sistema."),
    vigilar_cambios: bool = typer.Option(False, "--watch", "-w",
                                         help="Volver a armarla cada vez que se guarda el banco (Ctrl+C termina)."),
) -> None:
    """Vista previa de una pregunta (o de un banco) como sale en el examen, con sus diagramas."""
    import logging

    from generador_examenes.config.logging_config import setup_logging

    if formato not in ("html", "pdf"):
        _usage_error(f"argumento -f/--formato: valor inválido: '{formato}' (elegir entre 'html', 'pdf')")
    if pregunta and linea:
        _usage_error("--pregunta y --linea eligen la pregunta de dos formas: usá una sola")
    setup_logging(debug=False)
    logger = logging.getLogger("alucard.ver")

    def armar(abrir_ahora: bool = abrir) -> int:
        return cli_commands.ejecutar_vista_previa(banco, pregunta, linea, formato, output_dir, path_images,
                                                  clave, abrir_ahora, logger)

    if not vigilar_cambios:
        _ultimo_codigo_salida["code"] = armar()
        return
    from generador_examenes.core.vigilancia import vigilar
    primera = [True]

    def armar_una_vez_abierta() -> int:
        # Se abre la primera vez; después se recarga en el visor que ya está abierto.
        codigo = armar(abrir and primera[0])
        primera[0] = False
        return codigo

    _ultimo_codigo_salida["code"] = vigilar(lambda: [banco, *([path_images] if path_images else [])],
                                            armar_una_vez_abierta, excluir=[output_dir])


@app.command("build")
def _build(
    input_banco: Optional[List[Path]] = typer.Option(None, "-i", "--input-banco", exists=True,
                                                     help="Banco(s) de preguntas: Moodle XML (el de idkfa), GIFT… o "
                                                          "carpetas, con sus subcarpetas. "
                                                          "Reemplaza al input_banco de la definición."),
    consignas: Optional[List[Path]] = typer.Option(None, "--consignas", exists=True, file_okay=False, help=_AYUDA_CONSIGNAS),
    repositorio: Optional[List[Path]] = typer.Option(None, "--repositorio", exists=True, help=_AYUDA_REPOSITORIO),
    definicion: Optional[Path] = typer.Option(None, "-d", "--definicion", exists=True, dir_okay=False,
                                              help="Definición YAML; sin ella, una sección con todas las preguntas."),
    numero_temas: int = typer.Option(1, "-n", "--numero-temas", min=1, help="Temas (variantes) a generar."),
    semilla: int = typer.Option(42, "-s", "--semilla", help="Semilla del primer tema (los siguientes, +1, +2…)."),
    formato: List[str] = typer.Option(["pdf"], "-f", "--formato", help="pdf y/o html."),
    output_dir: Path = typer.Option(Path("output"), "-o", "--output-dir", help="Directorio de salida."),
    titulo: Optional[str] = typer.Option(None, "--titulo", help="Sin YAML: título del examen (por omisión, el nombre del banco)."),
    materia: str = typer.Option("", "--materia", help="Sin YAML: materia."),
    institucion: str = typer.Option("", "--institucion", help="Sin YAML: institución."),
    umbral: float = typer.Option(0.30, "--umbral", min=0.0, max=1.0, help="Frecuencia máxima de una letra correcta."),
) -> None:
    """Genera los temas en PDF desde un banco (sin YAML basta -i, --consignas o --repositorio) y audita el balance de claves.

    Cada tema reparte la opción correcta entre las letras (la menos usada, sin rachas); al terminar se
    muestra en qué letra quedó la correcta en cada tema. Sale con 1 si la generación falla o si alguna
    letra supera el umbral.
    """
    import logging
    import tempfile

    import yaml

    from generador_examenes.config.logging_config import setup_logging
    from generador_examenes.core.balance import armar_temas, auditar_balance, texto_del_informe

    for fmt in formato:
        if fmt not in ("html", "pdf"):
            _usage_error(f"argumento -f/--formato: valor inválido: '{fmt}' (elegir entre 'html', 'pdf')")
    setup_logging(debug=False)
    definicion_modelo, datos = _cargar_definicion(definicion, input_banco or [], titulo, materia, institucion,
                                                  consignas, repositorio)
    with tempfile.TemporaryDirectory(prefix="alucard-build-") as tmp:
        ruta = definicion
        if ruta is None or consignas or repositorio:
            ruta = Path(tmp) / "definicion.yaml"
            ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
        args = SimpleNamespace(definicion=ruta, input_banco=input_banco, output_dir=output_dir, path_images=None,
                               numero_temas=numero_temas, semilla=semilla, formato=formato, typst_template=None,
                               validate=False, debug=False, json_output=False, omr=False, accessible=False,
                               bundle_print=False, audit_typography=False)
        codigo = cli_commands.generar_examen(args, logging.getLogger("alucard.build"))
    if codigo != 0:
        _ultimo_codigo_salida["code"] = codigo
        return
    bancos = input_banco or (cli_commands.bancos_de_definicion(definicion) if definicion else None)
    reporte = auditar_balance(armar_temas(definicion_modelo, bancos, numero_temas, semilla), umbral)
    print("\n" + texto_del_informe(reporte))
    _ultimo_codigo_salida["code"] = 0 if reporte["ok"] else 1


@app.command("balance-check")
def _balance_check(
    input_banco: Optional[List[Path]] = typer.Option(None, "-i", "--input-banco", exists=True,
                                                     help="Banco(s) o carpetas de bancos; reemplaza al input_banco de la definición."),
    consignas: Optional[List[Path]] = typer.Option(None, "--consignas", exists=True, file_okay=False, help=_AYUDA_CONSIGNAS),
    repositorio: Optional[List[Path]] = typer.Option(None, "--repositorio", exists=True, help=_AYUDA_REPOSITORIO),
    definicion: Optional[Path] = typer.Option(None, "-d", "--definicion", exists=True, dir_okay=False,
                                              help="Definición YAML; sin ella, todas las preguntas."),
    numero_temas: int = typer.Option(4, "-n", "--numero-temas", min=1, help="Temas a auditar."),
    semilla: int = typer.Option(42, "-s", "--semilla", help="Semilla del primer tema (la misma que en la generación)."),
    umbral: float = typer.Option(0.30, "--umbral", min=0.0, max=1.0, help="Frecuencia máxima de una letra correcta."),
    json_output: bool = typer.Option(False, "--json", help="Emitir el informe como JSON."),
) -> None:
    """Audita que ninguna letra sea la correcta en más del 30 % de los casos en las variantes generadas.

    Arma los temas con las mismas semillas que `alucard` (sin renderizarlos) y cuenta en qué letra quedó la
    opción correcta de cada pregunta de selección múltiple. Sale con 1 si alguna supera el umbral (con
    preguntas de 2 o 3 opciones el umbral efectivo sube a lo que el banco permite, y se informa).
    """
    import json

    from generador_examenes.config.logging_config import setup_logging
    from generador_examenes.core.balance import armar_temas, auditar_balance, texto_del_informe

    setup_logging(debug=False)
    definicion_modelo, _ = _cargar_definicion(definicion, input_banco or [], None, "", "", consignas, repositorio)
    bancos = input_banco or (cli_commands.bancos_de_definicion(definicion) if definicion else None)
    reporte = auditar_balance(armar_temas(definicion_modelo, bancos, numero_temas, semilla), umbral)
    print(json.dumps(reporte, ensure_ascii=False, indent=2) if json_output else texto_del_informe(reporte))
    _ultimo_codigo_salida["code"] = 0 if reporte["ok"] else 1


@app.command("lint-gift")
def _lint_gift(
    archivos: List[Path] = typer.Argument(..., exists=True,
                                          help="Bancos de preguntas GIFT a revisar, o carpetas que los contengan."),
    fix: bool = typer.Option(False, "--fix", help="Corrige problemas comunes en el lugar."),
    compilar: bool = typer.Option(False, "--compilar",
                                  help="Compila con gcc -fsyntax-only los bloques de C que son programas completos."),
) -> None:
    """Revisa (y con --fix corrige) bancos GIFT: formato, compatibilidad con Moodle, bloques estructura
    y, con --compilar, el código C."""
    from generador_examenes.gift_linter import revisar_archivos

    _ultimo_codigo_salida["code"] = revisar_archivos(archivos, fix=fix, compilar=compilar)


@app.command("sintetizar")
def _sintetizar(
    plantilla: Optional[str] = typer.Argument(None, help="Plantilla a usar; sin ella, lista las disponibles."),
    cantidad: int = typer.Option(5, "-c", "--cantidad", min=1, help="Cantidad de preguntas a sintetizar."),
    opciones: int = typer.Option(4, "--opciones", min=2, max=8,
                                 help="Opciones de cada pregunta, la correcta incluida (2 a 8)."),
    formato_banco: str = typer.Option("gift", "-f", "--formato", help="Formato del banco: gift o xml."),
    output_dir: Path = typer.Option(Path("output"), "-o", "--output-dir", help="Directorio de salida."),
    semilla: int = typer.Option(42, "-s", "--semilla", help="Semilla de los parámetros al azar."),
    json_output: bool = typer.Option(False, "--json", help="Emitir el resultado como JSON."),
    debug: bool = typer.Option(False, "--debug", help="Activar modo debug con logging detallado."),
    muestra: bool = typer.Option(False, "--muestra",
                                 help="Mostrar una pregunta de ejemplo (con la correcta marcada) sin escribir el banco."),
    voight: bool = typer.Option(True, "--voight/--sin-voight",
                                help="Formatear el banco con voight: fix code-indent, code-chars --to-fullwidth y format."),
) -> None:
    """Genera un banco de preguntas de C con daedalus: cada respuesta se verifica con gcc.

    Las de traza se compilan y ejecutan; las de comportamiento indefinido (punteros salvajes y
    colgantes) se verifican con los avisos de gcc -fanalyzer; las de fugas cuentan la memoria que queda
    sin liberar. Sin PLANTILLA, lista las disponibles.
    """
    import logging

    from generador_examenes.config.logging_config import setup_logging

    if formato_banco not in ("gift", "xml"):
        _usage_error(f"argumento -f/--formato: valor inválido: '{formato_banco}' (elegir entre 'gift', 'xml')")
    if plantilla is None:
        _ultimo_codigo_salida["code"] = cli_commands.listar_sintetizadores_disponibles()
        return
    setup_logging(debug=debug)
    args = SimpleNamespace(sintetizar=plantilla, cantidad=cantidad, opciones=opciones, formato_banco=formato_banco,
                           output_dir=output_dir, semilla=semilla, json_output=json_output, debug=debug,
                           muestra=muestra, voight=voight)
    _ultimo_codigo_salida["code"] = cli_commands.ejecutar_sintetizar(args, logging.getLogger("alucard.sintetizar"))


@app.command("repartir")
def _repartir(
    temas: Path = typer.Argument(..., exists=True, file_okay=False, help="Carpeta con los examen_tema_*.pdf de `alucard build`."),
    padron: Path = typer.Option(..., "--padron", exists=True, dir_okay=False, help="Usuarios de GitHub, uno por línea."),
    salida: Path = typer.Option(Path("repartidos"), "-o", "--salida", help="Carpeta con una subcarpeta por usuario."),
    semilla: int = typer.Option(42, "-s", "--semilla", help="Semilla del sorteo: la misma da el mismo reparto."),
) -> None:
    """Reparte los temas en PDF entre los estudiantes, para entregarlos cifrados con uatu.

    Deja `<salida>/<usuario>/examen.pdf`, lo que espera `uatu-admin paquetes sellar`, y al lado
    `<salida>.asignacion.csv` con el tema de cada uno. Los temas quedan en partes iguales y las
    claves de corrección no se copian. Sale con 1 si el padrón o la salida no sirven.
    """
    from collections import Counter

    from generador_examenes.core.reparto import RepartoError, repartir

    try:
        reparto = repartir(temas, padron, salida, semilla)
    except RepartoError as error:
        print(f"Error: {error}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    for tema, cantidad in sorted(Counter(reparto.asignacion.values()).items()):
        print(f"{tema}: {cantidad} estudiante(s)")
    print(f"✓ {len(reparto.asignacion)} examen(es) en {salida}/; asignación en {reparto.registro}")
    print("Guardá la asignación: corregís con ella. No la subas a los repositorios del examen.")
    _ultimo_codigo_salida["code"] = 0


@app.command("diagramas-md")
def _diagramas_md(
    archivos: List[Path] = typer.Argument(..., exists=True, help="Archivos Markdown (o directorios) con bloques ```estructura."),
    verificar: bool = typer.Option(False, "--verificar", help="No escribe: falla si algún SVG falta, cambió o sobra."),
    color: bool = typer.Option(False, "--color", help="Paleta de color de statics (por omisión, ahorro de tinta)."),
) -> None:
    """Dibuja los bloques ```estructura de los Markdown como SVG versionados, para publicarlos sin alucarD.

    Cada bloque de `<dir>/*.md` queda en `<dir>/diagramas/estructura-<hash>.svg` (el hash es del
    contenido del bloque) y se borran los SVG que ya no usa ningún bloque. Pensado como hook de
    pre-commit (`alucard-diagramas`): si escribe o borra algo, termina con código 1 para que se
    agreguen al commit. Así `deckard export myst` publica el enunciado con su imagen.
    """
    from generador_examenes.diagramas import sincronizar_svgs

    directorios = sorted({(a if a.is_dir() else a.parent).resolve() for a in archivos
                          if a.is_dir() or a.suffix.lower() == ".md"})
    cambios = errores = 0
    for directorio in directorios:
        res = sincronizar_svgs(directorio, tinta=not color, escribir=not verificar)
        for ruta in res.escritos:
            print(f"{'Desactualizado' if verificar else '✓ Escrito'}: {ruta}")
        for ruta in res.borrados:
            print(f"{'Sobra' if verificar else '✓ Borrado'}: {ruta}")
        for error in res.errores:
            print(f"Error: {error}", file=sys.stderr)
        cambios += len(res.escritos) + len(res.borrados)
        errores += len(res.errores)
    if cambios and not verificar:
        print("Se actualizaron los SVG de los diagramas: agregalos al commit (git add).", file=sys.stderr)
    _ultimo_codigo_salida["code"] = 1 if cambios or errores else 0


@app.command("diagrama")
def _diagrama(
    archivo: Path = typer.Argument(..., exists=True, dir_okay=False,
                                   help="Bloque, lista de bloques o documento de statics, en YAML o JSON."),
    output_dir: Path = typer.Option(Path("output"), "-o", "--output-dir", help="Directorio de los SVG."),
    color: bool = typer.Option(False, "--color", help="Paleta de color de statics (por omisión, ahorro de tinta)."),
) -> None:
    """Dibuja estructuras de datos y diagramas de algoritmos como SVG, con el formato de bloques de statics.

    Escribe un SVG por bloque (`<id>.svg` o `<archivo>_<n>.svg`). Los bloques de statics que no son
    diagramas (texto, recortables) se saltean con un aviso. En las preguntas, el
    mismo bloque va en un bloque de código ```estructura.
    """
    from generador_examenes.diagramas import TIPOS, ErrorDiagrama, leer_bloques, renderizar

    try:
        bloques = leer_bloques(archivo.read_text(encoding="utf-8"))
    except ErrorDiagrama as e:
        _usage_error(f"{archivo}: {e}")
    output_dir.mkdir(parents=True, exist_ok=True)
    escritos = 0
    for n, bloque in enumerate(bloques, 1):
        if bloque.get("type") not in TIPOS:
            print(f"Aviso: bloque {n} ({bloque.get('type')!r}) no es una estructura; se saltea.", file=sys.stderr)
            continue
        destino = output_dir / f"{bloque.get('id') or f'{archivo.stem}_{n}'}.svg"
        try:
            destino.write_text(renderizar(bloque, tinta=not color), encoding="utf-8")
        except ErrorDiagrama as e:
            print(f"Error: bloque {n}: {e}", file=sys.stderr)
            continue
        print(f"✓ {destino}")
        escritos += 1
    _ultimo_codigo_salida["code"] = 0 if escritos else 1


_AYUDA_CARPETA_REGISTRO = "Carpeta del registro (por omisión, la de [registro] de alucard.toml o ./registro)."


def _carpeta_registro(carpeta: Optional[Path]) -> Path:
    if carpeta is not None:
        return carpeta
    from generador_examenes.config import proyecto

    curso = proyecto.cargar(Path.cwd())
    if curso.registro.get("carpeta"):
        return Path(curso.registro["carpeta"])
    return (curso.ruta.parent if curso.ruta else Path.cwd()) / "registro"


def _registros(carpeta: Optional[Path], cuatrimestre: Optional[str]):
    from generador_examenes.core import registro

    ruta = _carpeta_registro(carpeta)
    registros, fallas = registro.todos(ruta, cuatrimestre)
    for falla in fallas:
        print(f"Aviso: {falla}", file=sys.stderr)
    return ruta, registros


@registro_app.command("listar")
def _registro_listar(
    cuatrimestre: Optional[str] = typer.Option(None, "--cuatrimestre", help="Sólo los de este cuatrimestre (como 2026-2C)."),
    carpeta: Optional[Path] = typer.Option(None, "--carpeta", help=_AYUDA_CARPETA_REGISTRO),
    json_output: bool = typer.Option(False, "--json", help="La lista como JSON."),
) -> None:
    """Los exámenes registrados: cuatrimestre, fecha, temas, preguntas y si tienen resultados."""
    import json

    ruta, registros = _registros(carpeta, cuatrimestre)
    filas = [{"cuatrimestre": r["cuatrimestre"], "id": r["id"], "examen": r["examen"]["nombre"],
              "fecha": r["examen"].get("fecha"), "revision": r["revision"], "temas": len(r["temas"]),
              "preguntas": len(r["preguntas"]),
              "estudiantes": len((r.get("resultados") or {}).get("estudiantes") or [])} for r in registros]
    if json_output:
        print(json.dumps(filas, indent=2, ensure_ascii=False))
        return
    if not filas:
        print(f"No hay exámenes registrados en {ruta}.")
        return
    print(f"{'Cuatrimestre':<13} {'Id':<22} {'Fecha':<11} {'Rev':>3} {'Temas':>5} {'Preg.':>5} {'Result.':>7}  Examen")
    for f in filas:
        print(f"{f['cuatrimestre']:<13} {f['id']:<22} {f['fecha'] or '—':<11} {f['revision']:>3} {f['temas']:>5} "
              f"{f['preguntas']:>5} {f['estudiantes'] or '—':>7}  {f['examen']}")


@registro_app.command("usadas")
def _registro_usadas(
    cuatrimestre: Optional[str] = typer.Option(None, "--cuatrimestre", help="Sólo las de este cuatrimestre."),
    carpeta: Optional[Path] = typer.Option(None, "--carpeta", help=_AYUDA_CARPETA_REGISTRO),
    json_output: bool = typer.Option(False, "--json", help="La lista como JSON."),
) -> None:
    """Cada pregunta registrada con los exámenes en que salió (una pregunta es la misma por su contenido)."""
    import json

    _, registros = _registros(carpeta, cuatrimestre)
    por_huella: dict = {}
    for r in registros:
        for qid, p in r["preguntas"].items():
            fila = por_huella.setdefault(p["huella"], {"huella": p["huella"], "ids": [], "nombre": p["nombre"],
                                                         "categoria": p["categoria"], "examenes": []})
            if qid not in fila["ids"]:
                fila["ids"].append(qid)
            fila["examenes"].append({"cuatrimestre": r["cuatrimestre"], "id": r["id"], "fecha": r["examen"].get("fecha")})
    filas = sorted(por_huella.values(), key=lambda f: (-len(f["examenes"]), f["categoria"], f["nombre"]))
    if json_output:
        print(json.dumps(filas, indent=2, ensure_ascii=False))
        return
    for f in filas:
        donde = ", ".join(f"{e['cuatrimestre']}/{e['id']}" for e in f["examenes"])
        marca = "!" if len({e["cuatrimestre"] for e in f["examenes"]}) < len(f["examenes"]) else " "
        print(f"{marca} {len(f['examenes']):>2}  {f['categoria']} · {f['nombre']}  ({donde})")
    if any(len({e["cuatrimestre"] for e in f["examenes"]}) < len(f["examenes"]) for f in filas):
        print("\n! salió más de una vez en el mismo cuatrimestre")


@registro_app.command("resultados")
def _registro_resultados(
    examen: str = typer.Argument(..., help="Id del examen registrado."),
    archivo: Path = typer.Argument(..., exists=True, dir_okay=False,
                                   help="CSV con una fila por estudiante: estudiante, tema, [ausente] y una columna "
                                        "por pregunta (su número en el tema o su id)."),
    cuatrimestre: Optional[str] = typer.Option(None, "--cuatrimestre", help="Si hay exámenes con ese id en varios cuatrimestres."),
    carpeta: Optional[Path] = typer.Option(None, "--carpeta", help=_AYUDA_CARPETA_REGISTRO),
    forzar: bool = typer.Option(False, "--forzar", help="Reemplazar resultados ya importados."),
) -> None:
    """Importa los resultados de un examen registrado: la letra marcada o el puntaje de cada pregunta."""
    from generador_examenes.core import registro

    ruta = _carpeta_registro(carpeta)
    candidatos = sorted(ruta.glob(f"{cuatrimestre or '*'}/{examen}.json"))
    if len(candidatos) != 1:
        print(f"Error: {'no hay' if not candidatos else 'hay varios'} exámenes registrados con id {examen} en {ruta}"
              + ("" if not candidatos else ": indicá --cuatrimestre"), file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    try:
        actual = registro.leer(candidatos[0])
        if actual.get("resultados") and not forzar:
            raise registro.ErrorRegistro(f"{candidatos[0].name} ya tiene resultados ({actual['resultados']['fuente']}): "
                                         "con --forzar se reemplazan")
        nuevo, avisos = registro.importar_resultados(actual, archivo)
        registro.escribir(nuevo, candidatos[0])
    except (registro.ErrorRegistro, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    for aviso in avisos:
        print(f"Aviso: {aviso}", file=sys.stderr)
    estudiantes = nuevo["resultados"]["estudiantes"]
    ausentes = sum(1 for e in estudiantes if e["ausente"])
    print(f"✓ {candidatos[0]}: {len(estudiantes)} estudiante(s), {ausentes} ausente(s)")


@registro_app.command("analizar")
def _registro_analizar(
    cuatrimestre: Optional[str] = typer.Option(None, "--cuatrimestre", help="Sólo los exámenes de este cuatrimestre."),
    examen: Optional[List[str]] = typer.Option(None, "--examen", help="Sólo estos exámenes (por id; repetible)."),
    carpeta: Optional[Path] = typer.Option(None, "--carpeta", help=_AYUDA_CARPETA_REGISTRO),
    salida: Optional[Path] = typer.Option(None, "-o", "--output", help="Escribir el informe en Markdown."),
    json_output: bool = typer.Option(False, "--json", help="El análisis como JSON."),
) -> None:
    """La calidad de cada pregunta con resultados: dificultad, discriminación, omisiones y distractores,
    sumando todos los exámenes en que salió, y la confiabilidad (alfa) de cada tema."""
    import json

    from generador_examenes.core import registro

    _, registros = _registros(carpeta, cuatrimestre)
    if examen:
        registros = [r for r in registros if r["id"] in examen]
    analisis, temas = registro.analizar(registros)
    if not analisis:
        print("No hay resultados importados para analizar (alucard registro resultados).", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    if json_output:
        print(json.dumps(registro.a_dict(analisis, temas), indent=2, ensure_ascii=False))
    texto = registro.informe(analisis, temas)
    if salida is not None:
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(texto, encoding="utf-8")
        if not json_output:
            print(f"✓ {salida}")
    elif not json_output:
        print(texto)


omr_app = typer.Typer(context_settings=dict(CONTEXTO), add_completion=False, no_args_is_help=True,
                      help="Exámenes con carátula OMR para la app Escáner OMR (OMR_SPEC.md).")
app.add_typer(omr_app, name="omr")

_AYUDA_CONFIG = "exam.yaml o exam.json: identidad del examen, variantes, escala, curva y rúbrica."


def _omr_config(ruta: Path):
    """La configuración OMR validada, o el error (código 1) con cada problema en su renglón."""
    from generador_examenes.omr.config import ErrorConfig, cargar

    try:
        return cargar(ruta)
    except ErrorConfig as e:
        print(f"Error: {ruta}: la configuración no es válida:", file=sys.stderr)
        for problema in e.problemas:
            print(f"  - {problema}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return None


@omr_app.command("validate")
def _omr_validate(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False, help=_AYUDA_CONFIG),
    roster: Optional[Path] = typer.Option(None, "--roster", exists=True, dir_okay=False,
                                          help="inscriptos.csv (legajo,apellido,nombre[,student_id,variante])."),
    json_output: bool = typer.Option(False, "--json", help="El resultado como JSON."),
) -> None:
    """Valida la configuración (§3.3), el manifiesto que sale de ella (omr-layout/2) y, si se pasa, la nómina.

    Sale con 1 si algo no cumple, con cada problema en su renglón.
    """
    import json

    from generador_examenes.omr import layout, nomina, qr

    cfg = _omr_config(config)
    if cfg is None:
        return
    problemas = [f"manifiesto: {p}" for p in layout.problemas(layout.construir(cfg))]
    inscriptos = []
    if roster is not None:
        try:
            inscriptos = nomina.leer(roster, cfg.variants)
        except nomina.ErrorNomina as e:
            problemas += [f"{roster.name}: {p}" for p in e.problemas]
    largo = max((len(i.student_id) for i in inscriptos), default=4)
    if qr.largo_maximo_caratula(cfg, largo) > qr.CAPACIDAD_CARATULA:
        problemas.append(f"el QR de la carátula pasa de {qr.CAPACIDAD_CARATULA} caracteres (versión 3-Q)")
    compacto = qr.motivos_sin_compacto(cfg)
    if json_output:
        print(json.dumps({"valido": not problemas, "exam_id": cfg.exam_id, "problemas": problemas,
                          "inscriptos": len(inscriptos), "compacto_posible": not compacto,
                          "sin_compacto": compacto}, indent=2, ensure_ascii=False))
    elif problemas:
        print(f"Error: {config}:", file=sys.stderr)
        for problema in problemas:
            print(f"  - {problema}", file=sys.stderr)
    else:
        print(f"✓ {config}: {cfg.exam_id}, {len(cfg.rubric)} ejercicio(s), variantes {', '.join(cfg.variants)}"
              + (f", {len(inscriptos)} inscripto(s)" if roster else ""))
        if compacto:
            print(f"  El QR de configuración va sólo en OMRCFG2: ({'; '.join(compacto)}).")
    _ultimo_codigo_salida["code"] = 1 if problemas else 0


@omr_app.command("preview-curve")
def _omr_preview_curve(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False, help=_AYUDA_CONFIG),
) -> None:
    """Imprime la tabla porcentaje → nota → condición de la curva, la misma cuenta que hace la app."""
    from generador_examenes.omr.notas import texto_tabla

    cfg = _omr_config(config)
    if cfg is not None:
        print(texto_tabla(cfg))


@omr_app.command("build")
def _omr_build(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False, help=_AYUDA_CONFIG),
    roster: Path = typer.Option(..., "--roster", exists=True, dir_okay=False,
                                help="inscriptos.csv (legajo,apellido,nombre[,student_id,variante])."),
    questions: Optional[List[Path]] = typer.Option(None, "--questions", exists=True,
                                                   help="Bancos o carpetas de bancos; reemplaza al input_banco "
                                                        "de la definición."),
    out: Optional[Path] = typer.Option(None, "--out", help="Carpeta del lote (por omisión, dist/<exam_id>/)."),
    qr_config_mode: str = typer.Option("compressed", "--qr-config-mode",
                                       help="compressed (OMRCFG2:, por omisión) o compact (OMRCFG/2, "
                                            "sólo para el layout estándar)."),
    nueva_clave: bool = typer.Option(False, "--nueva-clave",
                                     help="Otra hmac_key: invalida las carátulas ya impresas con la anterior."),
    json_output: bool = typer.Option(False, "--json", help="El resumen del lote como JSON."),
) -> None:
    """Genera el lote: un examen con carátula OMR por estudiante, la nómina, el manifiesto, la hoja docente
    con el QR de configuración y la hoja de calibración.

    Antes de compilar los PDF imprime la tabla de verificación de la curva de notas.
    """
    from generador_examenes.omr import lote, nomina
    from generador_examenes.omr.cuerpo import ErrorCuerpo
    from generador_examenes.omr.notas import texto_tabla

    if qr_config_mode not in ("compressed", "compact"):
        _usage_error(f"--qr-config-mode: {qr_config_mode!r} (elegir entre 'compressed' y 'compact')")
    cfg = _omr_config(config)
    if cfg is None:
        return
    try:
        inscriptos = nomina.leer(roster, cfg.variants)
    except nomina.ErrorNomina as e:
        print(f"Error: {roster}:", file=sys.stderr)
        for problema in e.problemas:
            print(f"  - {problema}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    if not json_output:
        print(texto_tabla(cfg) + "\n")
    try:
        resultado = lote.build(cfg, inscriptos, out or Path("dist") / cfg.exam_id, questions,
                               modo_qr=qr_config_mode, nueva_clave=nueva_clave)
    except (lote.ErrorLote, ErrorCuerpo) as e:
        print(f"Error: {e}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    if json_output:
        print(lote.a_json(lote.resumen_json(resultado)))
        return
    for archivo in (resultado.examenes, resultado.nomina, resultado.manifiesto, resultado.config_qr,
                    resultado.config_qr_svg, resultado.calibracion, resultado.registro):
        print(f"✓ {archivo}")
    print(f"\n{len(inscriptos)} estudiante(s), manifiesto sha256 {resultado.huella}")
    print(f"⚠ {resultado.nomina.name} y {resultado.config_qr.name} son sólo para docentes: la nómina vincula "
          "student_id con la persona y la hoja docente lleva la hmac_key.")
    if resultado.avisos:
        print(f"\nRevisá antes de imprimir ({len(resultado.avisos)}):")
        for aviso in resultado.avisos:
            print(f"  ! {aviso}")


@omr_app.command("calibration-sheet")
def _omr_calibration_sheet(
    manifest: Path = typer.Option(..., "--manifest", exists=True, dir_okay=False, help="layout_<id>_v<n>.json."),
    out: Path = typer.Option(Path("layout_test.pdf"), "--out", help="PDF de la hoja de calibración."),
) -> None:
    """Genera la hoja de calibración de un manifiesto: la cabecera con burbujas rellenas al 0, 25, 50 y 100 %."""
    import json

    from generador_examenes.omr import layout, lote

    try:
        manifiesto = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        _usage_error(f"{manifest}: {e}")
    problemas = layout.problemas(manifiesto)
    if problemas:
        print(f"Error: {manifest}: no cumple omr-layout/2:", file=sys.stderr)
        for problema in problemas:
            print(f"  - {problema}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    raiz = manifest.resolve().parent
    from generador_examenes.core.estilo import FUENTE

    fuente = "(" + ", ".join(json.dumps(f) for f in FUENTE) + ",)"
    try:
        destino = lote._compilar(lote.hoja_calibracion(manifiesto, "/" + manifest.name, fuente), out.resolve(), raiz)
    except lote.ErrorLote as e:
        print(f"Error: {e}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    finally:
        import shutil as _shutil

        _shutil.rmtree(raiz / ".omr", ignore_errors=True)
    print(f"✓ {destino}")


@omr_app.command("verify-geometry")
def _omr_verify_geometry(
    pdf: Path = typer.Option(..., "--pdf", exists=True, dir_okay=False, help="examenes_<exam_id>.pdf u otro PDF con carátulas."),
    manifest: Path = typer.Option(..., "--manifest", exists=True, dir_okay=False, help="layout_<id>_v<n>.json."),
    pagina: Optional[List[int]] = typer.Option(None, "--pagina", min=1, help="Página a verificar (repetible; por omisión, la 1)."),
    todas: bool = typer.Option(False, "--todas", help="Todas las páginas con carátula (las que tienen los cuatro marcadores)."),
    tolerancia: float = typer.Option(0.3, "--tolerancia", min=0.01, help="Error máximo, en mm."),
    json_output: bool = typer.Option(False, "--json", help="El resultado como JSON."),
) -> None:
    """Rasteriza la carátula a 300 DPI, detecta los cuatro ArUco, rectifica el marco y verifica que el centro de
    cada burbuja dibujada coincida con el manifiesto (error < 0,3 mm). Sale con 1 si alguna no coincide."""
    import json

    from generador_examenes.omr import geometria

    try:
        manifiesto = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        _usage_error(f"{manifest}: {e}")
    try:
        paginas = geometria.verificar(pdf, manifiesto, [] if todas else (pagina or [1]), tolerancia)
    except geometria.ErrorGeometria as e:
        print(f"Error: {e}", file=sys.stderr)
        _ultimo_codigo_salida["code"] = 1
        return
    ok = bool(paginas) and all(p.ok for p in paginas)
    if json_output:
        print(json.dumps({"ok": ok, "tolerancia_mm": tolerancia, "paginas": geometria.a_dict(paginas)},
                         indent=2, ensure_ascii=False))
    else:
        print(geometria.texto(paginas, tolerancia) if paginas else f"✗ {pdf}: ninguna página tiene carátula")
    _ultimo_codigo_salida["code"] = 0 if ok else 1


@app.command("doctor")
def _doctor(
    json_output: bool = typer.Option(False, "--json", help="Emitir el diagnóstico como JSON (schema_version 1.0.0)."),
) -> None:
    """Diagnostica gcc, Typst, pypdf y conectividad LanguageTool."""
    if json_output:
        import json

        from generador_examenes.core.doctor import diagnosticar, informe_json

        informe = informe_json(diagnosticar())
        print(json.dumps(informe, ensure_ascii=False, indent=2))
        _ultimo_codigo_salida["code"] = 0 if informe["ok"] else 1
        return
    _ultimo_codigo_salida["code"] = cli_commands.ejecutar_doctor()


def main() -> int:
    """Punto de entrada compatible con el contrato histórico de la CLI.

    Ejecuta la app Typer con ``standalone_mode=False``. Los errores de uso
    de CLI (opciones inválidas, `--definicion` faltante, etc.) se reportan
    con ``SystemExit(2)`` sin capturar acá, tal como hacía
    ``ArgumentParser.error()``/argparse en la implementación previa; los
    códigos 0/1 de los modos de negocio se devuelven como valor de retorno
    de esta función (usado por los tests).
    """
    _ultimo_codigo_salida["code"] = 0
    try:
        app(sys.argv[1:], standalone_mode=False)
    except Exception as exc:  # errores de parseo de Typer/Click (opciones inválidas, etc.)
        if hasattr(exc, "exit_code") and hasattr(exc, "show"):
            exc.show()
            raise SystemExit(exc.exit_code) from exc
        raise
    return _ultimo_codigo_salida["code"]


if __name__ == '__main__':
    sys.exit(main())

