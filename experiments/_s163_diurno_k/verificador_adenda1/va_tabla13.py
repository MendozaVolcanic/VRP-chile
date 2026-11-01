import os, sys, pathlib, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import evaluar_diurno_k as ev, sustrato_k as sk
filas=sk.cargar_ref(pathlib.Path(sys.argv[1]))
W6=[("W6","2026-10-01","2026-10-14")]
for canal in ("tabla","union"):
    pas=ev.pasadas_de(filas,canal,W6)
    c=collections.Counter()
    for p in pas:
        d=p.instante.strftime("%Y-%m-%d")
        if d in ("2026-10-12","2026-10-13","2026-10-14"):
            c[(d,p.sensor_bucket,"dia" if ev.es_dia_vol(p.volcano,p.instante) else "noche")]+=1
    print(canal, sorted(c.items()))
# horas de las pasadas VIIRS 375 del 13 de octubre (union)
pas=ev.pasadas_de(filas,"union",W6)
print(sorted({(p.instante.strftime("%H:%M"),p.estado,p.fuente) for p in pas if p.instante.strftime("%Y-%m-%d")=="2026-10-13" and p.sensor_bucket=="VIIRS375"}))
