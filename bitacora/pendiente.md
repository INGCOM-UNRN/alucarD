# Pendiente

## Funcionalidad para implementar

- [ ] Crear una página para la configuración fina de la generación, para elegir y tener una vista previa de las opciones de visualizacion de cada pregunta (layout), la página debe dar tener un botón para descargar la configuracion necesaria para fusionarlo a la configuracion en la generación del cuestionario 

## ✅ Completado en esta sesión (2025-11-03)
- [x] Solucionar error de `uv sync` (pyproject.toml)
- [x] Corregir error de validación YAML (pool → pools)
- [x] Verificar funcionalidad `--init`
- [x] Llevar cobertura de parsers al 100%
- [x] Llevar cobertura de core/logic al 100%
- [x] Documentar guía UV completa
- [x] Crear ejemplos avanzados
- [x] Implementar soporte para categorías anidadas
- [x] Implementar formato markdown con syntax highlighting
- [x] Cobertura 100% en parsers (gift_parser, moodle_parser)
- [x] Cobertura 83% en markdown_utils

## Mejoras generales
- [ ] Mejorar los __str__ para que las salidas por los logs tengan mas información útil.
- [ ] Aumentar cobertura de __main__.py (actualmente 60%)

## Funcionalidades Adicionales (Opcionales)
- [ ] Validación más robusta de pools vacíos
- [ ] Soporte para más tipos de preguntas (emparejamiento, numérica)
- [ ] Exportación de estadísticas del examen
- [ ] Modo interactivo para configuración

## Mejoras de Parsers (Opcionales)
- [ ] Soporte completo para retroalimentación en GIFT
- [ ] Manejo de preguntas con imágenes embebidas en XML
- [x] Soporte para formato markdown indicado como [markdown] en GIFT o format="markdown" en XML
- [x] Normalización de caracteres fullwidth en bloques de código (implementado con unicodedata.normalize)
- [ ] Soporte para otros formatos de texto en preguntas:
  - [ ] moodle_auto_format: detección automática de formato por Moodle
  - [ ] html directo: HTML sin procesar
  - [ ] plain text: texto plano sin formato

## Documentación Adicional (Opcional)
- [ ] Tutorial de creación de plugins personalizados
- [ ] Documentación de API para extensiones

## Notas
- Cobertura general: **85%**
- Cobertura crítica (parsers + logic): **100%**
- Tests: 162 pasando, 2 skipped (PDF requiere deps de sistema)
