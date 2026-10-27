import os, sys, collections, json
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, nulo_estructural as nu, evaluador_comun as ec
ref = sys.argv[1]
T, sint = nu.armar(ref)
dia = [f for f in T if f["es_dia"] and f["pasada"].sensor_bucket in ev.SENSORES_DIA]
print("diurnas VIIRS", len(dia))
for s in ev.SENSORES_DIA:
    fs = [f for f in dia if f["pasada"].sensor_bucket == s]
    amb = [f for f in fs if ec.clase_p2(f) == "alerta_mb"]
    pro = [f for f in fs if f["protegida"]]
    neg = [f for f in fs if ec.clase_p2(f) == "negativo"]
    print(s, "alerta_mb", len(amb), "bloques mb", len({(f['pasada'].volcano, f['dia']) for f in amb}),
          "| protegidas", len(pro), "bloques", len({(f['pasada'].volcano, f['dia']) for f in pro}),
          "| neg", len(neg), "bloques neg", len({(f['pasada'].volcano, f['dia']) for f in neg}))
    print("   protegidas por volcan", dict(collections.Counter(f['pasada'].volcano for f in pro)))
    print("   mb por volcan", dict(collections.Counter(f['pasada'].volcano for f in amb)))
    print("   neg por volcan", dict(collections.Counter(f['pasada'].volcano for f in neg)))
    # pasadas por bloque
    pb = collections.Counter((f['pasada'].volcano, f['dia']) for f in fs)
    print("   pasadas diurnas por volcan-dia: max", max(pb.values()), "dist", dict(sorted(collections.Counter(pb.values()).items())))
    # elevacion
    el = [ev.elevacion(f['pasada'].volcano, f['pasada'].instante) for f in fs]
    b = collections.Counter(("<=5" if e <= 5 else "5-10" if e <= 10 else "10-30" if e <= 30 else "30-60" if e <= 60 else ">60") for e in el)
    print("   elevacion solar (todas las diurnas):", dict(b))
    ea = [ev.elevacion(f['pasada'].volcano, f['pasada'].instante) for f in amb + pro]
    print("   elevacion de las alertas:", sorted(round(e) for e in ea))
    hrs = collections.Counter(f['pasada'].instante.hour for f in fs)
    print("   hora UTC:", dict(sorted(hrs.items())))
    # negativos v1 (dia UTC entero) vs v2 (periodo)
    alerta_dia_utc = {(f['pasada'].volcano, f['pasada'].sensor_bucket, f['dia']) for f in T if f['pasada'].estado == 'alerta' and f['pasada'].sensor_bucket == s}
    fp_dia_utc = {(f['pasada'].volcano, f['pasada'].sensor_bucket, f['dia']) for f in T if f['pasada'].estado == 'fp' and f['pasada'].sensor_bucket == s}
    n_v1 = sum(1 for f in neg if (f['pasada'].volcano, s, f['dia']) not in alerta_dia_utc and (f['pasada'].volcano, s, f['dia']) not in fp_dia_utc)
    print("   negativos diurnos v2:", len(neg), " de ellos tambien negativos con el dia UTC entero (v1):", n_v1, " nuevos en v2:", len(neg) - n_v1)
    nuevos = [f for f in neg if (f['pasada'].volcano, s, f['dia']) in alerta_dia_utc or (f['pasada'].volcano, s, f['dia']) in fp_dia_utc]
    print("   nuevos por volcan:", dict(collections.Counter(f['pasada'].volcano for f in nuevos)))
    # periodos mezclados: alertas nocturnas del mismo dia UTC
    # nocturnos: bloques con noches mezcladas (madrugada + tarde-noche) por volcan-dia UTC
noc = [f for f in T if not f["es_dia"] and f["pasada"].sensor_bucket in ev.SENSORES_DIA]
print("nocturnas VIIRS", len(noc))
hrs = collections.Counter(f['pasada'].instante.hour for f in noc)
print("hora UTC nocturnas:", dict(sorted(hrs.items())))
