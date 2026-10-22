"""V0a (F1-H8): los proxies que S158 cito (max t_max_k V750, records con t_bg < 220 K) recomputados con loader propio
sobre SHA_MAIN; y si existe algun campo de M15 persistido. Pregunta 1: si el corpus hubiera cambiado, los numeros
cambian. Pregunta 2: control = el conteo de records V750 debe dar 28.581 (ya medido por v02)."""
import glob, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:/vrp-trabajo/temporales/s160_audit/main/data/mirova_equivalent"
VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
recs = []
for v in VOLS:
    recs += [r for r in json.load(open(os.path.join(ROOT, v + ".json"), encoding="utf-8"))["records"] if str(r.get("sensor","")).endswith("_750")]
print("V750 Tier A:", len(recs))
tm = [r["t_max_k"] for r in recs if r.get("t_max_k") is not None]; tb = [r["t_bg_k"] for r in recs if r.get("t_bg_k") is not None]
print("t_max_k max:", max(tm), "n:", len(tm), "; t_bg_k min:", min(tb), "; t_bg < 220 K:", sum(1 for x in tb if x < 220), "de", len(tb))
keys = set(); [keys.update(r.keys()) for r in recs]
print("campos con m15/tir en el nombre:", sorted(k for k in keys if "15" in k or "tir" in k.lower()))
print("campos de saturacion:", sorted(k for k in keys if "sat" in k.lower()))
