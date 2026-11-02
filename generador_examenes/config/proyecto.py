"""Configuración del curso en `alucard.toml`: los valores que se repiten en cada corrida.

Se busca desde la carpeta actual hacia arriba, sin salir del repositorio git, y vale como último
nivel: la línea de comandos manda sobre la definición YAML y la definición sobre `alucard.toml`.
Las rutas relativas se resuelven desde la carpeta del archivo.

```toml
input_banco = ["bancos/teoria.gift", "bancos/sintetizados"]
output_dir = "output"
path_images = "imagenes"
numero_temas = 2
semilla = 2026
formato = ["pdf"]

[ortografia]
servidor = "http://localhost:8081"
idioma = "es-AR"
ignorar_reglas = ["WHITESPACE_RULE"]
palabras = ["malloc", "struct", "GIFT"]   # el diccionario de la cátedra
diccionario = "diccionario.txt"            # más palabras, una por renglón (# comenta)
```
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ARCHIVO = "alucard.toml"


@dataclass
class ConfiguracionProyecto:
    ruta: Optional[Path] = None
    input_banco: list[Path] = field(default_factory=list)
    output_dir: Optional[Path] = None
    path_images: Optional[Path] = None
    numero_temas: Optional[int] = None
    semilla: Optional[int] = None
    formato: list[str] = field(default_factory=list)
    lt_servidor: Optional[str] = None
    lt_idioma: Optional[str] = None
    lt_ignorar_reglas: list[str] = field(default_factory=list)
    palabras: list[str] = field(default_factory=list)


def buscar(desde: Optional[Path] = None) -> Optional[Path]:
    """El `alucard.toml` más cercano hacia arriba, sin pasar la raíz del repositorio git."""
    carpeta = (desde or Path.cwd()).resolve()
    for d in (carpeta, *carpeta.parents):
        if (d / ARCHIVO).is_file():
            return d / ARCHIVO
        if (d / ".git").exists():
            return None
    return None


def cargar(desde: Optional[Path] = None) -> ConfiguracionProyecto:
    """La configuración del proyecto, vacía si no hay `alucard.toml`. Un archivo mal escrito es un
    error con el nombre del archivo, no un traceback."""
    ruta = buscar(desde)
    if ruta is None:
        return ConfiguracionProyecto()
    try:
        datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{ruta}: {e}") from e
    base = ruta.parent

    def rutas(valor) -> list[Path]:
        lista = valor if isinstance(valor, list) else [valor] if valor else []
        return [base / str(v) for v in lista]

    def ruta_sola(valor) -> Optional[Path]:
        return base / str(valor) if valor else None

    orto = datos.get("ortografia") or {}
    palabras = [str(p) for p in orto.get("palabras") or []]
    if orto.get("diccionario"):
        archivo = base / str(orto["diccionario"])
        try:
            renglones = archivo.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            raise ValueError(f"{ruta}: no se pudo leer el diccionario {archivo}: {e.strerror}") from e
        palabras += [r.split("#", 1)[0].strip() for r in renglones if r.split("#", 1)[0].strip()]
    formato = datos.get("formato")
    return ConfiguracionProyecto(
        ruta=ruta,
        input_banco=rutas(datos.get("input_banco")),
        output_dir=ruta_sola(datos.get("output_dir")),
        path_images=ruta_sola(datos.get("path_images")),
        numero_temas=datos.get("numero_temas"),
        semilla=datos.get("semilla"),
        formato=[formato] if isinstance(formato, str) else list(formato or []),
        lt_servidor=orto.get("servidor"),
        lt_idioma=orto.get("idioma"),
        lt_ignorar_reglas=list(orto.get("ignorar_reglas") or []),
        palabras=palabras,
    )
