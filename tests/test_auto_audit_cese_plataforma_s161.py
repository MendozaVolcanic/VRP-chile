# -*- coding: utf-8 -*-
"""S161: el auto-audit semanal no compara tasas de antes y de después del cese de Suomi NPP.

POR QUÉ (recomendación 5 del frente S159, experiments/_s159/cese_snpp/INFORME.md, rama `s159-pruebas`, §3 H3).
Desde el 2026-11-02 13:00 UTC Suomi NPP deja de entregar y VIIRS pasa de tres plataformas a dos: una pasada
menos por noche sobre cada volcán. El recall por noche se «salva» con menos pasadas y el máximo de la noche
sale de menos candidatos, así que las dos tasas que el audit juzga (recall por noche y magnitud mediana por
noche) cambian por el muestreo, no por el detector. La ventana rodante de 60 días mezclaría las dos mitades
hasta enero, y la mezcla puede tapar una caída o inventar una (A104, A90). Mismo arreglo que la frontera de K:
cada sensor afectado se juzga sólo desde el primer día UTC completo sin la plataforma, y lo de antes se
informa aparte. MODIS no pierde nada y no se recorta.

Las pruebas pasan por `main()` real, la vía pública que ya existía, para que antes del cambio fallen por
aserción. La fecha del cese sale de scripts/ceses_esperados.json (la lista que lee el NRT de #897 y la
vigilancia de #892), no se copia aquí; el «hoy» del escenario se arma desde ella. Las de control pasan antes y
después: antes del cese no cambia nada, MODIS no se recorta y una alerta protegida perdida antes del cese
sigue siendo una alerta perdida (es una pasada, no una tasa).
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
SHA = "f" * 40


def _cese_snpp():
    ceses = json.loads((ROOT / "scripts" / "ceses_esperados.json").read_text(encoding="utf-8"))["ceses"]
    snpp = [c for c in ceses if set(c["sensores"]) == {"VIIRS_SNPP", "VIIRS_SNPP_750"}]
    assert len(snpp) == 1, "la lista de ceses no trae a Suomi NPP"
    return datetime.strptime(snpp[0]["desde_utc"], "%Y-%m-%dT%H:%M:%SZ")


CESE = _cese_snpp()
# Primer día UTC completo sin Suomi NPP: la regla de pipeline/fetch.py::cese_cumplido (el día del cese
# todavía trae las pasadas nocturnas, que son de 04:54 a 07:06 UTC, y el cese es a las 13:00).
PRIMER_DIA = (CESE.date() if (CESE.hour, CESE.minute, CESE.second) == (0, 0, 0)
              else CESE.date() + timedelta(days=1))
# Hoy es la última de las 20 noches posteriores: sin cola sin datos al final de la ventana (S150).
DESPUES = datetime.combine(PRIMER_DIA + timedelta(days=19), datetime.min.time()).replace(
    hour=12, tzinfo=timezone.utc)
ANTES = datetime.combine(CESE.date() - timedelta(days=9), datetime.min.time()).replace(
    hour=12, tzinfo=timezone.utc)


def _iso(d):
    return d.isoformat()


def _record(fecha, sensor, vrp):
    return {"datetime_utc": fecha + " 05:00", "sensor": sensor, "distance_class": "summit",
            "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0} if vrp else {},
            "f5_core_vrp_mw": vrp or None, "anomaly_pixels": [{}] if vrp else [],
            "regimen": {"codigo_sha": SHA}}


def _alerta(fecha, bucket, vrp=1.0):
    return {"volcano": "Villarrica", "sensor_bucket": bucket, "fecha_utc": fecha + " 05:00:00", "vrp_mw": vrp}


def _brec(fecha, hora, b, pub, lab, sensor):
    dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab,
            "lab_original": lab, "sha": SHA, "z": 20.0, "sensor": sensor}


def _escenario():
    """VIIRS 375 de Villarrica, todas noches de K.

    - 35 noches antes del cese, con tres plataformas: MIROVA alerta y publicamos las 35 con su misma magnitud.
    - 20 noches después, con dos: publicamos 17 de 20 (85 %, bajo la banda de 93,4) a la mitad de MIROVA (0,5).
      Mezcladas: 52 de 55 (94,5 %, en banda) y razón mediana 1,0 (en banda): la mezcla tapa las dos caídas.
    - MODIS: 16 noches antes del cese, todas publicadas (control: MODIS no pierde plataforma, no se recorta).
    - Falsas de VIIRS 375 en negativos limpios: 9 de 10 antes y 1 de 10 después (mezcla 50 %, después 10 %).
    - Una alerta protegida de VIIRS 375 antes del cese, sin publicar (control: sigue siendo flag).
    """
    records, alertas = [], []
    for i in range(35):
        d = _iso(PRIMER_DIA - timedelta(days=1 + i))
        alertas.append(_alerta(d, "VIIRS375"))
        records.append(_record(d, "VIIRS_SNPP", 1.0))
    for i in range(20):
        d = _iso(PRIMER_DIA + timedelta(days=i))
        alertas.append(_alerta(d, "VIIRS375"))
        records.append(_record(d, "VIIRS_NOAA20", 0.5 if i >= 3 else 0.0))
    for i in range(16):
        d = _iso(PRIMER_DIA - timedelta(days=1 + i))
        alertas.append(_alerta(d, "MODIS"))
        records.append(_record(d, "MODIS_AQUA", 1.0))
    antes, despues = _iso(PRIMER_DIA - timedelta(days=5)), _iso(PRIMER_DIA + timedelta(days=5))
    prot = _iso(PRIMER_DIA - timedelta(days=3))
    banco_recs = ([_brec(antes, f"0{h}:00", "VIIRS375", h < 9, "neg_limpio", "VIIRS_SNPP") for h in range(10)]
                  + [_brec(despues, f"0{h}:00", "VIIRS375", h < 1, "neg_limpio", "VIIRS_NOAA20")
                     for h in range(10)]
                  + [_brec(prot, "06:40", "VIIRS375", False, "pos", "VIIRS_NOAA21")])
    banco_filas = [{"volcano": "Villarrica", "sensor_bucket": "VIIRS375", "fecha_utc": prot + " 06:40:00",
                    "vrp_mw": 2.0, "tipo": "ALERTA_TERMICA", "source": "CONS"}]
    return records, alertas, (banco_recs, banco_filas)


def _reloj(hoy):
    class _Reloj(datetime):
        @classmethod
        def now(cls, tz=None):
            return hoy
    return _Reloj


@pytest.fixture
def correr(monkeypatch, tmp_path):
    def _correr(hoy=DESPUES, ceses_json=None):
        records, alertas, banco = _escenario()
        monkeypatch.setattr(aa, "datetime", _reloj(hoy))
        monkeypatch.setattr(aa, "leer_frontera_k", lambda *a, **k: FRONTERA)
        monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: copy.deepcopy(alertas))
        monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: None)
        monkeypatch.setattr(aa, "cargar_records",
                            lambda: ({"Villarrica": copy.deepcopy(records)},
                                     {"parse_errors": [], "duplicates_total": 0}))
        monkeypatch.setattr(aa, "banco_ventana", lambda win: copy.deepcopy(banco))
        monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {"Villarrica": (-39.42, -71.94)})
        monkeypatch.setattr(aa, "es_pasada_diurna_descartada", lambda *a: False)
        monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: hoy.date().isoformat())
        monkeypatch.setattr(aa, "OUTDIR", str(tmp_path))
        if ceses_json is not None:
            monkeypatch.setattr(aa, "CESES_JSON", str(ceses_json), raising=False)
        aa.main()
        out = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
        hist = [json.loads(x) for x in (tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()]
        return out, hist
    return _correr


# ------------------------------------------------------------------ rojas antes del cambio
def test_recall_de_viirs_se_juzga_solo_despues_del_cese(correr):
    out, _ = correr()
    r = out["recall"]["VIIRS375"]
    assert (r["n_noches"], r["recall_crater_pct"]) == (20, 85.0), \
        "la ventana de VIIRS 375 mezcla noches con y sin Suomi NPP"
    assert any(f.startswith("recall VIIRS375 85.0%") for f in out["flags"])


def test_magnitud_de_viirs_se_juzga_solo_despues_del_cese(correr):
    out, _ = correr()
    m = out["magnitud_publicada_by_vol_sensor"]["Villarrica|VIIRS375"]
    assert (m["n_noches"], m["ratio_mediano"]) == (17, 0.5)
    assert any(f.startswith("magnitud Villarrica VIIRS375 0.5x < 0.7") for f in out["flags"])


def test_falsas_de_viirs_solo_despues_del_cese(correr):
    out, hist = correr()
    assert out["falsas_publicaciones"]["por_sensor"]["VIIRS375"] == {
        "n_neg_limpio": 10, "n_publica": 1, "falsas_pub_pct": 10.0}
    assert hist[-1]["falsas_pub_pct"]["VIIRS375"] == 10.0


def test_lo_de_antes_del_cese_se_informa_aparte(correr):
    out, hist = correr()
    plat = out.get("plataformas") or {}
    assert (plat.get("juzga_desde") or {}).get("VIIRS375") == PRIMER_DIA.isoformat()
    assert (plat.get("juzga_desde") or {}).get("VIIRS750") == PRIMER_DIA.isoformat()
    assert (plat.get("juzga_desde") or {}).get("MODIS") is None
    aparte = (plat.get("aparte") or {}).get("recall") or {}
    assert (aparte.get("VIIRS375") or {}).get("n_noches") == 35
    assert (aparte.get("VIIRS375") or {}).get("recall_crater_pct") == 100.0
    assert (hist[-1].get("plataformas_juzga_desde") or {}).get("VIIRS375") == PRIMER_DIA.isoformat()


def test_el_primer_dia_sin_snpp_es_el_mismo_que_el_del_nrt(correr):
    """A102: una sola regla del día del cese. El NRT (pipeline/fetch.py::cese_cumplido, #897) deja de buscar
    Suomi NPP desde un día; el audit tiene que empezar a juzgar sin ella ese mismo día."""
    fetch = pytest.importorskip("pipeline.fetch")
    dia = datetime(CESE.year, CESE.month, CESE.day)
    while fetch.cese_cumplido("VIIRS_SNPP", dia) is None:
        dia += timedelta(days=1)
    assert fetch.cese_cumplido("VIIRS_SNPP_750", dia) is not None
    out, _ = correr()
    assert ((out.get("plataformas") or {}).get("juzga_desde") or {}).get("VIIRS375") == dia.date().isoformat()


def test_lista_de_ceses_ilegible_degrada(correr, tmp_path):
    """Sin la lista no se sabe si la ventana mezcla: decirlo, como con la frontera de K ilegible."""
    out, _ = correr(ceses_json=tmp_path / "no_existe.json")
    assert any("ceses_esperados" in a for a in out["cobertura"]["avisos"])
    assert out["verdict"] == "DEGRADADO"


# ------------------------------------------------------------------ controles (pasan antes y después)
def test_control_antes_del_cese_no_cambia_nada(correr):
    out, _ = correr(hoy=ANTES)
    assert ANTES.date() < PRIMER_DIA
    # sólo caen en la ventana las noches previas (las 35 de VIIRS 375 menos las que quedan después de hoy)
    n_viirs = sum(1 for i in range(35) if PRIMER_DIA - timedelta(days=1 + i) <= ANTES.date())
    assert out["recall"]["VIIRS375"]["n_noches"] == n_viirs
    assert out["recall"]["VIIRS375"]["recall_crater_pct"] == 100.0


def test_control_modis_no_se_recorta(correr):
    out, _ = correr()
    r = out["recall"]["MODIS"]
    assert (r["n_noches"], r["recall_crater_pct"]) == (16, 100.0)


def test_control_la_protegida_perdida_antes_del_cese_sigue_siendo_flag(correr):
    out, _ = correr()
    prot = [f for f in out["flags"] if f.startswith("alerta protegida sin publicar")]
    assert len(prot) == 1 and "Villarrica VIIRS375" in prot[0]
    assert out["verdict"] == "FUERA_DE_BANDA"


# ------------------------------------------------------------------ S162: hallazgos PR162-01 y PR162-04
# Revisión independiente de #900: experiments/_s161_audit_cese/REVISION_S162.md.
UNA_SEMANA = datetime.combine(PRIMER_DIA + timedelta(days=6), datetime.min.time()).replace(
    hour=12, tzinfo=timezone.utc)


def test_viirs_sin_juzgar_por_n_bajo_el_minimo_lo_dice(correr, capsys):
    """PR162-01. Una semana después del cese VIIRS 375 junta 7 noches con alerta, bajo el mínimo de 15: sus
    flags de recall no pueden dispararse y, sin aviso, el informe se leería como «se arregló» cuando es «no se
    midió» (A87). Tiene que quedar escrito en latest.json y dicho en la consola. VIIRS 750 no tiene ninguna
    noche con alerta después del cese en el escenario, así que tampoco se juzga; MODIS no perdió plataforma."""
    out, _ = correr(hoy=UNA_SEMANA)
    assert out["recall"]["VIIRS375"]["n_noches"] == 7 < aa.MIN_N_RECALL
    plat = out.get("plataformas") or {}
    sj = plat.get("sin_juzgar") or {}
    assert set(sj) == {"VIIRS375", "VIIRS750"}, "un sensor sin juzgar desde el cese no queda escrito"
    v = sj["VIIRS375"]
    assert (v.get("n_noches"), v.get("minimo"), v.get("juzga_desde"), v.get("n_noches_aparte")) == \
        (7, aa.MIN_N_RECALL, PRIMER_DIA.isoformat(), 35)
    avisos = plat.get("avisos") or []
    assert len(avisos) == 2
    a375 = [a for a in avisos if a.startswith("VIIRS375 sin juzgar")]
    assert len(a375) == 1 and "plataformas.aparte" in a375[0]
    consola = capsys.readouterr().out
    assert all(a in consola for a in avisos), "el aviso no sale en la consola"
    # Con n suficiente el sensor sí se juzga y no sale como sin juzgar (20 noches de VIIRS 375).
    out, _ = correr(hoy=DESPUES)
    assert set((out.get("plataformas") or {}).get("sin_juzgar") or {}) == {"VIIRS750"}


def test_el_issue_lleva_los_sensores_sin_juzgar(tmp_path):
    """PR162-01, la otra mitad: el cuerpo del issue (FUERA_DE_BANDA y DEGRADADO) se arma en el workflow, no en
    el script. Se ejecuta el mismo comando que el workflow usa para listar los avisos."""
    import re
    import subprocess
    wf = (ROOT / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    m = re.search(r'python -c "([^"]*)" > /tmp/plataformas\.txt', wf)
    assert m, "el workflow no arma la lista de sensores sin juzgar para el issue"
    assert wf.count('"$(cat /tmp/plataformas.txt)"') == 2, "los dos cuerpos de issue tienen que llevarla"
    salida = tmp_path / "data" / "audit_continuous"
    salida.mkdir(parents=True)
    aviso = "VIIRS375 sin juzgar: 7 noches con alerta desde el cese"
    (salida / "latest.json").write_text(json.dumps({"plataformas": {"avisos": [aviso]}}), encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", m.group(1)], cwd=tmp_path, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "- " + aviso
    (salida / "latest.json").write_text(json.dumps({"plataformas": {"avisos": []}}), encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", m.group(1)], cwd=tmp_path, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0 and r.stdout.strip() == "- ninguno"


@pytest.mark.parametrize("sensores", [[None], "VIIRS_SNPP", ["SENSOR_INVENTADO"]],
                         ids=["sensor_null", "cadena_en_vez_de_lista", "sensor_desconocido"])
def test_lista_de_ceses_mal_formada_degrada_con_mensaje(correr, tmp_path, sensores):
    """PR162-04. Con un sensor null el audit moría (AttributeError) antes de escribir latest.json; con
    `sensores` como cadena o un sensor que no es de ningún bucket, no recortaba nada y no lo decía. Lo mismo
    que con la lista ilegible: aviso de cobertura que nombra el cese y DEGRADADO."""
    p = tmp_path / "ceses_mal.json"
    p.write_text(json.dumps({"ceses": [{"plataforma": "Suomi NPP", "sensores": sensores,
                                         "desde_utc": CESE.strftime("%Y-%m-%dT%H:%M:%SZ")}]}), encoding="utf-8")
    try:
        out, _ = correr(ceses_json=p)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"el audit muere con la lista mal formada ({type(e).__name__}: {e}) y no escribe latest.json")
    avisos = [a for a in out["cobertura"]["avisos"] if "ceses_esperados" in a]
    assert avisos, "la lista mal formada no recorta y nadie lo dice"
    assert "Suomi NPP" in avisos[0], "el aviso no dice qué cese está mal"
    assert out["verdict"] == "DEGRADADO"
