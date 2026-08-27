# -*- coding: utf-8 -*-
"""F70 brazo C — evaluacion contra el criterio pre-registrado. Fuente de verdad (S91).

Uso: python experiments/_s124_f70/02_brazo_c.py
Requiere: data/_s124_kernelbg_ab/ (git checkout 039f4191d -- data/_s124_kernelbg_ab)
"""
import collections, csv, io, json, statistics as st, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Isluga", "Tupungatito", "NevadosDeChillan", "Copahue", "Llaima"]
ALIAS = {"NevadosDeChillan": "Nevados de Chillan"}
INI, FIN = "2026-06-25", "2026-08-24"
BANDA = (0.7, 1.4)          # banda de la MEDIANA (no la de una deteccion suelta)


def ground_truth():
    """Noches con ALERTA VIIRS375 publicada por MIROVA, del consolidado."""
    gt = collections.defaultdict(dict)
    with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            v, f = r.get("Volcan"), (r.get("Fecha_Satelite_UTC") or "")[:10]
            if not v or not (INI <= f <= FIN):
                continue
            if "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            try:
                x = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if x > 0:
                gt[v][f] = max(gt[v].get(f, 0), x)
    return gt


def serie(path):
    """VRP summit por noche, VIIRS375 — el mismo campo que lee el dashboard (A10)."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for r in d["records"]:
        f, s = (r.get("datetime_utc") or "")[:10], r.get("sensor") or ""
        if not (INI <= f <= FIN) or "VIIRS" not in s or "750" in s:
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v <= 0 or r.get("distance_class") != "summit":
            continue
        out[f] = max(out.get(f, 0), v)
    return out


if __name__ == "__main__":
    gt = ground_truth()
    print(f"{'volcan':20s} {'n':>4s} {'control':>8s} {'brazo C':>8s} {'mov':>7s}")
    print("-" * 52)
    for v in VOLS:
        m = gt.get(ALIAS.get(v, v), {})
        b, c = serie(ROOT / f"data/mirova_equivalent/{v}.json"), serie(ROOT / f"data/_s124_kernelbg_ab/{v}.json")
        rb = [b[f] / m[f] for f in m if f in b]
        rc = [c[f] / m[f] for f in m if f in c]
        if not rb or not rc:
            print(f"{v:20s} {'-':>4s}   (sin noches cruzadas con MIROVA)")
            continue
        mb, mc = st.median(rb), st.median(rc)
        print(f"{v:20s} {len(rb):4d} {mb:8.2f} {mc:8.2f} {100*(mc-mb)/mb:+6.0f}%")
    print(f"\nCriterio primario: los sub-reportadores deben entrar en {BANDA}.")
    print("Lascar 0.47 -> 0.58: se mueve bien pero NO entra. Brazo C: NO ADOPTAR.")
