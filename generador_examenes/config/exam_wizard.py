"""
Asistente interactivo para configurar archivos YAML de exámenes
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class ExamWizard:
    """Asistente interactivo para crear/editar configuraciones de exámenes"""
    
    def __init__(self, yaml_path: Optional[Path] = None):
        self.yaml_path = yaml_path
        self.config: Dict[str, Any] = {}
        
        if yaml_path and yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
    
    def run(self):
        """Ejecuta el asistente interactivo"""
        console.clear()
        self._mostrar_banner()
        
        if self.yaml_path and self.yaml_path.exists():
            console.print(f"\n[cyan]Editando examen existente:[/cyan] [yellow]{self.yaml_path}[/yellow]")
            if not Confirm.ask("¿Deseas modificar este examen?", default=True):
                return
        else:
            console.print("\n[cyan]Creando nuevo examen[/cyan]")
            self.yaml_path = Path(Prompt.ask(
                "Nombre del archivo YAML",
                default="mi_examen.yaml"
            ))
        
        # Pasos del asistente
        self._configurar_informacion_basica()
        self._configurar_parametros_examen()
        self._configurar_secciones()
        
        # Mostrar resumen y guardar
        self._mostrar_resumen()
        
        if Confirm.ask("\n¿Guardar esta configuración?", default=True):
            self._guardar_yaml()
            console.print(f"\n[green]✓ Configuración guardada en:[/green] [yellow]{self.yaml_path}[/yellow]")
        else:
            console.print("\n[yellow]Configuración descartada[/yellow]")
    
    def _mostrar_banner(self):
        """Muestra el banner del asistente"""
        banner = """
[bold cyan]╔════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║     ASISTENTE DE CONFIGURACIÓN DE EXÁMENES            ║[/bold cyan]
[bold cyan]║            alucarD - Generador de Exámenes            ║[/bold cyan]
[bold cyan]╚════════════════════════════════════════════════════════╝[/bold cyan]
        """
        console.print(banner)
    
    def _configurar_informacion_basica(self):
        """Configura información básica del examen"""
        console.print("\n[bold]1. INFORMACIÓN BÁSICA[/bold]")
        console.print("─" * 60)
        
        self.config['nombre_examen'] = Prompt.ask(
            "Nombre del examen",
            default=self.config.get('nombre_examen', 'Examen Parcial I')
        )
        
        self.config['institucion'] = Prompt.ask(
            "Institución",
            default=self.config.get('institucion', 'Mi Universidad')
        )
        
        self.config['materia'] = Prompt.ask(
            "Materia/Asignatura",
            default=self.config.get('materia', 'Mi Materia')
        )
        
        if Confirm.ask("¿Incluir fecha del examen?", default=True):
            self.config['fecha'] = Prompt.ask(
                "Fecha (YYYY-MM-DD)",
                default=self.config.get('fecha', '2025-01-01')
            )
        
        if Confirm.ask("¿Especificar duración?", default=True):
            self.config['duracion_minutos'] = IntPrompt.ask(
                "Duración en minutos",
                default=self.config.get('duracion_minutos', 60)
            )
        
        if Confirm.ask("¿Agregar instrucciones generales?", default=True):
            default_instrucciones = self.config.get(
                'instrucciones_generales',
                'Lee cuidadosamente cada pregunta antes de responder.'
            )
            console.print("[dim]Instrucciones actuales:[/dim]")
            console.print(f"[dim]{default_instrucciones}[/dim]")
            
            if Confirm.ask("¿Modificar instrucciones?", default=False):
                console.print("[yellow]Escribe las instrucciones (termina con línea vacía):[/yellow]")
                lineas = []
                while True:
                    linea = input()
                    if not linea:
                        break
                    lineas.append(linea)
                self.config['instrucciones_generales'] = '\n'.join(lineas)
            else:
                self.config['instrucciones_generales'] = default_instrucciones
        
        self.config['idioma'] = Prompt.ask(
            "Idioma (es/en)",
            choices=['es', 'en'],
            default=self.config.get('idioma', 'es')
        )
    
    def _configurar_parametros_examen(self):
        """Configura parámetros de configuración del examen"""
        console.print("\n[bold]2. CONFIGURACIÓN DEL EXAMEN[/bold]")
        console.print("─" * 60)
        
        config_examen = self.config.get('configuracion_examen', {})
        
        config_examen['mezclar_preguntas_dentro_seccion'] = Confirm.ask(
            "¿Mezclar preguntas dentro de cada sección?",
            default=config_examen.get('mezclar_preguntas_dentro_seccion', True)
        )
        
        config_examen['mezclar_opciones_dentro_pregunta'] = Confirm.ask(
            "¿Mezclar opciones de cada pregunta?",
            default=config_examen.get('mezclar_opciones_dentro_pregunta', True)
        )
        
        config_examen['generar_clave_profesor'] = Confirm.ask(
            "¿Generar clave de respuestas para el profesor?",
            default=config_examen.get('generar_clave_profesor', True)
        )
        
        self.config['configuracion_examen'] = config_examen
    
    def _configurar_secciones(self):
        """Configura las secciones del examen"""
        console.print("\n[bold]3. SECCIONES DEL EXAMEN[/bold]")
        console.print("─" * 60)
        
        secciones_existentes = self.config.get('secciones_examen', [])
        
        if secciones_existentes:
            console.print(f"\n[cyan]Secciones existentes: {len(secciones_existentes)}[/cyan]")
            for i, seccion in enumerate(secciones_existentes, 1):
                console.print(f"  {i}. {seccion['nombre']} - {len(seccion.get('pools', []))} pool(s)")
            
            if not Confirm.ask("\n¿Modificar secciones existentes?", default=False):
                return
        
        secciones = []
        continuar = True
        
        while continuar:
            num_seccion = len(secciones) + 1
            console.print(f"\n[bold cyan]Configurando Sección #{num_seccion}[/bold cyan]")
            
            seccion = self._configurar_seccion()
            secciones.append(seccion)
            
            continuar = Confirm.ask("\n¿Agregar otra sección?", default=False)
        
        self.config['secciones_examen'] = secciones
    
    def _configurar_seccion(self) -> Dict[str, Any]:
        """Configura una sección individual"""
        seccion = {}
        
        seccion['nombre'] = Prompt.ask(
            "  Nombre de la sección",
            default="Sección 1"
        )
        
        if Confirm.ask("  ¿Agregar instrucciones específicas?", default=False):
            seccion['instrucciones'] = Prompt.ask("  Instrucciones")
        
        # Configurar pools
        console.print("\n  [yellow]Configuración de pools de preguntas[/yellow]")
        pools = []
        
        continuar_pools = True
        while continuar_pools:
            pool = self._configurar_pool()
            pools.append(pool)
            
            continuar_pools = Confirm.ask("  ¿Agregar otro pool?", default=False)
        
        seccion['pools'] = pools
        return seccion
    
    def _configurar_pool(self) -> Dict[str, Any]:
        """Configura un pool de preguntas"""
        pool = {}
        
        console.print("\n  [dim]Opciones de filtrado:[/dim]")
        console.print("  [dim]1. Categoría (ej: Math/Algebra, Programacion/**)  [/dim]")
        console.print("  [dim]2. Tipos (seleccion_multiple, verdadero_falso, etc.)[/dim]")
        console.print("  [dim]3. Etiquetas (facil, intermedio, avanzado, etc.)[/dim]")
        console.print("  [dim]4. Preguntas específicas (por ID)[/dim]")
        
        filtro = Prompt.ask(
            "\n  Tipo de filtro",
            choices=['categoria', 'tipos', 'etiquetas', 'fijadas', 'ninguno'],
            default='ninguno'
        )
        
        if filtro == 'categoria':
            pool['categoria'] = Prompt.ask("    Categoría")
        elif filtro == 'tipos':
            tipos_str = Prompt.ask(
                "    Tipos (separados por coma)",
                default="seleccion_multiple"
            )
            pool['tipos'] = [t.strip() for t in tipos_str.split(',')]
        elif filtro == 'etiquetas':
            etiquetas_str = Prompt.ask("    Etiquetas (separadas por coma)")
            pool['etiquetas'] = [e.strip() for e in etiquetas_str.split(',')]
        elif filtro == 'fijadas':
            ids_str = Prompt.ask("    IDs de preguntas (separados por coma)")
            pool['preguntas_fijadas'] = [id.strip() for id in ids_str.split(',')]
        
        if filtro != 'fijadas':
            pool['cantidad'] = IntPrompt.ask(
                "    Cantidad de preguntas",
                default=5
            )
            
            accion = Prompt.ask(
                "    Si no hay suficientes preguntas",
                choices=['error', 'advertir', 'usar_todas'],
                default='advertir'
            )
            pool['accion_si_insuficiente'] = accion
        
        return pool
    
    def _mostrar_resumen(self):
        """Muestra un resumen de la configuración"""
        console.print("\n[bold]RESUMEN DE LA CONFIGURACIÓN[/bold]")
        console.print("=" * 60)
        
        # Información básica
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="yellow")
        
        table.add_row("Nombre", self.config.get('nombre_examen', '-'))
        table.add_row("Institución", self.config.get('institucion', '-'))
        table.add_row("Materia", self.config.get('materia', '-'))
        if 'fecha' in self.config:
            table.add_row("Fecha", self.config['fecha'])
        if 'duracion_minutos' in self.config:
            table.add_row("Duración", f"{self.config['duracion_minutos']} min")
        table.add_row("Idioma", self.config.get('idioma', 'es'))
        
        console.print(table)
        
        # Configuración
        config_exam = self.config.get('configuracion_examen', {})
        console.print("\n[bold]Configuración:[/bold]")
        console.print(f"  • Mezclar preguntas: {config_exam.get('mezclar_preguntas_dentro_seccion', True)}")
        console.print(f"  • Mezclar opciones: {config_exam.get('mezclar_opciones_dentro_pregunta', True)}")
        console.print(f"  • Generar clave: {config_exam.get('generar_clave_profesor', True)}")
        
        # Secciones
        secciones = self.config.get('secciones_examen', [])
        console.print(f"\n[bold]Secciones ({len(secciones)}):[/bold]")
        for i, seccion in enumerate(secciones, 1):
            pools = seccion.get('pools', [])
            console.print(f"  {i}. {seccion['nombre']} - {len(pools)} pool(s)")
            for j, pool in enumerate(pools, 1):
                pool_desc = self._describir_pool(pool)
                console.print(f"     {i}.{j} {pool_desc}")
    
    def _describir_pool(self, pool: Dict[str, Any]) -> str:
        """Genera descripción legible de un pool"""
        partes = []
        
        if 'preguntas_fijadas' in pool:
            partes.append(f"{len(pool['preguntas_fijadas'])} preguntas fijadas")
        else:
            if 'categoria' in pool:
                partes.append(f"cat:{pool['categoria']}")
            if 'tipos' in pool:
                partes.append(f"tipos:{','.join(pool['tipos'])}")
            if 'etiquetas' in pool:
                partes.append(f"tags:{','.join(pool['etiquetas'])}")
            if 'cantidad' in pool:
                partes.append(f"cant:{pool['cantidad']}")
        
        return " | ".join(partes) if partes else "sin filtros"
    
    def _guardar_yaml(self):
        """Guarda la configuración en archivo YAML"""
        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )


def run_wizard(yaml_path: Optional[Path] = None):
    """Ejecuta el asistente de configuración"""
    try:
        wizard = ExamWizard(yaml_path)
        wizard.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Asistente cancelado por el usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
