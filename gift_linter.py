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
    
    # Validar nombre
    if not re.match(r'^::(.+?)::', question):
        issues.append((line_num, "Falta nombre de pregunta (::nombre::)"))
        valid = False
    
    # Validar llaves
    if '{' not in question or '}' not in question:
        issues.append((line_num, "Faltan opciones entre llaves {}"))
        valid = False
    else:
        open_b = question.count('{')
        close_b = question.count('}')
        if open_b != close_b:
            issues.append((line_num, f"Llaves desbalanceadas: {open_b} {{ vs {close_b} }}"))
            valid = False
        
        # Verificar contenido de opciones
        match = re.search(r'\{(.+?)\}', question, re.DOTALL)
        if match and not match.group(1).strip():
            issues.append((line_num, "Opciones vacías entre llaves"))
            valid = False
    
    # Formatear
    formatted = _format_question(question)
    output.extend(formatted.split('\n'))
    output.append('')
    
    return valid, issues

def _format_question(question):
    """Formatea una pregunta para mejor legibilidad."""
    lines = [l.strip() for l in question.split('\n') if l.strip()]
    result = '\n'.join(lines)
    
    # Espacios consistentes
    result = re.sub(r' +', ' ', result)
    result = re.sub(r'::([^:]+)::(\S)', r'::\1:: \2', result)
    result = re.sub(r'(\S)\{', r'\1 {', result)
    result = re.sub(r'\}(\[tags)', r'} \1', result)
    
    return result

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nEjemplos:")
        print("  python gift_linter.py bancos/teorico.gift")
        print("  python gift_linter.py bancos/*.gift --fix")
        sys.exit(1)
    
    fix = '--fix' in sys.argv
    files = [Path(arg) for arg in sys.argv[1:] if arg != '--fix']
    
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
