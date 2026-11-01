#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador F3 (S155): ratios de magnitud POR NOCHE del auto-audit, para F3-05 y F3-06.

Pregunta 1: la replica del bloque de magnitud (auto_audit_weekly.py l. 365-440) se valida contra
aw.main() en la misma configuracion: mediana y n por volcan deben coincidir EXACTO (control de
instrumento; se imprime CONTROL OK/FALLA). Si no coinciden, nada de lo de abajo vale.
Pregunta 2: un volcan sin noches comunes sale n=0 (SIN DATO), no ratio 0.

Configuraciones:
  A) estado del repo al commit f3b414213 (run del 2026-10-14), hoy=2026-10-14, sin capa historica
     (el run fue anterior a #803): debe dar Tupungatito 0,647 con n=23.
  A') commit 0a3b4e3ac (run del 2026-10-12), hoy=2026-10-12: debe dar 0,707 con n=24.
  B) datos de hoy, referencia fresca, hoy=2026-10-19, por regimen (raices C0/K de simular_cron.py).
"""
import json
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw  # noqa: E402
import simular_cron as sc  # noqa: E402

aw.medir_falsas_ventana = lambda win: []   # la magnitud no depende de esto; ahorra node


def fijar_hoy(d):
    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc)
    aw.datetime = FakeDT


def ratios(raiz, cons, ocr, hist, hoy):
    win = ((hoy - timedelta(days=aw.WINDOW_DAYS)).isoformat(), hoy.isoformat())
    in_win = lambda dt: bool(dt) and win[0] <= dt[:10] <= win[1]  # noqa: E731
    coords = aw._coords_por_volcan()
    mir = defaultdict(float)
    alertas = aw.alertas_mirova(cons, ocr, hist)
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if not in_win(dt) or a["sensor_bucket"] not in aw.SENSORS:
            continue
        ll = coords.get(a["volcano"])
        if ll:
            try:
                o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
            except ValueError:
                o = None
            if o and aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o):
                continue
        k = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
    ours = defaultdict(lambda: {"dash": [], "f5": [], "pub_sensor": []})
    for vol in aw.VOLS:
        d = json.load(open(Path(raiz) / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            dt = r.get("datetime_utc")
            if not in_win(dt):
                continue
            b = aw.our_bucket(r.get("sensor", ""))
            if b is None:
                continue
            pc = r.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cd = pc.get("centroid_dist_km")
            if (0 < vrp <= aw.CAP) and (cd is not None and cd <= aw.INNER[vol]):
                dc = r.get("distance_class")
                if not dc or dc == "summit":
                    ours[(vol, b, dt[:10])]["dash"].append(vrp)
    out = defaultdict(list)
    for (vol, s, date), mv in mir.items():
        o = ours.get((vol, s, date))
        if o and o["dash"] and mv > 0:
            out[vol].append((date, s, max(o["dash"]) / mv, len(o["dash"])))
    return out


def raiz_commit(sha):
    raiz = AQUI / f"raiz_{sha}"
    dd = raiz / "data/mirova_equivalent"
    dd.mkdir(parents=True, exist_ok=True)
    for vol in aw.VOLS:
        txt = subprocess.run(["git", "show", f"{sha}:data/mirova_equivalent/{vol}.json"], cwd=REPO,
                             capture_output=True, check=True).stdout
        d = json.loads(txt)
        d["records"] = [r for r in d["records"] if (r.get("datetime_utc") or "") >= "2026-08-01"]
        json.dump(d, open(dd / f"{vol}.json", "w", encoding="utf-8"))
    ref = raiz / "ref"
    ref.mkdir(exist_ok=True)
    for n in ["registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"]:
        (ref / n).write_bytes(subprocess.run(["git", "show", f"{sha}:data/mirova_reference/mirova_v1_snapshot/{n}"],
                                             cwd=REPO, capture_output=True, check=True).stdout)
    return raiz, str(ref / "registro_vrp_consolidado.csv"), str(ref / "registro_vrp_ocr.csv")


def control(nombre, raiz, cons, ocr, hist, hoy, res):
    fijar_hoy(hoy)
    lat = sc.correr(nombre, raiz=raiz, cons=cons, ocr=ocr, hist=hist)
    ok = True
    for v, m in lat["magnitud_ratio_by_vol"].items():
        mio = res.get(v, [])
        med = round(statistics.median([x[2] for x in mio]), 3) if mio else None
        if med != m["ratio_mediano"] or len(mio) != m["n_noches"]:
            ok = False
            print("  DIFERENCIA", v, m, med, len(mio))
    print(f"CONTROL {nombre}: {'OK' if ok else 'FALLA'}")
    return ok


def main():
    resumen = {}
    for sha, hoy in [("f3b414213", datetime(2026, 10, 14).date()), ("0a3b4e3ac", datetime(2026, 10, 12).date())]:
        raiz, cons, ocr = raiz_commit(sha)
        res = ratios(raiz, cons, ocr, None, hoy)
        sc.rmu.cargar_referencia_unificada.__defaults__ = (Path(cons), Path(ocr), None, None)
        ok = control("commit_" + sha, raiz, cons, ocr, None, hoy, res)
        t = res["Tupungatito"]
        resumen[sha] = {"control_ok": ok, "tupun_n": len(t),
                        "tupun_mediana": round(statistics.median([x[2] for x in t]), 3)}
    hoy = datetime(2026, 10, 19).date()
    for reg in ["C0", "K"]:
        raiz = AQUI / f"raiz_{reg}"
        res = ratios(raiz, sc.CONS_F, sc.OCR_F, str(sc.HIST_COMB), hoy)
        ok = control("hoy_" + reg, raiz, sc.CONS_F, sc.OCR_F, str(sc.HIST_COMB), hoy, res)
        resumen["hoy_" + reg] = {"control_ok": ok}
        for vol in ["Tupungatito", "NevadosDeChillan", "PuyehueCordonCaulle"]:
            t = sorted(res.get(vol, []))
            antes = [x[2] for x in t if x[0] < "2026-09-12"]
            desp = [x[2] for x in t if x[0] >= "2026-09-12"]
            resumen["hoy_" + reg][vol] = {
                "n": len(t), "mediana": round(statistics.median([x[2] for x in t]), 3) if t else None,
                "n_antes_0912": len(antes), "med_antes_0912": round(statistics.median(antes), 3) if antes else None,
                "n_desde_0912": len(desp), "med_desde_0912": round(statistics.median(desp), 3) if desp else None,
                "por_sensor": {s: (len([x for x in t if x[1] == s]),
                                   round(statistics.median([x[2] for x in t if x[1] == s]), 3)
                                   if [x for x in t if x[1] == s] else None) for s in aw.SENSORS},
                "noches": [(x[0], x[1], round(x[2], 3), x[3]) for x in t]}
    json.dump(resumen, open(AQUI / "magnitud_por_noche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k, v in resumen.items():
        print(k, json.dumps({kk: (vv if kk not in ("Tupungatito", "NevadosDeChillan", "PuyehueCordonCaulle")
                                  else {a: b for a, b in vv.items() if a != "noches"}) for kk, vv in v.items()},
                            ensure_ascii=False))


if __name__ == "__main__":
    main()
