"""
Tests para la lógica de orquestación
"""
import pytest
from pathlib import Path
from generador_examenes.core import logic
from generador_examenes.core.models import (
    Pregunta, Opcion, DefinicionExamen, SeccionExamen,
    PoolConfig, ConfiguracionExamen
)


class TestCargarBancos:
    """Tests para cargar_bancos"""
    
    def test_cargar_banco_gift(self):
        """Debe cargar banco GIFT"""
        ruta = Path("tests/bancos_ejemplo/banco_test.txt")
        if ruta.exists():
            banco = logic.cargar_bancos([ruta])
            assert len(banco) > 0
            assert all(isinstance(p, Pregunta) for p in banco.values())
    
    def test_cargar_banco_xml(self):
        """Debe cargar banco XML"""
        ruta = Path("tests/bancos_ejemplo/banco_test.xml")
        if ruta.exists():
            banco = logic.cargar_bancos([ruta])
            assert len(banco) > 0
    
    def test_cargar_multiples_bancos(self):
        """Debe cargar múltiples bancos"""
        rutas = [
            Path("tests/bancos_ejemplo/banco_test.txt"),
            Path("tests/bancos_ejemplo/banco_test.xml")
        ]
        rutas = [r for r in rutas if r.exists()]
        
        if len(rutas) == 2:
            banco = logic.cargar_bancos(rutas)
            # Debe combinar preguntas de ambos bancos
            assert len(banco) > 10
    
    def test_cargar_banco_inexistente(self):
        """Debe fallar con banco inexistente"""
        with pytest.raises(Exception):
            logic.cargar_bancos([Path("banco_inexistente.txt")])
    
    def test_cargar_bancos_con_duplicados(self, tmp_path):
        """Debe manejar preguntas duplicadas con warning"""
        # Crear dos archivos XML con el mismo ID de pregunta
        banco1 = tmp_path / "banco1.xml"
        banco1.write_text("""<?xml version='1.0' encoding='utf-8'?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta Duplicada</text></name>
    <questiontext><text>Texto 1</text></questiontext>
    <answer fraction="100"><text>Correcta 1</text></answer>
  </question>
</quiz>""")
        
        banco2 = tmp_path / "banco2.xml"
        banco2.write_text("""<?xml version='1.0' encoding='utf-8'?>
<quiz>
  <question type="multichoice">
    <name><text>Pregunta Duplicada</text></name>
    <questiontext><text>Texto 2</text></questiontext>
    <answer fraction="100"><text>Correcta 2</text></answer>
  </question>
</quiz>""")
        
        # Cargar ambos bancos - debe generar warning sobre duplicado.
        # pytest.warns(None) se eliminó en pytest 8: catch_warnings es el
        # equivalente para registrar cualquier advertencia sin exigir una.
        import warnings
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            banco = logic.cargar_bancos([banco1, banco2])
        
        # Debe tener solo una pregunta (la segunda sobrescribe)
        assert len(banco) == 1
        # La pregunta final debe ser la del segundo banco
        pregunta = list(banco.values())[0]
        assert "Texto 2" in pregunta.enunciado_html


class TestProcesarImagenes:
    """Tests para procesar_imagenes"""
    
    def test_sin_directorio_imagenes(self):
        """Debe manejar sin directorio de imágenes"""
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html="<p>Test</p>"
            )
        }
        
        # No debe fallar
        logic.procesar_imagenes(banco, None)
        assert banco["p1"].enunciado_html == "<p>Test</p>"
    
    def test_directorio_inexistente(self):
        """Debe manejar directorio inexistente"""
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html="<p>Test</p>"
            )
        }
        
        logic.procesar_imagenes(banco, Path("/directorio/inexistente"))
        # No debe modificar el HTML si no hay imágenes
        assert "<p>Test</p>" in banco["p1"].enunciado_html
    
    def test_imagen_no_encontrada(self, tmp_path):
        """Debe manejar imagen no encontrada con placeholder"""
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html='<img src="imagen_inexistente.png">'
            )
        }
        
        logic.procesar_imagenes(banco, tmp_path)
        # Debe incluir un placeholder SVG
        assert "data:image/svg+xml" in banco["p1"].enunciado_html
    
    def test_procesar_imagenes_en_opciones(self, tmp_path):
        """Debe procesar imágenes en opciones de respuesta"""
        # Crear una imagen de prueba
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html='<p>Pregunta</p>',
                opciones=[
                    Opcion(
                        texto_html=f'<img src="{img_path.name}">',
                        es_correcta=True
                    )
                ]
            )
        }
        
        logic.procesar_imagenes(banco, tmp_path)
        # Debe convertir imagen en opción a base64
        assert "data:image/png;base64," in banco["p1"].opciones[0].texto_html
    
    def test_imagen_ya_base64(self, tmp_path):
        """Debe dejar intactas imágenes ya en base64"""
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html='<img src="data:image/png;base64,ABC123">'
            )
        }
        
        original = banco["p1"].enunciado_html
        logic.procesar_imagenes(banco, tmp_path)
        # No debe modificar
        assert banco["p1"].enunciado_html == original
    
    def test_imagen_error_lectura(self, tmp_path):
        """Debe manejar error al leer imagen (ej: sin permisos)"""
        # Crear archivo de imagen sin permisos de lectura
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b'\x89PNG\r\n\x1a\n')
        import os
        os.chmod(img_path, 0o000)  # Sin permisos
        
        banco = {
            "p1": Pregunta(
                id="p1",
                tipo="seleccion_multiple",
                nombre="Test",
                categoria="Cat",
                enunciado_html='<img src="test.png">'
            )
        }
        
        # Debe manejar el error sin fallar
        try:
            logic.procesar_imagenes(banco, tmp_path)
            # Debe mantener src original en caso de error
            assert 'src="test.png"' in banco["p1"].enunciado_html
        finally:
            # Restaurar permisos para limpieza
            os.chmod(img_path, 0o644)


class TestConstruirPoolExamen:
    """Tests para construir_pool_examen"""
    
    def test_construir_pool_basico(self):
        """Debe construir pool básico"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1", 
                          categoria="Math", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Math", enunciado_html="Test 2"),
        }
        
        pool = PoolConfig(cantidad=2)
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
        
        assert 'secciones' in resultado
        assert len(resultado['secciones']) == 1
        assert len(resultado['secciones'][0]['preguntas']) == 2
    
    def test_filtrar_por_categoria(self):
        """Debe filtrar por categoría"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Matemáticas", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Historia", enunciado_html="Test 2"),
        }
        
        pool = PoolConfig(categoria="Matemáticas", cantidad=1)
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
        
        assert len(preguntas) == 1
        assert preguntas[0].categoria == "Matemáticas"
    
    def test_filtrar_por_tipo(self):
        """Debe filtrar por tipo"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Cat", enunciado_html="Test 2"),
            "p3": Pregunta(id="p3", tipo="ensayo", nombre="P3",
                          categoria="Cat", enunciado_html="Test 3"),
        }
        
        pool = PoolConfig(tipos=["verdadero_falso"], cantidad=1)
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
        
        assert len(preguntas) == 1
        assert preguntas[0].tipo == "verdadero_falso"
    
    def test_filtrar_por_etiquetas(self):
        """Debe filtrar por etiquetas"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1",
                          etiquetas=["facil", "algebra"]),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Cat", enunciado_html="Test 2",
                          etiquetas=["dificil"]),
        }
        
        pool = PoolConfig(etiquetas=["facil"], cantidad=1)
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
        
        assert len(preguntas) == 1
        assert "facil" in preguntas[0].etiquetas
    
    def test_preguntas_fijadas(self):
        """Debe usar preguntas fijadas"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Cat", enunciado_html="Test 2"),
            "p3": Pregunta(id="p3", tipo="ensayo", nombre="P3",
                          categoria="Cat", enunciado_html="Test 3"),
        }
        
        pool = PoolConfig(preguntas_fijadas=["p1", "p3"])
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
        
        assert len(preguntas) == 2
        ids = [p.id for p in preguntas]
        assert "p1" in ids
        assert "p3" in ids
    
    def test_insuficientes_preguntas_error(self):
        """Debe fallar con preguntas insuficientes (acción error)"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1"),
        }
        
        pool = PoolConfig(cantidad=10, accion_si_insuficiente="error")
        seccion = SeccionExamen(nombre="Sección A", pools=[pool])
        config = ConfiguracionExamen()
        
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Inst",
            materia="Mat",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        with pytest.raises(ValueError) as exc_info:
            logic.construir_pool_examen(definicion, banco)
        assert "insuficiente" in str(exc_info.value).lower()
    
    def test_insuficientes_preguntas_advertir(self):
        """Debe advertir con preguntas insuficientes y usar las disponibles"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Cat", enunciado_html="Test 2"),
        }
        
        pool = PoolConfig(cantidad=10, accion_si_insuficiente="advertir")
        seccion = SeccionExamen(nombre="Sección A", pools=[pool])
        config = ConfiguracionExamen()
        
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Inst",
            materia="Mat",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        # No debe fallar, solo advertir
        resultado = logic.construir_pool_examen(definicion, banco)
        preguntas = resultado['secciones'][0]['preguntas']
        # Debe usar solo las 2 disponibles
        assert len(preguntas) == 2
    
    def test_insuficientes_preguntas_usar_todas(self):
        """Debe usar todas las disponibles cuando no hay suficientes"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1"),
            "p2": Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                          categoria="Cat", enunciado_html="Test 2"),
            "p3": Pregunta(id="p3", tipo="ensayo", nombre="P3",
                          categoria="Cat", enunciado_html="Test 3"),
        }
        
        pool = PoolConfig(cantidad=10, accion_si_insuficiente="usar_todas")
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
        # Debe usar todas las 3 disponibles
        assert len(preguntas) == 3
    
    def test_puntaje_fijo(self):
        """Debe aplicar puntaje fijo"""
        banco = {
            "p1": Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                          categoria="Cat", enunciado_html="Test 1", puntaje=1.0),
        }
        
        pool = PoolConfig(cantidad=1, puntaje_fijo_por_pregunta=5.0)
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
        pregunta = resultado['secciones'][0]['preguntas'][0]
        
        assert pregunta.puntaje == 5.0


class TestMezclarExamen:
    """Tests para mezclar_examen"""
    
    def test_mezclar_preguntas(self):
        """Debe mezclar preguntas"""
        preguntas = [
            Pregunta(id=f"p{i}", tipo="seleccion_multiple", nombre=f"P{i}",
                    categoria="Cat", enunciado_html=f"Test {i}")
            for i in range(5)
        ]
        
        examen_data = {
            'secciones': [{
                'nombre': 'Sección A',
                'instrucciones': None,
                'preguntas': preguntas.copy()
            }]
        }
        
        config = ConfiguracionExamen(
            mezclar_preguntas_dentro_seccion=True,
            mezclar_opciones_dentro_pregunta=False
        )
        
        # Mezclar con dos semillas diferentes
        resultado1 = logic.mezclar_examen(examen_data, 42, config)
        resultado2 = logic.mezclar_examen(examen_data, 123, config)
        
        ids1 = [p.id for p in resultado1['secciones'][0]['preguntas']]
        ids2 = [p.id for p in resultado2['secciones'][0]['preguntas']]
        
        # Los IDs deben ser diferentes (mezclados diferente)
        assert ids1 != ids2
    
    def test_no_mezclar_preguntas(self):
        """Debe mantener orden si no se mezcla"""
        preguntas = [
            Pregunta(id=f"p{i}", tipo="seleccion_multiple", nombre=f"P{i}",
                    categoria="Cat", enunciado_html=f"Test {i}")
            for i in range(5)
        ]
        
        examen_data = {
            'secciones': [{
                'nombre': 'Sección A',
                'instrucciones': None,
                'preguntas': preguntas.copy()
            }]
        }
        
        config = ConfiguracionExamen(
            mezclar_preguntas_dentro_seccion=False,
            mezclar_opciones_dentro_pregunta=False
        )
        
        resultado = logic.mezclar_examen(examen_data, 42, config)
        ids_resultado = [p.id for p in resultado['secciones'][0]['preguntas']]
        ids_original = [p.id for p in preguntas]
        
        assert ids_resultado == ids_original
    
    def test_mezclar_opciones(self):
        """Debe mezclar opciones"""
        opciones = [
            Opcion(texto_html=f"Opción {i}", es_correcta=(i==0))
            for i in range(4)
        ]
        
        pregunta = Pregunta(
            id="p1",
            tipo="seleccion_multiple",
            nombre="Test",
            categoria="Cat",
            enunciado_html="Test",
            opciones=opciones.copy()
        )
        
        examen_data = {
            'secciones': [{
                'nombre': 'Sección A',
                'instrucciones': None,
                'preguntas': [pregunta]
            }]
        }
        
        config = ConfiguracionExamen(
            mezclar_preguntas_dentro_seccion=False,
            mezclar_opciones_dentro_pregunta=True
        )
        
        # Mezclar con dos semillas diferentes
        resultado1 = logic.mezclar_examen(examen_data, 42, config)
        resultado2 = logic.mezclar_examen(examen_data, 123, config)
        
        opciones1 = resultado1['secciones'][0]['preguntas'][0].opciones
        opciones2 = resultado2['secciones'][0]['preguntas'][0].opciones
        
        textos1 = [o.texto_html for o in opciones1]
        textos2 = [o.texto_html for o in opciones2]
        
        # Deben estar mezcladas diferente
        assert textos1 != textos2
    
    def test_reproducibilidad(self):
        """Debe ser reproducible con misma semilla"""
        preguntas = [
            Pregunta(id=f"p{i}", tipo="seleccion_multiple", nombre=f"P{i}",
                    categoria="Cat", enunciado_html=f"Test {i}")
            for i in range(5)
        ]
        
        examen_data = {
            'secciones': [{
                'nombre': 'Sección A',
                'instrucciones': None,
                'preguntas': preguntas.copy()
            }]
        }
        
        config = ConfiguracionExamen(mezclar_preguntas_dentro_seccion=True)
        
        resultado1 = logic.mezclar_examen(examen_data, 42, config)
        resultado2 = logic.mezclar_examen(examen_data, 42, config)
        
        ids1 = [p.id for p in resultado1['secciones'][0]['preguntas']]
        ids2 = [p.id for p in resultado2['secciones'][0]['preguntas']]
        
        # Deben ser idénticos con misma semilla
        assert ids1 == ids2


class TestCalcularPuntajeTotal:
    """Tests para calcular_puntaje_total"""
    
    def test_calcular_puntaje_simple(self):
        """Debe calcular puntaje total"""
        preguntas = [
            Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                    categoria="Cat", enunciado_html="Test", puntaje=2.0),
            Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                    categoria="Cat", enunciado_html="Test", puntaje=1.0),
        ]
        
        examen_data = {
            'secciones': [{
                'nombre': 'Sección A',
                'preguntas': preguntas
            }]
        }
        
        total = logic.calcular_puntaje_total(examen_data)
        assert total == 3.0
    
    def test_calcular_multiples_secciones(self):
        """Debe calcular puntaje con múltiples secciones"""
        examen_data = {
            'secciones': [
                {
                    'nombre': 'Sección A',
                    'preguntas': [
                        Pregunta(id="p1", tipo="seleccion_multiple", nombre="P1",
                                categoria="Cat", enunciado_html="Test", puntaje=2.0),
                    ]
                },
                {
                    'nombre': 'Sección B',
                    'preguntas': [
                        Pregunta(id="p2", tipo="verdadero_falso", nombre="P2",
                                categoria="Cat", enunciado_html="Test", puntaje=3.0),
                        Pregunta(id="p3", tipo="ensayo", nombre="P3",
                                categoria="Cat", enunciado_html="Test", puntaje=5.0),
                    ]
                }
            ]
        }
        
        total = logic.calcular_puntaje_total(examen_data)
        assert total == 10.0
    
    def test_examen_vacio(self):
        """Debe retornar 0 para examen vacío"""
        examen_data = {'secciones': []}
        total = logic.calcular_puntaje_total(examen_data)
        assert total == 0.0
