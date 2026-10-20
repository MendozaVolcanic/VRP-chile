# -*- coding: utf-8 -*-
r"""Verificador S157 1.29. Poblaciones que el 'rescatable' de sustrato_k.py no ve, sobre la MISMA copia unida K.

Uso: python v1_poblaciones_ocultas.py --kunido D:\vrp-trabajo\temporales\verif_s157\k_unido > v1_salida.txt
Cuenta, por ventana y sensor (pasadas nocturnas no publicadas por K):
  (a) cúmulo primario FUERA del inner (o dc far) y al menos un píxel guardado (anomaly_pixels o
      discarded_anomaly_pixels) con dist_km <= inner y vrp_mw == 0: un cúmulo del cráter mudo que el ranking
      vent_anchored saltó porque tiene VRP 0 (clustering.py: ranking_set = cúmulos con vrp > 0). D25 puede
      darle VRP > 0, volverlo primario y publicarlo. dist_km del píxel es desde volcano_lat/lon (aprox.).
  (b) ocultas por isThermalArtifact (summit y válida, pero filtro de cirrus o de campo difuso): D25 puede
      BAJAR su magnitud bajo el umbral del filtro y publicarlas.
  (c) protegidas A que K publica y que descansan SOLO en OCR de Suomi NPP (no deciden en V1, A119).
  (d) pares de magnitud de VIIRS 375 por tramo de cenit y volcán, y cuántos son de volcanes con kernel local.
"""
import argparse, collections, json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import sustrato_k as sk  # noqa
fk, bp = sk.fk, sk.bp
KERNEL = {"PuyehueCordonCaulle", "Villarrica", "Chaiten", "PlanchonPeteroa", "Lastarria"}


def crudos(kdir):
    out = {}
    for v in bp.VOLS:
        p = Path(kdir) / (v + ".json")
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            out[(v, bp.bucket(r.get("sensor")), r["datetime_utc"][:16])] = r
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kunido", required=True); a = ap.parse_args()
    raw = crudos(a.kunido)
    inner = bp.inner_desde_html()
    for nombre, (desde, hasta, ref, solo) in sk.VENTANAS.items():
        filas = fk.cargar_filas(ref, solo)
        recs, _ = fk.etiquetar_todo(a.kunido, filas, (desde, hasta), set(bp.VOLS))
        recs = [r for r in recs if not (r["vol"] == "NevadosDeChillan" and r["noche"] < sk.FRONTERA_K)]
        casos, raws = [], []
        for r in recs:
            rr = raw[(r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))]
            raws.append(rr)
            slim = {k: rr.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if rr.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (rr.get("anomaly_pixels") or [])]
            casos.append([slim, inner[r["vol"]]])
        pred = bp.correr_node(casos)
        c = collections.defaultdict(collections.Counter); ej = collections.defaultdict(list)
        pares = collections.defaultdict(collections.Counter)
        for r, rr, p in zip(recs, raws, pred):
            summit, valid, art, disp, pub = p
            assert pub == r["pub"], "predicado distinto al del sustrato"
            s = r["b"]; lab = r["lab"]
            if lab not in ("pos", "neg_limpio"):
                continue
            pc = rr.get("primary_cluster") or {}
            pcd = pc.get("centroid_dist_km")
            if not pub:
                fuera = (pcd is not None and pcd > inner[r["vol"]]) or r["dc"] == "far"
                pix = (rr.get("anomaly_pixels") or []) + (rr.get("discarded_anomaly_pixels") or [])
                mudo_dentro = [q for q in pix if (q.get("dist_km") is not None and q["dist_km"] <= inner[r["vol"]]
                                                   and (q.get("vrp_mw") or 0) == 0)]
                if fuera and mudo_dentro:
                    c[s]["a_" + lab] += 1
                    ej[(s, "a")].append("%s %s %s pc %.1f km vrp %s | %d px mudos dentro" % (
                        r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), lab, pcd if pcd is not None else -1, pc.get("vrp_mw"), len(mudo_dentro)))
                if summit and valid and art:
                    c[s]["b_" + lab] += 1
                    ej[(s, "b")].append("%s %s %s disp %.2f t_max %s n_px %s" % (
                        r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), lab, disp, rr.get("t_max_k"), pc.get("n_pixels")))
                if sk.rescatable(r, inner):
                    c[s]["resc_" + lab] += 1  # control: debe reproducir rescN/rescP del sustrato (disjunto de a)
                    assert not fuera
            if lab == "pos" and r["prot_A"] and pub:
                c[s]["pA_pub"] += 1
                c[s]["pA_pub_solo_ocr_snpp"] += r["prot_A_solo_ocr_snpp"]
            if lab == "pos" and pub and r.get("vrp_ref"):
                pares[(s, sk.tramo40(r))]["total"] += 1
                pares[(s, sk.tramo40(r))]["kernel" if r["vol"] in KERNEL else "otro"] += 1
                pares[(s, sk.tramo40(r))]["Chillan"] += r["vol"] == "NevadosDeChillan"
                if s == "VIIRS375" and r["z"] is not None and 30 <= r["z"] <= 40:
                    pares[(s, "30-40")]["total"] += 1
        print("\n######## %s %s a %s" % (nombre, desde, hasta))
        for s in sk.SENS:
            print("  %-8s %s" % (s, dict(c[s])))
        for (s, t), x in sorted(pares.items()):
            print("  pares %s %-10s %s" % (s, t, dict(x)))
        for k, l in sorted(ej.items()):
            print("  ejemplos %s (%d):" % (k, len(l)))
            for e in l[:12]:
                print("     " + e)


if __name__ == "__main__":
    main()
