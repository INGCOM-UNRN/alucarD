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
    
    # TODO: Implementar flujo principal
    print("Flujo principal pendiente de implementación")
    print("El esqueleto del proyecto está listo para desarrollo")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
