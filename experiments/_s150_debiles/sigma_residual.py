# -*- coding: utf-8 -*-
"""S150. ¿Las alertas que F pierde se parecen, en los campos del record, al residual que F apaga con razon?
Cuatro grupos VIIRS 375, abril a agosto, mismo instrumento (tabla de armar_tabla + record crudo de B):
  perdidas (alerta de MIROVA, B publica, F no; sin las 5 filas OCR malas)
  conservadas debiles (alerta < 0,10 MW, B y F publican)
  residual apagado (negativo limpio, B publica, F no)        <- lo que `max` arregla
  residual que sobrevive (negativo limpio, B y F publican)
Si perdidas y residual apagado son indistinguibles en sd, cenit, fondo, magnitud y camino, ningun umbral
sobre esas variables los separa: el arreglo tendra que salir de otra informacion (por pixel, o de cambiar
como se calcula la sigma), no de recalibrar C2.

  python sigma_residual.py --tmp <dir del paso 1> --filas filas.json
"""
import argparse, collections, io, json, statistics as st, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MESES = ["abril", "mayo", "junio", "julio", "agosto"]
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}


def auc(pos, neg):
    pos = [x for x in pos if x is not None]; neg = [x for x in neg if x is not None]
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tmp", required=True); ap.add_argument("--filas", required=True); a = ap.parse_args()
    filas = {r["clave"]: r for r in json.load(open(a.filas, encoding="utf-8"))}
    G = collections.defaultdict(list)
    for mes in MESES:
        base = Path(a.tmp) / mes
        crudo = {}
        for p in (base / "_s146_ab_sin_test1").glob("*.json"):
            for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
                s = r.get("sensor") or ""
                if s.startswith("VIIRS") and not s.endswith("_750"):
                    crudo["%s|VIIRS375|%s" % (p.stem, r.get("datetime_utc"))] = r
        T = json.loads((base / "tabla.json").read_text(encoding="utf-8"))["pasadas"]
        for k, v in T.items():
            if "|VIIRS375|" not in k or len(v) != 2 or not v["control"]["pub"] or k in MALAS:
                continue
            c, f = v["control"], v["brazo"]; r = crudo.get(k)
            if r is None:
                continue
            if c["lab"] == "neg_limpio":
                g = "residual que sobrevive a F" if f["pub"] else "residual apagado por F"
            elif c["lab"] == "pos" and k in filas:
                if filas[k]["perdida"]:
                    g = "alerta perdida por F"
                elif (c.get("vrp_ref") or 9) < 0.10:
                    g = "alerta debil conservada"
                else:
                    continue
            else:
                continue
            pc = r.get("primary_cluster") or {}
            ap_ = r.get("anomaly_pixels") or []
            exc = (max(q["bt_k"] for q in ap_) - r["t_bg_k"]) if ap_ and r.get("t_bg_k") else None
            G[g].append({"sd_dnti": r.get("diag_sd_dnti"), "sd_deti": r.get("diag_sd_deti"), "cenit": r.get("sensor_zenith_deg"),
                         "t_bg": r.get("t_bg_k"), "pc_vrp": pc.get("vrp_mw"), "bt_exceso": exc,
                         "solo_2o_pase": int(not r.get("diag_n_first_pass_pixels")), "pc_n": pc.get("n_pixels")})
    def q(xs):
        xs = sorted(x for x in xs if x is not None); n = len(xs)
        return "med %.4g [p25 %.4g, p75 %.4g]" % (st.median(xs), xs[n // 4], xs[(3 * n) // 4]) if n else "-"
    orden = ["alerta perdida por F", "alerta debil conservada", "residual apagado por F", "residual que sobrevive a F"]
    for g in orden:
        print("%-28s n=%d" % (g, len(G[g])))
    for var in ("sd_dnti", "sd_deti", "cenit", "t_bg", "pc_vrp", "bt_exceso", "solo_2o_pase", "pc_n"):
        print("\n%s" % var)
        for g in orden:
            print("   %-28s %s" % (g, q([x[var] for x in G[g]])))
        a1 = auc([x[var] for x in G["alerta perdida por F"]], [x[var] for x in G["residual apagado por F"]])
        a2 = auc([x[var] for x in G["alerta debil conservada"]], [x[var] for x in G["residual apagado por F"]])
        print("   AUC perdida contra residual apagado: %s | debil conservada contra residual apagado: %s" % (
            "-" if a1 is None else "%.2f" % a1, "-" if a2 is None else "%.2f" % a2))


if __name__ == "__main__":
    main()
