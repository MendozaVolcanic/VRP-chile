"""03: toda la evidencia por pasada en una tabla: fila OCR de MIROVA, filas de la tabla de esa noche, K re-corrido (artefacto
de S159), pixeles del port (modo "fisica", distancia al crater), los 10 brazos recalculados sobre la grilla guardada y la
cabecera "Last Update" de la imagen guardada con la hora de la fila (leida en RENDER por el auditor).

Preguntas del instrumento. (1) Si el port tuviera pixeles en el crater, aca saldria la distancia minima bajo la media
caja de C13 (6,5 celdas de 375 m = 2,44 km) y npix > 0 en algun brazo: un cero en los 10 brazos con pixeles a 9 km o mas
no es "no medi". (2) Control positivo del recalculo: una protegida de la tabla del mismo lote tiene que dar npix > 0 en
C13 con el mismo codigo; si el recalculo estuviera muerto daria 0 tambien ahi. Denominador: las 6 pasadas; la noche de
cada una (filas de la tabla antes de las 12 UTC). Artefactos: D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945.
"""
import sys, io, json, csv, hashlib
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "experiments/_s162_v375"))
import brazos as BR
import yaml
ART = Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
V = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
OBJ = {o["id"]: o for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))}
SEIS = [279, 285, 288, 289, 294, 295]
MEDIA_CAJA_C13_KM = 6.5 * 0.375
# cabeceras "Last Update" leidas en RENDER (imagenes _Latest.png de Mirova-v1 bajadas por la API; md5 en 00_md5_png.txt)
CABECERA = {279: "01-Aug-2026 06:06:02", 285: "22-Aug-2026 05:24:01", 288: "09-Sep-2026 06:30:01",
            289: "14-Sep-2026 06:36:01", 294: "28-Sep-2026 05:36:01", 295: "29-Sep-2026 06:36:00"}


def res_runner(i):
    for f in sorted(ART.glob("s159-portes-VIIRS375-*/resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["id"] == i:
                return r


def grilla(i):
    z = list(ART.rglob(f"grilla_{i}.npz"))
    assert len(z) == 1, (i, z)
    q = np.load(z[0])
    return q["mir"].astype(np.float64), q["tir"].astype(np.float64), z[0]


def fila_ocr(vol, h):
    out = []
    with open(RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["Volcan"] == vol and r["Sensor"] == "VIIRS375" and r["Fecha_Satelite_UTC"][:16] == h:
                out.append(r)
    return out


def tabla_noche(vol, dia):
    out = []
    with open(RAIZ / "latest_consolidado.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r["Volcan"] == vol and r["Sensor"] == "VIIRS375" and r["Fecha_Satelite_UTC"][:10] == dia
                    and r["Fecha_Satelite_UTC"][11:13] < "12"):
                out.append((r["Fecha_Satelite_UTC"][11:19], r["Tipo_Registro"], r["VRP_MW"], r["Distancia_km"]))
    return out


def correr(o, r, mir, tir):
    v = V[o["volcan"]]
    xc, yc = BR.crater_xy(o["grilla"], v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
    return BR.correr_brazos(mir, tir, o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc, v["inner_radius_km"],
                            o["volcan"], r["dayflag"], r["sunglint"], semillas=0)


salida = {}
for i in SEIS:
    o = OBJ[i]
    vol = o["volcan"]
    v = V[vol]
    r = res_runner(i)
    assert r and r["estado"] == "ok"
    mir, tir, zpath = grilla(i)
    arms = correr(o, r, mir, tir)
    fis = r["port"]["fisica"]
    dists = sorted(p[3] for p in fis["pixeles"])
    ocr = fila_ocr(vol, o["hora_utc"])
    K = r["K"]["record"]
    pc = K["primary_cluster"] or {}
    fila = {
        "id": i, "volcan": vol, "hora": o["hora_utc"], "sensor": o["sensor"], "granule": r["granule"],
        "zenit": round(r["geometria_centro"]["sensor_zenith"], 1), "inner_km": v["inner_radius_km"],
        "mirova_ocr": [{"vrp": x["VRP_MW"], "dist": x["Distancia_km"], "metodo": x["Nota_Validacion"],
                        "conf": x["Confianza_Validacion"], "version_ocr": x["Version_OCR"],
                        "aprox": (x["Distancia_aprox_km"], x["Distancia_aprox_min_km"], x["Distancia_aprox_max_km"],
                                  x["Distancia_aprox_metodo"], x["Distancia_aprox_pareos"]),
                        "aprox_imagen": x["Distancia_aprox_imagen"]} for x in ocr],
        "cabecera_imagen_guardada": CABECERA[i],
        "tabla_esa_noche": tabla_noche(vol, o["hora_utc"][:10]),
        "K_rerun": {"pub": bool(o["pub_prod"]), "dc": K["distance_class"], "pc_vrp": pc.get("vrp_mw"),
                    "pc_dist_km": pc.get("centroid_dist_km"), "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"),
                    "vrp_escena": K["vrp_mw"], "n_px": K["n_anomalous_pixels"], "t_max": K["t_max_k"],
                    "descartado": K.get("discarded_reason")},
        "port_runner": {"npix": fis["npix"], "vrp": round(fis["vrp_mw"], 3), "dist_km_min": dists[0], "dist_km_max": dists[-1],
                        "pixeles": fis["pixeles"]},
        "brazos_recalculados": {b: {"npix": a["npix"], "vrp": (None if a["vrp_mw"] is None else round(a["vrp_mw"], 3))}
                                 for b, a in arms.items()},
        "media_caja_c13_km": MEDIA_CAJA_C13_KM, "grilla_sha": hashlib.sha256(zpath.read_bytes()).hexdigest()[:12],
    }
    salida[i] = fila
    print(f"\n=== id {i} {vol} {o['hora_utc']} {o['sensor']} zen {fila['zenit']} inner {v['inner_radius_km']} km  granulo {r['granule']}")
    for x in fila["mirova_ocr"]:
        print(f"  MIROVA (fila solo OCR): VRP {x['vrp']} MW dist {x['dist']} km | metodo: {x['metodo']} | conf {x['conf']} v{x['version_ocr']}")
        print(f"     distancia por la serie (scraper, imagen {x['aprox_imagen'].split('/')[-1]}): {x['aprox']}")
    print(f"  cabecera Last Update de la imagen guardada con esa hora (RENDER): {CABECERA[i]}  (la fila dice {o['hora_utc']})")
    print(f"  tabla latest.php esa noche (VIIRS375): {fila['tabla_esa_noche']}")
    k = fila["K_rerun"]
    print(f"  K re-corrido: publica {k['pub']} | {k['dc']} pc {k['pc_vrp']} MW a {k['pc_dist_km']} km del crater | escena "
          f"{k['vrp_escena']} MW, {k['n_px']} px, t_max {k['t_max']} K {k['descartado'] or ''}")
    print(f"  port (fisica, runner): {fis['npix']} px, {fis['vrp_mw']:.3f} MW, distancias al crater {dists[0]} a {dists[-1]} km "
          f"(media caja C13 {MEDIA_CAJA_C13_KM:.2f} km)")
    print("  brazos recalculados (npix, MW):",
          {b: (a["npix"], None if a["vrp_mw"] is None else round(a["vrp_mw"], 3)) for b, a in arms.items()})
json.dump(salida, open(AQUI / "03_evidencia_por_pasada.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)

print("\n== control positivo del recalculo (protegidas de la TABLA del lote S159 en VIIRS375: C13 tiene que dar npix > 0)")
n_ok = n_tot = 0
for oid, o in sorted(OBJ.items()):
    if o.get("clase") == "pos_prot" and o.get("alerta_tabla") and o["b"] == "VIIRS375":
        r = res_runner(oid)
        if not r or r["estado"] != "ok":
            continue
        try:
            mir, tir, zp = grilla(oid)
        except AssertionError:
            continue
        arms = correr(o, r, mir, tir)
        n_tot += 1
        n_ok += int(arms["C13"]["npix"] > 0)
        if n_tot <= 3:
            print(f"  id {oid} {o['volcan']} {o['hora_utc']} MIROVA {o['mirova_vrp']} MW: C13 npix {arms['C13']['npix']} "
                  f"vrp {arms['C13']['vrp_mw']}; M14 npix {arms['M14']['npix']}")
print(f"  C13 con pixeles: {n_ok} de {n_tot} protegidas de la tabla con grilla guardada")
assert n_tot and n_ok == n_tot, "control positivo del recalculo FALLA"
