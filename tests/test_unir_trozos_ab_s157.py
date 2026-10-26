"""S157: el A/B corre por trozos de ventana con todos los brazos en el mismo job; `recolectar` une los trozos de
cada brazo y deja las salidas con la misma forma de antes (salidas/<brazo>/<volcan>.json y
salidas/logs/<brazo>_<volcan>.log), que es lo que leen contar_pasadas.py y los evaluadores.

POR QUE una prueba: con `merge-multiple` dos trozos del mismo brazo y volcan se pisarian en silencio (mismo camino
dentro del artefacto) y el A/B se evaluaria sobre la mitad de la ventana sin error.
"""
import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location("unir_trozos_ab_s157", RAIZ / "scripts" / "unir_trozos_ab.py")
ut = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ut)


def _rec(dt, sensor="VIIRS_SNPP"):
    return {"datetime_utc": dt, "sensor": sensor, "vrp_mw": 0.1}


def _trozo(raiz, vol, idx, ini, fin, brazos, records_por_brazo, log="linea"):
    base = raiz / f"s146ab-{vol}-{idx}-{ini}_{fin}"
    for b in brazos:
        p = base / "data" / b / f"{vol}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"volcano": vol, "updated": f"2026-10-20T0{idx}:00:00Z",
                                 "records": records_por_brazo[b]}), encoding="utf-8")
        lg = base / "logs" / f"{b}_{vol}.log"
        lg.parent.mkdir(parents=True, exist_ok=True)
        lg.write_text(f"FLAGS_BRAZO trozo{idx}\n{log}{idx}\n", encoding="utf-8")
    c = base / "cobertura" / f"cobertura_{vol}.json"
    c.parent.mkdir(parents=True, exist_ok=True)
    c.write_text(json.dumps({"fallas": [{"fecha": ini, "perfil": brazos[0]}] if idx == 2 else []}),
                 encoding="utf-8")


def test_une_los_trozos_de_cada_brazo_sin_pisarlos(tmp_path):
    rec, sal = tmp_path / "recolectado", tmp_path / "salidas"
    _trozo(rec, "Lascar", 1, "2026-09-01", "2026-09-10", ["_a", "_b"],
           {"_a": [_rec("2026-09-02T06:00:00Z")], "_b": [_rec("2026-09-03T06:00:00Z")]})
    _trozo(rec, "Lascar", 2, "2026-09-11", "2026-09-20", ["_a", "_b"],
           {"_a": [_rec("2026-09-12T06:00:00Z")], "_b": [_rec("2026-09-13T06:00:00Z")]})
    _trozo(rec, "Isluga", 1, "2026-09-01", "2026-09-20", ["_a"], {"_a": [_rec("2026-09-05T06:00:00Z")]})
    res = ut.unir(rec, sal)
    a = json.loads((sal / "_a" / "Lascar.json").read_text(encoding="utf-8"))
    assert [r["datetime_utc"] for r in a["records"]] == ["2026-09-02T06:00:00Z", "2026-09-12T06:00:00Z"]
    b = json.loads((sal / "_b" / "Lascar.json").read_text(encoding="utf-8"))
    assert [r["datetime_utc"] for r in b["records"]] == ["2026-09-03T06:00:00Z", "2026-09-13T06:00:00Z"]
    assert (sal / "_a" / "Isluga.json").exists()
    log = (sal / "logs" / "_a_Lascar.log").read_text(encoding="utf-8")
    assert log.index("trozo1") < log.index("trozo2")
    assert res["trozos"] == 3
    cob = json.loads((sal / "cobertura_brazos.json").read_text(encoding="utf-8"))
    assert cob["fallas"] == [{"fecha": "2026-09-11", "perfil": "_a", "volcan_trozo": "Lascar", "trozo": 2}]


def test_un_solo_trozo_se_copia_tal_cual(tmp_path):
    rec, sal = tmp_path / "recolectado", tmp_path / "salidas"
    _trozo(rec, "Lascar", 1, "2026-09-01", "2026-09-20", ["_a"], {"_a": [_rec("2026-08-01T06:00:00Z")]})
    ut.unir(rec, sal)
    orig = (rec / "s146ab-Lascar-1-2026-09-01_2026-09-20" / "data" / "_a" / "Lascar.json").read_bytes()
    assert (sal / "_a" / "Lascar.json").read_bytes() == orig


def test_volcan_con_guion_en_el_nombre(tmp_path):
    rec, sal = tmp_path / "recolectado", tmp_path / "salidas"
    _trozo(rec, "Planchon-Peteroa", 3, "2026-09-01", "2026-09-20", ["_a"], {"_a": []})
    ut.unir(rec, sal)
    assert (sal / "_a" / "Planchon-Peteroa.json").exists()


_spec2 = importlib.util.spec_from_file_location("plan_trozos_ab_s157", RAIZ / "scripts" / "plan_trozos_ab.py")
pt = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(pt)


def test_plan_tres_brazos_parte_la_ventana_de_d25_en_trozos_de_16_dias():
    jobs = pt.plan("2026-08-29", "2026-10-18", ["Lascar", "Isluga"], ["_c", "_g", "_on"])
    esperado = [("2026-08-29", "2026-09-13"), ("2026-09-14", "2026-09-29"), ("2026-09-30", "2026-10-15"),
                ("2026-10-16", "2026-10-18")]
    assert [(j["vol"], j["idx"], j["start"], j["end"]) for j in jobs] == [
        (v, k + 1, a, b) for v in ("Lascar", "Isluga") for k, (a, b) in enumerate(esperado)]


def test_plan_max_days_a_mano_manda():
    jobs = pt.plan("2026-09-01", "2026-09-20", ["Lascar"], ["_c", "_on"], max_days=30)
    assert [(j["start"], j["end"]) for j in jobs] == [("2026-09-01", "2026-09-20")]
