"""
Punto de entrada principal de la aplicación
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional
import shutil

import typer

from generador_examenes import cli_commands
from generador_examenes.cli_errors import usage_error as _usage_error

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


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


@app.command()
def _cli(
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
    cantidad: int = typer.Option(5, "--cantidad", help="Cantidad de preguntas a sintetizar (default: 5)"),
    formato_banco: str = typer.Option(
        "gift", "--formato-banco",
        help="Formato del banco generado por daedalus: gift|xml (default: gift)",
    ),
    definicion: Optional[Path] = typer.Option(
        None, "-d", "--definicion", help="Ruta al archivo de definición YAML del examen",
    ),
    input_banco: Optional[List[Path]] = typer.Option(
        None, "-i", "--input-banco",
        help="Ruta(s) a los archivos de banco de preguntas (override de YAML)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output-dir",
        help="Directorio de salida para los exámenes generados (override de YAML, default: ./output)",
    ),
    path_images: Optional[Path] = typer.Option(
        None, "-p", "--path-images",
        help="Ruta al directorio de imágenes referenciadas en las preguntas (override de YAML)",
    ),
    numero_temas: Optional[int] = typer.Option(
        None, "-n", "--numero-temas",
        help="Número de temas/versiones a generar (override de YAML, default: 1)",
    ),
    semilla: Optional[int] = typer.Option(
        None, "-s", "--semilla",
        help="Semilla pseudo-aleatoria para generación (override de YAML, default: 42)",
    ),
    formato: Optional[List[str]] = typer.Option(
        None, "-f", "--formato",
        help="Formato(s) de salida: html y/o pdf (override de YAML, default: html)",
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
    lt_lang: str = typer.Option("es-AR", "--lt-lang", help="Código de idioma para LanguageTool (default: es-AR)"),
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
) -> int:
    """Generador de exámenes basado en plantillas YAML y bancos Moodle/GIFT."""
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
        return cli_commands.ejecutar_completion(args)

    # Configurar logging
    from generador_examenes.config.logging_config import setup_logging
    setup_logging(debug=args.debug)

    import logging
    logger = logging.getLogger(__name__)

    if args.init:
        return cli_commands.ejecutar_init(args, logger)

    if args.wizard is not None:
        return cli_commands.ejecutar_wizard(args, logger)

    if args.listar_sintetizadores:
        return cli_commands.listar_sintetizadores_disponibles()

    if args.sintetizar:
        return cli_commands.ejecutar_sintetizar(args, logger)

    if getattr(args, 'spellcheck', False):
        return cli_commands.ejecutar_spellcheck(args, logger)

    if args.category_tree:
        return cli_commands.ejecutar_category_tree(args, logger)

    return cli_commands.generar_examen(args, logger)




def main() -> int:
    """Punto de entrada compatible con el contrato histórico de la CLI.

    Ejecuta la app Typer con ``standalone_mode=False`` para poder devolver
    el código de salida como valor de retorno (usado por los tests) y
    traduce los errores de uso de CLI en ``SystemExit(2)``, tal como hacía
    ``ArgumentParser.error`` en la implementación previa basada en argparse.
    """
    try:
        return app(sys.argv[1:], standalone_mode=False)
    except Exception as exc:  # errores de parseo de Typer/Click (opciones inválidas, etc.)
        if hasattr(exc, "exit_code") and hasattr(exc, "show"):
            exc.show()
            raise SystemExit(exc.exit_code)
        raise


if __name__ == '__main__':
    sys.exit(main())
