# Tarea 1.21: prediccion pre-registrada del brazo CC (etiqueta desde el cumulo, posicion de produccion)
# sobre la POBLACION entera de la 1.17 (5.395 granulos), con los records guardados. No decide nada: fija
# antes de correr cuanto deberia mover la etiqueta, y sirve de control del estimador (README, "Control
# del estimador con respuesta conocida").
#
# POR QUE SE PUEDE PREDECIR SIN L1B. `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` solo cambia la etiqueta:
# `derivar_distance_class` (pipeline/process_modis.py:300) la saca del centroide del cumulo en vez del
# hotspot final, y nada aguas arriba la lee (tests/test_distance_class_modis_s132.py). store.py no lee
# el flag: despues de la etiqueta aplica tres reglas que tampoco dependen de el (rescate F47 con su
# cerca de radius_km, store.py:393; regla D del vent, :479; guard A46, :514). Con el cumulo presente, la
# etiqueta final del brazo CC es por eso:
#   summit si el cumulo esta dentro del inner;
#   far si esta fuera y tiene energia (guard A46);
#   summit si esta fuera, sin energia, y el vent-path vio algo (regla D);
#   la de produccion si no hay cumulo (derivar cae al hotspot final).
# `replay_cumulo` aplica eso a un record guardado. Es un MODELO de la cadena, no la cadena: el probe lo
# compara contra el brazo CC medido sobre el L1B, granulo por granulo ("prueba del replay").
#
# Fuentes fijadas (reproducible): records de data/mirova_equivalent/ en el commit DATA_COMMIT (el de
# poblacion.json de la 1.17; este script comprueba que reproduce sus N por estrato) y la referencia de
# MIROVA en los commits de Mirova-v1 que guarda poblacion.json.
#
# Uso: python predecir_etiqueta_cumulo.py   (local; necesita git, node y red a raw.githubusercontent.com)
import collections
import copy
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIR_117 = AQUI.parent / "_s151_mxd03_etiquetas"
sys.path.insert(0, str(DIR_117))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import seleccionar_mxd03 as S  # noqa: E402
sys.path.insert(0, str(AQUI))
import modelo_corrimiento as MC  # noqa: E402

DATA_COMMIT = "bca47c6adba2bb8bef4c5154dd1d2ae97ee10778"   # #835, el que genero poblacion.json


def replay_cumulo(rec, inner):
    """Copia de un record guardado con la etiqueta que daria el brazo CC (ver cabecera)."""
    r = copy.deepcopy(rec)
    pc = r.get("primary_cluster") or {}
    d = pc.get("centroid_dist_km")
    if d is None or inner is None or r.get("distance_class") is None:
        return r
    if d <= inner:
        r["distance_class"] = "summit"
    elif (pc.get("vrp_mw") or 0) > 0:
        r["distance_class"] = "far"
    elif (r.get("vrp_vent_mw") or 0) > 0:
        r["distance_class"] = "summit"
    else:
        r["distance_class"] = "far"
    return r


def _slim(r, bp):
    s = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    s["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                           for p in (r.get("anomaly_pixels") or [])]
    return s


def _records(vol):
    txt = subprocess.run(["git", "-C", str(RAIZ), "show", f"{DATA_COMMIT}:data/mirova_equivalent/{vol}.json"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return json.loads(txt)["records"]


def poblacion_de(recs):
    """Los mismos granulos que seleccionar_mxd03.construir_poblacion: MODIS, ventana, uno por clave."""
    vistos = {}
    for r in recs:
        if not (r.get("sensor") or "").startswith("MODIS"):
            continue
        if not (S.VENTANA[0] <= (r.get("datetime_utc") or "")[:10] <= S.VENTANA[1]):
            continue
        k = S.clave_granulo(r)
        if k is not None:
            vistos.setdefault(k, r)
    return vistos


def main():
    import banco_paridad as bp
    from auto_audit_weekly import _coords_por_volcan
    from clase_mirova import alerta_protegida
    from referencia_mirova_unificada import URL_RAW, cargar_referencia_unificada
    pob = json.load(open(DIR_117 / "poblacion.json", encoding="utf-8"))
    ref = pob["meta"]["referencia"]
    tmp = Path(tempfile.mkdtemp())
    cons, ocr = tmp / "registro_vrp_consolidado.csv", tmp / "registro_vrp_ocr.csv"
    urllib.request.urlretrieve(URL_RAW.format(sha=ref["commit_cons"], nombre=cons.name), cons)
    urllib.request.urlretrieve(URL_RAW.format(sha=ref["commit_ocr"], nombre=ocr.name), ocr)
    filas_ref = cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas_ref, _coords_por_volcan(), S.VENTANA, regla_minimas="SN")

    salida = {"meta": {"data_commit": DATA_COMMIT, "referencia": ref, "regla_minimas": "SN",
                       "html_sha_git": bp.sha_git(bp.HTML)}, "volcanes": {}, "granulos": {}, "poblacion": {}}
    total = collections.Counter()
    for vol, v in pob["volcanes"].items():
        inner = v["inner_radius_km"]
        pobv = poblacion_de(_records(vol))
        claves = sorted(pobv)
        est = collections.Counter(S.estrato(pobv[k], inner) for k in claves)
        n_igual = dict(est) == {e: sum(x.values()) for e, x in v["N"].items()}
        casos = [[_slim(pobv[k], bp), inner] for k in claves] + \
                [[_slim(replay_cumulo(pobv[k], inner), bp), inner] for k in claves]
        res = bp.correr_node(casos)
        pub_c = [int(p[4]) for p in res[:len(claves)]]
        pub_cc = [int(p[4]) for p in res[len(claves):]]
        muestra = {g["clave"]: g for g in v["muestra"]}
        cuenta = collections.Counter()
        lab_distinto = pub_distinto = 0
        filas_pob = salida["poblacion"].setdefault(vol, [])
        for k, a, b in zip(claves, pub_c, pub_cc):
            r = pobv[k]
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            t = [{"vol": vol, "b": "MODIS", "dt": dt, "noche": dt.strftime("%Y-%m-%d")}]
            bp.etiquetar(t, por_vb, ns, nv)
            prot = any(alerta_protegida(f, lectura="A") for f in bp.parear(por_vb.get((vol, "MODIS"), []), dt))
            lab = t[0]["lab"]
            g = muestra.get(k)
            if g is not None:
                lab_distinto += (g["lab"] != lab) or (g["prot"] != prot)
                pub_distinto += g["pub_guardada"] != a
                salida["granulos"]["%s|%s" % (vol, k)] = {"pub_c_guardada": a, "pub_cc_replay": b}
            filas_pob.append([k, S.estrato(r, inner), lab, int(prot), a, b])
            # por que no se re-estratifica: con la etiqueta del cumulo lo que decide es la distancia del
            # cumulo al limite; se cuenta cuantos records la tienen dentro de la banda del peor caso
            pcd = (r.get("primary_cluster") or {}).get("centroid_dist_km")
            z, az, sen = r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg"), r.get("sensor")
            banda = MC.corrimiento_predicho_traza(z, az, sen) if z is not None and az is not None else None
            banda = (banda if banda is not None else MC.corrimiento_predicho_traza(65.0, 1.0, "MODIS_AQUA")) + 1.0
            cuenta["cumulo_cerca_del_limite"] += int(pcd is not None and abs(pcd - inner) <= banda)
            grupo = "protegida" if prot else lab
            cuenta[grupo + "|n"] += 1
            cuenta[grupo + "|pub_C"] += a
            cuenta[grupo + "|pub_CC"] += b
            cuenta[grupo + "|0->1"] += int(a == 0 and b == 1)
            cuenta[grupo + "|1->0"] += int(a == 1 and b == 0)
        delta = (cuenta["pos|1->0"] - cuenta["pos|0->1"]) + (cuenta["neg_limpio|0->1"] - cuenta["neg_limpio|1->0"])
        salida["volcanes"][vol] = {"n": len(claves), "N_por_estrato_igual_a_poblacion_117": n_igual,
                                   "muestra_lab_o_prot_distinta": lab_distinto,
                                   "muestra_pub_guardada_distinta": pub_distinto,
                                   "cuenta": dict(sorted(cuenta.items())), "delta_errores_CC_vs_C": delta}
        total.update(cuenta)
        total["delta"] += delta
        print(vol, "n", len(claves), "N igual:", n_igual, "| lab/prot distinta en la muestra:", lab_distinto,
              "| pub guardada distinta:", pub_distinto, "| delta CC-C:", delta, flush=True)
    salida["total"] = dict(sorted(total.items()))
    (AQUI / "prediccion_cumulo.json").write_text(json.dumps(salida, indent=0, ensure_ascii=False), encoding="utf-8")
    print("TOTAL", json.dumps(salida["total"], ensure_ascii=False))


if __name__ == "__main__":
    main()
