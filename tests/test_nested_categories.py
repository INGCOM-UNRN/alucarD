"""
Tests para soporte de categorías anidadas
"""
import pytest
from generador_examenes.core.logic import normalizar_categoria, categoria_coincide
from generador_examenes.core import logic
from generador_examenes.core.models import (
    Pregunta, DefinicionExamen, SeccionExamen,
    PoolConfig, ConfiguracionExamen
)


class TestNormalizarCategoria:
    """Tests para normalizar_categoria()"""
    
    def test_normalizar_basica(self):
        """Debe normalizar categoría básica"""
        assert normalizar_categoria("Math") == "math"
    
    def test_normalizar_anidada(self):
        """Debe normalizar categoría anidada"""
        assert normalizar_categoria("Math/Algebra") == "math/algebra"
    
    def test_normalizar_espacios(self):
        """Debe eliminar espacios extras"""
        assert normalizar_categoria("  Math / Algebra  ") == "math/algebra"
    
    def test_normalizar_backslashes(self):
        """Debe convertir backslashes a forward slashes"""
        assert normalizar_categoria("Math\\Algebra") == "math/algebra"
    
    def test_normalizar_slashes_dobles(self):
        """Debe eliminar slashes duplicados"""
        assert normalizar_categoria("Math//Algebra///Linear") == "math/algebra/linear"
    
    def test_normalizar_slash_final(self):
        """Debe eliminar slash final"""
        assert normalizar_categoria("Math/Algebra/") == "math/algebra"
    
    def test_normalizar_moodle_format(self):
        """Debe normalizar formato Moodle"""
        assert normalizar_categoria("$course$/top/Math/Algebra") == "$course$/top/math/algebra"
    
    def test_normalizar_vacia(self):
        """Debe manejar categoría vacía"""
        assert normalizar_categoria("") == ""
        assert normalizar_categoria(None) == ""


class TestCategoriaCoincide:
    """Tests para categoria_coincide()"""
    
    def test_coincidencia_exacta(self):
        """Debe coincidir exactamente"""
        assert categoria_coincide("Math/Algebra", "Math/Algebra") is True
    
    def test_coincidencia_case_insensitive(self):
        """Debe ser case-insensitive"""
        assert categoria_coincide("Math/Algebra", "math/algebra") is True
        assert categoria_coincide("MATH/ALGEBRA", "math/algebra") is True
    
    def test_no_coincidencia(self):
        """No debe coincidir categorías diferentes"""
        assert categoria_coincide("Math/Geometry", "Math/Algebra") is False
    
    def test_subcategoria_coincide(self):
        """Subcategoría debe coincidir con padre"""
        assert categoria_coincide("Math/Algebra/Linear", "Math/Algebra") is True
        assert categoria_coincide("Math/Algebra/Linear/Vectors", "Math/Algebra") is True
    
    def test_padre_no_coincide_con_hijo(self):
        """Categoría padre no debe coincidir con filtro de hijo"""
        assert categoria_coincide("Math", "Math/Algebra") is False
        assert categoria_coincide("Math/Algebra", "Math/Algebra/Linear") is False
    
    def test_wildcard_asterisco(self):
        """Debe soportar wildcard /*"""
        assert categoria_coincide("Math/Algebra", "Math/*") is True
        assert categoria_coincide("Math/Geometry", "Math/*") is True
        assert categoria_coincide("Math/Algebra/Linear", "Math/*") is False  # /* solo 1 nivel
    
    def test_wildcard_doble_asterisco(self):
        """Debe soportar wildcard /**"""
        assert categoria_coincide("Math/Algebra", "Math/**") is True
        assert categoria_coincide("Math/Algebra/Linear", "Math/**") is True
        assert categoria_coincide("Math/Algebra/Linear/Vectors", "Math/**") is True
        assert categoria_coincide("Math", "Math/**") is True
    
    def test_filtro_vacio(self):
        """Filtro vacío debe coincidir con todo"""
        assert categoria_coincide("Math/Algebra", "") is True
        assert categoria_coincide("Any/Category", None) is True
    
    def test_moodle_format(self):
        """Debe soportar formato Moodle"""
        assert categoria_coincide(
            "$course$/top/Math/Algebra",
            "$course$/top/Math"
        ) is True
        
        assert categoria_coincide(
            "$course$/top/Math/Algebra/Linear",
            "$course$/top/Math/**"
        ) is True
    
    def test_separadores_mixtos(self):
        """Debe manejar separadores mixtos"""
        assert categoria_coincide("Math\\Algebra", "Math/Algebra") is True
        assert categoria_coincide("Math/Algebra", "math\\algebra") is True


class TestFiltradoCategoriasAnidadas:
    """Tests para filtrado con categorías anidadas"""
    
    def test_filtrar_categoria_exacta(self):
        """Debe filtrar por categoría exacta"""
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="Math/Algebra", enunciado_html="Test 1"
            ),
            "p2": Pregunta(
                id="p2", tipo="seleccion_multiple", nombre="P2",
                categoria="Math/Geometry", enunciado_html="Test 2"
            ),
            "p3": Pregunta(
                id="p3", tipo="seleccion_multiple", nombre="P3",
                categoria="Physics", enunciado_html="Test 3"
            ),
        }
        
        pool = PoolConfig(categoria="Math/Algebra")
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
        assert preguntas[0].id == "p1"
    
    def test_filtrar_subcategorias(self):
        """Debe incluir subcategorías"""
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="Math/Algebra", enunciado_html="Test 1"
            ),
            "p2": Pregunta(
                id="p2", tipo="seleccion_multiple", nombre="P2",
                categoria="Math/Algebra/Linear", enunciado_html="Test 2"
            ),
            "p3": Pregunta(
                id="p3", tipo="seleccion_multiple", nombre="P3",
                categoria="Math/Algebra/Linear/Vectors", enunciado_html="Test 3"
            ),
            "p4": Pregunta(
                id="p4", tipo="seleccion_multiple", nombre="P4",
                categoria="Math/Geometry", enunciado_html="Test 4"
            ),
        }
        
        pool = PoolConfig(categoria="Math/Algebra", cantidad=10, accion_si_insuficiente="usar_todas")
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
        
        # Debe incluir p1, p2, p3 (todas en Math/Algebra o subcategorías)
        assert len(preguntas) == 3
        ids = {p.id for p in preguntas}
        assert ids == {"p1", "p2", "p3"}
    
    def test_filtrar_wildcard_simple(self):
        """Debe filtrar con wildcard /*"""
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="Math/Algebra", enunciado_html="Test 1"
            ),
            "p2": Pregunta(
                id="p2", tipo="seleccion_multiple", nombre="P2",
                categoria="Math/Geometry", enunciado_html="Test 2"
            ),
            "p3": Pregunta(
                id="p3", tipo="seleccion_multiple", nombre="P3",
                categoria="Math/Algebra/Linear", enunciado_html="Test 3"
            ),
            "p4": Pregunta(
                id="p4", tipo="seleccion_multiple", nombre="P4",
                categoria="Physics", enunciado_html="Test 4"
            ),
        }
        
        pool = PoolConfig(categoria="Math/*", cantidad=10, accion_si_insuficiente="usar_todas")
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
        
        # Debe incluir solo p1 y p2 (un nivel bajo Math)
        assert len(preguntas) == 2
        ids = {p.id for p in preguntas}
        assert ids == {"p1", "p2"}
    
    def test_filtrar_wildcard_recursivo(self):
        """Debe filtrar con wildcard /**"""
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="Math/Algebra", enunciado_html="Test 1"
            ),
            "p2": Pregunta(
                id="p2", tipo="seleccion_multiple", nombre="P2",
                categoria="Math/Geometry", enunciado_html="Test 2"
            ),
            "p3": Pregunta(
                id="p3", tipo="seleccion_multiple", nombre="P3",
                categoria="Math/Algebra/Linear", enunciado_html="Test 3"
            ),
            "p4": Pregunta(
                id="p4", tipo="seleccion_multiple", nombre="P4",
                categoria="Math/Algebra/Linear/Vectors", enunciado_html="Test 4"
            ),
            "p5": Pregunta(
                id="p5", tipo="seleccion_multiple", nombre="P5",
                categoria="Physics", enunciado_html="Test 5"
            ),
        }
        
        pool = PoolConfig(categoria="Math/**", cantidad=10, accion_si_insuficiente="usar_todas")
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
        
        # Debe incluir todas las preguntas de Math (cualquier nivel)
        assert len(preguntas) == 4
        ids = {p.id for p in preguntas}
        assert ids == {"p1", "p2", "p3", "p4"}
    
    def test_case_insensitive(self):
        """Debe ser case-insensitive"""
        banco = {
            "p1": Pregunta(
                id="p1", tipo="seleccion_multiple", nombre="P1",
                categoria="MATH/ALGEBRA", enunciado_html="Test 1"
            ),
            "p2": Pregunta(
                id="p2", tipo="seleccion_multiple", nombre="P2",
                categoria="Math/Algebra/Linear", enunciado_html="Test 2"
            ),
        }
        
        pool = PoolConfig(categoria="math/algebra", cantidad=10, accion_si_insuficiente="usar_todas")
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
