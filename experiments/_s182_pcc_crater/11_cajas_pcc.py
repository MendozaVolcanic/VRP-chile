# S182: mide en Cordón Caulle V750 las cajas de búsqueda (ROI) del port de producción sobre TODAS las grillas M13/M15
# que guardó V750-B (runs 41615021658 y 41693265163, artefactos locales), contra lo que publicó MIROVA.
# Referencia: objetivos_run_v750b.json, campo 'mirova' (filas de la TABLA, source CONS, y del OCR, source OCR, las dos);
# 'mirova_vrp' = máximo de las filas ALERTA de ambas. Se informa también la razón contra la tabla sola.
# Port: copia de origin/main:pipeline/mirova_v750_codigo.py (sha256 se imprime). Sin red, sin tocar el repo.
# Cajas:
#   crater          B2: anillo 21x21 conservador, 7x7 sensible en la celda del cráter
#   sens            B4: anillo 21x21 entero sensible (la de producción en PCC, grillas_mirova.yaml)
#   sens_sur_cons   sens con las filas al sur de la fila central (f > 33) conservadoras
#   sens_sur_fuera  sens con las filas al sur de la fila central fuera de la búsqueda (0)
# "Sur" se define por la fila central de la grilla, no por los píxeles de la pasada del 21-oct, para no ajustar al caso.
import importlib.util, json, glob, sys, io, hashlib, statistics as st, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np

PORT = r"D:\vrp-trabajo\temporales\s182_pcc\_port_main.py"
BASE = r"D:\vrp-trabajo\temporales\v750b_r4_20261103"
OBJ = BASE + r"\arbol\experiments\_s162_v750b\adenda2\objetivos_run_v750b.json"
SALIDA_JSON = r"D:\vrp-trabajo\temporales\s182_pcc\11_cajas_pcc_filas.json"
VOLC = "PuyehueCordonCaulle"
N, C = 67, 33
POS_X0Y0 = (32.667, 33.333)   # 02_geometria_pcc: posición fraccionaria de (X0, Y0) en la grilla
PASO_KM = 0.75

spec = importlib.util.spec_from_file_location("port", PORT)
port = importlib.util.module_from_spec(spec); spec.loader.exec_module(port)
print("sha256 port", hashlib.sha256(open(PORT, 'rb').read()).hexdigest()[:16])

obj = {o["id"]: o for o in json.load(open(OBJ, encoding="utf-8")) if o["volcan"] == VOLC}
res, npz = {}, {}
for run in ("art_41615021658", "art_41693265163"):
    for f in glob.glob(BASE + "\\" + run + r"\*\resultados_*.json"):
        for r in json.load(open(f, encoding="utf-8")):
            if r.get("id") in obj and r.get("estado") == "ok":
                res.setdefault(r["id"], r)
    for f in glob.glob(BASE + "\\" + run + r"\*\grilla_*.npz"):
        i = int(f.rsplit("_", 1)[1].split(".")[0])
        if i in obj:
            npz.setdefault(i, f)
print(f"objetivos PCC {len(obj)}  con resultado ok {len(res)}  con grilla {len(npz)}  ambos {len(set(res) & set(npz))}")


def cajas(celda):
    b_sens = port.caja_roi("sens", n=N)
    s_cons = b_sens.copy(); s_cons[C + 1:, :][s_cons[C + 1:, :] == 2] = 1
    s_fuera = b_sens.copy(); s_fuera[C + 1:, :] = 0
    return {"crater": port.caja_roi("crater", n=N, celda_crater=tuple(celda)), "sens": b_sens,
            "sens_sur_cons": s_cons, "sens_sur_fuera": s_fuera}


TIPOS = ("crater", "sens", "sens_sur_cons", "sens_sur_fuera")
filas = []
for i in sorted(set(res) & set(npz)):
    o, r = obj[i], res[i]
    z = np.load(npz[i])
    m13, m15 = z["m13"].astype(float), z["m15"].astype(float)
    nan_frac = float(np.isnan(m13).mean())
    fila = {"id": i, "hora": o["hora_utc"], "sensor": o["sensor"], "lab": o["lab"], "prot": o["protegida"],
            "mirova_vrp": o["mirova_vrp"],
            "tabla_vrp": max([m["vrp_mw"] or 0 for m in o["mirova"] if m["source"] == "CONS" and m["tipo"].startswith("ALERTA")], default=None),
            "mirova_dist": [m.get("dist_km") for m in o["mirova"] if m["tipo"].startswith("ALERTA")],
            "fuentes": sorted({m["source"] for m in o["mirova"] if m["tipo"].startswith("ALERTA")}),
            "nan_frac": round(nan_frac, 4)}
    for t, box in cajas(o["celda_crater"]).items():
        mask = port.detectar_mirova(m13, m15, box, r["dayflag"], r["sunglint"])
        v = port.vrp_mirova(m13, mask)
        pix = list(zip(*np.nonzero(mask)))
        dmax = None
        if pix:
            f, k = max(pix, key=lambda p: m13[p])
            dmax = round(math.hypot(f + 0.5 - POS_X0Y0[0], k + 0.5 - POS_X0Y0[1]) * PASO_KM, 2)
        fila[t] = {"npix": v["npix"], "vrp": None if not np.isfinite(v["VRP_MW"]) else round(float(v["VRP_MW"]), 4),
                   "dist_max": dmax, "n_sur": int(sum(1 for p in pix if p[0] > C))}
    filas.append(fila)
json.dump(filas, open(SALIDA_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("filas", len(filas), "->", SALIDA_JSON)

pos = [f for f in filas if f["lab"] == "pos"]
neg = [f for f in filas if f["lab"] != "pos"]
print(f"\nMIROVA alertó en {len(pos)} pasadas ({sum(f['prot'] for f in pos)} protegidas >= 1 MW); fuentes de esas alertas: "
      f"solo tabla {sum(f['fuentes']==['CONS'] for f in pos)}, solo OCR {sum(f['fuentes']==['OCR'] for f in pos)}, ambas {sum(f['fuentes']==['CONS','OCR'] for f in pos)}")
print(f"MIROVA no alertó (neg_limpio) en {len(neg)}")


def resumen(t):
    det = [f for f in pos if f[t]["npix"]]
    prot_perd = [f for f in pos if f["prot"] and not f[t]["npix"]]
    rz = [f[t]["vrp"] / f["mirova_vrp"] for f in det if f["mirova_vrp"] and f[t]["vrp"] is not None]
    rzt = [f[t]["vrp"] / f["tabla_vrp"] for f in det if f["tabla_vrp"] and f[t]["vrp"] is not None]
    dentro = sum(1 for x in rz if 0.5 <= x <= 2)
    neg_det = [f for f in neg if f[t]["npix"]]
    neg_mw = sum(f[t]["vrp"] or 0 for f in neg_det)
    ok = [f for f in pos if f[t]["npix"] and f[t]["dist_max"] is not None and f["mirova_dist"] and f["mirova_dist"][0]]
    dd = [abs(f[t]["dist_max"] - f["mirova_dist"][0]) for f in ok]
    print(f"\n[{t}]")
    print(f"  alertas de MIROVA vistas {len(det)}/{len(pos)}; protegidas perdidas {len(prot_perd)} {[f['hora'] for f in prot_perd]}")
    if rz:
        print(f"  razón VRP/MIROVA (tabla+OCR, máx): mediana {st.median(rz):.3f}  p10 {np.percentile(rz,10):.3f}  p90 {np.percentile(rz,90):.3f}  "
              f"máx {max(rz):.2f}  dentro de [0,5; 2] {dentro}/{len(rz)}")
    if rzt:
        print(f"  razón VRP/tabla sola: mediana {st.median(rzt):.3f}  máx {max(rzt):.2f}  n {len(rzt)}")
    if dd:
        print(f"  |dist del píxel más caliente - Distancia_km de MIROVA|: mediana {st.median(dd):.2f} km  >2 km en {sum(x>2 for x in dd)}/{len(dd)}")
    print(f"  pasadas sin alerta de MIROVA con algún píxel {len(neg_det)}/{len(neg)}  (suma {neg_mw:.2f} MW; detección cruda)")
    for f in neg_det:
        print(f"     {f['hora']} {f['sensor']:17s} {f[t]['npix']} px {f[t]['vrp']} MW dist {f[t]['dist_max']} sur {f[t]['n_sur']} nan {f['nan_frac']}")


for t in TIPOS:
    resumen(t)

print("\nPasadas con alerta de MIROVA donde alguna caja cambia npix o la razón sale de [0,5; 2]:")
print("  hora  sensor  prot  MIROVA(fuentes, dist) | crater | sens | sur_cons | sur_fuera   (npix/VRP MW)")
for f in pos:
    vals = [f[t] for t in TIPOS]
    rr = [(v["vrp"] / f["mirova_vrp"]) if (v["vrp"] and f["mirova_vrp"]) else None for v in vals]
    if len({v["npix"] for v in vals}) > 1 or any(x is not None and not (0.5 <= x <= 2) for x in rr) or any(v["npix"] == 0 for v in vals):
        print(f"  {f['hora']} {f['sensor'][-12:]} {str(f['prot'])[0]} {f['mirova_vrp']}({'+'.join(f['fuentes'])},{f['mirova_dist']}) | "
              + " | ".join(f"{v['npix']}/{v['vrp']}" for v in vals))
