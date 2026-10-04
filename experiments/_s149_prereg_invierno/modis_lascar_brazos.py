# S150. MODIS Lascar marzo-junio: B (banda 21, sin Test 1), J (banda 22), K (banda 22 + max).
# Tasa de publicacion en positivas y en negativos limpios, con intervalo de Wilson 95 %.
# Uso: python modis_lascar_brazos.py <TMP> experiments/_s149_prereg_invierno
#   <TMP> como en determinismo_lascar.py, mas mayo_lascar y <TMP>/mayo_B/Lascar.json (B de Lascar del run
#   35599902448, extraido con git archive con ruta). B de abril, mayo y junio sale del despacho VIIRS del mes.
import json, subprocess, sys, collections, io, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
S = Path(sys.argv[1]); AQ = Path(sys.argv[2]); R = "runs/experiments/_s146_ab_sin_test1/salidas"
B = {"marzo": S/"marzo_lascar"/R/"35632736532/_s146_ab_sin_test1", "abril": S/"abril_B/experiments/_s146_ab_sin_test1/salidas/35639417826/_s146_ab_sin_test1",
     "mayo": S/"mayo_B", "junio": S/"junio"/R/"35675490175/_s146_ab_sin_test1"}
L = {"marzo": ("marzo_lascar", "35632736532", "2026-03-01", "2026-03-31", "marzo_lascar"), "abril": ("abril_lascar", "35648804271", "2026-04-01", "2026-04-30", "abril"),
     "mayo": ("mayo_lascar", "35671459235", "2026-05-01", "2026-05-31", "mayo"), "junio": ("junio_lascar", "35679063864", "2026-06-01", "2026-06-30", "junio")}
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)
def tabla(ctrl, br, d, h, cong, tag):
    C = AQ/"_congelado"/cong; out = S/("mlas_%s.json" % tag)
    subprocess.run([sys.executable, str(AQ/"armar_tabla.py"), "--control", str(ctrl), "--brazo", str(br), "--cons", str(C/"registro_vrp_consolidado.csv"),
                    "--ocr", str(C/"registro_vrp_ocr.csv"), "--desde", d, "--hasta", h, "--out", str(out)], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return {k: v for k, v in json.loads(out.read_text(encoding="utf-8"))["pasadas"].items() if k.split("|")[0] == "Lascar" and k.split("|")[1] == "MODIS" and len(v) == 2}
tot = collections.defaultdict(lambda: [0, 0, 0, 0])   # brazo -> pos_n, pos_pub, neg_n, neg_pub
for m, (carp, run, d, h, cong) in L.items():
    J = S/carp/R/run/"_s149_ab_sin_test1_b22"; K = S/carp/R/run/"_s149_ab_sin_test1_b22_max"
    if not B[m].exists(): print(m, "sin B extraido"); continue
    TBJ = tabla(B[m], J, d, h, cong, m + "_BJ"); TJK = tabla(J, K, d, h, cong, m + "_JK")
    fila = {}
    for nom, T, lado in (("B", TBJ, "control"), ("J", TBJ, "brazo"), ("K", TJK, "brazo")):
        pos = [v[lado] for v in T.values() if v["control"]["lab"] == "pos"]; neg = [v[lado] for v in T.values() if v["control"]["lab"] == "neg_limpio"]
        a = tot[nom]; a[0] += len(pos); a[1] += sum(x["pub"] for x in pos); a[2] += len(neg); a[3] += sum(x["pub"] for x in neg)
        fila[nom] = "pos %d/%d neg %d/%d" % (sum(x["pub"] for x in pos), len(pos), sum(x["pub"] for x in neg), len(neg))
    print(m, fila)
print("\nAGREGADO marzo a junio, Lascar MODIS")
for nom, (pn, pp, nn, np_) in tot.items():
    lp = wilson(pp, pn); ln = wilson(np_, nn)
    print("  %s | con alerta publica %d de %d = %.1f %% [%.1f, %.1f] | negativos limpios %d de %d = %.1f %% [%.1f, %.1f] | intervalos %s" % (
        nom, pp, pn, 100 * pp / pn, 100 * lp[0], 100 * lp[1], np_, nn, 100 * np_ / nn, 100 * ln[0], 100 * ln[1], "SEPARADOS" if lp[0] > ln[1] else "SE CRUZAN"))
