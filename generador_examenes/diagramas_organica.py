"""Diagramas de química orgánica (estereoquímica y conformaciones) para los bloques ```` ```estructura ````.

| `type` | Qué dibuja |
| --- | --- |
| `newman` | Proyección de Newman: los sustituyentes del carbono de adelante y del de atrás, con el diedro y el nombre de la conformación (anti, gauche, eclipsada). |
| `chair` | Silla del ciclohexano con sustituyentes axiales y ecuatoriales, la inversión del anillo, cis/trans y el confórmero más estable por los valores A. |
| `fischer` | Proyección de Fischer de uno o varios estereocentros, con R/S por las reglas de Cahn-Ingold-Prelog y la serie D/L. |

Las estructuras y los mecanismos (Lewis, esqueletales, cuñas, flechas curvas) son `molecule` y `reaction`,
en `diagramas_quimica`. Las cuentas están en `generador_examenes.quimica`.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from generador_examenes import diagramas as d
from generador_examenes import quimica as q
from generador_examenes.diagramas_quimica import _caja_vacia, _encabezado_q, _errores, _rotulo_q, _tq, ancho_formula

Punto = tuple[float, float]


def _info(c: d._Lienzo, x: float, y: float, filas: list[tuple[str, str, bool]]) -> float:
    """Renglones `nombre: valor` (o para completar); devuelve dónde termina."""
    for nombre, valor, blanco in filas:
        c.t(x, y, f"{nombre}:", size=10.5, peso=700, fuente=d.SANS)
        x_valor = x + ancho_formula(nombre + ":", 10.5) * 1.08 + 8
        if blanco:
            c.vacio(x_valor, x_valor + 120, y + 2)
        else:
            _tq(c, x_valor, y, valor, size=10.5)
        y += 20
    return y


# --- Newman ---------------------------------------------------------------------------------------------

@_errores
def _newman(c: d._Lienzo, b: dict) -> Punto:
    adelante = [str(x) for x in (b.get("front") or [])]
    atras = [str(x) for x in (b.get("back") or [])]
    if len(adelante) != 3 or len(atras) != 3:
        raise d.ErrorDiagrama("newman: front y back son los tres sustituyentes de cada carbono")
    diedro = float(b.get("dihedral", 180))
    top = _encabezado_q(c, b)
    cx, cy, r, largo = 120.0, top + 110, 30.0, 70.0
    trazo = c.pal["strokeMain"]
    inicio = float(b.get("start", 90))
    # Atrás: salen del borde del círculo; un eclipsado exacto se corre 8° para que se vean los dos.
    correccion = 16 if abs(diedro % 120) < 1e-9 else 0
    for k, etiqueta in enumerate(atras):
        ang = math.radians(inicio + diedro + correccion + 120 * k)
        x1, y1 = cx + r * math.cos(ang), cy - r * math.sin(ang)
        x2, y2 = cx + largo * math.cos(ang), cy - largo * math.sin(ang)
        c.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{trazo}" stroke-width="1.6"/>')
        afuera = largo + (24 if correccion else 14)
        _tq(c, cx + afuera * math.cos(ang), cy - afuera * math.sin(ang) + 4, etiqueta, size=11, ancla="middle")
    c.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{c.pal["fillCell"]}" stroke="{trazo}" '
          'stroke-width="1.8"/>')
    for k, etiqueta in enumerate(adelante):
        ang = math.radians(inicio + 120 * k)
        x2, y2 = cx + largo * math.cos(ang), cy - largo * math.sin(ang)
        c.add(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{trazo}" stroke-width="1.8"/>')
        _tq(c, cx + (largo + 14) * math.cos(ang), cy - (largo + 14) * math.sin(ang) + 4, etiqueta, size=11,
            peso=600, ancla="middle")
    c.punto(cx, cy, color="strokeMain", radio=2.2)
    nombre = q.conformacion_newman(diedro)
    blanco = bool(b.get("blank"))
    eje = b.get("axis")
    filas = [("Diedro", f"{abs((diedro + 180) % 360 - 180):g}°", blanco or bool(b.get("blankDihedral"))),
             ("Conformación", nombre, blanco or bool(b.get("blankName")))]
    y = top + 70
    if eje:
        _tq(c, 270, y - 26, f"Mirando a lo largo de {eje}", size=10, color="textSub")
    y = _info(c, 270, y, filas)
    return 500, max(top + 210, y)


# --- Silla del ciclohexano ------------------------------------------------------------------------------

# La silla sale de la geometría real: los carbonos alrededor del eje z, alternando arriba y abajo, vistos
# un poco desde arriba. Así los axiales quedan verticales y los ecuatoriales, paralelos a enlaces del anillo.
_RADIO, _ALTURA, _ELEVACION, _ESCALA = 1.0, 0.36, math.radians(20), 58.0


def _proyectar(x: float, y: float, z: float) -> Punto:
    return x * _ESCALA, (-z * math.cos(_ELEVACION) - y * math.sin(_ELEVACION)) * _ESCALA


def _carbono(i: int, invertida: bool) -> tuple[float, float, float]:
    theta = math.radians(60 * (i - 1))
    signo = 1 if (i % 2 == 1) != invertida else -1
    return _RADIO * math.cos(theta), _RADIO * math.sin(theta), signo * _ALTURA


def _dibujar_silla(c: d._Lienzo, x0: float, y0: float, sustituyentes: list[dict], invertida: bool) -> None:
    trazo = c.pal["strokeMain"]
    tres_d = [_carbono(i, invertida) for i in range(1, 7)]
    puntos = [(x0 + px, y0 + py) for px, py in (_proyectar(*p) for p in tres_d)]
    c.add(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)}" fill="none" stroke="{trazo}" '
          'stroke-width="1.7" stroke-linejoin="round"/>')
    for i, ((x, y), (_, _, z)) in enumerate(zip(puntos, tres_d), 1):
        c.t(x + 9, y + (12 if z < 0 else -5), str(i), size=8, color="textMuted", ancla="middle", fuente=d.SANS)
    for s in sustituyentes:
        i = s["position"]
        cx3, cy3, cz3 = tres_d[i - 1]
        x, y = puntos[i - 1]
        signo = 1 if cz3 > 0 else -1                 # el axial apunta para el lado del carbono
        if s["axial"]:
            vector = (0.0, 0.0, signo * 0.62)
        else:
            norma = math.hypot(cx3, cy3)
            vector = (cx3 / norma * 0.62, cy3 / norma * 0.62, -signo * 0.2)
        fin = _proyectar(cx3 + vector[0], cy3 + vector[1], cz3 + vector[2])
        dx, dy = fin[0] - (x - x0), fin[1] - (y - y0)
        c.add(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + dx:.1f}" y2="{y + dy:.1f}" stroke="{trazo}" '
              'stroke-width="1.4"/>')
        norma = math.hypot(dx, dy) or 1
        ex, ey = x + dx + dx / norma * 12, y + dy + dy / norma * 10
        if s.get("blank"):
            _caja_vacia(c, ex, ey, 26, 14)
        else:
            _tq(c, ex, ey + 4, s["group"], size=10, ancla="middle")


def _sustituyentes(b: dict) -> list[dict]:
    salida = []
    for i, s in enumerate(b.get("substituents") or []):
        if not isinstance(s, dict) or "position" not in s or "group" not in s:
            raise d.ErrorDiagrama(f"chair: substituents[{i}] es {{position: 1-6, group, axial}}")
        posicion = int(s["position"])
        if not 1 <= posicion <= 6:
            raise d.ErrorDiagrama(f"chair: substituents[{i}].position va de 1 a 6")
        salida.append({"position": posicion, "group": str(s["group"]), "axial": bool(s.get("axial")),
                       "blank": bool(s.get("blank"))})
    return salida


@_errores
def _silla(c: d._Lienzo, b: dict) -> Punto:
    sust = _sustituyentes(b)
    top = _encabezado_q(c, b) + 70
    _dibujar_silla(c, 110, top, sust, False)
    ancho = 230.0
    invertidos = [{**s, "axial": not s["axial"]} for s in sust]
    if b.get("flip"):
        c.add(f'<path d="M 236 {top - 3:.1f} L 276 {top - 3:.1f} L 269 {top - 8:.1f}" fill="none" '
              f'stroke="{c.pal["accentPrimary"]}" stroke-width="1.5"/>'
              f'<path d="M 276 {top + 3:.1f} L 236 {top + 3:.1f} L 243 {top + 8:.1f}" fill="none" '
              f'stroke="{c.pal["accentPrimary"]}" stroke-width="1.5"/>')
        _dibujar_silla(c, 400, top, invertidos, True)
        ancho = 510.0
    y = top + 80
    blanco = bool(b.get("blank"))
    relacion = q.relacion_cis_trans(sust)
    filas = []
    if relacion and b.get("showRelation", True):
        nombres = [s for s in sust if s["group"] != "H"]
        filas.append(("Relación", f"{relacion} ({nombres[0]['position']},{nombres[1]['position']})",
                      blanco or bool(b.get("blankRelation"))))
    if b.get("flip") and b.get("showStability", True) and all(s["group"] in q.VALORES_A for s in sust):
        a1, a2 = q.costo_axial(sust), q.costo_axial(invertidos)
        if abs(a1 - a2) < 1e-9:
            texto = "las dos sillas tienen la misma energía"
        else:
            texto = f"la {'izquierda' if a1 < a2 else 'derecha'}, por {q._corto(round(abs(a1 - a2), 1))} kJ/mol"
        filas.append(("Más estable", texto, blanco or bool(b.get("blankStability"))))
    y = _info(c, 0, y, filas)
    return ancho, y


# --- Fischer --------------------------------------------------------------------------------------------

_LUGARES = ("top", "right", "bottom", "left")


@_errores
def _fischer(c: d._Lienzo, b: dict) -> Punto:
    centros = b.get("centers")
    if not isinstance(centros, list) or not centros:
        raise d.ErrorDiagrama("fischer: centers es una lista de {left, right} (de arriba hacia abajo)")
    arriba, abajo = str(b.get("top", "")), str(b.get("bottom", ""))
    top = _encabezado_q(c, b) + 20
    cx, paso, brazo = 120.0, 52.0, 46.0
    trazo = c.pal["strokeMain"]
    y = top + 14
    _tq(c, cx, y, arriba, size=11.5, peso=600, ancla="middle")
    y += 8
    resultados = []
    blanco = bool(b.get("blank"))
    for i, centro in enumerate(centros):
        if not isinstance(centro, dict) or "left" not in centro or "right" not in centro:
            raise d.ErrorDiagrama(f"fischer: centers[{i}] es {{left, right}}")
        yc = y + paso * (i + 0.5) + 6
        c.add(f'<line x1="{cx:.1f}" y1="{yc - paso / 2:.1f}" x2="{cx:.1f}" y2="{yc + paso / 2:.1f}" stroke="{trazo}" '
              f'stroke-width="1.6"/><line x1="{cx - brazo:.1f}" y1="{yc:.1f}" x2="{cx + brazo:.1f}" y2="{yc:.1f}" '
              f'stroke="{trazo}" stroke-width="1.6"/>')
        for lado, signo in (("left", -1), ("right", 1)):
            texto = str(centro[lado])
            if centro.get("blank") == lado or centro.get("blank") is True:
                _caja_vacia(c, cx + signo * (brazo + 18), yc, 30, 15)
            else:
                _tq(c, cx + signo * (brazo + 4), yc + 4, texto, size=11, ancla="start" if signo > 0 else "end")
        # R/S: con priorities (lugares de mayor a menor) o, en un único centro, por CIP.
        config = None
        if "priorities" in centro:
            lugares = [str(p) for p in centro["priorities"]]
            if sorted(lugares) != sorted(_LUGARES):
                raise d.ErrorDiagrama(f"fischer: centers[{i}].priorities son top, right, bottom y left, en orden")
            config = q.configuracion_fischer({lugar: k + 1 for k, lugar in enumerate(lugares)})
        elif len(centros) == 1:
            grupos = [arriba, str(centro["right"]), abajo, str(centro["left"])]
            rango = q.prioridades(grupos)
            config = q.configuracion_fischer(dict(zip(_LUGARES, rango)))
        resultados.append(config)
        if config and b.get("showConfig", True):
            if blanco or b.get("blankConfig"):
                _caja_vacia(c, cx + brazo + 90, yc, 22, 15)
            else:
                c.t(cx + brazo + 90, yc + 4, f"({config})", size=11, peso=700, color="textSub", ancla="middle",
                    fuente=d.SANS)
    y_fin = y + paso * len(centros) + 20
    _tq(c, cx, y_fin, abajo, size=11.5, peso=600, ancla="middle")
    y_fin += 26
    serie = None
    ultimo = centros[-1]
    for grupo in ("OH", "NH2", "NH3^+"):
        if str(ultimo["right"]) == grupo:
            serie = "D"
        elif str(ultimo["left"]) == grupo:
            serie = "L"
    if serie and b.get("showSeries", True):
        _rotulo_q(c, 0, y_fin, "Serie", serie, blanco or bool(b.get("blankSeries")), size=10.5)
        y_fin += 20
    return max(320.0, cx + brazo + 120), y_fin


RENDERIZADORES: dict[str, Callable[[d._Lienzo, dict], Punto]] = {
    "newman": _newman, "chair": _silla, "fischer": _fischer,
}
