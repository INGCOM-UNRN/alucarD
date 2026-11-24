"""Tests para el subcomando doctor (ALUCARD-D0401)."""
from unittest.mock import patch

from rich.console import Console

from generador_examenes.core import doctor
from generador_examenes import cli_commands


def test_chequear_binario_ausente():
    resultado = doctor.chequear_binario("comando-inexistente-xyz")
    assert resultado["disponible"] is False
    assert resultado["version"] is None


def test_chequear_binario_presente():
    resultado = doctor.chequear_binario("sh")
    assert resultado["disponible"] is True
    assert resultado["ruta"]


def test_chequear_modulo_python_ausente():
    resultado = doctor.chequear_modulo_python("modulo_inexistente_xyz")
    assert resultado["disponible"] is False


def test_chequear_modulo_python_presente():
    resultado = doctor.chequear_modulo_python("json")
    assert resultado["disponible"] is True


def test_chequear_conectividad_languagetool_maneja_error_de_red():
    with patch("urllib.request.urlopen", side_effect=OSError("sin red")):
        resultado = doctor.chequear_conectividad_languagetool()
    assert resultado["disponible"] is False
    assert "sin red" in resultado["detalle"]


def test_diagnostico_ok_cuando_todo_disponible():
    disponible = {"disponible": True, "version": "1.0", "ruta": "/usr/bin/x", "importable": True}
    with patch.object(doctor, "chequear_binario", return_value=disponible), \
         patch.object(doctor, "chequear_modulo_python", return_value=disponible), \
         patch.object(doctor, "chequear_conectividad_languagetool", return_value={"disponible": True, "detalle": "HTTP 200"}):
        ok = doctor.ejecutar_diagnostico_doctor(console=Console(file=open("/dev/null", "w")))
    assert ok is True


def test_diagnostico_falla_cuando_falta_requisito_obligatorio():
    ausente = {"disponible": False, "version": None, "ruta": None, "importable": False}
    with patch.object(doctor, "chequear_binario", return_value=ausente), \
         patch.object(doctor, "chequear_modulo_python", return_value=ausente), \
         patch.object(doctor, "chequear_conectividad_languagetool", return_value={"disponible": False, "detalle": "sin red"}):
        ok = doctor.ejecutar_diagnostico_doctor(console=Console(file=open("/dev/null", "w")))
    assert ok is False


def test_diagnostico_lo_opcional_no_afecta_resultado():
    disponible = {"disponible": True, "version": "1.0", "ruta": "/usr/bin/x", "importable": True}
    with patch.object(doctor, "chequear_binario", return_value=disponible), \
         patch.object(doctor, "chequear_modulo_python", return_value=disponible), \
         patch.object(doctor, "chequear_conectividad_languagetool", return_value={"disponible": False, "detalle": "sin red"}):
        ok = doctor.ejecutar_diagnostico_doctor(console=Console(file=open("/dev/null", "w")))
    assert ok is True


def test_ejecutar_doctor_retorna_0_si_todo_ok():
    with patch.object(doctor, "ejecutar_diagnostico_doctor", return_value=True):
        assert cli_commands.ejecutar_doctor() == 0


def test_ejecutar_doctor_retorna_1_si_falta_requisito():
    with patch.object(doctor, "ejecutar_diagnostico_doctor", return_value=False):
        assert cli_commands.ejecutar_doctor() == 1


def _chequeo_typst(monkeypatch, binario, modulo):
    monkeypatch.setattr(doctor, "chequear_binario", lambda c, *a: binario if c == "typst" else
                        {"disponible": True, "version": "1", "ruta": "/bin/gcc"})
    monkeypatch.setattr(doctor, "chequear_modulo_python", lambda m: modulo if m == "typst" else
                        {"disponible": True, "version": "1", "importable": True})
    monkeypatch.setattr(doctor, "chequear_conectividad_languagetool", lambda: {"disponible": False, "detalle": "x"})
    chequeos = doctor.diagnosticar()
    return next(c for c in chequeos if c["nombre"] == "typst"), doctor.informe_json(chequeos)


SIN_BINARIO = {"disponible": False, "version": None, "ruta": None}
SIN_MODULO = {"disponible": False, "version": None, "importable": False}


def test_doctor_exige_typst(monkeypatch):
    typst, informe = _chequeo_typst(monkeypatch, SIN_BINARIO, SIN_MODULO)
    assert typst["requerido"] and not typst["ok"] and not informe["ok"]


def test_doctor_no_da_por_bueno_un_modulo_que_no_se_importa(monkeypatch):
    roto = {"disponible": True, "version": "Detectado (no se pudo importar)", "importable": False}
    typst, informe = _chequeo_typst(monkeypatch, SIN_BINARIO, roto)
    assert not typst["ok"] and "no se puede importar" in typst["detalle"] and not informe["ok"]


def test_doctor_acepta_el_binario_sin_el_modulo(monkeypatch):
    typst, informe = _chequeo_typst(monkeypatch, {"disponible": True, "version": "typst 0.13", "ruta": "/bin/typst"}, SIN_MODULO)
    assert typst["ok"] and informe["ok"]


def test_doctor_no_pide_weasyprint(monkeypatch):
    _, informe = _chequeo_typst(monkeypatch, SIN_BINARIO, {"disponible": True, "version": "1", "importable": True})
    assert "weasyprint" not in {c["nombre"] for c in informe["chequeos"]}


def test_doctor_exige_dibu(monkeypatch):
    # Sin ALUCARD_DIBU / DIBU_BIN, ni dibu en el .venv ni en el $PATH.
    import generador_examenes.diagramas as diagramas
    monkeypatch.setattr(diagramas, "binario_dibu", lambda: None)
    monkeypatch.setattr(doctor, "chequear_binario", lambda c, *a: SIN_BINARIO if c == "dibu" else
                        {"disponible": True, "version": "1", "ruta": "/bin/x"})
    monkeypatch.setattr(doctor, "chequear_modulo_python", lambda m:
                        {"disponible": True, "version": "1", "importable": True})
    monkeypatch.setattr(doctor, "chequear_conectividad_languagetool", lambda: {"disponible": False, "detalle": "x"})
    chequeos = doctor.diagnosticar()
    dibu = next(c for c in chequeos if c["nombre"] == "dibu")
    assert dibu["requerido"] and not dibu["ok"] and not doctor.informe_json(chequeos)["ok"]


def test_doctor_informa_tipos_y_themes_de_dibu(monkeypatch):
    monkeypatch.setattr(doctor, "chequear_modulo_python", lambda m:
                        {"disponible": True, "version": "1", "importable": True})
    monkeypatch.setattr(doctor, "chequear_conectividad_languagetool", lambda: {"disponible": False, "detalle": "x"})
    dibu = next(c for c in doctor.diagnosticar() if c["nombre"] == "dibu")
    assert dibu["ok"] and "tipos" in dibu["detalle"] and "high-contrast" in dibu["detalle"]
