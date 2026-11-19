# SPEC.md — Generador de Exámenes con Carátula OMR (v2)

Especificación técnica completa del **subsistema generador de exámenes** (motor
Python + plantilla Typst), diseñado como única fuente de verdad geométrica y
criptográfica del sistema de exámenes con carátula OMR y la app Android
**Escáner OMR**.

---

## 1. Propósito y principios de diseño

El generador transforma una definición de examen (rúbrica, curva de notas y
banco de preguntas) y una nómina de inscriptos en un lote listo para imprimir y
escanear.

1. **Única fuente de verdad geométrica:** el motor Python genera
   `layout_manifest.json` con coordenadas físicas en milímetros; la plantilla
   Typst lee ese mismo archivo con `json()` para dibujar fiduciales, burbujas y
   etiquetas. Ni Typst ni la app Android hardcodean coordenadas.
2. **Privacidad por diseño:** el QR de cada estudiante jamás contiene DNI,
   correo ni legajo. Solo transporta un `STUDENT_ID` interno asignado por el
   generador; la correspondencia con la persona vive únicamente en
   `roster_<exam_id>.csv`.
3. **Integridad verificable:** cada carátula lleva una suma de control `CHK`
   (HMAC-SHA256 truncado) calculada con una clave secreta por examen
   (`hmac_key`), y el manifiesto se versiona y registra mediante su `sha256`.
4. **Cero fricción operativa:** el generador emite además un **QR de
   configuración exclusivo para docentes** que inicializa la sesión en la app
   Android (identidad del examen, `hmac_key`, manifiesto/rúbrica y curva de
   notas) en un único escaneo.

---

## 2. Arquitectura del generador

Se extiende un pipeline desacoplado de dos etapas:

| Componente               | Tecnología                                                        | Responsabilidades                                                                                                                                                                                                                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Motor de compilación** | Python 3.11+ (`segno`, `pyyaml`, `jsonschema`, `pypdf` / `typst`) | Validar configuración del examen y curva de notas; asignar `student_id` internos y variantes; generar `hmac_key`; construir y validar `layout_manifest.json`; emitir QR de estudiantes (SVG alfanumérico) y QR de configuración docente; imprimir vista previa de curva en consola; invocar Typst y empaquetar artefactos del lote. |
| **Maquetador vectorial** | Typst 0.12+                                                       | Leer `layout_manifest.json` mediante `json()`; renderizar en A4 exacto la franja de cabecera OMR (fiduciales ArUco SVG, burbujas vectoriales, etiquetas fuera de ROI, QR del estudiante y texto legible de respaldo); componer el cuerpo del examen debajo de la franja fija y agregar QR de pie de página en exámenes multi-hoja.  |

---

## 3. Entradas del generador

### 3.1 Archivo de configuración del examen (`exam.yaml` o `exam.json`)

```yaml
exam_id: "PROG1-2026-P1" # [A-Z0-9-], máx. 16 caracteres
title: "Programación I — Parcial 1"
layout_id: "OMR5E" # [A-Z0-9-]
layout_version: 7 # entero >= 1; incrementar ante cualquier cambio geométrico
variants: ["A", "B"] # letras mayúsculas individuales [A-Z]
cloud_sync_default: false # sugerencia opt-in para la app

grade_scale:
  min: 1.0
  max: 10.0
  decimals: 1 # 0, 1 o 2
  step: null # opcional: 0.5 o 0.25 (si decimals: 0 y step: 0.5 -> medio punto)
  rounding: "half_up" # "half_up" | "half_even"
  match_tolerance: 0 # unidades de la última cifra toleradas entre marcada y calculada

grade_map:
  type: "piecewise_log"
  pass_pct: 60.0 # obligatorio en [50.0, 70.0]
  pass_grade: 4.0 # fijo en 4.0
  promo_pct: 80.0 # opcional (null si no hay promoción); pass_pct < promo_pct < 100
  promo_grade: 7.0 # obligatorio si promo_pct != null; estrictamente en (4.0, max)
  curve_k: 3.0 # [-10.0, +10.0]; >0 generosa, 0 lineal, <0 exigente
  fail_curve: "linear" # tramo [0%, pass_pct) lineal desde min hasta < pass_grade

rubric:
  - id: "ej1"
    label: "Ejercicio 1"
    max_points: 2.5
    levels: 5 # 2 a 11 posiciones (0 siempre es burbuja explícita)
  - id: "ej2"
    label: "Ejercicio 2"
    max_points: 2.5
    levels: 5
  - id: "ej3"
    label: "Ejercicio 3 (V/F)"
    max_points: 1.0
    levels: 2
    labels: ["✗", "✓"] # opcional; por defecto porcentajes redondeados
  - id: "ej4"
    label: "Ejercicio 4"
    max_points: 2.0
    levels: 5
  - id: "ej5"
    label: "Ejercicio 5"
    max_points: 2.0
    levels: 11
```

### 3.2 Nómina de entrada (`inscriptos.csv`)

CSV UTF-8 con columnas mínimas `legajo,apellido,nombre` (y opcionalmente
`student_id` y `variante` si ya fueron preasignados). Si no trae `student_id`,
el motor asigna códigos secuenciales internos (`C001`, `C002`, …, `C999`) sin
correlación derivable con el DNI.

### 3.3 Reglas de validación obligatorias al iniciar

El motor **debe abortar con código de salida ≠ 0** si falla cualquiera de estas
reglas:

- `exam_id` no cumple `^[A-Z0-9-]{1,16}$`.
- `variants` contiene valores que no cumplen `^[A-Z]$`.
- `grade_scale.decimals` ∉ `{0, 1, 2}`, `min >= max` o `match_tolerance < 0`.
- `grade_map.pass_pct` fuera de `[50.0, 70.0]`.
- `promo_pct` definido y `promo_pct <= pass_pct` o `promo_pct >= 100.0`.
- `promo_pct` definido y `promo_grade` ausente o fuera de
  `(pass_grade, grade_scale.max)`.
- `curve_k` fuera de `[-10.0, +10.0]`.
- Algún ejercicio tiene `levels` fuera de `[2, 11]`, `max_points <= 0`, o `id`
  duplicado.

---

## 4. Contrato geométrico y `layout_manifest.json` (`omr-layout/2`)

### 4.1 Fiduciales ArUco `DICT_4X4_50`

El marco canónico queda definido por los centroides de 4 marcadores ArUco
`DICT_4X4_50` impresos en **negro puro K = 100 % (`#000000`)** como rectángulos
vectoriales (nunca bitmaps reescalados):

| ID  | Posición en el marco        | Centroide (mm)             | Matriz interior 4×4 (fila mayor, `1` = blanco, `0` = negro) | Máscara 16 bits         |
| --- | --------------------------- | -------------------------- | ----------------------------------------------------------- | ----------------------- |
| `0` | Superior izquierda (origen) | `(0.0, 0.0)`               | `1011 / 0101 / 0011 / 0010`                                 | `0b1011_0101_0011_0010` |
| `1` | Superior derecha            | `(frame_mm.w, 0.0)`        | `0000 / 1111 / 1001 / 1010`                                 | `0b0000_1111_1001_1010` |
| `2` | Inferior derecha            | `(frame_mm.w, frame_mm.h)` | `0011 / 0011 / 0001 / 1000`                                 | `0b0011_0011_0001_1000` |
| `3` | Inferior izquierda          | `(0.0, frame_mm.h)`        | `1001 / 1001 / 0100 / 0111`                                 | `0b1001_1001_0100_0111` |

- **Estructura 6×6:** cada marcador consta de un borde negro continuo de 1 celda
  rodeando la matriz interior 4×4.
- **Tamaño:** `marker_mm = 10.0` (celda ≈ 1,67 mm; mínimo absoluto permitido 8,0
  mm).
- **Márgenes de seguridad:** centroides a ≥ 12 mm de cada borde del papel A4
  (210 × 297 mm) para resistir "Ajustar a página" y márgenes no imprimibles;
  zona de silencio blanca ≥ 4 mm alrededor de cada marcador y del QR.

### 4.2 Esquema del manifiesto `omr-layout/2`

Todas las coordenadas (`x_mm`, `y_mm`, `x0_mm`, `y0_mm`) se expresan en
**milímetros desde el centroide del marcador 0**. El aspecto del lienzo canónico
se deriva como `(frame_mm.w * px_per_mm) × (frame_mm.h * px_per_mm)`.

```json
{
  "schema": "omr-layout/2",
  "layout_id": "OMR5E",
  "version": 7,
  "frame_mm": { "w": 180.0, "h": 74.0 },
  "marker_mm": 10.0,
  "px_per_mm": 10,
  "bubble_diameter_mm": 5.0,
  "grade_scale": {
    "min": 1.0,
    "max": 10.0,
    "decimals": 1,
    "step": null,
    "rounding": "half_up",
    "match_tolerance": 0
  },
  "grade_map": {
    "type": "piecewise_log",
    "pass_pct": 60.0,
    "pass_grade": 4.0,
    "promo_pct": 80.0,
    "promo_grade": 7.0,
    "curve_k": 3.0,
    "fail_curve": "linear"
  },
  "fields": [
    {
      "id": "ej1",
      "label": "Ejercicio 1",
      "type": "single_choice",
      "required": true,
      "max_points": 2.5,
      "levels": 5,
      "options": [
        { "step": 0, "label": "0", "x_mm": 32.0, "y_mm": 12.0 },
        { "step": 1, "label": "25", "x_mm": 40.0, "y_mm": 12.0 },
        { "step": 2, "label": "50", "x_mm": 48.0, "y_mm": 12.0 },
        { "step": 3, "label": "75", "x_mm": 56.0, "y_mm": 12.0 },
        { "step": 4, "label": "100", "x_mm": 64.0, "y_mm": 12.0 }
      ]
    },
    {
      "id": "nota_final",
      "label": "Nota final",
      "type": "decimal_digits",
      "required": true,
      "role": "final_grade",
      "digits": [
        {
          "place": 1.0,
          "start": 1,
          "count": 10,
          "x0_mm": 32.0,
          "y0_mm": 56.0,
          "step_mm": 8.0,
          "axis": "x"
        },
        {
          "place": 0.1,
          "start": 0,
          "count": 10,
          "x0_mm": 32.0,
          "y0_mm": 64.0,
          "step_mm": 8.0,
          "axis": "x"
        }
      ]
    },
    {
      "id": "ausente",
      "label": "Ausente",
      "type": "flag",
      "required": false,
      "x_mm": 162.0,
      "y_mm": 64.0
    }
  ]
}
```

#### Reglas de `decimal_digits` según `grade_scale`

| Configuración             | Filas `digits` emitidas                                                            |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `decimals: 0, step: null` | 1 fila: `place: 1.0, start: 1, count: 10`                                          |
| `decimals: 0, step: 0.5`  | 2 filas: unidades (`1..10`) + medio punto (`place: 0.1, count: 2, values: [0, 5]`) |
| `decimals: 1`             | 2 filas: unidades (`1..10`) + décimas (`place: 0.1, start: 0, count: 10`)          |
| `decimals: 2`             | 3 filas: unidades (`1..10`) + décimas (`0.1`) + centésimas (`0.01`)                |

#### Layout determinístico estándar (compatible con QR compacto `OMRCFG/2`)

Cuando se usa la disposición estándar por filas:

- `frame_mm.w = 180.0`, `marker_mm = 10.0`, `px_per_mm = 10`,
  `bubble_diameter_mm = 5.0`.
- Primera fila de ejercicio en `y_mm = 12.0`, inicio horizontal `x_mm = 32.0`,
  paso entre centros `step_mm = 8.0` (diámetro 5 mm + separación entre bordes 3
  mm).
- Cada ejercicio agrega `+8.0 mm` en `y`.
- Separación visual de `+4.0 mm` antes de las filas de `nota_final` (cada fila
  de dígitos agrega `+8.0 mm`).
- Flag `ausente` en `x_mm = 162.0`, `y_mm = max(24.0, last_row_y)`.
- Altura del marco `frame_mm.h = max(55.0, current_y + 6.0)`.
- Si el generador emplea agrupaciones horizontales o coordenadas personalizadas
  distintas de esta regla, **debe** emitir el QR de configuración en formato
  `OMRCFG2:` (manifiesto completo comprimido) y nunca en formato compacto
  `OMRCFG/2`.

---

## 5. Cálculo de notas y vista previa de curva

El generador implementa exactamente la misma matemática que la app Android para
imprimir en consola la tabla de verificación antes de compilar los PDF:

1. **Puntaje por ejercicio:** fracción exacta
   `step / (levels - 1) * max_points`, sin redondeo intermedio.
2. **Porcentaje global:**
   $p = 100 \cdot \sum \text{pts} / \sum \text{max\_points} \in [0, 100]$.
3. **Curva por tramos:**
   - **Desaprobados** ($p < \text{pass\_pct}$): tramo lineal de `min` (0 %) a
     `pass_grade` (`pass_pct`).
   - **Aprobados / Promocionados**: en cada tramo $[p_0, p_1] \to [g_0, g_1]$
     con $t = (p - p_0)/(p_1 - p_0)$:
     $$g = g_0 + (g_1 - g_0)\,f(t), \qquad f(t) = \begin{cases} \dfrac{\ln(1 + k t)}{\ln(1 + k)} & k > 0 \\ t & k = 0 \\ \dfrac{(1 + |k|)^t - 1}{|k|} & k < 0 \end{cases}$$
4. **Regla de no cruce de umbrales:** el redondeo jamás cruza un umbral. Si
   $p < \text{pass\_pct}$ y la nota redondeada alcanza `pass_grade`, se recorta
   a `pass_grade - unit` (p. ej. `3,9` con 1 decimal, `3` sin decimales);
   análogo para `promo_pct` respecto de `promo_grade`. La condición
   (`DESAPROBADO`, `APROBADO`, `PROMOCIONADO`, `AUSENTE`) se determina siempre
   por el porcentaje.

Antes de escribir PDFs, el CLI imprime la tabla para `0%`, `30%`,
`pass_pct - 0.1%`, `pass_pct`, punto medio, `promo_pct - 0.1%`, `promo_pct`,
punto medio superior y `100%`.

---

## 6. Códigos QR emitidos por el generador

### 6.1 Clave secreta por examen (`hmac_key`)

- Generada con entropía criptográfica (`secrets.token_bytes(16)`), codificada en
  **Base32 RFC 4648** sin `=` (26 caracteres alfanuméricos `A-Z2-7`).
- Única por examen. No se versiona en Git ni se imprime en las hojas de
  estudiantes.

### 6.2 QR de carátula por estudiante (página 1)

Formato estricto en **modo alfanumérico QR** (`0-9`, `A-Z`, espacio,
`$%*+-./:`):

```text
V/EXAM_ID/STUDENT_ID/VARIANT/LAYOUT_ID:VER/CHK
1/PROG1-2026-P1/C017/A/OMR5E:7/K7QF
```

Cálculo de `CHK`:

```python
import base64, hashlib, hmac

def compute_chk(body_without_chk: str, hmac_key: str) -> str:
    digest = hmac.new(
        hmac_key.encode("utf-8"),
        body_without_chk.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b32encode(digest).decode("ascii")[:4]
```

- **Parámetros QR:** versión objetivo **3**, corrección **Q** (capacidad 47
  caracteres alfanuméricos), módulo ≥ 0,5 mm (~15 mm de lado + ≥ 4 mm de zona de
  silencio), negro puro K = 100 %.
- **Respaldo legible:** imprimir `Apellido, Nombre` y `STUDENT_ID` en texto
  plano junto al QR para permitir la asignación `QR_MANUAL` si el código se
  daña.
- **Exámenes multi-hoja:** en páginas 2..N imprimir en el pie un QR compacto
  `EXAM_ID/STUDENT_ID/P<n>` para reagrupar hojas sueltas.

### 6.3 QR de configuración del escáner (uso exclusivo docente)

Permite inicializar la sesión en la app Android sin copiar archivos JSON ni
tipear `hmac_key`.

#### Formato principal: `OMRCFG2:` (JSON completo comprimido, recomendado)

```text
OMRCFG2:<base64url_sin_padding(zlib.compress(json_utf8, level=9))>
```

Sobre JSON (`omr-exam-config/2`):

```json
{
  "schema": "omr-exam-config/2",
  "exam_id": "PROG1-2026-P1",
  "title": "Programación I — Parcial 1",
  "hmac_key": "K7QFMZ2V9A...",
  "cloud_sync": false,
  "manifest": { "...objeto layout_manifest.json completo (omr-layout/2)..." }
}
```

Referencia en Python:

```python
import base64, json, zlib, segno

def make_config_qr_compressed(exam_id: str, title: str, hmac_key: str, manifest: dict, cloud_sync: bool = False) -> str:
    envelope = {
        "schema": "omr-exam-config/2",
        "exam_id": exam_id,
        "title": title,
        "hmac_key": hmac_key,
        "cloud_sync": cloud_sync,
        "manifest": manifest,
    }
    raw = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    b64 = base64.urlsafe_b64encode(zlib.compress(raw, level=9)).rstrip(b"=").decode("ascii")
    return f"OMRCFG2:{b64}"

def save_config_qr_svg(payload: str, path: str) -> None:
    segno.make(payload, error="m").save(path, scale=4, border=4, dark="#000000", light="#ffffff")
```

- **Tamaño típico:** ~550–700 caracteres → QR versión 14–16 nivel **M**,
  imprimir a ≥ 40 mm de lado (ideal 55–65 mm en la hoja docente).

#### Formato alternativo compacto: `OMRCFG/2` (solo layout estándar)

```text
OMRCFG/2/<EXAM_ID>/<LAYOUT_ID>:<VER>/<HMAC_KEY>/<PASS>:<PROMO>:<PROMO_GRADE>:<K>/<DEC>:<STEP>:<TOL>/<EX_SPEC>/<TITULO_URL>
```

- Si no hay promoción: `<PROMO>:<PROMO_GRADE>` = `NONE:0`.
- `<STEP>` va vacío si `grade_scale.step` es `null`.
- `<EX_SPEC>`: lista separada por `,` con `id:max_points:levels` (etiqueta
  opcional en 4.º subcampo codificado en URL).
- `<TITULO_URL>`: título codificado con `urllib.parse.quote_plus`.
- La app Android también acepta la variante URI
  `omrcfg://v2?exam_id=...&title=...&hmac_key=...&layout=...&pass=...&promo=...&k=...&dec=...&ex=...`
  y JSON plano.

---

## 7. Especificación de diseño gráfico en Typst

- **Tamaño de página:** A4 exacto (`210mm × 297mm`), sin márgenes de escala.
  Instrucción impresa: _"Imprimir al 100 % / Tamaño real"_.
- **Franja de cabecera fija (página 1 únicamente):** alto `frame_mm.h + 24mm`
  (79 mm mínimo en el layout estándar de 55 mm; crece 8 mm por fila adicional).
  El enunciado comienza debajo de una línea divisoria y nunca invade la franja.
- **Rotulado:** leyenda discreta _"Zona reservada para el docente — no escribir
  · Rellenar el círculo con lapicera, no tildar ni cruzar"_ en gris `#666666`
  fuera de las ROIs.
- **Burbujas:**
  - Diámetro `5.0 mm`, separación entre bordes ≥ `3.0 mm` (`step_mm >= 8.0`).
  - Contorno vectorial `0.5 pt`, color `#999999` (gris 60 %; la app mide solo el
    disco interior `0.7r`).
  - Etiqueta de valor (`0`, `25`, `50`, `75`, `100`, `✗`, `✓`, o dígito) de
    `7 pt` ubicada **por encima del borde superior de la burbuja**, nunca dentro
    del círculo ni invadiendo el anillo `1.3r..1.6r` en la medida de lo posible.
  - Etiqueta de fila a la izquierda (`Ej. 1 (2,5)`), fuera del área de burbujas
    (`x < 28 mm`).
- **Colorimetría:** fiduciales ArUco y QR en negro real K = 100 %
  (`cmyk(0%, 0%, 0%, 100%)` o `#000000` puro).

---

## 8. Artefactos de salida por lote

El comando de generación escribe en `dist/<exam_id>/`:

| Archivo                              | Descripción                                                                                                                                           | Distribución / Privacidad                                                                 |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `examenes_<exam_id>.pdf`             | Un examen completo por estudiante (página 1 con carátula OMR personalizada + páginas de enunciado).                                                   | Imprenta / Aula. Sin DNI en QR.                                                           |
| `roster_<exam_id>.csv`               | `student_id,legajo,apellido,nombre,variante` en UTF-8 con BOM. Único vínculo entre `student_id` y la persona.                                         | Solo docente (importar en la app). **No imprimir ni compartir.**                          |
| `layout_<layout_id>_v<version>.json` | Manifiesto geométrico y de rúbrica (`omr-layout/2`) + `layout_<layout_id>_v<version>.sha256`.                                                         | Cátedra / Repositorio de layouts.                                                         |
| `config_qr_<exam_id>.pdf` y `.svg`   | Hoja docente con el QR de configuración (`OMRCFG2:` + respaldo `OMRCFG/2`), resumen de la rúbrica, `sha256` del manifiesto y tabla porcentaje → nota. | **Uso exclusivo docente.** Contiene `hmac_key`; destruir si se imprime al cerrar el acta. |
| `layout_test_<layout_id>.pdf`        | Hoja de calibración con la cabecera y burbujas pre-rellenas al `0 %`, `25 %`, `50 %` y `100 %` para calibrar umbrales por impresora.                  | Imprenta / Calibración (una copia por impresora).                                         |

---

## 9. Interfaz de línea de comandos (CLI) recomendada

```bash
omr-gen build \
  --config exam.yaml \
  --roster inscriptos.csv \
  --questions banco_preguntas/ \
  --out dist/PROG1-2026-P1/ \
  --qr-config-mode compressed   # compressed (OMRCFG2:, default) | compact (OMRCFG/2)

# Subcomandos auxiliares
omr-gen validate --config exam.yaml
omr-gen preview-curve --config exam.yaml
omr-gen calibration-sheet --manifest dist/PROG1-2026-P1/layout_OMR5E_v7.json --out layout_test.pdf
omr-gen verify-geometry --pdf dist/PROG1-2026-P1/examenes_PROG1-2026-P1.pdf --manifest dist/PROG1-2026-P1/layout_OMR5E_v7.json
```

---

## 10. Seguridad, privacidad y cumplimiento (Ley 25.326)

- **Separación de identidad:** `examenes_<exam_id>.pdf` contiene el nombre
  legible para entregar al estudiante, pero el QR codifica solo `student_id`.
  `roster_<exam_id>.csv` se mantiene fuera de carpetas públicas y se elimina del
  teléfono al cerrar la sesión de examen.
- **Protección de `hmac_key`:** `config_qr_<exam_id>.pdf` no contiene datos
  personales de estudiantes, pero sí `hmac_key`. Nunca debe imprimirse junto con
  el mazo de exámenes ni subirse a repositorios compartidos con estudiantes.
- **Trazabilidad:** el generador registra el `sha256` del manifiesto en
  `config_qr_<exam_id>.pdf` y en un log de compilación para auditar
  correspondencia con las exportaciones CSV y PDF de evidencia de la app
  Android.

---

## 11. Pruebas de regresión y criterios de aceptación

Todo cambio en la plantilla Typst o en el motor Python debe pasar en CI antes de
emitir exámenes reales:

1. **Validación de esquema:** `layout_manifest.json` pasa JSON Schema
   `omr-layout/2` y las reglas de rango de `grade_scale` y `grade_map`.
2. **Alineación geométrica (< 0,3 mm):** `omr-gen verify-geometry` rasteriza la
   página 1 del PDF generado a 300 DPI, detecta los 4 fiduciales ArUco,
   rectifica el lienzo canónico y verifica que el centro de cada contorno de
   burbuja dibujado por Typst coincida con `(x_mm, y_mm)` del manifiesto con
   error < **0,3 mm** (3 px a 10 px/mm).
3. **Interoperabilidad de QR:**
   - Todos los QR de estudiantes se decodifican en modo alfanumérico (`<= 47`
     chars, versión ≤ 3-Q) y pasan la verificación `CHK` con la `hmac_key` del
     examen.
   - El QR de configuración (`OMRCFG2:` y `OMRCFG/2`) se decodifica y
     reconstruye el mismo `layout_manifest.json` y parámetros de curva que
     consume la app Android.
4. **Corpus sintético de integración:** generar carátulas con marcas simuladas
   (relleno total en tintas azul/roja/negra, relleno parcial 25 %/50 %, doble
   marca, ausente) más deformación de perspectiva, sombra y ruido JPEG, y
   ejecutar el módulo OMR JVM de la app Android exigiendo **0 errores
   silenciosos**.
