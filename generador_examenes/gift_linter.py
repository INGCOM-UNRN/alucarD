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

def _titulo_en(lines, numero):
    """El título `::…::` de la pregunta que contiene la línea `numero` (1-based)."""
    for linea in reversed(lines[:numero]):
        m = re.match(r"\s*::(.+?)::", linea)
        if m:
            return m.group(1).strip()
    return "?"


def revisar_diagramas(content):
    """Problemas de los bloques ```estructura: renglones en blanco o llaves (GIFT corta la pregunta
    ahí) y diagramas que no se pueden dibujar. Cada uno con su línea y su pregunta."""
    from generador_examenes.diagramas import _FENCE, ErrorDiagrama, leer_bloques, renderizar

    lines = content.split("\n")
    problemas = []
    for m in _FENCE.finditer(content):
        linea = content[:m.start()].count("\n") + 1
        titulo = _titulo_en(lines, linea)
        cuerpo = m.group("cuerpo")
        donde = f"Línea {linea} («{titulo}»)"
        if any(not renglon.strip() for renglon in cuerpo.rstrip("\n").split("\n")):
            problemas.append(f"{donde}: el bloque estructura tiene un renglón en blanco: en GIFT la pregunta se corta ahí")
        if "{" in cuerpo or "}" in cuerpo:
            problemas.append(f"{donde}: el bloque estructura tiene llaves: en GIFT abren las respuestas "
                             "(escribí las listas con corchetes)")
            continue
        try:
            for bloque in leer_bloques(cuerpo):
                renderizar(bloque)
        except ErrorDiagrama as e:
            problemas.append(f"{donde}: diagrama inválido: {e}")
    return problemas


def revisar_formulas(content):
    """Las fórmulas `$...$` que no se pueden dibujar, con su línea y su pregunta."""
    from generador_examenes.matematica import errores_en_texto

    lines = content.split("\n")
    problemas = []
    # `\=` y `\~` son los escapes de GIFT en una opción, no comandos de LaTeX.
    for pos, formula, motivo in errores_en_texto(re.sub(r"\\([=~])", r" \1", content)):
        linea = content[:pos].count("\n") + 1
        problemas.append(f"Línea {linea} («{_titulo_en(lines, linea)}»): fórmula inválida {formula}: {motivo}")
    return problemas


# Lo que puede llevar `:` en un banco: comentarios, `$CATEGORY:`, los delimitadores del título, las
# respuestas numéricas ({#3:2}) y el escape de GIFT. El resto cuenta como dos puntos sueltos.
_DOS_PUNTOS = re.compile(r"^[ \t]*//.*$|^[ \t]*\$CATEGORY:.*$|\{\s*#[^{}]*\}|\\:"
                         r"|^[ \t]*::(?P<titulo>.+?)::|(?P<dos_puntos>:)", re.M)
# Los metadatos de un comentario sin `:`: `[tag:x]` es el formato de Moodle, `[tag, x]` el nuestro.
_METADATO_CON_DOS_PUNTOS = re.compile(r"^[ \t]*//.*$", re.M)
_TAG_O_CATEGORIA = re.compile(r"\[(tag|category):\s*((?:\\\]|[^\]])*?)\s*\]", re.I)
_INICIO_PREGUNTA = re.compile(r"^[ \t]*::|(?:(?<=\n\n)|\A)[ \t]*\[(?:markdown|html)\]", re.M)
DOS_PUNTOS_ANCHOS = "\uff1a"  # alucard los muestra como `:` (NFKC); igual que los del sintetizador


def dos_puntos_sueltos(content):
    """Dónde hay un `:` que Moodle no admite: toda la pregunta, salvo los bloques ```estructura y las
    fórmulas (Moodle no los importa sin preprocesar) y la sintaxis vieja, que se
    revisa aparte."""
    from generador_examenes.diagramas import _FENCE
    from generador_examenes.matematica import tramos_de_formulas
    from generador_examenes.parsers.gift_parser import sintaxis_vieja

    exentos = ([m.span() for m in _FENCE.finditer(content)] + [m.span() for m in sintaxis_vieja(content)]
               + tramos_de_formulas(content))
    posiciones = []
    for m in _DOS_PUNTOS.finditer(content):
        if m.group("titulo"):
            posiciones += [m.start("titulo") + i for i, c in enumerate(m.group("titulo")) if c == ":"]
        elif m.group("dos_puntos"):
            posiciones.append(m.start())
    return [pos for pos in posiciones if not any(desde <= pos < hasta for desde, hasta in exentos)]


def revisar_moodle(content):
    """Lo que impide importar el banco en Moodle tal cual: metadatos fuera de un comentario o con `:`,
    `{desarrollo}` y dos puntos sueltos. `corregir_para_moodle` arregla todo esto."""
    from generador_examenes.parsers.gift_parser import sintaxis_vieja

    lines = content.split("\n")

    def donde(pos):
        linea = content[:pos].count("\n") + 1
        return f"Línea {linea} («{_titulo_en(lines, linea)}»)"

    problemas = []
    for m in sintaxis_vieja(content):
        if m.group("desarrollo"):
            problemas.append(f"{donde(m.start())}: Moodle toma {m.group().strip()} como respuesta corta: "
                             "escribí {} y el tamaño en un comentario // [tag, desarrollo-grande]")
        else:
            problemas.append(f"{donde(m.start())}: Moodle toma {m.group().strip()} como texto de la pregunta: "
                             "va en un comentario // [tag, …]")
    for comentario in _METADATO_CON_DOS_PUNTOS.finditer(content):
        for m in _TAG_O_CATEGORIA.finditer(comentario.group()):
            problemas.append(f"{donde(comentario.start())}: {m.group()} lleva `:`: escribilo [{m.group(1)}, {m.group(2)}]")
    for pos in dos_puntos_sueltos(content):
        problemas.append(f"{donde(pos)}: `:` en la pregunta: escribilo \\: o {DOS_PUNTOS_ANCHOS}")
    return problemas


def _inicio_de_pregunta(content, pos):
    inicios = [m.start() for m in _INICIO_PREGUNTA.finditer(content, 0, pos)]
    if inicios:
        return inicios[-1]
    corte = content.rfind("\n\n", 0, pos)
    return corte + 2 if corte >= 0 else 0


def corregir_para_moodle(content):
    """Pasa los metadatos a un comentario arriba de la pregunta, sin `:`, `{desarrollo:grande}` a `{}`
    con su etiqueta y los `:` sueltos a ancho completo."""
    from generador_examenes.parsers.gift_parser import _TAMANO, sintaxis_vieja

    ediciones, etiquetas, categorias = [], {}, {}
    for m in sintaxis_vieja(content):
        inicio = _inicio_de_pregunta(content, m.start())
        nuevas = etiquetas.setdefault(inicio, [])
        if m.group("desarrollo"):
            ediciones.append((m.start(), m.end(), "{}"))
            if _TAMANO.fullmatch(f"desarrollo-{m.group('tamano')}"):
                nuevas.append(f"desarrollo-{m.group('tamano').lower()}")
            continue
        if m.group("clave").lower() == "category":
            categorias[inicio] = m.group("valor")
        else:
            nuevas += [tag.strip() for tag in m.group("valor").split(",") if tag.strip()]
        sola_en_su_linea = content[m.start() - 1:m.start()] in ("", "\n") and content[m.end():m.end() + 1] == "\n"
        ediciones.append((m.start(), m.end() + sola_en_su_linea, ""))
    for pos in {*etiquetas, *categorias}:
        marcas = ([f"[tag, {', '.join(etiquetas[pos])}]"] if etiquetas.get(pos) else [])
        marcas += [f"[category, {categorias[pos]}]"] if pos in categorias else []
        if marcas:
            ediciones.append((pos, pos, f"// {' '.join(marcas)}\n"))
    for desde, hasta, texto in sorted(ediciones, reverse=True):
        content = content[:desde] + texto + content[hasta:]
    content = _METADATO_CON_DOS_PUNTOS.sub(
        lambda c: _TAG_O_CATEGORIA.sub(lambda m: f"[{m.group(1)}, {m.group(2)}]", c.group()), content)
    for pos in dos_puntos_sueltos(content):
        content = content[:pos] + DOS_PUNTOS_ANCHOS + content[pos + 1:]
    return content


def revisar_tablas(content):
    """Los bloques ```tabla que no se pueden armar, con su línea y su pregunta."""
    from generador_examenes.core.markdown_utils import markdown_to_html
    from generador_examenes.tablas import errores_en_texto

    lines = content.split("\n")
    problemas = []
    for pos, motivo in errores_en_texto(content, markdown_to_html):
        linea = content[:pos].count("\n") + 1
        problemas.append(f"Línea {linea} («{_titulo_en(lines, linea)}»): tabla inválida: {motivo}")
    return problemas


_BLOQUE_C = re.compile(r"^```[ \t]*c[ \t]*\n(?P<codigo>.*?)^```[ \t]*$", re.S | re.M)


def revisar_codigo(content, gcc="gcc"):
    """Con `--compilar`: los bloques ```c que son programas completos (tienen main) se compilan con
    `gcc -fsyntax-only`; los fragmentos se saltean. Devuelve (problemas, compilados)."""
    import shutil
    import subprocess
    import tempfile

    from generador_examenes.core.markdown_utils import normalizar_fullwidth

    if shutil.which(gcc) is None:
        return [f"No se puede compilar: no está {gcc}"], 0
    lines = content.split("\n")
    problemas, compilados = [], 0
    for m in _BLOQUE_C.finditer(content):
        # El código de un GIFT viene con los caracteres especiales escapados (\{) o en ancho completo
        # (＃, （, ↵, ··· de sangría): se vuelve a C antes de compilar.
        codigo = normalizar_fullwidth(m.group("codigo")).replace("·", " ")
        codigo = re.sub(r"\\([{}=~#:])", r"\1", codigo)
        if not re.search(r"\bmain\s*\(", codigo):
            continue
        compilados += 1
        linea = content[:m.start()].count("\n") + 1
        with tempfile.TemporaryDirectory(prefix="alucard-lint-") as tmp:
            fuente = Path(tmp) / "pregunta.c"
            fuente.write_text(codigo, encoding="utf-8")
            res = subprocess.run([gcc, "-fsyntax-only", "-std=c11", str(fuente)],
                                 capture_output=True, text=True, check=False)
        if res.returncode != 0:
            error = next((l for l in res.stderr.splitlines() if "error" in l), res.stderr.strip()[:120])
            # «pregunta.c:3:12: error: …» → la línea del banco: la del bloque más la del código.
            m_pos = re.search(r"pregunta\.c:(\d+):\d+:\s*(.*)", error)
            if m_pos:
                linea, error = linea + int(m_pos.group(1)), m_pos.group(2)
            problemas.append(f"Línea {linea} («{_titulo_en(lines, linea)}»): el código no compila: {error}")
    return problemas, compilados


def lint_gift_file(filepath, fix=False, compilar=False):
    """Analiza y opcionalmente formatea un archivo GIFT."""
    print(f"\n{'='*60}")
    print(f"Analizando: {filepath.name}")
    print(f"{'='*60}")
    
    if not filepath.exists():
        print(f"❌ Error: Archivo no encontrado")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    content = corregir_para_moodle(original) if fix else original
    lines = content.split('\n')
    issues = []
    stats = {'total': 0, 'valid': 0, 'errors': 0, 'warnings': 0}
    current_question = []
    line_num = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        if stripped.startswith('::'):
            if current_question:
                valid, errs = _process_question('\n'.join(current_question), line_num)
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
                valid, errs = _process_question('\n'.join(current_question), line_num)
                stats['total'] += 1
                if valid:
                    stats['valid'] += 1
                else:
                    stats['errors'] += len(errs)
                issues.extend(errs)
                current_question = []
        else:
            if stripped and not stripped.startswith('//') and not stripped.startswith('$CATEGORY:'):
                issues.append(f"Línea {i}: Texto fuera de pregunta: {stripped[:50]}")
                stats['warnings'] += 1
    
    if current_question:
        valid, errs = _process_question('\n'.join(current_question), line_num)
        stats['total'] += 1
        if valid:
            stats['valid'] += 1
        else:
            stats['errors'] += len(errs)
        issues.extend(errs)
    
    for problema in (revisar_moodle(content) + revisar_diagramas(content) + revisar_tablas(content)
                     + revisar_formulas(content)):
        issues.append(problema)
        stats['errors'] += 1
    if compilar:
        problemas_c, compilados = revisar_codigo(content)
        issues.extend(problemas_c)
        stats['errors'] += len(problemas_c)
        print(f"  Código compilado: {compilados} programa(s)")

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
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n💾 Archivo corregido y guardado")
    
    return stats['errors'] == 0

def _process_question(q_text, start_line):
    """Procesa una pregunta individual y valida su sintaxis."""
    from generador_examenes.parsers.gift_parser import _MARCA, _extraer_bloque_respuestas

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
    for _lang, code in code_blocks:
        if '\t' in code:
            issues.append(f"Línea {start_line} ({title}): Bloque de código contiene tabulaciones")
        
        escaped_brackets = re.findall(r'\\[{}]', code)
        if escaped_brackets:
            issues.append(f"Línea {start_line} ({title}): Llaves escapadas dentro de código: {escaped_brackets}")
    
    # Las respuestas son el último grupo de llaves, como en el parser: el enunciado puede tener
    # llaves propias (código C, una fórmula con \\frac{a}{b}).
    sin_metadatos = re.sub(r'^[ \t]*//.*$|\[(?:tags?|category):.*?\]', '', rest, flags=re.I | re.M)
    partes = _extraer_bloque_respuestas(sin_metadatos)
    if partes:
        answers = partes[1].strip()
        marcas = _MARCA.findall(answers)
        
        if answers in ('T', 'F', 'TRUE', 'FALSE'):
            pass
        elif '~' in marcas:
            if '=' not in marcas:
                issues.append(f"Línea {start_line} ({title}): Opción múltiple sin respuesta correcta (=)")
            
            if len(marcas) < 2:
                issues.append(f"Línea {start_line} ({title}): Menos de 2 opciones")
        elif '->' in answers:
            pairs = answers.split('=')
            if len(pairs) < 2:
                issues.append(f"Línea {start_line} ({title}): Menos de 2 pares de emparejamiento")
        elif answers.startswith('#'):
            pass
        elif not answers:
            pass
    
    return len(issues) == 0, issues

def format_gift_text(text):
    """Formatea texto GIFT normalizando espaciado."""
    result = text
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'::([^:]+)::\s*', r'::\1::\n', result)
    result = re.sub(r'([=~])\s+', r'\1 ', result)
    return result

def main():
    # gift-linter es un alias de `alucard lint-gift` (N-ALUCARD-02): responde también el contrato
    # (--version/-v y doctor) en lugar de tomar «doctor» o «--version» por nombres de archivo.
    if sys.argv[1:] in (['--version'], ['-v']):
        from generador_examenes import __version__
        print(f"gift-linter {__version__}")
        sys.exit(0)
    if sys.argv[1:2] == ['doctor']:
        from generador_examenes.__main__ import main as main_alucard
        sys.argv = ['alucard', *sys.argv[1:]]
        sys.exit(main_alucard())
    if '--help' in sys.argv or '-h' in sys.argv:
        # Ayuda en español, con la misma redacción que la de Typer traducida por yutani (N-ECO-14).
        print("""Uso: gift-linter [OPCIONES] ARCHIVOS...

Linter y formateador para archivos GIFT (alias de `alucard lint-gift`).

Opciones:
  --fix                 Corrige los problemas comunes en el mismo archivo y lo deja compatible con Moodle.
  --show-completion     Muestra el autocompletado para bash, para copiarlo o adaptarlo.
  --install-completion  Instala el autocompletado para bash.
  -v, --version         Muestra la versión de gift-linter y sale.
  -h, --help            Muestra esta ayuda y sale.

Comandos:
  doctor [--json]       Diagnostica el entorno (el mismo diagnóstico que `alucard doctor`).

Ejemplos:
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
                print(f"Autocompletado instalado en {target}")
            else:
                rc_file = Path.home() / ".bashrc"
                if rc_file.is_file():
                    with open(rc_file, "a", encoding="utf-8") as f:
                        f.write(f"\n# {prog} completion\n{script}\n")
                    print(f"Autocompletado instalado en {rc_file}")
                else:
                    # Antes salía con 0 sin instalar nada (N-ECO-18).
                    print("No se encontró ~/.bash_completions ni ~/.bashrc: no se instaló el "
                          "autocompletado. Copiá la salida de `gift-linter --show-completion` en la "
                          "configuración de tu terminal.", file=sys.stderr)
                    sys.exit(1)
            sys.exit(0)

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nEjemplos:")
        print("  gift-linter bancos/teorico.gift")
        print("  gift-linter bancos/*.gift --fix")
        sys.exit(1)
    
    fix = '--fix' in sys.argv
    files = [Path(arg) for arg in sys.argv[1:] if arg not in ('--fix', '--show-completion', '--install-completion')]
    sys.exit(revisar_archivos(files, fix=fix))


def revisar_archivos(files, fix=False, compilar=False) -> int:
    """Revisa (y con fix, corrige) bancos GIFT e imprime el resumen; 0 si están todos sin errores.

    La usan `alucard lint-gift` y el alias `gift-linter` (N-ALUCARD-02).
    """
    print("="*60)
    print("LINTER GIFT - Analizador de Bancos de Preguntas")
    print("="*60)

    all_clean = True
    for filepath in files:
        clean = lint_gift_file(filepath, fix=fix, compilar=compilar)
        if not clean:
            all_clean = False

    print(f"\n{'='*60}")
    print(f"Total archivos: {len(files)}")
    print(f"Estado: {'✅ Todos sin errores' if all_clean else '⚠️  Algunos con errores'}")
    print(f"{'='*60}\n")

    return 0 if all_clean else 1


if __name__ == '__main__':
    main()
