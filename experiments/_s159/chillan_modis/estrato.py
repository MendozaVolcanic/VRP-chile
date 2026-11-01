# -*- coding: utf-8 -*-
"""S159 frente Chillan MODIS: estrato de alertas MIROVA MODIS de Nevados de Chillan (septiembre y octubre de 2026)
contra nuestros records publicados, pareo a +-5 min.

Las dos preguntas del instrumento:
1. Si lo que mido estuviera roto (no publicamos ninguna protegida), lo veria? Si: cada alerta sale con su record y el
   predicado del tablero ejecutado con node (banco_paridad.correr_node, sin portar). Control positivo: el estrato
   "alerta MIROVA y publicamos" tiene que tener filas con pub=1 (si el predicado estuviera muerto daria 0 en todas).
2. Si el instrumento estuviera muerto: una alerta sin record nuestro sale como SIN RECORD (no como "no publicada"),
   y el control de identidad del predicado (banco_paridad.control_identidad_predicado) tiene que dar los valores
   esperados ([1,1,0,1,0] y [1,0]).
Denominador: filas de alerta (ALERTA_TERMICA, ALERTA_TERMICA_OCR) de MIROVA MODIS de NevadosDeChillan con fecha de
satelite entre VENTANA[0] y VENTANA[1], de la referencia unificada (consolidado + OCR + historia + respaldo).
Uso: python experiments/_s159/chillan_modis/estrato.py > experiments/_s159/chillan_modis/estrato_salida.txt
"""
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import banco_paridad as BP  # noqa: E402
from clase_mirova import alerta_protegida, TIPOS_ALERTA  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

VOL = "NevadosDeChillan"
VENTANA = ("2026-09-01", "2026-10-21")
TOL = timedelta(minutes=5)
CAMPOS = ("granule", "sensor_zenith_deg", "t_bg_k", "t_max_k", "diag_sigma_bg_k", "diag_n_bg_anillo",
          "diag_n_first_pass_pixels", "diag_n_first_pass_summit", "diag_n_second_pass_recapture",
          "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "diag_nti_bg", "diag_nti_max",
          "diag_t_max_dist_km", "distance_class", "n_anomalous_pixels")


def main():
    ident = BP.control_identidad_predicado()
    print("CONTROL identidad predicado:", ident, "(esperado ([0, 1, 1, 1, 0], [1, 0]), banco_paridad.controles)")
    ref = [f for f in cargar_referencia_unificada()
           if f["volcano"] == VOL and f["sensor_bucket"] == "MODIS"
           and VENTANA[0] <= f["fecha_utc"][:10] <= VENTANA[1]]
    print(f"Filas MIROVA MODIS {VOL} {VENTANA}: {len(ref)}; alertas: "
          f"{sum(f['tipo'] in TIPOS_ALERTA for f in ref)}; protegidas (lectura A): "
          f"{sum(alerta_protegida(f) for f in ref)}")
    d = json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{VOL}.json", encoding="utf-8"))
    recs = [r for r in d["records"] if (r.get("sensor") or "").startswith("MODIS")
            and VENTANA[0] <= r.get("datetime_utc", "")[:10] <= VENTANA[1]]
    inner = BP.inner_desde_html()[VOL]
    casos = []
    for r in recs:
        slim = {k: r.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner])
    pred = BP.correr_node(casos)
    for r, p in zip(recs, pred):
        r["_pub"], r["_disp"] = p[4], p[3]
        r["_dt"] = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
    print(f"Records MODIS nuestros en la ventana: {len(recs)}; publicados: {sum(r['_pub'] for r in recs)}; inner={inner}")

    filas = []
    for f in sorted(ref, key=lambda f: f["fecha_utc"]):
        if f["tipo"] not in TIPOS_ALERTA:
            continue
        t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
        cand = [r for r in recs if abs(r["_dt"] - t) <= TOL]
        cand.sort(key=lambda r: abs(r["_dt"] - t))
        r = cand[0] if cand else None
        pc = (r or {}).get("primary_cluster") or {}
        fila = {"mirova_utc": f["fecha_utc"][:16], "src": f["source"], "tipo": f["tipo"], "vrp_mirova": f["vrp_mw"],
                "dist_mirova": f["dist_km"], "protegida": alerta_protegida(f),
                "nuestro_utc": r["datetime_utc"] if r else None, "n_cand": len(cand),
                "pub": r["_pub"] if r else None, "disp": r["_disp"] if r else None,
                "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km")}
        if r:
            fila.update({k: r.get(k) for k in CAMPOS})
        filas.append(fila)
    print()
    print("ALERTAS MIROVA MODIS y nuestro record a +-5 min:")
    for x in filas:
        print(json.dumps(x, ensure_ascii=False, default=str))
    prot = [x for x in filas if x["protegida"]]
    # una pasada = minuto; consolidar CONS y OCR del mismo minuto
    def pasadas(xs):
        return sorted({x["mirova_utc"] for x in xs})
    pp = pasadas(prot)
    print()
    print(f"PASADAS PROTEGIDAS: {len(pp)}")
    for m in pp:
        xs = [x for x in prot if x["mirova_utc"] == m]
        x = xs[0]
        estado = "SIN RECORD" if x["nuestro_utc"] is None else ("PUBLICADA" if x["pub"] else "NO PUBLICADA")
        print(f"  {m} vrp_mirova={max(y['vrp_mirova'] for y in xs)} dist={x['dist_mirova']} -> {estado} "
              f"granule={x.get('granule')} cenit={x.get('sensor_zenith_deg')} fp={x.get('diag_n_first_pass_pixels')} "
              f"pc_vrp={x['pc_vrp']}")
    np_ = [m for m in pp if not any(x["pub"] for x in prot if x["mirova_utc"] == m)]
    print(f"Protegidas NO publicadas (incluye sin record): {len(np_)} de {len(pp)}")
    todas = pasadas(filas)
    pub_alerta = [m for m in todas if any(x["pub"] for x in filas if x["mirova_utc"] == m)]
    print(f"CONTROL POSITIVO: pasadas con alerta MIROVA (cualquier VRP) publicadas por nosotros: {len(pub_alerta)} de {len(todas)}")
    json.dump(filas, open(Path(__file__).with_name("estrato_tabla.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
