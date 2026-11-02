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
from typing import Optional

from generador_examenes.cli_errors import usage_error as _usage_error


def ejecutar_doctor() -> int:
    """Subcomando `doctor` (ALUCARD-D0401): diagnostica gcc/typst/weasyprint/pypdf/LT."""
    from rich.console import Console
    from generador_examenes.core.doctor import ejecutar_diagnostico_doctor

    ok = ejecutar_diagnostico_doctor(console=Console())
    return 0 if ok else 1


def ejecutar_completion(args) -> int:
    from generador_examenes.synthesizer.plantillas import PLANTILLAS as plantillas

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

local opts="build balance-check lint-gift sintetizar doctor --init --wizard --category-tree -d --definicion -i --input-banco -o --output-dir -p --path-images -n --numero-temas -s --semilla -f --formato --validate --debug --help --show-completion --install-completion"

case "$prev" in
    --formato|-f)
        COMPREPLY=($(compgen -W "html pdf" -- "$cur"))
        return 0
        ;;
    sintetizar)
        COMPREPLY=($(compgen -W "{' '.join(sorted(plantillas))}" -- "$cur"))
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
    from generador_examenes.synthesizer import catalogo

    print("\nPlantillas del sintetizador (cada respuesta se verifica con gcc):\n")
    for nombre, descripcion, verificacion in catalogo():
        print(f"  {nombre}")
        print(f"      {descripcion}")
        if verificacion:
            print(f"      Verificación: {verificacion}")
    print("\nUso: alucard sintetizar <plantilla> [-c N] [--opciones K] [-o output] [-f gift|xml] [-s semilla]")
    print("     alucard sintetizar <plantilla> --muestra      # una pregunta de ejemplo, sin escribir el banco")
    print("Cada plantilla queda en la categoría sintetizados/<plantilla>. Para agregar una: MANUAL,")
    print("«Agregar una plantilla al sintetizador».\n")
    return 0


def mostrar_muestra(snippet) -> str:
    """Una pregunta sintetizada como texto: enunciado, código y opciones con la correcta marcada."""
    lineas = [f"[{snippet.plantilla}] {snippet.titulo}", "", snippet.enunciado, "", snippet.codigo.rstrip(), ""]
    for i, opcion in enumerate(snippet.opciones):
        marca = "✓" if opcion == snippet.salida_correcta else " "
        lineas.append(f"  {marca} {chr(ord('a') + i)}) {opcion}")
    if snippet.explicacion:
        lineas += ["", f"Explicación: {snippet.explicacion}"]
    return "\n".join(lineas)


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

        semilla = args.semilla if args.semilla is not None else 42

        if getattr(args, 'muestra', False):
            [ejemplo] = sintetizar(args.sintetizar, cantidad=1, semilla=semilla,
                                   opciones=getattr(args, 'opciones', 4))
            print(mostrar_muestra(ejemplo))
            return 0

        logger.info(f"Sintetizando {args.cantidad} preguntas con la plantilla '{args.sintetizar}' "
                    f"(semilla: {semilla})...")
        snippets = sintetizar(args.sintetizar, cantidad=args.cantidad, semilla=semilla,
                              opciones=getattr(args, 'opciones', 4))

        output_dir = Path(args.output_dir or './output')
        output_dir.mkdir(parents=True, exist_ok=True)
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
        print("\nPodés usarlas directo como banco de alucarD (-i) o editarlas con voight ui.")
        return 0
    except Exception as e:
        logger.error(f"Error durante la síntesis: {e}")
        if getattr(args, 'json_output', False):
            import json
            print(json.dumps({"version": "1.0", "command": "sintetizar", "error": str(e)}, indent=2, ensure_ascii=False))
        if args.debug:
            raise
        return 1


def _leer_definicion(ruta: Path):
    import yaml
    from generador_examenes.core.models import DefinicionExamen

    with open(ruta, 'r', encoding='utf-8') as f:
        return DefinicionExamen(**yaml.safe_load(f))


def _preguntas_a_revisar(rutas_bancos: list[Path], definicion) -> list:
    """Las preguntas de los bancos y, con definición, también las consignas y las preguntas de los
    repositorios externos que algún pool puede elegir (no todo el repositorio).

    Las consignas se revisan sobre su Markdown completo (enunciado y todas las pistas), que es mucho
    más chico que el HTML con el código resaltado.
    """
    from generador_examenes.core.logic import cargar_banco_definicion, cargar_bancos, candidatas_pool

    proyecto = cargar_bancos(rutas_bancos) if rutas_bancos else {}
    if definicion is None:
        return list(proyecto.values())
    from generador_examenes.core.consignas import componer_markdown
    from generador_examenes.core.models import PresentacionConsigna

    banco = cargar_banco_definicion(definicion, rutas_bancos)
    elegibles = {p.id for seccion in definicion.secciones_examen for pool in seccion.pools
                 for p in candidatas_pool(pool, banco)}
    completa = PresentacionConsigna(metadatos=False, funciones=False, pistas=100, espacio_respuesta=False)
    return [p.model_copy(update={"enunciado_html": componer_markdown(p, completa)}) if p.tipo == "consigna_practica"
            else p
            for pid, p in banco.items() if pid in proyecto or pid in elegibles]


def ejecutar_spellcheck(args, logger) -> int:
    # Modo spellcheck / languagetool
    try:
        import json
        from generador_examenes.core.languagetool_checker import (
            analizar_pregunta_languagetool,
            aplicar_autofix_pregunta,
            generar_reporte_markdown_languagetool,
        )

        # Mismo orden que la generación: --input-banco manda sobre el input_banco del YAML; las
        # consignas y repositorios externos de la definición se suman.
        ruta_definicion = args.definicion if args.definicion and args.definicion.is_file() else next(
            (c for c in (Path('definicion.yaml'), Path('definicion_ejemplo.yaml')) if c.is_file()), None)
        definicion = _leer_definicion(ruta_definicion) if ruta_definicion else None
        from generador_examenes.config import proyecto
        curso = proyecto.cargar(Path(ruta_definicion).parent if ruta_definicion else None)
        rutas_bancos: list[Path] = list(args.input_banco) if args.input_banco else (
            [Path(b) for b in definicion.input_banco or []] if definicion and definicion.input_banco else
            list(curso.input_banco))
        # Servidor, idioma y reglas del alucard.toml cuando no vienen por la línea de comandos.
        lt_server = args.lt_server or curso.lt_servidor
        lt_lang = args.lt_lang if args.lt_lang != "es-AR" or not curso.lt_idioma else curso.lt_idioma
        preguntas_a_revisar = _preguntas_a_revisar(rutas_bancos, definicion)

        if not preguntas_a_revisar:
            print("No se encontraron preguntas para auditar con LanguageTool.")
            return 0

        reglas_ign = set(r.strip() for r in args.lt_ignore_rules.split(",") if r.strip()) if getattr(args, 'lt_ignore_rules', None) else None
        if curso.lt_ignorar_reglas:
            reglas_ign = (reglas_ign or set()) | set(curso.lt_ignorar_reglas)
        palabras_ign = set(w.strip() for w in args.lt_ignore_words.split(",") if w.strip()) if getattr(args, 'lt_ignore_words', None) else None
        # El diccionario de la cátedra (alucard.toml) se suma a las palabras de --lt-ignore-words.
        if curso.palabras:
            palabras_ign = (palabras_ign or set()) | set(curso.palabras)

        todos_los_issues = []
        total_arreglos = 0

        for p in preguntas_a_revisar:
            issues = analizar_pregunta_languagetool(
                p,
                lang=lt_lang,
                server_url=lt_server,
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


def bancos_de_definicion(definicion: Path) -> list[Path]:
    """Los bancos de una definición: su input_banco o, si no tiene, los del alucard.toml del curso."""
    from generador_examenes.config import proyecto

    datos = _leer_definicion(definicion)
    if datos.input_banco:
        return [Path(b) for b in datos.input_banco]
    return list(proyecto.cargar(definicion.parent).input_banco)


def ejecutar_inventario(bancos: list[Path], definicion: Optional[Path]) -> int:
    """`alucard categorias --resumen`: preguntas por categoría y tipo, y si alcanzan para los pools."""
    from generador_examenes.config.category_tree_viewer import cargar_fuentes
    from generador_examenes.core.informe import inventario

    modelo = _leer_definicion(definicion) if definicion else None
    preguntas, _ = cargar_fuentes(bancos, modelo)
    texto, alcanza = inventario(preguntas, modelo)
    print(texto)
    return 0 if alcanza else 1


def ejecutar_category_tree(args, logger) -> int:
    # Modo árbol de categorías
    logger.info("Modo árbol de categorías - generando visualización HTML")
    try:
        from generador_examenes.config.category_tree_viewer import (
            build_category_tree,
            cargar_fuentes,
            main_category_viewer,
        )
        
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
        # Con -d, también las consignas y repositorios externos de la definición.
        definicion = _leer_definicion(args.definicion) if getattr(args, 'definicion', None) else None
        resultado = main_category_viewer(banco_paths, output_path, definicion)
        
        if getattr(args, 'json_output', False):
            import json
            all_questions, bancos_meta = cargar_fuentes(banco_paths, definicion)
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
        
        # Prioridad: línea de comandos, definición YAML, alucard.toml del curso y, al final, el
        # valor por defecto. De la definición cuenta sólo lo que el YAML escribió.
        from generador_examenes.config import proyecto
        curso = proyecto.cargar(Path(args.definicion).parent)
        if curso.ruta is not None:
            logger.info(f"Configuración del curso: {curso.ruta}")

        def del_yaml(campo):
            return getattr(definicion, campo) if campo in definicion.model_fields_set else None

        input_banco = args.input_banco or (
            [Path(b) for b in del_yaml("input_banco")] if del_yaml("input_banco") else None
        ) or curso.input_banco or None
        output_dir = args.output_dir or (
            Path(del_yaml("output_dir")) if del_yaml("output_dir") else None) or curso.output_dir or Path('./output')
        path_images = args.path_images or (
            Path(del_yaml("path_images")) if del_yaml("path_images") else None) or curso.path_images
        numero_temas = next(v for v in (args.numero_temas, del_yaml("numero_temas"), curso.numero_temas, 1)
                            if v is not None)
        semilla = next(v for v in (args.semilla, del_yaml("semilla"), curso.semilla, 42) if v is not None)
        formato = args.formato or del_yaml("formato") or curso.formato or ['html']
        
        # Validar que tengamos bancos de preguntas (o consignas / repositorios externos que los complementen)
        if not input_banco and not definicion.input_consignas and not definicion.repositorios_externos:
            _usage_error("Se requiere input_banco en YAML o --input-banco en CLI "
                         "(o input_consignas / repositorios_externos en el YAML)")
        
        logger.info(f"Bancos: {input_banco}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Temas: {numero_temas}, Semilla: {semilla}, Formato(s): {formato}")
        
        # Cargar bancos de preguntas
        logger.info("Cargando bancos de preguntas...")
        banco_completo = logic.cargar_banco_definicion(definicion, list(input_banco or []))
        
        if not banco_completo:
            logger.error("No se cargaron preguntas de los bancos")
            return 1
        
        # Procesar imágenes si se especificó directorio
        if path_images:
            logger.info("Procesando imágenes...")
            logic.procesar_imagenes(banco_completo, path_images)
        
        # Construir pool del examen
        logger.info("Construyendo pool del examen...")
        examen_base = logic.construir_pool_examen(definicion, banco_completo, semilla)
        
        # Completitud de la clave (QoL #7): sin opción correcta no se imprime.
        sin_clave = logic.auditar_claves(examen_base)
        if sin_clave:
            for problema in sin_clave:
                logger.error(f"Clave incompleta: {problema}")
            print("Error: hay preguntas sin respuesta correcta; corregí el banco antes de generar el examen.",
                  file=sys.stderr)
            return 1

        # Un diagrama mal escrito sale en el examen como un aviso: se dice en qué pregunta antes.
        for problema in diagramas_invalidos(examen_base):
            print(f"Aviso: {problema}", file=sys.stderr)

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
        uso_global: dict = {}  # posición de la correcta en los temas ya generados (balance entre temas)
        temas_generados = []

        for i in range(numero_temas):
            semilla_tema = semilla + i
            logger.info(f"Generando tema {i + 1}/{numero_temas} (semilla: {semilla_tema})")
            
            # Mezclar examen para este tema
            examen_mezclado = logic.mezclar_examen(
                examen_base,
                semilla_tema,
                definicion.configuracion_examen,
                uso_global=uso_global,
            )
            temas_generados.append(examen_mezclado)
            
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

        # Informe de la generación: qué se eligió, de dónde y por qué quedó afuera cada consigna.
        try:
            from generador_examenes.core.informe import armar_informe
            informe = output_dir / "informe.md"
            output_dir.mkdir(parents=True, exist_ok=True)
            informe.write_text(armar_informe(definicion, banco_completo, examen_base, temas_generados,
                                             semilla, list(formato)), encoding="utf-8")
            archivos_generados.append(str(informe))
            if not getattr(args, 'json_output', False):
                print(f"✓ Informe: {informe}")
        except Exception as e:  # el informe no debe impedir el examen
            logger.warning(f"No se pudo armar el informe de la generación: {e}")

        # Auditoría tipográfica de código si fue solicitada
        if getattr(args, 'audit_typography', False):
            from generador_examenes.core.alucard_qol import auditar_calidad_tipografica_codigo
            if not getattr(args, 'json_output', False):
                print("\n--- Auditoría Tipográfica de Bloques de Código ---")
            for sec in examen_base.get('secciones', []):
                for preg in sec.get('preguntas', []):
                    enunciado = getattr(preg, 'enunciado_html', '') or ''
                    if '```' in enunciado or '<pre>' in enunciado or 'int ' in enunciado:
                        calidad = auditar_calidad_tipografica_codigo(enunciado)
                        if not calidad['cumple_calidad'] and not getattr(args, 'json_output', False):
                            print(f"  [!] Pregunta {preg.id}: {len(calidad['lineas_largas'])} líneas largas detectadas.")

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






def fuentes_de_generacion(args) -> tuple[list[Path], list[Path]]:
    """(fuentes, salida) de una generación, para --watch: la definición, el alucard.toml, los bancos,
    las consignas, las imágenes y la plantilla; y la carpeta de salida, que no se mira."""
    import yaml

    from generador_examenes.config import proyecto

    definicion = Path(args.definicion)
    try:
        datos = yaml.safe_load(definicion.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        datos = {}  # mientras se escribe, la definición puede estar a medio guardar
    try:
        curso = proyecto.cargar(definicion.parent)
    except ValueError:
        curso = proyecto.ConfiguracionProyecto()
    rutas = [definicion, *([curso.ruta] if curso.ruta else [])]
    bancos = args.input_banco or datos.get("input_banco") or curso.input_banco or []
    rutas += [Path(b) for b in bancos]
    rutas += [Path(c) for c in datos.get("input_consignas") or []]
    imagenes = args.path_images or datos.get("path_images") or curso.path_images
    if imagenes:
        rutas.append(Path(imagenes))
    if getattr(args, "typst_template", None):
        rutas.append(Path(args.typst_template))
    salida = args.output_dir or datos.get("output_dir") or curso.output_dir or "output"
    return rutas, [Path(salida)]


def diagramas_invalidos(examen: dict) -> list[str]:
    """«La pregunta X (banco) tiene un diagrama inválido: …» por cada bloque ```estructura que no se
    pudo dibujar (en el examen quedaría como un recuadro de error)."""
    import html as html_mod
    import re

    problemas = []
    for seccion in examen.get("secciones", []):
        for p in seccion.get("preguntas", []):
            for m in re.finditer(r'class="estructura-error"><strong>Diagrama inválido:</strong> (.*?)</p>',
                                 getattr(p, "enunciado_html", "") or ""):
                banco = f" de {p.fuente_banco}" if getattr(p, "fuente_banco", None) else ""
                problemas.append(f"la pregunta «{p.nombre}»{banco} tiene un diagrama inválido: "
                                 f"{html_mod.unescape(m.group(1))}")
    return problemas


# --- Vista previa de preguntas (alucard ver) -------------------------------------------------

def preguntas_por_linea(banco: Path) -> list[tuple[int, str]]:
    """(línea, título) de cada pregunta GIFT con título (`::titulo::`), en orden."""
    import re

    try:
        lineas = banco.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    titulos = []
    for n, linea in enumerate(lineas, 1):
        m = re.match(r"\s*::(.+?)::", linea)
        if m:
            titulos.append((n, m.group(1).strip()))
    return titulos


def elegir_preguntas(banco_cargado: dict, ruta_banco: Path, pregunta: Optional[str],
                     linea: Optional[int]) -> tuple[list, str]:
    """Las preguntas de la vista previa y, si no hay ninguna, por qué."""
    preguntas = list(banco_cargado.values())
    if linea is not None:
        anteriores = [t for n, t in preguntas_por_linea(ruta_banco) if n <= linea]
        if not anteriores:
            return [], f"no hay ninguna pregunta con título en {ruta_banco.name} antes de la línea {linea}"
        pregunta = anteriores[-1]
        elegidas = [p for p in preguntas if p.nombre.strip() == pregunta]
        return elegidas, "" if elegidas else f"la pregunta «{pregunta}» de la línea {linea} no se pudo leer"
    if pregunta:
        clave = pregunta.casefold()
        exactas = [p for p in preguntas if p.nombre.casefold() == clave or p.id == pregunta]
        elegidas = exactas or [p for p in preguntas if clave in p.nombre.casefold()]
        if not elegidas:
            disponibles = ", ".join(p.nombre for p in preguntas[:8])
            return [], f"ninguna pregunta se llama «{pregunta}» (hay: {disponibles}{'…' if len(preguntas) > 8 else ''})"
        return elegidas, ""
    return preguntas, ""


def abrir_archivo(ruta: Path) -> bool:
    """Abre `ruta` con el visor del sistema si hay entorno gráfico; False si no se pudo."""
    import os
    import subprocess

    if sys.platform == "win32":
        os.startfile(str(ruta))  # type: ignore[attr-defined]
        return True
    comando = "open" if sys.platform == "darwin" else "xdg-open"
    if comando == "xdg-open" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        subprocess.Popen([comando, str(ruta)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True


def ejecutar_vista_previa(banco: Path, pregunta: Optional[str], linea: Optional[int], formato: str,
                          salida: Path, path_images: Optional[Path], clave: bool, abrir: bool, logger) -> int:
    """Renderiza una pregunta (o todas las del banco) sola, como sale en el examen."""
    from generador_examenes.core import logic
    from generador_examenes.core.balance import definicion_implicita
    from generador_examenes.core.models import DefinicionExamen
    from generador_examenes.generators import obtener_renderer

    banco_cargado = logic.cargar_bancos([banco])
    elegidas, motivo = elegir_preguntas(banco_cargado, banco, pregunta, linea)
    if not elegidas:
        print(f"Error: {motivo}.", file=sys.stderr)
        return 1
    titulo = elegidas[0].nombre if len(elegidas) == 1 else f"{banco.name} ({len(elegidas)} preguntas)"
    datos = definicion_implicita([banco], f"Vista previa: {titulo}")
    datos["configuracion_examen"].update(mezclar_preguntas_dentro_seccion=False,
                                         mezclar_opciones_dentro_pregunta=False, generar_clave_profesor=clave)
    definicion = DefinicionExamen(**datos)
    solo = {p.id: p for p in elegidas}
    if path_images:
        logic.procesar_imagenes(solo, path_images)
    examen = logic.construir_pool_examen(definicion, solo, 0)
    salida.mkdir(parents=True, exist_ok=True)
    renderer = obtener_renderer(formato)
    archivo = renderer.renderizar_examen(examen, definicion, salida, 0)
    archivos = [archivo]
    if clave:
        archivos.append(renderer.renderizar_clave(examen, definicion, salida, 0))
    for a in archivos:
        print(f"✓ Vista previa: {a}")
    if abrir and not abrir_archivo(Path(archivo)):
        print("  (sin entorno gráfico: abrilo a mano)")
    return 0
