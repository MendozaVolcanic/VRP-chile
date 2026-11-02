"""VS34 V-3: constantes resueltas de pipeline.profile (A89: se lee el modulo, no el YAML) para sombra_34, sombra_codigo_mirova
y mirova_equivalent (produccion). Q1: si sombra_34 difiriera en un flag de deteccion, la diferencia aparece. Q2: el control
sombra_codigo_mirova vs mirova_equivalent debe dar EXACTAMENTE las diferencias de las vias (control positivo del instrumento)."""
import subprocess, sys, json, os
W = "D:/vrp-trabajo/worktrees/s172-sombra34"
code = "import json, pipeline.profile as p; print(json.dumps({k: getattr(p, k) for k in dir(p) if k.isupper()}, default=repr, sort_keys=True))"
def res(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", code], cwd=W, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.strip().splitlines()[-1]); d.pop("VALID_PROFILES", None); return d
a, b, c = res("sombra_34"), res("sombra_codigo_mirova"), res("mirova_equivalent")
dif = lambda x, y: {k: (x.get(k), y.get(k)) for k in sorted(set(x) | set(y)) if x.get(k) != y.get(k)}
print("n constantes:", len(a), len(b), len(c))
print("sombra_34 vs sombra_codigo_mirova:", dif(a, b))
print("sombra_34 vs mirova_equivalent (produccion):", dif(a, c))
