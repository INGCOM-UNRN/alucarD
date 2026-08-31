---
title: "Manual de Referencia: alucarD"
subtitle: "Alucard — Generador de Exámenes Impresos, Variantes Anti-Copia y Plantillas OMR"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-alucard)=
# Alucard — Generador de Exámenes Impresos, Variantes Anti-Copia y Plantillas OMR

````{abstract}
**Rol en el ecosistema:** Generación y maquetación de exámenes presenciales con Typst, síntesis de variantes permutadas y lectura óptica OMR.
````

---

(manual-alucard-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`alucarD`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-alucard-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `alucard`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
alucard doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-alucard-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `alucard`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `alucard render <examen.yaml>` | Compila el examen a PDF listo para impresión usando Typst. |
| `alucard randomize <examen.yaml> -n 4` | Genera 4 variantes/temas con opciones y ejercicios permutados. |
| `alucard omr-grid <examen.yaml>` | Genera la grilla de lectura óptica OMR para corrección rápida. |
| `alucard gift-lint <preguntas.gift>` | Audita la sintaxis y completitud de bancos de preguntas en formato GIFT. |
| `alucard spellcheck <examen.yaml>` | Verifica ortografía y gramática de enunciados con LanguageTool. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-alucard-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// Pregunta de seguimiento de código para examen
int vec[] = {10, 20, 30, 40};
int *p = vec + 1;
*p += 5;
*(p + 2) -= 10;
printf("%d, %d\n", vec[1], vec[3]); // ¿Qué valor imprime?
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
alucard render <examen.yaml>
````

### Salida Obtenida en Consola

````{code-block} text
[✓] Compilando parcial_tema_1.typ -> parcial_tema_1.pdf (Typst 0.11)
[✓] Generada variante Tema 2 (semilla: 0xDEADBEEF) -> parcial_tema_2.pdf
[✓] Generada hoja de lectura óptica OMR de 20 preguntas -> omr_respuestas.pdf
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-alucard-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`alucarD`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Generación de Parcial con 3 Temas
Definir un archivo `parcial.yaml` y compilar 3 temas con opciones permutadas.

**Instrucción de ejecución:**
```bash
alucard randomize parcial.yaml -n 3 -o ./pdf_temas
```
````

````{solution} Desafío 1
```bash
alucard randomize parcial.yaml -n 3 -o ./pdf_temas
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Auditoría de Banco GIFT
Validar que `preguntas.gift` no tenga opciones correctas faltantes.

**Instrucción de ejecución:**
```bash
alucard gift-lint preguntas.gift --fix
```
````

````{solution} Desafío 2
```bash
alucard gift-lint preguntas.gift --fix
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Corrección Ortográfica con LanguageTool
Verificar enunciados docentes antes de imprimir el examen.

**Instrucción de ejecución:**
```bash
alucard spellcheck parcial.yaml --lang es-AR
```
````

````{solution} Desafío 3
```bash
alucard spellcheck parcial.yaml --lang es-AR
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-alucard-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `alucarD` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-alucard:
	@echo "=== Ejecutando verificación con alucarD ==="
	alucard check src/ include/

.PHONY: check-alucard
````

Ejecutá `make check-alucard` antes de cada commit para asegurar que tu código conserve el estado de aprobación.
