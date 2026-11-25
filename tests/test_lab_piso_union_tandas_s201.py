# -*- coding: utf-8 -*-
"""S201: la unión de las tandas del barrido del piso (experiments/_s196_lab_piso/unir_tandas.py) se detiene ante
cualquier ambigüedad en vez de elegir en silencio. POR QUÉ: el verificador limpio del frente A de la ronda 5 de Codex
mostró que el evaluador re-sellado puede elegir otro piso con filas duplicadas de otro código (R5FA-102), copias de
una pasada (R5FA-101) o noches distintas entre brazos (R5FA-105); la cadena oficial no los produce salvo en la unión.
Cada prueba arma tandas sintéticas con un lector inyectado (sin git ni red)."""
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("unir_tandas", RAIZ / "experiments" / "_s196_lab_piso" / "unir_tandas.py")
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)


def rec(dt, sensor="VIIRS_NOAA20", vrp=0.0, sha="aaa", proc="2026-11-23T00:00:00Z"):
    return {"datetime_utc": dt, "sensor": sensor, "vrp_mw": vrp, "processed_utc": proc,
            "regimen": {"perfil": "x", "codigo_sha": sha, "origen": "actions"}}


def lector_de(tablas):
    """tablas: {(run, volcán): [records]}; mismos records en todos los brazos salvo que se diga."""
    def leer(run, brazo, volcan):
        v = tablas.get((run, brazo, volcan), tablas.get((run, volcan)))
        return None if v is None else {"volcano": volcan, "records": [dict(r) for r in v]}
    return leer


MAN = [{"run": "1", "etiqueta": "t1", "ini": "2026-03-01", "fin": "2026-03-31", "volcanes": ["A", "PCC"]},
       {"run": "2", "etiqueta": "t2", "ini": "2026-04-01", "fin": "2026-04-30", "volcanes": ["A", "PCC"]}]
SANO = {("1", "A"): [rec("2026-03-02 05:00"), rec("2026-03-03 05:00")], ("1", "PCC"): [rec("2026-03-02 05:10")],
        ("2", "A"): [rec("2026-04-02 05:00", sha="bbb")], ("2", "PCC"): [rec("2026-04-02 05:10", sha="bbb")]}


def test_union_sana_sin_problemas(tmp_path):
    problemas, conteo = U.unir(MAN, tmp_path, leer=lector_de(SANO))
    assert problemas == []
    d = json.loads((tmp_path / "_s196_lab_control" / "A.json").read_text(encoding="utf-8"))
    assert [r["datetime_utc"] for r in d["records"]] == ["2026-03-02 05:00", "2026-03-03 05:00", "2026-04-02 05:00"]
    assert conteo["_s196_lab_p150"]["PCC"]["unidos"] == 2
    assert (tmp_path / "informe_union.json").exists()


def test_duplicado_de_otro_codigo_aborta(tmp_path):
    """El caso real de marzo: Cordón Caulle en dos runs con el mismo dato y distinto codigo_sha (R5FA-102)."""
    man = MAN + [{"run": "3", "etiqueta": "t1b", "ini": "2026-03-01", "fin": "2026-03-31", "volcanes": ["PCC"]}]
    t = dict(SANO); t[("3", "PCC")] = [rec("2026-03-02 05:10", sha="ccc", proc="2026-11-24T00:00:00Z")]
    problemas, _ = U.unir(man, tmp_path, leer=lector_de(t))
    assert any("CONFLICTIVO" in p for p in problemas)


def test_duplicado_identico_salvo_hora_de_proceso_se_cuenta(tmp_path):
    man = MAN + [{"run": "3", "etiqueta": "t1b", "ini": "2026-03-01", "fin": "2026-03-31", "volcanes": ["PCC"]}]
    t = dict(SANO); t[("3", "PCC")] = [rec("2026-03-02 05:10", proc="2026-11-24T00:00:00Z")]
    problemas, conteo = U.unir(man, tmp_path, leer=lector_de(t))
    assert problemas == []
    assert conteo["_s196_lab_control"]["PCC"]["duplicados_identicos"] == 1
    assert conteo["_s196_lab_control"]["PCC"]["unidos"] == 2


def test_duplicado_dentro_de_un_run_aborta_si_difiere(tmp_path):
    t = dict(SANO); t[("1", "A")] = SANO[("1", "A")] + [rec("2026-03-02 05:00", vrp=3.0)]
    problemas, _ = U.unir(MAN, tmp_path, leer=lector_de(t))
    assert any("CONFLICTIVO" in p for p in problemas)


def test_record_fuera_de_la_ventana(tmp_path):
    t = dict(SANO); t[("2", "A")] = SANO[("2", "A")] + [rec("2026-05-01 05:00", sha="bbb")]
    problemas, _ = U.unir(MAN, tmp_path, leer=lector_de(t))
    assert any("fuera de la ventana" in p for p in problemas)


def test_mes_sin_fuente(tmp_path):
    man = [MAN[0], dict(MAN[1], volcanes=["PCC"])]
    problemas, _ = U.unir(man, tmp_path, leer=lector_de(SANO))
    assert any("A 2026-04" in p and "ningún run" in p for p in problemas)


def test_brazo_faltante(tmp_path):
    def leer(run, brazo, volcan):
        if brazo == "_s196_lab_p225" and run == "2" and volcan == "A":
            return None
        return lector_de(SANO)(run, brazo, volcan)
    problemas, _ = U.unir(MAN, tmp_path, leer=leer)
    assert any("_s196_lab_p225 A: falta en t2" in p for p in problemas)


def test_brazos_con_claves_distintas(tmp_path):
    """R5FA-105: una noche que está en un brazo y no en el control."""
    t = dict(SANO); t[("1", "_s196_lab_p250", "A")] = SANO[("1", "A")] + [rec("2026-03-09 05:00")]
    problemas, _ = U.unir(MAN, tmp_path, leer=lector_de(t))
    assert any("_s196_lab_p250 tiene 1 claves que el control no" in p for p in problemas)


def test_fin_distinto_del_sellado(tmp_path):
    problemas, _ = U.unir(MAN, tmp_path, leer=lector_de(SANO), fin_esperado="2026-11-23")
    assert any("distinto del esperado" in p for p in problemas)


def test_cli_sale_2_con_problemas(tmp_path, monkeypatch):
    m = tmp_path / "m.json"; m.write_text(json.dumps(MAN), encoding="utf-8")
    monkeypatch.setattr(U, "leer_git", lector_de(SANO))
    assert U.main([str(m), str(tmp_path / "s")]) == 0
    assert U.main([str(m), str(tmp_path / "s2"), "--fin-esperado", "2026-11-23"]) == 2


def test_manifiesto_real_cubre_marzo_a_noviembre_sin_repetir_volcan_por_mes():
    """El manifiesto del repo: cada volcán de la zona A y Cordón Caulle en cada mes de 2026-03 a 2026-11, una sola vez."""
    man = json.loads((RAIZ / "experiments" / "_s196_lab_piso" / "MANIFIESTO_TANDAS.json").read_text(encoding="utf-8"))
    vistos = {}
    for e in man:
        for v in e["volcanes"]:
            for mes in U.meses(e["ini"], e["fin"]):
                assert (v, mes) not in vistos, (v, mes, vistos.get((v, mes)), e["etiqueta"])
                vistos[(v, mes)] = e["etiqueta"]
    volcanes = {v for v, _ in vistos}
    assert len(volcanes) == 11
    ultimo = max(e["fin"] for e in man)
    for v in volcanes:
        for mes in U.meses("2026-03-01", ultimo):
            assert (v, mes) in vistos, (v, mes)
