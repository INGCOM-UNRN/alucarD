# Guía de Configuración con UV

Esta guía te permite ejecutar el proyecto **alucarD** usando **UV**, un gestor de paquetes y entornos virtuales ultrarrápido para Python. Ideal para llevar el proyecto a cualquier computadora de forma simple.

## ¿Qué es UV?

[UV](https://github.com/astral-sh/uv) es un gestor de paquetes Python escrito en Rust, extremadamente rápido y compatible con pip. Reemplaza `pip`, `venv` y `virtualenv` con una herramienta unificada.

## Instalación de UV

### Linux / macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verificar instalación

```bash
uv --version
```

## Configuración del Proyecto

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd alucard
```

### 2. Crear Entorno Virtual con UV

UV maneja automáticamente los entornos virtuales:

```bash
# Crear entorno virtual
uv venv

# Activar el entorno (Linux/macOS)
source .venv/bin/activate

# Activar el entorno (Windows)
.venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Opción 1: Con uv sync (recomendado - más rápido)
uv sync

# Opción 2: Instalar desde pyproject.toml
uv pip install -e .

# Opción 3: Instalar dependencias específicas
uv pip install pydantic pyyaml jinja2 weasyprint
```

### 4. Verificar Instalación

```bash
# Verificar que el paquete está instalado
uv pip list | grep generador

# Probar el comando
generador-examenes --help

# O ejecutar como módulo
python -m generador_examenes --help
```

## Uso Rápido

### Validar Definición

```bash
cd tests/bancos_ejemplo
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  --validate
```

### Generar Exámenes

```bash
# Generar 2 temas en HTML
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  -o ../../output \
  -n 2 \
  -f html

# Ver archivos generados
ls -la ../../output/
```

### Generar con PDF (requiere dependencias del sistema)

```bash
# Instalar dependencias del sistema primero (ver sección Troubleshooting)

# Generar HTML y PDF
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  -o ../../output \
  -n 2 \
  -f html pdf
```

## Comandos UV Útiles

### Gestión de Paquetes

```bash
# Instalar paquete
uv pip install nombre-paquete

# Instalar versión específica
uv pip install pydantic==2.5.0

# Actualizar paquete
uv pip install --upgrade nombre-paquete

# Desinstalar paquete
uv pip uninstall nombre-paquete

# Listar paquetes instalados
uv pip list

# Mostrar información de un paquete
uv pip show pydantic
```

### Gestión de Entorno Virtual

```bash
# Crear entorno virtual
uv venv

# Crear con nombre personalizado
uv venv mi_entorno

# Crear con versión específica de Python
uv venv --python 3.11

# Eliminar entorno virtual
rm -rf .venv
```

### Exportar/Importar Dependencias

```bash
# Exportar dependencias actuales
uv pip freeze > requirements.txt

# Instalar desde requirements.txt
uv pip install -r requirements.txt
```

## Llevar el Proyecto a Otra Computadora

### Método 1: Con requirements.txt (Recomendado)

**En la computadora original:**

```bash
# Exportar dependencias exactas
uv pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: agregar requirements.txt"
git push
```

**En la computadora nueva:**

```bash
# Instalar UV (ver sección Instalación de UV)

# Clonar proyecto
git clone <url-del-repositorio>
cd alucard

# Crear entorno y instalar
uv venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
uv pip install -r requirements.txt

# Verificar
generador-examenes --help
```

### Método 2: Con pyproject.toml (Más moderno)

**En la computadora nueva:**

```bash
# Instalar UV
# Clonar proyecto
git clone <url-del-repositorio>
cd alucard

# UV instala todo automáticamente
uv venv
source .venv/bin/activate
uv sync  # Instala dependencias y crea lockfile

# Listo!
generador-examenes --help
```

### Método 3: Script de Setup Automatizado

Crea un archivo `setup.sh` en el proyecto:

```bash
#!/bin/bash
# setup.sh - Script de configuración automatizado

echo "🚀 Configurando alucarD..."

# Verificar UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV no está instalado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
uv venv

# Activar entorno
source .venv/bin/activate

# Instalar dependencias
echo "⬇️  Instalando dependencias..."
uv pip install -e .

# Verificar instalación
echo "✅ Verificando instalación..."
if generador-examenes --help &> /dev/null; then
    echo "✨ ¡Instalación completada con éxito!"
    echo ""
    echo "Para usar el proyecto:"
    echo "  1. Activar entorno: source .venv/bin/activate"
    echo "  2. Ejecutar: generador-examenes --help"
else
    echo "❌ Error en la instalación"
    exit 1
fi
```

**Uso:**

```bash
chmod +x setup.sh
./setup.sh
```

## Troubleshooting

### Error: "uv: command not found"

```bash
# Instalar UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Agregar al PATH (agregar a ~/.bashrc o ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Recargar shell
source ~/.bashrc  # o source ~/.zshrc
```

### Error al generar PDF (WeasyPrint)

WeasyPrint requiere dependencias del sistema:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
  python3-dev \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  shared-mime-info
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Windows:**
Instalar GTK3: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

### Error: "No module named 'generador_examenes'"

```bash
# Asegurarse de estar en el directorio del proyecto
cd /ruta/a/alucard

# Reinstalar en modo editable
uv pip install -e .
```

### Entorno virtual no se activa

```bash
# Linux/macOS
source .venv/bin/activate

# Windows CMD
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

## Comparación: UV vs Poetry vs pip

| Característica | UV | Poetry | pip + venv |
|---------------|-----|--------|------------|
| Velocidad | ⚡⚡⚡ Muy rápido | ⚡ Lento | ⚡⚡ Medio |
| Instalación | Simple (1 comando) | Requiere Python | Incluido en Python |
| Lock files | ✅ Sí | ✅ Sí | ❌ No |
| Gestión deps | ✅ Automática | ✅ Automática | 🔧 Manual |
| Compatible pip | ✅ 100% | ⚠️ Limitado | ✅ Nativo |

## Lockfile (uv.lock)

UV genera automáticamente un archivo `uv.lock` que garantiza instalaciones reproducibles:

```bash
# El lockfile se genera automáticamente con:
uv sync

# Se versionan en git para asegurar que todos usen las mismas versiones
git add uv.lock
git commit -m "chore: actualizar lockfile"
```

**Ventajas del lockfile:**
- ✅ Instalaciones reproducibles 100% determinísticas
- ✅ Todos los desarrolladores usan las mismas versiones
- ✅ Builds consistentes en CI/CD
- ✅ Previene problemas de "funciona en mi máquina"

## Ventajas de UV para este Proyecto

1. **Velocidad**: Instalación 10-100x más rápida que pip
2. **Simplicidad**: Un solo comando para setup completo
3. **Portabilidad**: Fácil de compartir entre computadoras
4. **Compatible**: Funciona con `pyproject.toml` y `requirements.txt`
5. **Moderno**: Aprovecha las mejores prácticas de Python moderno
6. **Lockfile**: Instalaciones reproducibles con uv.lock

## Comandos Rápidos de Referencia

```bash
# Setup inicial
uv venv && source .venv/bin/activate && uv pip install -e .

# Ejecutar validación
generador-examenes -d def.yaml -i banco.txt --validate

# Generar exámenes
generador-examenes -d def.yaml -i banco.txt -n 3 -f html

# Actualizar dependencias
uv pip install --upgrade pydantic jinja2 pyyaml weasyprint

# Desactivar entorno
deactivate
```

## Recursos Adicionales

- **UV Docs**: https://github.com/astral-sh/uv
- **Python Packaging**: https://packaging.python.org/
- **alucarD Docs**: Ver `README.md`, `INSTALACION.md`, `EJEMPLOS.md`

## Soporte

Si encuentras problemas:
1. Verifica que UV esté instalado: `uv --version`
2. Verifica Python: `python --version` (debe ser 3.10+)
3. Revisa la sección Troubleshooting
4. Consulta los logs con `--debug`

---

**¡Listo!** Con UV puedes tener el proyecto funcionando en cualquier máquina en menos de 2 minutos. 🚀
