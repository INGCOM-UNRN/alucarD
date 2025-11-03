.PHONY: help setup install test validate example clean

help: ## Mostrar esta ayuda
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                   alucarD - Makefile                           ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Configurar entorno con UV (ejecuta setup.sh)
	@chmod +x setup.sh
	@./setup.sh

install: ## Instalar dependencias con UV
	@uv venv
	@. .venv/bin/activate && uv pip install -e .
	@echo "✅ Dependencias instaladas"

dev-install: ## Instalar con dependencias de desarrollo
	@uv venv
	@. .venv/bin/activate && uv pip install -e ".[dev]"
	@echo "✅ Dependencias de desarrollo instaladas"

test: ## Ejecutar pruebas (cuando existan)
	@. .venv/bin/activate && pytest tests/ -v

validate: ## Validar el examen de ejemplo
	@. .venv/bin/activate && cd tests/bancos_ejemplo && \
		generador-examenes -d definicion_ejemplo.yaml \
		-i banco_test.txt banco_test.xml --validate

example: ## Generar examen de ejemplo
	@. .venv/bin/activate && cd tests/bancos_ejemplo && \
		generador-examenes -d definicion_ejemplo.yaml \
		-i banco_test.txt banco_test.xml \
		-o ../../output -n 2 -f html
	@echo "✅ Exámenes generados en ./output/"

example-pdf: ## Generar examen de ejemplo con PDF
	@. .venv/bin/activate && cd tests/bancos_ejemplo && \
		generador-examenes -d definicion_ejemplo.yaml \
		-i banco_test.txt banco_test.xml \
		-o ../../output -n 2 -f html pdf
	@echo "✅ Exámenes HTML y PDF generados en ./output/"

clean: ## Limpiar archivos generados
	@rm -rf output/
	@rm -rf .pytest_cache/
	@rm -rf generador_examenes/__pycache__/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Archivos temporales eliminados"

clean-all: clean ## Limpiar todo incluyendo entorno virtual
	@rm -rf .venv/
	@echo "✅ Entorno virtual eliminado"

format: ## Formatear código con black (si está instalado)
	@. .venv/bin/activate && black generador_examenes/ tests/ || echo "black no instalado"

lint: ## Verificar código con mypy (si está instalado)
	@. .venv/bin/activate && mypy generador_examenes/ || echo "mypy no instalado"

freeze: ## Exportar dependencias a requirements.txt
	@. .venv/bin/activate && uv pip freeze > requirements.txt
	@echo "✅ Dependencias exportadas a requirements.txt"

info: ## Mostrar información del proyecto
	@echo "Proyecto: alucarD - Generador de Exámenes v5.0.0"
	@echo "Python: $$(python3 --version)"
	@if command -v uv &> /dev/null; then echo "UV: $$(uv --version)"; else echo "UV: no instalado"; fi
	@echo "Entorno virtual: $$(if [ -d .venv ]; then echo 'Existe'; else echo 'No existe'; fi)"
	@echo ""
	@if [ -d .venv ]; then \
		echo "Paquetes instalados:"; \
		. .venv/bin/activate && uv pip list | grep -E "pydantic|pyyaml|jinja2|weasyprint" || true; \
	fi

docs: ## Abrir documentación
	@echo "📚 Documentación disponible:"
	@echo "  • README.md - Introducción"
	@echo "  • GUIA_UV.md - Guía de UV"
	@echo "  • EJEMPLOS.md - Ejemplos"
	@echo "  • INSTALACION.md - Instalación"
	@echo "  • RESUMEN_PROYECTO.md - Resumen técnico"
