# N3 no es equivalente: si la variante d reclasificara tambien los FALSO_POSITIVO nocturnos, Qn y su denominador cambian.
import os, sys, random, pathlib
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, sustrato_k as sk, banco_paridad as bp
filas = sk.cargar_ref(sys.argv[1])
ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = ev.pasadas_de(filas, "union", ventanas)
SHA = "a" * 40
ctrl = [r for r in ev.cargar_brazo([pathlib.Path(R) / "data"], "mirova_equivalent", ventanas, bp.inner_desde_html()) if r["b"] in ev.SENSORES_DIA and not r["es_dia"]]
for r in ctrl: r["sha"] = SHA
sint = [{"vol": p.volcano, "b": p.sensor_bucket, "dt": p.instante.replace(tzinfo=None), "es_dia": True, "pub": False, "disp": 0.0, "diag_dia": True, "sha": SHA} for p in pas if ev.es_dia_vol(p.volcano, p.instante)]
recs = {"ctrl": ctrl, "diurno": [dict(r) for r in ctrl] + sint}
psup = {s: 0.5 for s in ev.SENSORES_DIA}
bien = ev.evaluar(pas, recs, "ctrl", "diurno", "e-i", psup, SHA, ventanas, otra_como_negativo=True)
mal_pas = [p._replace(estado="rutina") if (p.estado == "fp" and p.fuente == "CONS" and p.sensor_bucket in ev.SENSORES_DIA) else p for p in pas]
mal = ev.evaluar(mal_pas, recs, "ctrl", "diurno", "e-i", psup, SHA, ventanas, otra_como_negativo=True)
for s in ev.SENSORES_DIA:
    print(s, "correcto: Qn_den", bien["por_sensor"][s]["Qn_den"], "Qn", round(bien["por_sensor"][s]["Qn"], 4),
          "| con N3: Qn_den", mal["por_sensor"][s]["Qn_den"], "Qn", round(mal["por_sensor"][s]["Qn"], 4))
