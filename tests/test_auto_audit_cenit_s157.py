# -*- coding: utf-8 -*-
"""S157 (tarea 1.35 del loop): el auto-audit informa la magnitud publicada y las falsas publicaciones
también por tramo de cenit del sensor y por régimen, sin cambiar ningún veredicto.

POR QUÉ: en Nevados de Chillán la razón contra MIROVA cae con el cenit del sensor (VIIRS 0,64 a 0,72 a
20-22°, 0,41 a 0,46 a 49°, 0,12 a 0,35 a 67,6°; experiments/_s154_chillan/razon_por_cenit.py). Un agregado
por volcán y sensor esconde esa curva (A90, A114): una semana con más pasadas de borde se lee como deriva
del volcán. Y una ventana que cruza #535 o la frontera de K mezcla tres regímenes (A104). Los estratos son
claves NUEVAS de latest.json; las de siempre, el veredicto y los avisos no cambian (prueba de no regresión).
"""
import copy
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"
WIN = ("2026-08-01", "2026-10-20")
# Commit de main sobre el que nace este cambio: la versión «antes» para la no regresión contra el código real.
BASE_SHA = "c408a909e"


def _rec(fecha, sensor="VIIRS_SNPP", vrp=1.0, core=None, z=None, sha="abc", dist=1.0, dc="summit"):
    r = {"datetime_utc": fecha, "sensor": sensor, "distance_class": dc,
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": dist}, "anomaly_pixels": [{}]}
    if core is not None:
        r["f5_core_vrp_mw"] = core
    if z is not None:
        r["sensor_zenith_deg"] = z
    if sha:
        r["regimen"] = {"perfil": "mirova_equivalent", "codigo_sha": sha}
    return r


# ------------------------------------------------------------------ tramos y régimen
def test_tramos_de_cenit_son_los_del_banco_y_sin_cenit_aparte():
    import banco_paridad as bp
    for z in (0.0, 20.5, 29.99, 30.0, 48.6, 49.99, 50.0, 59.9, 60.0, 67.6):
        assert aa.tramo_cenit(z) == bp.zbin(z)
    assert aa.tramo_cenit(21) == "z<30"
    assert aa.tramo_cenit(48.6) == "z30-50"
    assert aa.tramo_cenit(67.6) == "z>=60"
    assert aa.tramo_cenit(None) == "sin_cenit"


def test_regimen_de_pasada_separa_535_571_y_k():
    assert aa.regimen_de_pasada("2026-08-28 22:59", FRONTERA) == "antes_535"
    assert aa.regimen_de_pasada("2026-08-28 23:00", FRONTERA) == "535_a_571"
    assert aa.regimen_de_pasada("2026-08-31 23:59", FRONTERA) == "535_a_571"
    # borde de #571: el mismo corte que la ventana de falsas (INICIO_REGIMEN_FALSAS)
    assert aa.regimen_de_pasada(aa.INICIO_REGIMEN_FALSAS + " 00:00", FRONTERA) == "571_a_K"
    assert aa.regimen_de_pasada("2026-09-17 09:00", FRONTERA) == "571_a_K"
    assert aa.regimen_de_pasada("2026-09-18 01:00", FRONTERA) == "K"
    # sin frontera declarada no hay K
    assert aa.regimen_de_pasada("2026-10-01 01:00", None) == "571_a_K"


# ------------------------------------------------------------------ nuestros records por noche
def test_cada_publicacion_lleva_su_cenit_y_su_hora():
    recs = {"NevadosDeChillan": [_rec("2026-10-18 05:06", vrp=9.0, core=9.78, z=48.6),
                                 _rec("2026-10-18 05:42", vrp=7.0, core=7.0, z=20.5),
                                 _rec("2026-10-18 06:30", vrp=2.0, core=2.0)]}
    o = aa.nuestros_por_noche(recs, WIN, FRONTERA)["ours"][("NevadosDeChillan", "VIIRS375", "2026-10-18")]
    assert o["pub"] == [9.78, 7.0, 2.0]
    assert o["z_pub"] == [48.6, 20.5, None]
    assert o["dt_pub"] == ["2026-10-18 05:06", "2026-10-18 05:42", "2026-10-18 06:30"]


# ------------------------------------------------------------------ magnitud por cenit y régimen
def _chillan_k():
    """Seis noches K de Chillán VIIRS 375: dos de nadir (0,7), dos a 49° (0,45), dos oblicuas (0,2)."""
    mir, recs = {}, []
    for i, (z, razon) in enumerate([(21, 0.70), (22, 0.70), (48.6, 0.45), (49, 0.45), (67.6, 0.20), (65, 0.20)]):
        d = f"2026-10-{i + 1:02d}"
        mir[("NevadosDeChillan", "VIIRS375", d)] = 10.0
        recs.append(_rec(d + " 05:00", vrp=10 * razon, core=10 * razon, z=z))
    return mir, {"NevadosDeChillan": recs}


def test_magnitud_publicada_por_cenit_muestra_la_curva():
    mir, recs = _chillan_k()
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    est = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K")
    c = est["por_cenit"]["NevadosDeChillan|VIIRS375"]
    assert c["z<30"] == {"n_noches": 2, "ratio_mediano": 0.7, "n_misma_pasada": None}
    assert c["z30-50"] == {"n_noches": 2, "ratio_mediano": 0.45, "n_misma_pasada": None}
    assert c["z>=60"] == {"n_noches": 2, "ratio_mediano": 0.2, "n_misma_pasada": None}
    assert "z50-60" not in c


def test_el_cenit_de_la_noche_es_el_de_la_pasada_que_publica_el_maximo():
    """La razón de la noche usa max(pub): su cenit es el de esa pasada, no el de otra."""
    mir = {("NevadosDeChillan", "VIIRS375", "2026-10-18"): 20.0}
    # la pasada del máximo va SEGUNDA: con la primera el cenit saldría bien por azar (mutación M2, S157)
    recs = {"NevadosDeChillan": [_rec("2026-10-18 06:48", vrp=8.93, core=8.93, z=67.6),
                                 _rec("2026-10-18 05:06", vrp=9.78, core=9.78, z=48.6)]}
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    c = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K")["por_cenit"]["NevadosDeChillan|VIIRS375"]
    assert c == {"z30-50": {"n_noches": 1, "ratio_mediano": 0.489, "n_misma_pasada": None}}


def test_sin_cenit_se_cuenta_aparte_y_no_se_pierde_ninguna_noche():
    mir, recs = _chillan_k()
    mir[("NevadosDeChillan", "VIIRS375", "2026-10-10")] = 10.0
    recs["NevadosDeChillan"].append(_rec("2026-10-10 05:00", vrp=5.0, core=5.0, z=None))
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    ev = aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA)
    est = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K")
    c = est["por_cenit"]["NevadosDeChillan|VIIRS375"]
    assert c["sin_cenit"] == {"n_noches": 1, "ratio_mediano": 0.5, "n_misma_pasada": None}
    # la misma población que la clave de siempre: ninguna noche descartada en silencio
    for k, m in ev["magnitud_publicada_by_vol_sensor"].items():
        assert sum(t["n_noches"] for t in est["por_cenit"][k].values()) == m["n_noches"]


def test_por_cenit_es_solo_del_detector_vigente():
    mir, recs = _chillan_k()
    mir[("NevadosDeChillan", "VIIRS375", "2026-09-05")] = 10.0          # noche C0
    recs["NevadosDeChillan"].append(_rec("2026-09-05 05:00", vrp=9.0, core=9.0, z=21, sha=None))
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    c = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K")["por_cenit"]["NevadosDeChillan|VIIRS375"]
    assert c["z<30"]["n_noches"] == 2


def test_magnitud_por_regimen_separa_535_571_y_k_y_lleva_el_cenit():
    mir, recs = _chillan_k()
    extra = [("2026-08-25 05:00", 1.0, 21), ("2026-08-26 05:00", 1.0, 21),     # antes de #535
             ("2026-08-30 05:00", 0.8, 40),                                      # #535 a #571
             ("2026-09-05 05:00", 0.9, 21), ("2026-09-06 05:00", 0.3, 67)]     # #571 a K (C0)
    for fecha, razon, z in extra:
        mir[("NevadosDeChillan", "VIIRS375", fecha[:10])] = 10.0
        recs["NevadosDeChillan"].append(_rec(fecha, vrp=10 * razon, core=10 * razon, z=z, sha=None))
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    reg = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K")["por_regimen"]["NevadosDeChillan|VIIRS375"]
    assert list(reg) == ["antes_535", "535_a_571", "571_a_K", "K"]
    assert reg["antes_535"]["n_noches"] == 2 and reg["antes_535"]["ratio_mediano"] == 1.0
    assert reg["535_a_571"]["n_noches"] == 1 and reg["535_a_571"]["ratio_mediano"] == 0.8
    assert reg["571_a_K"]["n_noches"] == 2 and reg["571_a_K"]["ratio_mediano"] == 0.6
    assert reg["571_a_K"]["por_cenit"] == {"z<30": {"n_noches": 1, "ratio_mediano": 0.9, "n_misma_pasada": None},
                                          "z>=60": {"n_noches": 1, "ratio_mediano": 0.3, "n_misma_pasada": None}}
    assert reg["K"]["n_noches"] == 6 and reg["K"]["ratio_mediano"] == 0.45


def test_cada_celda_cuenta_las_noches_en_que_nuestra_pasada_maxima_es_la_de_miroVA():
    """El tramo divide NUESTRO máximo de la noche por el máximo de MIROVA de la noche: no es la razón
    pareada por pasada de S154. n_misma_pasada dice en cuántas noches las dos pasadas son la misma (±120 s)."""
    mir = {("NevadosDeChillan", "VIIRS375", "2026-10-01"): 10.0, ("NevadosDeChillan", "VIIRS375", "2026-10-02"): 10.0,
           ("NevadosDeChillan", "VIIRS375", "2026-10-03"): 10.0}
    recs = {"NevadosDeChillan": [_rec("2026-10-01 05:00", vrp=7, core=7, z=21),
                                 _rec("2026-10-02 05:00", vrp=7, core=7, z=22),
                                 _rec("2026-10-03 05:00", vrp=4, core=4, z=67)]}
    inst = {("NevadosDeChillan", "VIIRS375", "2026-10-01"): "2026-10-01 05:02:00",    # 120 s: misma
            ("NevadosDeChillan", "VIIRS375", "2026-10-02"): "2026-10-02 05:03:00",    # 180 s: otra
            ("NevadosDeChillan", "VIIRS375", "2026-10-03"): "2026-10-03 04:58:30"}    # 90 s: misma
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    est = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K", inst)
    c = est["por_cenit"]["NevadosDeChillan|VIIRS375"]
    assert c["z<30"] == {"n_noches": 2, "ratio_mediano": 0.7, "n_misma_pasada": 1}
    assert c["z>=60"] == {"n_noches": 1, "ratio_mediano": 0.4, "n_misma_pasada": 1}
    k = est["por_regimen"]["NevadosDeChillan|VIIRS375"]["K"]
    assert k["n_misma_pasada"] == 2 and k["por_cenit"]["z<30"]["n_misma_pasada"] == 1


def test_el_instante_de_miroVA_es_el_de_su_alerta_maxima_y_no_cambia_mir():
    alertas = [{"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 05:00:00", "vrp_mw": 3.0},
               {"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 06:40:00", "vrp_mw": 9.0},
               {"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 07:10:00", "vrp_mw": 2.0}]
    coords = {"NevadosDeChillan": (-36.86, -71.38)}
    mir, inst, nd = aa.noches_mirova_con_instante(alertas, coords, WIN)
    assert (mir, nd) == aa.noches_mirova(alertas, coords, WIN)
    assert inst == {("NevadosDeChillan", "VIIRS375", "2026-10-01"): "2026-10-01 06:40:00"}


# ------------------------------------------------------------------ falsas por cenit
def _banco(vol, b, noche, lab, pub, z, sha="abc"):
    dt = datetime.fromisoformat(noche + "T05:00:00").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": noche, "lab": lab, "lab_original": lab, "pub": pub,
            "z": z, "sha": sha, "sensor": "VIIRS_SNPP"}


def test_falsas_por_cenit_por_sensor_con_sin_cenit_y_solo_vigente():
    recs = [_banco("Llaima", "VIIRS375", "2026-10-01", "neg_limpio", True, 20),
            _banco("Llaima", "VIIRS375", "2026-10-02", "neg_limpio", False, 25),
            _banco("Llaima", "VIIRS375", "2026-10-03", "neg_limpio", True, 65),
            _banco("Llaima", "VIIRS375", "2026-10-04", "neg_limpio", True, None),
            _banco("Llaima", "VIIRS375", "2026-10-05", "pos", True, 20),               # no es negativo
            _banco("Llaima", "VIIRS750", "2026-10-06", "neg_limpio", False, 55),
            _banco("Llaima", "MODIS", "2026-10-07", "neg_limpio", True, 40),
            _banco("Llaima", "VIIRS375", "2026-09-10", "neg_limpio", True, 20, sha=None)]  # C0: fuera
    pc = aa.falsas_por_cenit(recs, FRONTERA, "K")
    assert set(pc) == set(aa.SENSORS)
    assert pc["VIIRS375"]["z<30"] == {"n_neg_limpio": 2, "n_publica": 1, "falsas_pub_pct": 50.0}
    assert pc["VIIRS375"]["z>=60"] == {"n_neg_limpio": 1, "n_publica": 1, "falsas_pub_pct": 100.0}
    assert pc["VIIRS375"]["sin_cenit"] == {"n_neg_limpio": 1, "n_publica": 1, "falsas_pub_pct": 100.0}
    assert pc["VIIRS750"] == {"z50-60": {"n_neg_limpio": 1, "n_publica": 0, "falsas_pub_pct": 0.0}}
    assert pc["MODIS"] == {"z30-50": {"n_neg_limpio": 1, "n_publica": 1, "falsas_pub_pct": 100.0}}


# ------------------------------------------------------------------ no regresión de main()
HOY = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return HOY


def _insumo():
    """Insumo sintético de main(): 60 días de Chillán y Villarrica, alertas de MIROVA y banco."""
    records = {"NevadosDeChillan": [], "Villarrica": []}
    alertas, banco = [], []
    for i in range(61):
        d = (HOY.date() - timedelta(days=i)).isoformat()
        sha = "abc" if d >= FRONTERA else None
        z = (21, 48.6, 67.6, None)[i % 4]
        records["NevadosDeChillan"].append(_rec(d + " 05:00", vrp=3.0 + i % 3, core=2.0 + i % 3, z=z, sha=sha))
        records["Villarrica"].append(_rec(d + " 05:00", sensor="VIIRS_SNPP_750", vrp=0.2, z=z, sha=sha))
        if i % 2 == 0:
            alertas.append({"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375",
                            "fecha_utc": d + " 05:00:00", "vrp_mw": 8.0})
            alertas.append({"volcano": "Villarrica", "sensor_bucket": "VIIRS750",
                            "fecha_utc": d + " 05:00:00", "vrp_mw": 0.3})
        banco.append(_banco("Villarrica", "VIIRS375", d, "neg_limpio" if i % 3 else "pos", i % 2 == 0, z, sha=sha))
        banco.append(_banco("Villarrica", "MODIS", d, "neg_limpio", i % 5 == 0, z, sha=sha))
    return records, alertas, banco


def _correr_main(mod, tmp_path, monkeypatch, nombre):
    records, alertas, banco = _insumo()
    out = tmp_path / nombre
    monkeypatch.setattr(mod, "OUTDIR", str(out))
    monkeypatch.setattr(mod, "datetime", _Reloj)
    monkeypatch.setattr(mod, "leer_frontera_k", lambda *a, **k: FRONTERA)
    monkeypatch.setattr(mod, "alertas_mirova", lambda *a, **k: copy.deepcopy(alertas))
    monkeypatch.setattr(mod, "_coords_por_volcan",
                        lambda: {"NevadosDeChillan": (-36.86, -71.38), "Villarrica": (-39.42, -71.94)})
    monkeypatch.setattr(mod, "cargar_filas_referencia", lambda: None)
    monkeypatch.setattr(mod, "cargar_records",
                        lambda: (copy.deepcopy(records), {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(mod, "banco_ventana", lambda win: (copy.deepcopy(banco), []))
    monkeypatch.setattr(mod, "_csv_ultima_fecha", lambda p: "2026-10-19")
    mod.main()
    latest = json.loads((out / "latest.json").read_text(encoding="utf-8"))
    hist = [json.loads(x) for x in (out / "history.jsonl").read_text(encoding="utf-8").splitlines()]
    return latest, hist


def _sin_claves_nuevas(latest):
    d = copy.deepcopy(latest)
    d.pop("magnitud_publicada_by_vol_sensor_cenit", None)
    d.pop("magnitud_publicada_by_vol_sensor_regimen", None)
    if isinstance(d.get("falsas_publicaciones"), dict):
        d["falsas_publicaciones"].pop("por_cenit", None)
    return d


def _sin_claves_s166(latest):
    """S166 (issue #915): `informado_aparte` es posterior al commit base. El insumo no trae protegidas, así
    que queda vacío y todo lo demás queda idéntico (tests/test_auto_audit_referencia_s166.py)."""
    d = copy.deepcopy(latest)
    assert d.pop("informado_aparte")["protegidas"] == []
    return d


def test_no_regresion_las_claves_de_siempre_no_cambian(tmp_path, monkeypatch):
    """Antes = el mismo main() con el paso de estratos apagado. Todo lo que existía queda idéntico.
    Corre en el CI (no necesita historia git), a diferencia de la comparación contra el commit base."""
    despues, hist_d = _correr_main(aa, tmp_path, monkeypatch, "despues")
    monkeypatch.setattr(aa, "agregar_estratos", lambda out, *a, **k: None)
    antes, hist_a = _correr_main(aa, tmp_path, monkeypatch, "antes")
    # el insumo ejercita lo que se vigila
    assert despues["magnitud_publicada_by_vol_sensor_cenit"]
    assert despues["magnitud_publicada_by_vol_sensor_regimen"]
    assert despues["falsas_publicaciones"]["por_cenit"]["VIIRS375"]
    # el insumo trae alertas de MIROVA pareables: n_misma_pasada no queda en None
    cel = despues["magnitud_publicada_by_vol_sensor_cenit"]["NevadosDeChillan|VIIRS375"]
    assert all(t["n_misma_pasada"] is not None for t in cel.values())
    assert sum(t["n_misma_pasada"] for t in cel.values()) > 0
    assert despues["magnitud_publicada_by_vol_sensor"]
    assert despues["flags"]
    for clave in antes:
        assert clave in despues
    assert _sin_claves_nuevas(despues) == antes
    assert despues["verdict"] == antes["verdict"]
    assert despues["avisos_detector"] == antes["avisos_detector"]
    assert despues["flags"] == antes["flags"]
    assert hist_d == hist_a


def _modulo_base():
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE_SHA}:scripts/auto_audit_weekly.py"],
                             capture_output=True, encoding="utf-8", check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    spec = importlib.util.spec_from_loader("auto_audit_weekly_base_s157", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(ROOT / "scripts" / "auto_audit_weekly.py")
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)  # noqa: S102
    return mod


def test_no_regresion_contra_el_codigo_de_main_previo(tmp_path, monkeypatch):
    """SÓLO LOCAL. Antes = el auto_audit_weekly.py del commit base (SHA fijo, el de origen de la rama), no
    un apagado simulado. El CI hace checkout con fetch-depth 1, no tiene ese commit y la prueba se salta
    diciéndolo; la que corre en el CI es test_no_regresion_las_claves_de_siempre_no_cambian."""
    base = _modulo_base()
    if base is None:
        pytest.skip(f"SOLO LOCAL: el CI hace checkout con fetch-depth 1 y no trae el commit base {BASE_SHA}; "
                    "la no regresion del CI es test_no_regresion_las_claves_de_siempre_no_cambian")
    antes, hist_a = _correr_main(base, tmp_path, monkeypatch, "base")
    despues, hist_d = _correr_main(aa, tmp_path, monkeypatch, "nuevo")
    # S161 agregó `plataformas` (y su línea de historial) después del commit base; el insumo es de antes del
    # cese de Suomi NPP, así que no recorta nada y todo lo demás tiene que quedar idéntico.
    assert despues.pop("plataformas")["juzga_desde"] == {s: None for s in aa.SENSORS}
    for h in hist_d:
        assert h.pop("plataformas_juzga_desde") == {s: None for s in aa.SENSORS}
    assert _sin_claves_nuevas(_sin_claves_s166(despues)) == antes
    assert despues["verdict"] == antes["verdict"]
    assert despues["avisos_detector"] == antes["avisos_detector"]
    assert hist_d == hist_a
