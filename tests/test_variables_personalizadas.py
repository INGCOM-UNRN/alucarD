"""
Tests para variables personalizadas con f-strings
"""
import pytest
from datetime import datetime
from generador_examenes.core.models import DefinicionExamen, ConfiguracionExamen


class TestVariablesPersonalizadas:
    """Tests para variables personalizadas"""
    
    def test_sin_variables_personalizadas(self):
        """Debe funcionar sin variables personalizadas"""
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Test U",
            materia="Testing",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[]
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables == {}
    
    def test_variables_simples(self):
        """Debe evaluar variables simples sin f-strings"""
        definicion = DefinicionExamen(
            nombre_examen="Parcial I",
            institucion="UNRN",
            materia="Matemáticas",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'profesor': 'Dr. García',
                'aula': 'Aula 301',
                'departamento': 'Matemáticas'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['profesor'] == 'Dr. García'
        assert variables['aula'] == 'Aula 301'
        assert variables['departamento'] == 'Matemáticas'
    
    def test_variables_con_fstrings_campos_definicion(self):
        """Debe evaluar f-strings con campos de la definición"""
        definicion = DefinicionExamen(
            nombre_examen="Parcial I",
            institucion="UNRN Andina",
            materia="Programación 1",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'titulo_completo': '{nombre_examen} de {materia}',
                'ubicacion': 'Sede {institucion}',
                'descripcion': '{materia} - {institucion}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['titulo_completo'] == 'Parcial I de Programación 1'
        assert variables['ubicacion'] == 'Sede UNRN Andina'
        assert variables['descripcion'] == 'Programación 1 - UNRN Andina'
    
    def test_variables_con_fecha_actual(self):
        """Debe incluir variables de fecha actual"""
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Test U",
            materia="Testing",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'periodo': 'Año {anio_actual}',
                'fecha_generacion': 'Generado el {fecha_actual}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        anio_actual = datetime.now().year
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        assert variables['periodo'] == f'Año {anio_actual}'
        assert variables['fecha_generacion'] == f'Generado el {fecha_actual}'
    
    def test_variables_referenciando_otras_variables(self):
        """Debe permitir que variables referencien otras variables ya evaluadas"""
        definicion = DefinicionExamen(
            nombre_examen="Parcial I",
            institucion="UNRN",
            materia="Matemáticas",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'profesor': 'Dr. García',
                'departamento': 'Matemáticas',
                'info_profesor': 'Profesor: {profesor}',
                'info_completa': '{info_profesor}, Dpto. {departamento}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['profesor'] == 'Dr. García'
        assert variables['info_profesor'] == 'Profesor: Dr. García'
        assert variables['info_completa'] == 'Profesor: Dr. García, Dpto. Matemáticas'
    
    def test_variables_complejas(self):
        """Debe evaluar variables con múltiples sustituciones"""
        definicion = DefinicionExamen(
            nombre_examen="Examen Final",
            institucion="Universidad Nacional",
            materia="Física I",
            fecha="2025-12-15",
            duracion_minutos=180,
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'encabezado': '{institucion} - {materia}',
                'info_examen': '{nombre_examen} - Fecha: {fecha}',
                'nota_importante': 'Este examen tiene una duración de {duracion_minutos} minutos',
                'pie_pagina': '{encabezado} | {fecha}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['encabezado'] == 'Universidad Nacional - Física I'
        assert variables['info_examen'] == 'Examen Final - Fecha: 2025-12-15'
        assert variables['nota_importante'] == 'Este examen tiene una duración de 180 minutos'
        assert variables['pie_pagina'] == 'Universidad Nacional - Física I | 2025-12-15'
    
    def test_variable_con_error_mantiene_original(self):
        """Si una variable falla al evaluarse, debe mantener el valor original"""
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Test U",
            materia="Testing",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'valida': 'Profesor: {institucion}',
                'invalida': 'Campo inexistente: {campo_que_no_existe}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['valida'] == 'Profesor: Test U'
        # La variable inválida mantiene su valor original
        assert variables['invalida'] == 'Campo inexistente: {campo_que_no_existe}'
    
    def test_str_con_variables_personalizadas(self):
        """El __str__ debe mostrar cantidad de variables"""
        definicion = DefinicionExamen(
            nombre_examen="Test",
            institucion="Test U",
            materia="Testing",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={'var1': 'val1', 'var2': 'val2'}
        )
        
        str_repr = str(definicion)
        assert '+2 vars' in str_repr
    
    def test_variables_con_html_entities(self):
        """Debe manejar HTML entities en variables"""
        definicion = DefinicionExamen(
            nombre_examen="Test & Exam",
            institucion="Universidad <Nacional>",
            materia="Física",
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[],
            variables_personalizadas={
                'nota': 'Examen de {nombre_examen} en {institucion}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert variables['nota'] == 'Examen de Test & Exam en Universidad <Nacional>'


class TestIntegracionVariablesPersonalizadas:
    """Tests de integración con otras partes del sistema"""
    
    def test_definicion_completa_con_variables(self):
        """Debe crear definición completa con variables personalizadas"""
        from generador_examenes.core.models import SeccionExamen, PoolConfig
        
        definicion = DefinicionExamen(
            nombre_examen="Parcial II",
            institucion="UNRN",
            materia="Álgebra",
            fecha="2025-11-20",
            duracion_minutos=90,
            idioma="es",
            configuracion_examen=ConfiguracionExamen(),
            secciones_examen=[
                SeccionExamen(
                    nombre="Sección 1",
                    pools=[
                        PoolConfig(cantidad=10, tipos=['seleccion_multiple'])
                    ]
                )
            ],
            variables_personalizadas={
                'profesor': 'Dra. Martínez',
                'aula': 'Aula Magna',
                'nota_footer': '{materia} - {profesor} - {aula}',
                'periodo': 'Periodo {anio_actual}'
            }
        )
        
        variables = definicion.evaluar_variables_personalizadas()
        assert 'profesor' in variables
        assert 'aula' in variables
        assert 'nota_footer' in variables
        assert 'Álgebra' in variables['nota_footer']
        assert 'Dra. Martínez' in variables['nota_footer']
