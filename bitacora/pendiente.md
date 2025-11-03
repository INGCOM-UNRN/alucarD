# Pendiente

## Core
- [ ] core/logic.py - Lógica de orquestación:
  - [ ] cargar_bancos()
  - [ ] procesar_imagenes()
  - [ ] construir_pool_examen()
  - [ ] mezclar_examen()

## Parsers
- [ ] parsers/gift_parser.py - Parser GIFT completo
- [ ] parsers/moodle_parser.py - Parser Moodle XML completo
- [ ] Registro de plugins en parsers/__init__.py

## Generators
- [ ] generators/html_renderer.py - Renderer HTML completo
- [ ] generators/pdf_renderer.py - Renderer PDF con WeasyPrint
- [ ] Registro de plugins en generators/__init__.py

## Tests
- [ ] tests/test_parsers.py - Tests unitarios de parsers
- [ ] tests/test_logic.py - Tests de lógica
- [ ] tests/test_models.py - Tests de modelos Pydantic
- [ ] tests/bancos_ejemplo/banco_test.xml - Banco de ejemplo XML
- [ ] tests/bancos_ejemplo/banco_test.txt - Banco de ejemplo GIFT

## Main
- [ ] Implementar flujo completo en __main__.py
- [ ] Implementar modo --init para crear ejemplos

## Ejemplos
- [ ] Crear archivo de ejemplo definicion.yaml
- [ ] Crear bancos de ejemplo funcionales
