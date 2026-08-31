"""
Punto de entrada principal de la aplicación
"""
import sys
import argparse
from pathlib import Path
import shutil


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


def main():
    """Función principal del CLI"""
    parser = argparse.ArgumentParser(
        prog='generador-examenes',
        description='Generador de exámenes basado en plantillas YAML y bancos Moodle/GIFT'
    )
    
    # Argumentos principales
    parser.add_argument(
        '--init',
        action='store_true',
        help='Inicializar proyecto con archivos de ejemplo'
    )
    
    parser.add_argument(
        '--wizard',
        nargs='?',
        const=None,
        type=Path,
        metavar='YAML',
        help='Asistente interactivo para crear/editar configuración de examen'
    )
    
    parser.add_argument(
        '--category-tree',
        nargs='+',
        type=Path,
        metavar='BANCO',
        help='Generar árbol HTML de categorías de uno o más bancos de preguntas'
    )

    parser.add_argument(
        '--sintetizar',
        type=str,
        metavar='PLANTILLA',
        help='Generar un banco de preguntas de C con daedalus (sintetizador verificado con gcc). '
             'Ver plantillas disponibles con --listar-sintetizadores'
    )

    parser.add_argument(
        '--listar-sintetizadores',
        action='store_true',
        help='Lista las plantillas disponibles del sintetizador daedalus'
    )

    parser.add_argument(
        '--cantidad',
        type=int,
        default=5,
        help='Cantidad de preguntas a sintetizar (default: 5)'
    )

    parser.add_argument(
        '--formato-banco',
        choices=['gift', 'xml'],
        default='gift',
        help='Formato del banco generado por daedalus (default: gift)'
    )

    parser.add_argument(
        '-d', '--definicion',
        type=Path,
        help='Ruta al archivo de definición YAML del examen'
    )

    parser.add_argument(
        '-i', '--input-banco',
        type=Path,
        nargs='+',
        help='Ruta(s) a los archivos de banco de preguntas (override de YAML)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        help='Directorio de salida para los exámenes generados (override de YAML, default: ./output)'
    )

    parser.add_argument(
        '-p', '--path-images',
        type=Path,
        help='Ruta al directorio de imágenes referenciadas en las preguntas (override de YAML)'
    )

    parser.add_argument(
        '-n', '--numero-temas',
        type=int,
        help='Número de temas/versiones a generar (override de YAML, default: 1)'
    )

    parser.add_argument(
        '-s', '--semilla',
        type=int,
        help='Semilla pseudo-aleatoria para generación (override de YAML, default: 42)'
    )

    parser.add_argument(
        '-f', '--formato',
        nargs='+',
        choices=['html', 'pdf'],
        help='Formato(s) de salida (override de YAML, default: html)'
    )
    
    parser.add_argument(
        '-t', '--template', '--typst-template',
        type=Path,
        dest='typst_template',
        help='Ruta a una plantilla Typst personalizada (.typ / .typ.j2) para generación de PDF'
    )
    
    parser.add_argument(
        '--spellcheck', '--languagetool',
        action='store_true',
        dest='spellcheck',
        help='Auditar ortografía y gramática de las preguntas del examen o banco usando LanguageTool'
    )
    
    parser.add_argument(
        '--lt-server',
        type=str,
        help='URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública)'
    )

    parser.add_argument(
        '--lt-username',
        type=str,
        help='Usuario / email de LanguageTool Premium'
    )

    parser.add_argument(
        '--lt-api-key',
        type=str,
        help='API Key / Token de LanguageTool Premium'
    )

    parser.add_argument(
        '--lt-premium',
        action='store_true',
        help='Forzar uso de la API LanguageTool Premium'
    )

    parser.add_argument(
        '--lt-lang',
        default='es-AR',
        help='Código de idioma para LanguageTool (default: es-AR)'
    )

    parser.add_argument(
        '--lt-ignore-rules',
        type=str,
        help='Reglas de LanguageTool a ignorar separadas por comas'
    )

    parser.add_argument(
        '--lt-ignore-words',
        type=str,
        help='Palabras personalizadas a ignorar separadas por comas'
    )

    parser.add_argument(
        '--lt-fix',
        action='store_true',
        help='Aplica correcciones ortográficas automáticas'
    )

    parser.add_argument(
        '--md', '--output-md',
        type=Path,
        dest='output_md',
        help='Genera reporte de auditoría en formato Markdown'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        dest='json_output',
        help='Emite salida estructurada en formato JSON'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validar la definición sin generar archivos'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug con logging detallado'
    )

    parser.add_argument(
        '--show-completion',
        action='store_true',
        help='Show completion for the current shell, to copy it or customize the installation.'
    )

    parser.add_argument(
        '--install-completion',
        action='store_true',
        help='Install completion for the current shell.'
    )
    
    args = parser.parse_args()

    if getattr(args, 'show_completion', False) or getattr(args, 'install_completion', False):
        prog = Path(sys.argv[0]).name
        if prog not in ("generador-examenes", "alucard"):
            prog = "generador-examenes"
        script = f"""_{prog.replace('-', '_')}_completion() {{
    local cur prev words cword
    if declare -F _init_completion >/dev/null 2>&1; then
        _init_completion || return
    else
        cur="${{COMP_WORDS[COMP_CWORD]}}"
        prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    fi

    local opts="--init --wizard --category-tree --sintetizar --listar-sintetizadores --cantidad --formato-banco -d --definicion -i --input-banco -o --output-dir -p --path-images -n --numero-temas -s --semilla -f --formato --validate --debug --help --show-completion --install-completion"

    case "$prev" in
        --formato|-f)
            COMPREPLY=($(compgen -W "html pdf" -- "$cur"))
            return 0
            ;;
        --formato-banco)
            COMPREPLY=($(compgen -W "gift xml" -- "$cur"))
            return 0
            ;;
        --sintetizar)
            COMPREPLY=($(compgen -W "incrementos precedencia recursion traza-punteros" -- "$cur"))
            return 0
            ;;
        -d|--definicion|-i|--input-banco|-o|--output-dir|-p|--path-images|--wizard|--category-tree)
            COMPREPLY=($(compgen -f -- "$cur"))
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "$opts" -- "$cur"))
        return 0
    fi
    COMPREPLY=($(compgen -f -- "$cur"))
}}
complete -F _{prog.replace('-', '_')}_completion {prog}
"""
        if args.show_completion:
            print(script)
            return 0
        if args.install_completion:
            comp_dir = Path.home() / ".bash_completions"
            if comp_dir.is_dir():
                target = comp_dir / f"{prog}.bash"
                target.write_text(script, encoding="utf-8")
                print(f"Completion installed in {target}")
            else:
                rc_file = Path.home() / ".bashrc"
                if rc_file.is_file():
                    with open(rc_file, "a", encoding="utf-8") as f:
                        f.write(f"\n# {prog} completion\n{script}\n")
                    print(f"Completion installed in {rc_file}")
            return 0
    
    # Configurar logging
    from generador_examenes.config.logging_config import setup_logging
    setup_logging(debug=args.debug)
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Modo inicialización
    if args.init:
        logger.info("Modo inicialización - creando archivos de ejemplo")
        try:
            inicializar_proyecto()
            return 0
        except Exception as e:
            logger.error(f"Error durante la inicialización: {e}")
            if args.debug:
                raise
            return 1
    
    # Modo wizard
    if args.wizard is not None:
        try:
            from generador_examenes.config.exam_wizard import run_wizard
            run_wizard(args.wizard)
            return 0
        except Exception as e:
            logger.error(f"Error en el wizard: {e}")
            if args.debug:
                raise
            return 1
    
    # Modo catálogo del sintetizador daedalus
    if args.listar_sintetizadores:
        from generador_examenes.synthesizer import plantillas_disponibles

        print("\nPlantillas disponibles del sintetizador daedalus (verificadas con gcc):")
        for nombre, descripcion in sorted(plantillas_disponibles().items()):
            print(f"  - {nombre}: {descripcion}")
        print("\nUso: generador-examenes --sintetizar <plantilla> --cantidad N [-o output] [--formato-banco gift|xml]\n")
        return 0

    # Modo síntesis de preguntas de C compiladas y verificadas al vuelo
    if args.sintetizar:
        try:
            from generador_examenes.synthesizer import (
                plantillas_disponibles,
                sintetizar,
                exportar_gift,
                exportar_xml,
            )

            if args.sintetizar not in plantillas_disponibles():
                logger.error(f"✗ Plantilla desconocida: '{args.sintetizar}'. "
                             f"Disponibles: {', '.join(sorted(plantillas_disponibles()))}")
                return 1

            output_dir = args.output_dir or Path('./output')
            output_dir.mkdir(parents=True, exist_ok=True)
            semilla = args.semilla if args.semilla is not None else 42

            logger.info(f"Sintetizando {args.cantidad} preguntas con la plantilla '{args.sintetizar}' "
                        f"(semilla: {semilla})...")
            snippets = sintetizar(args.sintetizar, cantidad=args.cantidad, semilla=semilla)

            extension = 'gift' if args.formato_banco == 'gift' else 'xml'
            destino = output_dir / f"sintetizados_{args.sintetizar}.{extension}"
            contenido = exportar_gift(snippets) if extension == 'gift' else exportar_xml(snippets)
            destino.write_text(contenido, encoding='utf-8')

            logger.info(f"✓ Banco generado: {destino} ({len(snippets)} preguntas verificadas)")
            print(f"\n✓ {len(snippets)} preguntas de C sintetizadas y verificadas con gcc:")
            print(f"  {destino}")
            print("\nPodés usarlas directo como banco de alucarD (-i) o editarlas con questions ui.")
            return 0
        except Exception as e:
            logger.error(f"Error durante la síntesis: {e}")
            if args.debug:
                raise
            return 1

    # Modo spellcheck / languagetool
    if getattr(args, 'spellcheck', False):
        try:
            import json
            from generador_examenes.config.config_loader import cargar_definicion, cargar_bancos
            from generador_examenes.core.languagetool_checker import (
                analizar_pregunta_languagetool,
                aplicar_autofix_pregunta,
                generar_reporte_markdown_languagetool,
            )

            preguntas_a_revisar = []
            if args.definicion and args.definicion.is_file():
                definicion = cargar_definicion(args.definicion)
                bancos = cargar_bancos(definicion.bancos_preguntas)
                for preguntas in bancos.values():
                    preguntas_a_revisar.extend(preguntas)
            elif args.input_banco:
                bancos = cargar_bancos([str(p) for p in args.input_banco])
                for preguntas in bancos.values():
                    preguntas_a_revisar.extend(preguntas)
            else:
                for candidate in (Path('definicion.yaml'), Path('definicion_ejemplo.yaml')):
                    if candidate.is_file():
                        definicion = cargar_definicion(candidate)
                        bancos = cargar_bancos(definicion.bancos_preguntas)
                        for preguntas in bancos.values():
                            preguntas_a_revisar.extend(preguntas)
                        break

            if not preguntas_a_revisar:
                print("No se encontraron preguntas para auditar con LanguageTool.")
                return 0

            reglas_ign = set(r.strip() for r in args.lt_ignore_rules.split(",") if r.strip()) if getattr(args, 'lt_ignore_rules', None) else None
            palabras_ign = set(w.strip() for w in args.lt_ignore_words.split(",") if w.strip()) if getattr(args, 'lt_ignore_words', None) else None

            todos_los_issues = []
            total_arreglos = 0

            for p in preguntas_a_revisar:
                issues = analizar_pregunta_languagetool(
                    p,
                    lang=args.lt_lang,
                    server_url=args.lt_server,
                    username=args.lt_username,
                    api_key=args.lt_api_key,
                    premium=args.lt_premium,
                    ignore_words=palabras_ign,
                    ignore_rules=reglas_ign,
                )
                if getattr(args, 'lt_fix', False) and issues:
                    total_arreglos += aplicar_autofix_pregunta(p, issues)
                todos_los_issues.extend(issues)

            if getattr(args, 'output_md', None):
                md_text = generar_reporte_markdown_languagetool(todos_los_issues)
                args.output_md.parent.mkdir(parents=True, exist_ok=True)
                args.output_md.write_text(md_text, encoding='utf-8')
                print(f"✓ Reporte Markdown generado en: {args.output_md}")
                return 0 if not todos_los_issues else 1

            if getattr(args, 'json_output', False):
                res = {
                    "total_preguntas": len(preguntas_a_revisar),
                    "total_issues": len(todos_los_issues),
                    "total_arreglos": total_arreglos,
                    "issues": [i.to_dict() for i in todos_los_issues],
                }
                print(json.dumps(res, indent=2, ensure_ascii=False))
                return 0 if not todos_los_issues else 1

            if not todos_los_issues:
                print(f"✓ LanguageTool Passed: {len(preguntas_a_revisar)} preguntas sin observaciones.")
                return 0

            print(f"\n⚠️  Observaciones de LanguageTool ({len(todos_los_issues)} encontradas):")
            for iss in todos_los_issues:
                sug = ", ".join(iss.replacements[:2]) if iss.replacements else "—"
                print(f"  - [{iss.pregunta_id} -> {iss.campo}] {iss.line}:{iss.column} | {iss.original_word} ({iss.context}) -> {sug}")

            return 1
        except Exception as e:
            logger.error(f"Error durante LanguageTool spellcheck: {e}")
            if args.debug:
                raise
            return 1

    # Modo árbol de categorías
    if args.category_tree:
        logger.info("Modo árbol de categorías - generando visualización HTML")
        try:
            from generador_examenes.config.category_tree_viewer import main_category_viewer
            
            banco_paths = args.category_tree
            for banco_path in banco_paths:
                if not banco_path.exists():
                    logger.error(f"✗ Banco no encontrado: {banco_path}")
                    return 1
            
            output_path = args.output_dir / "category_tree.html" if args.output_dir else Path("output/category_tree.html")
            resultado = main_category_viewer(banco_paths, output_path)
            
            logger.info(f"✓ Árbol de categorías generado exitosamente")
            logger.info(f"  Abre el archivo en tu navegador: {resultado.absolute()}")
            print(f"\n✓ Árbol de categorías generado: {resultado.absolute()}")
            print(f"  Abre el archivo en tu navegador para explorar las categorías.")
            
            return 0
        except Exception as e:
            logger.error(f"Error generando árbol de categorías: {e}")
            if args.debug:
                raise
            return 1
    
    # Validar argumentos requeridos
    if not args.definicion:
        parser.error("Se requiere --definicion (o --init para inicializar, o --wizard para configurar, o --category-tree para ver categorías)")
    
    logger.info(f"Iniciando generador de exámenes v5.7.0")
    logger.info(f"Definición: {args.definicion}")
    
    try:
        # Cargar y validar definición
        import yaml
        from pydantic import ValidationError
        from generador_examenes.core.models import DefinicionExamen
        from generador_examenes.core import logic
        from generador_examenes.generators import obtener_renderer
        
        logger.info("Cargando definición del examen...")
        with open(args.definicion, 'r', encoding='utf-8') as f:
            definicion_yaml = yaml.safe_load(f)
        
        try:
            definicion = DefinicionExamen(**definicion_yaml)
            logger.info(f"Definición validada: {definicion}")
        except ValidationError as e:
            logger.error(f"Error de validación en definición:\n{e}")
            return 1
        
        # Aplicar overrides de CLI sobre configuración YAML
        # Los argumentos de CLI tienen prioridad sobre YAML
        input_banco = args.input_banco if args.input_banco else (
            [Path(b) for b in definicion.input_banco] if definicion.input_banco else None
        )
        output_dir = args.output_dir if args.output_dir else Path(definicion.output_dir or './output')
        path_images = args.path_images if args.path_images else (
            Path(definicion.path_images) if definicion.path_images else None
        )
        numero_temas = args.numero_temas if args.numero_temas is not None else (definicion.numero_temas or 1)
        semilla = args.semilla if args.semilla is not None else (definicion.semilla or 42)
        formato = args.formato if args.formato else (definicion.formato or ['html'])
        
        # Validar que tengamos bancos de preguntas
        if not input_banco:
            parser.error("Se requiere input_banco en YAML o --input-banco en CLI")
        
        logger.info(f"Bancos: {input_banco}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Temas: {numero_temas}, Semilla: {semilla}, Formato(s): {formato}")
        
        # Cargar bancos de preguntas
        logger.info("Cargando bancos de preguntas...")
        banco_completo = logic.cargar_bancos(input_banco)
        
        if not banco_completo:
            logger.error("No se cargaron preguntas de los bancos")
            return 1
        
        # Procesar imágenes si se especificó directorio
        if path_images:
            logger.info("Procesando imágenes...")
            logic.procesar_imagenes(banco_completo, path_images)
        
        # Construir pool del examen
        logger.info("Construyendo pool del examen...")
        examen_base = logic.construir_pool_examen(definicion, banco_completo)
        
        # Calcular puntaje total
        puntaje_total = logic.calcular_puntaje_total(examen_base)
        logger.info(f"Puntaje total del examen: {puntaje_total}")
        
        # Modo validación
        if args.validate:
            print("\n" + "="*60)
            print("VALIDACIÓN DEL EXAMEN")
            print("="*60)
            print(f"\nExamen: {definicion.nombre_examen}")
            print(f"Institución: {definicion.institucion}")
            print(f"Materia: {definicion.materia}")
            print(f"\nPuntaje total: {puntaje_total}")
            print(f"\nSecciones:")
            for seccion in examen_base['secciones']:
                num_preguntas = len(seccion['preguntas'])
                puntaje_seccion = sum(p.puntaje for p in seccion['preguntas'])
                print(f"  - {seccion['nombre']}: {num_preguntas} preguntas, {puntaje_seccion} puntos")
            print("\nValidación exitosa ✓")
            return 0
        
        # Modo generación
        logger.info(f"Generando {numero_temas} tema(s)...")
        
        for i in range(numero_temas):
            semilla_tema = semilla + i
            logger.info(f"Generando tema {i + 1}/{numero_temas} (semilla: {semilla_tema})")
            
            # Mezclar examen para este tema
            examen_mezclado = logic.mezclar_examen(
                examen_base,
                semilla_tema,
                definicion.configuracion_examen
            )
            
            # Generar en cada formato solicitado
            for fmt in formato:
                try:
                    renderer = obtener_renderer(fmt, custom_template=getattr(args, 'typst_template', None))
                    
                    # Generar examen
                    archivo_examen = renderer.renderizar_examen(
                        examen_mezclado,
                        definicion,
                        output_dir,
                        i
                    )
                    print(f"✓ Examen generado: {archivo_examen}")
                    
                    # Generar clave si está configurado
                    if definicion.configuracion_examen.generar_clave_profesor:
                        archivo_clave = renderer.renderizar_clave(
                            examen_mezclado,
                            definicion,
                            output_dir,
                            i
                        )
                        print(f"✓ Clave generada: {archivo_clave}")
                
                except Exception as e:
                    logger.error(f"Error generando formato {fmt}: {e}")
                    if args.debug:
                        raise
        
        print(f"\n✓ Generación completada exitosamente")
        print(f"  Archivos guardados en: {output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        if args.debug:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
