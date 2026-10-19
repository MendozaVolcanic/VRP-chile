# -*- coding: utf-8 -*-
"""S156: prueba de punta a punta de `auto_audit_weekly.main()` con datos sintéticos.

POR QUE: el verificador con contexto limpio de S156 hizo 12 mutaciones del script y las pruebas de las
funciones sueltas atraparon 4. Pasaban, entre otras, mezclar C0 y K en las falsas (el defecto que el
cambio arregla), no agregar los flags de protegidas, perder la marca `sha` en el banco, juzgar con C0,
quitar D-9 del recall e ignorar la frontera. Esta prueba corre `main()` entero sobre un escenario donde
cada una de esas mutaciones cambia el resultado.

Escenario (fechas relativas a hoy, porque `main()` usa la ventana rodante de hoy):
- frontera de K hace 19 días: 20 noches K y 40 C0 en la ventana de 60;
- VIIRS 375 Villarrica: 16 noches C0 con alerta que NO vemos y 16 noches K que vemos todas (recall C0 0 %,
  K 100 %; mezclados darían 50 % y flag); además 4 noches K con alertas mínimas (0,04 MW) que no vemos: con
  D-9 SN no cuentan, sin D-9 el recall K baja a 80 % y da flag;
- falsas: 10 negativos limpios C0 con 9 publicados y 10 K con 1 publicado (K 10 %, mezcla 50 %);
- una alerta protegida MODIS K de 2 MW sin publicar.
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

HOY = datetime.now(timezone.utc).date()
FRONTERA = (HOY - timedelta(days=19)).isoformat()
SHA = "f" * 40


def _dia(n):
    return (HOY - timedelta(days=n)).isoformat()


def _record(fecha, vrp, sha):
    r = {"datetime_utc": fecha + " 05:00", "sensor": "VIIRS_SNPP", "distance_class": "summit",
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0} if vrp else {},
         "f5_core_vrp_mw": vrp or None, "anomaly_pixels": [{}] if vrp else []}
    if sha:
        r["regimen"] = {"codigo_sha": SHA}
    return r


def _brec(fecha, hora, b, pub, lab, sha, sensor="VIIRS_SNPP"):
    dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab,
            "lab_original": lab, "sha": sha, "z": 20.0, "sensor": sensor}


def _escenario(sha_en_banco=True):
    records, alertas, filas_ref = [], [], []
    k_dias = [_dia(n) for n in range(0, 20)]          # 20 noches K
    c0_dias = [_dia(n) for n in range(20, 61)]        # 41 noches C0 (la ventana tiene 61 días)
    for i, d in enumerate(k_dias):
        minima = i >= 16
        vrp_mir = 0.04 if minima else 1.0
        alertas.append({"volcano": "Villarrica", "sensor_bucket": "VIIRS375",
                        "fecha_utc": d + " 05:00:00", "vrp_mw": vrp_mir})
        filas_ref.append({"volcano": "Villarrica", "sensor_bucket": "VIIRS375", "fecha_utc": d + " 05:00:00",
                          "vrp_mw": vrp_mir, "tipo": "ALERTA_TERMICA", "source": "CONS"})
        records.append(_record(d, 0.0 if minima else 1.0, sha=True))
    for i, d in enumerate(c0_dias):
        if i < 16:
            alertas.append({"volcano": "Villarrica", "sensor_bucket": "VIIRS375",
                            "fecha_utc": d + " 05:00:00", "vrp_mw": 1.0})
        records.append(_record(d, 0.0, sha=False))
    sha = SHA if sha_en_banco else None
    banco_recs = ([_brec(_dia(30), f"0{h}:00", "VIIRS375", h < 9, "neg_limpio", None) for h in range(10)]
                  + [_brec(_dia(5), f"0{h}:00", "VIIRS375", h < 1, "neg_limpio", sha) for h in range(10)]
                  + [_brec(_dia(3), "07:20", "MODIS", False, "pos", sha, sensor="MODIS_AQUA")])
    banco_filas = [{"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": _dia(3) + " 07:20:00",
                    "vrp_mw": 2.0, "tipo": "ALERTA_TERMICA", "source": "CONS"}]
    return records, alertas, filas_ref, (banco_recs, banco_filas)


@pytest.fixture
def correr(monkeypatch, tmp_path):
    def _correr(**kw):
        records, alertas, filas_ref, banco = _escenario(**kw)
        monkeypatch.setattr(aa, "leer_frontera_k", lambda *a: FRONTERA)
        monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: alertas)
        monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: filas_ref)
        monkeypatch.setattr(aa, "cargar_records",
                            lambda: ({"Villarrica": records}, {"parse_errors": [], "duplicates_total": 0}))
        monkeypatch.setattr(aa, "banco_ventana", lambda win: banco)
        monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {"Villarrica": (-39.42, -71.94)})
        monkeypatch.setattr(aa, "es_pasada_diurna_descartada", lambda *a: False)
        monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: HOY.isoformat())
        monkeypatch.setattr(aa, "OUTDIR", str(tmp_path))
        aa.main()
        out = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
        hist = [json.loads(x) for x in (tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()]
        return out, hist
    return _correr


def test_juzga_solo_k_con_d9(correr):
    out, _ = correr()
    assert out["detector"] == {"vigente": "K", "frontera_datos": FRONTERA, "regla_minimas": "SN"}
    r = out["recall"]["VIIRS375"]
    assert (r["recall_crater_pct"], r["n_noches"]) == (100.0, 16)          # D-9 SN quita las 4 mínimas
    ro = out["recall_regla_original"]["VIIRS375"]
    assert (ro["recall_crater_pct"], ro["n_noches"]) == (80.0, 20)
    c0 = out["por_detector"]["C0"]["recall"]["VIIRS375"]
    assert (c0["recall_crater_pct"], c0["n_noches"]) == (0.0, 16)
    assert not any(f.startswith("recall") for f in out["flags"])


def test_falsas_del_detector_vigente_no_la_mezcla(correr):
    out, hist = correr()
    f = out["falsas_publicaciones"]
    assert f["por_sensor"]["VIIRS375"] == {"n_neg_limpio": 10, "n_publica": 1, "falsas_pub_pct": 10.0}
    assert f["por_detector"]["C0"]["VIIRS375"]["falsas_pub_pct"] == 90.0
    assert hist[-1]["falsas_pub_pct"]["VIIRS375"] == 10.0
    assert hist[-1]["detector"]["vigente"] == "K"


def test_la_protegida_sin_publicar_es_flag_y_decide_el_veredicto(correr):
    out, _ = correr()
    prot = [f for f in out["flags"] if f.startswith("alerta protegida sin publicar")]
    assert len(prot) == 1 and "Villarrica MODIS" in prot[0] and "2.0 MW" in prot[0]
    assert out["verdict"] == "FUERA_DE_BANDA"
    assert out["cobertura"]["avisos"] == []


def test_sin_sha_en_el_banco_degrada(correr):
    out, _ = correr(sha_en_banco=False)
    assert any("marca de detector" in a for a in out["cobertura"]["avisos"])
    assert out["verdict"] == "DEGRADADO"


def test_frontera_ilegible_degrada(correr, monkeypatch):
    out, _ = correr()
    assert out["verdict"] != "DEGRADADO"
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a: None)
    aa.main()
    out2 = json.loads((Path(aa.OUTDIR) / "latest.json").read_text(encoding="utf-8"))
    assert out2["verdict"] == "DEGRADADO"
    assert any("DATOS_K_DESDE_UTC" in a for a in out2["cobertura"]["avisos"])
