"""Registro de exámenes tomados: qué preguntas salieron en cada tema y cómo les fue a los estudiantes.

Cada examen registrado es un JSON `alucard-examen/1` en `<carpeta>/<cuatrimestre>/<id>.json` (un
archivo por examen: se versiona en git sin conflictos). Sirve para tres cosas:

- **No repetir preguntas en el cuatrimestre.** `generar` y `validar` leen los exámenes registrados del
  mismo cuatrimestre y dejan afuera (o avisan, según `repetidas`) las preguntas que ya salieron. Una
  pregunta se reconoce por su `id` y por su huella (el contenido), así que cambiarle el nombre o
  moverla de banco no la esconde. A un examen ya registrado sólo lo restringen los registrados antes
  que él: volver a guardarlo da las mismas preguntas.
- **Cruzar datos.** `alucard registro usadas` lista cada pregunta con los exámenes en que salió.
- **Analizar la calidad de cada pregunta.** Con los resultados importados (`alucard registro
  resultados`), `alucard registro analizar` calcula la dificultad, la discriminación, las omisiones y
  los distractores de cada pregunta, sumando todos los exámenes en que se usó.

Registrar es explícito (`alucard registro guardar` o `alucard generar --registrar`): un examen se arma
de a poco, y sólo cuenta como tomado la versión que se guarda. Volver a guardarlo reemplaza la
anterior (sube `revision`); si ya tiene resultados y cambiaron las preguntas, hace falta `--forzar`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

ESQUEMA = "alucard-examen/1"
REPETIDAS = ("evitar", "avisar", "permitir")
NOMBRE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TIPOS_CON_OPCIONES = ("seleccion_multiple", "verdadero_falso")


class ErrorRegistro(ValueError):
    pass


# --- Configuración ------------------------------------------------------------------------------------

def cuatrimestre_de(dia: date) -> str:
    """`2026-1C` de enero a julio y `2026-2C` de agosto a diciembre."""
    return f"{dia.year}-{1 if dia.month <= 7 else 2}C"


@dataclass(frozen=True)
class ConfigRegistro:
    carpeta: Path
    cuatrimestre: str
    id: str
    repetidas: str = "evitar"

    @property
    def archivo(self) -> Path:
        return self.carpeta / self.cuatrimestre / f"{self.id}.json"


def configuracion(definicion: Any, ruta_definicion: Path, curso: Any, cuatrimestre: str | None = None,
                  id_: str | None = None) -> ConfigRegistro:
    """De la línea de comandos, de `registro:` de la definición, de `[registro]` de `alucard.toml` y, al
    final, la fecha del examen (o la de hoy) y el nombre del archivo de la definición."""
    propio = getattr(definicion, "registro", None)
    del_curso = getattr(curso, "registro", None) or {}
    base = curso.ruta.parent if getattr(curso, "ruta", None) else ruta_definicion.parent
    carpeta = del_curso.get("carpeta") or base / "registro"
    cuatri = (cuatrimestre or (propio.cuatrimestre if propio else None) or del_curso.get("cuatrimestre")
              or cuatrimestre_de(_fecha(getattr(definicion, "fecha", None)) or date.today()))
    nombre = id_ or (propio.id if propio else None) or ruta_definicion.stem
    repetidas = (propio.repetidas if propio and propio.repetidas else None) or del_curso.get("repetidas") or "evitar"
    for etiqueta, valor in (("cuatrimestre", cuatri), ("id", nombre)):
        if not NOMBRE.match(str(valor)):
            raise ErrorRegistro(f"registro: {etiqueta} {valor!r}: letras, números, '.', '_' o '-'")
    if repetidas not in REPETIDAS:
        raise ErrorRegistro(f"registro: repetidas es {', '.join(REPETIDAS)}: {repetidas!r}")
    return ConfigRegistro(carpeta=Path(carpeta), cuatrimestre=str(cuatri), id=str(nombre), repetidas=repetidas)


def _fecha(texto: str | None) -> date | None:
    if not texto:
        return None
    try:
        return date.fromisoformat(str(texto)[:10])
    except ValueError:
        return None


# --- Huella e identidad de una pregunta -------------------------------------------------------------

def _normal(html: str) -> str:
    return re.sub(r"\s+", " ", html or "").strip()


def huella(pregunta: Any) -> str:
    """El contenido de la pregunta: tipo, enunciado y opciones (sin su orden). Dos preguntas con la
    misma huella son la misma aunque tengan otro id u otro banco."""
    opciones = sorted((_normal(o.texto_html), bool(o.es_correcta)) for o in pregunta.opciones)
    datos = json.dumps([pregunta.tipo, _normal(pregunta.enunciado_html), opciones], ensure_ascii=False)
    return "sha256:" + hashlib.sha256(datos.encode("utf-8")).hexdigest()


def _letra(i: int) -> str:
    return chr(ord("A") + i)


# --- Armar, leer y escribir -----------------------------------------------------------------------------

def armar(cfg: ConfigRegistro, definicion: Any, ruta_definicion: Path, banco: dict, temas: list[dict],
          semilla: int, bancos: Iterable[Path], excluidas: Iterable[str] = ()) -> dict[str, Any]:
    """El registro del examen: la definición tal como estaba, cada pregunta (con su contenido) y el orden
    de preguntas y opciones de cada tema."""
    from generador_examenes import __version__

    texto = ruta_definicion.read_text(encoding="utf-8")
    import yaml

    catalogo: dict[str, dict] = {}
    salida_temas = []
    for n, tema in enumerate(temas, 1):
        orden, secciones = 0, []
        for seccion in tema.get("secciones", []):
            preguntas = []
            for p in seccion.get("preguntas", []):
                original = banco.get(p.id, p)
                if p.id not in catalogo:
                    catalogo[p.id] = {
                        "huella": huella(original), "nombre": original.nombre, "tipo": original.tipo,
                        "categoria": original.categoria, "etiquetas": list(original.etiquetas),
                        "fuente_banco": original.fuente_banco, "enunciado_html": original.enunciado_html,
                        "opciones": [{"texto_html": o.texto_html, "es_correcta": o.es_correcta} for o in original.opciones],
                    }
                orden += 1
                indices = _indices(original.opciones, p.opciones)
                preguntas.append({
                    "orden": orden, "id": p.id, "puntaje": p.puntaje, "opciones": indices,
                    "correctas": [_letra(i) for i, o in enumerate(p.opciones) if o.es_correcta],
                })
            secciones.append({"nombre": seccion.get("nombre", ""), "preguntas": preguntas})
        salida_temas.append({"tema": n, "semilla": semilla + n - 1, "secciones": secciones})
    # Con microsegundos: el orden de alta decide qué examen restringe a cuál (ver `anteriores`).
    ahora = datetime.now().isoformat(timespec="microseconds")
    return {
        "schema": ESQUEMA, "id": cfg.id, "cuatrimestre": cfg.cuatrimestre, "revision": 1,
        "registrado": ahora, "actualizado": ahora, "alucard": __version__,
        "examen": {"nombre": definicion.nombre_examen, "institucion": definicion.institucion,
                   "materia": definicion.materia, "fecha": definicion.fecha,
                   "duracion_minutos": definicion.duracion_minutos},
        "definicion": {"archivo": str(ruta_definicion), "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
                       "contenido": yaml.safe_load(texto)},
        "generacion": {"semilla": semilla, "numero_temas": len(temas), "bancos": [str(b) for b in bancos],
                       "repetidas": cfg.repetidas, "excluidas": sorted(excluidas)},
        "preguntas": catalogo,
        "temas": salida_temas,
        "resultados": None,
    }


def _indices(originales: list, mezcladas: list) -> list[int]:
    """Qué opción del banco (por posición) es cada opción del tema."""
    libres = list(range(len(originales)))
    indices = []
    for o in mezcladas:
        for i in libres:
            if originales[i].texto_html == o.texto_html and originales[i].es_correcta == o.es_correcta:
                indices.append(i)
                libres.remove(i)
                break
        else:
            indices.append(-1)
    return indices


def esquema() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "esquemas" / "alucard-examen-1.schema.json").read_text(encoding="utf-8"))


def problemas(registro: dict[str, Any]) -> list[str]:
    import jsonschema

    validador = jsonschema.Draft202012Validator(esquema())
    salida = [f"{'/'.join(map(str, e.absolute_path)) or '(raíz)'}: {e.message}"
              for e in validador.iter_errors(registro)]
    if salida:
        return salida
    for tema in registro["temas"]:
        for seccion in tema["secciones"]:
            for p in seccion["preguntas"]:
                if p["id"] not in registro["preguntas"]:
                    salida.append(f"tema {tema['tema']}: la pregunta {p['id']} no está en preguntas")
    return salida


def leer(ruta: Path) -> dict[str, Any]:
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ErrorRegistro(f"{ruta}: {e}") from e
    fallas = problemas(datos)
    if fallas:
        raise ErrorRegistro(f"{ruta}: no cumple {ESQUEMA}: " + "; ".join(fallas[:5]))
    return datos


def escribir(registro: dict[str, Any], ruta: Path) -> None:
    fallas = problemas(registro)
    if fallas:
        raise ErrorRegistro(f"el registro no cumple {ESQUEMA}: " + "; ".join(fallas[:5]))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(f".{os.getpid()}.tmp")
    temporal.write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporal, ruta)


def _mismas_preguntas(a: dict, b: dict) -> bool:
    def clave(r):
        return [[(p["id"], tuple(p["opciones"])) for s in t["secciones"] for p in s["preguntas"]] for t in r["temas"]]
    return clave(a) == clave(b)


def guardar(nuevo: dict[str, Any], ruta: Path, forzar: bool = False) -> tuple[dict[str, Any], list[str]]:
    """Guarda el registro. Si ya había uno, conserva su fecha de alta, sube `revision` y, si las preguntas
    no cambiaron, sus resultados. Con resultados y otras preguntas, hace falta `forzar`."""
    avisos: list[str] = []
    if ruta.exists():
        viejo = leer(ruta)
        nuevo["registrado"] = viejo["registrado"]
        nuevo["revision"] = viejo["revision"] + 1
        if viejo.get("resultados"):
            if _mismas_preguntas(viejo, nuevo):
                nuevo["resultados"] = viejo["resultados"]
            elif not forzar:
                raise ErrorRegistro(f"{ruta} ya tiene resultados de {len(viejo['resultados']['estudiantes'])} "
                                    "estudiante(s) y las preguntas cambiaron: con --forzar se reemplaza y los "
                                    "resultados se descartan")
            else:
                avisos.append(f"{ruta.name}: se descartaron los resultados, que eran de otras preguntas")
    escribir(nuevo, ruta)
    return nuevo, avisos


def todos(carpeta: Path, cuatrimestre: str | None = None) -> tuple[list[dict], list[str]]:
    """Los registros de la carpeta (de un cuatrimestre, si se pide) y los archivos que no se pudieron leer."""
    registros: list[dict] = []
    fallas: list[str] = []
    if not carpeta.is_dir():
        return registros, fallas
    patron = f"{cuatrimestre}/*.json" if cuatrimestre else "*/*.json"
    for ruta in sorted(carpeta.glob(patron)):
        try:
            registros.append(leer(ruta))
        except ErrorRegistro as e:
            fallas.append(str(e))
    return registros, fallas


# --- Preguntas ya usadas --------------------------------------------------------------------------------

@dataclass
class Uso:
    examen: str
    fecha: str | None
    id: str
    nombre: str


def anteriores(registros: list[dict], id_: str) -> list[dict]:
    """Los registros que restringen al examen `id_`: los dados de alta antes que él (todos, si todavía no
    está registrado). Así, volver a guardar un examen ya registrado lo reproduce aunque después se hayan
    registrado otros con sus preguntas."""
    propio = next((r for r in registros if r["id"] == id_), None)
    if propio is None:
        return [r for r in registros if r["id"] != id_]
    return [r for r in registros if r["id"] != id_ and (r["registrado"], r["id"]) < (propio["registrado"], id_)]


def usos(registros: Iterable[dict], excepto: str | None = None) -> dict[str, list[Uso]]:
    """Por `id` y por huella, en qué exámenes salió cada pregunta (salvo en `excepto`)."""
    salida: dict[str, list[Uso]] = {}
    for r in registros:
        if r["id"] == excepto:
            continue
        for qid, p in r["preguntas"].items():
            uso = Uso(examen=r["id"], fecha=r["examen"].get("fecha"), id=qid, nombre=p["nombre"])
            for clave in (qid, p["huella"]):
                salida.setdefault(clave, []).append(uso)
    return salida


def usada(pregunta: Any, tabla: dict[str, list[Uso]]) -> list[Uso]:
    vistos = {}
    for uso in tabla.get(pregunta.id, []) + tabla.get(huella(pregunta), []):
        vistos[(uso.examen, uso.id)] = uso
    return list(vistos.values())


# --- Resultados -------------------------------------------------------------------------------------------

def _preguntas_del_tema(registro: dict, tema: int) -> list[dict]:
    for t in registro["temas"]:
        if t["tema"] == tema:
            return [p for s in t["secciones"] for p in s["preguntas"]]
    raise ErrorRegistro(f"el examen {registro['id']} no tiene tema {tema}")


def importar_resultados(registro: dict, archivo: Path) -> tuple[dict, list[str]]:
    """Los resultados de un CSV con una fila por estudiante.

    Columnas: `estudiante` (o `student_id`, `legajo`), `tema` (número), `ausente` (opcional: si/no) y una
    por pregunta, con el número de pregunta en el tema (`1`, `2`…) o su `id`. En cada celda va la letra
    marcada (`A`, `B`…; `V` o `F` en verdadero o falso), o el puntaje obtenido, o nada si no respondió.
    """
    with archivo.open(encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise ErrorRegistro(f"{archivo}: no tiene filas")
    columnas = {c.strip().lower(): c for c in filas[0] if c}
    col_est = next((columnas[c] for c in ("estudiante", "student_id", "legajo") if c in columnas), None)
    if col_est is None or "tema" not in columnas:
        raise ErrorRegistro(f"{archivo}: faltan las columnas estudiante (o student_id, legajo) y tema")
    problemas_csv: list[str] = []
    estudiantes: list[dict[str, Any]] = []
    avisos: list[str] = []
    for n, fila in enumerate(filas, 2):
        estudiante = (fila.get(col_est) or "").strip()
        try:
            tema = int((fila.get(columnas["tema"]) or "").strip())
            preguntas = _preguntas_del_tema(registro, tema)
        except (ValueError, ErrorRegistro) as e:
            problemas_csv.append(f"fila {n}: tema {fila.get(columnas['tema'])!r}: {e}")
            continue
        ausente = (fila.get(columnas.get("ausente", ""), "") or "").strip().lower() in ("si", "sí", "1", "true", "x")
        respuestas: dict[str, dict[str, Any]] = {}
        for p in preguntas:
            celda = None
            for clave in (str(p["orden"]), p["id"]):
                if clave.lower() in columnas:
                    celda = (fila.get(columnas[clave.lower()]) or "").strip()
                    break
            if celda is None:
                if not ausente:
                    problemas_csv.append(f"fila {n}: falta la columna de la pregunta {p['orden']} ({p['id']})")
                continue
            try:
                respuestas[p["id"]] = _respuesta(registro["preguntas"][p["id"]], p, celda)
            except ErrorRegistro as e:
                problemas_csv.append(f"fila {n}, pregunta {p['orden']}: {e}")
        estudiantes.append({"estudiante": estudiante, "tema": tema, "ausente": ausente,
                            "respuestas": {} if ausente else respuestas})
    if problemas_csv:
        raise ErrorRegistro(f"{archivo}: " + "; ".join(problemas_csv[:10])
                            + (f" (y {len(problemas_csv) - 10} más)" if len(problemas_csv) > 10 else ""))
    repetidos = {e["estudiante"] for e in estudiantes if sum(1 for x in estudiantes if x["estudiante"] == e["estudiante"]) > 1}
    if repetidos:
        avisos.append(f"estudiantes repetidos: {', '.join(sorted(repetidos))}")
    registro = {**registro, "resultados": {"importado": datetime.now().isoformat(timespec="seconds"),
                                           "fuente": archivo.name, "estudiantes": estudiantes}}
    return registro, avisos


def _respuesta(pregunta: dict, en_tema: dict, celda: str) -> dict[str, Any]:
    maximo = en_tema["puntaje"]
    if not celda:
        return {"opcion": None, "puntaje": 0.0, "omitida": True}
    if pregunta["tipo"] in TIPOS_CON_OPCIONES and re.fullmatch(r"[A-Za-z]", celda):
        letra = celda.upper()
        if pregunta["tipo"] == "verdadero_falso" and letra in ("V", "F"):
            buscada = "verdadero" if letra == "V" else "falso"
            posiciones = [i for i, idx in enumerate(en_tema["opciones"])
                          if _normal(pregunta["opciones"][idx]["texto_html"]).lower() == buscada]
            if not posiciones:
                raise ErrorRegistro(f"{celda!r}: la pregunta no tiene la opción {buscada.capitalize()}")
            letra = _letra(posiciones[0])
        i = ord(letra) - ord("A")
        if not 0 <= i < len(en_tema["opciones"]):
            raise ErrorRegistro(f"{celda!r}: la pregunta tiene {len(en_tema['opciones'])} opciones")
        return {"opcion": letra, "puntaje": maximo if letra in en_tema["correctas"] else 0.0, "omitida": False}
    try:
        puntos = float(celda.replace(",", "."))
    except ValueError as e:
        raise ErrorRegistro(f"{celda!r} no es una letra ni un puntaje") from e
    if not 0 <= puntos <= maximo + 1e-9:
        raise ErrorRegistro(f"{puntos:g} está fuera de 0 a {maximo:g}")
    return {"opcion": None, "puntaje": puntos, "omitida": False}


# --- Calidad de las preguntas ---------------------------------------------------------------------------

POCOS_DATOS = 10
DISTRACTOR_MINIMO = 0.05


@dataclass
class Analisis:
    huella: str
    id: str
    nombre: str
    tipo: str
    categoria: str
    examenes: list[str] = field(default_factory=list)
    n: int = 0
    dificultad: float | None = None        # puntaje medio / máximo: 1 = todos bien
    discriminacion: float | None = None    # correlación ítem-resto
    indice_d: float | None = None          # p del 27 % superior menos p del 27 % inferior
    omision: float | None = None
    opciones: list[dict] = field(default_factory=list)
    diagnostico: list[str] = field(default_factory=list)


def _correlacion(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return None if sx == 0 or sy == 0 else sxy / (sx * sy)


def analizar(registros: Iterable[dict]) -> tuple[list[Analisis], list[dict]]:
    """La calidad de cada pregunta (sumando los exámenes en que salió) y la confiabilidad de cada tema."""
    por_huella: dict[str, Analisis] = {}
    datos: dict[str, dict[str, Any]] = {}
    temas_info = []
    for r in registros:
        resultados = (r.get("resultados") or {}).get("estudiantes") or []
        presentes = [e for e in resultados if not e["ausente"]]
        if not presentes:
            continue
        for t in r["temas"]:
            preguntas = [p for s in t["secciones"] for p in s["preguntas"]]
            del_tema = [e for e in presentes if e["tema"] == t["tema"]]
            if not del_tema:
                continue
            totales = [sum(e["respuestas"].get(p["id"], {}).get("puntaje", 0.0) for p in preguntas) for e in del_tema]
            temas_info.append(_confiabilidad(r, t, preguntas, del_tema))
            orden = sorted(range(len(del_tema)), key=lambda i: totales[i])
            corte = max(1, round(len(del_tema) * 0.27))
            inferiores, superiores = set(orden[:corte]), set(orden[-corte:])
            for p in preguntas:
                cat = r["preguntas"][p["id"]]
                a = por_huella.setdefault(cat["huella"], Analisis(huella=cat["huella"], id=p["id"], nombre=cat["nombre"],
                                                                 tipo=cat["tipo"], categoria=cat["categoria"]))
                if r["id"] not in a.examenes:
                    a.examenes.append(r["id"])
                d = datos.setdefault(cat["huella"], {"s": [], "resto": [], "omitidas": 0, "sup": [], "inf": [],
                                                     "elegidas": {}, "totales_por_opcion": {}, "opciones": cat["opciones"]})
                for i, e in enumerate(del_tema):
                    resp = e["respuestas"].get(p["id"], {"puntaje": 0.0, "omitida": True, "opcion": None})
                    s = resp["puntaje"] / p["puntaje"] if p["puntaje"] else 0.0
                    d["s"].append(s)
                    d["resto"].append(totales[i] - resp["puntaje"])
                    d["omitidas"] += 1 if resp.get("omitida") else 0
                    if i in superiores:
                        d["sup"].append(s)
                    if i in inferiores:
                        d["inf"].append(s)
                    if resp.get("opcion"):
                        indice = p["opciones"][ord(resp["opcion"]) - ord("A")]
                        d["elegidas"][indice] = d["elegidas"].get(indice, 0) + 1
                        d["totales_por_opcion"].setdefault(indice, []).append(totales[i] / max(1e-9, sum(x["puntaje"] for x in preguntas)))
    for clave, a in por_huella.items():
        d = datos[clave]
        a.n = len(d["s"])
        a.dificultad = sum(d["s"]) / a.n
        a.discriminacion = _correlacion(d["s"], d["resto"])
        a.indice_d = (sum(d["sup"]) / len(d["sup"]) - sum(d["inf"]) / len(d["inf"])) if d["sup"] and d["inf"] else None
        a.omision = d["omitidas"] / a.n
        _opciones(a, d)
        _diagnosticar(a)
    return sorted(por_huella.values(), key=lambda a: (a.categoria, a.nombre)), temas_info


def _opciones(a: Analisis, d: dict) -> None:
    respondidas = sum(d["elegidas"].values())
    if not respondidas:
        return
    medias = {i: sum(v) / len(v) for i, v in d["totales_por_opcion"].items()}
    correctas = [i for i, o in enumerate(d["opciones"]) if o["es_correcta"]]
    media_correctas = [medias[i] for i in correctas if i in medias]
    for i, o in enumerate(d["opciones"]):
        a.opciones.append({"opcion": i, "texto": re.sub(r"<[^>]+>", "", o["texto_html"])[:60],
                           "correcta": o["es_correcta"], "elegida": d["elegidas"].get(i, 0) / respondidas,
                           "media_total": medias.get(i)})
        # En verdadero o falso la otra opción no es un distractor: lo dice la dificultad.
        if not o["es_correcta"] and a.tipo != "verdadero_falso":
            if d["elegidas"].get(i, 0) / respondidas < DISTRACTOR_MINIMO and a.n >= POCOS_DATOS:
                a.diagnostico.append(f"el distractor «{a.opciones[-1]['texto']}» casi no se elige: no funciona")
            if media_correctas and i in medias and medias[i] > max(media_correctas) and d["elegidas"].get(i, 0) >= 3:
                a.diagnostico.append(f"el distractor «{a.opciones[-1]['texto']}» atrae a los que mejor les fue: "
                                     "revisá la clave y la redacción")


def _diagnosticar(a: Analisis) -> None:
    if a.n < POCOS_DATOS:
        a.diagnostico.insert(0, f"pocos datos ({a.n} respuestas): tomalo como orientación")
    if a.dificultad is not None:
        if a.dificultad > 0.90:
            a.diagnostico.append("muy fácil: casi todos la resuelven")
        elif a.dificultad < 0.20:
            a.diagnostico.append("muy difícil: casi nadie la resuelve")
    if a.discriminacion is not None:
        if a.discriminacion < 0:
            a.diagnostico.append("discriminación negativa: a los que mejor les fue les va peor en esta; revisá la clave")
        elif a.discriminacion < 0.20:
            a.diagnostico.append("discrimina poco entre los que saben y los que no")
    if a.omision is not None and a.omision > 0.25:
        a.diagnostico.append(f"la deja en blanco el {a.omision:.0%}: ¿se entiende la consigna? ¿alcanza el tiempo?")


def _confiabilidad(r: dict, t: dict, preguntas: list[dict], estudiantes: list[dict]) -> dict:
    """Alfa de Cronbach del tema, con el puntaje de cada pregunta sobre su máximo."""
    k, n = len(preguntas), len(estudiantes)
    alfa = None
    if k >= 2 and n >= 3:
        matriz = [[e["respuestas"].get(p["id"], {}).get("puntaje", 0.0) / (p["puntaje"] or 1) for p in preguntas]
                  for e in estudiantes]

        def var(v):
            m = sum(v) / len(v)
            return sum((x - m) ** 2 for x in v) / (len(v) - 1)
        total = var([sum(f) for f in matriz])
        if total > 0:
            alfa = k / (k - 1) * (1 - sum(var([f[j] for f in matriz]) for j in range(k)) / total)
    return {"examen": r["id"], "cuatrimestre": r["cuatrimestre"], "tema": t["tema"], "preguntas": k,
            "estudiantes": n, "alfa": alfa}


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def _num(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def informe(analisis: list[Analisis], temas: list[dict]) -> str:
    """El análisis en Markdown."""
    lineas = ["# Calidad de las preguntas", "",
              "- **Dificultad**: puntaje medio sobre el máximo (1 = todos bien). Entre 0,30 y 0,80 es lo esperable.",
              ("- **Discriminación**: correlación entre la pregunta y el resto del examen. Desde 0,30 es buena; "
               "por debajo de 0,20, no separa a los que saben de los que no; negativa, hay que revisarla."),
              "- **D**: dificultad en el 27 % al que mejor le fue menos en el 27 % al que peor le fue.", "",
              "| Pregunta | Categoría | Exámenes | n | Dificultad | Discriminación | D | Omisión |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for a in analisis:
        lineas.append(f"| {a.nombre} | {a.categoria} | {', '.join(a.examenes)} | {a.n} | {_num(a.dificultad)} | "
                      f"{_num(a.discriminacion)} | {_num(a.indice_d)} | {_pct(a.omision)} |")
    revisar = [a for a in analisis if [d for d in a.diagnostico if not d.startswith("pocos datos")]]
    if revisar:
        lineas += ["", "## Para revisar", ""]
        for a in revisar:
            lineas.append(f"- **{a.nombre}** (`{a.id}`): " + "; ".join(a.diagnostico) + ".")
    con_opciones = [a for a in analisis if a.opciones]
    if con_opciones:
        lineas += ["", "## Opciones", ""]
        for a in con_opciones:
            lineas.append(f"**{a.nombre}**: " + " · ".join(
                f"{'✓ ' if o['correcta'] else ''}«{o['texto']}» {o['elegida']:.0%}" for o in a.opciones))
            lineas.append("")
    if temas:
        lineas += ["", "## Confiabilidad de cada tema", "", "| Examen | Cuatrimestre | Tema | Preguntas | Estudiantes | Alfa |",
                   "| --- | --- | ---: | ---: | ---: | ---: |"]
        lineas += [f"| {t['examen']} | {t['cuatrimestre']} | {t['tema']} | {t['preguntas']} | {t['estudiantes']} | "
                   f"{_num(t['alfa'])} |" for t in temas]
    return "\n".join(lineas) + "\n"


def a_dict(analisis: list[Analisis], temas: list[dict]) -> dict[str, Any]:
    return {"preguntas": [a.__dict__ for a in analisis], "temas": temas}
