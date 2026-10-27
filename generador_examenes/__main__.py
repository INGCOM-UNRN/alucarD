"""
Punto de entrada principal de la aplicación
"""
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
    dirs_crear = ['templates', 'i18n', 'bancos', 'output']
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

secciones_examen:
  - nombre: "Sección 1 - Preguntas de Ejemplo"
    instrucciones: "Selecciona la respuesta correcta"
    pools:
      - cantidad: 5
        tipos: ["seleccion_multiple"]
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
    
    # Crear README
    readme = Path('README_PROYECTO.md')
    if not readme.exists():
        contenido_readme = """# Proyecto de Generación de Exámenes

Este proyecto usa **alucarD** (generador-examenes) para crear exámenes personalizados.

## Estructura de Directorios

```
.
├── bancos/              # Bancos de preguntas (GIFT o Moodle XML)
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
2. Agrega tus bancos de preguntas en `bancos/`
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
    print("  - output/             (exámenes generados)")
    print("  - definicion_ejemplo.yaml")
    print("  - banco_ejemplo.txt")
    print("  - README_PROYECTO.md")
    print("\nPróximos pasos:")
    print("  1. Edita definicion_ejemplo.yaml con tu configuración")
    print("  2. Agrega tus bancos de preguntas en bancos/")
    print("  3. Ejecuta: generador-examenes -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt --validate")
    print("  4. Genera exámenes: generador-examenes -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt -n 3")
    print()


@app.callback(invoke_without_command=True)
def _cli(
    ctx: typer.Context,
    version: bool = opcion_version("alucard", __version__),  # noqa: ARG001
    init: bool = typer.Option(False, "--init", help="Inicializar proyecto con archivos de ejemplo"),
    wizard: Optional[Path] = typer.Option(
        None, "--wizard", metavar="YAML",
        help="Asistente interactivo para crear/editar configuración de examen",
    ),
    category_tree: Optional[List[Path]] = typer.Option(
        None, "--category-tree", metavar="BANCO",
        help="Generar árbol HTML de categorías de uno o más bancos de preguntas",
    ),
    sintetizar: Optional[str] = typer.Option(
        None, "--sintetizar", metavar="PLANTILLA",
        help="Generar un banco de preguntas de C con daedalus (sintetizador verificado con gcc). "
             "Ver plantillas disponibles con --listar-sintetizadores",
    ),
    listar_sintetizadores: bool = typer.Option(
        False, "--listar-sintetizadores",
        help="Lista las plantillas disponibles del sintetizador daedalus",
    ),
    cantidad: int = typer.Option(5, "--cantidad", help="Cantidad de preguntas a sintetizar."),
    formato_banco: str = typer.Option(
        "gift", "--formato-banco",
        help="Formato del banco generado por daedalus: gift o xml.",
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
        False, "--spellcheck", "--languagetool",
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
    validate: bool = typer.Option(False, "--validate", help="Validar la definición sin generar archivos"),
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

    args = SimpleNamespace(
        init=init, wizard=wizard, category_tree=category_tree, sintetizar=sintetizar,
        listar_sintetizadores=listar_sintetizadores, cantidad=cantidad, formato_banco=formato_banco,
        definicion=definicion, input_banco=input_banco, output_dir=output_dir, path_images=path_images,
        numero_temas=numero_temas, semilla=semilla, formato=formato, typst_template=typst_template,
        spellcheck=spellcheck, lt_server=lt_server, lt_username=lt_username, lt_api_key=lt_api_key,
        lt_premium=lt_premium, lt_lang=lt_lang, lt_ignore_rules=lt_ignore_rules, lt_ignore_words=lt_ignore_words,
        lt_fix=lt_fix, output_md=output_md, json_output=json_output, validate=validate, debug=debug,
        omr=omr, accessible=accessible, bundle_print=bundle_print, audit_typography=audit_typography,
        show_completion=show_completion, install_completion=install_completion,
    )

    if formato_banco not in ("gift", "xml"):
        _usage_error(f"argumento --formato-banco: valor inválido: '{formato_banco}' (elegir entre 'gift', 'xml')")
    if formato:
        for fmt in formato:
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
    elif args.listar_sintetizadores:
        codigo = cli_commands.listar_sintetizadores_disponibles()
    elif args.sintetizar:
        codigo = cli_commands.ejecutar_sintetizar(args, logger)
    elif getattr(args, 'spellcheck', False):
        codigo = cli_commands.ejecutar_spellcheck(args, logger)
    elif args.category_tree:
        codigo = cli_commands.ejecutar_category_tree(args, logger)
    else:
        codigo = cli_commands.generar_examen(args, logger)

    _ultimo_codigo_salida["code"] = codigo


def _cargar_definicion(definicion: Optional[Path], bancos: List[Path], titulo: Optional[str], materia: str,
                       institucion: str):
    """La definición del YAML o, sin él, una con todas las preguntas de los bancos."""
    import yaml

    from generador_examenes.core.balance import definicion_implicita
    from generador_examenes.core.models import DefinicionExamen

    if definicion is not None:
        datos = yaml.safe_load(definicion.read_text(encoding="utf-8"))
    else:
        datos = definicion_implicita(bancos, titulo, materia, institucion)
    return DefinicionExamen(**datos), datos


@app.command("build")
def _build(
    input_banco: List[Path] = typer.Option(..., "-i", "--input-banco", exists=True, dir_okay=False,
                                           help="Banco(s) de preguntas: Moodle XML (el de idkfa), GIFT…"),
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
    """Genera los temas en PDF desde un banco (sin YAML hace falta sólo -i) y audita el balance de claves.

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
    definicion_modelo, datos = _cargar_definicion(definicion, input_banco, titulo, materia, institucion)
    with tempfile.TemporaryDirectory(prefix="alucard-build-") as tmp:
        ruta = definicion
        if ruta is None:
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
    input_banco: List[Path] = typer.Option(..., "-i", "--input-banco", exists=True, dir_okay=False,
                                           help="Banco(s) de preguntas."),
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
    definicion_modelo, _ = _cargar_definicion(definicion, input_banco, None, "", "")
    reporte = auditar_balance(armar_temas(definicion_modelo, input_banco, numero_temas, semilla), umbral)
    print(json.dumps(reporte, ensure_ascii=False, indent=2) if json_output else texto_del_informe(reporte))
    _ultimo_codigo_salida["code"] = 0 if reporte["ok"] else 1


@app.command("lint-gift")
def _lint_gift(
    archivos: List[Path] = typer.Argument(..., exists=True, dir_okay=False, help="Bancos de preguntas GIFT a revisar."),
    fix: bool = typer.Option(False, "--fix", help="Corrige problemas comunes en el lugar."),
) -> None:
    """Revisa (y con --fix corrige) bancos de preguntas GIFT (antes, el ejecutable gift-linter)."""
    from generador_examenes.gift_linter import revisar_archivos

    _ultimo_codigo_salida["code"] = revisar_archivos(archivos, fix=fix)


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

