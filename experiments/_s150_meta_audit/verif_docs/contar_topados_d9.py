"""Cuenta records con magnitud exactamente igual al tope D9 (5,0 MW) en data/mirova_equivalent/*.json.
Verificador S150 meta-auditoria. Solo lectura."""
import glob, json, os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CAP = 5.0
def eq(v):
    return isinstance(v, (int, float)) and abs(v - CAP) < 1e-9
tot = 0; fechas = []
c_pc = Counter(); c_rec = Counter(); c_f5 = Counter(); c_any = Counter(); c_any_summit = Counter()
vol_any = Counter(); mes_any = Counter(); over = 0
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    vol = os.path.basename(f)[:-5]
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print("ERR", f, e); continue
    for r in d.get("records", []):
        tot += 1
        dt = r.get("datetime_utc") or ""
        fechas.append(dt)
        pc = r.get("primary_cluster") or {}
        s = r.get("sensor", "?")
        a, b, c = eq(r.get("vrp_mw")), eq(pc.get("vrp_mw")), eq(r.get("f5_core_vrp_mw"))
        pv = pc.get("vrp_mw")
        if isinstance(pv, (int, float)) and pv > CAP + 1e-9: over += 1
        if a: c_rec[s] += 1
        if b: c_pc[s] += 1
        if c: c_f5[s] += 1
        if a or b or c:
            c_any[s] += 1; vol_any[vol] += 1; mes_any[dt[:7]] += 1
            if r.get("distance_class") == "summit": c_any_summit[s] += 1
fechas = [x for x in fechas if x]
print("records totales:", tot, "ventana:", min(fechas), "a", max(fechas))
print("pc.vrp_mw > 5,0:", over)
print("record.vrp_mw == 5,0:", sum(c_rec.values()), dict(c_rec))
print("pc.vrp_mw == 5,0:", sum(c_pc.values()), dict(c_pc))
print("f5_core_vrp_mw == 5,0:", sum(c_f5.values()), dict(c_f5))
print("cualquiera de los tres == 5,0:", sum(c_any.values()), dict(c_any))
print("  de esos, distance_class summit:", sum(c_any_summit.values()), dict(c_any_summit))
print("por volcan:", dict(vol_any.most_common()))
print("por mes:", dict(sorted(mes_any.items())))
