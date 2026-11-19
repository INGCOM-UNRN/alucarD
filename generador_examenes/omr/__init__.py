"""Exámenes con carátula OMR: la especificación de `OMR_SPEC.md`, con `alucard omr` como CLI.

- `config`: `exam.yaml` (rúbrica, curva de notas, variantes) y sus reglas de validación (§3).
- `notas`: la curva por tramos, el redondeo sin cruzar umbrales y la tabla de verificación (§5).
- `layout`: el manifiesto geométrico `omr-layout/2` y su esquema (§4).
- `qr`: `hmac_key`, el QR de cada carátula, el de pie de página y el de configuración docente (§6).
- `nomina`: los inscriptos, sus `student_id` y variantes, y `roster_<exam_id>.csv` (§3.2, §8).
- `lote`: el lote completo de `alucard omr build` (§8).
- `geometria`: `alucard omr verify-geometry`, que mide en el PDF lo que dibujó Typst (§11.2).
"""
