# -*- coding: utf-8 -*-
"""S166 (issue #915, clasificado en experiments/_s165_issue915/INFORME.md de la rama loop/activo): el
auto-audit deja de levantar flags por artefactos de la referencia y por una pérdida ya decidida.

POR QUÉ: el audit semanal abrió #915 «FUERA DE BANDA» con tres alertas protegidas «sin publicar». La
clasificación de S165 mostró que ninguna era una pérdida de cráter que el operador no viera. Un audit que
se dispara cada semana por eso confunde más de lo que ayuda (decisión de Nicolás, 2026-10-28). Dos cambios:

1. protegida con `referencia_sospechosa` (sólo OCR de Suomi NPP antes del hito A119): no levanta flag, se
   informa aparte;
2. pérdida aceptada: PCC VIIRS 750 2026-10-10 05:54 (#865, #881), y ninguna otra pasada.

Cada cambio tiene un control: la protegida normal (tabla, NOAA-20 o posterior al hito, o cualquier otra
pasada) sigue siendo flag. El cambio no puede apagar el audit entero. (Un tercer cambio, sacar de la
mediana de magnitud las noches que comparan otro objeto, se probó y se retiró del PR #924: con
inner_radius_km no corrige PCC y la regla de Suomi NPP borraba una bandera real de Chillán.)
"""
import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"
WIN = ("2026-08-27", "2026-10-26")


# ------------------------------------------------------------------ ayudas
def _fila(vol, b, fecha, vrp, source="CONS", tipo=None, dist=None):
    tipo = tipo or ("ALERTA_TERMICA_OCR" if source == "OCR" else "ALERTA_TERMICA")
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo,
            "source": source, "dist_km": dist}


def _brec(vol, b, fecha, pub, sensor, sha="abc"):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": pub, "sha": sha, "sensor": sensor}


def _protegidas(filas, recs):
    return aa.alertas_protegidas(filas, recs, WIN, FRONTERA, diurna=lambda *a: False)


# ------------------------------------------------------------------ 1. referencia sospechosa
def test_protegida_con_referencia_sospechosa_no_es_flag_y_se_informa_aparte():
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR")]
    recs = [_brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", False, "VIIRS_SNPP")]
    lista = _protegidas(filas, recs)
    assert [(p["estado"], p["referencia_sospechosa"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == []
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1
    assert "Tupungatito VIIRS375 2026-09-28 05:18" in aparte[0] and "2.51" in aparte[0]
    assert "referencia sospechosa" in aparte[0] and aa.HITO_OCR_SUOMI_NPP in aparte[0]


@pytest.mark.parametrize("fila,sensor", [
    # control: de la tabla (CONS), aunque sea Suomi NPP y antes del hito
    (_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="CONS"), "VIIRS_SNPP"),
    # control: sólo OCR antes del hito, pero de NOAA-20
    (_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR"), "VIIRS_NOAA20"),
    # control: sólo OCR de Suomi NPP, pero posterior al hito
    (_fila("Tupungatito", "VIIRS375", "2026-10-12 05:18:00", 2.51, source="OCR"), "VIIRS_SNPP"),
])
def test_protegida_normal_sigue_siendo_flag(fila, sensor):
    recs = [_brec("Tupungatito", "VIIRS375", fila["fecha_utc"][:16], False, sensor)]
    lista = _protegidas([fila], recs)
    assert lista[0]["referencia_sospechosa"] is False
    flags = aa.flags_protegidas(lista, "K")
    assert len(flags) == 1 and flags[0].startswith("alerta protegida sin publicar: Tupungatito VIIRS375")
    assert aa.protegidas_aparte(lista, "K") == []


def test_aparte_solo_del_detector_vigente_y_solo_sin_publicar():
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-10 05:18:00", 2.0, source="OCR"),   # C0
             _fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.5, source="OCR")]   # K, publicada
    recs = [_brec("Tupungatito", "VIIRS375", "2026-09-10 05:18", False, "VIIRS_SNPP", sha=None),
            _brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", True, "VIIRS_SNPP")]
    lista = _protegidas(filas, recs)
    assert aa.protegidas_aparte(lista, "K") == []
    assert aa.flags_protegidas(lista, "K") == []


# ------------------------------------------------------------------ 3. pérdida aceptada
def test_el_registro_de_perdidas_aceptadas_tiene_una_sola_pasada():
    assert set(aa.PERDIDAS_ACEPTADAS) == {("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")}
    motivo = aa.PERDIDAS_ACEPTADAS[("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")]
    assert "#865" in motivo and "#881" in motivo


def test_la_perdida_aceptada_no_es_flag_y_se_informa_como_aceptada():
    filas = [_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:00", 1.19, dist=7.83)]
    recs = [_brec("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", False, "VIIRS_NOAA20_750"),
            _brec("PuyehueCordonCaulle", "VIIRS375", "2026-10-10 05:54", True, "VIIRS_NOAA21")]
    lista = _protegidas(filas, recs)
    assert [(p["estado"], p["perdida_aceptada"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == []
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1
    assert "pérdida aceptada" in aparte[0] and "PuyehueCordonCaulle VIIRS750 2026-10-10 05:54" in aparte[0]
    assert "#865" in aparte[0]


@pytest.mark.parametrize("vol,b,fecha,sensor", [
    ("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 04:54:00", "VIIRS_SNPP_750"),   # otra pasada de esa noche
    ("PuyehueCordonCaulle", "VIIRS750", "2026-10-11 05:54:00", "VIIRS_NOAA20_750"),  # otra noche, misma hora
    ("PuyehueCordonCaulle", "VIIRS375", "2026-10-10 05:54:00", "VIIRS_NOAA21"),      # mismo minuto, otro sensor
    ("NevadosDeChillan", "VIIRS750", "2026-10-10 05:54:00", "VIIRS_NOAA20_750"),     # mismo minuto, otro volcán
])
def test_el_registro_no_acepta_ninguna_otra_pasada(vol, b, fecha, sensor):
    lista = _protegidas([_fila(vol, b, fecha, 1.5)], [_brec(vol, b, fecha[:16], False, sensor)])
    assert lista[0]["perdida_aceptada"] is False
    assert len(aa.flags_protegidas(lista, "K")) == 1
    assert aa.protegidas_aparte(lista, "K") == []


# ------------------------------------------------------------------ main(): lo aparte llega a latest.json
HOY = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return HOY


def _correr_main(tmp_path, monkeypatch, con_normal):
    """Escenario de #915 en chico: una protegida sospechosa (Tupungatito), la aceptada de PCC y, si
    `con_normal`, una protegida MODIS de Chillán de la tabla sin publicar (control)."""
    banco_recs = [dict(_brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", False, "VIIRS_SNPP"),
                       lab="pos", lab_original="pos", z=16.0),
                  dict(_brec("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", False, "VIIRS_NOAA20_750"),
                       lab="pos", lab_original="pos", z=63.0)]
    banco_filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR", dist=5.27),
                   _fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:00", 1.19, dist=7.83)]
    if con_normal:
        banco_recs.append(dict(_brec("NevadosDeChillan", "MODIS", "2026-10-12 07:20", False, "MODIS_AQUA"),
                               lab="pos", lab_original="pos", z=50.0))
        banco_filas.append(_fila("NevadosDeChillan", "MODIS", "2026-10-12 07:20:00", 2.18, dist=1.0))
    records = {"Tupungatito": [], "PuyehueCordonCaulle": []}
    for i in range(61):   # un record por día para que la cobertura no degrade
        d = (HOY.date() - timedelta(days=i)).isoformat()
        records["Tupungatito"].append({"datetime_utc": d + " 05:00", "sensor": "VIIRS_NOAA20",
                                       "regimen": {"codigo_sha": "abc"} if d >= FRONTERA else {}})
    out = tmp_path / ("con" if con_normal else "sin")
    monkeypatch.setattr(aa, "OUTDIR", str(out))
    monkeypatch.setattr(aa, "datetime", _Reloj)
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a, **k: FRONTERA)
    monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: [])
    monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: None)
    monkeypatch.setattr(aa, "cargar_records",
                        lambda: (copy.deepcopy(records), {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(aa, "banco_ventana", lambda win: (copy.deepcopy(banco_recs), copy.deepcopy(banco_filas)))
    monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {})
    monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: "2026-10-25")
    monkeypatch.setattr(aa, "leer_ceses", lambda *a, **k: ([], None))
    aa.main()
    return json.loads((out / "latest.json").read_text(encoding="utf-8"))


def test_main_informa_aparte_sin_cambiar_el_veredicto(tmp_path, monkeypatch):
    out = _correr_main(tmp_path, monkeypatch, con_normal=False)
    aparte = out["informado_aparte"]["protegidas"]
    assert len(aparte) == 2
    assert any("Tupungatito" in a and "referencia sospechosa" in a for a in aparte)
    assert any("PuyehueCordonCaulle" in a and "pérdida aceptada" in a for a in aparte)
    assert not any(f.startswith("alerta protegida") for f in out["flags"])
    assert out["verdict"] == "VERDE"


def test_main_control_la_protegida_normal_sigue_dando_fuera_de_banda(tmp_path, monkeypatch):
    out = _correr_main(tmp_path, monkeypatch, con_normal=True)
    prot = [f for f in out["flags"] if f.startswith("alerta protegida")]
    assert len(prot) == 1 and "NevadosDeChillan MODIS 2026-10-12 07:20" in prot[0]
    assert out["verdict"] == "FUERA_DE_BANDA"
    assert len(out["informado_aparte"]["protegidas"]) == 2


def test_el_issue_lleva_lo_informado_aparte():
    """El cuerpo del issue (audit-weekly.yml) tiene que traer la lista aparte, para que lo que no decide el
    veredicto siga a la vista de quien lee el issue."""
    yml = (ROOT / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    assert "informado_aparte" in yml
    assert "/tmp/aparte.txt" in yml
