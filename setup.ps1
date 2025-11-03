# setup.ps1 - Script de configuración automatizado para alucarD (Windows)
# Uso: .\setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "║                   🎓 alucarD Setup 🎓                         ║" -ForegroundColor Cyan
Write-Host "║         Sistema de Generación de Exámenes v5.0.0              ║" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no está instalado" -ForegroundColor Red
    Write-Host "   Por favor instala Python 3.10 o superior desde python.org" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar/Instalar UV
Write-Host "🚀 Verificando UV..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✅ $uvVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "⬇️  UV no está instalado. Instalando..." -ForegroundColor Yellow
    try {
        Invoke-Expression "& { $(Invoke-RestMethod https://astral.sh/uv/install.ps1) }"
        Write-Host "✅ UV instalado correctamente" -ForegroundColor Green
        Write-Host "⚠️  Por favor reinicia PowerShell y ejecuta el script nuevamente" -ForegroundColor Yellow
        exit 0
    } catch {
        Write-Host "❌ Error instalando UV" -ForegroundColor Red
        Write-Host "   Por favor instala manualmente: https://github.com/astral-sh/uv" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Crear entorno virtual
Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "⚠️  Entorno virtual ya existe. ¿Deseas recrearlo? (S/N)" -ForegroundColor Yellow
    $respuesta = Read-Host
    if ($respuesta -eq "S" -or $respuesta -eq "s") {
        Remove-Item -Recurse -Force .venv
        uv venv
    }
} else {
    uv venv
}
Write-Host "✅ Entorno virtual creado en .venv" -ForegroundColor Green
Write-Host ""

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
Write-Host "✅ Entorno activado" -ForegroundColor Green
Write-Host ""

# Instalar dependencias
Write-Host "⬇️  Instalando dependencias..." -ForegroundColor Yellow
Write-Host "   Esto puede tardar un momento..." -ForegroundColor Gray
try {
    uv pip install -e . --quiet
    Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error instalando dependencias" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar instalación
Write-Host "🧪 Verificando instalación..." -ForegroundColor Yellow
try {
    python -m generador_examenes --help > $null 2>&1
    Write-Host "✅ generador-examenes funciona correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: el comando no funciona" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Mostrar información de dependencias
Write-Host "📋 Dependencias instaladas:" -ForegroundColor Yellow
uv pip list | Select-String -Pattern "pydantic|pyyaml|jinja2|weasyprint"
Write-Host ""

# Mensaje final
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "║              ✨ ¡Instalación completada! ✨                   ║" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Próximos pasos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Activar el entorno virtual:" -ForegroundColor White
Write-Host "    .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Ver ayuda del comando:" -ForegroundColor White
Write-Host "    generador-examenes --help" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Probar con ejemplos:" -ForegroundColor White
Write-Host "    cd tests\bancos_ejemplo" -ForegroundColor Gray
Write-Host "    generador-examenes -d definicion_ejemplo.yaml ``" -ForegroundColor Gray
Write-Host "      -i banco_test.txt banco_test.xml --validate" -ForegroundColor Gray
Write-Host ""
Write-Host "4️⃣  Generar primer examen:" -ForegroundColor White
Write-Host "    generador-examenes -d definicion_ejemplo.yaml ``" -ForegroundColor Gray
Write-Host "      -i banco_test.txt banco_test.xml ``" -ForegroundColor Gray
Write-Host "      -o ..\..\output -n 2 -f html" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Documentación:" -ForegroundColor Yellow
Write-Host "   • README.md - Introducción" -ForegroundColor Gray
Write-Host "   • GUIA_UV.md - Guía detallada de UV" -ForegroundColor Gray
Write-Host "   • EJEMPLOS.md - Ejemplos de uso" -ForegroundColor Gray
Write-Host "   • INSTALACION.md - Guía de instalación" -ForegroundColor Gray
Write-Host ""
Write-Host "🐛 ¿Problemas? Ver sección Troubleshooting en GUIA_UV.md" -ForegroundColor Yellow
Write-Host ""

# Nota sobre PDF en Windows
Write-Host "⚠️  NOTA IMPORTANTE para generar PDFs:" -ForegroundColor Yellow
Write-Host "   WeasyPrint requiere GTK3 en Windows" -ForegroundColor Gray
Write-Host "   Descarga desde: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases" -ForegroundColor Gray
Write-Host ""
