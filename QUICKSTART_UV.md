# 🚀 Inicio Rápido con UV

Instala y ejecuta **alucarD** en 3 pasos (menos de 2 minutos).

## Linux / macOS

```bash
# 1. Setup automático
./setup.sh

# 2. Activar entorno
source .venv/bin/activate

# 3. Generar primer examen
cd tests/bancos_ejemplo
generador-examenes -d definicion_ejemplo.yaml \
  -i banco_test.txt banco_test.xml \
  -o ../../output -n 2 -f html

# Ver resultado
open ../../output/examen_tema_01.html  # macOS
xdg-open ../../output/examen_tema_01.html  # Linux
```

## Windows (PowerShell)

```powershell
# 1. Setup automático
.\setup.ps1

# 2. Activar entorno
.venv\Scripts\Activate.ps1

# 3. Generar primer examen
cd tests\bancos_ejemplo
generador-examenes -d definicion_ejemplo.yaml `
  -i banco_test.txt banco_test.xml `
  -o ..\..\output -n 2 -f html

# Ver resultado
start ..\..\output\examen_tema_01.html
```

## Alternativa: Makefile (Linux/macOS)

```bash
# Setup completo
make setup

# Generar ejemplo
make example

# Ver todos los comandos
make help
```

## Comandos Útiles

```bash
# Ver ayuda
generador-examenes --help

# Solo validar (sin generar)
generador-examenes -d def.yaml -i banco.txt --validate

# Generar 5 temas con PDF
generador-examenes -d def.yaml -i banco.txt -n 5 -f html pdf

# Modo debug
generador-examenes -d def.yaml -i banco.txt --debug
```

## ¿Problemas?

Ver **GUIA_UV.md** sección Troubleshooting.

## Más Información

- **GUIA_UV.md** - Guía completa de UV
- **EJEMPLOS.md** - Más ejemplos de uso
- **README.md** - Documentación general
