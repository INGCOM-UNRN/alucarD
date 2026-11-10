"""La referencia del manual nombra todas las opciones de la definición YAML y de `alucard.toml`."""
import re
from pathlib import Path

import pytest

from generador_examenes.config import proyecto
from generador_examenes.core import models

REFERENCIA = (Path(__file__).parent.parent / "MANUAL.md").read_text(encoding="utf-8").split("## 6. Referencia de configuración")[1]
MODELOS = (models.DefinicionExamen, models.ConfiguracionExamen, models.PresentacionConsigna, models.SeccionExamen,
           models.PoolConfig, models.RepositorioExterno, models.EstiloExamen)
# Las claves que lee `proyecto.cargar`: `datos.get("x")` y `orto.get("x")`.
CLAVES_TOML = set(re.findall(r'(?:datos|orto)(?:\.get\(|\[)"(\w+)"', Path(proyecto.__file__).read_text(encoding="utf-8")))


@pytest.mark.parametrize("modelo, clave", [(m, c) for m in MODELOS for c in m.model_fields])
def test_cada_clave_del_yaml_esta_documentada(modelo, clave):
    assert f"`{clave}`" in REFERENCIA, f"falta {modelo.__name__}.{clave} en la referencia del manual"


@pytest.mark.parametrize("clave", sorted(CLAVES_TOML - {"ortografia", "estilo"}))
def test_cada_clave_del_toml_esta_documentada(clave):
    assert f"`{clave}`" in REFERENCIA


def test_las_secciones_del_toml_estan_documentadas():
    assert {"ortografia", "estilo"} <= CLAVES_TOML
    assert "#### `[ortografia]`" in REFERENCIA and "#### `[estilo]`" in REFERENCIA


def test_cada_espacio_de_desarrollo_esta_documentado():
    for tamano in models.TamanoDesarrollo.__args__:
        assert f"`{tamano}`" in REFERENCIA
