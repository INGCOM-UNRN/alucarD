"""
Tests para los modelos Pydantic
"""
import pytest
from pydantic import ValidationError
from generador_examenes.core.models import (
    Opcion, Pregunta, PoolConfig, SeccionExamen,
    ConfiguracionExamen, DefinicionExamen
)


class TestOpcion:
    """Tests para el modelo Opcion"""
    
    def test_opcion_valida(self):
        """Debe crear una opción válida"""
        opcion = Opcion(texto_html="Respuesta A", es_correcta=True)
        assert opcion.texto_html == "Respuesta A"
        assert opcion.es_correcta is True
        assert opcion.retroalimentacion is None
    
    def test_opcion_con_retroalimentacion(self):
        """Debe crear una opción con retroalimentación"""
        opcion = Opcion(
            texto_html="Respuesta B",
            es_correcta=False,
            retroalimentacion="Incorrecto, intenta de nuevo"
        )
        assert opcion.retroalimentacion == "Incorrecto, intenta de nuevo"
    
    def test_opcion_sin_texto_falla(self):
        """Debe fallar sin texto"""
        with pytest.raises(ValidationError):
            Opcion(es_correcta=True)


class TestPregunta:
    """Tests para el modelo Pregunta"""
    
    def test_pregunta_seleccion_multiple(self):
        """Debe crear pregunta de selección múltiple"""
        opciones = [
            Opcion(texto_html="A", es_correcta=True),
            Opcion(texto_html="B", es_correcta=False),
        ]
        pregunta = Pregunta(
            id="p1",
            tipo="seleccion_multiple",
            nombre="Pregunta 1",
            categoria="Matemáticas",
            enunciado_html="¿Cuánto es 2+2?",
            opciones=opciones
        )
        assert pregunta.id == "p1"
        assert pregunta.tipo == "seleccion_multiple"
        assert pregunta.puntaje == 1.0
        assert len(pregunta.opciones) == 2
        assert pregunta.etiquetas == []
    
    def test_pregunta_con_etiquetas(self):
        """Debe crear pregunta con etiquetas"""
        pregunta = Pregunta(
            id="p2",
            tipo="verdadero_falso",
            nombre="Pregunta 2",
            categoria="Historia",
            enunciado_html="La tierra es plana",
            etiquetas=["facil", "geografia"]
        )
        assert len(pregunta.etiquetas) == 2
        assert "facil" in pregunta.etiquetas
    
    def test_pregunta_tipo_invalido_falla(self):
        """Debe fallar con tipo inválido"""
        with pytest.raises(ValidationError):
            Pregunta(
                id="p3",
                tipo="tipo_inexistente",
                nombre="Pregunta",
                categoria="Cat",
                enunciado_html="Texto"
            )
    
    def test_pregunta_puntaje_personalizado(self):
        """Debe aceptar puntaje personalizado"""
        pregunta = Pregunta(
            id="p4",
            tipo="ensayo",
            nombre="Ensayo",
            categoria="Literatura",
            enunciado_html="Describe...",
            puntaje=5.0
        )
        assert pregunta.puntaje == 5.0


class TestPoolConfig:
    """Tests para el modelo PoolConfig"""
    
    def test_pool_basico(self):
        """Debe crear pool básico"""
        pool = PoolConfig()
        assert pool.banco is None
        assert pool.preguntas_fijadas == []
        assert pool.cantidad is None
        assert pool.accion_si_insuficiente == "error"
    
    def test_pool_con_filtros(self):
        """Debe crear pool con filtros"""
        pool = PoolConfig(
            categoria="Matemáticas",
            tipos=["seleccion_multiple"],
            etiquetas=["facil"],
            cantidad=10,
            puntaje_fijo_por_pregunta=2.0
        )
        assert pool.categoria == "Matemáticas"
        assert pool.cantidad == 10
        assert pool.puntaje_fijo_por_pregunta == 2.0
    
    def test_pool_con_preguntas_fijadas(self):
        """Debe crear pool con preguntas fijadas"""
        pool = PoolConfig(
            preguntas_fijadas=["p1", "p2", "p3"]
        )
        assert len(pool.preguntas_fijadas) == 3
    
    def test_pool_accion_si_insuficiente(self):
        """Debe validar acción si insuficiente"""
        pool = PoolConfig(accion_si_insuficiente="advertir")
        assert pool.accion_si_insuficiente == "advertir"
        
        with pytest.raises(ValidationError):
            PoolConfig(accion_si_insuficiente="accion_invalida")


class TestSeccionExamen:
    """Tests para el modelo SeccionExamen"""
    
    def test_seccion_basica(self):
        """Debe crear sección básica"""
        pool = PoolConfig(cantidad=5)
        seccion = SeccionExamen(
            nombre="Sección A",
            pools=[pool]
        )
        assert seccion.nombre == "Sección A"
        assert len(seccion.pools) == 1
        assert seccion.instrucciones is None
    
    def test_seccion_con_instrucciones(self):
        """Debe crear sección con instrucciones"""
        pool = PoolConfig()
        seccion = SeccionExamen(
            nombre="Sección B",
            instrucciones="Lee cuidadosamente",
            pools=[pool]
        )
        assert seccion.instrucciones == "Lee cuidadosamente"
    
    def test_seccion_multiples_pools(self):
        """Debe crear sección con múltiples pools"""
        pools = [
            PoolConfig(cantidad=5),
            PoolConfig(cantidad=10)
        ]
        seccion = SeccionExamen(nombre="Multi", pools=pools)
        assert len(seccion.pools) == 2


class TestConfiguracionExamen:
    """Tests para el modelo ConfiguracionExamen"""
    
    def test_configuracion_default(self):
        """Debe crear configuración con valores por defecto"""
        config = ConfiguracionExamen()
        assert config.mezclar_preguntas_dentro_seccion is True
        assert config.mezclar_opciones_dentro_pregunta is True
        assert config.generar_clave_profesor is True
    
    def test_configuracion_personalizada(self):
        """Debe crear configuración personalizada"""
        config = ConfiguracionExamen(
            mezclar_preguntas_dentro_seccion=False,
            mezclar_opciones_dentro_pregunta=False,
            generar_clave_profesor=False
        )
        assert config.mezclar_preguntas_dentro_seccion is False
        assert config.generar_clave_profesor is False


class TestDefinicionExamen:
    """Tests para el modelo DefinicionExamen"""
    
    def test_definicion_minima(self):
        """Debe crear definición con campos mínimos"""
        config = ConfiguracionExamen()
        seccion = SeccionExamen(
            nombre="Sección 1",
            pools=[PoolConfig()]
        )
        
        definicion = DefinicionExamen(
            nombre_examen="Examen Final",
            institucion="Universidad XYZ",
            materia="Programación",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        assert definicion.nombre_examen == "Examen Final"
        assert definicion.idioma == "es"  # Default
        assert definicion.fecha is None
        assert len(definicion.secciones_examen) == 1
    
    def test_definicion_completa(self):
        """Debe crear definición completa"""
        config = ConfiguracionExamen()
        seccion = SeccionExamen(
            nombre="Sección A",
            pools=[PoolConfig(cantidad=10)]
        )
        
        definicion = DefinicionExamen(
            nombre_examen="Examen Parcial",
            institucion="Instituto ABC",
            materia="Matemáticas",
            fecha="2024-06-15",
            duracion_minutos=120,
            instrucciones_generales="Lee todo antes de empezar",
            idioma="en",
            configuracion_examen=config,
            secciones_examen=[seccion]
        )
        
        assert definicion.fecha == "2024-06-15"
        assert definicion.duracion_minutos == 120
        assert definicion.idioma == "en"
        assert definicion.instrucciones_generales is not None
    
    def test_definicion_sin_campos_requeridos_falla(self):
        """Debe fallar sin campos requeridos"""
        with pytest.raises(ValidationError):
            DefinicionExamen(nombre_examen="Test")
    
    def test_definicion_multiples_secciones(self):
        """Debe crear definición con múltiples secciones"""
        config = ConfiguracionExamen()
        secciones = [
            SeccionExamen(nombre="A", pools=[PoolConfig()]),
            SeccionExamen(nombre="B", pools=[PoolConfig()]),
            SeccionExamen(nombre="C", pools=[PoolConfig()])
        ]
        
        definicion = DefinicionExamen(
            nombre_examen="Examen",
            institucion="Inst",
            materia="Mat",
            configuracion_examen=config,
            secciones_examen=secciones
        )
        
        assert len(definicion.secciones_examen) == 3
