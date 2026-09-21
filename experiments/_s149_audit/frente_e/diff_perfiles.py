# Frente E S149: diferencia EFECTIVA (desde pipeline.profile, A89) de cada perfil candidato a "literal" contra mirova_equivalent.
# P1: si un flag del YAML no llegara al modulo, se veria? Si: aparece ausente del diff. P2: control positivo = DATA_SUBDIR siempre difiere.
import subprocess, json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
perfiles = sys.argv[1:]
def res(name):
    env = dict(os.environ, VRP_PROFILE=name, PYTHONPATH=".")
    code = "import pipeline.profile as p, json; print(json.dumps({k: repr(getattr(p,k)) for k in dir(p) if k.isupper() and k not in ('VALID_PROFILES',)}))"
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    if r.returncode: return {"ERROR": r.stderr[-300:]}
    return json.loads(r.stdout.strip().splitlines()[-1])
base = res("mirova_equivalent")
for n in perfiles:
    d = res(n)
    print("===", n)
    for k in sorted(set(base) | set(d)):
        if base.get(k) != d.get(k): print(f"  {k}: {base.get(k)} -> {d.get(k)}")
