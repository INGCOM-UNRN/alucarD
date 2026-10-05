"""
Comandos/modos de ejecución del CLI (extraídos de __main__.py, ALUCARD-D0202).

Cada función implementa un "modo" del CLI (init, wizard, sintetizador,
spellcheck, árbol de categorías, generación de examen) recibiendo el
``SimpleNamespace`` de argumentos ya parseado y, cuando corresponde, el
logger configurado por el entrypoint. Se mantiene la lógica original
sin cambios de comportamiento; el objetivo es reducir el tamaño de
``__main__.py`` (848 LOC) separando orquestación de parseo de CLI.
"""
import json
import sys
from pathlib import Path

from generador_examenes.cli_errors import usage_error as _usage_error


def ejecutar_doctor() -> int:
    """Subcomando `doctor` (ALUCARD-D0401): diagnostica gcc/typst/weasyprint/pypdf/LT."""
    from rich.console import Console
    from generador_examenes.core.doctor import ejecutar_diagnostico_doctor

    ok = ejecutar_diagnostico_doctor(console=Console())
    return 0 if ok else 1


def ejecutar_completion(args) -> int:
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
    return 0


def ejecutar_init(args, logger) -> int:
    # Modo inicialización
    logger.info("Modo inicialización - creando archivos de ejemplo")
    try:
        from generador_examenes.__main__ import inicializar_proyecto
        inicializar_proyecto()
        return 0
    except Exception as e:
        logger.error(f"Error durante la inicialización: {e}")
        if args.debug:
            raise
        return 1


def ejecutar_wizard(args, logger) -> int:
    # Modo wizard
    try:
        from generador_examenes.config.exam_wizard import run_wizard
        run_wizard(args.wizard)
        return 0
    except Exception as e:
        logger.error(f"Error en el wizard: {e}")
        if args.debug:
            raise
        return 1


def listar_sintetizadores_disponibles() -> int:
    # Modo catálogo del sintetizador daedalus
    from generador_examenes.synthesizer import plantillas_disponibles

    print("\nPlantillas disponibles del sintetizador daedalus (verificadas con gcc):")
    for nombre, descripcion in sorted(plantillas_disponibles().items()):
        print(f"  - {nombre}: {descripcion}")
    print("\nUso: generador-examenes --sintetizar <plantilla> --cantidad N [-o output] [--formato-banco gift|xml]\n")
    return 0


def ejecutar_sintetizar(args, logger) -> int:
    # Modo síntesis de preguntas de C compiladas y verificadas al vuelo
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
        if getattr(args, 'json_output', False):
            import json
            res = {
                "version": "1.0",
                "command": "sintetizar",
                "plantilla": args.sintetizar,
                "semilla": semilla,
                "cantidad": len(snippets),
                "formato": extension,
                "archivo": str(destino),
                "snippets": [
                    {
                        "titulo": s.titulo,
                        "enunciado": s.enunciado,
                        "codigo": s.codigo,
                        "salida_correcta": s.salida_correcta,
                        "distractores": s.distractores,
                        "opciones": s.opciones,
                        "explicacion": s.explicacion,
                    }
                    for s in snippets
                ],
            }
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0

        print(f"\n✓ {len(snippets)} preguntas de C sintetizadas y verificadas con gcc:")
        print(f"  {destino}")
        print("\nPodés usarlas directo como banco de alucarD (-i) o editarlas con questions ui.")
        return 0
    except Exception as e:
        logger.error(f"Error durante la síntesis: {e}")
        if getattr(args, 'json_output', False):
            import json
            print(json.dumps({"version": "1.0", "command": "sintetizar", "error": str(e)}, indent=2, ensure_ascii=False))
        if args.debug:
            raise
        return 1


def _bancos_de_definicion(ruta: Path) -> list[Path]:
    """Rutas de los bancos (`input_banco`) que declara una definición YAML."""
    import yaml
    from generador_examenes.core.models import DefinicionExamen

    with open(ruta, 'r', encoding='utf-8') as f:
        definicion = DefinicionExamen(**yaml.safe_load(f))
    return [Path(b) for b in definicion.input_banco or []]


def ejecutar_spellcheck(args, logger) -> int:
    # Modo spellcheck / languagetool
    try:
        import json
        from generador_examenes.core.logic import cargar_bancos
        from generador_examenes.core.languagetool_checker import (
            analizar_pregunta_languagetool,
            aplicar_autofix_pregunta,
            generar_reporte_markdown_languagetool,
        )

        # Mismo orden que la generación: --input-banco manda sobre el input_banco del YAML.
        rutas_bancos: list[Path] = []
        if args.input_banco:
            rutas_bancos = list(args.input_banco)
        elif args.definicion and args.definicion.is_file():
            rutas_bancos = _bancos_de_definicion(args.definicion)
        else:
            for candidate in (Path('definicion.yaml'), Path('definicion_ejemplo.yaml')):
                if candidate.is_file():
                    rutas_bancos = _bancos_de_definicion(candidate)
                    break
        # cargar_bancos devuelve {id: Pregunta}.
        preguntas_a_revisar = list(cargar_bancos(rutas_bancos).values()) if rutas_bancos else []

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
                "version": "1.0",
                "command": "spellcheck",
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
        if getattr(args, 'json_output', False):
            import json
            print(json.dumps({"version": "1.0", "command": "spellcheck", "error": str(e)}, indent=2, ensure_ascii=False))
        if args.debug:
            raise
        return 1


def ejecutar_category_tree(args, logger) -> int:
    # Modo árbol de categorías
    logger.info("Modo árbol de categorías - generando visualización HTML")
    try:
        from generador_examenes.config.category_tree_viewer import (
            build_category_tree,
            generate_html_content,
            main_category_viewer,
        )
        from generador_examenes.parsers import obtener_parser
        
        banco_paths = args.category_tree
        for banco_path in banco_paths:
            if not banco_path.exists():
                logger.error(f"✗ Banco no encontrado: {banco_path}")
                if getattr(args, 'json_output', False):
                    import json
                    print(json.dumps({
                        "version": "1.0",
                        "command": "category-tree",
                        "error": f"Banco no encontrado: {banco_path}",
                    }, indent=2, ensure_ascii=False))
                return 1
        
        output_path = args.output_dir / "category_tree.html" if args.output_dir else Path("output/category_tree.html")
        resultado = main_category_viewer(banco_paths, output_path)
        
        if getattr(args, 'json_output', False):
            import json
            all_questions = {}
            bancos_meta = []
            for b in banco_paths:
                p = obtener_parser(b)
                qs = p.parse(b)
                all_questions.update(qs)
                bancos_meta.append({
                    "path": str(b),
                    "name": b.name,
                    "count": len(qs),
                    "tipo": b.suffix,
                })
            tree = build_category_tree(all_questions)
            res = {
                "version": "1.0",
                "command": "category-tree",
                "html_file": str(resultado.absolute()),
                "total_preguntas": len(all_questions),
                "bancos": bancos_meta,
                "tree": tree.to_dict(),
            }
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0

        logger.info(f"✓ Árbol de categorías generado exitosamente")
        logger.info(f"  Abre el archivo en tu navegador: {resultado.absolute()}")
        print(f"\n✓ Árbol de categorías generado: {resultado.absolute()}")
        print(f"  Abre el archivo en tu navegador para explorar las categorías.")
        
        return 0
    except Exception as e:
        logger.error(f"Error generando árbol de categorías: {e}")
        if getattr(args, 'json_output', False):
            import json
            print(json.dumps({
                "version": "1.0",
                "command": "category-tree",
                "error": str(e),
            }, indent=2, ensure_ascii=False))
        if args.debug:
            raise
        return 1


def generar_examen(args, logger) -> int:
    # Validar argumentos requeridos
    if not args.definicion:
        _usage_error("Se requiere --definicion (o --init para inicializar, o --wizard para configurar, o --category-tree para ver categorías)")
    
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
            _usage_error("Se requiere input_banco en YAML o --input-banco en CLI")
        
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
        
        # Completitud de la clave (QoL #7): sin opción correcta no se imprime.
        sin_clave = logic.auditar_claves(examen_base)
        if sin_clave:
            for problema in sin_clave:
                logger.error(f"Clave incompleta: {problema}")
            print("Error: hay preguntas sin respuesta correcta; corregí el banco antes de generar el examen.",
                  file=sys.stderr)
            return 1

        # Calcular puntaje total
        puntaje_total = logic.calcular_puntaje_total(examen_base)
        logger.info(f"Puntaje total del examen: {puntaje_total}")
        
        # Modo validación
        if args.validate:
            if getattr(args, 'json_output', False):
                import json
                secciones_json = []
                for seccion in examen_base['secciones']:
                    num_preguntas = len(seccion['preguntas'])
                    puntaje_seccion = sum(p.puntaje for p in seccion['preguntas'])
                    secciones_json.append({
                        "nombre": seccion['nombre'],
                        "num_preguntas": num_preguntas,
                        "puntaje": puntaje_seccion,
                    })
                res = {
                    "version": "1.0",
                    "command": "validate",
                    "valido": True,
                    "examen": definicion.nombre_examen,
                    "institucion": definicion.institucion,
                    "materia": definicion.materia,
                    "puntaje_total": puntaje_total,
                    "secciones": secciones_json,
                }
                print(json.dumps(res, indent=2, ensure_ascii=False))
                return 0

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
        archivos_generados = []
        
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
                    archivos_generados.append(str(archivo_examen))
                    if not getattr(args, 'json_output', False):
                        print(f"✓ Examen generado: {archivo_examen}")
                    
                    # Generar clave si está configurado
                    if definicion.configuracion_examen.generar_clave_profesor:
                        archivo_clave = renderer.renderizar_clave(
                            examen_mezclado,
                            definicion,
                            output_dir,
                            i
                        )
                        archivos_generados.append(str(archivo_clave))
                        if not getattr(args, 'json_output', False):
                            print(f"✓ Clave generada: {archivo_clave}")
                
                except Exception as e:
                    logger.error(f"Error generando formato {fmt}: {e}")
                    if args.debug:
                        raise

            # Si se solicitó OMR, generar hoja Typst y descriptor JSON
            if getattr(args, 'omr', False):
                from generador_examenes.core.alucard_qol import generar_plantilla_omr, generar_especificacion_omr_json
                total_pregs = sum(len(s.get('preguntas', [])) for s in examen_mezclado.get('secciones', []))
                omr_typst = generar_plantilla_omr(
                    num_preguntas=total_pregs,
                    tema=i + 1,
                    institucion=definicion.institucion,
                    materia=definicion.materia
                )
                omr_file = output_dir / f"omr_tema_{i + 1:02d}.typ"
                omr_file.write_text(omr_typst, encoding='utf-8')
                archivos_generados.append(str(omr_file))
                
                omr_spec = generar_especificacion_omr_json(num_preguntas=total_pregs, tema=i + 1)
                spec_file = output_dir / f"omr_descriptor_tema_{i + 1:02d}.json"
                spec_file.write_text(json.dumps(omr_spec, indent=2, ensure_ascii=False), encoding='utf-8')
                archivos_generados.append(str(spec_file))
                if not getattr(args, 'json_output', False):
                    print(f"✓ OMR y Descriptor JSON generados para tema {i + 1}: {spec_file.name}")

        # Auditoría tipográfica de código si fue solicitada
        if getattr(args, 'audit_typography', False):
            from generador_examenes.core.alucard_qol import auditar_calidad_tipografica_codigo
            if not getattr(args, 'json_output', False):
                print("\n--- Auditoría Tipográfica de Bloques de Código ---")
            for sec in examen_base.get('secciones', []):
                for preg in sec.get('preguntas', []):
                    enunciado = getattr(preg, 'enunciado_html', '') or ''
                    if '```' in enunciado or '<pre>' in enunciado or 'int ' in enunciado:
                        res = auditar_calidad_tipografica_codigo(enunciado)
                        if not res['cumple_calidad'] and not getattr(args, 'json_output', False):
                            print(f"  [!] Pregunta {preg.id}: {len(res['lineas_largas'])} líneas largas detectadas.")

        # Empaquetado para imprenta si fue solicitado
        if getattr(args, 'bundle_print', False):
            from generador_examenes.core.alucard_qol import empaquetar_pdfs_para_imprenta
            pdfs_generados = sorted(output_dir.glob("examen_tema_*.pdf"))
            if pdfs_generados:
                salida_imprenta = output_dir / "paquete_imprenta_todos_los_temas.pdf"
                empaquetar_pdfs_para_imprenta(pdfs_generados, salida_imprenta, doble_faz=True)
                archivos_generados.append(str(salida_imprenta))
                if not getattr(args, 'json_output', False):
                    print(f"✓ Paquete para imprenta generado (doble faz verificado): {salida_imprenta}")

        if getattr(args, 'json_output', False):
            import json
            res = {
                "version": "1.0",
                "command": "generar_examen",
                "examen": definicion.nombre_examen,
                "institucion": definicion.institucion,
                "materia": definicion.materia,
                "numero_temas": numero_temas,
                "formatos": formato,
                "output_dir": str(output_dir),
                "archivos_generados": archivos_generados,
            }
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0

        print(f"\n✓ Generación completada exitosamente")
        print(f"  Archivos guardados en: {output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        if getattr(args, 'json_output', False):
            import json
            print(json.dumps({
                "version": "1.0",
                "command": "generar_examen",
                "error": str(e),
            }, indent=2, ensure_ascii=False))
        if args.debug:
            raise
        return 1




