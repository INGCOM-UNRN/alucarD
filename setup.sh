#!/bin/bash
# setup.sh - Script de configuración automatizado para alucarD
# Uso: ./setup.sh

set -e  # Salir si hay error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║                   🎓 alucarD Setup 🎓                         ║"
echo "║         Sistema de Generación de Exámenes v5.0.0              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Detectar sistema operativo
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    MINGW*)     MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  Sistema detectado: $MACHINE"
echo ""

# Verificar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "   Por favor instala Python 3.10 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar/Instalar UV
echo "🚀 Verificando UV..."
if ! command -v uv &> /dev/null; then
    echo "⬇️  UV no está instalado. Instalando..."
    
    if [ "$MACHINE" = "Windows" ]; then
        echo "❌ Por favor instala UV manualmente en Windows:"
        echo "   powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        exit 1
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Agregar al PATH para esta sesión
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if ! command -v uv &> /dev/null; then
            echo "❌ Error instalando UV"
            exit 1
        fi
    fi
fi

UV_VERSION=$(uv --version)
echo "✅ $UV_VERSION encontrado"
echo ""

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ -d ".venv" ]; then
    echo "⚠️  Entorno virtual ya existe. ¿Deseas recrearlo? (s/n)"
    read -r respuesta
    if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
        rm -rf .venv
        uv venv
    fi
else
    uv venv
fi
echo "✅ Entorno virtual creado en .venv"
echo ""

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
if [ "$MACHINE" = "Windows" ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi
echo "✅ Entorno activado"
echo ""

# Instalar dependencias
echo "⬇️  Instalando dependencias..."
echo "   Esto puede tardar un momento..."

# Preferir uv sync si pyproject.toml tiene [project]
if grep -q "\[project\]" pyproject.toml 2>/dev/null; then
    uv sync --quiet
else
    uv pip install -e . --quiet
fi

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "❌ Error instalando dependencias"
    exit 1
fi
echo ""

# Verificar instalación
echo "🧪 Verificando instalación..."
if python -m generador_examenes --help &> /dev/null; then
    echo "✅ generador-examenes funciona correctamente"
else
    echo "❌ Error: el comando no funciona"
    exit 1
fi
echo ""

# Mostrar información de dependencias
echo "📋 Dependencias instaladas:"
uv pip list | grep -E "pydantic|pyyaml|jinja2|weasyprint" || true
echo ""

# Mensaje final
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              ✨ ¡Instalación completada! ✨                   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Próximos pasos:"
echo ""
echo "1️⃣  Activar el entorno virtual:"
if [ "$MACHINE" = "Windows" ]; then
    echo "    .venv\\Scripts\\activate"
else
    echo "    source .venv/bin/activate"
fi
echo ""
echo "2️⃣  Ver ayuda del comando:"
echo "    generador-examenes --help"
echo ""
echo "3️⃣  Probar con ejemplos:"
echo "    cd tests/bancos_ejemplo"
echo "    generador-examenes -d definicion_ejemplo.yaml \\"
echo "      -i banco_test.txt banco_test.xml --validate"
echo ""
echo "4️⃣  Generar primer examen:"
echo "    generador-examenes -d definicion_ejemplo.yaml \\"
echo "      -i banco_test.txt banco_test.xml \\"
echo "      -o ../../output -n 2 -f html"
echo ""
echo "📖 Documentación:"
echo "   • README.md - Introducción"
echo "   • GUIA_UV.md - Guía detallada de UV"
echo "   • EJEMPLOS.md - Ejemplos de uso"
echo "   • INSTALACION.md - Guía de instalación"
echo ""
echo "🐛 ¿Problemas? Ver sección Troubleshooting en GUIA_UV.md"
echo ""
