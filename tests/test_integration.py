"""
Tests de integración end-to-end
"""
import pytest
from pathlib import Path
import yaml
from generador_examenes.core import logic
from generador_examenes.core.models import DefinicionExamen
from generador_examenes.generators.html_renderer import HtmlRenderer


class TestIntegracionCompleta:
    """Tests de integración del flujo completo"""
    
    def test_flujo_completo_ejemplo(self, tmp_path):
        """Debe ejecutar flujo completo con archivos de ejemplo"""
        # Rutas a archivos de ejemplo
        ruta_gift = Path("tests/bancos_ejemplo/banco_test.txt")
        ruta_xml = Path("tests/bancos_ejemplo/banco_test.xml")
        ruta_def = Path("tests/bancos_ejemplo/definicion_ejemplo.yaml")
        
        # Verificar que existen
        if not all([ruta_gift.exists(), ruta_xml.exists(), ruta_def.exists()]):
            pytest.skip("Archivos de ejemplo no encontrados")
        
        # 1. Cargar definición
        with open(ruta_def, 'r', encoding='utf-8') as f:
            definicion_yaml = yaml.safe_load(f)
        
        definicion = DefinicionExamen(**definicion_yaml)
        assert definicion.nombre_examen is not None
        
        # 2. Cargar bancos
        banco = logic.cargar_bancos([ruta_gift, ruta_xml])
        assert len(banco) > 0
        
        # 3. Construir pool
        examen_base = logic.construir_pool_examen(definicion, banco)
        assert 'secciones' in examen_base
        assert len(examen_base['secciones']) > 0
        
        # 4. Calcular puntaje
        puntaje = logic.calcular_puntaje_total(examen_base)
        assert puntaje > 0
        
        # 5. Mezclar examen
        examen_mezclado = logic.mezclar_examen(
            examen_base,
            42,
            definicion.configuracion_examen
        )
        
        # 6. Renderizar
        renderer = HtmlRenderer()
        archivo_examen = renderer.renderizar_examen(
            examen_mezclado,
            definicion,
            tmp_path,
            0
        )
        
        assert archivo_examen.exists()
        assert archivo_examen.suffix == '.html'
        
        # 7. Renderizar clave si está configurado
        if definicion.configuracion_examen.generar_clave_profesor:
            archivo_clave = renderer.renderizar_clave(
                examen_mezclado,
                definicion,
                tmp_path,
                0
            )
            assert archivo_clave.exists()
    
    def test_multiples_temas(self, tmp_path):
        """Debe generar múltiples temas con diferentes semillas"""
        ruta_gift = Path("tests/bancos_ejemplo/banco_test.txt")
        ruta_def = Path("tests/bancos_ejemplo/definicion_ejemplo.yaml")
        
        if not all([ruta_gift.exists(), ruta_def.exists()]):
            pytest.skip("Archivos de ejemplo no encontrados")
        
        # Cargar
        with open(ruta_def, 'r', encoding='utf-8') as f:
            definicion_yaml = yaml.safe_load(f)
        definicion = DefinicionExamen(**definicion_yaml)
        
        banco = logic.cargar_bancos([ruta_gift])
        examen_base = logic.construir_pool_examen(definicion, banco)
        
        # Generar 3 temas
        renderer = HtmlRenderer()
        archivos_generados = []
        
        for i in range(3):
            semilla = 42 + i
            examen_mezclado = logic.mezclar_examen(
                examen_base,
                semilla,
                definicion.configuracion_examen
            )
            
            archivo = renderer.renderizar_examen(
                examen_mezclado,
                definicion,
                tmp_path,
                i
            )
            archivos_generados.append(archivo)
        
        # Verificar que se crearon 3 archivos diferentes
        assert len(archivos_generados) == 3
        assert all(f.exists() for f in archivos_generados)
        
        # Verificar que tienen diferentes nombres
        nombres = [f.name for f in archivos_generados]
        assert len(set(nombres)) == 3
    
    def test_validacion_definicion_invalida(self):
        """Debe fallar con definición inválida"""
        from pydantic import ValidationError
        
        definicion_invalida = {
            "nombre_examen": "Test",
            # Faltan campos requeridos
        }
        
        with pytest.raises(ValidationError):
            DefinicionExamen(**definicion_invalida)
    
    def test_banco_vacio(self):
        """Debe manejar banco vacío"""
        from generador_examenes.core.models import (
            ConfiguracionExamen, SeccionExamen, PoolConfig
        )
        
        banco = {}
        
        config = ConfiguracionExamen()
        seccion = SeccionExamen(
            nombre="Sección A",
            pools=[PoolConfig(cantidad=1)]
        )
        
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Inst",
            materia="Mat",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        # Debe fallar porque no hay preguntas
        with pytest.raises(ValueError):
            logic.construir_pool_examen(definicion, banco)
    
    def test_reproducibilidad_completa(self, tmp_path):
        """Debe generar resultados idénticos con misma semilla"""
        ruta_gift = Path("tests/bancos_ejemplo/banco_test.txt")
        ruta_def = Path("tests/bancos_ejemplo/definicion_ejemplo.yaml")
        
        if not all([ruta_gift.exists(), ruta_def.exists()]):
            pytest.skip("Archivos de ejemplo no encontrados")
        
        # Cargar
        with open(ruta_def, 'r', encoding='utf-8') as f:
            definicion_yaml = yaml.safe_load(f)
        definicion = DefinicionExamen(**definicion_yaml)
        
        banco = logic.cargar_bancos([ruta_gift])
        examen_base = logic.construir_pool_examen(definicion, banco)
        
        # Generar dos veces con misma semilla
        examen1 = logic.mezclar_examen(examen_base, 42, definicion.configuracion_examen)
        examen2 = logic.mezclar_examen(examen_base, 42, definicion.configuracion_examen)
        
        # Deben tener el mismo orden de preguntas
        ids1 = [p.id for p in examen1['secciones'][0]['preguntas']]
        ids2 = [p.id for p in examen2['secciones'][0]['preguntas']]
        
        assert ids1 == ids2
    
    def test_filtros_combinados(self):
        """Debe aplicar múltiples filtros correctamente"""
        from generador_examenes.core.models import (
            Pregunta, ConfiguracionExamen, SeccionExamen, PoolConfig
        )
        
        # Crear banco con preguntas variadas
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="Matemáticas", enunciado_html="Test 1",
                etiquetas=["facil", "algebra"]
            ),
            "p2": Pregunta(
                id="p2", tipo="verdadero_falso", nombre="P2",
                categoria="Matemáticas", enunciado_html="Test 2",
                etiquetas=["facil"]
            ),
            "p3": Pregunta(
                id="p3", tipo="seleccion_multiple", nombre="P3",
                categoria="Historia", enunciado_html="Test 3",
                etiquetas=["facil"]
            ),
            "p4": Pregunta(
                id="p4", tipo="seleccion_multiple", nombre="P4",
                categoria="Matemáticas", enunciado_html="Test 4",
                etiquetas=["dificil", "algebra"]
            ),
        }
        
        # Pool con filtros combinados: Matemáticas + selección_multiple + facil
        pool = PoolConfig(
            categoria="Matemáticas",
            tipos=["seleccion_multiple"],
            etiquetas=["facil"],
            cantidad=1
        )
        
        seccion = SeccionExamen(nombre="Sección A", pools=[pool])
        config = ConfiguracionExamen()
        
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Inst",
            materia="Mat",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        resultado = logic.construir_pool_examen(definicion, banco)
        preguntas = resultado['secciones'][0]['preguntas']
        
        # Solo debe seleccionar p1 (cumple todos los filtros)
        assert len(preguntas) == 1
        assert preguntas[0].id == "p1"
