"""Módulo de verificación y corrección ortográfica en alucarD — Delegado a myst-tools."""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple, Dict, Any

try:
    from myst_tools.languagetool_checker import (
        DEFAULT_LANGUAGETOOL_URL,
        DEFAULT_LANGUAGETOOL_PREMIUM_URL,
        LOCAL_LANGUAGETOOL_URL,
        PALABRAS_IGNORADAS_DEFAULT,
        LanguageToolIssue,
        consultar_languagetool,
        analizar_texto_languagetool as _analizar_texto_base,
        aplicar_autofix_texto,
    )
except ImportError as error:  # sin el extra `languagetool` (myst-tools)
    raise ModuleNotFoundError(
        "La revisión con LanguageTool usa myst-tools, que no está instalado. Instalá alucarD con el "
        "extra languagetool: uv tool install \"generador-examenes[languagetool] @ "
        "git+https://github.com/INGCOM-UNRN/alucarD\"",
        name="myst_tools",
    ) from error

from generador_examenes.core.models import Pregunta, Opcion


def enmascarar_pregunta(contenido: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Enmascara HTML, GIFT, LaTeX y bloques de código preservando longitudes de offset."""
    enmascarado = list(contenido)
    mascaras = []

    def _mask_range(start: int, end: int, preserve_newlines: bool = True):
        for i in range(start, end):
            if preserve_newlines and enmascarado[i] == '\n':
                continue
            enmascarado[i] = ' '
        mascaras.append({"start": start, "end": end})

    # 1. Bloques de código ``` ... ``` o <pre><code> ... </code></pre>
    for m in re.finditer(r'(```|~~~|````)[^\n]*\n.*?\n\s*\1', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'<pre[^>]*>.*?</pre>', contenido, re.DOTALL | re.IGNORECASE):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'<code[^>]*>.*?</code>', contenido, re.DOTALL | re.IGNORECASE):
        _mask_range(m.start(), m.end())

    # 2. Fórmulas matemáticas LaTeX \( ... \), \[ ... \], $$ ... $$, $ ... $
    for m in re.finditer(r'\\\(.*?\\\)', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\\\[.*?\\\]', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\$\$.*?\$\$', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\$[^\$\n]+\$', contenido):
        _mask_range(m.start(), m.end())

    # 3. Etiquetas HTML <...>
    for m in re.finditer(r'<[^>\n]+>', contenido):
        _mask_range(m.start(), m.end())

    # 4. Sintaxis GIFT {:SHORTANSWER:...}, ~..., =..., {#...}
    for m in re.finditer(r'\{[^\}]+\}', contenido):
        _mask_range(m.start(), m.end())

    # 5. Código inline `...`
    for m in re.finditer(r'`[^`\n]+`', contenido):
        _mask_range(m.start(), m.end())

    return "".join(enmascarado), mascaras


def analizar_texto_languagetool(
    texto: str,
    pregunta_id: str,
    campo: str,
    lang: str = "es-AR",
    server_url: Optional[str] = None,
    username: Optional[str] = None,
    api_key: Optional[str] = None,
    premium: bool = False,
    ignore_words: Optional[Set[str]] = None,
    ignore_rules: Optional[Set[str]] = None,
) -> List[LanguageToolIssue]:
    """Analiza un fragmento de texto de una pregunta enmascarando sintaxis específica."""
    issues = _analizar_texto_base(
        texto,
        pregunta_id=pregunta_id,
        campo=campo,
        lang=lang,
        server_url=server_url,
        username=username,
        api_key=api_key,
        premium=premium,
        ignore_words=ignore_words,
        ignore_rules=ignore_rules,
        custom_mask_fn=enmascarar_pregunta,
    )
    for iss in issues:
        iss.pregunta_id = pregunta_id
        iss.campo = campo
    return issues


def analizar_pregunta_languagetool(
    pregunta: Pregunta,
    lang: str = "es-AR",
    server_url: Optional[str] = None,
    username: Optional[str] = None,
    api_key: Optional[str] = None,
    premium: bool = False,
    ignore_words: Optional[Set[str]] = None,
    ignore_rules: Optional[Set[str]] = None,
) -> List[LanguageToolIssue]:
    """Audita todos los campos textuales de una pregunta de examen."""
    issues = []
    # 1. Nombre / Título
    issues.extend(analizar_texto_languagetool(
        pregunta.nombre,
        pregunta_id=pregunta.id,
        campo="nombre",
        lang=lang,
        server_url=server_url,
        username=username,
        api_key=api_key,
        premium=premium,
        ignore_words=ignore_words,
        ignore_rules=ignore_rules,
    ))
    # 2. Enunciado
    issues.extend(analizar_texto_languagetool(
        pregunta.enunciado_html,
        pregunta_id=pregunta.id,
        campo="enunciado",
        lang=lang,
        server_url=server_url,
        username=username,
        api_key=api_key,
        premium=premium,
        ignore_words=ignore_words,
        ignore_rules=ignore_rules,
    ))
    # 3. Opciones
    for idx, opt in enumerate(pregunta.opciones, start=1):
        issues.extend(analizar_texto_languagetool(
            opt.texto_html,
            pregunta_id=pregunta.id,
            campo=f"opcion_{idx}",
            lang=lang,
            server_url=server_url,
            username=username,
            api_key=api_key,
            premium=premium,
            ignore_words=ignore_words,
            ignore_rules=ignore_rules,
        ))
        if opt.retroalimentacion:
            issues.extend(analizar_texto_languagetool(
                opt.retroalimentacion,
                pregunta_id=pregunta.id,
                campo=f"opcion_{idx}_feedback",
                lang=lang,
                server_url=server_url,
                username=username,
                api_key=api_key,
                premium=premium,
                ignore_words=ignore_words,
                ignore_rules=ignore_rules,
            ))
    # 4. Retroalimentación general
    if pregunta.retroalimentacion_general:
        issues.extend(analizar_texto_languagetool(
            pregunta.retroalimentacion_general,
            pregunta_id=pregunta.id,
            campo="retroalimentacion_general",
            lang=lang,
            server_url=server_url,
            username=username,
            api_key=api_key,
            premium=premium,
            ignore_words=ignore_words,
            ignore_rules=ignore_rules,
        ))
    return issues


def aplicar_autofix_pregunta(pregunta: Pregunta, issues: List[LanguageToolIssue]) -> int:
    """Aplica correcciones ortográficas sobre los campos de una pregunta in-place."""
    total_cambios = 0
    issues_por_campo: Dict[str, List[LanguageToolIssue]] = {}
    for iss in issues:
        if iss.campo:
            issues_por_campo.setdefault(iss.campo, []).append(iss)

    if "nombre" in issues_por_campo:
        nuevo_nom, c = aplicar_autofix_texto(pregunta.nombre, issues_por_campo["nombre"])
        if c > 0:
            pregunta.nombre = nuevo_nom
            total_cambios += c

    if "enunciado" in issues_por_campo:
        nuevo_enun, c = aplicar_autofix_texto(pregunta.enunciado_html, issues_por_campo["enunciado"])
        if c > 0:
            pregunta.enunciado_html = nuevo_enun
            total_cambios += c

    for idx, opt in enumerate(pregunta.opciones):
        campo_opt = f"opcion_{idx + 1}"
        if campo_opt in issues_por_campo:
            nuevo_txt, c = aplicar_autofix_texto(opt.texto_html, issues_por_campo[campo_opt])
            if c > 0:
                opt.texto_html = nuevo_txt
                total_cambios += c

    return total_cambios


def generar_reporte_markdown_languagetool(issues: List[LanguageToolIssue]) -> str:
    """Genera reporte Markdown de observaciones ortográficas en preguntas."""
    lines = ["## Auditoría Ortográfica y Gramatical de Preguntas (LanguageTool)\n"]
    lines.append(f"- **Total de observaciones encontradas:** {len(issues)}\n")

    if not issues:
        lines.append("> [!TIP]\n> **Preguntas Impecables:** No se detectaron faltas de ortografía ni errores gramaticales en las preguntas analizadas.\n")
        return "\n".join(lines)

    lines.append("| Pregunta ID | Campo | Línea:Col | Categoría | Regla | Palabra / Contexto | Sugerencia |")
    lines.append("| :--- | :--- | :---: | :--- | :---: | :--- | :--- |")
    for iss in issues:
        sug = ", ".join(f"`{r}`" for r in iss.replacements[:3]) if iss.replacements else "*Ninguna*"
        ctx = iss.context.replace("\n", " ").replace("|", "\\|")
        lines.append(f"| `{iss.pregunta_id}` | `{iss.campo}` | {iss.line}:{iss.column} | {iss.category} | `{iss.rule_id}` | `{iss.original_word}` ({ctx[:35]}...) | {sug} |")
    lines.append("")
    return "\n".join(lines)
