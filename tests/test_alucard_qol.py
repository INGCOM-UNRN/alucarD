import pytest
from pathlib import Path
from generador_examenes.core.alucard_qol import (
    generar_plantilla_omr,
    generar_especificacion_omr_json,
    verificar_alineacion_doble_faz,
    formatear_caja_codigo_con_lineas,
    auditar_calidad_tipografica_codigo,
    verificar_balance_preguntas_entre_temas,
    empaquetar_pdfs_para_imprenta,
)


def test_generar_plantilla_omr():
    typ = generar_plantilla_omr(num_preguntas=10, opciones_por_pregunta=5, tema=2)
    assert "HOJA DE RESPUESTAS OMR" in typ
    assert "TEMA 2" in typ
    assert "circle" in typ
    assert "P10" in typ


def test_generar_especificacion_omr_json():
    spec = generar_especificacion_omr_json(num_preguntas=5, opciones_por_pregunta=4, tema=1)
    assert spec["schema_version"] == "1.0-omr"
    assert spec["total_preguntas"] == 5
    assert len(spec["preguntas"]) == 5
    assert spec["preguntas"][0]["opciones"] == ["A", "B", "C", "D"]
    assert "A" in spec["preguntas"][0]["coordenadas"]
    assert len(spec["fiducial_markers"]) == 4


def test_verificar_alineacion_doble_faz():
    res_par = verificar_alineacion_doble_faz(4)
    assert res_par["es_par"] is True
    assert res_par["requiere_pagina_blanco"] is False
    assert res_par["paginas_impresion"] == 4

    res_impar = verificar_alineacion_doble_faz(3)
    assert res_impar["es_par"] is False
    assert res_impar["requiere_pagina_blanco"] is True
    assert res_impar["paginas_impresion"] == 4
    assert "impar" in res_impar["advertencia"]


def test_formatear_caja_codigo_con_lineas():
    codigo = "int x = 10;\nprintf(\"%d\", x);\nreturn 0;"
    box = formatear_caja_codigo_con_lineas(codigo)
    assert "```c" in box
    assert "int x = 10;" in box
    assert "printf" in box
    assert "return 0;" in box


def test_auditar_calidad_tipografica_codigo():
    codigo_ok = "int a = 1;\nint b = 2;\nreturn a + b;"
    aud_ok = auditar_calidad_tipografica_codigo(codigo_ok, max_cols=40)
    assert aud_ok["cumple_calidad"] is True
    assert len(aud_ok["lineas_largas"]) == 0

    codigo_largo = "char *muy_largo = \"Este es un string extraordinariamente largo que va a superar el limite de columnas\";"
    aud_bad = auditar_calidad_tipografica_codigo(codigo_largo, max_cols=30)
    assert aud_bad["cumple_calidad"] is False
    assert len(aud_bad["lineas_largas"]) == 1


def test_verificar_balance_preguntas_entre_temas():
    tema1 = {"preguntas": [{"puntaje": 2.0}, {"puntaje": 3.0}]}
    tema2 = {"preguntas": [{"puntaje": 2.5}, {"puntaje": 2.5}]}
    bal = verificar_balance_preguntas_entre_temas([tema1, tema2])
    assert bal["balanceado"] is True
    assert bal["balance_cantidad"] is True
    assert bal["balance_puntaje"] is True

    tema3 = {"preguntas": [{"puntaje": 1.0}]}
    desbal = verificar_balance_preguntas_entre_temas([tema1, tema3])
    assert desbal["balanceado"] is False
    assert len(desbal["discrepancias"]) > 0


def test_empaquetar_pdfs_para_imprenta(tmp_path):
    import pypdf
    # Crear dos PDFs ficticios válidos
    pdf1_path = tmp_path / "t1.pdf"
    pdf2_path = tmp_path / "t2.pdf"
    
    writer1 = pypdf.PdfWriter()
    writer1.add_blank_page(width=100, height=100)
    with open(pdf1_path, "wb") as f:
        writer1.write(f)
        
    writer2 = pypdf.PdfWriter()
    writer2.add_blank_page(width=100, height=100)
    with open(pdf2_path, "wb") as f:
        writer2.write(f)
        
    salida = tmp_path / "imprenta_total.pdf"
    res = empaquetar_pdfs_para_imprenta([pdf1_path, pdf2_path], salida, doble_faz=True)
    assert res.exists()
    reader = pypdf.PdfReader(str(salida))
    # Como ambos tenían 1 página (impar), se les agrega 1 página en blanco a cada uno -> total 4
    assert len(reader.pages) == 4
