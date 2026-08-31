"""Verificador de legibilidad tipográfica y márgenes para imprenta."""

from __future__ import annotations

from typing import Dict, Any


def auditar_legibilidad_imprenta(config_typst: Dict[str, Any]) -> Dict[str, Any]:
    """Valida que los parámetros tipográficos aseguren legibilidad en fotocopiado masivo."""
    font_size = float(config_typst.get("font_size", 10.0))
    margin_mm = float(config_typst.get("margin_mm", 15.0))

    advertencias = []
    if font_size < 9.0:
        advertencias.append(f"Tamaño de fuente muy pequeño ({font_size}pt < 9pt); riesgo de ilegibilidad en copias.")
    if margin_mm < 10.0:
        advertencias.append(f"Márgenes excesivamente estrechos ({margin_mm}mm < 10mm); riesgo de corte en guillotina.")

    return {
        "apto_imprenta": len(advertencias) == 0,
        "advertencias": advertencias,
        "font_size_evaluado": font_size,
        "margin_evaluado": margin_mm,
    }
