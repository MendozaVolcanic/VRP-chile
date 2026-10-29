# Reproduce las 13 publicaciones diurnas del brazo sin pasada de MIROVA (VD167-01) y vuelca los records completos.
import sys, io, json, glob, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path("D:/vrp-trabajo/temporales/s167_diurno_lectura")
sys.path.insert(0, str(BASE/"codigo/experiments/_s163_diurno_k")); sys.path.insert(0, str(BASE/"codigo/scripts"))
import os; os.chdir(BASE/"codigo")
import evaluar_diurno_k as e, sustrato_k as sk, banco_paridad as bp
REF = BASE/"ref"
sus = json.loads(Path("experiments/_s163_diurno_k/sustrato_k.json").read_text(encoding="utf-8"))
print("ref distinta:", [n for n in sk.ARCHIVOS_REF if e.sha256(REF/n) != sus["sha256"][n]])
filas = sk.cargar_ref(REF)
raices = sorted(glob.glob(str(BASE/"corridas/experiments/_s151_ab_diurno/salidas/*")))
ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
inner = bp.inner_desde_html()
C, B = "_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on"
recs = {C: e.cargar_brazo(raices, C, ventanas, inner), B: e.cargar_brazo(raices, B, ventanas, inner)}
p_sup = e.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
r = e.evaluar(e.pasadas_de(filas, "union", ventanas), recs, C, B, "e-ii", p_sup, "68687d2d4b73bb0527da18a2c886a6dcc241a0ac", ventanas)
T = r["T"]; print("global", r["global"])
sin = []
for rec in recs[B]:
    if not (rec["es_dia"] and rec["pub"] and rec["b"] in e.SENSORES_DIA): continue
    cand = [f for f in T if f["es_dia"] and f["pasada"].volcano == rec["vol"] and f["pasada"].sensor_bucket == rec["b"]
            and abs((f["pasada"].instante.replace(tzinfo=None) - rec["dt"]).total_seconds()) <= 120]
    if not cand: sin.append(rec)
print("n sin pasada:", len(sin))
# records crudos completos
out = []
for rec in sin:
    tt = rec["dt"].strftime("%Y-%m-%d %H:%M"); hit = None
    for raiz in raices:
        p = Path(raiz)/B/("%s.json" % rec["vol"])
        if not p.exists(): continue
        for x in json.loads(p.read_text(encoding="utf-8"))["records"]:
            if x.get("datetime_utc") == tt and bp.bucket(x.get("sensor")) == rec["b"]:
                hit = dict(x); hit["_raiz"] = Path(raiz).name; break
        if hit: break
    hit["_vol"] = rec["vol"]; hit["_disp"] = rec["disp"]; hit["_soz"] = rec["soz"]; hit["_soa"] = rec["soa"]; hit["_sz"] = rec["sz"]; hit["_sa"] = rec["sa"]
    out.append(hit)
# nocturnas del brazo y del control, por volcan (para +-72 h)
noct = {}
for brazo in (B, C):
    for rec in recs[brazo]:
        if rec["es_dia"]: continue
        noct.setdefault(brazo, []).append({"vol": rec["vol"], "b": rec["b"], "dt": rec["dt"].strftime("%Y-%m-%d %H:%M"), "pub": rec["pub"], "disp": rec["disp"]})
OUTD = Path("D:/vrp-trabajo/temporales/s167_diurnas_13")
# dia del control: mismo granulo publicado?
ctrl = {(x["vol"], x["b"], x["dt"].strftime("%Y-%m-%d %H:%M")): x for x in recs[C]}
(OUTD/"brazo_idx.json").write_text(json.dumps({"|".join((x["vol"], x["b"], x["dt"].strftime("%Y-%m-%d %H:%M"))): {"pub": x["pub"], "disp": x["disp"], "es_dia": x["es_dia"]} for x in recs[B]}, ensure_ascii=False), encoding="utf-8")
for h in out:
    k = (h["volcano"] if "volcano" in h else None)
(OUTD/"trece_records.json").write_text(json.dumps(out, default=str, ensure_ascii=False, indent=1), encoding="utf-8")
(OUTD/"nocturnas_brazos.json").write_text(json.dumps(noct, ensure_ascii=False), encoding="utf-8")
(OUTD/"control_mismo_granulo.json").write_text(json.dumps({"|".join(k): {"pub": v["pub"], "disp": v["disp"], "es_dia": v["es_dia"]} for k, v in ctrl.items()}, ensure_ascii=False), encoding="utf-8")
for h in out:
    pc = h.get("primary_cluster") or {}
    print(h["_raiz"], h["_vol"], h.get("sensor"), h.get("datetime_utc"), "disp=%.3f" % h["_disp"], "vrp=", h.get("vrp_mw"), "pc=", pc.get("vrp_mw"), "f5=", h.get("f5_core_vrp_mw"),
          "dist=", h.get("final_hotspot_dist_km"), h.get("distance_class"), "src=", h.get("final_hotspot_source"),
          "soz=", h["_soz"], "sz=", h["_sz"], "tbg=", h.get("t_bg_k"), "tmax=", h.get("t_max_k"), "nti=", h.get("nti_max"), "npx=", h.get("n_anomalous_pixels"))
