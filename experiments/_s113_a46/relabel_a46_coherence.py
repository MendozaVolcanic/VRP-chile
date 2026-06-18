# -*- coding: utf-8 -*-
"""S113 #3 — Relabel post-hoc del guard de coherencia A46 sobre los JSON existentes.

POR QUÉ: el guard nuevo en store.py (pre-s113-a46-coherence-guard) corrige NRT
forward, pero los records ya escritos conservan la etiqueta incoherente. Este
relabel aplica EXACTAMENTE el mismo predicado del guard de forma determinista
sobre data/mirova_equivalent/*.json — NO re-fetchea granules ni re-corre cluster
selection (A18-safe: solo cambia el campo de clasificación visual distance_class).

Predicado (idéntico a pipeline/store.py): distance_class=="summit" AND
primary_cluster.vrp_mw>0 AND primary_cluster.centroid_dist_km > inner_radius_km
→ distance_class="far" + diag_a46_relabel="summit_to_far_pc_beyond_inner".

inner_radius_km se lee de volcanoes.yaml (fuente de verdad).

Uso:
    python experiments/_s113_a46/relabel_a46_coherence.py          # dry-run (default)
    python experiments/_s113_a46/relabel_a46_coherence.py --apply  # escribe los JSON
"""
import io
import json
import os
import sys

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
VOLC_YAML = os.path.join(ROOT, "volcanoes.yaml")

APPLY = "--apply" in sys.argv


def load_inner_radii():
    with open(VOLC_YAML, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out = {}
    for v in cfg["volcanoes"]:
        out[v["name"]] = v.get("inner_radius_km")
    return out


def main():
    inner = load_inner_radii()
    total = 0
    changed_records = []
    for name, ir in sorted(inner.items()):
        path = os.path.join(DATA, name + ".json")
        if not os.path.exists(path):
            continue
        if ir is None:
            continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        n_changed = 0
        for r in d.get("records", []):
            if r.get("distance_class") != "summit":
                continue
            pc = r.get("primary_cluster") or {}
            cd = pc.get("centroid_dist_km")
            v = pc.get("vrp_mw") or 0
            if v > 0 and cd is not None and cd > ir:
                changed_records.append(
                    (name, r.get("datetime_utc"), r.get("sensor"),
                     round(cd, 2), round(v, 2), r.get("final_hotspot_source"))
                )
                if APPLY:
                    r["distance_class"] = "far"
                    r["diag_a46_relabel"] = "summit_to_far_pc_beyond_inner"
                n_changed += 1
        total += n_changed
        if n_changed and APPLY:
            # Igualar EXACTO el formato de store.py (json.dump(store, f, indent=2),
            # ensure_ascii default True) → diff mínimo (solo las líneas cambiadas).
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)

    mode = "APPLIED" if APPLY else "DRY-RUN (usar --apply para escribir)"
    print(f"=== Relabel A46 coherence — {mode} ===")
    print(f"records summit->far: {total}")
    for rec in changed_records:
        print(f"  {rec[0]:20s} {rec[1]} {rec[2]:18s} pc.cdist={rec[3]:6.2f} "
              f"pc.vrp={rec[4]:7.2f} src={rec[5]}")


if __name__ == "__main__":
    main()
