"""
Tests para el módulo principal __main__.py
"""
import pytest
from pathlib import Path
import sys
from generador_examenes.__main__ import main, inicializar_proyecto


class TestInicializarProyecto:
    """Tests para la función inicializar_proyecto"""
    
    def test_inicializar_proyecto_crea_directorios(self, tmp_path, monkeypatch):
        """Debe crear todos los directorios necesarios"""
        monkeypatch.chdir(tmp_path)
        
        inicializar_proyecto()
        
        # Verificar que se crearon los directorios
        assert (tmp_path / "templates").exists()
        assert (tmp_path / "i18n").exists()
        assert (tmp_path / "bancos").exists()
        assert (tmp_path / "output").exists()
    
    def test_inicializar_proyecto_crea_archivos(self, tmp_path, monkeypatch):
        """Debe crear archivos de ejemplo"""
        monkeypatch.chdir(tmp_path)
        
        inicializar_proyecto()
        
        # Verificar que se crearon los archivos
        assert (tmp_path / "definicion_ejemplo.yaml").exists()
        assert (tmp_path / "bancos" / "banco_ejemplo.txt").exists()
        assert (tmp_path / "README_PROYECTO.md").exists()
    
    def test_inicializar_proyecto_no_sobrescribe(self, tmp_path, monkeypatch):
        """No debe sobrescribir archivos existentes"""
        monkeypatch.chdir(tmp_path)
        
        # Crear archivo existente con contenido
        existing_file = tmp_path / "definicion_ejemplo.yaml"
        existing_file.write_text("contenido original")
        
        inicializar_proyecto()
        
        # El archivo debe mantener su contenido original
        assert existing_file.read_text() == "contenido original"


class TestMainCLI:
    """Tests para la función main del CLI"""
    
    def test_main_sin_argumentos_muestra_error(self, monkeypatch):
        """Sin argumentos debe mostrar error"""
        monkeypatch.setattr(sys, 'argv', ['generador-examenes'])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error code
    
    def test_main_init_ejecuta_inicializacion(self, tmp_path, monkeypatch, capsys):
        """--init debe ejecutar inicialización"""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, 'argv', ['generador-examenes', '--init'])
        
        exit_code = main()
        
        assert exit_code == 0
        assert (tmp_path / "definicion_ejemplo.yaml").exists()
        
        captured = capsys.readouterr()
        assert "INICIALIZACIÓN COMPLETADA" in captured.out
    
    def test_main_con_definicion_invalida(self, tmp_path, monkeypatch):
        """Debe fallar con definición inválida"""
        definicion = tmp_path / "def.yaml"
        definicion.write_text("""
nombre_examen: "Test"
# Falta institucion, materia, etc.
        """)
        
        banco = tmp_path / "banco.txt"
        banco.write_text("::P1::Test{T}")
        
        monkeypatch.setattr(sys, 'argv', [
            'generador-examenes',
            '-d', str(definicion),
            '-i', str(banco)
        ])
        
        exit_code = main()
        
        assert exit_code == 1
    
    def test_main_con_banco_vacio(self, tmp_path, monkeypatch):
        """Debe fallar con banco vacío"""
        definicion = tmp_path / "def.yaml"
        definicion.write_text("""
nombre_examen: "Test"
institucion: "Inst"
materia: "Mat"
fecha: "2024-01-01"
duracion_minutos: 60
idioma: "es"
configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: false
secciones_examen:
  - nombre: "Sección A"
    pools:
      - cantidad: 2
        """)
        
        banco = tmp_path / "banco.txt"
        banco.write_text("")  # Banco vacío
        
        monkeypatch.setattr(sys, 'argv', [
            'generador-examenes',
            '-d', str(definicion),
            '-i', str(banco)
        ])
        
        exit_code = main()
        
        assert exit_code == 1
    
    def test_main_sin_definicion_muestra_error(self, monkeypatch):
        """Sin --definicion debe mostrar error"""
        monkeypatch.setattr(sys, 'argv', [
            'generador-examenes',
            '-i', 'banco.txt'
        ])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
    
    def test_main_sin_banco_muestra_error(self, tmp_path, monkeypatch):
        """Sin --input-banco en CLI ni en YAML debe mostrar error"""
        definicion = tmp_path / "def.yaml"
        definicion.write_text("""
nombre_examen: "Test"
institucion: "Inst"
materia: "Mat"
configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: false
secciones_examen:
  - nombre: "Sección A"
    pools:
      - cantidad: 2
# Sin input_banco en YAML
        """)
        
        monkeypatch.setattr(sys, 'argv', [
            'generador-examenes',
            '-d', str(definicion)
        ])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
