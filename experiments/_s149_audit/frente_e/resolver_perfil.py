# Frente E S149: resuelve el perfil como lo hace el codigo (A89) y lo vuelca a JSON.
# Pregunta 1: si el perfil estuviera roto, lo veria? Si: comparo contra el perfil base sin VRP_PROFILE.
# Pregunta 2: si el instrumento estuviera muerto? El control positivo es DATA_SUBDIR/PROFILE_NAME distinto.
import os, sys, json, io, importlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pipeline.profile as p
out = {k: getattr(p, k) for k in sorted(dir(p)) if k.isupper()}
def ser(v):
    try:
        json.dumps(v); return v
    except Exception:
        return repr(v)
out = {k: ser(v) for k, v in out.items()}
name = os.environ.get("VRP_PROFILE", "SIN_VAR")
json.dump(out, open(f"experiments/_s149_audit/frente_e/perfil_{name}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(name, len(out))
for k, v in out.items():
    s = json.dumps(v, ensure_ascii=False)
    print(f"{k} = {s[:150]}")
