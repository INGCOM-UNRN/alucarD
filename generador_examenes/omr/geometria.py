"""`alucard omr verify-geometry`: que Typst dibujó cada burbuja donde dice el manifiesto (§11.2).

1. Rasteriza la página a 300 DPI (`pdftoppm`, de poppler).
2. Busca los cuatro marcadores ArUco: manchas oscuras de unos 10 mm en una copia reducida, el borde
   exterior de cada una en la imagen completa y su matriz 6×6, que tiene que ser la de un id 0-3.
3. Con sus centroides arma la homografía del marco canónico (mm desde el marcador 0) a la imagen.
4. Para cada burbuja del manifiesto, mide el centro del contorno dibujado: desde el centro esperado
   sale hacia los cuatro lados hasta cruzar el anillo, y el centro es el punto medio de los cruces.
   El error es la distancia, en mm del marco, entre el centro medido y el del manifiesto.

Sin OpenCV: los marcadores son del PDF que generó alucard (vectoriales, sin rotar), así que basta
con Pillow. Una página escaneada, torcida o con perspectiva es trabajo de la app.

Una página puede tener varios marcos (la planilla docente: un marco por estudiante). Cada marcador 0
se junta con los 1, 2 y 3 que quedan donde los pone el manifiesto, y cada marco se verifica aparte.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from generador_examenes.omr import layout

DPI = 300
TOLERANCIA_MM = 0.3
REDUCCION = 6                      # la copia para buscar manchas: unos 2 px por mm
OSCURO = 128                       # marcadores (negro puro)
CONTORNO = 205                     # el anillo de las burbujas (#999999, 0,5 pt, con antialias)


class ErrorGeometria(RuntimeError):
    pass


@dataclass
class Marcador:
    id: int
    rotacion: int                   # en cuartos de vuelta; 0 en un PDF derecho
    cx: float                       # centroide, en px de la imagen
    cy: float
    lado_mm: float


@dataclass
class Medicion:
    campo: str
    valor: str
    esperado: tuple[float, float]   # mm del marco
    medido: tuple[float, float] | None
    error_mm: float | None
    diametro_mm: float | None


@dataclass
class Pagina:
    numero: int
    marcadores: list[Marcador]
    marco: int = 0                  # en una página con varios marcos, cuál (desde 1); 0 si hay uno solo
    mediciones: list[Medicion] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)

    @property
    def error_maximo(self) -> float | None:
        errores = [m.error_mm for m in self.mediciones if m.error_mm is not None]
        return max(errores) if errores else None

    @property
    def ok(self) -> bool:
        return not self.problemas


# --- Imagen ---------------------------------------------------------------------------------------

def rasterizar(pdf: Path, pagina: int, dpi: int = DPI):
    from PIL import Image

    if shutil.which("pdftoppm") is None:
        raise ErrorGeometria("falta pdftoppm (poppler-utils) para rasterizar el PDF")
    with tempfile.TemporaryDirectory(prefix="alucard-geometria-") as tmp:
        prefijo = Path(tmp) / "pagina"
        res = subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-f", str(pagina), "-l", str(pagina),
                              "-singlefile", str(pdf), str(prefijo)], capture_output=True, text=True, timeout=120,
                             check=False)
        archivo = prefijo.with_suffix(".pgm")
        if res.returncode != 0 or not archivo.exists():
            raise ErrorGeometria(f"pdftoppm no pudo rasterizar la página {pagina}: {res.stderr.strip()}")
        imagen = Image.open(archivo)
        imagen.load()
        return imagen.convert("L")


def _manchas(imagen, px_mm: float) -> list[tuple[int, int, int, int]]:
    """Las cajas (en px de la imagen) de las manchas oscuras de 8,5 a 11,5 mm de lado."""
    from PIL import Image

    chica = imagen.resize((imagen.width // REDUCCION, imagen.height // REDUCCION), Image.Resampling.BOX)
    w, h = chica.size
    datos = chica.tobytes()
    visto = bytearray(w * h)
    cajas = []
    escala = REDUCCION / px_mm
    for inicio in range(w * h):
        if visto[inicio] or datos[inicio] >= OSCURO:
            continue
        cola = deque([inicio])
        visto[inicio] = 1
        x0 = x1 = inicio % w
        y0 = y1 = inicio // w
        while cola:
            i = cola.popleft()
            x, y = i % w, i // w
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
            for j in (i - 1 if x > 0 else -1, i + 1 if x < w - 1 else -1, i - w, i + w):
                if 0 <= j < w * h and not visto[j] and datos[j] < OSCURO:
                    visto[j] = 1
                    cola.append(j)
        ancho, alto = (x1 - x0 + 1) * escala, (y1 - y0 + 1) * escala
        if 8.5 <= ancho <= 11.5 and 8.5 <= alto <= 11.5:
            cajas.append((x0 * REDUCCION, y0 * REDUCCION, (x1 + 1) * REDUCCION, (y1 + 1) * REDUCCION))
    return cajas


def _borde(px, w: int, h: int, x: int, y: int, dx: int, dy: int, silencio: int, limite: int) -> int | None:
    """Desde (x, y) hacia (dx, dy): el último píxel oscuro antes de `silencio` píxeles claros seguidos."""
    ultimo, claros = None, 0
    for paso in range(limite):
        xi, yi = x + dx * paso, y + dy * paso
        if not (0 <= xi < w and 0 <= yi < h):
            break
        if px[xi, yi] < OSCURO:
            ultimo, claros = paso, 0
        else:
            claros += 1
            if claros >= silencio and ultimo is not None:
                break
    return None if ultimo is None else (xi - dx * (paso - ultimo) if dx else yi - dy * (paso - ultimo))


def _rotar(matriz: tuple[str, ...]) -> tuple[str, ...]:
    """Un cuarto de vuelta en sentido horario."""
    n = len(matriz)
    return tuple("".join(matriz[n - 1 - f][c] for f in range(n)) for c in range(n))


def _marcador(imagen, px, caja, px_mm: float) -> Marcador | None:
    w, h = imagen.size
    cx, cy = (caja[0] + caja[2]) // 2, (caja[1] + caja[3]) // 2
    # Adentro del marcador hay a lo sumo 2 celdas blancas seguidas (3,3 mm); afuera, la zona de silencio.
    silencio, limite = int(3.8 * px_mm), int(9 * px_mm)
    bordes = []
    for desvio in (-int(1.5 * px_mm), 0, int(1.5 * px_mm)):
        izq = _borde(px, w, h, cx, cy + desvio, -1, 0, silencio, limite)
        der = _borde(px, w, h, cx, cy + desvio, 1, 0, silencio, limite)
        arr = _borde(px, w, h, cx + desvio, cy, 0, -1, silencio, limite)
        aba = _borde(px, w, h, cx + desvio, cy, 0, 1, silencio, limite)
        if None in (izq, der, arr, aba):
            return None
        bordes.append((izq, der, arr, aba))
    izq = sorted(b[0] for b in bordes)[1]
    der = sorted(b[1] for b in bordes)[1]
    arr = sorted(b[2] for b in bordes)[1]
    aba = sorted(b[3] for b in bordes)[1]
    lado_x, lado_y = der - izq + 1, aba - arr + 1
    celda_x, celda_y = lado_x / 6, lado_y / 6
    filas = []
    for f in range(6):
        fila = ""
        for c in range(6):
            x, y = int(izq + (c + 0.5) * celda_x), int(arr + (f + 0.5) * celda_y)
            valores = [px[x + i, y + j] for i in (-2, 0, 2) for j in (-2, 0, 2)]
            fila += "0" if sum(valores) / len(valores) < OSCURO else "1"
        filas.append(fila)
    if any(c != "0" for c in filas[0] + filas[5] + "".join(f[0] + f[5] for f in filas)):
        return None
    interior = tuple(f[1:5] for f in filas[1:5])
    for id_, matriz in layout.ARUCO.items():
        rotada = tuple(matriz)
        for giro in range(4):
            if interior == rotada:
                return Marcador(id=id_, rotacion=giro, cx=(izq + der + 1) / 2, cy=(arr + aba + 1) / 2,
                                lado_mm=(lado_x + lado_y) / 2 / px_mm)
            rotada = _rotar(rotada)
    return None


def marcadores(imagen, px_mm: float) -> list[Marcador]:
    px = imagen.load()
    encontrados = [m for caja in _manchas(imagen, px_mm) if (m := _marcador(imagen, px, caja, px_mm))]
    return sorted(encontrados, key=lambda m: m.id)


# --- Homografía -----------------------------------------------------------------------------------

def _resolver(a: list[list[float]], b: list[float]) -> list[float]:
    """Eliminación gaussiana con pivoteo parcial."""
    n = len(b)
    m = [fila[:] + [b[i]] for i, fila in enumerate(a)]
    for col in range(n):
        pivote = max(range(col, n), key=lambda f: abs(m[f][col]))
        if abs(m[pivote][col]) < 1e-12:
            raise ErrorGeometria("los marcadores no definen un marco (están alineados)")
        m[col], m[pivote] = m[pivote], m[col]
        for f in range(n):
            if f != col:
                k = m[f][col] / m[col][col]
                m[f] = [x - k * y for x, y in zip(m[f], m[col], strict=True)]
    return [m[i][n] / m[i][i] for i in range(n)]


def homografia(origen: list[tuple[float, float]], destino: list[tuple[float, float]]) -> list[list[float]]:
    a, b = [], []
    for (x, y), (u, v) in zip(origen, destino, strict=True):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    h = _resolver(a, b)
    return [h[0:3], h[3:6], [h[6], h[7], 1.0]]


def aplicar(h: list[list[float]], x: float, y: float) -> tuple[float, float]:
    w = h[2][0] * x + h[2][1] * y + h[2][2]
    return ((h[0][0] * x + h[0][1] * y + h[0][2]) / w, (h[1][0] * x + h[1][1] * y + h[1][2]) / w)


def inversa(h: list[list[float]]) -> list[list[float]]:
    (a, b, c), (d, e, f), (g, i, j) = h
    det = a * (e * j - f * i) - b * (d * j - f * g) + c * (d * i - e * g)
    return [[(e * j - f * i) / det, (c * i - b * j) / det, (b * f - c * e) / det],
            [(f * g - d * j) / det, (a * j - c * g) / det, (c * d - a * f) / det],
            [(d * i - e * g) / det, (b * g - a * i) / det, (a * e - b * d) / det]]


# --- Burbujas -------------------------------------------------------------------------------------

def _cruce(px, w: int, h: int, x: float, y: float, dx: int, dy: int, limite: int) -> float | None:
    """Desde (x, y): la posición (en px, a lo largo del eje) del medio del primer tramo oscuro."""
    xi, yi = int(x), int(y)
    inicio = None
    for paso in range(limite):
        xp, yp = xi + dx * paso, yi + dy * paso
        if not (0 <= xp < w and 0 <= yp < h):
            return None
        oscuro = px[xp, yp] < CONTORNO
        if oscuro and inicio is None:
            inicio = paso
        elif not oscuro and inicio is not None:
            medio = (inicio + paso - 1) / 2
            return (xi + dx * medio + 0.5) if dx else (yi + dy * medio + 0.5)
    return None


def medir_burbuja(px, w: int, h: int, cx: float, cy: float, radio_px: float) -> tuple[float, float, float] | None:
    """El centro (px) y el diámetro (px) del contorno que rodea a (cx, cy)."""
    limite = int(radio_px * 1.6)
    xs, ys, diametros = [], [], []
    for desvio in (-0.35 * radio_px, 0.0, 0.35 * radio_px):
        izq = _cruce(px, w, h, cx, cy + desvio, -1, 0, limite)
        der = _cruce(px, w, h, cx, cy + desvio, 1, 0, limite)
        arr = _cruce(px, w, h, cx + desvio, cy, 0, -1, limite)
        aba = _cruce(px, w, h, cx + desvio, cy, 0, 1, limite)
        if None in (izq, der, arr, aba):
            return None
        xs.append((izq + der) / 2)
        ys.append((arr + aba) / 2)
        if desvio == 0.0:
            diametros += [der - izq, aba - arr]
    return sum(xs) / len(xs), sum(ys) / len(ys), sum(diametros) / len(diametros)


def marcos(encontrados: list[Marcador], manifiesto: dict[str, Any], px_mm: float,
           holgura_mm: float = 5.0) -> tuple[list[list[Marcador]], list[Marcador]]:
    """Agrupa los marcadores de una página en marcos [0, 1, 2, 3], de arriba hacia abajo, y devuelve
    también los que no forman ninguno."""
    w, h = manifiesto["frame_mm"]["w"] * px_mm, manifiesto["frame_mm"]["h"] * px_mm
    libres = list(encontrados)
    grupos = []
    for cero in sorted((m for m in encontrados if m.id == 0), key=lambda m: (m.cy, m.cx)):
        grupo = [cero]
        for id_, dx, dy in ((1, w, 0.0), (2, w, h), (3, 0.0, h)):
            esperado = (cero.cx + dx, cero.cy + dy)
            candidatos = [m for m in libres if m.id == id_]
            if not candidatos:
                break
            mejor = min(candidatos, key=lambda m: math.dist((m.cx, m.cy), esperado))
            if math.dist((mejor.cx, mejor.cy), esperado) > holgura_mm * px_mm:
                break
            grupo.append(mejor)
        if len(grupo) == 4:
            grupos.append(grupo)
            libres = [m for m in libres if all(m is not g for g in grupo)]
    return grupos, libres


def _verificar_marco(imagen, manifiesto: dict[str, Any], pagina: Pagina, tolerancia: float, px_mm: float) -> None:
    por_id = {m.id: m for m in pagina.marcadores}
    for m in pagina.marcadores:
        if m.rotacion:
            pagina.problemas.append(f"el marcador {m.id} está rotado {m.rotacion * 90}°")
        if abs(m.lado_mm - manifiesto["marker_mm"]) > tolerancia:
            pagina.problemas.append(f"el marcador {m.id} mide {m.lado_mm:.2f} mm (debería medir "
                                    f"{manifiesto['marker_mm']:g})")
    w_mm, h_mm = manifiesto["frame_mm"]["w"], manifiesto["frame_mm"]["h"]
    canonico = [(0.0, 0.0), (w_mm, 0.0), (w_mm, h_mm), (0.0, h_mm)]
    h = homografia(canonico, [(por_id[i].cx, por_id[i].cy) for i in range(4)])
    h_inv = inversa(h)
    ancho_medido = math.dist((por_id[0].cx, por_id[0].cy), (por_id[1].cx, por_id[1].cy)) / px_mm
    if abs(ancho_medido - w_mm) > tolerancia:
        pagina.problemas.append(f"entre los marcadores 0 y 1 hay {ancho_medido:.2f} mm (el marco mide {w_mm:g}): "
                                "la página no está en tamaño real")

    px = imagen.load()
    radio_px = manifiesto["bubble_diameter_mm"] / 2 * px_mm
    for campo, valor, x, y in layout.burbujas(manifiesto):
        cx, cy = aplicar(h, x, y)
        medida = medir_burbuja(px, imagen.width, imagen.height, cx, cy, radio_px)
        if medida is None:
            pagina.mediciones.append(Medicion(campo, valor, (x, y), None, None, None))
            pagina.problemas.append(f"{campo}={valor}: no se encontró el contorno alrededor de ({x:g}, {y:g}) mm")
            continue
        mx, my = aplicar(h_inv, medida[0], medida[1])
        error = math.dist((mx, my), (x, y))
        diametro = medida[2] / px_mm
        pagina.mediciones.append(Medicion(campo, valor, (x, y), (mx, my), error, diametro))
        if error >= tolerancia:
            pagina.problemas.append(f"{campo}={valor}: el contorno está en ({mx:.2f}, {my:.2f}) mm, "
                                    f"a {error:.2f} mm de ({x:g}, {y:g})")
        elif abs(diametro - manifiesto["bubble_diameter_mm"]) >= tolerancia:
            pagina.problemas.append(f"{campo}={valor}: el contorno mide {diametro:.2f} mm "
                                    f"(debería medir {manifiesto['bubble_diameter_mm']:g})")


def verificar_marcos(imagen, manifiesto: dict[str, Any], numero: int = 1, tolerancia: float = TOLERANCIA_MM,
                     dpi: int = DPI) -> list[Pagina]:
    """Un resultado por marco de la página. Con un solo juego de marcadores 0-3 (la carátula), uno;
    en la planilla docente, uno por estudiante. Sin ningún marco completo, un resultado con el problema."""
    px_mm = dpi / 25.4
    encontrados = marcadores(imagen, px_mm)
    ids = [m.id for m in encontrados]
    if sorted(ids) == [0, 1, 2, 3]:
        pagina = Pagina(numero=numero, marcadores=encontrados)
        _verificar_marco(imagen, manifiesto, pagina, tolerancia, px_mm)
        return [pagina]
    grupos, libres = marcos(encontrados, manifiesto, px_mm)
    if not grupos:
        pagina = Pagina(numero=numero, marcadores=encontrados)
        pagina.problemas.append(f"se esperaban los marcadores 0, 1, 2 y 3; se encontraron {ids or 'ninguno'}")
        return [pagina]
    resultado = []
    for n, grupo in enumerate(grupos, 1):
        pagina = Pagina(numero=numero, marcadores=grupo, marco=n)
        _verificar_marco(imagen, manifiesto, pagina, tolerancia, px_mm)
        resultado.append(pagina)
    if libres:
        resultado[-1].problemas.append(f"marcadores que no forman un marco: {[m.id for m in libres]}")
    return resultado


def verificar_pagina(imagen, manifiesto: dict[str, Any], numero: int = 1, tolerancia: float = TOLERANCIA_MM,
                     dpi: int = DPI) -> Pagina:
    """El primer marco de la página (la carátula tiene uno solo)."""
    return verificar_marcos(imagen, manifiesto, numero, tolerancia, dpi)[0]


def paginas_del_pdf(pdf: Path) -> int:
    import pypdf

    return len(pypdf.PdfReader(str(pdf)).pages)


def verificar(pdf: Path, manifiesto: dict[str, Any], paginas: list[int] | None = None,
              tolerancia: float = TOLERANCIA_MM) -> list[Pagina]:
    """Verifica las páginas pedidas (por omisión, la 1). Con `paginas=[]`, todas las que tengan carátula:
    las que no tienen los cuatro marcadores se saltean."""
    todas = paginas is not None and not paginas
    numeros = range(1, paginas_del_pdf(pdf) + 1) if todas else (paginas or [1])
    salida = []
    for n in numeros:
        for pagina in verificar_marcos(rasterizar(pdf, n), manifiesto, n, tolerancia):
            if todas and not pagina.marcadores:
                continue
            salida.append(pagina)
    return salida


def texto(paginas: list[Pagina], tolerancia: float = TOLERANCIA_MM) -> str:
    lineas = []
    for p in paginas:
        medidas = [m for m in p.mediciones if m.error_mm is not None]
        maximo = p.error_maximo
        estado = "✓" if p.ok else "✗"
        detalle = (f"{len(medidas)} burbujas, error máximo {maximo:.3f} mm (tolerancia < {tolerancia:g} mm)"
                   if maximo is not None else "sin burbujas medidas")
        donde = f"página {p.numero}" + (f", marco {p.marco}" if p.marco else "")
        lineas.append(f"{estado} {donde}: {len(p.marcadores)} marcadores; {detalle}")
        lineas += [f"    {problema}" for problema in p.problemas]
    return "\n".join(lineas)


def a_dict(paginas: list[Pagina]) -> list[dict[str, Any]]:
    return [{"pagina": p.numero, "marco": p.marco, "ok": p.ok, "marcadores": [m.id for m in p.marcadores],
             "error_maximo_mm": p.error_maximo, "burbujas": len(p.mediciones), "problemas": p.problemas}
            for p in paginas]
