"""Frente G (S146): vuelca TODOS los atributos publicos de pipeline.profile
con el perfil mirova_equivalent. Solo lectura."""
import os, sys, json, io
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import pipeline.profile as p
out = {}
for k in sorted(dir(p)):
    if k.startswith("_"): continue
    v = getattr(p, k)
    if callable(v) or type(v).__name__ == "module": continue
    try:
        json.dumps(v); out[k] = v
    except Exception:
        out[k] = repr(v)
dst = os.path.join(os.path.dirname(__file__), "perfil_efectivo.json")
json.dump(out, open(dst, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(out))
for k, v in out.items():
    s = json.dumps(v, ensure_ascii=False)
    print(k, "=", s[:150])
