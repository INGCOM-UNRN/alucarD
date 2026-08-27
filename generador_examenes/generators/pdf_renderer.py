"""
Renderizador PDF usando Typst con soporte de plantillas personalizables.
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from generador_examenes.core.models import DefinicionExamen
from generador_examenes.generators.base import BaseRenderer
from generador_examenes.generators.html_renderer import HtmlRenderer


logger = logging.getLogger(__name__)


def compilar_typst_a_pdf(typst_source: str, output_pdf: Path, root_dir: Optional[Path] = None) -> Path:
    """Compila código Typst a un archivo PDF usando la librería python o el binario CLI."""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".typ", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(typst_source)
        tmp_path = Path(tmp.name)

    try:
        try:
            import typst
            typst.compile(str(tmp_path), output=str(output_pdf), root=str(root_dir) if root_dir else None)
            return output_pdf
        except Exception as e_py:
            # Fallback a binario typst de sistema
            res = subprocess.run(
                ["typst", "compile", str(tmp_path), str(output_pdf)],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode != 0:
                raise RuntimeError(f"Fallo en compilación Typst: {res.stderr or e_py}")
            return output_pdf
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


class PdfRenderer(BaseRenderer):
    """Renderizador para generar archivos PDF vía Typst (con soporte de plantillas personalizadas)."""

    def __init__(self, templates_dir: Path | None = None, custom_typst_template: Path | None = None):
        """
        Inicializa el renderizador PDF con motor Typst.

        Args:
            templates_dir: Directorio de plantillas (por defecto usa ./templates)
            custom_typst_template: Ruta a una plantilla Typst personalizada (.typ / .typ.j2)
        """
        self.templates_dir = templates_dir or (Path(__file__).parent.parent.parent / 'templates')
        self.custom_typst_template = custom_typst_template
        self.html_renderer = HtmlRenderer(templates_dir)

    @staticmethod
    def get_supported_formats() -> list[str]:
        return ['pdf', 'typst', 'typ']

    def renderizar_examen(
        self,
        examen_data: Any,
        definicion: DefinicionExamen,
        output_dir: Path,
        tema: int
    ) -> Path:
        """
        Renderiza un examen en formato PDF usando Typst.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Generando Typst para PDF del tema {tema + 1}")

        from jinja2 import Environment, FileSystemLoader
        import json

        # Cargar traducciones
        i18n_dir = Path(__file__).parent.parent.parent / 'i18n'
        i18n_file = i18n_dir / f"{definicion.idioma}.json"
        if not i18n_file.exists():
            i18n_file = i18n_dir / "es.json"

        i18n = {}
        if i18n_file.exists():
            with open(i18n_file, 'r', encoding='utf-8') as f:
                i18n = json.load(f)

        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }

        # Cargar plantilla Typst
        if self.custom_typst_template and self.custom_typst_template.exists():
            template_content = self.custom_typst_template.read_text(encoding="utf-8")
            env = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
            template = env.from_string(template_content)
        else:
            search_dirs = [str(self.templates_dir), str(Path(__file__).parent.parent.parent / 'templates')]
            env = Environment(
                loader=FileSystemLoader(search_dirs),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True
            )
            try:
                template = env.get_template('base_examen.typ.j2')
            except Exception:
                # Fallback a HTML + WeasyPrint si no existe plantilla typst
                return self._renderizar_examen_weasyprint(examen_data, definicion, output_dir, tema)

        typst_content = template.render(**contexto)
        output_file = output_dir / f"examen_tema_{tema + 1:02d}.pdf"

        try:
            compilar_typst_a_pdf(typst_content, output_file, root_dir=self.templates_dir)
            logger.info(f"Examen PDF generado con Typst: {output_file}")
            return output_file
        except Exception as e:
            logger.warning(f"Error compilando con Typst ({e}), intentando fallback HTML/WeasyPrint...")
            return self._renderizar_examen_weasyprint(examen_data, definicion, output_dir, tema)

    def renderizar_clave(
        self,
        examen_data: Any,
        definicion: DefinicionExamen,
        output_dir: Path,
        tema: int
    ) -> Path:
        """
        Renderiza la clave de respuestas en formato PDF usando Typst.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Generando clave Typst para PDF del tema {tema + 1}")

        from jinja2 import Environment, FileSystemLoader
        import json

        i18n_dir = Path(__file__).parent.parent.parent / 'i18n'
        i18n_file = i18n_dir / f"{definicion.idioma}.json"
        if not i18n_file.exists():
            i18n_file = i18n_dir / "es.json"

        i18n = {}
        if i18n_file.exists():
            with open(i18n_file, 'r', encoding='utf-8') as f:
                i18n = json.load(f)

        contexto = {
            'definicion': definicion,
            'secciones': examen_data.get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }

        search_dirs = [str(self.templates_dir), str(Path(__file__).parent.parent.parent / 'templates')]
        env = Environment(
            loader=FileSystemLoader(search_dirs),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        try:
            template = env.get_template('clave_profesor.typ.j2')
            typst_content = template.render(**contexto)
            output_file = output_dir / f"clave_tema_{tema + 1:02d}.pdf"
            compilar_typst_a_pdf(typst_content, output_file, root_dir=self.templates_dir)
            logger.info(f"Clave PDF generada con Typst: {output_file}")
            return output_file
        except Exception as e:
            logger.warning(f"Error compilando clave con Typst ({e}), intentando fallback HTML/WeasyPrint...")
            return self._renderizar_clave_weasyprint(examen_data, definicion, output_dir, tema)

    def _renderizar_examen_weasyprint(self, examen_data, definicion, output_dir, tema) -> Path:
        from jinja2 import Environment, FileSystemLoader
        import json
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template('base_examen.html.j2')
        contexto = {'definicion': definicion, 'secciones': examen_data.get('secciones', []), 'tema': tema, 'i18n': {}}
        html_content = template.render(**contexto)
        output_file = output_dir / f"examen_tema_{tema + 1:02d}.pdf"
        import weasyprint
        weasyprint.HTML(string=html_content, base_url=str(templates_dir)).write_pdf(str(output_file))
        return output_file

    def _renderizar_clave_weasyprint(self, examen_data, definicion, output_dir, tema) -> Path:
        from jinja2 import Environment, FileSystemLoader
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template('clave_profesor.html.j2')
        contexto = {'definicion': definicion, 'secciones': examen_data.get('secciones', []), 'tema': tema, 'i18n': {}}
        html_content = template.render(**contexto)
        output_file = output_dir / f"clave_tema_{tema + 1:02d}.pdf"
        import weasyprint
        weasyprint.HTML(string=html_content, base_url=str(templates_dir)).write_pdf(str(output_file))
        return output_file
