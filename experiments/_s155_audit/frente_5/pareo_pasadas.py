# -*- coding: utf-8 -*-
"""S155 auditoria, frente 5: magnitud de Nevados de Chillan en erupcion, pasada por pasada.

POR QUE. Desde fines de septiembre de 2026 Chillan esta en fase eruptiva. Detectamos las pasadas nocturnas
que MIROVA alerta, pero la magnitud publicada queda en 0,12 a 0,72 veces la de MIROVA y la razon cae con el
cenit del sensor. Este script separa, pasada por pasada, cuanto del deficit puede venir de cada mecanismo
usando SOLO lo que el record persiste (sin L1B):
  (a) seleccion: publicado contra cumulo entero (antes del modo de un pixel) contra toda la escena;
  (b) fondo: cuanto se le resta a cada pixel, y la cota de "fondo cero";
  (c) recorte: tope D9 de 5 MW y lista truncada a 100 pixeles;
  (d) saturacion: senales indirectas en el record;
  (e) area: factor geometrico de huella segun el cenit (modelo, ver huella()).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el mecanismo estuviera roto, lo veria? Para (a), (b), (c) si, porque reconstruyo el VRP por pixel desde
   la BT persistida con la formula del codigo y compruebo que el fondo implicito coincide con t_bg del record
   (control "reconstruccion": si no coincide, el instrumento no reproduce el codigo y la pasada se marca).
   Para (d) solo parcialmente: un pixel saturado se descarta como NaN ANTES de entrar al record, asi que el
   record no lo puede mostrar; lo unico visible es una BT alta cerca del techo o un hueco. Para (e) no: el
   area es un MODELO geometrico, no medida; sirve de cota, no de verificacion.
2. Si el instrumento estuviera muerto, se veria distinto? Se informa el control positivo: la razon
   publicado/MIROVA debe reproducir la tabla de S154 (razon_por_cenit_salida_20261018.txt) en las 10 pasadas
   del 2026-10-18, y el fondo implicito debe coincidir con t_bg en los records con fondo de anillo.

Denominador: pares (pasada nuestra, alerta MIROVA) con la misma hora al minuto y el mismo grupo de sensor,
ventana 2026-09-28 a 2026-10-19 (primera alerta >= 1 MW de MIROVA en Chillan: 2026-09-28 04:42).
Referencia: consolidado remoto de Mirova-v1 (pisa al OCR) y OCR remoto, bajados el 2026-10-19 10:43 UTC a
D:/vrp-trabajo/temporales/frente_5/ (sha256 en la salida).

Uso: python experiments/_s155_audit/frente_5/pareo_pasadas.py > experiments/_s155_audit/frente_5/pareo_pasadas_salida.txt
"""
import csv
import hashlib
import io
import itertools
import json
import math
import os
import sys

WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, WT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
_stdout = sys.stdout
sys.stdout = io.StringIO()  # el import del perfil imprime una linea; la tiro
from pipeline.process_viirs import C1, C2, I04_LAMBDA, WOOSTER_COEFF as K375, NADIR_PIXEL_AREA_M2 as A375  # noqa
from pipeline.process_viirs_mod import M13_LAMBDA, WOOSTER_COEFF as K750, NADIR_PIXEL_AREA_M2 as A750  # noqa
from pipeline.process_modis import BAND21_LAMBDA, BAND22_LAMBDA, WOOSTER_COEFF as KMOD, NADIR_PIXEL_AREA_M2 as AMOD  # noqa
import pipeline.profile as P  # noqa
sys.stdout = io.TextIOWrapper(_stdout.buffer, encoding="utf-8")

TMP = "D:/vrp-trabajo/temporales/frente_5"
CONS = os.path.join(TMP, "registro_vrp_consolidado_remoto_20261019.csv")
OCR = os.path.join(TMP, "registro_vrp_ocr_remoto_20261019.csv")
DESDE, HASTA = "2026-09-28", "2026-10-19 23:59"
INNER_KM = 5.0
K_SHA = "34cea39e4"  # merge de #850 (adopcion de K)

CONST = {  # lambda de la conversion BT->L usada en el VRP, k de Wooster, area nadir (m2)
    "VIIRS375": (I04_LAMBDA, K375, A375),
    "VIIRS750": (M13_LAMBDA, K750, A750),
    "MODIS": (BAND21_LAMBDA, KMOD, AMOD),  # process_modis.py convierte con BAND21_LAMBDA
}
TECHO = {"VIIRS375": 361.77 - 0.5, "VIIRS750": 634.0 - 0.5, "MODIS": 500.0}  # descartes del codigo


def planck(bt, lam):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * bt)) - 1.0))


def bucket(s):
    s = s.upper()
    if "MODIS" in s:
        return "MODIS"
    return "VIIRS750" if (s.endswith("_750") or s == "VIIRS") else "VIIRS375"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def huella(zen_deg, sensor):
    """Factor de huella respecto del nadir para el cenit dado. MODELO geometrico, no medido.

    Tierra esferica R=6371 km. Altura H: VIIRS 829 km, MODIS 705 km. r = distancia oblicua.
    Eje de traza: crece como r/H. Eje de barrido: crece como (r/H)/cos(cenit) por muestra; VIIRS agrega
    3, 2 o 1 muestras segun el angulo de barrido (zonas 31,589 y 44,680 grados, ATBD de geolocalizacion VIIRS,
    citado en docs/s131/REMUESTREO_LEY_DE_AREA.md), lo que se modela dividiendo por 3, 1,5 o 1.
    Devuelve (factor_barrido, factor_area_completa). El paso de muestreo a lo largo de la traza es fijo por
    construccion del barrido, asi que la huella "completa" sobrecuenta lo que se solapa: la verdad energetica
    queda entre las dos (cota baja = solo barrido, cota alta = area completa).
    """
    R = 6371.0
    H = 829.0 if sensor != "MODIS" else 705.0
    z = math.radians(zen_deg)
    r = math.sqrt((R + H) ** 2 - (R * math.sin(z)) ** 2) - R * math.cos(z)
    scan = math.degrees(math.asin(R / (R + H) * math.sin(z)))
    f_track = r / H
    f_scan = (r / H) / math.cos(z)
    if sensor != "MODIS":
        agg = 3.0 if scan < 31.589 else (2.0 if scan < 44.680 else 1.0)
        f_scan = f_scan * agg / 3.0
    return f_scan, f_scan * f_track


def cargar_ref():
    ref = {}
    for nombre, path in (("ocr", OCR), ("cons", CONS)):  # cons pisa a ocr
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            if "hill" not in r["Volcan"].lower():
                continue
            t = r["Fecha_Satelite_UTC"]
            if not (DESDE <= t[:16] <= HASTA):
                continue
            if not r["Tipo_Registro"].startswith("ALERTA"):
                continue
            k = (t[:16], bucket(r["Sensor"]))
            prev = ref.get(k, {})
            ref[k] = {
                "vrp": float(r["VRP_MW"] or 0), "fuente": nombre, "tipo": r["Tipo_Registro"],
                "dist": r.get("Distancia_km", ""), "clase": r.get("Clasificacion Mirova", ""),
                "zen_ocr": r.get("Zenith_Sat_deg") or prev.get("zen_ocr", ""),
            }
    return ref


def miembros_cumulo(pc, pix):
    """Reconstruye los pixeles del cumulo (n<=3) buscando el subconjunto cuyo promedio de lat/lon es el
    centroide persistido (redondeo 1e-5). Devuelve la lista o None si no hay subconjunto unico."""
    n = pc.get("n_pixels") or 0
    if n < 1 or n > 3 or not pix:
        return None
    cand = [p for p in pix if p.get("lat") is not None]
    hits = []
    for comb in itertools.combinations(range(len(cand)), n):
        la = sum(cand[i]["lat"] for i in comb) / n
        lo = sum(cand[i]["lon"] for i in comb) / n
        if abs(round(la, 5) - pc["centroid_lat"]) <= 1.5e-5 and abs(round(lo, 5) - pc["centroid_lon"]) <= 1.5e-5:
            hits.append([cand[i] for i in comb])
            if len(hits) > 1:
                return None
    return hits[0] if hits else None


def main():
    ref = cargar_ref()
    recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
    print("perfil=%s ENABLE_SINGLE_PIXEL_SUB_MW_MODE=%s SUB_MW_REGIME_THRESHOLD_MW=%s SINGLE_PIXEL_MAX_CLUSTER_PIXELS=%s"
          % (P.PROFILE_NAME, P.ENABLE_SINGLE_PIXEL_SUB_MW_MODE, P.SUB_MW_REGIME_THRESHOLD_MW, P.SINGLE_PIXEL_MAX_CLUSTER_PIXELS))
    print("PATH_D_ONLY_CAP_MW=%s PATH_D_ONLY_CAP_TBG_MAX_K=%s ENABLE_LOCAL_KERNEL_BG=%s ENABLE_VRP_BG_NEIGHBOR_MEAN_V375=%s V750=%s"
          % (P.PATH_D_ONLY_CAP_MW, P.PATH_D_ONLY_CAP_TBG_MAX_K, P.ENABLE_LOCAL_KERNEL_BG,
             P.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375, P.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750))
    print("sha256[:16] consolidado=%s ocr=%s" % (sha(CONS), sha(OCR)))
    nuestros = {}
    for r in recs:
        if not (DESDE <= r["datetime_utc"][:16] <= HASTA):
            continue
        k = (r["datetime_utc"][:16], bucket(r["sensor"]))
        nuestros.setdefault(k, []).append(r)
    colis = {k: v for k, v in nuestros.items() if len(v) > 1}
    print("records en ventana=%d claves=%d claves con mas de un record=%d" % (
        sum(len(v) for v in nuestros.values()), len(nuestros), len(colis)))

    filas, sin_par = [], []
    for k in sorted(ref):
        m = ref[k]
        if k not in nuestros:
            sin_par.append((k, m))
            continue
        for r in nuestros[k]:
            b = k[1]
            lam, kw, A = CONST[b]
            pc = r.get("primary_cluster") or {}
            pix = r.get("anomaly_pixels") or []
            t_bg = r.get("t_bg_k")
            Lbg_anillo = planck(t_bg, lam) if t_bg else float("nan")
            # control de reconstruccion: fondo implicito por pixel
            dev = []
            for p in pix:
                if p["vrp_mw"] > 0.001:
                    L = planck(p["bt_k"], lam)
                    Lbg_impl = L - p["vrp_mw"] * 1e6 / (A * kw)
                    dev.append(abs(Lbg_impl - Lbg_anillo) / Lbg_anillo)
            rec_ok = (max(dev) if dev else float("nan"))
            f5 = r.get("f5_core_vrp_mw")
            pub = f5 if (b == "VIIRS375" and f5 is not None) else pc.get("vrp_mw")
            spm = pc.get("single_pixel_mode")
            miem = miembros_cumulo(pc, pix) if spm else None
            pc_sum = sum(p["vrp_mw"] for p in miem) if miem else pc.get("vrp_mw")
            lista = sum(p["vrp_mw"] for p in pix)
            inner = sum(p["vrp_mw"] for p in pix if p["dist_km"] <= INNER_KM)
            nobg_lista = sum(A * kw * planck(p["bt_k"], lam) / 1e6 for p in pix)
            nobg_inner = sum(A * kw * planck(p["bt_k"], lam) / 1e6 for p in pix if p["dist_km"] <= INNER_KM)
            btmax = max((p["bt_k"] for p in pix), default=float("nan"))
            peak = max(pix, key=lambda p: p["vrp_mw"]) if pix else None
            frac_bg_peak = Lbg_anillo / planck(peak["bt_k"], lam) if peak else float("nan")
            fs, fa = huella(r["sensor_zenith_deg"], b) if r.get("sensor_zenith_deg") is not None else (float("nan"),) * 2
            sha_r = (r.get("regimen") or {}).get("codigo_sha", "")[:9]
            reg = "K" if sha_r else "C0"
            filas.append({
                "t": k[0], "b": b, "sat": r["sensor"], "zen": r.get("sensor_zenith_deg"), "zen_ocr": m["zen_ocr"],
                "reg": reg, "mir": m["vrp"], "fuente": m["fuente"], "dist_mir": m["dist"],
                "pub": pub, "pc": pc.get("vrp_mw"), "pc_sum": pc_sum, "pc_n": pc.get("n_pixels"), "spm": spm,
                "miem_ok": bool(miem), "d9": bool(pc.get("d9_capped")), "scene": r.get("vrp_mw"), "lista": lista,
                "inner": inner, "n_anom": r.get("n_anomalous_pixels"), "n_list": len(pix),
                "n_clu": r.get("n_hotspots_clustered"), "pc_dist": pc.get("centroid_dist_km"),
                "src": r.get("final_hotspot_source"), "t1": r.get("triggered_test1"), "t_bg": t_bg,
                "Lbg_local": r.get("diag_L_bg_local_w_m2_sr_um"), "btmax": btmax, "frac_bg": frac_bg_peak,
                "nobg_lista": nobg_lista, "nobg_inner": nobg_inner, "fs": fs, "fa": fa, "rec_dev": rec_ok,
                "n_bt": r.get("n_bt_path"), "n_nti": r.get("n_nti_path"), "n_ctx": r.get("n_dnti_ctx_path"),
                "techo": btmax >= TECHO[b] if btmax == btmax else False,
            })

    hdr = ("pasada b reg zen zenOCR MIR fuente distMIR | pub pc pc_sum n spm d9 | escena lista inner n_anom n_lis nclu "
           "pcdist | t_bg btmax fbg | Rpub Rpcsum Rinner Rnobg | fs fa | dev")
    print(hdr)
    for f in filas:
        def R(x):
            return (x / f["mir"]) if (x is not None and f["mir"]) else float("nan")
        print("%s %-8s %-2s %5.1f %5s %6.2f %-4s %5s | %6.2f %6.2f %6.2f %3s %-5s %-5s | %6.2f %6.2f %6.2f %4s %3d %2s %5s | %6.1f %6.1f %4.2f | %4.2f %4.2f %4.2f %4.2f | %4.2f %4.2f | %.0e" % (
            f["t"], f["b"], f["reg"], f["zen"] or float("nan"), f["zen_ocr"] or "-", f["mir"], f["fuente"], f["dist_mir"] or "-",
            f["pub"] if f["pub"] is not None else float("nan"), f["pc"] if f["pc"] is not None else float("nan"),
            f["pc_sum"] if f["pc_sum"] is not None else float("nan"), f["pc_n"], f["spm"], f["d9"],
            f["scene"] or 0, f["lista"], f["inner"], f["n_anom"], f["n_list"], f["n_clu"], f["pc_dist"],
            f["t_bg"] or float("nan"), f["btmax"], f["frac_bg"],
            R(f["pub"]), R(f["pc_sum"]), R(f["inner"]), R(f["nobg_inner"]), f["fs"], f["fa"], f["rec_dev"]))
    print("\nALERTAS MIROVA SIN RECORD PAREADO AL MINUTO (n=%d):" % len(sin_par))
    for k, m in sin_par:
        print("  %s %-8s %6.2f %s %s" % (k[0], k[1], m["vrp"], m["fuente"], m["tipo"]))
    json.dump(filas, open(os.path.join(os.path.dirname(__file__), "pareo_pasadas.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
