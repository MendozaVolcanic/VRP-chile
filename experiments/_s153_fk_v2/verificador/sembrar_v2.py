# -*- coding: utf-8 -*-
"""Siembras sobre los datos REALES de V2 (uniones V2a union_2766 y V2b union), en copias. Casos:
  lascar375   K oculta una protegida A de Lascar VIIRS375 (2026-05) -> esperado P1 PENDIENTE (sin gemelo), global PENDIENTE
  lascar375r  igual + --repeticion con la misma siembra -> esperado VETADO, NO CUMPLE (veto)
  lascarmodis K oculta la protegida MODIS de Lascar 2026-04-20 01:30 (sin cumulo, VRP 0) -> PENDIENTE
  marzo375    K oculta una protegida A de Lascar VIIRS375 de marzo -> no decide (A119 b): CUMPLE
  pierde375   K recibe el record de C0 (triggered_test1 False) en los negativos limpios VIIRS375 que C0 publica -> PIERDE
  cable       el log de K Lascar en V2b dice banda 22 false -> K mal cableado, INDECIDIBLE
"""
import sys, json, shutil, subprocess, copy
from pathlib import Path
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E
TT = Path(r"C:\Users\nmend\AppData\Local\Temp\claude")
SRC = {"a": TT / "v2a_38648773684" / "union_2766", "b": TT / "v2b_39033530622" / "union"}
LOGS = {"a": TT / "v2a_38648773684" / "i2" / "logs", "b": TT / "v2b_39033530622" / "logs_union"}
V = TT / "verif_fk_v2"
caso = sys.argv[1]
T = json.load(open(V / "rep" / "tmp_v2" / "t_C0_K.json", encoding="utf-8"))["pasadas"]
def clave(v, r): return "|".join((v, E.bp.bucket(r.get("sensor")) or "", r.get("datetime_utc", "")[:16]))
def mitad(k): return "a" if k.split("|")[2][:10] <= "2026-04-20" else "b"
dst = V / ("s2_" + caso)
if dst.exists(): shutil.rmtree(dst)
for h in "ab": shutil.copytree(SRC[h], dst / h)
logs = dict(LOGS)
mod = {}
def doc(h, n, v):
    if (h, n, v) not in mod: mod[(h, n, v)] = json.load(open(SRC[h] / E.BRAZOS[n] / (v + ".json"), encoding="utf-8"))
    return mod[(h, n, v)]
def ocultar(k, mecanismo="far"):
    v = k.split("|")[0]; c = 0
    for r in doc(mitad(k), "K", v)["records"]:
        if clave(v, r) == k:
            if mecanismo == "far": r["distance_class"] = "far"
            else:
                r["primary_cluster"] = None; r["vrp_mw"] = 0.0; r["vrp_mir_mw"] = 0.0; r["f5_core_vrp_mw"] = None
                r["discarded_reason"] = "sembrado_verificador"
            c += 1
    return c
cambios = 0; extra = []
if caso in ("lascar375", "lascar375r"):
    cambios = ocultar("Lascar|VIIRS375|" + " ".join(sys.argv[2:]))
    if caso == "lascar375r": extra = ["--repeticion", "REP"]
elif caso == "lascarmodis":
    cambios = ocultar("Lascar|MODIS|2026-04-20 01:30", "sin")
elif caso == "marzo375":
    cambios = ocultar("Lascar|VIIRS375|" + " ".join(sys.argv[2:]))
elif caso == "pierde375":
    ks = {k for k, v in T.items() if len(v) == 2 and k.split("|")[1] == "VIIRS375" and v["control"]["lab"] == "neg_limpio"
          and v["control"]["pub"] and not v["brazo"]["pub"]}
    for k in ks:
        v = k.split("|")[0]; h = mitad(k)
        c0 = {clave(v, r): r for r in json.load(open(SRC[h] / E.BRAZOS["C0"] / (v + ".json"), encoding="utf-8"))["records"]}
        recs = doc(h, "K", v)["records"]
        for i, r in enumerate(recs):
            if clave(v, r) == k:
                nr = copy.deepcopy(c0[k]); nr["triggered_test1"] = False; recs[i] = nr; cambios += 1
elif caso == "cable":
    nl = dst / "logs_b"; shutil.copytree(LOGS["b"], nl); logs["b"] = nl
    p = nl / "_s149_ab_sin_test1_b22_max_Lascar.log"
    t = p.read_text(encoding="utf-8"); t2 = t.replace('"ENABLE_MODIS_B22_PRIMARY": true', '"ENABLE_MODIS_B22_PRIMARY": false', 1)
    cambios = int(t != t2); p.write_text(t2, encoding="utf-8")
for (h, n, v), d in mod.items():
    json.dump(d, open(dst / h / E.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
print("caso", caso, "modificados", cambios)
out = V / ("s2_" + caso + ".json")
cmd = [sys.executable, str(RAIZ / "experiments" / "_s151_prereg_fk_11" / "evaluar_fk.py"), "--ventana", "V2",
       "--raiz", str(dst / "a"), "--raiz", str(dst / "b"), "--logs", str(logs["a"]), "--logs", str(logs["b"]),
       "--ruido-de", str(V / "rep" / "v1.json"), "--out", str(out), "--tmp", str(dst / "_tmp")]
if extra:
    # la repeticion necesita los dos brazos fusionados: se arma primero la fusion corriendo una vez sin repeticion
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    cmd += ["--repeticion", str(dst / "_tmp" / "fusion")]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
(V / ("s2_" + caso + ".log")).write_text(p.stdout + p.stderr, encoding="utf-8")
r = json.load(open(out, encoding="utf-8"))
print("global", r["global"]["K"], "| controles", r["controles_ok"], "cableado", r["cableado"])
for kk, vv in sorted(r["veredicto"].items()):
    if kk.split("|")[1] == "K" and (kk.endswith("|A") or kk.startswith("P3") or kk.startswith("P4")): print("  ", kk, vv)
for kk in ("C0|VIIRS375|A", "K|VIIRS375|A"): print("   suma", kk, r["suma"][kk])
c = subprocess.run([sys.executable, str(RAIZ / "experiments" / "_s151_prereg_fk_11" / "evaluar_fk.py"), "--combinar", str(V / "rep" / "v1.json"), str(out)],
                   capture_output=True, text=True, encoding="utf-8")
print("   combinado:", [l.strip() for l in c.stdout.splitlines() if l.strip().startswith("K lectura A") or "regla SN       K lectura A" in l])
shutil.rmtree(dst)
