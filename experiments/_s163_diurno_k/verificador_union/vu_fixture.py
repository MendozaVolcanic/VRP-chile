# Fixture sintetico propio: un record por cada pasada de MIROVA de W2 a W6 (referencia congelada), control sin diurno.
import sys, os, json, random, pathlib
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import evaluar_diurno_k as ev, sustrato_k as sk
ref, destino = sys.argv[1], pathlib.Path(sys.argv[2])
filas=sk.cargar_ref(pathlib.Path(ref))
vent=[(w[0],w[1],w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas=ev.pasadas_de(filas,"union",vent)
SHA="a"*40
rng=random.Random(11)
suf={"VIIRS375":"VIIRS_SNPP","VIIRS750":"VIIRS_SNPP_750","MODIS":"MODIS_AQUA"}
out={"C":{}, "B":{}}; n=0
for p in pas:
    dia=ev.es_dia_vol(p.volcano,p.instante)
    base={"distance_class":"summit","vrp_mw":0.0,"primary_cluster":None,"anomaly_pixels":[],"regimen":{"codigo_sha":SHA},
          "sensor_zenith_deg":10.0,"sensor_azimuth_deg":20.0,"solar_zenith_deg":40.0,"solar_azimuth_deg":50.0,
          "sensor":suf[p.sensor_bucket],"datetime_utc":p.instante.strftime("%Y-%m-%d %H:%M")}
    u=rng.random(); vrp=0.0
    if p.estado=="alerta": vrp=(p.vrp_mw or 0.5) if u<0.7 else 0.0
    elif u<0.12: vrp=0.2
    rec=dict(base, vrp_mw=vrp)
    if vrp>0: rec["primary_cluster"]={"vrp_mw":vrp,"n_pixels":1,"centroid_lat":0,"centroid_lon":0}
    if not dia:
        out["C"].setdefault(p.volcano,[]).append(rec); out["B"].setdefault(p.volcano,[]).append(dict(rec))
    else:
        out["B"].setdefault(p.volcano,[]).append(dict(rec, diag_umbrales_diurnos={"x":1})); n+=1
for lado,nm in (("C","_s154_ab_diurno_k_control"),("B","_s154_ab_diurno_k_on")):
    (destino/nm).mkdir(parents=True,exist_ok=True)
    for vol,rs in out[lado].items():
        (destino/nm/(vol+".json")).write_text(json.dumps({"records":rs}),encoding="utf-8")
print("diurnos",n,"pasadas",len(pas))
