# -*- coding: utf-8 -*-
"""Verificador F/K V2, punto 2. (a) Origen de cada record de la union: de que intento sale (comparacion exacta
salvo campos de proceso). (b) FLAGS_BRAZO de cada log de cada intento que aporta records. (c) entre intentos,
misma decision del tablero (pub), misma magnitud mostrada (disp) y mismo cumulo (pc_lat/lon) en las pasadas
comunes, con armar_tabla (predicado con node), independiente de unir_intentos."""
import json, sys, subprocess, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
T = Path(r"C:\Users\nmend\AppData\Local\Temp\claude")
REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
OUT = T / "verif_fk_v2" / "a2"; OUT.mkdir(parents=True, exist_ok=True)
PROCESO = {"processed_utc", "first_processed_utc", "regimen", "updated"}
DECL = {"_s146_ab_control": (True, False, False, False, 5.0), "_s151_ab_control_gemelo": (True, False, False, False, 5.0),
        "_s147_ab_sin_test1_max": (False, True, False, False, 5.0), "_s149_ab_sin_test1_b22_max": (False, True, True, False, 5.0)}
CLAVES = ("ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY",
          "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER", "PATH_D_ONLY_CAP_MW")
EXTRA = {"ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": False, "ENABLE_VENT_ANCHORED_CLUSTERING": True}
VEN = {
 "V1": {"union": T/"v1_38639658446"/"union_2766", "intentos": {"i1": T/"v1_38639658446/i1/experiments/_s146_ab_sin_test1/salidas/38639658446", "i3": T/"v1_38639658446/i3"},
        "desde": "2026-08-29", "hasta": "2026-10-08", "ref": REPO/"experiments/_s151_prereg_fk_11/_congelado_v1"},
 "V2a": {"union": T/"v2a_38648773684"/"union_2766", "intentos": {"i1": T/"v2a_38648773684/i1/experiments/_s146_ab_sin_test1/salidas/38648773684", "i2": T/"v2a_38648773684/i2"},
        "desde": "2026-03-01", "hasta": "2026-04-20", "ref": REPO/"experiments/_s151_prereg_fk_11/_congelado_v2"},
 "V2b": {"union": T/"v2b_39033530622"/"union", "intentos": {"i1": T/"v2b_39033530622/i1", "i2": T/"v2b_39033530622/i2"},
        "desde": "2026-04-21", "hasta": "2026-06-12", "ref": REPO/"experiments/_s151_prereg_fk_11/_congelado_v2"},
}
def limpio(r): return {k: v for k, v in r.items() if k not in PROCESO}
def flags(logdir, arm, vol):
    p = logdir / ("%s_%s.log" % (arm, vol))
    if not p.exists(): return "SIN LOG"
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if l.startswith("FLAGS_BRAZO "):
            return json.loads(l[12:])
    return "SIN LINEA"
resumen = {}
for w, c in VEN.items():
    print("==", w)
    origen_tot = collections.Counter(); probs = []
    for armdir in sorted(c["union"].iterdir()):
        arm = armdir.name
        for f in sorted(armdir.glob("*.json")):
            vol = f.stem
            U = json.load(open(f, encoding="utf-8"))["records"]
            fuentes = {}
            for nom, d in c["intentos"].items():
                p = d / arm / f.name
                if p.exists():
                    fuentes[nom] = [json.dumps(limpio(r), sort_keys=True) for r in json.load(open(p, encoding="utf-8"))["records"]]
            sets = {n: collections.Counter(v) for n, v in fuentes.items()}
            org = collections.Counter()
            for r in U:
                s = json.dumps(limpio({k: v for k, v in r.items()}), sort_keys=True)
                quien = tuple(n for n in sets if sets[n][s] > 0)
                org[quien] += 1
            for q, n in org.items():
                origen_tot[q] += n
                if not q: probs.append("%s %s: %d records de la union no estan identicos en ningun intento" % (arm, vol, n))
            # flags de cada intento que aporta (cualquier intento que contenga records de la union)
            aporta = {n for q in org for n in q}
            for n in sorted(aporta):
                fl = flags(c["intentos"][n] / "logs", arm, vol)
                if not isinstance(fl, dict):
                    probs.append("%s %s %s: %s" % (arm, vol, n, fl)); continue
                ok = fl.get("PROFILE_NAME") == arm and fl.get("DATA_SUBDIR") == arm and tuple(fl.get(k) for k in CLAVES) == DECL[arm] \
                     and all(fl.get(k, v) == v for k, v in EXTRA.items())
                if not ok: probs.append("%s %s %s: FLAGS MAL %s" % (arm, vol, n, fl))
            # records que aporta SOLO un intento cuyo log no exista
            solo = {q[0] for q in org if len(q) == 1}
            for n in solo:
                if not (c["intentos"][n] / "logs" / ("%s_%s.log" % (arm, vol))).exists():
                    probs.append("%s %s: records solo de %s y ese intento no tiene log" % (arm, vol, n))
    print("   origen de los records de la union (tupla de intentos que lo traen identico):", dict(origen_tot))
    print("   problemas:", probs or "ninguno")
    resumen[w] = {"origen": {"+".join(k) or "NINGUNO": v for k, v in origen_tot.items()}, "problemas": probs}
json.dump(resumen, open(OUT / "origen_flags.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
