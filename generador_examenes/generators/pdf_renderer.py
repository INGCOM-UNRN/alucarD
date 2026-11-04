"""
Renderizador PDF usando Typst con soporte de plantillas personalizables.
"""
import functools
import logging
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from generador_examenes.core.models import DefinicionExamen
from generador_examenes.core.estilo import contexto_estilo, preparar_examen
from generador_examenes.generators.base import BaseRenderer
from generador_examenes.generators.html_renderer import HtmlRenderer


logger = logging.getLogger(__name__)

TIMEOUT_TYPST = 300  # segundos para el binario typst (el primer arranque indexa las fuentes del sistema)


@functools.lru_cache(maxsize=1)
def _fuentes_typst(libreria):
    """Las fuentes del sistema, cargadas una vez por proceso.

    Cada `typst.compile` las volvía a buscar (unos 0,3 s): con varios temas, sus claves, la búsqueda
    de la pregunta que no compila o `--watch`, eso era casi todo el tiempo de la generación. Con las
    fuentes ya cargadas, una compilación tarda milisegundos.
    """
    fuentes = getattr(libreria, "Fonts", None)
    return fuentes() if fuentes is not None else None


def compilar_typst_a_pdf(typst_source: str, output_pdf: Path, root_dir: Optional[Path] = None) -> Path:
    """Compila código Typst a un archivo PDF usando la librería python o el binario CLI."""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".typ", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(typst_source)
        tmp_path = Path(tmp.name)

    root = str(root_dir) if (root_dir and tmp_path.is_relative_to(root_dir)) else None
    try:
        try:
            import typst as libreria_typst
        except ImportError:
            libreria_typst = None  # type: ignore[assignment]
        if libreria_typst is not None:
            # Un error de compilación de la librería se informa tal cual: el binario fallaría igual,
            # y sólo arrancar puede llevar decenas de segundos (recorre todas las fuentes del sistema).
            try:
                fuentes = _fuentes_typst(libreria_typst)
                extra = {"font_paths": fuentes} if fuentes is not None else {}
                libreria_typst.compile(str(tmp_path), output=str(output_pdf), root=root, **extra)
            except Exception as e_py:
                raise RuntimeError(f"Fallo en compilación Typst: {e_py}") from e_py
            return output_pdf

        # Sin la librería: binario typst del sistema
        cmd = ["typst", "compile", *(["--root", root] if root else []), str(tmp_path), str(output_pdf)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=TIMEOUT_TYPST)
        except FileNotFoundError as e:
            raise RuntimeError("Typst no está instalado (ni la librería de Python ni el binario)") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Typst no terminó en {TIMEOUT_TYPST} s") from e
        if res.returncode != 0:
            raise RuntimeError(f"Fallo en compilación Typst: {res.stderr}")
        return output_pdf
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _con_filtros(env):
    """`|typst` convierte el HTML de las preguntas a marcado Typst; `letra(i)` da A, B, C…"""
    from generador_examenes.generators.typst_markup import _cadena, escapar, html_a_typst, largo_visible, letra

    env.filters["typst"] = html_a_typst
    env.filters["typst_texto"] = lambda t: escapar("" if t is None else str(t))
    env.filters["typst_cadena"] = lambda t: _cadena("" if t is None else str(t))
    env.globals["letra"] = letra
    env.filters["largo_visible"] = largo_visible
    return env


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

        contexto = {**contexto_estilo(definicion, tema, clave=False),
            'definicion': definicion,
            'secciones': preparar_examen(examen_data, definicion).get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }

        # Cargar plantilla Typst
        if self.custom_typst_template and self.custom_typst_template.exists():
            template_content = self.custom_typst_template.read_text(encoding="utf-8")
            env = _con_filtros(Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True))
            template = env.from_string(template_content)
        else:
            search_dirs = [str(self.templates_dir), str(Path(__file__).parent.parent.parent / 'templates')]
            env = _con_filtros(Environment(
                loader=FileSystemLoader(search_dirs),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True
            ))
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
            self._avisar_fallo_typst(e, template, contexto)
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

        contexto = {**contexto_estilo(definicion, tema, clave=True),
            'definicion': definicion,
            'secciones': preparar_examen(examen_data, definicion).get('secciones', []),
            'tema': tema,
            'i18n': i18n
        }

        search_dirs = [str(self.templates_dir), str(Path(__file__).parent.parent.parent / 'templates')]
        env = _con_filtros(Environment(
            loader=FileSystemLoader(search_dirs),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        ))

        template = None
        try:
            template = env.get_template('clave_profesor.typ.j2')
            typst_content = template.render(**contexto)
            output_file = output_dir / f"clave_tema_{tema + 1:02d}.pdf"
            compilar_typst_a_pdf(typst_content, output_file, root_dir=self.templates_dir)
            logger.info(f"Clave PDF generada con Typst: {output_file}")
            return output_file
        except Exception as e:
            self._avisar_fallo_typst(e, template, contexto, "la clave")
            return self._renderizar_clave_weasyprint(examen_data, definicion, output_dir, tema)

    def _avisar_fallo_typst(self, error: Exception, template, contexto: dict, que: str = "el examen") -> None:
        """Typst no compiló: se dice en qué pregunta, para no tener que buscarla en el .typ generado."""
        culpable = self._pregunta_que_falla(template, contexto) if template is not None else None
        donde = f" en la pregunta {culpable}" if culpable else ""
        mensaje = (f"Typst no pudo compilar {que}{donde}: {str(error).splitlines()[0] if str(error) else error}. "
                   "Se genera con WeasyPrint.")
        logger.warning(mensaje)
        print(f"Aviso: {mensaje}", file=sys.stderr)

    def _pregunta_que_falla(self, template, contexto: dict) -> Optional[str]:
        """La primera pregunta que, sola, no compila (o «la plantilla» si falla sin preguntas).

        La librería de Typst no informa la línea del error; compilar de a una pregunta sólo cuesta
        tiempo cuando ya hubo un error."""
        import tempfile

        def compila(secciones) -> bool:
            with tempfile.TemporaryDirectory(prefix="alucard-typst-") as tmp:
                try:
                    compilar_typst_a_pdf(template.render(**{**contexto, "secciones": secciones}),
                                         Path(tmp) / "pregunta.pdf", root_dir=self.templates_dir)
                except Exception:
                    return False
            return True

        secciones = contexto.get("secciones", [])
        if not compila([{**s, "preguntas": []} for s in secciones]):
            return None
        for seccion in secciones:
            for preg in seccion.get("preguntas", []):
                if not compila([{**seccion, "preguntas": [preg]}]):
                    nombre = getattr(preg, "nombre", "?")
                    banco = getattr(preg, "fuente_banco", None)
                    return f"«{nombre}»" + (f" de {banco}" if banco else "")
        return None

    def _renderizar_examen_weasyprint(self, examen_data, definicion, output_dir, tema) -> Path:
        from jinja2 import Environment, FileSystemLoader
        import json
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template('base_examen.html.j2')
        contexto = {**contexto_estilo(definicion, tema, clave=False), 'definicion': definicion, 'secciones': preparar_examen(examen_data, definicion).get('secciones', []), 'tema': tema, 'i18n': {}}
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
        contexto = {**contexto_estilo(definicion, tema, clave=True), 'definicion': definicion, 'secciones': preparar_examen(examen_data, definicion).get('secciones', []), 'tema': tema, 'i18n': {}}
        html_content = template.render(**contexto)
        output_file = output_dir / f"clave_tema_{tema + 1:02d}.pdf"
        import weasyprint
        weasyprint.HTML(string=html_content, base_url=str(templates_dir)).write_pdf(str(output_file))
        return output_file
