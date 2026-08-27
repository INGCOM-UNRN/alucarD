#!/usr/bin/env python3
"""
Linter y formateador para archivos GIFT.

Uso:
    python gift_linter.py archivo.gift [--fix]
    python gift_linter.py bancos/*.gift [--fix]
"""
import re
import sys
from pathlib import Path

def lint_gift_file(filepath, fix=False):
    """Analiza y opcionalmente formatea un archivo GIFT."""
    print(f"\n{'='*60}")
    print(f"Analizando: {filepath.name}")
    print(f"{'='*60}")
    
    if not filepath.exists():
        print(f"❌ Error: Archivo no encontrado")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    issues = []
    stats = {'total': 0, 'valid': 0, 'errors': 0, 'warnings': 0}
    formatted_lines = []
    current_question = []
    line_num = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        if stripped.startswith('::'):
            if current_question:
                valid, errs = _process_question('\n'.join(current_question), line_num, formatted_lines)
                stats['total'] += 1
                if valid:
                    stats['valid'] += 1
                else:
                    stats['errors'] += len(errs)
                issues.extend(errs)
            
            current_question = [line]
            line_num = i
        elif current_question:
            current_question.append(line)
            if not stripped:
                valid, errs = _process_question('\n'.join(current_question), line_num, formatted_lines)
                stats['total'] += 1
                if valid:
                    stats['valid'] += 1
                else:
                    stats['errors'] += len(errs)
                issues.extend(errs)
                current_question = []
                formatted_lines.append('')
        else:
            formatted_lines.append(line)
    
    if current_question:
        valid, errs = _process_question('\n'.join(current_question), line_num, formatted_lines)
        stats['total'] += 1
        if valid:
            stats['valid'] += 1
        else:
            stats['errors'] += len(errs)
        issues.extend(errs)
    
    # Reporte
    print(f"\n📊 Estadísticas:")
    print(f"  • Total de preguntas: {stats['total']}")
    print(f"  • Válidas: {stats['valid']}")
    
    if issues:
        print(f"\n⚠️  Problemas encontrados: {len(issues)}")
        for line_no, msg in issues[:10]:
            print(f"  Línea {line_no}: {msg}")
        if len(issues) > 10:
            print(f"  ... y {len(issues) - 10} más")
    else:
        print("\n✅ No se encontraron problemas")
    
    if fix and issues:
        backup = filepath.with_suffix(filepath.suffix + '.backup')
        with open(backup, 'w', encoding='utf-8') as f:
            f.write(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_lines))
        print(f"\n✓ Archivo formateado")
        print(f"✓ Backup: {backup.name}")
    
    return len(issues) == 0

def _process_question(question, line_num, output):
    """Valida y formatea una pregunta."""
    issues = []
    valid = True
    
    # Extraer nombre
    name_match = re.match(r'^::(.+?)::', question)
    if not name_match:
        issues.append((line_num, "Falta nombre de pregunta (::nombre::)"))
        valid = False
        question_name = f"pregunta_linea_{line_num}"
    else:
        question_name = name_match.group(1)
    
    # Validar llaves
    if '{' not in question or '}' not in question:
        issues.append((line_num, f"[{question_name}] Faltan opciones entre llaves {{}}"))
        valid = False
    else:
        open_b = question.count('{')
        close_b = question.count('}')
        if open_b != close_b:
            issues.append((line_num, f"[{question_name}] Llaves desbalanceadas: {open_b} {{ vs {close_b} }}"))
            valid = False
        
        # Verificar contenido de opciones
        match = re.search(r'\{(.+?)\}', question, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if not content:
                issues.append((line_num, f"[{question_name}] Opciones vacías entre llaves"))
                valid = False
            # Verificar que tenga al menos una opción válida
            elif not re.search(r'[=~]', content) and content.lower() not in ['t', 'f', 'true', 'false', 'desarrollo', 'desarrollo:pequeno', 'desarrollo:mediano', 'desarrollo:grande']:
                issues.append((line_num, f"[{question_name}] No se encontraron opciones válidas (=, ~) o tipo de pregunta"))
                valid = False
    
    # Validar formato de tags si existen
    if '[tags' in question.lower() or '[tag:' in question.lower():
        tag_match = re.search(r'\[tags?:\s*(.+?)\]', question, re.IGNORECASE)
        if not tag_match:
            issues.append((line_num, f"[{question_name}] Tags mal formados, debe ser [tags: tag1, tag2]"))
    
    # Validar categoría si existe
    if '[category' in question.lower():
        cat_match = re.search(r'\[category:\s*(.+?)\]', question, re.IGNORECASE)
        if not cat_match:
            issues.append((line_num, f"[{question_name}] Categoría mal formada, debe ser [category: nombre]"))
    
    # Formatear
    formatted = _format_question(question)
    output.extend(formatted.split('\n'))
    output.append('')
    
    return valid, issues

def _format_question(question):
    """Formatea una pregunta para mejor legibilidad."""
    # Dividir en líneas y procesar
    lines = question.split('\n')
    
    # Identificar componentes de la pregunta
    formatted_lines = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detectar bloques de código markdown
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            formatted_lines.append(line)
            continue
        
        # Preservar líneas dentro de bloques de código
        if in_code_block:
            formatted_lines.append(line)
            continue
        
        # Saltar líneas vacías
        if not stripped:
            continue
        
        # Formatear líneas normales
        # Normalizar espacios múltiples
        formatted = re.sub(r' +', ' ', stripped)
        
        # Espacio después de ::nombre::
        formatted = re.sub(r'::([^:]+)::(\S)', r'::\1:: \2', formatted)
        
        # Espacio antes de llaves
        formatted = re.sub(r'(\S)\{', r'\1 {', formatted)
        
        # Espacio entre } y [tags
        formatted = re.sub(r'\}(\[tags)', r'} \1', formatted, flags=re.IGNORECASE)
        
        # Espacio entre } y [category
        formatted = re.sub(r'\}(\[category)', r'} \1', formatted, flags=re.IGNORECASE)
        
        formatted_lines.append(formatted)
    
    # Unir líneas
    result = '\n'.join(formatted_lines)
    
    return result

def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""Usage: gift-linter [OPTIONS] FILES...

Linter y formateador para archivos GIFT.

Options:
  --fix                 Corrige problemas comunes in-place.
  --show-completion     Show completion for the current shell, to copy it or customize the installation.
  --install-completion  Install completion for the current shell.
  -h, --help            Show this message and exit.

Examples:
  gift-linter bancos/teorico.gift
  gift-linter bancos/*.gift --fix
""")
        sys.exit(0)

    if '--show-completion' in sys.argv or '--install-completion' in sys.argv:
        prog = "gift-linter"
        script = f"""_{prog.replace('-', '_')}_completion() {{
    local cur prev words cword
    if declare -F _init_completion >/dev/null 2>&1; then
        _init_completion || return
    else
        cur="${{COMP_WORDS[COMP_CWORD]}}"
    fi
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "--fix --help -h --show-completion --install-completion" -- "$cur"))
        return 0
    fi
    COMPREPLY=($(compgen -f -X '!*.gift' -- "$cur") $(compgen -d -- "$cur"))
}}
complete -F _{prog.replace('-', '_')}_completion {prog}
"""
        if '--show-completion' in sys.argv:
            print(script)
            sys.exit(0)
        if '--install-completion' in sys.argv:
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
            sys.exit(0)

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nEjemplos:")
        print("  gift-linter bancos/teorico.gift")
        print("  gift-linter bancos/*.gift --fix")
        sys.exit(1)
    
    fix = '--fix' in sys.argv
    files = [Path(arg) for arg in sys.argv[1:] if arg not in ('--fix', '--show-completion', '--install-completion')]
    
    print("="*60)
    print("LINTER GIFT - Analizador de Bancos de Preguntas")
    print("="*60)
    
    all_clean = True
    for filepath in files:
        clean = lint_gift_file(filepath, fix=fix)
        if not clean:
            all_clean = False
    
    print(f"\n{'='*60}")
    print(f"Total archivos: {len(files)}")
    print(f"Estado: {'✅ Todos sin errores' if all_clean else '⚠️  Algunos con errores'}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if all_clean else 1)


if __name__ == '__main__':
    main()

