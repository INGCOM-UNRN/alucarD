"""Plantillas del sintetizador: cada una arma un snippet C con parámetros al azar y verifica su respuesta.

Una plantilla es una función ``(rng) -> SnippetGenerado`` registrada en `PLANTILLAS`
con su descripción. La respuesta correcta nunca se calcula a mano:

- las de traza se compilan y ejecutan (`compilar_y_ejecutar`);
- las de comportamiento indefinido se verifican con los avisos de gcc
  (`diagnosticos`), que tienen que señalar el defecto, y sus variantes correctas
  tienen que compilar sin avisos y se ejecutan;
- las de memoria cuentan lo que queda sin liberar (`memoria_sin_liberar`).

Los distractores van del más al menos verosímil: el sintetizador se queda con
los primeros que necesita según la cantidad de opciones pedida.
"""

from __future__ import annotations

import functools
import hashlib
import random
from dataclasses import dataclass, field

from .sandbox import compilar_y_ejecutar, diagnosticos, memoria_sin_liberar

ENUNCIADO_TRAZA = "¿Qué imprime por pantalla el siguiente programa?"
ENUNCIADO_DIAGNOSTICO = "¿Qué ocurre al compilar y ejecutar el siguiente programa?"

# Avisos de gcc que señalan un defecto de memoria (una variante correcta no puede tener ninguno).
_DEFECTOS = {
    "uninitialized", "maybe-uninitialized", "return-local-addr", "dangling-pointer", "use-after-free",
    "analyzer-use-of-uninitialized-value", "analyzer-use-after-free", "analyzer-double-free",
    "analyzer-malloc-leak", "analyzer-null-dereference", "analyzer-possible-null-dereference",
}


@dataclass
class SnippetGenerado:
    """Un snippet C verificado listo para volverse pregunta."""

    plantilla: str
    titulo: str
    enunciado: str
    codigo: str
    salida_correcta: str
    distractores: list[str] = field(default_factory=list)
    explicacion: str = ""

    @property
    def opciones(self) -> list[str]:
        """Opciones (correcta primero) sin duplicados."""
        vistos: set[str] = {self.salida_correcta}
        opciones = [self.salida_correcta]
        for d in self.distractores:
            if d not in vistos:
                vistos.add(d)
                opciones.append(d)
        return opciones


def _huella(codigo: str) -> str:
    """Seis caracteres del código, para que el título distinga variantes sin revelar la respuesta."""
    return hashlib.sha1(codigo.encode("utf-8")).hexdigest()[:6]


def _ejecutar(codigo: str, flags_extra: list[str] | None = None) -> str:
    ok, salida = compilar_y_ejecutar(codigo, flags_extra=flags_extra)
    if not ok:
        raise RuntimeError(salida)
    return salida


def _programa(cuerpo: list[str], antes: str = "", includes: tuple[str, ...] = ("stdio.h",)) -> str:
    """Un programa con `main` que ejecuta las líneas de `cuerpo` (y `antes` arriba de `main`)."""
    cabecera = "".join(f"#include <{h}>\n" for h in includes)
    previo = f"\n{antes.strip()}\n" if antes.strip() else ""
    lineas = "".join(f"    {linea}\n" for linea in cuerpo)
    return f"{cabecera}{previo}\nint main(void) {{\n{lineas}    return 0;\n}}\n"


@functools.lru_cache(maxsize=1)
def tamanos_plataforma() -> tuple[int, int]:
    """``(sizeof(int), sizeof(int *))`` de la plataforma donde se verifica."""
    salida = _ejecutar(_programa(['printf("%zu %zu\\n", sizeof(int), sizeof(int *));']))
    entero, puntero = salida.split()
    return int(entero), int(puntero)


def _verificar_defecto(codigo: str, esperados: set[str]) -> None:
    encontrados = diagnosticos(codigo)
    if not encontrados & esperados:
        raise RuntimeError(f"gcc no señaló el defecto esperado ({', '.join(sorted(esperados))}); "
                           f"avisos: {', '.join(sorted(encontrados)) or 'ninguno'}")


def _verificar_correcto(codigo: str) -> str:
    defectos = diagnosticos(codigo) & _DEFECTOS
    if defectos:
        raise RuntimeError(f"la variante correcta tiene avisos de gcc: {', '.join(sorted(defectos))}")
    return _ejecutar(codigo)


# ---------------------------------------------------------------------------
# Trazas
# ---------------------------------------------------------------------------

def _plantilla_precedencia(rng: random.Random) -> SnippetGenerado:
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 5)

    variantes = {
        "a + b * c": (f"({a} + {b}) * {c}", f"{a} * {b} + {c}", f"{a*b + c*a}"),
        "(a + b) * c": (f"{a} + {b} * {c}", f"{a} * {b} + {c}", f"{a} + {b} + {c}"),
        "a - b - c": (f"{a} - ({b} - {c})", f"{b} - {a} - {c}", f"{a} - {b} + {c}"),
        "a * b % c": (f"{a} * ({b} % {c})", f"{a} % {b} * {c}", f"({a} * {b}) // {c}"),
    }
    expr = rng.choice(list(variantes))
    codigo = _programa([f"int a = {a}, b = {b}, c = {c};", f'printf("%d\\n", {expr});'])
    salida = _ejecutar(codigo)

    distractores = [str(eval(candidato, {"__builtins__": {}})) for candidato in variantes[expr]]
    return SnippetGenerado(
        plantilla="precedencia",
        titulo=f"Precedencia de operadores ({a}, {b}, {c})",
        enunciado=ENUNCIADO_TRAZA,
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion=f"`{expr}` aplica la precedencia estándar de C: `*`, `/` y `%` antes que `+` y `-`, "
                    "y asociatividad izquierda a derecha entre operadores de igual nivel.",
    )


def _plantilla_traza_punteros(rng: random.Random) -> SnippetGenerado:
    valores = [rng.randint(10, 99) for _ in range(4)]
    k = rng.randint(1, len(valores) - 1)
    codigo = _programa([
        f"int v[] = {{{', '.join(map(str, valores))}}};",
        "int *p = v;",
        f"p += {k};",
        'printf("%d\\n", *p);',
    ])
    salida = _ejecutar(codigo)

    distractores = [str(valores[0]), str(valores[k - 1]), str(valores[min(k + 1, len(valores) - 1)]),
                    str(valores[0] + k), str(k)]
    return SnippetGenerado(
        plantilla="traza-punteros",
        titulo=f"Aritmética de punteros (avanza {k})",
        enunciado=ENUNCIADO_TRAZA,
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="`p += k` mueve el puntero `k` posiciones dentro del arreglo; "
                    "`*p` desreferencia esa posición (`v[" + str(k) + "]`).",
    )


def _plantilla_recursion(rng: random.Random) -> SnippetGenerado:
    n = rng.randint(3, 8)
    codigo = _programa([f'printf("%d\\n", suma({n}));'], antes=(
        "int suma(int n) {\n"
        "    if (n <= 0) {\n"
        "        return 0;\n"
        "    }\n"
        "    return n + suma(n - 1);\n"
        "}"
    ))
    salida = _ejecutar(codigo)

    real = sum(range(1, n + 1))
    distractores = [str(real - n), str(n * n), str(real + n), str(n), str(real - 1)]
    return SnippetGenerado(
        plantilla="recursion",
        titulo=f"Recursión: suma de 1 a {n}",
        enunciado=ENUNCIADO_TRAZA,
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="La recursión acumula `n + suma(n-1)` hasta el caso base `suma(0) = 0`.",
    )


def _plantilla_incrementos(rng: random.Random) -> SnippetGenerado:
    i = rng.randint(0, 5)
    codigo = _programa([
        f"int i = {i};",
        'printf("%d ", i++);',
        'printf("%d ", i);',
        'printf("%d\\n", ++i);',
    ])
    salida = _ejecutar(codigo)

    distractores = [f"{i+1} {i+1} {i+2}", f"{i} {i+1} {i+1}", f"{i} {i} {i+1}",
                    f"{i+1} {i+1} {i+1}", f"{i} {i+2} {i+2}", f"{i+1} {i+2} {i+3}"]
    return SnippetGenerado(
        plantilla="incrementos",
        titulo=f"Post-incremento vs pre-incremento (i = {i})",
        enunciado=ENUNCIADO_TRAZA,
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="`i++` entrega el valor viejo y luego incrementa; `++i` incrementa primero y entrega el valor nuevo.",
    )


def _plantilla_array_decay(rng: random.Random) -> SnippetGenerado:
    entero, puntero = tamanos_plataforma()
    n = rng.randint(3, 9)
    if n * entero == puntero:  # el tamaño del arreglo no se distinguiría del de un puntero
        n += 1
    total = n * entero
    datos = f"int datos[{n}] = {{{', '.join(str(rng.randint(1, 99)) for _ in range(n))}}};"
    variante = rng.choice(["contar", "puntero", "parametro", "expresion"])

    if variante == "contar":
        antes = "size_t contar(int v[]) {\n    return sizeof(v) / sizeof(v[0]);\n}"
        cuerpo = [datos, 'printf("%zu %zu\\n", sizeof(datos) / sizeof(datos[0]), contar(datos));']
        en_funcion = puntero // entero
        distractores = [f"{n} {n}", f"{en_funcion} {en_funcion}", f"{n} {puntero}", f"{total} {en_funcion}", f"{n} 1"]
        explicacion = (f"En `main`, `datos` es un arreglo: `sizeof(datos)` vale {total} y la división da {n}. "
                       f"Al pasarlo a `contar`, el arreglo decae a `int *`: `sizeof(v)` es el tamaño de un puntero "
                       f"({puntero}) y la división da {en_funcion}, no la cantidad de elementos (gcc lo advierte "
                       "con -Wsizeof-array-argument).")
    elif variante == "puntero":
        antes = ""
        cuerpo = [datos, "int *p = datos;", 'printf("%zu %zu\\n", sizeof(datos), sizeof(p));']
        distractores = [f"{total} {total}", f"{n} {puntero}", f"{total} {entero}", f"{puntero} {puntero}", f"{n} {n}"]
        explicacion = (f"`sizeof(datos)` mide el arreglo completo ({n} × {entero} = {total}); `p` es un puntero "
                       f"aunque apunte al arreglo, y `sizeof(p)` vale {puntero}.")
    elif variante == "parametro":
        antes = f'void mostrar(int v[{n}]) {{\n    printf("%zu\\n", sizeof(v));\n}}'
        cuerpo = [datos, "mostrar(datos);"]
        distractores = [str(total), str(n), str(entero), str(total + puntero)]
        explicacion = (f"Aunque el parámetro se declare `int v[{n}]`, es un `int *`: el tamaño entre corchetes "
                       f"se ignora y `sizeof(v)` vale {puntero}.")
    else:
        antes = ""
        cuerpo = [datos, 'printf("%zu %zu %zu\\n", sizeof(datos), sizeof(datos + 0), sizeof(*datos));']
        distractores = [f"{total} {total} {entero}", f"{total} {total} {total}", f"{n} {puntero} {entero}",
                        f"{total} {entero} {entero}", f"{total} {puntero} {total}"]
        explicacion = (f"`sizeof(datos)` mide el arreglo ({total}); en `datos + 0` el arreglo decae a puntero "
                       f"({puntero}); `*datos` es el primer `int` ({entero}).")

    codigo = _programa(cuerpo, antes=antes)
    salida = _ejecutar(codigo, flags_extra=["-Wno-sizeof-array-argument", "-Wno-sizeof-pointer-div"])
    return SnippetGenerado(
        plantilla="array-decay",
        titulo=f"Decaimiento de arreglos: {variante} {_huella(codigo)}",
        enunciado=(f"En una plataforma donde `int` ocupa {entero} bytes y los punteros {puntero}, "
                   "¿qué imprime el siguiente programa?"),
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion=explicacion,
    )


# ---------------------------------------------------------------------------
# Comportamiento indefinido: la respuesta la verifican los avisos de gcc
# ---------------------------------------------------------------------------

UB_SALVAJE = "Comportamiento indefinido: se usa un puntero sin inicializar (puntero salvaje)."
UB_LIBERADA = "Comportamiento indefinido: se accede a memoria ya liberada con `free` (puntero colgante)."
UB_LOCAL = ("Comportamiento indefinido: se usa la dirección de una variable local que ya dejó de existir "
            "(puntero colgante).")
UB_DOBLE = "Comportamiento indefinido: se libera dos veces el mismo bloque (doble `free` por un puntero colgante)."
NO_COMPILA = "No compila: el compilador rechaza el uso del puntero."
SEGFAULT = "Siempre termina con *segmentation fault*."
NULL_AUTOMATICO = "Imprime 0: un puntero sin valor asignado apunta a `NULL`."
FREE_PONE_NULL = "Imprime 0: `free` deja el puntero en `NULL`."
FUGA = "Funciona, pero pierde memoria: el bloque nunca se libera."
DIRECCION = "Imprime una dirección de memoria."
# Al final de los distractores de todas las preguntas de diagnóstico: completan hasta 8 opciones.
_COMUNES = [UB_SALVAJE, UB_LIBERADA, UB_LOCAL, UB_DOBLE, NO_COMPILA, SEGFAULT, FUGA, DIRECCION]


def _imprime(salida: str) -> str:
    return f"Imprime `{salida}`."


def _diagnostico(plantilla: str, titulo: str, codigo: str, defecto: str | None, esperados: set[str],
                 ingenua: str, otros: list[str], explicacion: str) -> SnippetGenerado:
    """Pregunta de «¿qué ocurre?»: con `defecto`, la respuesta es ese defecto (lo tiene que ver gcc);
    sin él, el programa es correcto y la respuesta es lo que imprime."""
    if defecto is not None:
        _verificar_defecto(codigo, esperados)
        correcta = defecto
        distractores = [_imprime(ingenua), *otros, *_COMUNES]
    else:
        correcta = _imprime(_verificar_correcto(codigo))
        distractores = [*otros, *_COMUNES]
    return SnippetGenerado(plantilla=plantilla, titulo=f"{titulo} {_huella(codigo)}",
                           enunciado=ENUNCIADO_DIAGNOSTICO, codigo=codigo,
                           salida_correcta=correcta, distractores=distractores, explicacion=explicacion)


def _plantilla_punteros_salvajes(rng: random.Random) -> SnippetGenerado:
    v = rng.randint(2, 99)
    defectuoso = rng.random() < 0.7
    forma = rng.choice(["entero", "estructura", "indice"])
    antes = "struct punto {\n    int x;\n    int y;\n};" if forma == "estructura" else ""

    if forma == "entero":
        inicio = ["int *p;"] if defectuoso else ["int x = 0;", "int *p = &x;"]
        cuerpo = [*inicio, f"*p = {v};", 'printf("%d\\n", *p);']
    elif forma == "estructura":
        inicio = ["struct punto *q;"] if defectuoso else ["struct punto origen = {0, 0};", "struct punto *q = &origen;"]
        cuerpo = [*inicio, f"q->x = {v};", 'printf("%d\\n", q->x);']
    else:
        inicio = ["int *v;"] if defectuoso else ["int datos[3] = {0};", "int *v = datos;"]
        cuerpo = [*inicio, f"v[2] = {v};", 'printf("%d\\n", v[2]);']

    otros = [NULL_AUTOMATICO, NO_COMPILA, SEGFAULT, DIRECCION]
    if not defectuoso:
        otros = [UB_SALVAJE, *otros]
    return _diagnostico(
        "punteros-salvajes", f"Punteros sin inicializar: {forma}",
        _programa(cuerpo, antes=antes), UB_SALVAJE if defectuoso else None,
        {"uninitialized", "maybe-uninitialized", "analyzer-use-of-uninitialized-value"},
        str(v), otros,
        "Un puntero local sin inicializar contiene basura: escribir a través de él es comportamiento "
        "indefinido. Puede parecer que funciona, colgarse o corromper otros datos; no está garantizado "
        "ni que imprima el valor ni el *segmentation fault*. gcc lo advierte con -Wuninitialized."
        if defectuoso else "El puntero apunta a memoria válida antes de usarse, así que el programa está bien definido.",
    )


def _plantilla_punteros_colgantes(rng: random.Random) -> SnippetGenerado:
    v = rng.randint(2, 50)
    defectuoso = rng.random() < 0.7
    forma = rng.choice(["free", "local", "doble"])
    includes: tuple[str, ...] = ("stdio.h", "stdlib.h")

    if forma == "free":
        n = rng.randint(3, 6)
        k = rng.randint(0, n - 1)
        cuerpo = [f"int *p = malloc({n} * sizeof(int));", "if (p == NULL) {", "    return 1;", "}",
                  f"for (int i = 0; i < {n}; i++) {{", f"    p[i] = {v} + i;", "}"]
        cuerpo += (["free(p);", f'printf("%d\\n", p[{k}]);'] if defectuoso
                   else [f'printf("%d\\n", p[{k}]);', "free(p);", "p = NULL;"])
        antes, ingenua, defecto = "", str(v + k), UB_LIBERADA
        esperados = {"use-after-free", "analyzer-use-after-free"}
        otros = [FREE_PONE_NULL, NO_COMPILA, FUGA]
        explicacion = ("Después de `free(p)` el bloque ya no pertenece al programa y `p` queda colgando: "
                       "sigue guardando la dirección vieja. Leer `p[k]` es comportamiento indefinido."
                       if defectuoso else "Se lee antes de liberar y después se anula el puntero: no hay accesos colgantes.")
    elif forma == "local":
        if defectuoso:
            antes = "int *crear(int v) {\n    int x = v * 2;\n    return &x;\n}"
        elif rng.random() < 0.5:
            antes = "int *crear(int v) {\n    static int x;\n    x = v * 2;\n    return &x;\n}"
        else:
            antes = ("int *crear(int v) {\n    int *x = malloc(sizeof(int));\n    if (x != NULL) {\n"
                     "        *x = v * 2;\n    }\n    return x;\n}")
        cuerpo = [f"int *p = crear({v});", "if (p == NULL) {", "    return 1;", "}", 'printf("%d\\n", *p);']
        if not defectuoso and "malloc" in antes:
            cuerpo.append("free(p);")
        ingenua, defecto = str(v * 2), UB_LOCAL
        esperados = {"return-local-addr", "dangling-pointer"}
        otros = [NO_COMPILA, _imprime(str(v)), FUGA]
        explicacion = ("`x` vive en el marco de `crear` y deja de existir al volver: el puntero devuelto queda "
                       "colgando (gcc lo advierte con -Wreturn-local-addr)."
                       if defectuoso else "El valor devuelto sigue vivo después de volver de `crear` "
                       "(variable `static` o memoria dinámica), así que el puntero es válido.")
    else:
        cuerpo = ["int *p = malloc(sizeof(int));", "if (p == NULL) {", "    return 1;", "}",
                  "int *q = p;", f"*q = {v};", 'printf("%d\\n", *q);', "free(p);"]
        if defectuoso:
            cuerpo.append("free(q);")
        antes, ingenua, defecto = "", f"{v}", UB_DOBLE
        esperados = {"analyzer-double-free"}
        otros = [FUGA, NO_COMPILA, FREE_PONE_NULL]
        explicacion = ("`q` y `p` apuntan al mismo bloque: tras `free(p)`, `q` queda colgando y `free(q)` "
                       "libera dos veces la misma memoria." if defectuoso
                       else "`q` es otro nombre del mismo bloque: alcanza con liberarlo una sola vez.")

    if not defectuoso:
        otros = [defecto, *otros]
    return _diagnostico(
        "punteros-colgantes", f"Punteros colgantes: {forma}",
        _programa(cuerpo, antes=antes, includes=includes), defecto if defectuoso else None,
        esperados, ingenua, otros, explicacion,
    )


# ---------------------------------------------------------------------------
# Memoria dinámica: la respuesta la da el conteo de malloc/free
# ---------------------------------------------------------------------------

def _plantilla_fugas_malloc(rng: random.Random) -> SnippetGenerado:
    entero, puntero = tamanos_plataforma()
    forma = rng.choice(["bucle", "reasignacion", "matriz"])
    n, k, m = rng.randint(4, 8), rng.randint(2, 6), rng.randint(2, 3)   # bucle
    a, b = rng.randint(8, 40), rng.randint(8, 40)                       # reasignación
    f, c = rng.randint(2, 5), rng.randint(2, 6)                         # matriz

    if forma == "bucle":
        cuerpo = [f"for (int i = 0; i < {n}; i++) {{",
                  f"    int *p = malloc({k} * sizeof(int));",
                  "    if (p == NULL) {", "        return 1;", "    }",
                  "    p[0] = i;",
                  f"    if (i % {m} == 0) {{", "        free(p);", "    }", "}"]
    elif forma == "reasignacion":
        cuerpo = [f"char *s = malloc({a});", "if (s == NULL) {", "    return 1;", "}",
                  f"s = malloc({b});", "if (s == NULL) {", "    return 1;", "}",
                  "free(s);"]
    else:
        cuerpo = [f"int **m = malloc({f} * sizeof(int *));", "if (m == NULL) {", "    return 1;", "}",
                  f"for (int i = 0; i < {f}; i++) {{",
                  f"    m[i] = malloc({c} * sizeof(int));",
                  "    if (m[i] == NULL) {", "        return 1;", "    }", "}",
                  "free(m);"]
    codigo = _programa(cuerpo, includes=("stdio.h", "stdlib.h"))
    _, fuga, _ = memoria_sin_liberar(codigo)

    if forma == "bucle":
        bloque = k * entero
        distractores = [str(n * bloque), "0", str(fuga // entero), str(fuga - bloque), str(fuga + bloque),
                        str(n * bloque - fuga)]
        explicacion = (f"Se piden {n} bloques de {k} enteros ({bloque} bytes) y sólo se liberan los de las "
                       f"vueltas con `i % {m} == 0`; el resto se pierde al salir del bloque del `for`.")
    elif forma == "reasignacion":
        distractores = ["0", str(b), str(a + b), str(abs(a - b))]
        explicacion = (f"Al reasignar `s` se pierde la única referencia al primer bloque ({a} bytes): "
                       f"`free(s)` libera sólo el segundo.")
    else:
        indice = f * puntero
        distractores = ["0", str(fuga + indice), str(indice), str(f * c), str(c * entero)]
        explicacion = (f"`free(m)` libera sólo el arreglo de punteros ({f} × {puntero} bytes): las {f} filas "
                       f"de {c} enteros ({c * entero} bytes cada una) quedan sin liberar. Hay que liberar cada "
                       "`m[i]` antes que `m`.")
    return SnippetGenerado(
        plantilla="fugas-malloc",
        titulo=f"Fugas de memoria: {forma} {_huella(codigo)}",
        enunciado=(f"Al terminar el programa, ¿cuántos bytes de memoria dinámica quedaron sin liberar? "
                   f"(`int` ocupa {entero} bytes y los punteros {puntero})"),
        codigo=codigo,
        salida_correcta=str(fuga),
        distractores=distractores,
        explicacion=explicacion,
    )


PLANTILLAS = {
    "precedencia": ("Expresiones aritméticas con precedencia de operadores", _plantilla_precedencia),
    "traza-punteros": ("Traza de aritmética de punteros sobre un arreglo", _plantilla_traza_punteros),
    "recursion": ("Recursión simple (suma acumulada)", _plantilla_recursion),
    "incrementos": ("Post-incremento vs pre-incremento", _plantilla_incrementos),
    "array-decay": ("Decaimiento de arreglos a punteros: sizeof en main, en parámetros y en expresiones",
                    _plantilla_array_decay),
    "punteros-salvajes": ("Punteros sin inicializar: ¿comportamiento indefinido o programa correcto?",
                          _plantilla_punteros_salvajes),
    "punteros-colgantes": ("Punteros colgantes: uso tras free, dirección de una local y doble free",
                           _plantilla_punteros_colgantes),
    "fugas-malloc": ("Fugas de memoria con malloc: cuántos bytes quedan sin liberar", _plantilla_fugas_malloc),
}

# Cómo se verifica la respuesta de cada plantilla (lo muestra `alucard sintetizar` sin argumentos).
_EJECUTA = "se compila y se ejecuta: la salida es la respuesta"
_ANALIZA = "gcc -fanalyzer tiene que señalar el defecto; las variantes correctas se ejecutan"
VERIFICACION = {
    "precedencia": _EJECUTA,
    "traza-punteros": _EJECUTA,
    "recursion": _EJECUTA,
    "incrementos": _EJECUTA,
    "array-decay": _EJECUTA,
    "punteros-salvajes": _ANALIZA,
    "punteros-colgantes": _ANALIZA,
    "fugas-malloc": "se cuentan los bytes que quedan sin liberar (malloc y free interceptados)",
}
