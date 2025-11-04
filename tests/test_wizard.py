"""
Tests para el asistente de configuración (wizard)
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from generador_examenes.config.exam_wizard import ExamWizard


class TestExamWizard:
    """Tests para el ExamWizard"""
    
    def test_inicializacion_sin_yaml(self):
        """Debe inicializar wizard sin archivo YAML"""
        wizard = ExamWizard()
        assert wizard.yaml_path is None
        assert wizard.config == {}
    
    def test_inicializacion_con_yaml_existente(self, tmp_path):
        """Debe cargar configuración desde YAML existente"""
        yaml_path = tmp_path / "test.yaml"
        config_test = {
            'nombre_examen': 'Test',
            'institucion': 'Test U',
            'materia': 'Test',
            'idioma': 'es'
        }
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_test, f)
        
        wizard = ExamWizard(yaml_path)
        assert wizard.yaml_path == yaml_path
        assert wizard.config['nombre_examen'] == 'Test'
    
    def test_inicializacion_con_yaml_inexistente(self, tmp_path):
        """Debe inicializar con config vacía si YAML no existe"""
        yaml_path = tmp_path / "inexistente.yaml"
        wizard = ExamWizard(yaml_path)
        assert wizard.yaml_path == yaml_path
        assert wizard.config == {}
    
    def test_guardar_yaml(self, tmp_path):
        """Debe guardar configuración en archivo YAML"""
        yaml_path = tmp_path / "output.yaml"
        wizard = ExamWizard(yaml_path)
        
        wizard.config = {
            'nombre_examen': 'Examen Test',
            'institucion': 'Test University',
            'materia': 'Testing 101',
            'idioma': 'es',
            'configuracion_examen': {
                'mezclar_preguntas_dentro_seccion': True
            },
            'secciones_examen': []
        }
        
        wizard._guardar_yaml()
        
        assert yaml_path.exists()
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['nombre_examen'] == 'Examen Test'
        assert loaded['configuracion_examen']['mezclar_preguntas_dentro_seccion'] is True
    
    def test_describir_pool_con_categoria(self):
        """Debe describir pool con filtro de categoría"""
        wizard = ExamWizard()
        pool = {
            'categoria': 'Math/Algebra',
            'cantidad': 10
        }
        
        descripcion = wizard._describir_pool(pool)
        assert 'cat:Math/Algebra' in descripcion
        assert 'cant:10' in descripcion
    
    def test_describir_pool_con_tipos(self):
        """Debe describir pool con filtro de tipos"""
        wizard = ExamWizard()
        pool = {
            'tipos': ['seleccion_multiple', 'verdadero_falso'],
            'cantidad': 5
        }
        
        descripcion = wizard._describir_pool(pool)
        assert 'tipos:seleccion_multiple,verdadero_falso' in descripcion
        assert 'cant:5' in descripcion
    
    def test_describir_pool_con_etiquetas(self):
        """Debe describir pool con filtro de etiquetas"""
        wizard = ExamWizard()
        pool = {
            'etiquetas': ['facil', 'basico'],
            'cantidad': 3
        }
        
        descripcion = wizard._describir_pool(pool)
        assert 'tags:facil,basico' in descripcion
        assert 'cant:3' in descripcion
    
    def test_describir_pool_con_preguntas_fijadas(self):
        """Debe describir pool con preguntas fijadas"""
        wizard = ExamWizard()
        pool = {
            'preguntas_fijadas': ['p1', 'p2', 'p3']
        }
        
        descripcion = wizard._describir_pool(pool)
        assert '3 preguntas fijadas' in descripcion
    
    def test_describir_pool_vacio(self):
        """Debe describir pool sin filtros"""
        wizard = ExamWizard()
        pool = {}
        
        descripcion = wizard._describir_pool(pool)
        assert descripcion == 'sin filtros'
    
    def test_configurar_pool_con_categoria(self):
        """Debe configurar pool con categoría"""
        wizard = ExamWizard()
        
        with patch('generador_examenes.config.exam_wizard.Prompt.ask') as mock_ask, \
             patch('generador_examenes.config.exam_wizard.IntPrompt.ask') as mock_int_ask, \
             patch('generador_examenes.config.exam_wizard.console'):
            
            mock_ask.side_effect = ['categoria', 'Math/Algebra', 'advertir']
            mock_int_ask.return_value = 10
            
            pool = wizard._configurar_pool()
            
            assert pool['categoria'] == 'Math/Algebra'
            assert pool['cantidad'] == 10
            assert pool['accion_si_insuficiente'] == 'advertir'
    
    def test_configurar_pool_con_tipos(self):
        """Debe configurar pool con tipos"""
        wizard = ExamWizard()
        
        with patch('generador_examenes.config.exam_wizard.Prompt.ask') as mock_ask, \
             patch('generador_examenes.config.exam_wizard.IntPrompt.ask') as mock_int_ask, \
             patch('generador_examenes.config.exam_wizard.console'):
            
            mock_ask.side_effect = ['tipos', 'seleccion_multiple, verdadero_falso', 'error']
            mock_int_ask.return_value = 5
            
            pool = wizard._configurar_pool()
            
            assert pool['tipos'] == ['seleccion_multiple', 'verdadero_falso']
            assert pool['cantidad'] == 5
    
    def test_configurar_pool_con_preguntas_fijadas(self):
        """Debe configurar pool con preguntas fijadas"""
        wizard = ExamWizard()
        
        with patch('generador_examenes.config.exam_wizard.Prompt.ask') as mock_ask, \
             patch('generador_examenes.config.exam_wizard.console'):
            
            mock_ask.side_effect = ['fijadas', 'p1, p2, p3']
            
            pool = wizard._configurar_pool()
            
            assert pool['preguntas_fijadas'] == ['p1', 'p2', 'p3']
            assert 'cantidad' not in pool


class TestExamWizardIntegration:
    """Tests de integración del wizard"""
    
    def test_crear_examen_completo(self, tmp_path):
        """Debe crear configuración completa de examen"""
        yaml_path = tmp_path / "examen_completo.yaml"
        wizard = ExamWizard(yaml_path)
        
        # Configurar manualmente (simula interacción)
        wizard.config = {
            'nombre_examen': 'Parcial I',
            'institucion': 'UNRN',
            'materia': 'Matemáticas',
            'fecha': '2025-11-15',
            'duracion_minutos': 90,
            'instrucciones_generales': 'Lee cada pregunta cuidadosamente',
            'idioma': 'es',
            'configuracion_examen': {
                'mezclar_preguntas_dentro_seccion': True,
                'mezclar_opciones_dentro_pregunta': True,
                'generar_clave_profesor': True
            },
            'secciones_examen': [
                {
                    'nombre': 'Sección 1',
                    'pools': [
                        {
                            'categoria': 'Math/Algebra',
                            'cantidad': 10,
                            'accion_si_insuficiente': 'advertir'
                        }
                    ]
                },
                {
                    'nombre': 'Sección 2',
                    'instrucciones': 'Responde todas',
                    'pools': [
                        {
                            'tipos': ['seleccion_multiple'],
                            'etiquetas': ['facil'],
                            'cantidad': 5,
                            'accion_si_insuficiente': 'usar_todas'
                        }
                    ]
                }
            ]
        }
        
        wizard._guardar_yaml()
        
        # Verificar archivo
        assert yaml_path.exists()
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['nombre_examen'] == 'Parcial I'
        assert len(loaded['secciones_examen']) == 2
        assert loaded['secciones_examen'][0]['nombre'] == 'Sección 1'
        assert loaded['secciones_examen'][1]['instrucciones'] == 'Responde todas'
