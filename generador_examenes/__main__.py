"""
Punto de entrada principal de la aplicación
"""
import sys
import argparse
from pathlib import Path
import shutil


def inicializar_proyecto():
    """
    Crea estructura de directorios y archivos de ejemplo para un nuevo proyecto
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Crear directorios
    dirs_crear = ['templates', 'i18n', 'bancos', 'output']
    for dir_name in dirs_crear:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            logger.info(f"✓ Directorio creado: {dir_name}/")
        else:
            logger.info(f"  Directorio ya existe: {dir_name}/")
    
    # Copiar plantillas desde el paquete instalado
    import generador_examenes
    package_dir = Path(generador_examenes.__file__).parent
    
    # Copiar templates
    template_src = package_dir / 'templates'
    if template_src.exists():
        for template_file in template_src.glob('*.j2'):
            dest = Path('templates') / template_file.name
            if not dest.exists():
                shutil.copy(template_file, dest)
                logger.info(f"✓ Plantilla copiada: {template_file.name}")
            else:
                logger.info(f"  Plantilla ya existe: {template_file.name}")
    
    # Copiar archivos i18n
    i18n_src = package_dir / 'i18n'
    if i18n_src.exists():
        for i18n_file in i18n_src.glob('*.json'):
            dest = Path('i18n') / i18n_file.name
            if not dest.exists():
                shutil.copy(i18n_file, dest)
                logger.info(f"✓ Archivo i18n copiado: {i18n_file.name}")
            else:
                logger.info(f"  Archivo i18n ya existe: {i18n_file.name}")
    
    # Crear definicion_ejemplo.yaml
    definicion_ejemplo = Path('definicion_ejemplo.yaml')
    if not definicion_ejemplo.exists():
        contenido_definicion = """nombre_examen: "Examen de Ejemplo"
institucion: "Mi Institución"
materia: "Mi Materia"
fecha: "2024-01-01"
duracion_minutos: 60
instrucciones_generales: |
  Lee cuidadosamente cada pregunta antes de responder.
  Marca la respuesta correcta en cada caso.
idioma: "es"

configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
  incluir_metadata_debug: false

secciones_examen:
  - nombre: "Sección 1 - Preguntas de Ejemplo"
    instrucciones: "Selecciona la respuesta correcta"
    pools:
      - cantidad: 5
        tipos: ["seleccion_multiple"]
"""
        definicion_ejemplo.write_text(contenido_definicion, encoding='utf-8')
        logger.info(f"✓ Archivo creado: definicion_ejemplo.yaml")
    else:
        logger.info(f"  Archivo ya existe: definicion_ejemplo.yaml")
    
    # Crear banco de ejemplo
    banco_ejemplo = Path('bancos') / 'banco_ejemplo.txt'
    if not banco_ejemplo.exists():
        contenido_banco = """// Banco de preguntas de ejemplo en formato GIFT

::Pregunta 1:: ¿Cuál es la capital de Francia? {
=París
~Londres
~Berlín
~Madrid
}

::Pregunta 2:: Python es un lenguaje de programación {T}

::Pregunta 3:: ¿Qué significa HTML? {
=HyperText Markup Language
~High Tech Modern Language
~Home Tool Markup Language
}
"""
        banco_ejemplo.write_text(contenido_banco, encoding='utf-8')
        logger.info(f"✓ Banco de ejemplo creado: bancos/banco_ejemplo.txt")
    else:
        logger.info(f"  Banco ya existe: bancos/banco_ejemplo.txt")
    
    # Crear README
    readme = Path('README_PROYECTO.md')
    if not readme.exists():
        contenido_readme = """# Proyecto de Generación de Exámenes

Este proyecto usa **alucarD** (generador-examenes) para crear exámenes personalizados.

## Estructura de Directorios

```
.
├── bancos/              # Bancos de preguntas (GIFT o Moodle XML)
├── templates/           # Plantillas Jinja2 personalizables
├── i18n/                # Archivos de internacionalización
├── output/              # Exámenes generados
└── definicion_ejemplo.yaml  # Ejemplo de definición de examen
```

## Uso Rápido

### 1. Validar la definición

```bash
generador-examenes -d definicion_ejemplo.yaml \\
  -i bancos/banco_ejemplo.txt \\
  --validate
```

### 2. Generar exámenes

```bash
generador-examenes -d definicion_ejemplo.yaml \\
  -i bancos/banco_ejemplo.txt \\
  -o output \\
  -n 3 \\
  -f html
```

## Siguientes Pasos

1. Edita `definicion_ejemplo.yaml` con tu configuración
2. Agrega tus bancos de preguntas en `bancos/`
3. Personaliza las plantillas en `templates/` (opcional)
4. Genera tus exámenes con el comando anterior

## Documentación

Para más información, consulta la documentación oficial de alucarD.
"""
        readme.write_text(contenido_readme, encoding='utf-8')
        logger.info(f"✓ README creado: README_PROYECTO.md")
    else:
        logger.info(f"  README ya existe: README_PROYECTO.md")
    
    print("\n" + "="*60)
    print("✓ INICIALIZACIÓN COMPLETADA")
    print("="*60)
    print("\nArchivos y directorios creados:")
    print("  - templates/          (plantillas HTML)")
    print("  - i18n/               (archivos de idioma)")
    print("  - bancos/             (bancos de preguntas)")
    print("  - output/             (exámenes generados)")
    print("  - definicion_ejemplo.yaml")
    print("  - banco_ejemplo.txt")
    print("  - README_PROYECTO.md")
    print("\nPróximos pasos:")
    print("  1. Edita definicion_ejemplo.yaml con tu configuración")
    print("  2. Agrega tus bancos de preguntas en bancos/")
    print("  3. Ejecuta: generador-examenes -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt --validate")
    print("  4. Genera exámenes: generador-examenes -d definicion_ejemplo.yaml -i bancos/banco_ejemplo.txt -n 3")
    print()


def main():
    """Función principal del CLI"""
    parser = argparse.ArgumentParser(
        prog='generador-examenes',
        description='Generador de exámenes basado en plantillas YAML y bancos Moodle/GIFT'
    )
    
    # Argumentos principales
    parser.add_argument(
        '--init',
        action='store_true',
        help='Inicializar proyecto con archivos de ejemplo'
    )
    
    parser.add_argument(
        '--wizard',
        nargs='?',
        const=None,
        type=Path,
        metavar='YAML',
        help='Asistente interactivo para crear/editar configuración de examen'
    )
    
    parser.add_argument(
        '-d', '--definicion',
        type=Path,
        help='Ruta al archivo de definición YAML del examen'
    )
    
    parser.add_argument(
        '-i', '--input-banco',
        type=Path,
        nargs='+',
        help='Ruta(s) a los archivos de banco de preguntas'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        default=Path('./output'),
        help='Directorio de salida para los exámenes generados (default: ./output)'
    )
    
    parser.add_argument(
        '-p', '--path-images',
        type=Path,
        help='Ruta al directorio de imágenes referenciadas en las preguntas'
    )
    
    parser.add_argument(
        '-n', '--numero-temas',
        type=int,
        default=1,
        help='Número de temas/versiones a generar (default: 1)'
    )
    
    parser.add_argument(
        '-s', '--semilla',
        type=int,
        default=42,
        help='Semilla pseudo-aleatoria para generación (default: 42)'
    )
    
    parser.add_argument(
        '-f', '--formato',
        nargs='+',
        choices=['html', 'pdf'],
        default=['html'],
        help='Formato(s) de salida (default: html)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validar la definición sin generar archivos'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug con logging detallado'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    from generador_examenes.config.logging_config import setup_logging
    setup_logging(debug=args.debug)
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Modo inicialización
    if args.init:
        logger.info("Modo inicialización - creando archivos de ejemplo")
        try:
            inicializar_proyecto()
            return 0
        except Exception as e:
            logger.error(f"Error durante la inicialización: {e}")
            if args.debug:
                raise
            return 1
    
    # Modo wizard
    if args.wizard is not None:
        try:
            from generador_examenes.config.exam_wizard import run_wizard
            run_wizard(args.wizard)
            return 0
        except Exception as e:
            logger.error(f"Error en el wizard: {e}")
            if args.debug:
                raise
            return 1
    
    # Validar argumentos requeridos
    if not args.definicion:
        parser.error("Se requiere --definicion (o --init para inicializar, o --wizard para configurar)")
    
    if not args.input_banco:
        parser.error("Se requiere --input-banco con al menos un archivo de banco")
    
    logger.info(f"Iniciando generador de exámenes v5.0.0")
    logger.info(f"Definición: {args.definicion}")
    logger.info(f"Bancos: {args.input_banco}")
    logger.info(f"Formato(s): {args.formato}")
    
    try:
        # Cargar y validar definición
        import yaml
        from pydantic import ValidationError
        from generador_examenes.core.models import DefinicionExamen
        from generador_examenes.core import logic
        from generador_examenes.generators import obtener_renderer
        
        logger.info("Cargando definición del examen...")
        with open(args.definicion, 'r', encoding='utf-8') as f:
            definicion_yaml = yaml.safe_load(f)
        
        try:
            definicion = DefinicionExamen(**definicion_yaml)
            logger.info("Definición validada correctamente")
        except ValidationError as e:
            logger.error(f"Error de validación en definición:\n{e}")
            return 1
        
        # Cargar bancos de preguntas
        logger.info("Cargando bancos de preguntas...")
        banco_completo = logic.cargar_bancos(args.input_banco)
        
        if not banco_completo:
            logger.error("No se cargaron preguntas de los bancos")
            return 1
        
        # Procesar imágenes si se especificó directorio
        if args.path_images:
            logger.info("Procesando imágenes...")
            logic.procesar_imagenes(banco_completo, args.path_images)
        
        # Construir pool del examen
        logger.info("Construyendo pool del examen...")
        examen_base = logic.construir_pool_examen(definicion, banco_completo)
        
        # Calcular puntaje total
        puntaje_total = logic.calcular_puntaje_total(examen_base)
        logger.info(f"Puntaje total del examen: {puntaje_total}")
        
        # Modo validación
        if args.validate:
            print("\n" + "="*60)
            print("VALIDACIÓN DEL EXAMEN")
            print("="*60)
            print(f"\nExamen: {definicion.nombre_examen}")
            print(f"Institución: {definicion.institucion}")
            print(f"Materia: {definicion.materia}")
            print(f"\nPuntaje total: {puntaje_total}")
            print(f"\nSecciones:")
            for seccion in examen_base['secciones']:
                num_preguntas = len(seccion['preguntas'])
                puntaje_seccion = sum(p.puntaje for p in seccion['preguntas'])
                print(f"  - {seccion['nombre']}: {num_preguntas} preguntas, {puntaje_seccion} puntos")
            print("\nValidación exitosa ✓")
            return 0
        
        # Modo generación
        logger.info(f"Generando {args.numero_temas} tema(s)...")
        
        for i in range(args.numero_temas):
            semilla_tema = args.semilla + i
            logger.info(f"Generando tema {i + 1}/{args.numero_temas} (semilla: {semilla_tema})")
            
            # Mezclar examen para este tema
            examen_mezclado = logic.mezclar_examen(
                examen_base,
                semilla_tema,
                definicion.configuracion_examen
            )
            
            # Generar en cada formato solicitado
            for formato in args.formato:
                try:
                    renderer = obtener_renderer(formato)
                    
                    # Generar examen
                    archivo_examen = renderer.renderizar_examen(
                        examen_mezclado,
                        definicion,
                        args.output_dir,
                        i
                    )
                    print(f"✓ Examen generado: {archivo_examen}")
                    
                    # Generar clave si está configurado
                    if definicion.configuracion_examen.generar_clave_profesor:
                        archivo_clave = renderer.renderizar_clave(
                            examen_mezclado,
                            definicion,
                            args.output_dir,
                            i
                        )
                        print(f"✓ Clave generada: {archivo_clave}")
                
                except Exception as e:
                    logger.error(f"Error generando formato {formato}: {e}")
                    if args.debug:
                        raise
        
        print(f"\n✓ Generación completada exitosamente")
        print(f"  Archivos guardados en: {args.output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        if args.debug:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
