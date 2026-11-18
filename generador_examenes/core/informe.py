"""Informe de la generación (`informe.md` junto a los temas): qué se eligió, de dónde y por qué.

- Pools: cuántas preguntas podía elegir cada uno y cuántas eligió.
- Preguntas: sección, título, tipo, categoría, banco y puntaje.
- Orden de cada tema: los temas comparten preguntas y cambian el orden (y el de las opciones).
- Consignas prácticas que no entraron en ningún pool, con el filtro que las dejó afuera, y las del
  proyecto que tienen `publicar: false`.
- Categorías del banco, con cuántas preguntas tiene cada una, y sus etiquetas.

Si la generación falla después de leer los bancos, `informe.md` igual se escribe con el error, qué
filtro dejó vacío cada pool (y qué hay parecido en el banco) y lo que se cargó.

Con `debug_candidatas`, además `candidatas.txt`: cada pregunta que cada pool podía elegir.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from generador_examenes.core.carpetas_banco import SIN_CATEGORIA
from generador_examenes.core.models import DefinicionExamen, PoolConfig, Pregunta

# Grupos de filtros de un pool, en el orden en que se aplican.
_FILTROS = [
    ("categoría", ("categoria", "categorias")),
    ("tipo", ("tipos",)),
    ("etiquetas", ("etiquetas",)),
    ("minutos", ("minutos_min", "minutos_max")),
]


def _celda(texto: Any) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def motivo_fuera(pregunta: Pregunta, pool: PoolConfig) -> Optional[str]:
    """Por qué el pool no puede elegir la pregunta (el primer filtro que no pasa), o None si puede."""
    from generador_examenes.core.logic import _minutos, candidatas_pool

    solo = {pregunta.id: pregunta}
    if pool.preguntas_fijadas:
        return None if pregunta.id in pool.preguntas_fijadas else "no está entre las fijadas"
    for nombre, campos in _FILTROS:
        valores = {c: getattr(pool, c) for c in campos}
        if not any(valores.values()) and valores.get("minutos_min") is None:
            continue
        if candidatas_pool(PoolConfig(**valores), solo):
            continue
        if nombre == "minutos":
            minutos = _minutos(pregunta)
            if minutos is None:
                return "no tiene minutos estimados"
            return f"{minutos} min, fuera de [{pool.minutos_min or 0}, {pool.minutos_max or '∞'}]"
        if nombre == "categoría":
            return f"categoría {pregunta.categoria}"
        if nombre == "tipo":
            return f"tipo {pregunta.tipo}"
        return f"etiquetas {', '.join(pregunta.etiquetas) or '(ninguna)'}"
    return None


def _parecidas(buscada: str, existentes: Iterable[str], n: int = 3) -> List[str]:
    """Las de `existentes` que más se parecen a `buscada` (sin mayúsculas ni separadores raros): un
    nombre mal escrito, otra mayúscula o el último nivel de una categoría anidada."""
    from difflib import get_close_matches

    from generador_examenes.core.logic import normalizar_categoria

    por_norma: Dict[str, str] = {}
    for e in existentes:
        por_norma.setdefault(normalizar_categoria(e), e)
    clave = normalizar_categoria(buscada)
    hoja = clave.rsplit("/", 1)[-1]
    elegidas = get_close_matches(clave, por_norma, n=n, cutoff=0.6)
    elegidas += [c for c in por_norma if hoja and hoja in c.split("/") and c not in elegidas]
    return [por_norma[c] for c in elegidas[:n]]


def _sugerencia(pool: PoolConfig, descripcion: str, antes: List[Pregunta]) -> str:
    """Qué hay en el banco parecido a lo que pide el filtro que vació el pool."""
    if descripcion.startswith("categor"):
        buscadas = [pool.categoria] if pool.categoria else list(pool.categorias)
        existentes = sorted({p.categoria for p in antes})
        parecidas = list(dict.fromkeys(c for b in buscadas for c in _parecidas(b, existentes)))
        if existentes == [SIN_CATEGORIA]:
            return (f"Ninguna pregunta tiene categoría (todas quedaron en «{SIN_CATEGORIA}»): ponela con "
                    "$CATEGORY: en el banco o, en una carpeta de bancos, con un banco.toml "
                    '(categoria = "carpeta").')
        if parecidas:
            return f"¿Quisiste decir {', '.join(f'«{c}»' for c in parecidas)}?"
        return f"Categorías que hay: {_lista(existentes)}." if existentes else ""
    if descripcion.startswith("etiquetas"):
        existentes = sorted({e for p in antes for e in p.etiquetas})
        parecidas = list(dict.fromkeys(e for b in pool.etiquetas for e in _parecidas(b, existentes)))
        if parecidas:
            return f"¿Quisiste decir {', '.join(f'«{e}»' for e in parecidas)}?"
        return f"Etiquetas que hay: {_lista(existentes)}." if existentes else "Ninguna pregunta tiene etiquetas."
    if descripcion.startswith("tipos"):
        from collections import Counter

        tipos = Counter(p.tipo for p in antes)
        return "Tipos que hay: " + ", ".join(f"{t} ({n})" for t, n in tipos.most_common()) + "." if tipos else ""
    if descripcion.startswith("banco"):
        existentes = sorted({p.fuente_banco for p in antes if p.fuente_banco})
        parecidas = _parecidas(pool.banco or "", existentes)
        if parecidas:
            return f"¿Quisiste decir {', '.join(f'«{b}»' for b in parecidas)}?"
        return f"Bancos que hay: {_lista(existentes)}." if existentes else ""
    return ""


def _lista(valores: List[str], hasta: int = 12) -> str:
    resto = len(valores) - hasta
    return ", ".join(f"«{v}»" for v in valores[:hasta]) + (f" y {resto} más" if resto > 0 else "")


def por_que_no_alcanza(pool: PoolConfig, banco: Dict[str, Pregunta], pide: int) -> str:
    """Qué filtro del pool dejó menos preguntas de las que pide, y qué hay parecido en el banco."""
    from generador_examenes.core.logic import pasos_pool

    pasos = pasos_pool(pool, banco)
    if not banco:
        return "El banco no tiene preguntas: revisá input_banco."
    if pool.preguntas_fijadas:
        faltan = [i for i in pool.preguntas_fijadas if i not in banco]
        return f"No existen en el banco: {', '.join(faltan)}." if faltan else ""
    for (_, antes), (descripcion, despues) in zip(pasos, pasos[1:], strict=False):
        if len(despues) < pide:
            texto = f"El filtro {descripcion} deja {len(despues)} de {len(antes)}."
            sugerencia = _sugerencia(pool, descripcion, antes)
            return f"{texto} {sugerencia}" if sugerencia else texto
    if pool.presupuesto_minutos is not None:
        return f"Los filtros dejan {len(pasos[-1][1])}, pero el presupuesto de {pool.presupuesto_minutos} min no alcanza."
    return ""


def _seccion_categorias(banco: Dict[str, Pregunta]) -> List[str]:
    """Las categorías del banco con cuántas preguntas tiene cada una: lo primero a mirar cuando un
    filtro de categoría no encuentra nada."""
    from collections import Counter

    cuenta = Counter(p.categoria or "(sin categoría)" for p in banco.values())
    l = ["", "## Categorías del banco", ""]
    if not cuenta:
        return l + ["El banco no tiene preguntas."]
    l += ["| Categoría | Preguntas |", "| --- | ---: |"]
    l += [f"| {_celda(c)} | {n} |" for c, n in sorted(cuenta.items())]
    etiquetas = Counter(e for p in banco.values() for e in p.etiquetas)
    if etiquetas:
        l += ["", "Etiquetas: " + ", ".join(f"`{_celda(e)}` ({n})" for e, n in sorted(etiquetas.items()))]
    return l


def armar_informe_de_fallo(definicion: DefinicionExamen, banco: Dict[str, Pregunta], error: str,
                           rutas_bancos: Sequence[Path] = (), repetidos: Sequence[Any] = ()) -> str:
    """El informe de una generación que falló: el error, cada pool con lo que podía elegir y qué
    filtro lo vació, y lo que hay en el banco. Los temas de la carpeta son de la corrida anterior."""
    from generador_examenes.core.logic import candidatas_pool

    l: List[str] = [f"# Informe de generación: {definicion.nombre_examen} (falló)", ""]
    l.append(f"{datetime.now():%d/%m/%Y %H:%M} · **la generación falló**: los temas que haya en esta "
             "carpeta son de una corrida anterior.")
    l += ["", "## Error", "", "```text", error.strip() or "el motivo está en el log", "```"]

    l += ["", "## Pools", "", "| Sección | Pool | Filtro | Podía elegir | Pide | |",
          "| --- | --- | --- | ---: | ---: | --- |"]
    problemas: List[str] = []
    for seccion in definicion.secciones_examen:
        for n, pool in enumerate(seccion.pools, 1):
            hay = len(candidatas_pool(pool, banco))
            pide = pool.cantidad or hay
            alcanza = hay >= pide and hay > 0
            marca = "✓" if alcanza else ("!" if pool.accion_si_insuficiente != "error" else "✗")
            l.append(f"| {_celda(seccion.nombre)} | {n} | {_celda(pool)} | {hay} | {pide} | {marca} |")
            if not alcanza:
                motivo = por_que_no_alcanza(pool, banco, max(pide, 1)) or "no alcanzan las preguntas"
                problemas.append(f"- **{_celda(seccion.nombre)}, pool {n}** (pide {pide}, hay {hay}): {_celda(motivo)}")
    if problemas:
        l += ["", "### Por qué no alcanzan", "", *problemas]

    if rutas_bancos:
        l += ["", "## Bancos", ""]
        from collections import Counter

        por_banco = Counter(p.fuente_banco or "?" for p in banco.values())
        from generador_examenes.core.consignas import bancos_de_carpeta

        for ruta in map(Path, rutas_bancos):
            if not ruta.exists():
                estado = "no existe"
            elif ruta.is_dir():
                cuantos = len(bancos_de_carpeta(ruta))
                estado = f"carpeta con {cuantos} banco(s) .gift o .xml" if cuantos else "carpeta sin bancos .gift ni .xml"
            else:
                estado = "archivo"
            l.append(f"- `{ruta}` ({estado})")
        if por_banco:
            l += ["", "| Banco | Preguntas |", "| --- | ---: |"]
            l += [f"| {_celda(b)} | {n} |" for b, n in sorted(por_banco.items())]
    l += _seccion_categorias(banco)
    l += _seccion_repetidos(repetidos)
    return "\n".join(l) + "\n"


def no_publicadas(rutas: Iterable[str]) -> List[Pregunta]:
    """Las consignas de las carpetas `rutas` que tienen `publicar: false`."""
    from generador_examenes.core.consignas import cargar_consignas

    resultado: List[Pregunta] = []
    for ruta in rutas:
        try:
            todas = cargar_consignas(ruta, incluir_no_publicados=True)
        except Exception:
            continue
        resultado += [p for p in todas.values() if not p.metadata.get("publicar", True)]
    return resultado


def comentario_de_etiquetas(pregunta: Pregunta) -> str:
    """El comentario `// [tag, …] [category, …]` de la pregunta, como se escribe en un GIFT."""
    etiquetas = ([f"desarrollo-{pregunta.tamano_desarrollo}"] if pregunta.tamano_desarrollo else []) + [
        e.replace("]", "\\]") for e in pregunta.etiquetas]
    partes = [f"[tag, {', '.join(etiquetas)}]"] if etiquetas else []
    return "// " + " ".join(partes + [f"[category, {pregunta.categoria}]"])


def armar_candidatas(definicion: DefinicionExamen, banco: Dict[str, Pregunta], temas: List[Dict[str, Any]]) -> str:
    """`candidatas.txt`: por pool, cada pregunta que podía salir como `banco:id`, con sus etiquetas en
    el renglón de abajo. Los renglones con `#` dicen de qué sección y pool son."""
    from generador_examenes.core.logic import candidatas_pool

    salieron = {p.id for t in temas for s in t.get("secciones", []) for p in s.get("preguntas", [])}
    l = [f"# Candidatas: {definicion.nombre_examen}",
         "# Cada pregunta que un pool podía elegir: banco:id y, abajo, sus etiquetas."]
    for seccion in definicion.secciones_examen:
        for n, pool in enumerate(seccion.pools, 1):
            candidatas = candidatas_pool(pool, banco)  # en el orden de los bancos
            elegidas = sum(1 for p in candidatas if p.id in salieron)
            l += ["", f"# Sección «{seccion.nombre}», pool {n}: {pool}",
                  f"# {len(candidatas)} candidatas, {elegidas} {'salió' if elegidas == 1 else 'salieron'}"]
            for p in candidatas:
                l += [f"{p.fuente_banco or '?'}:{p.id}", comentario_de_etiquetas(p)]
    return "\n".join(l) + "\n"


def _temas_distintos(temas: List[Dict[str, Any]]) -> bool:
    return len({frozenset(p.id for s in t.get("secciones", []) for p in s.get("preguntas", [])) for t in temas}) > 1


def _preguntas_de_todos_los_temas(examen_base: Dict[str, Any], temas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Con sorteo por tema, el examen base no alcanza: cada sección con lo que salió en algún tema."""
    if not _temas_distintos(temas):
        return examen_base
    secciones = []
    for i, seccion in enumerate(examen_base.get("secciones", [])):
        todas = {p.id: p for t in temas for p in t["secciones"][i].get("preguntas", [])}
        secciones.append({**seccion, "preguntas": list(todas.values())})
    return {**examen_base, "secciones": secciones}


def _seccion_repetidos(repetidos: Sequence[Any]) -> List[str]:
    """Los ids repetidos: la pregunta descartada no puede salir en el examen."""
    if not repetidos:
        return []
    return ["", "## Ids repetidos", "",
            "Dos preguntas con el mismo id: queda la última que se cargó y la otra no puede salir en el examen.",
            "", "| Id | Pregunta | Queda la de | Se descarta la de |", "| --- | --- | --- | --- |",
            *(f"| {_celda(r.id)} | {_celda(r.nombre)} | {_celda(r.queda)} | {_celda(r.descartada)} |"
              for r in repetidos)]


def armar_informe(definicion: DefinicionExamen, banco: Dict[str, Pregunta], examen_base: Dict[str, Any],
                  temas: List[Dict[str, Any]], semilla: int, formatos: List[str],
                  repetidos: Sequence[Any] = ()) -> str:
    from generador_examenes.core.logic import candidatas_pool

    l: List[str] = [f"# Informe de generación: {definicion.nombre_examen}", ""]
    l.append(f"{datetime.now():%d/%m/%Y %H:%M} · semilla {semilla} · {len(temas)} tema(s) · "
             f"{', '.join(formatos)}")
    examen_base = _preguntas_de_todos_los_temas(examen_base, temas)
    l += ["", "## Pools", "", "| Sección | Pool | Filtro | Podía elegir | Eligió |", "| --- | --- | --- | ---: | ---: |"]
    pools_consignas: List[PoolConfig] = []
    for seccion_def, seccion in zip(definicion.secciones_examen, examen_base.get("secciones", []), strict=False):
        ids_seccion = {p.id for p in seccion.get("preguntas", [])}
        for n, pool in enumerate(seccion_def.pools, 1):
            candidatas = candidatas_pool(pool, banco)
            elegidas = sum(1 for p in candidatas if p.id in ids_seccion)
            l.append(f"| {_celda(seccion_def.nombre)} | {n} | {_celda(pool)} | {len(candidatas)} | {elegidas} |")
            if "consigna_practica" in pool.tipos or any(p.tipo == "consigna_practica" for p in candidatas):
                pools_consignas.append(pool)

    l += ["", "## Preguntas", "", "| Sección | Pregunta | Tipo | Categoría | Banco | Puntaje |",
          "| --- | --- | --- | --- | --- | ---: |"]
    for seccion in examen_base.get("secciones", []):
        for p in seccion.get("preguntas", []):
            banco_p = Path(p.fuente_banco).name if p.fuente_banco else "—"
            l.append(f"| {_celda(seccion['nombre'])} | {_celda(p.nombre)} | {p.tipo} | {_celda(p.categoria)} | "
                     f"{_celda(banco_p)} | {p.puntaje:g} |")

    if len(temas) > 1:
        l += ["", "## Orden de cada tema", "",
              "Cada tema toma sus preguntas de los pools que sortean por tema; cambian su orden y el de las opciones."
              if _temas_distintos(temas) else
              "Todos los temas tienen las mismas preguntas; cambian su orden y el de las opciones.", ""]
        for i, tema in enumerate(temas, 1):
            orden = [p.nombre for s in tema.get("secciones", []) for p in s.get("preguntas", [])]
            l.append(f"- **Tema {i}:** " + " → ".join(_celda(o) for o in orden))

    consignas = [p for p in banco.values() if p.tipo == "consigna_practica"]
    elegidas_ids = {p.id for s in examen_base.get("secciones", []) for p in s.get("preguntas", [])}
    fuera = []
    for c in consignas:
        if c.id in elegidas_ids or not pools_consignas:
            continue
        motivos = [m for m in (motivo_fuera(c, pool) for pool in pools_consignas) if m]
        if len(motivos) == len(pools_consignas):
            fuera.append(f"- «{_celda(c.nombre)}» ({c.id}): {'; '.join(dict.fromkeys(motivos))}")
    ocultas = no_publicadas(definicion.input_consignas or [])
    if fuera or ocultas:
        l += ["", "## Consignas que no podían entrar", ""]
        l += fuera
        l += [f"- «{_celda(c.nombre)}» ({c.id}): publicar: false" for c in ocultas]
    l += _seccion_categorias(banco)
    l += _seccion_repetidos(repetidos)
    return "\n".join(l) + "\n"


# Abreviaturas de los tipos para las columnas del inventario.
_TIPOS = {
    "seleccion_multiple": "selección", "verdadero_falso": "V/F", "respuesta_corta": "corta",
    "ensayo": "ensayo", "emparejamiento": "emparej.", "numerica": "numérica", "desarrollo": "desarrollo",
    "consigna_practica": "consigna",
}


def inventario(preguntas: Dict[str, Pregunta], definicion: Optional[DefinicionExamen] = None,
               repetidos: Sequence[Any] = ()) -> tuple[str, bool]:
    """Cuántas preguntas hay por categoría y tipo y, con `definicion`, si cada pool tiene las que pide.

    Devuelve (texto, alcanza): `alcanza` es False si algún pool pide más de las que puede elegir.
    """
    from collections import Counter, defaultdict

    from generador_examenes.core.logic import candidatas_pool

    por_categoria: Dict[str, Counter] = defaultdict(Counter)
    for p in preguntas.values():
        por_categoria[p.categoria or "(sin categoría)"][p.tipo] += 1
    tipos = [t for t in _TIPOS if any(c[t] for c in por_categoria.values())]
    ancho = max([len("Categoría"), *(len(c) for c in por_categoria)])
    encabezado = f"{'Categoría':<{ancho}}  {'Total':>5}  " + "  ".join(f"{_TIPOS[t]:>9}" for t in tipos)
    lineas = [encabezado, "-" * len(encabezado)]
    for categoria in sorted(por_categoria):
        cuenta = por_categoria[categoria]
        celdas = "  ".join(f"{(cuenta[t] or ''):>9}" for t in tipos)
        lineas.append(f"{categoria:<{ancho}}  {sum(cuenta.values()):>5}  {celdas}")
    lineas.append(f"{'Total':<{ancho}}  {len(preguntas):>5}")
    if repetidos:
        lineas += ["", f"! Ids repetidos ({len(repetidos)}): la descartada no cuenta en el total ni puede salir."]
        lineas += [f"  ! {r}" for r in repetidos]

    alcanza = True
    if definicion is not None:
        lineas += ["", f"Pools de «{definicion.nombre_examen}»:"]
        for seccion in definicion.secciones_examen:
            for n, pool in enumerate(seccion.pools, 1):
                hay = len(candidatas_pool(pool, preguntas))
                pide = pool.cantidad if pool.cantidad else hay
                ok = hay >= pide or pool.accion_si_insuficiente != "error"
                alcanza &= ok
                marca = "✓" if hay >= pide else ("!" if ok else "✗")
                lineas.append(f"  {marca} {seccion.nombre}, pool {n}: pide {pide}, hay {hay}  ({pool})")
        if not alcanza:
            lineas.append("\n✗ Algún pool pide más preguntas de las que hay: el examen no se puede generar.")
    return "\n".join(lineas), alcanza
