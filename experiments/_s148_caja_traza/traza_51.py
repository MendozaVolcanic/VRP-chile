"""S148 - por que los negativos limpios publicados fuera de la caja sobreviven al brazo G.

FENOMENO. El brazo G aplica el umbral estricto (0,010) fuera de una caja de 5 x 5 km. Si un
pixel tibio de la corona (entre la caja y el circulo inner) se sigue publicando, o su exceso
supera el piso estricto, o entra por una etapa que no mira la caja.

QUE MIDE. Para cada pasada VIIRS 375 publicada por el control B (neg_limpio fuera / dentro de la
caja, y pos), compara el record crudo de B y de G: pixeles del primer pase, recaptura del segundo
pase, pixeles anomalos dentro/fuera de la caja y del circulo inner, y el exceso de BT de cada
pixel sobre el fondo (el primer pase exige bt > t_bg + 3 K; un pixel con menos NO pudo entrar
por el primer pase).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el brazo no cambiara nada? Corrido con el control contra si mismo da cero diferencias.
2. Si estuviera muerto? Los denominadores (51 fuera, 44 dentro, 125 pos) deben coincidir con
   los de lectura_caja.py; y con el brazo de la conectiva los campos deben diferir.

Reusa experiments/_s148_caja/lectura_caja.py; datos: copia local de trabajo prelim_s148 (no esta en git).
Uso: PYTHONIOENCODING=utf-8 python experiments/_s148_caja_traza/traza_51.py [brazo]
"""
from __future__ import annotations
import json
import math
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_LC = ROOT / "experiments" / "_s148_caja" / "lectura_caja.py"
if _LC.exists():
    src = _LC.read_text(encoding="utf-8")
else:  # antes del merge vivia solo en la rama
    src = subprocess.run(["git", "show", "origin/s148-lectura-caja:experiments/_s148_caja/lectura_caja.py"],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
lc = types.ModuleType("lectura_caja")
lc.__file__ = str(ROOT / "experiments" / "_s148_caja" / "lectura_caja.py")
exec(compile(src, lc.__file__, "exec"), lc.__dict__)
bp = lc.bp

RUN = "prelim_s148"
CONTROL, BRAZO = "_s146_ab_sin_test1", "_s147_ab_sin_test1_caja"
if len(sys.argv) > 1:
    BRAZO = sys.argv[1]
V = ("2026-09-01", "2026-09-17")
D = lc.LECTURA / "experiments" / "_s146_ab_sin_test1" / "salidas" / RUN
GATE_K = 3.0  # NTI_BT_SANITY_K leido de pipeline.profile con los dos perfiles


def crudos(brazo):
    out = {}
    for vol in bp.VOLS:
        p = D / brazo / f"{vol}.json"
        if p.exists():
            for r in json.load(open(p, encoding="utf-8"))["records"]:
                out[(vol, r.get("granule"))] = r
    return out


def px_cumulo(r):
    """pixeles del cumulo publicado: anomaly_pixels cerca del centroide del primary_cluster."""
    pc = r.get("primary_cluster") or {}
    if pc.get("centroid_lat") is None:
        return []
    out = []
    radio = 0.6 * max(1, (pc.get("n_pixels") or 1)) ** 0.5
    for q in r.get("anomaly_pixels") or []:
        dy = (q["lat"] - pc["centroid_lat"]) * 111.0
        dx = (q["lon"] - pc["centroid_lon"]) * 111.0 * math.cos(math.radians(q["lat"]))
        if math.hypot(dx, dy) <= radio:
            out.append(q)
    return out


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = lc.cargar_referencia_unificada(lc.CONGELADO / "registro_vrp_consolidado.csv",
                                           lc.CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
    anc = lc.anclas()

    def carga(br):
        recs = lc.cargar_brazo(D / br, coords, inner, V)
        bp.etiquetar(recs, por_vb, ns, nv)
        return {lc.clave(r): r for r in recs}

    C, B = carga(CONTROL), carga(BRAZO)
    assert set(C) == set(B), "cobertura no exacta"
    RC, RB = crudos(CONTROL), crudos(BRAZO)
    print(f"control {CONTROL} | brazo {BRAZO} | tramo {V} | pasadas {len(C)}")

    grupos = {}
    for k, rc in C.items():
        if rc["b"] != "VIIRS375" or rc["lab"] not in ("neg_limpio", "pos") or not rc["pub"]:
            continue
        donde = "dentro" if lc.en_caja(rc["pc_lat"], rc["pc_lon"], anc[k[0]]) else "fuera"
        grupos.setdefault((rc["lab"], donde), []).append(k)

    for g, ks in sorted(grupos.items()):
        print(f"\n===== {g[0]} / cumulo del control {g[1]} de la caja: {len(ks)} pasadas =====")
        cnt = Counter()
        difs = Counter()
        exc_G = []
        tot = {"fp": [0, 0], "sp": [0, 0], "an": [0, 0]}
        det = []
        for k in ks:
            vol = k[0]
            rb_, rg_ = RC[(vol, C[k]["granule"])], RB[(vol, B[k]["granule"])]
            fpb, fpg = rb_.get("diag_n_first_pass_pixels") or 0, rg_.get("diag_n_first_pass_pixels") or 0
            spb, spg = rb_.get("diag_n_second_pass_recapture") or 0, rg_.get("diag_n_second_pass_recapture") or 0
            anb, ang = rb_.get("n_anomalous_pixels") or 0, rg_.get("n_anomalous_pixels") or 0
            tot["fp"][0] += fpb; tot["fp"][1] += fpg
            tot["sp"][0] += spb; tot["sp"][1] += spg
            tot["an"][0] += anb; tot["an"][1] += ang
            cnt["B: primer pase = 0 pixeles en toda la escena"] += int(fpb == 0)
            cnt["G: primer pase = 0 pixeles en toda la escena"] += int(fpg == 0)
            cnt["G: recaptura del 2do pase > 0"] += int(spg > 0)
            cnt["primer pase pierde pixeles en G respecto de B"] += int(fpg < fpb)
            cnt["2do pase gana pixeles en G respecto de B"] += int(spg > spb)
            cnt["lo que pierde el 1er pase == lo que gana el 2do"] += int(fpb - fpg == spg - spb)
            cnt["n_anomalous_pixels igual en B y G"] += int(anb == ang)
            pcb, pcg = rb_.get("primary_cluster") or {}, rg_.get("primary_cluster") or {}
            cnt["cumulo primario identico (lat, lon, vrp, n_pixels)"] += int(
                all(pcb.get(f) == pcg.get(f) for f in ("centroid_lat", "centroid_lon", "vrp_mw", "n_pixels")))
            cg = px_cumulo(rg_)
            tg = rg_.get("t_bg_k")
            eg = max((q["bt_k"] - tg for q in cg), default=None) if tg is not None else None
            if eg is not None:
                exc_G.append(eg)
            cnt["G: cumulo publicado identificado entre los anomaly_pixels"] += int(bool(cg))
            cnt["G: pixel mas caliente del cumulo con exceso BT < 3 K (no pudo entrar por el 1er pase)"] += int(
                eg is not None and eg < GATE_K)
            cnt["G: cumulo con TODOS sus pixeles fuera de la caja"] += int(
                bool(cg) and not any(lc.en_caja(q["lat"], q["lon"], anc[vol]) for q in cg))
            cnt["G: cumulo con todos sus pixeles dentro del circulo inner"] += int(
                bool(cg) and all(q["dist_km"] <= inner[vol] for q in cg))
            for f in rb_:
                if f.startswith("diag_") or f in ("n_anomalous_pixels", "vrp_mw", "vrp_mir_mw", "n_hotspots_clustered"):
                    if rb_.get(f) != rg_.get(f):
                        difs[f] += 1
            px = rg_.get("anomaly_pixels") or []
            n_caja = sum(lc.en_caja(q["lat"], q["lon"], anc[vol]) for q in px)
            det.append((vol, k[2], fpb, fpg, spb, spg, anb, ang, len(px), n_caja, len(px) - n_caja,
                        None if eg is None else round(eg, 2), pcg.get("n_pixels"),
                        pcg.get("centroid_dist_km"), inner[vol]))
        for a, b in cnt.items():
            print(f"  {a}: {b} de {len(ks)}")
        print(f"  suma pixeles primer pase  B={tot['fp'][0]}  G={tot['fp'][1]}")
        print(f"  suma recaptura 2do pase   B={tot['sp'][0]}  G={tot['sp'][1]}")
        print(f"  suma n_anomalous_pixels   B={tot['an'][0]}  G={tot['an'][1]}")
        if exc_G:
            s = sorted(exc_G)
            print(f"  exceso BT (K) del pixel mas caliente del cumulo publicado en G: min {s[0]:.2f} "
                  f"mediana {s[len(s) // 2]:.2f} max {s[-1]:.2f} (n={len(s)}); "
                  f"con exceso >= 3 K: {sum(1 for x in s if x >= GATE_K)}")
        print("  campos que difieren entre B y G (n pasadas):", dict(difs.most_common()))
        if g == ("neg_limpio", "fuera"):
            print("  detalle: vol, hora, fp_B, fp_G, sp_B, sp_G, anom_B, anom_G, px_persistidos_G, en_caja, "
                  "fuera_caja, exceso_BT_cumulo_G, n_px_cumulo, dist_cumulo_km, inner_km")
            for f in sorted(det):
                print("   ", *f)


if __name__ == "__main__":
    main()
