"""El lote de `alucard omr build`: todo lo que sale de un examen con carátula OMR (§8).

En `--out` (por omisión `dist/<exam_id>/`):

| Archivo | Qué es |
| --- | --- |
| `examenes_<exam_id>.pdf` | Un examen por estudiante: carátula personalizada y enunciado. Cada uno ocupa un número par de páginas (doble faz). |
| `roster_<exam_id>.csv` | `student_id,legajo,apellido,nombre,variante` (UTF-8 con BOM): el único vínculo con la persona. |
| `layout_<layout_id>_v<version>.json` y `.sha256` | El manifiesto `omr-layout/2`. |
| `config_qr_<exam_id>.pdf` y `.svg` | La hoja docente con el QR de configuración, que lleva la `hmac_key`. |
| `layout_test_<layout_id>.pdf` | La hoja de calibración, con burbujas rellenas al 0, 25, 50 y 100 %. |
| `build_<exam_id>.log` | Lo generado, con el `sha256` del manifiesto y de cada PDF. |

La `hmac_key` queda en `.hmac_key` (permisos 600) para que regenerar el lote no invalide las
carátulas ya impresas ni la sesión de la app; `--nueva-clave` la cambia. Un `.gitignore` deja
fuera del repositorio la clave, la nómina y la hoja docente.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from generador_examenes.omr import layout, nomina, notas, qr
from generador_examenes.omr.config import ConfigExamen

# Disposición de la página, en mm. El marco y sus burbujas salen del manifiesto; esto es dónde va el
# marco en la hoja y lo que el manifiesto no describe (el QR, el texto de respaldo).
OX, OY = 15.0, 15.0                 # el centroide del marcador 0: a 15 mm de los bordes del A4
DIVISORIA = 9.0                     # debajo del marco: la franja mide frame_mm.h + 24 mm
QR_LADO, QR_X, QR_Y = 15.0, 132.5, 10.5       # versión 3 (29 módulos): 0,52 mm por módulo
TEXTO_X, TEXTO_Y, TEXTO_ANCHO = 124.0, 30.0, 32.0
PIE_LADO = 12.0                     # el QR de pie de las páginas 2..N
MARGEN_INFERIOR = 30.0
PAGINAS_PROBABLES = 30
PLANTILLA_CARATULA = Path(__file__).resolve().parents[2] / "templates" / "omr" / "caratula.typ"
IGNORAR = ".hmac_key\nroster_*.csv\nconfig_qr_*\n.omr/\n"


class ErrorLote(RuntimeError):
    pass


@dataclass
class Lote:
    salida: Path
    examenes: Path
    nomina: Path
    manifiesto: Path
    huella: str
    config_qr: Path
    config_qr_svg: Path
    calibracion: Path
    registro: Path
    inscriptos: list[nomina.Inscripto]
    modo_qr: str
    avisos: list[str] = field(default_factory=list)


def _cadena(texto: str) -> str:
    from generador_examenes.generators.typst_markup import _cadena as cadena

    return cadena(texto)


def _compilar(fuente: str, destino: Path, raiz: Path, desbordes: list | None = None) -> Path:
    from generador_examenes.generators.pdf_renderer import compilar_typst_a_pdf

    try:
        return compilar_typst_a_pdf(fuente, destino, root_dir=raiz, desbordes=desbordes, carpeta=raiz / ".omr")
    except RuntimeError as e:
        raise ErrorLote(f"Typst no pudo generar {destino.name}: {e}") from e


def clave_del_examen(salida: Path, config: ConfigExamen, nueva: bool = False) -> str:
    """La `hmac_key` guardada en la salida (si es de este examen) o una nueva."""
    archivo = salida / ".hmac_key"
    if archivo.is_file() and not nueva:
        exam_id, _, clave = archivo.read_text(encoding="utf-8").strip().partition(":")
        if exam_id == config.exam_id and qr.clave_valida(clave):
            return clave
    clave = qr.nueva_clave()
    archivo.write_text(f"{config.exam_id}:{clave}\n", encoding="utf-8")
    try:
        os.chmod(archivo, 0o600)
    except OSError:
        pass
    return clave


def _contexto_omr(config: ConfigExamen, manifiesto: dict, ruta_manifiesto: str, inscripto: nomina.Inscripto,
                  clave: str, paginas: int, margen_sup: float) -> dict[str, Any]:
    contenido = qr.contenido_caratula(config, inscripto.student_id, inscripto.variante, clave)
    alto_franja = OY + manifiesto["frame_mm"]["h"] + DIVISORIA
    pies = {n: qr.svg(qr.qr_pie(qr.contenido_pie(config, inscripto.student_id, n))) for n in range(2, paginas + 1)}
    return {
        "modulo": PLANTILLA_CARATULA.read_text(encoding="utf-8"),
        "manifiesto": ruta_manifiesto,
        "ox_mm": OX, "oy_mm": OY, "divisoria_mm": DIVISORIA,
        "qr": qr.svg(qr.qr_caratula(contenido)), "qr_x": QR_X, "qr_y": QR_Y, "qr_lado": QR_LADO,
        "respaldo": [inscripto.nombre_completo, f"{inscripto.student_id} · Variante {inscripto.variante}"],
        "texto_x": TEXTO_X, "texto_y": TEXTO_Y, "texto_ancho": TEXTO_ANCHO,
        "pies": pies, "pie_lado": PIE_LADO, "margen_inf_mm": MARGEN_INFERIOR,
        "salto_mm": max(0.0, alto_franja + 4 - margen_sup),
        "nombre": inscripto.nombre_completo, "variante": inscripto.variante,
    }


def _paginas(pdf: Path) -> int:
    import pypdf

    return len(pypdf.PdfReader(str(pdf)).pages)


def build(config: ConfigExamen, inscriptos: list[nomina.Inscripto], salida: Path,
          preguntas: list[Path] | None = None, modo_qr: Literal["compressed", "compact"] = "compressed",
          nueva_clave: bool = False, avisar=print) -> Lote:
    from generador_examenes.core.alucard_qol import empaquetar_pdfs_para_imprenta
    from generador_examenes.core.estilo import contexto_estilo
    from generador_examenes.generators.pdf_renderer import PdfRenderer
    from generador_examenes.omr import cuerpo as modulo_cuerpo

    largo = max(len(i.student_id) for i in inscriptos)
    if qr.largo_maximo_caratula(config, largo) > qr.CAPACIDAD_CARATULA:
        raise ErrorLote(f"el QR de la carátula pasa de {qr.CAPACIDAD_CARATULA} caracteres (versión 3-Q): "
                        "acortá exam_id, layout_id o los student_id")
    motivos = qr.motivos_sin_compacto(config)
    if modo_qr == "compact" and motivos:
        raise ErrorLote("--qr-config-mode compact no alcanza para esta configuración: " + "; ".join(motivos))

    manifiesto = layout.construir(config)
    problemas = layout.problemas(manifiesto)
    if problemas:
        raise ErrorLote("el manifiesto no cumple omr-layout/2: " + "; ".join(problemas))
    cuerpo = modulo_cuerpo.armar(config, preguntas)

    salida.mkdir(parents=True, exist_ok=True)
    (salida / ".gitignore").write_text(IGNORAR, encoding="utf-8")
    clave = clave_del_examen(salida, config, nueva=nueva_clave)
    ruta_manifiesto = salida / layout.nombre_archivo(config)
    huella = layout.escribir(manifiesto, ruta_manifiesto)
    temporal = salida / ".omr"
    if temporal.exists():
        shutil.rmtree(temporal)

    renderer = PdfRenderer()
    margen_sup = float(contexto_estilo(cuerpo.definicion, 0)["estilo"]["margen_sup_mm"])
    temas = {letra: i for i, letra in enumerate(config.variants)}
    paginas_de: dict[str, int] = {}
    pdfs, desbordes, avisos = [], set(), list(cuerpo.avisos)
    for inscripto in inscriptos:
        variante = inscripto.variante
        paginas = paginas_de.get(variante, PAGINAS_PROBABLES)
        destino = temporal / f"{inscripto.student_id}.pdf"
        for _ in range(2):
            extra = {"omr": _contexto_omr(config, manifiesto, "/" + ruta_manifiesto.name, inscripto, clave, paginas,
                                          margen_sup)}
            _, _, fuente = renderer.fuente_examen(cuerpo.variantes[variante], cuerpo.definicion, temas[variante], extra)
            marcas: list = []
            _compilar(fuente, destino, salida, marcas)
            reales = _paginas(destino)
            if reales <= paginas:
                break
            paginas = reales                    # más páginas que QR de pie: otra vez, con todos
        paginas_de[variante] = max(paginas_de.get(variante, 0), reales)
        desbordes.update(f"variante {variante}, «{m.get('pregunta')}»: {m.get('motivo')}" for m in marcas)
        pdfs.append(destino)
    avisos += sorted(desbordes)

    examenes = empaquetar_pdfs_para_imprenta(pdfs, salida / f"examenes_{config.exam_id}.pdf", doble_faz=True)
    ruta_nomina = salida / f"roster_{config.exam_id}.csv"
    nomina.escribir(inscriptos, ruta_nomina)

    principal = qr.config_comprimida(config, clave, manifiesto)
    compacto = None if motivos else qr.config_compacta(config, clave)
    if modo_qr == "compact":
        principal, compacto = compacto, None
    svg = salida / f"config_qr_{config.exam_id}.svg"
    qr.qr_configuracion(principal).save(str(svg), kind="svg", scale=4, border=4, dark="#000000", light="#ffffff")
    fuente_texto = contexto_estilo(cuerpo.definicion, 0)["estilo"]["fuente_typst"]
    hoja = salida / f"config_qr_{config.exam_id}.pdf"
    _compilar(hoja_docente(config, manifiesto, huella, principal, compacto, motivos, fuente_texto), hoja, salida)
    calibracion = salida / f"layout_test_{config.layout_id}.pdf"
    _compilar(hoja_calibracion(manifiesto, "/" + ruta_manifiesto.name, fuente_texto), calibracion, salida)
    shutil.rmtree(temporal, ignore_errors=True)

    registro = salida / f"build_{config.exam_id}.log"
    _registrar(registro, config, manifiesto, huella, inscriptos, paginas_de, modo_qr,
               [examenes, ruta_nomina, hoja, svg, calibracion])
    return Lote(salida=salida, examenes=examenes, nomina=ruta_nomina, manifiesto=ruta_manifiesto, huella=huella,
                config_qr=hoja, config_qr_svg=svg, calibracion=calibracion, registro=registro,
                inscriptos=inscriptos, modo_qr=modo_qr, avisos=avisos)


def _registrar(registro: Path, config: ConfigExamen, manifiesto: dict, huella: str, inscriptos, paginas_de,
               modo_qr: str, archivos: list[Path]) -> None:
    from generador_examenes import __version__

    lineas = [f"{datetime.now().isoformat(timespec='seconds')} alucard {__version__} omr build {config.exam_id}",
              f"manifiesto {layout.nombre_archivo(config)} sha256 {huella} ({manifiesto['schema']})",
              f"estudiantes {len(inscriptos)}; variantes "
              + ", ".join(f"{v}: {sum(1 for i in inscriptos if i.variante == v)} ({paginas_de.get(v, 0)} págs.)"
                          for v in config.variants),
              f"qr de configuración {modo_qr}"]
    for archivo in archivos:
        lineas.append(f"sha256 {hashlib.sha256(archivo.read_bytes()).hexdigest()}  {archivo.name}")
    registro.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# --- Hojas auxiliares ------------------------------------------------------------------------------

MODULO_MINIMO = 0.5                 # mm por módulo: más chico, la cámara del teléfono no lo resuelve


def lado_qr(contenido: str, minimo_mm: float) -> float:
    """El lado impreso del QR: el pedido o, si es denso, el que deja 0,5 mm por módulo."""
    modulos = qr.qr_configuracion(contenido).symbol_size(border=0)[0]
    return round(max(minimo_mm, modulos * MODULO_MINIMO), 1)


def _qr_typst(contenido: str, minimo_mm: float) -> str:
    svg, lado = qr.svg(qr.qr_configuracion(contenido)), lado_qr(contenido, minimo_mm)
    return f'image(bytes({_cadena(svg)}), format: "svg", width: {lado}mm, height: {lado}mm)'


def hoja_docente(config: ConfigExamen, manifiesto: dict, huella: str, principal: str, compacto: str | None,
                 motivos: list[str], fuente: str) -> str:
    """La hoja de configuración del escáner (§6.3, §8): QR, rúbrica, sha256 y tabla de notas."""
    escala = config.grade_scale
    filas_rubrica = ", ".join(
        f"[{_e(e.id)}], [{_e(e.label)}], [{notas.formato_nota(e.max_points, escala)}], [{e.levels}], "
        f"[{_e(' · '.join(e.etiquetas()))}]" for e in config.rubric)
    filas_notas = ", ".join(f"[{p:.1f} %], [{notas.formato_nota(g, escala)}], [{c}]"
                            for p, g, c in notas.tabla_verificacion(config))
    tipo = "OMRCFG2: (comprimido)" if principal.startswith("OMRCFG2:") else "OMRCFG/2 (compacto)"
    if compacto:
        respaldo = (f'#figure({_qr_typst(compacto, 40)}, caption: [Respaldo OMRCFG/2 (compacto)], '
                    'numbering: none)')
    elif principal.startswith("OMRCFG2:"):
        respaldo = f"#text(size: 9pt)[Sin respaldo compacto: {_e('; '.join(motivos))}.]"
    else:
        respaldo = ""
    curva = config.grade_map
    promo = (f"promoción {curva.promo_pct:g} % → {curva.promo_grade:g}" if curva.promo_pct is not None
             else "sin promoción")
    return f"""#set page(paper: "a4", margin: 18mm)
#set text(font: {fuente}, size: 10pt, lang: "es")
#set table(stroke: 0.5pt + luma(150), inset: 4pt)
#text(size: 16pt, weight: "bold")[Configuración del escáner OMR]\\
#text(size: 12pt)[{_e(config.title)}]

#rect(width: 100%, inset: 8pt, stroke: 1pt + rgb("#b00020"), fill: rgb("#fdecee"))[
  *Uso exclusivo docente.* Esta hoja contiene la clave del examen (`hmac_key`). No la imprimas
  junto con el mazo de exámenes ni la subas a un repositorio compartido con estudiantes; si la
  imprimís, destruila al cerrar el acta.
]

#grid(columns: ({lado_qr(principal, 60) + 2}mm, 1fr), column-gutter: 8mm,
  figure({_qr_typst(principal, 60)}, caption: [{tipo}], numbering: none),
  [
    *Examen:* `{config.exam_id}` \\
    *Layout:* `{config.layout_id}` versión {config.layout_version} ({manifiesto['schema']}) \\
    *sha256 del manifiesto:* #text(size: 7.5pt, raw({_cadena(huella)})) \\
    *Variantes:* {', '.join(config.variants)} \\
    *Curva:* aprobación {curva.pass_pct:g} % → {curva.pass_grade:g}, {_e(promo)}, k = {curva.curve_k:g} \\
    *Escala:* {escala.min:g} a {escala.max:g}, {escala.decimals} decimal(es), redondeo {escala.rounding}

    Escaneá el QR desde la app Escáner OMR para cargar la identidad del examen, la clave, el
    manifiesto y la curva de notas.

    {respaldo}
  ])

== Rúbrica
#table(columns: (auto, 1fr, auto, auto, auto), table.header([*Id*], [*Ejercicio*], [*Puntos*], [*Niveles*], [*Burbujas*]),
  {filas_rubrica})

== Porcentaje → nota
#table(columns: (auto, auto, auto), table.header([*Porcentaje*], [*Nota*], [*Condición*]),
  {filas_notas})
"""


def hoja_calibracion(manifiesto: dict, ruta_manifiesto: str, fuente: str) -> str:
    """La cabecera con las burbujas rellenas al 0, 25, 50 y 100 % (§8), para calibrar umbrales."""
    niveles = (0.0, 0.25, 0.5, 1.0)
    rellenos, en_fila = {}, {}
    for campo, valor, _x, _y in layout.burbujas(manifiesto):
        n = en_fila[campo] = en_fila.get(campo, -1) + 1
        rellenos[f"{campo}={valor}"] = niveles[n % len(niveles)]
    pares = ", ".join(f"{_cadena(k)}: {v}" for k, v in rellenos.items())
    alto = OY + manifiesto["frame_mm"]["h"] + DIVISORIA
    return f"""{PLANTILLA_CARATULA.read_text(encoding="utf-8")}
#set page(paper: "a4", margin: (top: {alto + 6}mm, rest: 20mm),
  background: place(top + left, omr-franja(json({_cadena(ruta_manifiesto)}), ox: {OX}mm, oy: {OY}mm,
    divisoria: {DIVISORIA}mm, rellenos: ({pares}),
    respaldo: ("Hoja de calibración", {_cadena(f"{manifiesto['layout_id']} v{manifiesto['version']}")}),
    texto: (x: {TEXTO_X}, y: {TEXTO_Y - 12}, ancho: {TEXTO_ANCHO}))))
#set text(font: {fuente}, size: 10pt, lang: "es")
= Hoja de calibración — layout {manifiesto['layout_id']} v{manifiesto['version']}

Imprimí esta hoja en cada impresora al 100 % (tamaño real), sin «Ajustar a página». En cada fila, de
izquierda a derecha, las burbujas están rellenas al 0 %, 25 %, 50 % y 100 % del disco que mide la
app (0,7 r; la de 100 % está pintada entera), y el ciclo vuelve a empezar cada cuatro burbujas.
Escaneala con la app para ajustar los umbrales de marca de esa impresora.
"""


def _e(texto: str) -> str:
    from generador_examenes.generators.typst_markup import escapar

    return escapar(texto)


def resumen_json(lote: Lote) -> dict[str, Any]:
    return {"salida": str(lote.salida), "examenes": str(lote.examenes), "roster": str(lote.nomina),
            "manifiesto": str(lote.manifiesto), "sha256": lote.huella, "config_qr": str(lote.config_qr),
            "config_qr_svg": str(lote.config_qr_svg), "calibracion": str(lote.calibracion),
            "registro": str(lote.registro), "estudiantes": len(lote.inscriptos), "qr_config_mode": lote.modo_qr,
            "avisos": lote.avisos}


def a_json(datos: Any) -> str:
    return json.dumps(datos, indent=2, ensure_ascii=False)
