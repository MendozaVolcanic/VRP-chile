# Cuanto sube el INDECIDIBLE por I6 con el tope de GANA, en el principal y en la variante d, con un brazo ruidoso q.
import os, sys, random, collections, time, pathlib
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R0 = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
R = os.environ.get("VRP_R") or R0
DATA = pathlib.Path(R0) / "data"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
import banco_paridad as bp
ref, q, n = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
filas = sk.cargar_ref(ref)
ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = ev.pasadas_de(filas, "union", ventanas)
SHA = "a" * 40
ctrl = ev.cargar_brazo([DATA], "mirova_equivalent", ventanas, bp.inner_desde_html())
ctrl = [r for r in ctrl if r["b"] in ev.SENSORES_DIA and not r["es_dia"]]
for r in ctrl: r["sha"] = SHA
base = [{"vol": p.volcano, "b": p.sensor_bucket, "dt": p.instante.replace(tzinfo=None), "es_dia": True,
         "pub": False, "disp": 0.0, "diag_dia": True, "sha": SHA} for p in pas if ev.es_dia_vol(p.volcano, p.instante)]
psup = {s: 0.5 for s in ev.SENSORES_DIA}
res = collections.defaultdict(list)
t0 = time.time()
for sem in range(n):
    rng = random.Random(1000 + sem)
    sint = [dict(r) for r in base]
    for r in sint:
        p = rng.random() < q
        r["pub"], r["disp"] = p, (0.3 if p else 0.0)
    recs = {"ctrl": ctrl, "diurno": [dict(r) for r in ctrl] + sint}
    for nom, kw in (("principal", {}), ("d", {"otra_como_negativo": True})):
        r = ev.evaluar(pas, recs, "ctrl", "diurno", "e-i", psup, SHA, ventanas, **kw)
        for s in ev.SENSORES_DIA:
            i = r["i6"][s]
            res[(nom, s)].append((i["c_falsos"], i.get("c_gana", 0)))
    print("semilla", sem, "%.0fs" % (time.time() - t0), flush=True)
print("q =", q, "n =", n)
for (nom, s), v in sorted(res.items()):
    f3 = sum(1 for f, g in v if f > 7)
    f31 = sum(1 for f, g in v if f > 7 or g > 4)
    print("%-9s %s | falla v3 (suma>7) %d/%d | falla v3.1 (suma>7 o GANA>4) %d/%d | falsos medianos %s" % (
        nom, s, f3, len(v), f31, len(v), sorted(f for f, g in v)[len(v) // 2]))
# por corrida: alguna de las 4 combinaciones
anyv3 = sum(1 for i in range(n) if any(res[k][i][0] > 7 for k in res))
anyv31 = sum(1 for i in range(n) if any(res[k][i][0] > 7 or res[k][i][1] > 4 for k in res))
print("corridas con al menos un I6 fallido (principal o d, algun sensor): v3 %d/%d, v3.1 %d/%d" % (anyv3, n, anyv31, n))
