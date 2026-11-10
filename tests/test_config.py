"""
Tests para la configuración del sistema
"""
import pytest
import logging
from generador_examenes.config.logging_config import setup_logging


class TestLoggingConfig:
    """Tests para configuración de logging"""
    
    def test_setup_logging_info(self):
        """Debe configurar logging en nivel INFO"""
        setup_logging(debug=False)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
    
    def test_setup_logging_debug(self):
        """Debe configurar logging en nivel DEBUG"""
        setup_logging(debug=True)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_logging_tiene_handler(self):
        """Debe tener al menos un handler"""
        setup_logging(debug=False)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    

    def test_logging_formato(self):
        """Debe tener formato correcto"""
        setup_logging(debug=False)
        
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        
        # Verificar que tiene formatter
        assert formatter is not None
        assert hasattr(formatter, '_fmt')
