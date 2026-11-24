"""La clave del examen y los QR que emite el generador (§6).

- La carátula de cada estudiante: `V/EXAM_ID/STUDENT_ID/VARIANT/LAYOUT_ID:VER/CHK` en modo
  alfanumérico, versión 3, corrección Q. `CHK` son los 4 primeros caracteres Base32 del
  HMAC-SHA256 del resto con la `hmac_key` del examen.
- El pie de las páginas 2..N: `EXAM_ID/STUDENT_ID/P<n>`, para reagrupar hojas sueltas.
- La configuración del escáner, sólo para docentes: `OMRCFG2:` (JSON comprimido, el principal) y,
  cuando el layout es el estándar y la configuración entra, el compacto `OMRCFG/2`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import re
import secrets
import zlib
from typing import Any
from urllib.parse import quote_plus

import segno

from generador_examenes.omr.config import ConfigExamen

VERSION_CARATULA = 1
CAPACIDAD_CARATULA = 47          # alfanuméricos de un QR versión 3, corrección Q
ALFANUMERICO = re.compile(r"^[0-9A-Z $%*+\-./:]*$")
ESQUEMA_CONFIG = "omr-exam-config/2"


def nueva_clave() -> str:
    """16 bytes de entropía criptográfica en Base32 RFC 4648 sin `=`: 26 caracteres A-Z2-7."""
    return base64.b32encode(secrets.token_bytes(16)).decode("ascii").rstrip("=")


def clave_valida(clave: str) -> bool:
    return bool(re.fullmatch(r"[A-Z2-7]{26}", clave))


def compute_chk(body_without_chk: str, hmac_key: str) -> str:
    digest = hmac.new(hmac_key.encode("utf-8"), body_without_chk.encode("utf-8"), hashlib.sha256).digest()
    return base64.b32encode(digest).decode("ascii")[:4]


def cuerpo_caratula(config: ConfigExamen, student_id: str, variante: str) -> str:
    return f"{VERSION_CARATULA}/{config.exam_id}/{student_id}/{variante}/{config.layout_id}:{config.layout_version}"


def contenido_caratula(config: ConfigExamen, student_id: str, variante: str, hmac_key: str) -> str:
    cuerpo = cuerpo_caratula(config, student_id, variante)
    return f"{cuerpo}/{compute_chk(cuerpo, hmac_key)}"


def verificar_caratula(contenido: str, hmac_key: str) -> bool:
    cuerpo, _, chk = contenido.rpartition("/")
    return bool(cuerpo) and hmac.compare_digest(compute_chk(cuerpo, hmac_key), chk)


def largo_maximo_caratula(config: ConfigExamen, largo_student_id: int) -> int:
    return len(cuerpo_caratula(config, "X" * largo_student_id, "A")) + 5


def contenido_pie(config: ConfigExamen, student_id: str, pagina: int) -> str:
    return f"{config.exam_id}/{student_id}/P{pagina}"


def qr_caratula(contenido: str) -> segno.QRCode:
    if len(contenido) > CAPACIDAD_CARATULA or not ALFANUMERICO.match(contenido):
        raise ValueError(f"el QR de la carátula no entra en una versión 3-Q alfanumérica: {contenido!r}")
    return segno.make(contenido, error="q", version=3, mode="alphanumeric", boost_error=False)


def qr_pie(contenido: str) -> segno.QRCode:
    return segno.make(contenido, error="m", mode="alphanumeric", boost_error=False)


def svg(qr: segno.QRCode, borde: int = 0) -> str:
    """El QR como SVG vectorial en negro puro, sin la zona de silencio (la deja el layout)."""
    salida = io.BytesIO()
    qr.save(salida, kind="svg", xmldecl=False, svgns=True, svgclass=None, lineclass=None, scale=1, border=borde,
            dark="#000000", light=None)
    return salida.getvalue().decode("utf-8")


# --- Configuración del escáner --------------------------------------------------------------------

def sobre_configuracion(config: ConfigExamen, hmac_key: str, manifiesto: dict[str, Any]) -> dict[str, Any]:
    return {"schema": ESQUEMA_CONFIG, "exam_id": config.exam_id, "title": config.title, "hmac_key": hmac_key,
            "cloud_sync": config.cloud_sync_default, "manifest": manifiesto}


def config_comprimida(config: ConfigExamen, hmac_key: str, manifiesto: dict[str, Any]) -> str:
    crudo = json.dumps(sobre_configuracion(config, hmac_key, manifiesto), separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")
    b64 = base64.urlsafe_b64encode(zlib.compress(crudo, level=9)).rstrip(b"=").decode("ascii")
    return f"OMRCFG2:{b64}"


def leer_config_comprimida(contenido: str) -> dict[str, Any]:
    """La inversa de `config_comprimida`, para las pruebas de interoperabilidad (§11.3)."""
    if not contenido.startswith("OMRCFG2:"):
        raise ValueError("no es un QR OMRCFG2:")
    b64 = contenido[len("OMRCFG2:"):]
    return json.loads(zlib.decompress(base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))).decode("utf-8"))


def motivos_sin_compacto(config: ConfigExamen) -> list[str]:
    """Lo que el QR compacto `OMRCFG/2` no puede llevar: con algo de esto, sólo vale `OMRCFG2:`."""
    escala, motivos = config.grade_scale, []
    if (escala.min, escala.max) != (1.0, 10.0):
        motivos.append(f"la escala no es de 1 a 10 ({escala.min:g} a {escala.max:g})")
    if escala.rounding != "half_up":
        motivos.append(f"el redondeo es {escala.rounding}")
    if any(e.labels for e in config.rubric):
        motivos.append("hay ejercicios con etiquetas propias en las burbujas")
    if config.cloud_sync_default:
        motivos.append("cloud_sync_default está activo")
    return motivos


def _n(x: float) -> str:
    return f"{x:g}"


def config_compacta(config: ConfigExamen, hmac_key: str) -> str:
    """`OMRCFG/2/<EXAM_ID>/<LAYOUT_ID>:<VER>/<HMAC_KEY>/<PASS>:<PROMO>:<PROMO_GRADE>:<K>/<DEC>:<STEP>:<TOL>/<EX_SPEC>/<TITULO_URL>`."""
    motivos = motivos_sin_compacto(config)
    if motivos:
        raise ValueError("el QR compacto OMRCFG/2 no alcanza: " + "; ".join(motivos))
    curva, escala = config.grade_map, config.grade_scale
    promo = (
        "NONE:0"
        if curva.promo_pct is None or curva.promo_grade is None
        else f"{_n(curva.promo_pct)}:{_n(curva.promo_grade)}"
    )
    paso = "" if escala.step is None else _n(escala.step)
    ejercicios = ",".join(f"{e.id}:{_n(e.max_points)}:{e.levels}:{quote_plus(e.label)}" for e in config.rubric)
    return "/".join(["OMRCFG", "2", config.exam_id, f"{config.layout_id}:{config.layout_version}", hmac_key,
                     f"{_n(curva.pass_pct)}:{promo}:{_n(curva.curve_k)}",
                     f"{escala.decimals}:{paso}:{escala.match_tolerance}", ejercicios, quote_plus(config.title)])


def qr_configuracion(contenido: str) -> segno.QRCode:
    return segno.make(contenido, error="m", boost_error=False)
