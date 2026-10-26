# -*- coding: utf-8 -*-
"""S160 (V3-01 de docs/AUDIT_S160.md): una alerta protegida de MIROVA en una pasada de la que no tenemos
ningun record es un aviso de COBERTURA del auto-audit.

POR QUE: el 2026-11-02 Suomi NPP deja de entregar datos. Cuando una plataforma se calla, las otras siguen
dando datos ese dia, asi que la guarda de cobertura por dias (S124/S150) no se entera, y flags_protegidas
solo mira `sin_publicar`. Una protegida `sin_record` quedaba en el JSON sin que nada la dijera
(experiments/_s160_audit/v3/v3_protegida_sin_record.py). S150 separo `sin_record` de `sin_publicar` porque
«no miramos» no es «no vimos»: por eso esto no es un flag de recall sino un aviso de cobertura, que deja el
veredicto en DEGRADADO (no sabemos si la ventana es interpretable) y no lo cuenta como perdida de deteccion.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402


def _p(estado, detector="K", vol="Lascar", sensor="VIIRS375", fecha="2026-11-05T05:00", vrp=2.5):
    return {"volcano": vol, "sensor": sensor, "fecha_utc": fecha, "vrp_mirova_mw": vrp,
            "detector": detector, "estado": estado, "detector_records": [],
            "noche_publicada_otra_pasada": False, "referencia_sospechosa": False}


def test_protegida_sin_record_del_detector_vigente_da_aviso():
    avisos = aa.avisos_protegidas_sin_record([_p("sin_record")], "K")
    assert len(avisos) == 1
    assert "Lascar VIIRS375 2026-11-05T05:00" in avisos[0] and "2.5" in avisos[0]
    assert "sin record" in avisos[0]


def test_publicada_y_sin_publicar_no_son_avisos_de_cobertura():
    lista = [_p("publicada"), _p("sin_publicar")]
    assert aa.avisos_protegidas_sin_record(lista, "K") == []
    # y sin_record no entra a los flags de deteccion (decision S150: no miramos no es no vimos)
    assert aa.flags_protegidas([_p("sin_record")], "K") == []


def test_sin_record_de_otro_detector_no_avisa():
    assert aa.avisos_protegidas_sin_record([_p("sin_record", detector="C0")], "K") == []


def test_main_lleva_el_aviso_a_la_cobertura():
    """El aviso tiene que llegar a cobertura_avisos (que decide DEGRADADO), no quedarse en una funcion
    que nadie llama: se busca la llamada con frontera de palabra (A92), no por subcadena."""
    import re
    src = (ROOT / "scripts" / "auto_audit_weekly.py").read_text(encoding="utf-8")
    cuerpo_main = src[src.index("def main():"):]
    assert re.search(r"(?<![A-Za-z0-9_])avisos_protegidas_sin_record\s*\(\s*protegidas\s*,\s*vigente\s*\)",
                     cuerpo_main)
    assert re.search(r"cobertura_avisos\s*(\+=|\.extend\()", cuerpo_main)
