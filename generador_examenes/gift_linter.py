#!/usr/bin/env python3
"""
Linter y formateador para archivos GIFT.

Uso:
    gift-linter archivo.gift [--fix]
    gift-linter bancos/*.gift [--fix]
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
            if stripped and not stripped.startswith('//'):
                issues.append(f"Línea {i}: Texto fuera de pregunta: {stripped[:50]}")
                stats['warnings'] += 1
            if fix:
                formatted_lines.append(line)
    
    if current_question:
        valid, errs = _process_question('\n'.join(current_question), line_num, formatted_lines)
        stats['total'] += 1
        if valid:
            stats['valid'] += 1
        else:
            stats['errors'] += len(errs)
        issues.extend(errs)
    
    if issues:
        print("\nProblemas encontrados:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Archivo válido, sin errores")
    
    print(f"\nResumen:")
    print(f"  Total preguntas: {stats['total']}")
    print(f"  Válidas: {stats['valid']}")
    print(f"  Errores: {stats['errors']}")
    print(f"  Advertencias: {stats['warnings']}")
    
    if fix and formatted_lines:
        new_content = '\n'.join(formatted_lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"\n💾 Archivo formateado y guardado")
    
    return stats['errors'] == 0

def _process_question(q_text, start_line, formatted_lines):
    """Procesa una pregunta individual y valida su sintaxis."""
    issues = []
    
    title_match = re.match(r'::([^:]+)::(.*)', q_text, re.DOTALL)
    if not title_match:
        return False, [f"Línea {start_line}: Formato de título inválido"]
    
    title = title_match.group(1).strip()
    rest = title_match.group(2).strip()
    
    if not re.search(r'\{[^}]*\}', rest):
        issues.append(f"Línea {start_line} ({title}): No contiene bloque de respuestas {{...}}")
        return False, issues
    
    code_blocks = re.findall(r'```([a-zA-Z]*)\n(.*?)```', rest, re.DOTALL)
    for lang, code in code_blocks:
        if '\t' in code:
            issues.append(f"Línea {start_line} ({title}): Bloque de código contiene tabulaciones")
        
        escaped_brackets = re.findall(r'\\[{}]', code)
        if escaped_brackets:
            issues.append(f"Línea {start_line} ({title}): Llaves escapadas dentro de código: {escaped_brackets}")
    
    curly_match = re.search(r'\{([^}]*)\}', rest)
    if curly_match:
        answers = curly_match.group(1).strip()
        
        if answers in ('T', 'F', 'TRUE', 'FALSE'):
            pass
        elif '=' in answers or '~' in answers:
            if '=' not in answers:
                issues.append(f"Línea {start_line} ({title}): Opción múltiple sin respuesta correcta (=)")
            
            opts = re.findall(r'([=~][^=~]*)', answers)
            if len(opts) < 2:
                issues.append(f"Línea {start_line} ({title}): Menos de 2 opciones")
        elif '->' in answers:
            pairs = answers.split('=')
            if len(pairs) < 2:
                issues.append(f"Línea {start_line} ({title}): Menos de 2 pares de emparejamiento")
        elif answers.startswith('#'):
            pass
        elif not answers:
            pass
    
    formatted_lines.append(q_text)
    
    return len(issues) == 0, issues

def format_gift_text(text):
    """Formatea texto GIFT normalizando espaciado."""
    result = text
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'::([^:]+)::\s*', r'::\1::\n', result)
    result = re.sub(r'([=~])\s+', r'\1 ', result)
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
