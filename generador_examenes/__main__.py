"""
Punto de entrada principal de la aplicación
"""
import sys
import argparse
from pathlib import Path


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
        # TODO: Implementar lógica de inicialización
        print("Función de inicialización pendiente de implementación")
        return 0
    
    # Validar argumentos requeridos
    if not args.definicion:
        parser.error("Se requiere --definicion (o --init para inicializar)")
    
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
