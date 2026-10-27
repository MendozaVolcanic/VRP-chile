import os, sys, collections
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, nulo_estructural as nu, evaluador_comun as ec
T, sint = nu.armar(sys.argv[1])
for s in ev.SENSORES_DIA:
    noc = [f for f in T if not f["es_dia"] and f["pasada"].sensor_bucket == s]
    sin = [f for f in noc if f["rec"]["ctrl"] is None]
    al = [f for f in noc if f["pasada"].estado == "alerta"]
    print(s, "nocturnas", len(noc), "sin record", len(sin), "alertas nocturnas", len(al), "alertas sin record", sum(1 for f in al if f["rec"]["ctrl"] is None))
    print("   sin record por estado:", dict(collections.Counter(f["pasada"].estado + "/" + f["pasada"].fuente for f in sin)))
    print("   sin record:", [(f["pasada"].volcano, f["pasada"].instante.strftime("%m-%d %H:%M")) for f in sin][:12])
    # fuente de las alertas diurnas
    d = [f for f in T if f["es_dia"] and f["pasada"].sensor_bucket == s and f["pasada"].estado == "alerta"]
    print("   alertas diurnas por fuente:", dict(collections.Counter((f["pasada"].fuente, f["pasada"].solo_ocr) for f in d)))
    print("   alertas diurnas (volcan, hora, vrp, fuente):", sorted((f["pasada"].volcano, f["pasada"].instante.strftime("%m-%d %H:%M"), f["pasada"].vrp_mw, f["pasada"].fuente) for f in d)[:40])
