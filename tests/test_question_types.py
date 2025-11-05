"""
Tests para el módulo de tipos de preguntas
"""
import pytest
from generador_examenes.core.question_types import (
    QuestionType,
    QuestionTypeRegistry,
    get_question_type_registry,
    is_valid_question_type,
    get_display_name,
    requires_options
)


class TestQuestionType:
    """Tests para el enum QuestionType"""
    
    def test_display_names(self):
        """Los tipos tienen nombres legibles"""
        assert QuestionType.SELECCION_MULTIPLE.display_name == "Selección Múltiple"
        assert QuestionType.VERDADERO_FALSO.display_name == "Verdadero/Falso"
        assert QuestionType.DESARROLLO.display_name == "Desarrollo"
    
    def test_requires_options(self):
        """Identificación correcta de tipos que requieren opciones"""
        assert QuestionType.SELECCION_MULTIPLE.requires_options is True
        assert QuestionType.VERDADERO_FALSO.requires_options is True
        assert QuestionType.DESARROLLO.requires_options is False
        assert QuestionType.RESPUESTA_CORTA.requires_options is False
    
    def test_typical_points(self):
        """Puntajes típicos asignados correctamente"""
        assert QuestionType.VERDADERO_FALSO.typical_points == 1.0
        assert QuestionType.SELECCION_MULTIPLE.typical_points == 2.0
        assert QuestionType.DESARROLLO.typical_points == 10.0
    
    def test_ideal_time_minutes(self):
        """Tiempos ideales asignados correctamente"""
        assert QuestionType.VERDADERO_FALSO.ideal_time_minutes == 0.5
        assert QuestionType.SELECCION_MULTIPLE.ideal_time_minutes == 1.5
        assert QuestionType.DESARROLLO.ideal_time_minutes == 15.0
    
    def test_from_moodle_type(self):
        """Conversión desde tipos Moodle"""
        assert QuestionType.from_moodle_type("multichoice") == QuestionType.SELECCION_MULTIPLE
        assert QuestionType.from_moodle_type("truefalse") == QuestionType.VERDADERO_FALSO
        assert QuestionType.from_moodle_type("essay") == QuestionType.DESARROLLO
        assert QuestionType.from_moodle_type("shortanswer") == QuestionType.RESPUESTA_CORTA
    
    def test_to_moodle_type(self):
        """Conversión a tipos Moodle"""
        assert QuestionType.to_moodle_type(QuestionType.SELECCION_MULTIPLE) == "multichoice"
        assert QuestionType.to_moodle_type(QuestionType.VERDADERO_FALSO) == "truefalse"
        assert QuestionType.to_moodle_type(QuestionType.DESARROLLO) == "essay"
    
    def test_supports_partial_credit(self):
        """Identificación de soporte para crédito parcial"""
        assert QuestionType.SELECCION_MULTIPLE.supports_partial_credit is True
        assert QuestionType.VERDADERO_FALSO.supports_partial_credit is False
        assert QuestionType.DESARROLLO.supports_partial_credit is False


class TestQuestionTypeRegistry:
    """Tests para el registro de tipos de preguntas"""
    
    def test_registry_initialized(self):
        """El registro está inicializado con tipos por defecto"""
        registry = QuestionTypeRegistry()
        tipos = registry.get_all_types()
        
        assert "seleccion_multiple" in tipos
        assert "verdadero_falso" in tipos
        assert "desarrollo" in tipos
        assert len(tipos) == 7  # Todos los tipos definidos
    
    def test_get_type_valid(self):
        """Obtener tipo válido del registro"""
        registry = QuestionTypeRegistry()
        tipo = registry.get_type("seleccion_multiple")
        
        assert tipo == QuestionType.SELECCION_MULTIPLE
        assert tipo.display_name == "Selección Múltiple"
    
    def test_get_type_invalid(self):
        """Obtener tipo inválido lanza ValueError"""
        registry = QuestionTypeRegistry()
        
        with pytest.raises(ValueError, match="Tipo de pregunta no soportado"):
            registry.get_type("tipo_inexistente")
    
    def test_is_valid_type(self):
        """Validación de tipos"""
        registry = QuestionTypeRegistry()
        
        assert registry.is_valid_type("seleccion_multiple") is True
        assert registry.is_valid_type("verdadero_falso") is True
        assert registry.is_valid_type("tipo_falso") is False
        assert registry.is_valid_type("") is False
    
    def test_get_types_requiring_options(self):
        """Obtener tipos que requieren opciones"""
        registry = QuestionTypeRegistry()
        tipos = registry.get_types_requiring_options()
        
        assert "seleccion_multiple" in tipos
        assert "verdadero_falso" in tipos
        assert "emparejamiento" in tipos
        assert "desarrollo" not in tipos
        assert "respuesta_corta" not in tipos
    
    def test_estimate_exam_duration_single_type(self):
        """Estimación de duración con un solo tipo de pregunta"""
        registry = QuestionTypeRegistry()
        
        # 10 preguntas de selección múltiple (1.5 min c/u) = 15 min + 10% = 16.5
        duration = registry.estimate_exam_duration({
            "seleccion_multiple": 10
        })
        
        assert duration == pytest.approx(16.5, rel=0.01)
    
    def test_estimate_exam_duration_mixed_types(self):
        """Estimación de duración con múltiples tipos"""
        registry = QuestionTypeRegistry()
        
        # 10 V/F (0.5 min) + 5 selección múltiple (1.5 min) + 2 desarrollo (15 min)
        # = 5 + 7.5 + 30 = 42.5 min + 10% = 46.75
        duration = registry.estimate_exam_duration({
            "verdadero_falso": 10,
            "seleccion_multiple": 5,
            "desarrollo": 2
        })
        
        assert duration == pytest.approx(46.75, rel=0.01)
    
    def test_estimate_exam_duration_unknown_type(self):
        """Tipos desconocidos son ignorados en la estimación"""
        registry = QuestionTypeRegistry()
        
        duration = registry.estimate_exam_duration({
            "seleccion_multiple": 10,
            "tipo_desconocido": 5  # Ignorado
        })
        
        # Solo cuenta las 10 de selección múltiple
        assert duration == pytest.approx(16.5, rel=0.01)


class TestHelperFunctions:
    """Tests para funciones helper"""
    
    def test_get_question_type_registry_singleton(self):
        """El registry es un singleton"""
        registry1 = get_question_type_registry()
        registry2 = get_question_type_registry()
        
        assert registry1 is registry2
    
    def test_is_valid_question_type_helper(self):
        """Helper de validación funciona"""
        assert is_valid_question_type("seleccion_multiple") is True
        assert is_valid_question_type("verdadero_falso") is True
        assert is_valid_question_type("tipo_falso") is False
    
    def test_get_display_name_helper_valid(self):
        """Helper de display name para tipos válidos"""
        assert get_display_name("seleccion_multiple") == "Selección Múltiple"
        assert get_display_name("verdadero_falso") == "Verdadero/Falso"
        assert get_display_name("desarrollo") == "Desarrollo"
    
    def test_get_display_name_helper_invalid(self):
        """Helper de display name para tipos inválidos devuelve fallback"""
        assert get_display_name("tipo_falso") == "Tipo Falso"
        assert get_display_name("mi_tipo_custom") == "Mi Tipo Custom"
    
    def test_requires_options_helper_valid(self):
        """Helper requires_options para tipos válidos"""
        assert requires_options("seleccion_multiple") is True
        assert requires_options("verdadero_falso") is True
        assert requires_options("desarrollo") is False
        assert requires_options("respuesta_corta") is False
    
    def test_requires_options_helper_invalid(self):
        """Helper requires_options para tipos inválidos devuelve False"""
        assert requires_options("tipo_falso") is False
        assert requires_options("") is False


class TestQuestionTypeIntegration:
    """Tests de integración del sistema de tipos"""
    
    def test_all_enum_values_in_registry(self):
        """Todos los valores del enum están en el registry"""
        registry = get_question_type_registry()
        
        for tipo in QuestionType:
            assert tipo.value in registry.get_all_types()
    
    def test_moodle_conversion_roundtrip(self):
        """Conversión Moodle ida y vuelta"""
        tipos_internos = [
            QuestionType.SELECCION_MULTIPLE,
            QuestionType.VERDADERO_FALSO,
            QuestionType.DESARROLLO
        ]
        
        for tipo in tipos_internos:
            moodle_type = QuestionType.to_moodle_type(tipo)
            back_to_internal = QuestionType.from_moodle_type(moodle_type)
            # Desarrollo y Ensayo se mapean al mismo tipo Moodle
            if tipo != QuestionType.ENSAYO:
                assert back_to_internal.value in [tipo.value, QuestionType.DESARROLLO.value]
    
    def test_realistic_exam_duration_estimate(self):
        """Estimación realista de duración de examen típico"""
        registry = get_question_type_registry()
        
        # Examen típico: 20 V/F, 10 selección múltiple, 2 desarrollo
        duration = registry.estimate_exam_duration({
            "verdadero_falso": 20,      # 20 * 0.5 = 10 min
            "seleccion_multiple": 10,    # 10 * 1.5 = 15 min
            "desarrollo": 2              # 2 * 15 = 30 min
        })
        # Total: 55 min + 10% = 60.5 min
        
        assert 60 <= duration <= 61
        # Duración razonable para un examen
        assert duration < 180  # No más de 3 horas
