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
    disponible = {"disponible": True, "version": "1.0", "ruta": "/usr/bin/x"}
    with patch.object(doctor, "chequear_binario", return_value=disponible), \
         patch.object(doctor, "chequear_modulo_python", return_value=disponible), \
         patch.object(doctor, "chequear_conectividad_languagetool", return_value={"disponible": True, "detalle": "HTTP 200"}):
        ok = doctor.ejecutar_diagnostico_doctor(console=Console(file=open("/dev/null", "w")))
    assert ok is True


def test_diagnostico_falla_cuando_falta_requisito_obligatorio():
    ausente = {"disponible": False, "version": None, "ruta": None}
    with patch.object(doctor, "chequear_binario", return_value=ausente), \
         patch.object(doctor, "chequear_modulo_python", return_value=ausente), \
         patch.object(doctor, "chequear_conectividad_languagetool", return_value={"disponible": False, "detalle": "sin red"}):
        ok = doctor.ejecutar_diagnostico_doctor(console=Console(file=open("/dev/null", "w")))
    assert ok is False


def test_diagnostico_lo_opcional_no_afecta_resultado():
    disponible = {"disponible": True, "version": "1.0", "ruta": "/usr/bin/x"}
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
