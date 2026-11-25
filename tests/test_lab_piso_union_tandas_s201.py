# -*- coding: utf-8 -*-
"""S201: la unión de las tandas del barrido del piso (experiments/_s196_lab_piso/unir_tandas.py) se detiene ante
cualquier ambigüedad en vez de elegir en silencio, y con problemas no deja carpetas de brazo para el evaluador.
POR QUÉ: el verificador limpio del frente A de la ronda 5 de Codex mostró que el evaluador re-sellado puede elegir otro
piso con duplicados de otro código (R5FA-102), copias de una pasada (R5FA-101) o noches distintas entre brazos
(R5FA-105); la cadena oficial no los produce salvo en la unión. El verificador limpio del PR mostró que un run con
trabajos caídos publica datos parciales (Isluga de marzo en t2: 8 records en vez de 271) y que 13 de 22 mutaciones
sobrevivían a la primera versión de estas pruebas. Todo con tandas sintéticas y lectores inyectados (sin git ni red)."""
import hashlib
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("unir_tandas", RAIZ / "experiments" / "_s196_lab_piso" / "unir_tandas.py")
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)

V = U.VOLCANES


def rec(dt, sensor="VIIRS_NOAA20", vrp=0.0, sha="aaa", proc="2026-11-23T00:00:00Z"):
    return {"datetime_utc": dt, "sensor": sensor, "vrp_mw": vrp, "processed_utc": proc,
            "regimen": {"perfil": "x", "codigo_sha": sha, "origen": "actions"}}


def man(entradas=None):
    return entradas or [
        {"run": "1", "etiqueta": "t1", "ini": "2026-03-01", "fin": "2026-03-31", "volcanes": list(V)},
        {"run": "2", "etiqueta": "t2", "ini": "2026-04-01", "fin": "2026-04-30", "volcanes": list(V)}]


def recs_de(ini, fin, sha="aaa"):
    """Un record cada 2 días de ini a fin, incluidos el primer y el último día (bordes de la ventana)."""
    a, b, out = date.fromisoformat(ini), date.fromisoformat(fin), []
    while a < b:
        out.append(rec(a.isoformat() + " 05:00", sha=sha)); a += timedelta(days=2)
    out.append(rec(b.isoformat() + " 05:00", sha=sha))
    return list(reversed(out))                     # desordenados a propósito: la unión ordena


def tablas(entradas=None):
    return {(e["run"], v): recs_de(e["ini"], e["fin"], sha="s" + e["run"]) for e in man(entradas) for v in e["volcanes"]}


def lector(t, por_brazo=None):
    por_brazo = por_brazo or {}
    def leer(run, brazo, volcan):
        v = por_brazo.get((run, brazo, volcan), t.get((run, volcan)))
        return None if v is None else {"volcano": volcan, "records": [dict(r) for r in v]}
    return leer


def verdes(run):
    return {v: ["success"] * 7 for v in V}


def correr(tmp_path, entradas=None, t=None, por_brazo=None, trabajos=verdes, **kw):
    return U.unir(man(entradas), tmp_path / "s", leer=lector(t or tablas(entradas), por_brazo), trabajos=trabajos, **kw)


def test_constantes():
    assert len(U.BRAZOS) == 9 and len(set(U.BRAZOS)) == 9 and U.CONTROL in U.BRAZOS
    assert {"_s196_lab_sinzona", "_s196_lab_p300", "_s196_lab_p150"} <= set(U.BRAZOS)
    assert len(V) == 11 and "PuyehueCordonCaulle" in V and U.INICIO == "2026-03-01"


def test_union_sana(tmp_path):
    problemas, conteo = correr(tmp_path)
    assert problemas == []
    f = tmp_path / "s" / "_s196_lab_control" / "Isluga.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    fechas = [r["datetime_utc"] for r in d["records"]]
    assert fechas == sorted(fechas)                                       # ordenados
    assert fechas[0] == "2026-03-01 05:00" and fechas[-1] == "2026-04-30 05:00"   # bordes de la ventana
    assert conteo["_s196_lab_p150"]["Isluga"]["unidos"] == len(fechas)
    assert conteo["_s196_lab_control"]["Isluga"]["sha256"] == hashlib.sha256(f.read_bytes()).hexdigest()
    assert (tmp_path / "s" / "informe_union.json").exists() and not (tmp_path / "s.parcial").exists()


def test_salida_existente_no_se_toca(tmp_path):
    (tmp_path / "s").mkdir(); (tmp_path / "s" / "viejo.json").write_text("{}", encoding="utf-8")
    problemas, _ = correr(tmp_path)
    assert any("ya existe" in p for p in problemas)
    assert (tmp_path / "s" / "viejo.json").read_text(encoding="utf-8") == "{}"


def _sin_brazos(tmp_path):
    return not (tmp_path / "s").exists() and not any((tmp_path / "s.parcial" / b).exists() for b in U.BRAZOS)


def test_conflictivo_dentro_de_un_run_aborta_sin_carpetas(tmp_path):
    t = tablas(); t[("1", "Isluga")] = t[("1", "Isluga")] + [rec("2026-03-01 05:00", vrp=3.0, sha="s1")]
    problemas, _ = correr(tmp_path, t=t)
    assert any("Isluga: duplicado CONFLICTIVO" in p for p in problemas)
    assert _sin_brazos(tmp_path)
    assert json.loads((tmp_path / "s.parcial" / "informe_union.json").read_text(encoding="utf-8"))["problemas"]


def test_duplicado_de_otro_codigo_es_conflictivo(tmp_path):
    t = tablas(); t[("1", "Isluga")] = t[("1", "Isluga")] + [rec("2026-03-01 05:00", sha="otro")]
    problemas, _ = correr(tmp_path, t=t)
    assert any("CONFLICTIVO" in p for p in problemas)


def test_duplicado_identico_salvo_hora_de_proceso_se_cuenta(tmp_path):
    t = tablas(); t[("1", "Isluga")] = t[("1", "Isluga")] + [rec("2026-03-01 05:00", sha="s1", proc="2026-11-24T00:00:00Z")]
    problemas, conteo = correr(tmp_path, t=t)
    assert problemas == []
    assert conteo["_s196_lab_control"]["Isluga"]["duplicados_identicos"] == 1


def test_volcan_mes_en_dos_entradas(tmp_path):
    e = man() + [{"run": "3", "etiqueta": "t1b", "ini": "2026-03-01", "fin": "2026-03-31", "volcanes": ["PuyehueCordonCaulle"]}]
    problemas, _ = correr(tmp_path, entradas=e)
    assert any("PuyehueCordonCaulle 2026-03: en dos entradas" in p for p in problemas)


def test_record_fuera_de_la_ventana(tmp_path):
    t = tablas(); t[("2", "Lascar")] = t[("2", "Lascar")] + [rec("2026-05-01 05:00", sha="s2")]
    problemas, _ = correr(tmp_path, t=t)
    assert any("Lascar: record 2026-05-01 05:00 fuera de la ventana de t2" in p for p in problemas)


def test_record_sin_sensor_o_sin_hora(tmp_path):
    t = tablas(); t[("1", "Llaima")] = t[("1", "Llaima")] + [rec("2026-03-04 05:00", sensor=None)]
    problemas, _ = correr(tmp_path, t=t)
    assert any("Llaima: record sin datetime_utc o sensor" in p for p in problemas)
    t = tablas(); t[("1", "Llaima")] = t[("1", "Llaima")] + [{"sensor": "VIIRS_NOAA20"}]
    problemas, _ = U.unir(man(), tmp_path / "s2", leer=lector(t), trabajos=verdes)
    assert any("Llaima: record sin datetime_utc o sensor" in p for p in problemas)


def test_trabajo_caido_o_sin_dato(tmp_path):
    def con_caida(run):
        d = verdes(run)
        if run == "1":
            d["Isluga"] = ["success"] * 6 + ["failure"]
        return d
    problemas, _ = correr(tmp_path, trabajos=con_caida)
    assert any("t1 (1) Isluga: trabajos no todos en success" in p for p in problemas)
    problemas, _ = U.unir(man(), tmp_path / "s2", leer=lector(tablas()), trabajos=lambda run: None)
    assert any("sin dato de sus trabajos" in p for p in problemas)
    problemas, _ = U.unir(man(), tmp_path / "s3", leer=lector(tablas()),
                          trabajos=lambda run: {v: ["success"] for v in V if v != "Copahue"})
    assert any("Copahue: trabajos no todos en success: []" in p for p in problemas)


def test_trozo_vacio_como_isluga_en_t2(tmp_path):
    """El caso real: un run con trabajos caídos publica sólo unos pocos records del volcán."""
    t = tablas(); t[("1", "Isluga")] = [rec("2026-03-02 05:00", sha="s1"), rec("2026-03-03 05:00", sha="s1")]
    problemas, _ = correr(tmp_path, t=t)
    assert any("Isluga: trozo 2026-03-06 a 2026-03-10 de t1 sin ningún record" in p for p in problemas)


def test_brazo_faltante(tmp_path):
    t = tablas()
    def leer(run, brazo, volcan):
        if (run, brazo, volcan) == ("2", "_s196_lab_p225", "Chaiten"):
            return None
        return lector(t)(run, brazo, volcan)
    problemas, _ = U.unir(man(), tmp_path / "s", leer=leer, trabajos=verdes)
    assert any("_s196_lab_p225 Chaiten: falta en t2" in p for p in problemas)


def test_brazo_con_claves_de_mas_o_de_menos(tmp_path):
    t = tablas()
    extra = {("1", "_s196_lab_p250", "Villarrica"): t[("1", "Villarrica")] + [rec("2026-03-10 07:00", sha="s1")]}
    problemas, _ = correr(tmp_path, t=t, por_brazo=extra)
    assert any("Villarrica: _s196_lab_p250 tiene 1 claves que el control no y le faltan 0" in p for p in problemas)
    menos = {("1", "_s196_lab_p250", "Villarrica"): t[("1", "Villarrica")][1:]}
    problemas, _ = U.unir(man(), tmp_path / "s2", leer=lector(t, menos), trabajos=verdes)
    assert any("Villarrica: _s196_lab_p250 tiene 0 claves que el control no y le faltan 1" in p for p in problemas)
    sz = {("1", "_s196_lab_sinzona", "Villarrica"): t[("1", "Villarrica")][1:]}
    problemas, _ = U.unir(man(), tmp_path / "s3", leer=lector(t, sz), trabajos=verdes)
    assert any("Villarrica: _s196_lab_sinzona tiene 0 claves" in p for p in problemas)


def test_manifiesto_mal_armado(tmp_path):
    casos = {
        "no aparece en el manifiesto": [dict(e, volcanes=[v for v in V if v != "Copahue"]) for e in man()],
        "no en 2026-03-01": [dict(man()[1])],
        "fuera de formato": [dict(man()[0], fin="2026-3-31"), man()[1]],
        "volcán desconocido": [dict(man()[0], volcanes=list(V) + ["Osorno"]), man()[1]],
        "ningún run del manifiesto lo cubre": [man()[0], dict(man()[1], volcanes=[v for v in V if v != "Lascar"]),
                                               dict(man()[1], run="3", etiqueta="t3", ini="2026-05-01",
                                                    fin="2026-05-31")],
        "posterior a fin": [dict(man()[0], ini="2026-03-31", fin="2026-03-01"), man()[1]],
    }
    for i, (texto, e) in enumerate(casos.items()):
        problemas, _ = U.unir(e, tmp_path / f"s{i}", leer=lector(tablas()), trabajos=verdes)
        assert any(texto in p for p in problemas), (texto, problemas[:3])
        assert not (tmp_path / f"s{i}").exists()


def test_fin_distinto_del_sellado(tmp_path):
    problemas, _ = correr(tmp_path, fin_esperado="2026-11-23")
    assert any("distinto del esperado 2026-11-23" in p for p in problemas)


def test_cli_sale_0_o_2(tmp_path, monkeypatch):
    m = tmp_path / "m.json"; m.write_text(json.dumps(man()), encoding="utf-8")
    monkeypatch.setattr(U, "leer_git", lector(tablas()))
    monkeypatch.setattr(U, "trabajos_gh", verdes)
    assert U.main([str(m), str(tmp_path / "s")]) == 0
    assert U.main([str(m), str(tmp_path / "s2"), "--fin-esperado", "2026-11-23"]) == 2


def test_manifiesto_real_valido():
    """El manifiesto del repo: 11 volcanes desde 2026-03-01, cada volcán y mes una sola vez, sin huecos."""
    m = json.loads((RAIZ / "experiments" / "_s196_lab_piso" / "MANIFIESTO_TANDAS.json").read_text(encoding="utf-8"))
    assert U.validar_manifiesto(m) == []
