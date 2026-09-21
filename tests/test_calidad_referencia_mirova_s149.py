"""A119 (S149): el cargador de la referencia avisa cuando la ventana pisa un tramo defectuoso.

POR QUE EXISTE. La calidad de los CSV del scraper por mes se midio en S139 y en S149 se eligio una ventana
de A/B sin mirarla, porque vivia solo en un informe. Estos tests fijan lo que importa: septiembre no
avisa, mayo avisa del OCR mal calibrado y sin distancia, enero avisa de todo, y el aviso de verdad sale
cuando se indexa la referencia (no solo cuando alguien se acuerda de llamarlo).
"""
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import calidad_referencia_mirova as cal  # noqa: E402


def test_septiembre_no_pisa_nada():
    assert cal.avisos_de_ventana("2026-09-01", "2026-09-20") == []
    assert cal.etiqueta_que_decide("2026-09-01") == "tabla y OCR"


def test_mayo_avisa_del_ocr_y_decide_solo_la_tabla():
    av = " ".join(cal.avisos_de_ventana("2026-05-01", "2026-05-31"))
    assert "2026-06-11" in av and "2026-06-13" in av and "2026-03-01" not in av
    assert cal.etiqueta_que_decide("2026-05-01").startswith("SOLO la tabla")


def test_marzo_avisa_de_la_tasa_por_pasada_de_viirs():
    av = " ".join(cal.avisos_de_ventana("2026-03-01", "2026-03-31"))
    assert "2026-04-01" in av and "cobertura nocturna" not in av


def test_enero_avisa_de_todo():
    assert len(cal.avisos_de_ventana("2026-01-10", "2026-01-31")) == len(cal.HITOS)


def test_el_documento_fuente_existe():
    assert os.path.exists(os.path.join(RAIZ, "docs", "audit_s139", "MAPA_BASES_MIROVA_V1.md"))


def test_indexar_la_referencia_dispara_el_aviso(capsys):
    import banco_paridad as bp
    bp.indexar_referencia([], {}, ("2026-05-01", "2026-05-31"))
    assert "[referencia MIROVA]" in capsys.readouterr().err
    bp.indexar_referencia([], {}, ("2026-09-01", "2026-09-20"))
    assert "[referencia MIROVA]" not in capsys.readouterr().err
