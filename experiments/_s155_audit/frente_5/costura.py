# -*- coding: utf-8 -*-
"""S155 frente 5: los cumulos que se descartan, estan pegados en el terreno al cumulo publicado?

POR QUE. cluster_hotspots une componentes 8-conexas en el ESPACIO DEL ARREGLO (fila, columna del granulo), no en el
terreno (pipeline/clustering.py: ndi_label sobre hot_mask_2d). Lejos del nadir VIIRS borra filas de borde de cada
barrido (bow-tie) y los barridos vecinos se solapan en el terreno: dos pixeles vecinos en el suelo pueden quedar
separados en el arreglo y salir como dos cumulos. Si eso pasa, la distancia en el terreno entre el cumulo publicado y
el descartado deberia ser del orden del paso entre pixeles, no de varios pixeles.

Instrumento. Para cada pasada protegida con seleccion (estratos.json, Rpub < 0,9 Rinner) y membresia reconstruida
(n <= 3), la menor distancia en el terreno entre un pixel publicado y uno descartado, dividida por el paso nominal a
lo largo de la traza (0,742 km VIIRS M, 0,371 km VIIRS I, 1 km MODIS; ese paso es fijo con el angulo porque lo fija
el avance del satelite) y por la huella de barrido del modelo (fs * paso de barrido nadir). Pregunta 1: si no hubiera
fragmentacion por topologia, las razones serian >= ~2 (hay un pixel no alertado entre medio). Pregunta 2: control =
pasadas nadir con un solo cumulo no aportan (no hay descartado); el control positivo es interno: dos pixeles del
MISMO cumulo publicado deben dar razon <= ~1,5 (son vecinos en el arreglo, luego en el terreno).
LIMITE: sin L1B no se ve la fila; esto es indicio, no prueba."""
import io, json, math, os, sys, itertools
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import pareo_pasadas as PP  # noqa
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp, dl = p2 - p1, math.radians(d - b)
    return 2 * R * math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
PASO_TRAZA = {"VIIRS750": 0.742, "VIIRS375": 0.371, "MODIS": 1.0}
PASO_BARRIDO = {"VIIRS750": 0.776, "VIIRS375": 0.388, "MODIS": 1.0}
recs = {(r["datetime_utc"][:16], PP.bucket(r["sensor"])): r for r in json.load(open(
    os.path.join(PP.WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]}
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
print("t b zen | nPUB nFUERA | dmin_pub_fuera km | /paso_traza /huella_barrido | dmax_dentro_pub km /paso_traza | VRP_fuera/VRP_pub")
for f in ok:
    if not f["Rpub"] < 0.9 * f["Rinner"]:
        continue
    r = recs[(f["t"], f["b"])]; pc = r["primary_cluster"]; pix = r["anomaly_pixels"]
    if pc["n_pixels"] > 3:
        continue
    miem = PP.miembros_cumulo(pc, pix)
    if not miem:
        continue
    ids = {id(p) for p in miem}
    fuera = [p for p in pix if id(p) not in ids and p["vrp_mw"] > 0]
    if not fuera:
        print("%s %-8s %5.1f | %d 0 | sin descartados con VRP>0 (solo modo de un pixel)" % (f["t"], f["b"], f["zen"], len(miem)))
        continue
    dmin = min(hav(a["lat"], a["lon"], b["lat"], b["lon"]) for a in miem for b in fuera)
    dmax_in = max((hav(a["lat"], a["lon"], b["lat"], b["lon"]) for a, b in itertools.combinations(miem, 2)), default=float("nan"))
    hb = f["fs"] * PASO_BARRIDO[f["b"]]
    print("%s %-8s %5.1f | %d %d | %5.2f | %5.2f %5.2f | %5.2f %5.2f | %5.2f" % (
        f["t"], f["b"], f["zen"], len(miem), len(fuera), dmin, dmin / PASO_TRAZA[f["b"]], dmin / hb,
        dmax_in, dmax_in / PASO_TRAZA[f["b"]], sum(p["vrp_mw"] for p in fuera) / max(sum(p["vrp_mw"] for p in miem), 1e-9)))
