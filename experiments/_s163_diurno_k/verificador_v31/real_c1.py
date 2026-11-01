# C1 sobre la referencia congelada: la reclasificacion de la variante d, que toca y que no.
import os, sys, random, collections
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import clase_mirova as cm, evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
import banco_paridad as bp
ref = sys.argv[1]
filas = sk.cargar_ref(ref)
ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
print("ventanas", ventanas)
pas = ev.pasadas_de(filas, "union", ventanas)
copia = list(pas)
print("pasadas union:", len(pas))
# 1. conteo diurno por (sensor, estado, fuente)
c = collections.Counter()
for p in pas:
    dia = ev.es_dia_vol(p.volcano, p.instante)
    c[(p.sensor_bucket, "dia" if dia else "noche", p.estado, p.fuente)] += 1
for k in sorted(c): print(k, c[k])
SHA = "a" * 40
ctrl = ev.cargar_brazo([R + r"\data"] if False else [__import__("pathlib").Path(R) / "data"], "mirova_equivalent", ventanas, bp.inner_desde_html())
ctrl = [r for r in ctrl if r["b"] in ev.SENSORES_DIA and not r["es_dia"]]
for r in ctrl: r["sha"] = SHA
sint = []
for p in pas:
    if ev.es_dia_vol(p.volcano, p.instante):
        sint.append({"vol": p.volcano, "b": p.sensor_bucket, "dt": p.instante.replace(tzinfo=None), "es_dia": True,
                     "pub": False, "disp": 0.0, "diag_dia": True, "sha": SHA})
rng = random.Random(5)
for r in sint:
    p = rng.random() < 0.05
    r["pub"], r["disp"] = p, (0.3 if p else 0.0)
brazo = [dict(r) for r in ctrl] + sint
recs = {"ctrl": ctrl, "diurno": brazo}
psup = {s: 0.5 for s in ev.SENSORES_DIA}
def clases(rr):
    T = rr["T"]
    return {(f["clave"]): (ec.clase_p2(f), f["es_dia"], f["pasada"].estado) for f in T}
r0 = ev.evaluar(pas, recs, "ctrl", "diurno", "e-i", psup, SHA, ventanas)
r1 = ev.evaluar(pas, recs, "ctrl", "diurno", "e-i", psup, SHA, ventanas, otra_como_negativo=True)
assert pas == copia, "la lista de entrada cambio"
c0, c1 = clases(r0), clases(r1)
print("claves iguales:", set(c0) == set(c1), len(c0), len(c1))
cambios = collections.Counter()
for k in c0:
    a, b = c0[k], c1[k]
    if a != b:
        cambios[(k[1], a[0], b[0], a[2], b[2], a[1])] += 1
for k, v in sorted(cambios.items(), key=lambda x: -x[1]): print("cambio", k, v)
# nocturnas y MODIS: ninguna cambia
noche_cambia = [k for k in c0 if c0[k] != c1[k] and not c0[k][1]]
print("pasadas NOCTURNAS que cambian de clase o estado:", len(noche_cambia))
# clase de las diurnas despues
d1 = collections.Counter()
for k, v in c1.items():
    if v[1]: d1[(k[1], v[0])] += 1
print("diurnas variante d (sensor, clase):", dict(d1))
d0 = collections.Counter()
for k, v in c0.items():
    if v[1]: d0[(k[1], v[0])] += 1
print("diurnas principal (sensor, clase):", dict(d0))
for s in ev.SENSORES_DIA:
    for nom, rr in (("principal", r0), ("variante d", r1)):
        m = rr["por_sensor"][s]
        print(s, nom, "neg_obs", m["neg_obs"], "neg_pub", m["neg_pub"], "pub_otra", m["pub_otra"], "p2", m["p2"], "neto", m["neto"], "veredicto", m["veredicto"], "i6", rr["i6"][s]["c_falsos"], rr["i6"][s]["c_gana"], rr["i6"][s]["a"]["resultado"])
print("globales:", r0["global"], r1["global"])
print("compuertas principal:", r0["compuertas"]); print("compuertas d:", r1["compuertas"])
