# -*- coding: utf-8 -*-
"""Port en Python de mirovaEqVrp (frontend/index.html:1162) para contar lo que el tablero publica antes y despues,
y prueba sintetica del tope del 2 % quitando un sensor entero de un trozo. Read-only."""
import json, sys, io, copy
from collections import Counter
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from scripts.reemplazar_ventana_reproceso import reemplazar_ventana
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[5]  # raiz del repo
DESDE, HASTA, P = "2025-02-15", "2026-09-17", "_s154_reproc_k_historico"
cfg = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))
INNER = {v["name"]: v.get("inner_radius_km", 10) for v in cfg["volcanoes"]}


def eqvrp(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") if r.get("vrp_mw") is not None else (r.get("vrp_mir_mw") or 0)
        return 0 if v > 50000 else v
    if r.get("distance_class") and r.get("distance_class") != "summit":
        return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


vols = sys.argv[1:]
for v in vols:
    inner = INNER[v]
    op = json.load(open(RAIZ / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))
    re_ = json.load(open(RAIZ / "data/_s154_reproc_k_historico" / f"{v}.json", encoding="utf-8"))
    store, inf = reemplazar_ventana(op, re_, DESDE, HASTA, P)
    en = lambda r: DESDE <= r["datetime_utc"][:10] <= HASTA
    pub_antes = [r for r in op["records"] if en(r) and eqvrp(r, inner) > 0]
    pub_desp = [r for r in store["records"] if en(r) and eqvrp(r, inner) > 0]
    islas = [r for r in store["records"] if en(r) and not (r.get("regimen") or {}).get("codigo_sha")]
    islas_pub = [(r["datetime_utc"], r["sensor"], round(eqvrp(r, inner), 3)) for r in islas if eqvrp(r, inner) > 0]
    fuera_pub_c0 = [(r["datetime_utc"], r["sensor"], round(eqvrp(r, inner), 3)) for r in store["records"]
                    if r["datetime_utc"][:10] > HASTA and not (r.get("regimen") or {}).get("codigo_sha") and eqvrp(r, inner) > 0]
    fuera_c0 = [r for r in store["records"] if r["datetime_utc"][:10] > HASTA and not (r.get("regimen") or {}).get("codigo_sha")]
    print(f"== {v} (inner {inner}): publicadas en ventana antes {len(pub_antes)} -> despues {len(pub_desp)}; "
          f"islas C0 en ventana {len(islas)} (publicadas {len(islas_pub)}): {islas_pub}")
    print(f"   C0 sin marca despues de la ventana: {len(fuera_c0)} (publicadas {fuera_pub_c0})")
    # sintetico: quitar VIIRS_SNPP del trozo 2025-07-13..2025-08-18 (trozo 5 de split_window)
    re2 = copy.deepcopy(re_)
    n0 = len(re2["records"])
    re2["records"] = [r for r in re2["records"]
                      if not (r["sensor"] in ("VIIRS_SNPP",) and "2025-07-13" <= r["datetime_utc"][:10] <= "2025-08-18")]
    _, inf2 = reemplazar_ventana(op, re2, DESDE, HASTA, P)
    frac = inf2["solo_operacional"] / inf2["operacional_en_ventana"]
    print(f"   SINTETICO sin VIIRS_SNPP en 2025-07-13..08-18: quitados {n0-len(re2['records'])}, solo_op "
          f"{inf2['solo_operacional']} de {inf2['operacional_en_ventana']} = {frac:.4f} -> {'REHUSADO' if frac > 0.02 else 'PASA'}")
    re3 = copy.deepcopy(re_)
    re3["records"] = [r for r in re3["records"]
                      if not (r["sensor"] in ("VIIRS_SNPP", "VIIRS_SNPP_750") and "2025-07-13" <= r["datetime_utc"][:10] <= "2025-08-18")]
    _, inf3 = reemplazar_ventana(op, re3, DESDE, HASTA, P)
    frac = inf3["solo_operacional"] / inf3["operacional_en_ventana"]
    print(f"   SINTETICO sin SNPP 375+750 en ese trozo: solo_op {inf3['solo_operacional']} = {frac:.4f} -> "
          f"{'REHUSADO' if frac > 0.02 else 'PASA'}")
    # round trip: el archivo en disco es json.dumps(indent=2)?
    raw = (RAIZ / "data/mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8")
    print(f"   round-trip byte a byte del operacional con json.dump(indent=2): {json.dumps(op, indent=2) == raw} "
          f"(termina en newline: {raw.endswith(chr(10))})")
