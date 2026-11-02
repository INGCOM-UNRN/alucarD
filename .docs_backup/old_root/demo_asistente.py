"""
Script de demostración del wizard (sin interacción real)
Muestra cómo se vería la salida del wizard
"""
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

def demo_wizard():
    """Demuestra el wizard sin interacción"""
    
    # Banner
    banner = """
[bold cyan]╔════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║     ASISTENTE DE CONFIGURACIÓN DE EXÁMENES            ║[/bold cyan]
[bold cyan]║            alucarD - Generador de Exámenes            ║[/bold cyan]
[bold cyan]╚════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)
    
    console.print("\n[cyan]Creando nuevo examen[/cyan]")
    console.print("Nombre del archivo YAML: [yellow]mi_examen_demo.yaml[/yellow]")
    
    # Paso 1: Información básica
    console.print("\n[bold]1. INFORMACIÓN BÁSICA[/bold]")
    console.print("─" * 60)
    console.print("Nombre del examen: [yellow]Examen Parcial de Matemáticas[/yellow]")
    console.print("Institución: [yellow]Universidad Nacional[/yellow]")
    console.print("Materia/Asignatura: [yellow]Álgebra Lineal[/yellow]")
    console.print("Fecha (YYYY-MM-DD): [yellow]2025-11-15[/yellow]")
    console.print("Duración en minutos: [yellow]120[/yellow]")
    console.print("Idioma (es/en): [yellow]es[/yellow]")
    
    # Paso 2: Configuración
    console.print("\n[bold]2. CONFIGURACIÓN DEL EXAMEN[/bold]")
    console.print("─" * 60)
    console.print("¿Mezclar preguntas dentro de cada sección? [yellow]Sí[/yellow]")
    console.print("¿Mezclar opciones de cada pregunta? [yellow]Sí[/yellow]")
    console.print("¿Generar clave de respuestas para el profesor? [yellow]Sí[/yellow]")
    
    # Paso 3: Secciones
    console.print("\n[bold]3. SECCIONES DEL EXAMEN[/bold]")
    console.print("─" * 60)
    
    console.print("\n[bold cyan]Configurando Sección #1[/bold cyan]")
    console.print("  Nombre de la sección: [yellow]Parte 1: Vectores y Matrices[/yellow]")
    console.print("  ¿Agregar instrucciones específicas? [yellow]No[/yellow]")
    
    console.print("\n  [yellow]Configuración de pools de preguntas[/yellow]")
    console.print("  Tipo de filtro: [yellow]categoria[/yellow]")
    console.print("    Categoría: [yellow]Matemáticas/Álgebra/**[/yellow]")
    console.print("    Cantidad de preguntas: [yellow]10[/yellow]")
    console.print("    Si no hay suficientes preguntas: [yellow]advertir[/yellow]")
    console.print("  ¿Agregar otro pool? [yellow]No[/yellow]")
    
    console.print("\n[bold cyan]Configurando Sección #2[/bold cyan]")
    console.print("  Nombre de la sección: [yellow]Parte 2: Problemas Aplicados[/yellow]")
    
    console.print("\n  [yellow]Configuración de pools de preguntas[/yellow]")
    console.print("  Tipo de filtro: [yellow]etiquetas[/yellow]")
    console.print("    Etiquetas (separadas por coma): [yellow]aplicado, avanzado[/yellow]")
    console.print("    Cantidad de preguntas: [yellow]5[/yellow]")
    console.print("    Si no hay suficientes preguntas: [yellow]advertir[/yellow]")
    console.print("  ¿Agregar otro pool? [yellow]No[/yellow]")
    
    console.print("\n¿Agregar otra sección? [yellow]No[/yellow]")
    
    # Resumen
    console.print("\n[bold]RESUMEN DE LA CONFIGURACIÓN[/bold]")
    console.print("=" * 60)
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="yellow")
    
    table.add_row("Nombre", "Examen Parcial de Matemáticas")
    table.add_row("Institución", "Universidad Nacional")
    table.add_row("Materia", "Álgebra Lineal")
    table.add_row("Fecha", "2025-11-15")
    table.add_row("Duración", "120 min")
    table.add_row("Idioma", "es")
    
    console.print(table)
    
    console.print("\n[bold]Configuración:[/bold]")
    console.print("  • Mezclar preguntas: True")
    console.print("  • Mezclar opciones: True")
    console.print("  • Generar clave: True")
    
    console.print("\n[bold]Secciones (2):[/bold]")
    console.print("  1. Parte 1: Vectores y Matrices - 1 pool(s)")
    console.print("     1.1 cat:Matemáticas/Álgebra/** | cant:10")
    console.print("  2. Parte 2: Problemas Aplicados - 1 pool(s)")
    console.print("     2.1 tags:aplicado,avanzado | cant:5")
    
    console.print("\n¿Guardar esta configuración? [yellow]Sí[/yellow]")
    console.print("\n[green]✓ Configuración guardada en:[/green] [yellow]mi_examen_demo.yaml[/yellow]")
    
    # Mostrar contenido del YAML generado
    console.print("\n[bold]Contenido del archivo generado:[/bold]")
    console.print("[dim]─" * 60 + "[/dim]")
    
    yaml_content = """nombre_examen: Examen Parcial de Matemáticas
institucion: Universidad Nacional
materia: Álgebra Lineal
fecha: '2025-11-15'
duracion_minutos: 120
instrucciones_generales: Lee cuidadosamente cada pregunta antes de responder.
idioma: es
configuracion_examen:
  mezclar_preguntas_dentro_seccion: true
  mezclar_opciones_dentro_pregunta: true
  generar_clave_profesor: true
secciones_examen:
- nombre: 'Parte 1: Vectores y Matrices'
  pools:
  - categoria: Matemáticas/Álgebra/**
    cantidad: 10
    accion_si_insuficiente: advertir
- nombre: 'Parte 2: Problemas Aplicados'
  pools:
  - etiquetas:
    - aplicado
    - avanzado
    cantidad: 5
    accion_si_insuficiente: advertir"""
    
    console.print(f"[green]{yaml_content}[/green]")
    console.print("[dim]─" * 60 + "[/dim]")
    
    console.print("\n[bold cyan]Uso del wizard:[/bold cyan]")
    console.print("  • Crear nuevo: [yellow]generador-examenes --wizard[/yellow]")
    console.print("  • Editar:      [yellow]generador-examenes --wizard mi_examen.yaml[/yellow]")

if __name__ == "__main__":
    demo_wizard()
