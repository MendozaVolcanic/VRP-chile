# -*- coding: utf-8 -*-
"""S162, A/B de MxD03, P3 del §6 / §7 del pre-registro: la vara VIIRS (fisica), con el instrumento de la tarea 1.23 sin
cambios (construir_vara_viirs.py para armarla, evaluar_sola.vara lectura 3 para leerla), aplicada al censo de este A/B.

POR QUE. La pregunta de la vara es fisica: la noche en que MIROVA alerto una pasada MODIS, donde esta el objeto caliente
segun OTRO sensor (VIIRS 375 m, otra geolocalizacion por pixel, la misma noche), y cual de las dos geolocalizaciones
MODIS pone el pixel MODIS mas caliente (elegido por indice: el mismo pixel fisico del L1B en todos los brazos) mas
cerca. Solo DETIENE el ciclo (INTERP MAS CERCA con el mismo signo en Terra y Aqua); no adopta nada. Decide bajo 35 grados
(nulo comparable); sobre 35 grados es descriptiva (bow tie).

Dos modos:
  --construir   ANTES del despacho: arma vara_viirs_mxd03.json con las pasadas VIIRS 375 publicadas y no-Test 1, a 6 h
                o menos de cada alerta MODIS del censo (protegida o bajo 1 MW), en sus niveles estricto (MIROVA alerto la
                pasada VIIRS) y amplio. Usa los JSON del main congelado y la referencia congelada (sha256 del MANIFIESTO).
  --evaluar     DESPUES del A/B: lee las filas del arnes (campo `pico`) y corre evaluar_sola.vara (lectura 3) sobre las
                alertas con cenit <= 35 (decide) y sobre todas (descriptiva). Escribe vara_resultado.json para el
                evaluador.

Las dos preguntas del instrumento: (1) si la vara no tuviera pasadas, evaluar_sola.vara da SIN VARA (minimos de 10
granulos y 5 noches) y el evaluador lo lee como «no detiene» con la marca SIN VARA; (2) si la posicion del pico no
cambiara entre brazos, dd = 0 en todas y el estado seria INDECIDIBLE, nunca un lado.

Uso: python -I vara_mxd03.py --construir --ref D:/vrp-trabajo/temporales/s162_mxd03/ref
     python -I vara_mxd03.py --evaluar --art DIR_ARTEFACTOS
"""
import argparse
import glob
import hashlib
import io
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIR_123 = RAIZ / "experiments/_s151_mxd03_sola_123"
# al final de sys.path: _s151_mxd03_etiquetas trae otro evaluar_mxd03.py (el de la 1.17) que no puede tapar al de esta
# carpeta (verificador VMX-06)
for p in (DIR_123, RAIZ / "experiments/_s151_mxd03_cumulo_121", RAIZ / "experiments/_s151_mxd03_etiquetas",
          RAIZ / "scripts", RAIZ):
    sys.path.append(str(p))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

CENIT = 35.0


def construir(ref):
    import construir_vara_viirs as CV          # resumir_noche, VENTANA_H, VIIRS375: sin copiar
    import banco_paridad as bp
    from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
    from pipeline.geo_utils import get_detection_anchor
    import run_pipeline as rp
    from referencia_mirova_unificada import cargar_referencia_unificada
    pob = json.load(open(AQUI / "poblacion.json", encoding="utf-8"))
    for n, v in pob["referencia"].items():
        h = hashlib.sha256((Path(ref) / n).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if h != v["sha256_lf"]:
            sys.exit(f"{n}: sha256 distinto del congelado")
    filas_ref = cargar_referencia_unificada(Path(ref) / "registro_vrp_consolidado.csv", Path(ref) / "registro_vrp_ocr.csv")
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    ventana = pob["ventana"]
    por_vb, ns, nv, _ = bp.indexar_referencia(filas_ref, coords, ventana, regla_minimas="SN")
    alertas = [(g["clave"], f) for g in pob["granulos"] for f in g["records"] if f["lab"] in ("protegida", "bajo1")]
    salida = {"meta": {"main_congelado": pob["checkout"], "referencia": pob["referencia"], "ventana_h": CV.VENTANA_H,
                       "sensores": list(CV.VIIRS375), "regla_minimas": "SN", "excluye_fuente": "test1*",
                       "instrumento": "experiments/_s151_mxd03_sola_123/construir_vara_viirs.py (resumir_noche)"},
              "granulos": {}, "resumen": {}}
    por_vol = {}
    for vol in sorted({f["vol"] for _, f in alertas}):
        volcan = rp.load_volcanoes(vol)[0]
        vent = get_detection_anchor(volcan)
        recs = json.loads((RAIZ / "data/mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))["records"]
        lo = (datetime.fromisoformat(ventana[0]) - timedelta(days=1)).strftime("%Y-%m-%d")
        hi = (datetime.fromisoformat(ventana[1]) + timedelta(days=1)).strftime("%Y-%m-%d")
        viirs = [r for r in recs if r.get("sensor") in CV.VIIRS375 and lo <= (r.get("datetime_utc") or "")[:10] <= hi
                 and (r.get("primary_cluster") or {}).get("centroid_lat") is not None]
        for r in viirs:
            r["_dt"] = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        viirs = [r for r in viirs if not es_pasada_diurna_descartada("VIIRS375", coords[vol][0], coords[vol][1], r["_dt"])]
        casos = []
        for r in viirs:
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
        for r, p in zip(viirs, bp.correr_node(casos) if casos else []):
            r["_pub"] = int(p[4])
        t = [{"vol": vol, "b": "VIIRS375", "dt": r["_dt"], "noche": r["_dt"].strftime("%Y-%m-%d")} for r in viirs]
        bp.etiquetar(t, por_vb, ns, nv)
        for r, e in zip(viirs, t):
            r["_lab"] = e["lab"]
        n_est = 0
        for clave, f in [(c, f) for c, f in alertas if f["vol"] == vol]:
            tg = datetime.strptime(f["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            cerca = [r for r in viirs if abs((r["_dt"] - tg).total_seconds()) <= CV.VENTANA_H * 3600 and r["_pub"] == 1
                     and not str(r.get("final_hotspot_source") or "").startswith("test1")]
            fila = {}
            for nivel, sel in (("amplia", cerca), ("estricta", [r for r in cerca if r["_lab"] == "pos"])):
                pas = [{"lat": r["primary_cluster"]["centroid_lat"], "lon": r["primary_cluster"]["centroid_lon"],
                        "datetime_utc": r["datetime_utc"], "sensor": r["sensor"], "lab": r["_lab"],
                        "pc_vrp": r["primary_cluster"].get("vrp_mw"), "cenit": r.get("sensor_zenith_deg"),
                        "fuente": r.get("final_hotspot_source")} for r in sel]
                fila[nivel] = {"noche": CV.resumir_noche(pas, vent), "pasadas": pas}
            n_est += bool(fila["estricta"]["pasadas"])
            fila.update({"vent": list(vent), "lab_modis": "pos", "prot": f["lab"] == "protegida", "z": f["z"]})
            salida["granulos"]["%s|%s" % (vol, clave)] = fila
        por_vol[vol] = {"alertas": sum(1 for _, x in alertas if x["vol"] == vol), "con_vara_estricta": n_est}
        print(vol, por_vol[vol], flush=True)
    salida["resumen"] = por_vol
    le35 = [k for k, v in salida["granulos"].items() if v["estricta"]["pasadas"] and v["z"] is not None and v["z"] <= CENIT]
    salida["resumen"]["total"] = {"alertas": len(alertas),
                                  "con_vara_estricta": sum(v["con_vara_estricta"] for v in por_vol.values()),
                                  "con_vara_estricta_cenit_le35": len(le35)}
    print("total", salida["resumen"]["total"])
    (AQUI / "vara_viirs_mxd03.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print("escrito", AQUI / "vara_viirs_mxd03.json")


def a_formato_123(f):
    """Una fila del arnes con los nombres que lee evaluar_sola.vara (1.23)."""
    return {"volcan": f["vol"], "clave": f["clave"], "lab": "pos" if f.get("lab") in ("protegida", "bajo1") else f.get("lab"),
            "pico": f.get("pico"), "sensor": f.get("sensor"), "datetime_utc": f["dt"], "sensor_zenith_deg": f.get("z")}


def evaluar(art):
    import evaluar_sola as ES
    tabla = json.load(open(AQUI / "vara_viirs_mxd03.json", encoding="utf-8"))
    filas = []
    for p in sorted(glob.glob(str(Path(art) / "**" / "ab_parte*.jsonl"), recursive=True)):
        filas += [json.loads(x) for x in open(p, encoding="utf-8")]
    ok = [a_formato_123(f) for f in filas if f.get("tipo") == "record" and f.get("estado") == "ok"]
    decide = ES.vara([f for f in ok if f["sensor_zenith_deg"] is not None and f["sensor_zenith_deg"] <= CENIT], tabla)
    todas = ES.vara(ok, tabla)
    out = {"estado": decide["estado"], "decide_le35": {k: v for k, v in decide.items() if k != "granulos"},
           "descriptiva_todas": {k: v for k, v in todas.items() if k != "granulos"}}
    (Path(art) / "vara_resultado.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str),
                                                   encoding="utf-8")
    print("vara (<= 35, decide):", decide["estado"], "| n", decide.get("n"), "noches", decide.get("n_noches"))
    print("vara (todas, describe):", todas["estado"])


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--construir", action="store_true")
    ap.add_argument("--evaluar", action="store_true")
    ap.add_argument("--ref")
    ap.add_argument("--art")
    a = ap.parse_args()
    if a.construir:
        construir(a.ref)
    if a.evaluar:
        evaluar(a.art)


if __name__ == "__main__":
    main()
