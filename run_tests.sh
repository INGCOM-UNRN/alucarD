#!/bin/bash
# Script para ejecutar tests con cobertura

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Ejecutando Tests de alucarD                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "🔌 Activando entorno virtual..."
    source .venv/bin/activate
fi

# Verificar pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no está instalado"
    echo "   Instala con: pip install pytest pytest-cov"
    exit 1
fi

echo "🧪 Ejecutando tests con cobertura..."
echo ""

# Ejecutar tests
pytest tests/ \
    -v \
    --cov=generador_examenes \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    "$@"

RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ Tests completados exitosamente"
    echo ""
    echo "📊 Reporte de cobertura generado en:"
    echo "   • htmlcov/index.html (HTML)"
    echo "   • coverage.xml (XML)"
    echo ""
    echo "Para ver el reporte HTML:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   open htmlcov/index.html"
    else
        echo "   xdg-open htmlcov/index.html"
    fi
else
    echo "❌ Tests fallaron con código $RESULT"
fi

exit $RESULT
