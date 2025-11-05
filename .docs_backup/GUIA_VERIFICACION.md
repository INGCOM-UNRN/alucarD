# Guía de Verificación de Mejoras

Esta guía te ayuda a verificar cada una de las mejoras implementadas en el proyecto.

---

## 1. 🎨 CSS de Código Optimizado para Impresión

### Archivo a revisar:
- `templates/base_examen.html.j2` (líneas 335-379)

### Qué verificar:
```css
@media print {
  .highlight {
    background-color: #f9f9f9 !important;
    font-size: 0.8em !important;
    line-height: 1.3 !important;
    padding: 0.4em !important;
  }
}
```

### Prueba práctica:
1. Generar un examen con código
2. Abrir en navegador
3. Vista previa de impresión (Ctrl+P)
4. Verificar que el código se ve compacto y legible

---

## 2. 📊 Logging Mejorado

### Archivo a revisar:
- `generador_examenes/generators/html_renderer.py` (líneas 106, 131)

### Qué verificar:
```python
logger.info(f"✓ Examen HTML generado: {output_file.name} (tema {tema + 1})")
logger.info(f"✓ Clave HTML generada: {output_file.name} (tema {tema + 1})")
```

### Prueba práctica:
```bash
python -m generador_examenes -d examenes_prueba/quiz_rapido.yaml \
  -i bancos/*.gift -o output -n 2 -f html
```

Verificar en la salida:
```
[INFO] ✓ Examen HTML generado: examen_tema_01.html (tema 1)
[INFO] ✓ Examen HTML generado: examen_tema_02.html (tema 2)
```

---

## 3. 🎨 Variables Personalizadas con F-Strings

### Archivos a revisar:
- `generador_examenes/core/models.py` (líneas 132-175) - Método `evaluar_variables_personalizadas()`
- `generador_examenes/generators/html_renderer.py` (líneas 84-86, 131-133)
- `examenes_prueba/final_completo.yaml` (líneas 22-31) - Ejemplo de uso

### Qué verificar:

**En models.py:**
```python
def evaluar_variables_personalizadas(self) -> Dict[str, Any]:
    contexto = {
        'nombre_examen': self.nombre_examen,
        'fecha_actual': datetime.now().strftime('%Y-%m-%d'),
        # ...
    }
    # Evaluar f-strings con .format()
```

**En html_renderer.py:**
```python
variables = definicion.evaluar_variables_personalizadas()
contexto['variables'] = variables
```

**En YAML:**
```yaml
variables_personalizadas:
  profesor: "Prof. Carlos Rodríguez"
  periodo: "Segundo Cuatrimestre {anio_actual}"
  titulo_completo: "FINAL - {materia}"
```

### Prueba práctica:
```bash
# Generar examen con variables
python -m generador_examenes -d examenes_prueba/final_completo.yaml \
  -i bancos/*.xml bancos/*.gift -o output -n 1 -f html

# Verificar en HTML generado
grep -E "(Profesor|Aula|periodo)" output/examen_tema_01.html
```

Deberías ver:
```html
<div class="info"><strong>Profesor:</strong> Prof. Carlos Rodríguez</div>
<div class="info"><strong>Aula:</strong> Aula Magna</div>
```

---

## 4. 🧙 Wizard para Configuración

### Archivo a revisar:
- `generador_examenes/config/exam_wizard.py` (clase completa)
- `generador_examenes/__main__.py` (líneas 287-296)

### Qué verificar:

**Clase ExamWizard:**
- `__init__()` - Inicialización
- `run()` - Flujo principal
- `_configurar_informacion_basica()` - Paso 1
- `_configurar_parametros_examen()` - Paso 2
- `_configurar_secciones()` - Paso 3

**Integración en CLI:**
```python
if args.wizard is not None:
    from generador_examenes.config.exam_wizard import run_wizard
    run_wizard(args.wizard)
```

### Prueba práctica:
```bash
# Crear nueva configuración
python -m generador_examenes --wizard test_wizard.yaml

# Editar existente
python -m generador_examenes --wizard examenes_prueba/quiz_rapido.yaml
```

Seguir el flujo interactivo y verificar que se guarda el YAML correctamente.

---

## 5. 📋 Selección por Categoría en Pools

### Archivos a revisar:
- `generador_examenes/core/models.py` (línea 49) - Campo `categoria` en `PoolConfig`
- `generador_examenes/core/logic.py` (líneas 56-102) - Funciones de categorías
- `examenes_prueba/parcial2_codigo.yaml` (línea 42) - Ejemplo de uso

### Qué verificar:

**En PoolConfig:**
```python
class PoolConfig(BaseModel):
    categoria: Optional[str] = None
```

**Funciones de categoría:**
```python
def normalizar_categoria(categoria: str) -> str:
    # Normalización case-insensitive

def categoria_coincide(pregunta_cat: str, filtro_cat: str) -> bool:
    # Soporta wildcards * y **
```

**En YAML:**
```yaml
pools:
  - categoria: "**codigo**"
    tipos: ["seleccion_multiple"]
    cantidad: 10
```

### Prueba práctica:
```bash
# Validar con filtro de categoría
python -m generador_examenes -d examenes_prueba/parcial2_codigo.yaml \
  -i bancos/*.xml --validate
```

Verificar en la salida que las preguntas filtradas sean de la categoría correcta.

---

## 6. 📐 Layout de 4 Columnas

### Archivos a revisar:
- `generador_examenes/core/models.py` (línea 80) - Literal con `compact-4col`
- `templates/base_examen.html.j2` (líneas 163-192) - CSS para 4 columnas
- `examenes_prueba/final_completo.yaml` (línea 53) - Ejemplo de uso

### Qué verificar:

**En SeccionExamen:**
```python
class SeccionExamen(BaseModel):
    layout: Literal["default", "compact-2col", "compact-3col", "compact-4col"] = "default"
```

**CSS:**
```css
.section.layout-compact-4col .options {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr; /* 4 columnas */
  gap: 0.15em;
}
```

**En YAML:**
```yaml
- nombre: "Parte 3: Verdadero/Falso (20%)"
  layout: "compact-4col"
```

### Prueba práctica:
```bash
# Generar examen con layout 4col
python -m generador_examenes -d examenes_prueba/quiz_rapido.yaml \
  -i bancos/*.gift -o output -n 1 -f html

# Verificar en HTML
grep "layout-compact-4col" output/examen_tema_01.html
```

---

## 7. 🧪 Configuraciones de Examen de Prueba

### Archivos a revisar:
- `examenes_prueba/parcial1_basico.yaml`
- `examenes_prueba/parcial2_codigo.yaml`
- `examenes_prueba/final_completo.yaml` ⭐
- `examenes_prueba/recuperatorio_mixto.yaml`
- `examenes_prueba/quiz_rapido.yaml`

### Qué verificar en cada archivo:

**parcial1_basico.yaml:**
- ✅ 2 secciones con layouts compact-2col y compact-3col
- ✅ Variables personalizadas (6 variables)
- ✅ Filtrado por tipo de pregunta

**parcial2_codigo.yaml:**
- ✅ Layout default para código
- ✅ Filtrado por categoría con wildcard `**codigo**`
- ✅ Variable `nota_especial`

**final_completo.yaml:** ⭐ (Más completo)
- ✅ 3 secciones con layouts mixtos
- ✅ Puntajes diferenciados (2.0, 4.0, 1.0)
- ✅ 7 variables personalizadas con composición
- ✅ Múltiples tipos de filtrado

**recuperatorio_mixto.yaml:**
- ✅ 3 secciones con diferentes layouts
- ✅ Configuración compleja
- ✅ Variable `nota_minima`

**quiz_rapido.yaml:**
- ✅ Examen corto (30 minutos)
- ✅ Layout compact-4col
- ✅ Variables: semana, tema_evaluado, peso_nota

### Prueba práctica:
```bash
# Validar todos
for config in examenes_prueba/*.yaml; do
    echo "=== $(basename $config) ==="
    python -m generador_examenes -d "$config" \
        -i bancos/*.xml bancos/*.gift --validate
    echo ""
done
```

**Generar uno completo:**
```bash
python -m generador_examenes -d examenes_prueba/final_completo.yaml \
  -i bancos/*.xml bancos/*.gift -o output -n 2 -f html
```

Verificar archivos generados:
```bash
ls -lh output/
```

---

## 8. 📚 Documentación Consolidada

### Archivos a revisar:
- `README.md` (nuevo, ~2000 líneas)
- `CHANGELOG.md` (actualizado con v5.4.0)
- `.docs_backup/` (respaldo de archivos originales)

### Qué verificar:

**README.md debe incluir:**
- ✅ Tabla de contenidos completa
- ✅ Sección Instalación (consolidado de GUIA_UV.md + INSTALACION.md)
- ✅ Sección Inicio Rápido (consolidado de QUICKSTART_UV.md)
- ✅ Sección Wizard (consolidado de WIZARD.md)
- ✅ Sección Layouts (consolidado de LAYOUTS.md)
- ✅ Sección Variables (consolidado de VARIABLES_PERSONALIZADAS.md)
- ✅ Sección Categorías (consolidado de CATEGORIAS.md)
- ✅ Sección Ejemplos (consolidado de EJEMPLOS.md + EJEMPLOS_AVANZADOS.md)
- ✅ Arquitectura y contribución

**CHANGELOG.md debe incluir:**
- ✅ Versión 5.4.0 (última)
- ✅ Versión 5.3.0 (layouts)
- ✅ Versión 5.2.0 (wizard)
- ✅ Versión 5.1.0 (variables)
- ✅ Versiones anteriores hasta 1.0.0

**Archivos eliminados (en backup):**
```bash
ls .docs_backup/
```

Debería mostrar:
```
CATEGORIAS.md
EJEMPLOS.md
EJEMPLOS_AVANZADOS.md
GUIA_UV.md
INSTALACION.md
LAYOUTS.md
QUICKSTART_UV.md
README.md (original)
RESUMEN_MARKDOWN.md
VARIABLES_PERSONALIZADAS.md
WIZARD.md
```

### Prueba práctica:
```bash
# Verificar estructura de README
grep "^##" README.md | head -20

# Verificar CHANGELOG
grep "^\[" CHANGELOG.md

# Verificar que archivos viejos no existen
ls *.md
# Debería mostrar solo: README.md, CHANGELOG.md, descripcion.md
```

---

## 9. ✅ Commits Descriptivos

### Qué verificar:
```bash
git log --oneline -5
```

**Esperado:**
```
0872611 docs: agregar resumen completo de mejoras implementadas
4eeeaba docs: consolidación completa de documentación en README.md y CHANGELOG.md
492affd feat: mejoras en renderizado y configuraciones de prueba
f5a3000 feat(layouts): agregar layout compact-4col de 4 columnas
86e9fe7 fix: corregir implementación de layouts CSS
```

**Cada commit debe:**
- ✅ Tener prefijo semántico (feat:, docs:, fix:)
- ✅ Descripción clara y concisa
- ✅ Cuerpo del commit con detalles (usar `git show <hash>`)

### Prueba práctica:
```bash
# Ver detalles de un commit
git show 492affd

# Ver estadísticas
git log --stat -3
```

---

## 10. 📋 Cumplimiento con descripcion.md

### Archivo a revisar:
- `descripcion.md` (especificación del proyecto)

### Checklist de verificación:

**Arquitectura:**
- ✅ Estructura de carpetas según especificación
- ✅ Paquete Python instalable con `pyproject.toml`
- ✅ Directorio `templates/` con archivos `.j2`
- ✅ Directorio `i18n/` con archivos de idioma

**Clases Base:**
- ✅ `BaseParser` en `parsers/base.py`
- ✅ `BaseRenderer` en `generators/base.py`
- ✅ Implementaciones: `GiftParser`, `MoodleXMLParser`
- ✅ Implementaciones: `HtmlRenderer`, `PdfRenderer`

**Modelos Pydantic:**
- ✅ `Pregunta` con campos especificados
- ✅ `Opcion` con retroalimentación
- ✅ `PoolConfig` con filtros
- ✅ `SeccionExamen` con layout
- ✅ `DefinicionExamen` con variables

**Funcionalidad:**
- ✅ Parseo XML y GIFT
- ✅ Validación YAML con Pydantic
- ✅ Filtrado por categoría, tipo, etiquetas
- ✅ Mezcla aleatoria con semillas
- ✅ Generación HTML/PDF
- ✅ Internacionalización
- ✅ Logging configurable

### Prueba práctica:
```bash
# Verificar estructura
tree -L 2 generador_examenes/

# Verificar que todo funciona según especificación
python -m generador_examenes --help
```

---

## 📊 Prueba Integral Completa

### Script de prueba completo:

```bash
#!/bin/bash
cd /home/mrtin/dev/arsenal/alucard
source .venv/bin/activate

echo "=== PRUEBA INTEGRAL DE MEJORAS ==="
echo ""

echo "1. Validando configuraciones..."
for config in examenes_prueba/*.yaml; do
    echo "  - $(basename $config)"
    python -m generador_examenes -d "$config" \
        -i bancos/*.xml bancos/*.gift --validate > /dev/null 2>&1
    [ $? -eq 0 ] && echo "    ✓ OK" || echo "    ✗ ERROR"
done
echo ""

echo "2. Generando examen completo..."
python -m generador_examenes -d examenes_prueba/final_completo.yaml \
    -i bancos/*.xml bancos/*.gift -o output -n 2 -f html > /dev/null 2>&1
[ $? -eq 0 ] && echo "  ✓ OK" || echo "  ✗ ERROR"
echo ""

echo "3. Verificando archivos generados..."
[ -f output/examen_tema_01.html ] && echo "  ✓ examen_tema_01.html" || echo "  ✗ ERROR"
[ -f output/examen_tema_02.html ] && echo "  ✓ examen_tema_02.html" || echo "  ✗ ERROR"
[ -f output/clave_tema_01.html ] && echo "  ✓ clave_tema_01.html" || echo "  ✗ ERROR"
[ -f output/clave_tema_02.html ] && echo "  ✓ clave_tema_02.html" || echo "  ✗ ERROR"
echo ""

echo "4. Verificando variables en HTML..."
grep -q "Profesor" output/examen_tema_01.html && echo "  ✓ Variables presentes" || echo "  ✗ ERROR"
echo ""

echo "5. Verificando layouts..."
grep -q "layout-compact-2col" output/examen_tema_01.html && echo "  ✓ Layout 2col" || echo "  ✗ ERROR"
grep -q "layout-compact-4col" output/examen_tema_01.html && echo "  ✓ Layout 4col" || echo "  ✗ ERROR"
grep -q "layout-default" output/examen_tema_01.html && echo "  ✓ Layout default" || echo "  ✗ ERROR"
echo ""

echo "6. Verificando documentación..."
[ -f README.md ] && [ $(wc -l < README.md) -gt 1000 ] && echo "  ✓ README consolidado" || echo "  ✗ ERROR"
[ -f CHANGELOG.md ] && grep -q "5.4.0" CHANGELOG.md && echo "  ✓ CHANGELOG actualizado" || echo "  ✗ ERROR"
[ -d .docs_backup ] && echo "  ✓ Backup existente" || echo "  ✗ ERROR"
echo ""

echo "=== PRUEBA COMPLETADA ==="
```

Guardar como `test_mejoras.sh`, dar permisos y ejecutar:
```bash
chmod +x test_mejoras.sh
./test_mejoras.sh
```

---

## 📝 Checklist Final

Marca cada elemento después de verificarlo:

### Código
- [ ] CSS de impresión optimizado verificado
- [ ] Logging mejorado funcionando
- [ ] Variables personalizadas evaluándose
- [ ] Wizard ejecutable
- [ ] Categorías filtrando correctamente
- [ ] Layout 4col implementado
- [ ] 5 configuraciones validadas

### Generación
- [ ] Exámenes HTML generados correctamente
- [ ] Claves de profesor generadas
- [ ] Múltiples temas con diferentes semillas
- [ ] Variables presentes en HTML
- [ ] Layouts aplicados correctamente

### Documentación
- [ ] README.md consolidado y completo
- [ ] CHANGELOG.md actualizado
- [ ] Archivos antiguos eliminados
- [ ] Backup en .docs_backup
- [ ] RESUMEN_MEJORAS.md creado

### Git
- [ ] Commits descriptivos realizados
- [ ] Mensajes de commit claros
- [ ] Historial limpio y organizado

---

**¡Todo listo para producción!** ✨
