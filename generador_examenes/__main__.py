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
    banco_ejemplo = Path('bancos') / 'banco_ejemplo.txt'
    if not banco_ejemplo.exists():
        contenido_banco = """// Banco de preguntas de ejemplo en formato GIFT

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
        logger.info(f"✓ Banco de ejemplo creado: bancos/banco_ejemplo.txt")
    else:
        logger.info(f"  Banco ya existe: bancos/banco_ejemplo.txt")
    
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
input_banco = ["bancos/banco_ejemplo.txt"]
output_dir = "output"
numero_temas = 2
semilla = 2026
formato = ["html"]

[ortografia]
idioma = "es-AR"
# Palabras de la cátedra que LanguageTool no debe marcar.
palabras = ["malloc", "struct", "printf"]
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
└── definicion_ejemplo.yaml  # Ejemplo de definición de examen
```

## Uso Rápido

### 1. Validar la definición

```bash
generador-examenes -d definicion_ejemplo.yaml \\
  -i bancos/banco_ejemplo.txt \\
  --validate
```

### 2. Generar exámenes

```bash
generador-examenes -d definicion_ejemplo.yaml \\
  -i bancos/banco_ejemplo.txt \\
  -o output \\
  -n 3 \\
  -f html
```

## Siguientes Pasos

1. Edita `definicion_ejemplo.yaml` con tu configuración
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
    print("  - alucard.toml          (bancos, salida, temas y formato del curso)")
    print("  - banco_ejemplo.txt")
    print("  - README_PROYECTO.md")
    print("\nPróximos pasos:")
    print("  1. Edita definicion_ejemplo.yaml con tu configuración")
    print("  2. Agrega tus bancos de preguntas en bancos/")
    print("  3. Validá: alucard validar -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt")
    print("  4. Generá los temas: alucard generar -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt -n 3")
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
    definicion: Optional[Path] = typer.Option(
        None, "-d", "--definicion", help="Ruta al archivo de definición YAML del examen",
    ),
    input_banco: Optional[List[Path]] = typer.Option(
        None, "-i", "--input-banco",
        help="Ruta(s) a los archivos de banco de preguntas (tiene prioridad sobre el YAML)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output-dir",
        help="Directorio de salida para los exámenes generados (tiene prioridad sobre el YAML; si no está en ninguno: ./output)",
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
    elif getattr(args, "vigilar", False) and args.definicion:
        from generador_examenes.core.vigilancia import vigilar
        _, salida = cli_commands.fuentes_de_generacion(args)
        codigo = vigilar(lambda: cli_commands.fuentes_de_generacion(args)[0],
                         lambda: cli_commands.generar_examen(args, logger), excluir=salida)
    else:
        codigo = cli_commands.generar_examen(args, logger)

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
    "typst_template", "json_output", "debug", "omr", "accessible", "bundle_print", "audit_typography", "vigilar",
]


def _comando_de_opciones(nombre: str, opciones: List[str], fijos: dict, ayuda: str) -> None:
    """Registra `alucard <nombre>` con las mismas opciones (nombre, tipo, ayuda) que el modo raíz."""
    firma = inspect.signature(_cli)
    parametros = [firma.parameters[n] for n in opciones]

    def comando(**valores):
        _ejecutar({**valores, **fijos})

    comando.__signature__ = firma.replace(parameters=parametros)  # type: ignore[attr-defined]
    comando.__annotations__ = {n: _cli.__annotations__[n] for n in opciones if n in _cli.__annotations__}
    comando.__doc__ = ayuda
    comando.__name__ = f"_comando_{nombre}"
    app.command(nombre)(comando)


_comando_de_opciones("generar", _OPCIONES_GENERAR, {},
                     "Genera los temas del examen de una definición YAML (HTML y/o PDF, claves, OMR).")
_comando_de_opciones("validar", ["definicion", "input_banco", "json_output", "debug"], {"validate": True},
                     "Valida la definición y sus pools sin generar archivos.")
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
    input_banco: Optional[List[Path]] = typer.Option(None, "-i", "--input-banco", exists=True, dir_okay=False,
                                                     help="Banco(s) de preguntas: Moodle XML (el de idkfa), GIFT… "
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
    reporte = auditar_balance(armar_temas(definicion_modelo, input_banco, numero_temas, semilla), umbral)
    print("\n" + texto_del_informe(reporte))
    _ultimo_codigo_salida["code"] = 0 if reporte["ok"] else 1


@app.command("balance-check")
def _balance_check(
    input_banco: Optional[List[Path]] = typer.Option(None, "-i", "--input-banco", exists=True, dir_okay=False,
                                                     help="Banco(s) de preguntas; reemplaza al input_banco de la definición."),
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
    reporte = auditar_balance(armar_temas(definicion_modelo, input_banco, numero_temas, semilla), umbral)
    print(json.dumps(reporte, ensure_ascii=False, indent=2) if json_output else texto_del_informe(reporte))
    _ultimo_codigo_salida["code"] = 0 if reporte["ok"] else 1


@app.command("lint-gift")
def _lint_gift(
    archivos: List[Path] = typer.Argument(..., exists=True, dir_okay=False, help="Bancos de preguntas GIFT a revisar."),
    fix: bool = typer.Option(False, "--fix", help="Corrige problemas comunes en el lugar."),
    compilar: bool = typer.Option(False, "--compilar",
                                  help="Compila con gcc -fsyntax-only los bloques de C que son programas completos."),
) -> None:
    """Revisa (y con --fix corrige) bancos GIFT: formato, bloques estructura y, con --compilar, el código C."""
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
    """Dibuja estructuras de datos (arreglo, matriz, lista, pila, pila de llamadas, cola, árbol) como SVG, con el formato de bloques de statics.

    Escribe un SVG por bloque (`<id>.svg` o `<archivo>_<n>.svg`). Los bloques de statics que no son
    estructuras (texto, tablas de traza, recortables) se saltean con un aviso. En las preguntas, el
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


@app.command("doctor")
def _doctor(
    json_output: bool = typer.Option(False, "--json", help="Emitir el diagnóstico como JSON (schema_version 1.0.0)."),
) -> None:
    """Diagnostica gcc, Typst, WeasyPrint, pypdf y conectividad LanguageTool."""
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

