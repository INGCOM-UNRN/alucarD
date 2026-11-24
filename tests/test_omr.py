"""Exámenes con carátula OMR (OMR_SPEC.md): validación, curva, manifiesto, QR, nómina, lote y geometría.

Los criterios de aceptación de §11: el manifiesto pasa el JSON Schema `omr-layout/2`, las burbujas del
PDF quedan a menos de 0,3 mm de su lugar, los QR se decodifican (zxing-cpp), pasan la verificación
`CHK` y el de configuración reconstruye el mismo manifiesto.
"""

import copy
import csv
import json
import shutil
import sys

import pytest

from generador_examenes.__main__ import main
from generador_examenes.omr import config, geometria, layout, nomina, notas, qr

EJEMPLO = {
    "exam_id": "PROG1-2026-P1", "title": "Programación I — Parcial 1", "layout_id": "OMR5E", "layout_version": 7,
    "variants": ["A", "B"], "cloud_sync_default": False,
    "grade_scale": {"min": 1.0, "max": 10.0, "decimals": 1, "step": None, "rounding": "half_up", "match_tolerance": 0},
    "grade_map": {"type": "piecewise_log", "pass_pct": 60.0, "pass_grade": 4.0, "promo_pct": 80.0,
                  "promo_grade": 7.0, "curve_k": 3.0, "fail_curve": "linear"},
    "rubric": [
        {"id": "ej1", "label": "Ejercicio 1", "max_points": 2.5, "levels": 5},
        {"id": "ej2", "label": "Ejercicio 2", "max_points": 2.5, "levels": 5},
        {"id": "ej3", "label": "Ejercicio 3 (V/F)", "max_points": 1.0, "levels": 2, "labels": ["✗", "✓"]},
        {"id": "ej4", "label": "Ejercicio 4", "max_points": 2.0, "levels": 5},
        {"id": "ej5", "label": "Ejercicio 5", "max_points": 2.0, "levels": 11},
    ],
}
CON_POPPLER = pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="falta pdftoppm")


def _config(**cambios):
    datos = copy.deepcopy(EJEMPLO)
    for clave, valor in cambios.items():
        if isinstance(valor, dict) and isinstance(datos.get(clave), dict):
            datos[clave].update(valor)
        else:
            datos[clave] = valor
    return config.desde_dict(datos)


# --- §3.3 Reglas de validación ---------------------------------------------------------------------

@pytest.mark.parametrize("cambios, mensaje", [
    ({"exam_id": "prog1"}, "exam_id"),
    ({"exam_id": "A" * 17}, "exam_id"),
    ({"variants": ["A", "b"]}, "variants: 'b'"),
    ({"variants": ["AB"]}, "variants: 'AB'"),
    ({"grade_scale": {"decimals": 3}}, "decimals"),
    ({"grade_scale": {"min": 10.0, "max": 10.0}}, "min (10) tiene que ser menor"),
    ({"grade_scale": {"match_tolerance": -1}}, "match_tolerance"),
    ({"grade_map": {"pass_pct": 49.9}}, "pass_pct: 49.9"),
    ({"grade_map": {"pass_pct": 70.1}}, "pass_pct: 70.1"),
    ({"grade_map": {"promo_pct": 60.0}}, "promo_pct: 60"),
    ({"grade_map": {"promo_pct": 100.0}}, "promo_pct: 100"),
    ({"grade_map": {"promo_grade": None}}, "promo_grade: es obligatorio"),
    ({"grade_map": {"promo_grade": 4.0}}, "promo_grade: 4.0"),
    ({"grade_map": {"promo_grade": 10.0}}, "promo_grade: 10.0"),
    ({"grade_map": {"curve_k": 10.5}}, "curve_k"),
    ({"rubric": [{"id": "e", "max_points": 1, "levels": 12}]}, "levels: 12"),
    ({"rubric": [{"id": "e", "max_points": 1, "levels": 1}]}, "levels: 1"),
    ({"rubric": [{"id": "e", "max_points": 0, "levels": 5}]}, "max_points: 0"),
    ({"rubric": [{"id": "e", "max_points": 1, "levels": 2}, {"id": "e", "max_points": 1, "levels": 2}]}, "duplicado"),
])
def test_reglas_de_validacion(cambios, mensaje):
    with pytest.raises(config.ErrorConfig) as e:
        _config(**cambios)
    assert any(mensaje in p for p in e.value.problemas), e.value.problemas


def test_junta_todos_los_problemas():
    with pytest.raises(config.ErrorConfig) as e:
        _config(exam_id="x", variants=["1"], grade_map={"curve_k": 99})
    assert len(e.value.problemas) == 3


def test_el_ejemplo_de_la_spec_es_valido():
    c = _config()
    assert c.puntaje_total == 10.0 and c.rubric[0].etiquetas() == ["0", "25", "50", "75", "100"]
    assert c.rubric[2].etiquetas() == ["✗", "✓"]


# --- §4 Manifiesto ------------------------------------------------------------------------------------

def test_el_manifiesto_reproduce_el_ejemplo_de_la_spec_y_pasa_el_esquema():
    m = layout.construir(_config())
    assert layout.problemas(m) == []
    assert m["schema"] == "omr-layout/2" and m["frame_mm"] == {"w": 180.0, "h": 74.0}
    assert (m["marker_mm"], m["px_per_mm"], m["bubble_diameter_mm"]) == (10.0, 10, 5.0)
    ej1 = m["fields"][0]
    assert [(o["step"], o["label"], o["x_mm"], o["y_mm"]) for o in ej1["options"]] == [
        (0, "0", 32.0, 12.0), (1, "25", 40.0, 12.0), (2, "50", 48.0, 12.0), (3, "75", 56.0, 12.0), (4, "100", 64.0, 12.0)]
    assert [f["options"][0]["y_mm"] for f in m["fields"][:5]] == [12.0, 20.0, 28.0, 36.0, 44.0]
    nota = m["fields"][5]
    assert nota["role"] == "final_grade" and nota["digits"] == [
        {"place": 1.0, "start": 1, "count": 10, "x0_mm": 32.0, "y0_mm": 56.0, "step_mm": 8.0, "axis": "x"},
        {"place": 0.1, "start": 0, "count": 10, "x0_mm": 32.0, "y0_mm": 64.0, "step_mm": 8.0, "axis": "x"}]
    assert m["fields"][6] == {"id": "ausente", "label": "Ausente", "type": "flag", "required": False,
                              "x_mm": 162.0, "y_mm": 64.0}


@pytest.mark.parametrize("escala, filas", [
    ({"decimals": 0}, [(1.0, 1, 10, None)]),
    ({"decimals": 0, "step": 0.5}, [(1.0, 1, 10, None), (0.1, 0, 2, [0, 5])]),
    ({"decimals": 1}, [(1.0, 1, 10, None), (0.1, 0, 10, None)]),
    ({"decimals": 2}, [(1.0, 1, 10, None), (0.1, 0, 10, None), (0.01, 0, 10, None)]),
])
def test_filas_de_la_nota_segun_la_escala(escala, filas):
    m = layout.construir(_config(grade_scale=escala))
    assert layout.problemas(m) == []
    assert [(d["place"], d["start"], d["count"], d.get("values")) for d in m["fields"][-2]["digits"]] == filas


def test_el_alto_del_marco_tiene_un_minimo_de_55():
    m = layout.construir(_config(rubric=[{"id": "e", "max_points": 1, "levels": 2}], grade_scale={"decimals": 0}))
    assert m["frame_mm"]["h"] == 55.0 and m["fields"][-1]["y_mm"] == 24.0


@pytest.mark.parametrize("romper, mensaje", [
    (lambda m: m["grade_map"].update(pass_pct=80.0), "grade_map/pass_pct"),
    (lambda m: m.update(schema="omr-layout/1"), "schema"),
    (lambda m: m["fields"][0]["options"][0].update(x_mm=-1.0), "sale del marco"),
    (lambda m: m["fields"][1].update(id="ej1"), "ids repetidos"),
])
def test_un_manifiesto_roto_no_pasa(romper, mensaje):
    m = layout.construir(_config())
    romper(m)
    assert any(mensaje in p for p in layout.problemas(m))


# --- §5 Notas ----------------------------------------------------------------------------------------

def test_puntaje_y_porcentaje_sin_redondeo_intermedio():
    c = _config()
    assert notas.puntaje(1, 5, 2.5) == 0.625
    assert notas.porcentaje(c, {"ej1": 4, "ej2": 4, "ej3": 1, "ej4": 4, "ej5": 10}) == 100.0
    assert notas.porcentaje(c, {"ej1": 1}) == pytest.approx(6.25)


def test_la_tabla_de_verificacion():
    c = _config()
    tabla = {p: (g, cond) for p, g, cond in notas.tabla_verificacion(c)}
    assert list(tabla) == [0.0, 30.0, 59.9, 60.0, 70.0, 79.9, 80.0, 90.0, 100.0]
    assert tabla[0.0] == (1.0, notas.DESAPROBADO) and tabla[100.0] == (10.0, notas.PROMOCIONADO)
    assert tabla[59.9] == (3.9, notas.DESAPROBADO)          # 3,99 redondea a 4,0: se recorta
    assert tabla[60.0] == (4.0, notas.APROBADO)
    assert tabla[79.9] == (6.9, notas.APROBADO)             # no cruza la promoción
    assert tabla[80.0] == (7.0, notas.PROMOCIONADO)
    assert tabla[70.0][0] == 6.0                             # k = 3: ln(1 + 1,5) / ln(4) del tramo


@pytest.mark.parametrize("k, esperado", [(0.0, 5.5), (3.0, 4 + 3 * 0.660964), (-3.0, 4 + 3 * (4 ** 0.5 - 1) / 3)])
def test_la_forma_de_la_curva(k, esperado):
    c = _config(grade_map={"curve_k": k})
    assert notas.nota_continua(70.0, c.grade_map, c.grade_scale) == pytest.approx(esperado, abs=1e-5)


def test_sin_decimales_no_cruza_el_umbral_y_medio_punto():
    c = _config(grade_scale={"decimals": 0})
    assert notas.nota(59.9, c) == 3.0
    m = _config(grade_scale={"decimals": 0, "step": 0.5})
    assert notas.nota(59.9, m) == 3.5 and notas.redondear(6.74, m.grade_scale) == 6.5


def test_half_even_y_half_up():
    arriba, par = _config().grade_scale, _config(grade_scale={"rounding": "half_even"}).grade_scale
    assert notas.redondear(6.25, arriba) == 6.3 and notas.redondear(6.25, par) == 6.2


def test_sin_promocion_y_ausente():
    c = _config(grade_map={"promo_pct": None, "promo_grade": None})
    assert notas.condicion(95.0, c.grade_map) == notas.APROBADO
    assert notas.condicion(95.0, c.grade_map, ausente=True) == notas.AUSENTE
    assert notas.puntos_de_verificacion(c.grade_map) == [0.0, 30.0, 59.9, 60.0, 80.0, 100.0]


def test_tolerancia_entre_marcada_y_calculada():
    estricta, flexible = _config().grade_scale, _config(grade_scale={"match_tolerance": 1}).grade_scale
    assert not notas.coincide(6.1, 6.0, estricta) and notas.coincide(6.1, 6.0, flexible)


# --- §6 QR -------------------------------------------------------------------------------------------

def test_hmac_key_y_chk():
    clave = qr.nueva_clave()
    assert qr.clave_valida(clave) and clave != qr.nueva_clave()
    contenido = qr.contenido_caratula(_config(), "C017", "A", clave)
    assert contenido.startswith("1/PROG1-2026-P1/C017/A/OMR5E:7/") and len(contenido.rpartition("/")[2]) == 4
    assert qr.verificar_caratula(contenido, clave)
    assert not qr.verificar_caratula(contenido.replace("C017", "C018"), clave)
    assert not qr.verificar_caratula(contenido, qr.nueva_clave())


def test_el_qr_de_la_caratula_es_3q_alfanumerico():
    codigo = qr.qr_caratula(qr.contenido_caratula(_config(), "C017", "A", qr.nueva_clave()))
    assert (codigo.version, codigo.error, codigo.mode) == (3, "Q", "alphanumeric")
    with pytest.raises(ValueError):
        qr.qr_caratula("minúsculas/no")


def test_qr_compacto_y_comprimido():
    c = _config(rubric=[{"id": "ej1", "label": "Ejercicio 1", "max_points": 2.5, "levels": 5}],
                grade_map={"promo_pct": None, "promo_grade": None})
    clave = "A" * 26
    assert qr.config_compacta(c, clave) == ("OMRCFG/2/PROG1-2026-P1/OMR5E:7/" + clave + "/60:NONE:0:3/1::0/"
                                            "ej1:2.5:5:Ejercicio+1/Programaci%C3%B3n+I+%E2%80%94+Parcial+1")
    m = layout.construir(c)
    sobre = qr.leer_config_comprimida(qr.config_comprimida(c, clave, m))
    assert sobre == {"schema": "omr-exam-config/2", "exam_id": "PROG1-2026-P1", "title": c.title,
                     "hmac_key": clave, "cloud_sync": False, "manifest": m}


def test_el_compacto_no_alcanza_con_etiquetas_propias_o_otra_escala():
    assert "etiquetas propias" in qr.motivos_sin_compacto(_config())[0]
    sin = _config(rubric=EJEMPLO["rubric"][:2], grade_scale={"rounding": "half_even"})
    assert qr.motivos_sin_compacto(sin) == ["el redondeo es half_even"]
    with pytest.raises(ValueError):
        qr.config_compacta(_config(), "A" * 26)


# --- §3.2 Nómina -------------------------------------------------------------------------------------

def _filas(*filas):
    return [dict(zip(("legajo", "apellido", "nombre", "student_id", "variante"), f, strict=False)) for f in filas]


def test_asigna_ids_libres_y_variantes_en_ronda():
    filas = _filas(("1", "A", "a"), ("2", "B", "b", "C001"), ("3", "C", "c", "", "B"), ("4", "D", "d"))
    inscriptos = nomina.asignar("n.csv", filas, {"legajo", "apellido", "nombre", "student_id", "variante"}, ("A", "B"))
    assert [(i.student_id, i.variante) for i in inscriptos] == [("C002", "A"), ("C001", "B"), ("C003", "B"),
                                                                 ("C004", "A")]


@pytest.mark.parametrize("filas, mensaje", [
    (_filas(("1", "A", "a", "C-1")), "student_id 'C-1'"),
    (_filas(("1", "A", "a", "X1"), ("2", "B", "b", "X1")), "X1 repetido"),
    (_filas(("1", "A", "a"), ("1", "B", "b")), "legajo 1 repetido"),
    (_filas(("1", "A", "a", "", "Z")), "variante Z"),
    (_filas(("1", "", "a")), "falta el apellido"),
])
def test_nomina_invalida(filas, mensaje):
    with pytest.raises(nomina.ErrorNomina) as e:
        nomina.asignar("n.csv", filas, {"legajo", "apellido", "nombre", "student_id", "variante"}, ("A", "B"))
    assert any(mensaje in p for p in e.value.problemas)


# --- §8 Lote y §11 aceptación ----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def proyecto(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("omr")
    (raiz / "banco").mkdir()
    preguntas = [f"// [tag, {e['id']}]\n::{e['id']}_v{v}::Consigna {e['id']} versión {v}. {{}}\n"
                 for e in EJEMPLO["rubric"] for v in range(2)]
    (raiz / "banco" / "practica.gift").write_text("\n".join(preguntas), encoding="utf-8")
    (raiz / "exam.yaml").write_text(json.dumps(EJEMPLO, ensure_ascii=False), encoding="utf-8")
    (raiz / "inscriptos.csv").write_text("legajo,apellido,nombre\n1001,Pérez,Ana\n1002,Gómez,Luis\n"
                                         "1003,Núñez,Sofía\n", encoding="utf-8")
    return raiz


def _cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["alucard", *argv])
    return main()


@pytest.fixture(scope="module")
def lote(proyecto):
    salida = proyecto / "dist"
    mp = pytest.MonkeyPatch()
    try:
        assert _cli(mp, "omr", "build", "--config", str(proyecto / "exam.yaml"), "--roster",
                    str(proyecto / "inscriptos.csv"), "--questions", str(proyecto / "banco"),
                    "--out", str(salida)) == 0
    finally:
        mp.undo()
    return salida


def test_el_lote_tiene_todos_los_artefactos(lote):
    nombres = {p.name for p in lote.iterdir()}
    assert {"examenes_PROG1-2026-P1.pdf", "roster_PROG1-2026-P1.csv", "layout_OMR5E_v7.json",
            "layout_OMR5E_v7.sha256", "config_qr_PROG1-2026-P1.pdf", "config_qr_PROG1-2026-P1.svg",
            "layout_test_OMR5E.pdf", "build_PROG1-2026-P1.log", ".gitignore", ".hmac_key"} <= nombres
    assert ".omr" not in nombres
    assert (lote / "roster_PROG1-2026-P1.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    with (lote / "roster_PROG1-2026-P1.csv").open(encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    assert [(r["student_id"], r["variante"]) for r in filas] == [("C001", "A"), ("C002", "B"), ("C003", "A")]
    assert "roster_*.csv" in (lote / ".gitignore").read_text() and ".hmac_key" in (lote / ".gitignore").read_text()
    huella = (lote / "layout_OMR5E_v7.sha256").read_text().split()[0]
    assert huella in (lote / "build_PROG1-2026-P1.log").read_text()
    m = json.loads((lote / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    assert m == layout.construir(_config()) and layout.problemas(m) == []


def test_cada_examen_ocupa_paginas_pares_en_a4(lote):
    import pypdf

    lector = pypdf.PdfReader(str(lote / "examenes_PROG1-2026-P1.pdf"))
    assert len(lector.pages) % 2 == 0 and len(lector.pages) >= 6
    pagina = lector.pages[0]
    assert (round(float(pagina.mediabox.width)), round(float(pagina.mediabox.height))) == (595, 842)
    texto = pagina.extract_text()
    assert "Pérez, Ana" in texto and "C001" in texto and "VARIANTE A" in texto
    assert "Zona reservada para el docente" in texto


@CON_POPPLER
def test_las_burbujas_quedan_a_menos_de_03_mm(lote):
    m = json.loads((lote / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    paginas = geometria.verificar(lote / "examenes_PROG1-2026-P1.pdf", m, [])
    assert [p.numero for p in paginas] == [1, 3, 5]          # una carátula por estudiante, en página impar
    for p in paginas:
        assert p.ok, p.problemas
        assert [x.id for x in p.marcadores] == [0, 1, 2, 3] and all(x.rotacion == 0 for x in p.marcadores)
        assert len(p.mediciones) == len(layout.burbujas(m)) and p.error_maximo < 0.3


@CON_POPPLER
def test_verify_geometry_detecta_una_burbuja_corrida(lote, tmp_path):
    m = json.loads((lote / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    m["fields"][0]["options"][2]["x_mm"] += 0.5
    pagina = geometria.verificar(lote / "examenes_PROG1-2026-P1.pdf", m)[0]
    assert not pagina.ok and any("ej1=2" in p for p in pagina.problemas)


@CON_POPPLER
def test_los_qr_se_decodifican_y_pasan_el_chk(lote):
    zxingcpp = pytest.importorskip("zxingcpp")
    clave = (lote / ".hmac_key").read_text().strip().partition(":")[2]
    pdf = lote / "examenes_PROG1-2026-P1.pdf"
    caratula = [c.text for c in zxingcpp.read_barcodes(geometria.rasterizar(pdf, 1))]
    assert len(caratula) == 1 and len(caratula[0]) <= 47
    assert caratula[0].startswith("1/PROG1-2026-P1/C001/A/OMR5E:7/") and qr.verificar_caratula(caratula[0], clave)
    pie = [c.text for c in zxingcpp.read_barcodes(geometria.rasterizar(pdf, 2))]
    assert pie == ["PROG1-2026-P1/C001/P2"]
    hoja = [c.text for c in zxingcpp.read_barcodes(geometria.rasterizar(lote / "config_qr_PROG1-2026-P1.pdf", 1))]
    sobre = qr.leer_config_comprimida(next(t for t in hoja if t.startswith("OMRCFG2:")))
    assert sobre["hmac_key"] == clave
    assert sobre["manifest"] == json.loads((lote / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))


@CON_POPPLER
def test_la_hoja_de_calibracion_tiene_la_cabecera(lote):
    m = json.loads((lote / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    pagina = geometria.verificar_pagina(geometria.rasterizar(lote / "layout_test_OMR5E.pdf", 1), m)
    assert [x.id for x in pagina.marcadores] == [0, 1, 2, 3]


def test_regenerar_conserva_la_clave_salvo_nueva_clave(proyecto, lote, tmp_path):
    from generador_examenes.omr.lote import clave_del_examen

    c = config.cargar(proyecto / "exam.yaml")
    copia = tmp_path / "dist"
    shutil.copytree(lote, copia)
    antes = (copia / ".hmac_key").read_text()
    assert clave_del_examen(copia, c) == antes.strip().partition(":")[2]
    assert clave_del_examen(copia, c, nueva=True) != antes.strip().partition(":")[2]


# --- CLI ---------------------------------------------------------------------------------------------

def test_validate_y_preview_curve(proyecto, monkeypatch, capsys):
    assert _cli(monkeypatch, "omr", "validate", "--config", str(proyecto / "exam.yaml"), "--roster",
                str(proyecto / "inscriptos.csv")) == 0
    assert "3 inscripto(s)" in capsys.readouterr().out
    assert _cli(monkeypatch, "omr", "preview-curve", "--config", str(proyecto / "exam.yaml")) == 0
    assert "59.9%     3,9  DESAPROBADO" in capsys.readouterr().out


def test_validate_sale_con_1_y_lista_los_problemas(tmp_path, monkeypatch, capsys):
    malo = tmp_path / "exam.json"
    malo.write_text(json.dumps({**EJEMPLO, "exam_id": "mal", "grade_map": {**EJEMPLO["grade_map"], "pass_pct": 90}}),
                    encoding="utf-8")
    assert _cli(monkeypatch, "omr", "validate", "--config", str(malo)) == 1
    err = capsys.readouterr().err
    assert "exam_id: 'mal'" in err and "pass_pct: 90" in err


def test_build_compacto_con_etiquetas_propias_falla(proyecto, tmp_path, monkeypatch, capsys):
    assert _cli(monkeypatch, "omr", "build", "--config", str(proyecto / "exam.yaml"), "--roster",
                str(proyecto / "inscriptos.csv"), "--questions", str(proyecto / "banco"), "--out",
                str(tmp_path / "x"), "--qr-config-mode", "compact") == 1
    assert "etiquetas propias" in capsys.readouterr().err


def test_build_sin_preguntas_para_un_ejercicio_falla(proyecto, tmp_path, monkeypatch, capsys):
    otra = tmp_path / "exam.json"
    rubrica = EJEMPLO["rubric"] + [{"id": "ej9", "label": "Sin consigna", "max_points": 1, "levels": 2}]
    otra.write_text(json.dumps({**EJEMPLO, "rubric": rubrica}, ensure_ascii=False), encoding="utf-8")
    assert _cli(monkeypatch, "omr", "build", "--config", str(otra), "--roster", str(proyecto / "inscriptos.csv"),
                "--questions", str(proyecto / "banco"), "--out", str(tmp_path / "x")) == 1
    assert "ej9" in capsys.readouterr().err


@CON_POPPLER
def test_cli_verify_geometry_y_calibration_sheet(lote, tmp_path, monkeypatch, capsys):
    manifiesto = str(lote / "layout_OMR5E_v7.json")
    assert _cli(monkeypatch, "omr", "verify-geometry", "--pdf", str(lote / "examenes_PROG1-2026-P1.pdf"),
                "--manifest", manifiesto, "--json") == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    destino = tmp_path / "cal.pdf"
    assert _cli(monkeypatch, "omr", "calibration-sheet", "--manifest", manifiesto, "--out", str(destino)) == 0
    assert destino.stat().st_size > 0 and not (lote / ".omr").exists()


# --- Modo planilla: las notas en una planilla docente, no en las hojas de los estudiantes ------------------

@pytest.fixture(scope="module")
def planilla(proyecto):
    salida = proyecto / "dist_planilla"
    mp = pytest.MonkeyPatch()
    try:
        assert _cli(mp, "omr", "build", "--config", str(proyecto / "exam.yaml"), "--roster",
                    str(proyecto / "inscriptos.csv"), "--questions", str(proyecto / "banco"),
                    "--out", str(salida), "--modo", "planilla") == 0
    finally:
        mp.undo()
    return salida


def test_en_modo_planilla_los_examenes_no_llevan_franja(planilla):
    import pypdf

    assert (planilla / "planilla_PROG1-2026-P1.pdf").is_file()
    assert "planilla_*.pdf" in (planilla / ".gitignore").read_text()
    lector = pypdf.PdfReader(str(planilla / "examenes_PROG1-2026-P1.pdf"))
    assert len(lector.pages) % 2 == 0
    texto = lector.pages[0].extract_text()
    assert "Pérez, Ana" in texto and "VARIANTE A" in texto and "Zona reservada" not in texto
    assert "notas en la planilla docente" in (planilla / "build_PROG1-2026-P1.log").read_text()


@CON_POPPLER
def test_los_examenes_del_modo_planilla_no_tienen_marcadores(planilla):
    m = json.loads((planilla / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    assert geometria.verificar(planilla / "examenes_PROG1-2026-P1.pdf", m, []) == []


@CON_POPPLER
def test_la_planilla_tiene_un_marco_por_estudiante_y_cada_uno_es_exacto(planilla):
    m = json.loads((planilla / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    from generador_examenes.omr.lote import marcos_por_hoja

    assert marcos_por_hoja(m) == 2                          # el marco de la SPEC mide 74 mm
    marcos = geometria.verificar(planilla / "planilla_PROG1-2026-P1.pdf", m, [])
    assert [(p.numero, p.marco) for p in marcos] == [(1, 1), (1, 2), (2, 0)]
    for p in marcos:
        assert p.ok, p.problemas
        assert len(p.mediciones) == len(layout.burbujas(m)) and p.error_maximo < 0.3


@CON_POPPLER
def test_los_qr_de_la_planilla_son_los_de_la_caratula(planilla):
    zxingcpp = pytest.importorskip("zxingcpp")
    clave = (planilla / ".hmac_key").read_text().strip().partition(":")[2]
    pdf = planilla / "planilla_PROG1-2026-P1.pdf"
    leidos = sorted(c.text for n in (1, 2) for c in zxingcpp.read_barcodes(geometria.rasterizar(pdf, n)))
    assert [t.split("/")[2:4] for t in leidos] == [["C001", "A"], ["C002", "B"], ["C003", "A"]]
    assert all(qr.verificar_caratula(t, clave) for t in leidos)


def test_marcos_por_hoja_y_posiciones():
    from generador_examenes.omr import lote

    m = layout.construir(_config())
    entran = lote.marcos_por_hoja(m)
    assert entran >= 2 and lote.marcos_por_hoja(m, 1) == 1 and lote.marcos_por_hoja(m, 99) == entran
    posiciones = lote.posiciones_planilla(m, entran + 1)
    assert posiciones[0] == (1, lote.OY) and posiciones[-1] == (2, lote.OY)
    alto = m["frame_mm"]["h"]
    assert all(oy + alto <= lote.LIMITE_PLANILLA for _, oy in posiciones)
    assert all(b - a >= alto + m["marker_mm"] + lote.SEPARACION_PLANILLA
               for (_, a), (_, b) in zip(posiciones, posiciones[1:entran], strict=False))


@CON_POPPLER
def test_por_hoja_reparte_los_marcos(proyecto, tmp_path, monkeypatch):
    salida = tmp_path / "dist"
    assert _cli(monkeypatch, "omr", "build", "--config", str(proyecto / "exam.yaml"), "--roster",
                str(proyecto / "inscriptos.csv"), "--questions", str(proyecto / "banco"), "--out", str(salida),
                "--modo", "planilla", "--por-hoja", "1") == 0
    m = json.loads((salida / "layout_OMR5E_v7.json").read_text(encoding="utf-8"))
    marcos = geometria.verificar(salida / "planilla_PROG1-2026-P1.pdf", m, [])
    assert [(p.numero, p.marco) for p in marcos] == [(1, 0), (2, 0), (3, 0)] and all(p.ok for p in marcos)


@pytest.mark.parametrize("argumentos, mensaje", [
    (["--modo", "hoja"], "--modo"),
    (["--por-hoja", "2"], "--por-hoja sólo"),
])
def test_opciones_del_modo_invalidas(proyecto, tmp_path, monkeypatch, capsys, argumentos, mensaje):
    with pytest.raises(SystemExit) as salida:
        _cli(monkeypatch, "omr", "build", "--config", str(proyecto / "exam.yaml"), "--roster",
             str(proyecto / "inscriptos.csv"), "--out", str(tmp_path / "d"), *argumentos)
    salidas = capsys.readouterr()
    assert salida.value.code == 2 and mensaje in salidas.out + salidas.err
