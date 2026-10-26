"""F3: reproducir el 0,647x (n=23) de Tupungatito de latest.json del 2026-10-14 y el 0,707 (n=24) del
2026-10-12 con el corpus y la referencia DE ESOS COMMITS (git show a D:\vrp-trabajo\temporales\frente_3),
y la lógica de magnitud de scripts/auto_audit_weekly.py de hoy. P1 (control de instrumento): si no reproduce
0,647/23 con el corpus del 10-14, este script no mide lo mismo que el audit y no sirve para atribuir.
P2: imprime n."""
import sys, os, json, statistics
from collections import defaultdict
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa
TMP = r"D:\vrp-trabajo\temporales\frente_3"
def ratio(commit, win, con_hist):
    T = os.path.join(TMP, "c_" + commit)
    h = os.path.join(T, "hist.csv")
    al = aw.alertas_mirova(os.path.join(T, "cons.csv"), os.path.join(T, "ocr.csv"), h if (con_hist and os.path.exists(h)) else None)
    coords = aw._coords_por_volcan(); vol = "Tupungatito"
    mir = defaultdict(float)
    for a in al:
        dt = a["fecha_utc"] or ""
        if a["volcano"] != vol or not (win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS: continue
        o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        if aw.es_pasada_diurna_descartada(a["sensor_bucket"], *coords[vol], o): continue
        k = (a["sensor_bucket"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0)
    ours = defaultdict(list)
    for r in json.load(open(os.path.join(T, "Tupungatito.json"), encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc") or ""
        if not (win[0] <= dt[:10] <= win[1]): continue
        b = aw.our_bucket(r.get("sensor", "")); pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0; cd = pc.get("centroid_dist_km"); dc = r.get("distance_class")
        if b and 0 < v <= aw.CAP and cd is not None and cd <= aw.INNER[vol] and (not dc or dc == "summit"):
            ours[(b, dt[:10])].append(v)
    rs = sorted((k, max(ours[k]) / m) for k, m in mir.items() if ours.get(k) and m > 0)
    return len(rs), round(statistics.median([x for _, x in rs]), 3), rs
for commit, win in (("0a3b4e3ac", ("2026-08-13", "2026-10-12")), ("f3b414213", ("2026-08-15", "2026-10-14"))):
    for ch in (True, False):
        n, med, rs = ratio(commit, win, ch)
        print(commit, win, "historico" if ch else "sin_historico", "n", n, "mediana", med)
    print("   noches:", [(k[1], round(x, 3)) for k, x in rs])
