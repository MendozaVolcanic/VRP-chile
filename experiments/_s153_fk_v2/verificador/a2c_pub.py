# -*- coding: utf-8 -*-
"""Entre intentos del MISMO brazo: decision del tablero (pub), disp y cumulo en pasadas comunes (armar_tabla)."""
import json, sys, subprocess, math
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from a2_intentos import VEN, REPO, OUT
ARMAR = REPO / "experiments/_s149_prereg_invierno/armar_tabla.py"
res = {}
for w, c in VEN.items():
    (a, da), (b, db) = list(c["intentos"].items())
    ref = c["ref"]
    for armdir in sorted(c["union"].iterdir()):
        arm = armdir.name
        out = OUT / ("pub_%s_%s.json" % (w, arm))
        cmd = [sys.executable, str(ARMAR), "--control", str(da / arm), "--brazo", str(db / arm), "--cons", str(ref / "registro_vrp_consolidado.csv"),
               "--ocr", str(ref / "registro_vrp_ocr.csv"), "--desde", c["desde"], "--hasta", c["hasta"], "--out", str(out),
               "--historico", str(ref / "consolidado_filas_perdidas.csv"), "--respaldo", str(ref / "respaldo_20260408.csv")]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode: print(r.stderr[-2000:]); continue
        P = json.loads(out.read_text(encoding="utf-8"))["pasadas"]
        com = {k: v for k, v in P.items() if len(v) == 2}
        dpub = [k for k, v in com.items() if v["control"]["pub"] != v["brazo"]["pub"]]
        ddisp = [k for k, v in com.items() if v["control"]["pub"] and v["brazo"]["pub"] and not (
            (v["control"]["disp"] is None and v["brazo"]["disp"] is None) or
            (v["control"]["disp"] is not None and v["brazo"]["disp"] is not None and math.isclose(v["control"]["disp"], v["brazo"]["disp"], rel_tol=1e-6, abs_tol=1e-9)))]
        dpc = [k for k, v in com.items() if (v["control"]["pc_lat"], v["control"]["pc_lon"]) != (v["brazo"]["pc_lat"], v["brazo"]["pc_lon"])]
        print("%s %-28s %s vs %s comunes %5d | pub distinto %d %s | disp distinto %d %s | cumulo distinto %d %s" % (
            w, arm, a, b, len(com), len(dpub), dpub[:3], len(ddisp), ddisp[:3], len(dpc), dpc[:3]))
        res["%s|%s" % (w, arm)] = {"comunes": len(com), "pub": dpub, "disp": ddisp, "pc": dpc}
json.dump(res, open(OUT / "pub_entre_intentos.json", "w", encoding="utf-8"), indent=1)
