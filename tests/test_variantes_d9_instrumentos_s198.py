# -*- coding: utf-8 -*-
"""F7-V501 (auditoría Codex ronda 2, verificado): las variantes de D-9 en el auto-audit, la comparación vía/K y el eje
de referencia.

POR QUÉ. La regla D-9 (`docs/MISSION.md`, regla 5 del criterio de victoria, issue #811) decide SN: una pasada de VIIRS
375 cuyas alertas son todas de 0,05 MW o menos cuenta como «MIROVA no vio nada». La misma regla exige que cada
evaluación informe además SE (estrato aparte), la regla original y las dos con umbral 0,04. #1115 lo resolvió en el
banco de paridad con un script aparte (el banco está sellado). F7-V501 encontró la misma omisión en
`scripts/auto_audit_weekly.py`, `scripts/comparacion_via_k.py` y el eje de referencia
(`scripts/clasificacion_referencia.py` con su CLI `scripts/clasificar_referencia.py`). Ninguno de los tres está en un
manifiesto sellado, así que cada uno agrega una sección `variantes_d9` a su salida, con las cinco lecturas de
`banco_paridad_variantes_d9.VARIANTES_D9` (una sola definición), sin tocar las cifras de la decidida ni el veredicto.

Escenario sintético (el de #1115): Lastarria VIIRS 375, una noche con alertas de 0,04 y 0,05 MW y una RUTINA de la tabla
con VRP 0, y otra noche con una protegida de 2 MW. Cada variante tiene que contar lo suyo y la protegida no cambia.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import banco_paridad as bp  # noqa: E402
import banco_paridad_variantes_d9 as vd  # noqa: E402
import clasificar_referencia as clr  # noqa: E402
import comparacion_via_k as cv  # noqa: E402
import scripts.auto_audit_weekly as aa  # noqa: E402

VENTANA = ("2026-09-10", "2026-09-11")
NOMBRES = ["SN_005", "SE_005", "original", "SN_004", "SE_004"]


def _f(vrp, tipo="ALERTA_TERMICA", hora="2026-09-10 05:30:00", source="CONS"):
    return {"volcano": "Lastarria", "sensor_bucket": "VIIRS375", "fecha_utc": hora, "source": source, "tipo": tipo,
            "vrp_mw": vrp, "dist_km": 1.0}


def _filas():
    return [_f(0.04, hora="2026-09-10 05:30:00"), _f(0.05, hora="2026-09-10 06:10:00"),
            _f(0.0, tipo="RUTINA", hora="2026-09-10 07:00:00"), _f(2.0, hora="2026-09-11 05:30:00")]


HORAS = (((10, 5, 30), 1), ((10, 6, 10), 0), ((10, 7, 0), 1), ((11, 5, 30), 1))


def _recs():
    out = []
    for (d, h, m), pub in HORAS:
        dt = datetime(2026, 9, d, h, m, tzinfo=timezone.utc)
        out.append({"vol": "Lastarria", "b": "VIIRS375", "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "pub": pub,
                    "clave": dt.strftime("%Y-%m-%d %H:%M") + "|VIIRS_SNPP"})
    return out


# Etiqueta del banco de cada pasada (05:30, 06:10, 07:00 del 10; 05:30 del 11) en cada lectura, escrita a mano desde
# la regla: SN pasa las mínimas a RUTINA (la noche queda limpia), SE las manda al estrato «minima» (la noche no cambia),
# con 0,04 la alerta de 0,05 sigue siendo alerta.
ETIQUETAS = {"original": ["pos", "pos", "sin_info", "pos"],
             "SN_005": ["neg_limpio", "neg_limpio", "neg_limpio", "pos"],
             "SN_004": ["sin_info", "pos", "sin_info", "pos"],
             "SE_005": ["minima", "minima", "sin_info", "pos"],
             "SE_004": ["minima", "pos", "sin_info", "pos"]}


def test_los_tres_instrumentos_usan_la_misma_lista_de_variantes():
    assert [v[0] for v in vd.VARIANTES_D9] == NOMBRES and vd.VARIANTE_DECIDIDA == "SN_005"


# ------------------------------------------------------------------ auto_audit_weekly
def test_audit_etiqueta_cada_pasada_con_las_cinco_lecturas():
    recs = _recs()
    aa.etiquetas_variantes_d9(recs, _filas(), bp._coords_por_volcan(), VENTANA)
    for nombre, esperado in ETIQUETAS.items():
        assert [r["lab_d9"][nombre] for r in recs] == esperado, nombre
    assert all("lab" not in r for r in recs)   # no pisa la etiqueta que usa el resto del audit


def test_audit_falsas_por_variante():
    recs = _recs()
    aa.etiquetas_variantes_d9(recs, _filas(), bp._coords_por_volcan(), VENTANA)
    fv = aa.falsas_variantes_d9(recs)
    assert fv["SN_005"]["VIIRS375"] == {"n_neg_limpio": 3, "n_publica": 2, "falsas_pub_pct": 66.7, "n_minima": 0}
    assert fv["original"]["VIIRS375"] == {"n_neg_limpio": 0, "n_publica": 0, "falsas_pub_pct": None, "n_minima": 0}
    assert fv["SE_005"]["VIIRS375"]["n_minima"] == 2 and fv["SE_004"]["VIIRS375"]["n_minima"] == 1
    assert fv["SN_004"]["VIIRS375"]["n_neg_limpio"] == 0
    # Sin las etiquetas (banco que no pasó por etiquetas_variantes_d9) no inventa cifras.
    assert aa.falsas_variantes_d9(_recs()) is None


def test_audit_recall_por_variante():
    # Tres noches con alerta de MIROVA que no vemos: 0,04, 0,05 y una protegida de 2 MW.
    alertas = [{"volcano": "Lastarria", "sensor_bucket": "VIIRS375", "fecha_utc": f"2026-09-{d} 05:30:00", "vrp_mw": v}
               for d, v in (("10", 0.04), ("11", 0.05), ("12", 2.0))]
    filas = [dict(a, tipo="ALERTA_TERMICA", source="CONS") for a in alertas]
    vistos = {("Lastarria", "VIIRS375", f"2026-09-{d}") for d in ("10", "11", "12")}
    rv = aa.recall_variantes_d9(alertas, filas, bp._coords_por_volcan(), ("2026-09-01", "2026-09-30"), {}, None, "C0",
                                None, vistos, {})
    n = {nombre: rv[nombre]["VIIRS375"]["n_noches"] for nombre in NOMBRES}
    assert n == {"SN_005": 1, "SE_005": 1, "original": 3, "SN_004": 2, "SE_004": 2}
    assert all(rv[nombre]["VIIRS375"]["recall_crater_pct"] == 0.0 for nombre in NOMBRES)


# Punta a punta sobre el escenario de tests/test_auto_audit_main_s156.py (cuatro noches K con alertas de 0,04 MW).
import test_auto_audit_main_s156 as s156  # noqa: E402


def _correr_main(monkeypatch, tmp_path, romper=False):
    records, alertas, filas_ref, (brecs, bfilas) = s156._escenario()
    for r in brecs:   # el banco simulado no pasa por etiquetas_variantes_d9: misma etiqueta en las cinco lecturas
        r["lab_d9"] = {n: r["lab"] for n in NOMBRES}
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a: s156.FRONTERA)
    monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: alertas)
    monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: filas_ref)
    monkeypatch.setattr(aa, "cargar_records",
                        lambda: ({"Villarrica": records}, {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(aa, "banco_ventana", lambda win: (brecs, bfilas))
    monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {"Villarrica": (-39.42, -71.94)})
    monkeypatch.setattr(aa, "es_pasada_diurna_descartada", lambda *a: False)
    monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: s156.HOY.isoformat())
    monkeypatch.setattr(aa, "leer_ceses", lambda *a, **k: ([], None))
    monkeypatch.setattr(aa, "OUTDIR", str(tmp_path))
    if romper:
        def _falla(*a, **k):
            raise RuntimeError("roto a propósito")
        monkeypatch.setattr(aa, "variantes_d9_audit", _falla)
    aa.main()
    out = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    hist = [json.loads(x) for x in (tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()]
    return out, hist


def test_audit_main_informa_las_cinco_y_los_controles(monkeypatch, tmp_path):
    out, _ = _correr_main(monkeypatch, tmp_path)
    v = out["variantes_d9"]
    assert v["variante_decidida"] == "SN_005" and list(v["variantes"]) == NOMBRES
    rec = {n: (v["variantes"][n]["recall"]["VIIRS375"]["n_noches"],
               v["variantes"][n]["recall"]["VIIRS375"]["recall_crater_pct"]) for n in NOMBRES}
    assert rec == {"SN_005": (16, 100.0), "SE_005": (16, 100.0), "original": (20, 80.0),
                   "SN_004": (16, 100.0), "SE_004": (16, 100.0)}
    assert v["control"] == {"decidida_reproduce_recall": True, "original_reproduce_recall_regla_original": True,
                            "decidida_reproduce_falsas": True, "original_reproduce_falsas_regla_original": True}


def test_audit_la_seccion_no_cambia_nada_mas(monkeypatch, tmp_path):
    """Lo demás de latest.json (veredicto, flags, recall, falsas) y la línea del historial quedan idénticos aunque la
    sección falle: la sección sólo informa."""
    a, ha = _correr_main(monkeypatch, tmp_path / "a")
    b, hb = _correr_main(monkeypatch, tmp_path / "b", romper=True)
    assert "error" in b["variantes_d9"] and "error" not in a["variantes_d9"]
    for d in (a, b):
        d.pop("variantes_d9")
        d.pop("generated_utc")
    assert a == b
    assert [dict(h, date=None) for h in ha] == [dict(h, date=None) for h in hb]


# ------------------------------------------------------------------ comparacion_via_k
def _pasadas(pubs):
    out = []
    for ((d, h, m), _), pub in zip(HORAS, pubs):
        dt = datetime(2026, 9, d, h, m, tzinfo=timezone.utc)
        out.append({"vol": "Lastarria", "b": "VIIRS375", "sensor": "VIIRS_SNPP", "dt": dt,
                    "noche": dt.strftime("%Y-%m-%d"), "pub": pub, "disp": 1.0 if pub else None, "dc": "summit",
                    "d_mc": 0.5})
    return out


VENTS = {"historia": {"VIIRS375": VENTANA}}


def _comparar_como_main(via, k, filas):
    """Lo que hace main() con la regla decidida, para la clave de VENTS."""
    coords = bp._coords_por_volcan()
    idx = bp.indexar_referencia(cv.filas_ref_de_franja(filas, coords, False), coords, VENTANA,
                                regla_minimas=cv.MODO_MINIMAS)
    v_l, k_l = cv.etiquetar(via, idx), cv.etiquetar(k, idx)
    return {"tabla|historia|VIIRS375": cv.comparar(cv._indice(v_l, "VIIRS375", *VENTANA),
                                                   cv._indice(k_l, "VIIRS375", *VENTANA), "VIIRS375")}


@pytest.fixture(scope="module")
def comparacion():
    via, k, filas = _pasadas([p for _, p in HORAS]), _pasadas([0, 0, 0, 0]), _filas()
    res = _comparar_como_main(via, k, filas)
    return cv.variantes_d9({"tabla": filas}, bp._coords_por_volcan(), VENTANA, VENTS, via, [], k, res), res


@pytest.mark.parametrize("variante,via_tp,via_fp,k_fn,k_tn", [
    ("original", 2, 0, 2, 0),
    ("SN_005", 1, 1, 1, 1),   # la noche del 10 queda limpia y la vía publicó en ella
    ("SN_004", 2, 0, 2, 0),
    ("SE_005", 1, 0, 1, 0),   # la noche del 10 va al estrato aparte: ni alerta ni negativo
    ("SE_004", 2, 0, 2, 0),
])
def test_comparacion_cada_variante_cuenta_lo_suyo(comparacion, variante, via_tp, via_fp, k_fn, k_tn):
    v, _ = comparacion
    r = v["variantes"][variante]["resultados"]["tabla|historia|VIIRS375"]
    assert (r["via"]["TP"], r["via"]["FP"], r["k"]["FN"], r["k"]["TN"]) == (via_tp, via_fp, k_fn, k_tn)
    assert (r["via"]["protegidas"], r["k"]["protegidas_perdidas"]) == (1, 1)   # la protegida no cambia


def test_comparacion_la_decidida_reproduce_los_resultados(comparacion):
    v, res = comparacion
    assert v["variante_decidida"] == "SN_005" and list(v["variantes"]) == NOMBRES
    assert v["decidida_coincide_con_resultados"] is True
    # Control de que el control puede fallar: con otros resultados dice False.
    otro = {k: dict(x, n_pasadas_pareadas=x["n_pasadas_pareadas"] + 1) for k, x in res.items()}
    via, k, filas = _pasadas([p for _, p in HORAS]), _pasadas([0, 0, 0, 0]), _filas()
    v2 = cv.variantes_d9({"tabla": filas}, bp._coords_por_volcan(), VENTANA, VENTS, via, [], k, otro)
    assert v2["decidida_coincide_con_resultados"] is False


# ------------------------------------------------------------------ eje de referencia (clasificar_referencia --stats)
@pytest.mark.parametrize("variante,esperado", [
    ("original", {"mirova_confirmed": 3, "mirova_same_night": 1}),
    ("SN_005", {"mirova_confirmed": 1, "mirova_silent": 3}),
    ("SN_004", {"mirova_confirmed": 2, "mirova_same_night": 2}),
    ("SE_005", {"mirova_confirmed": 1, "mirova_same_night": 3}),
    ("SE_004", {"mirova_confirmed": 2, "mirova_same_night": 2}),
])
def test_eje_cada_variante_cuenta_lo_suyo(variante, esperado):
    recs = _recs()
    v = clr.variantes_d9(recs, _filas(), bp._coords_por_volcan(), VENTANA)
    t = v["variantes"][variante]["todas"]["por_sensor"]["VIIRS375"]
    assert {k: n for k, n in t.items() if n and k != "total"} == esperado
    assert t["total"] == 4
    assert all("valor" not in r for r in recs)   # trabaja sobre copias


def test_eje_publicadas_por_variante():
    v = clr.variantes_d9(_recs(), _filas(), bp._coords_por_volcan(), VENTANA)
    p = v["variantes"]["SN_005"]["publicadas"]["por_sensor"]["VIIRS375"]
    assert (p["mirova_silent"], p["mirova_confirmed"], p["total"]) == (2, 1, 3)


def test_eje_la_decidida_es_la_del_modulo():
    """La variante decidida rotula igual que `clasificar_pasadas` sin argumentos (lo que escriben los JSON por volcán)."""
    recs = _recs()
    from clasificacion_referencia import clasificar_pasadas
    clasificar_pasadas(recs, _filas(), bp._coords_por_volcan(), VENTANA)
    base = clr._tabla(recs, lambda r: r["b"])
    v = clr.variantes_d9(_recs(), _filas(), bp._coords_por_volcan(), VENTANA)
    assert v["variantes"]["SN_005"]["todas"]["por_sensor"] == base
    assert v["variantes"]["original"]["todas"]["por_sensor"] != base
