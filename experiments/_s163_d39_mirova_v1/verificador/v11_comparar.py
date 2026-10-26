"""v11_comparar.py (A3 y A4, instrumento propio a nivel de TEXTO): compara los CSV originales de main con los que
dejan los ciclos A (main) y B (PR + s163) de v10. Mira bytes: BOM, terminador de linea, cabecera; y por llave cruda
(timestamp, Volcan, Sensor) la LINEA entera, no campos parseados, para que un cambio de formato (24 -> 24.0,
comillas, orden de columnas) no se esconda. Tambien positivos y maestro."""
import csv, io, os, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
V = os.path.dirname(os.path.abspath(__file__)); S = r"D:\vrp-trabajo\s163-d39"
def leer(p):
    b = open(p, "rb").read()
    info = {"bom": b.startswith(b"\xef\xbb\xbf"), "crlf": b.count(b"\r\n"), "lf": b.count(b"\n"), "bytes": len(b)}
    t = b.decode("utf-8-sig")
    lineas = t.split("\n"); cab = lineas[0]
    cols = next(csv.reader([cab]))
    filas = list(csv.reader(io.StringIO(t)))[1:]
    ik = [cols.index("timestamp"), cols.index("Volcan"), cols.index("Sensor")]
    porllave = {}; rep = 0
    for f, ln in zip(filas, [l for l in lineas[1:] if l != ""]):
        k = tuple(f[i].strip() for i in ik)
        rep += k in porllave; porllave[k] = (f, ln)
    return info, cols, porllave, rep
def comparar(nom, pO, pA, pB, rep_keys=None):
    iO, cO, O, rO = leer(pO); iA, cA, A, rA = leer(pA); iB, cB, B, rB = leer(pB)
    print(f"\n#### {nom}")
    print("  bytes/BOM/CRLF/LF:", "O", iO, "| A", iA, "| B", iB)
    print("  cabecera O==A:", cO == cA, "O==B:", cO == cB, "| columnas nuevas en B:", [c for c in cB if c not in cO], "| orden de las viejas igual:", [c for c in cB if c in cO] == cO)
    print("  filas O/A/B:", len(O), len(A), len(B), "repetidas:", rO, rA, rB)
    for et, X, Y, cX, cY in (("O->A", O, A, cO, cA), ("O->B", O, B, cO, cB), ("A->B", A, B, cA, cB)):
        perd = set(X) - set(Y); nue = set(Y) - set(X)
        camb = collections.Counter(); ej = {}
        for k in set(X) & set(Y):
            if X[k][1] != Y[k][1]:
                dx = dict(zip(cX, X[k][0])); dy = dict(zip(cY, Y[k][0]))
                d = tuple(c for c in cY if dx.get(c, "") != dy.get(c, ""))
                camb[d] += 1; ej.setdefault(d, (k, [(c, dx.get(c, "")[:60], dy.get(c, "")[:60]) for c in d][:3]))
        print(f"  {et}: llaves perdidas {len(perd)} | nuevas {len(nue)} | lineas comunes distintas {sum(camb.values())}")
        for d, n in camb.most_common(6):
            print(f"      {n} {d} ej {ej[d]}")
        if et == "A->B" and rep_keys is not None and nue:
            print("      nuevas que estan en el archivo de reposicion:", sum(k in rep_keys for k in nue), "de", len(nue))
            malas = [k for k in nue if k in rep_keys and B[k][1] != rep_keys[k]]
            print("      nuevas cuya LINEA difiere de la del archivo de reposicion:", len(malas), (malas[:2] and [(k, B[k][1][:120], rep_keys[k][:120]) for k in malas[:2]]))
rep = {}
_, cR, R, _ = leer(os.path.join(V, "ciclo_B", "monitoreo_satelital", "filas_perdidas_por_mezcla_2026.csv"))
rep = {k: v[1] for k, v in R.items()}
comparar("registro_vrp_consolidado.csv", os.path.join(S, "scripts", "cons_main_original.csv"),
         os.path.join(V, "ciclo_A", "monitoreo_satelital", "registro_vrp_consolidado.csv"),
         os.path.join(V, "ciclo_B", "monitoreo_satelital", "registro_vrp_consolidado.csv"), rep)
# positivos: el original no esta guardado aparte; se compara A contra B
pA = os.path.join(V, "ciclo_A", "monitoreo_satelital", "registro_vrp_positivos.csv"); pB = os.path.join(V, "ciclo_B", "monitoreo_satelital", "registro_vrp_positivos.csv")
if os.path.exists(pA) and os.path.exists(pB):
    comparar("registro_vrp_positivos.csv (O = A)", pA, pA, pB, rep)
comparar("registro_vrp_ocr.csv", os.path.join(S, "scripts", "ocr_main_original.csv"),
         os.path.join(V, "ciclo_A", "monitoreo_satelital", "registro_vrp_ocr.csv"),
         os.path.join(V, "ciclo_B", "monitoreo_satelital", "registro_vrp_ocr.csv"))
mA = os.path.join(V, "ciclo_A", "monitoreo_satelital", "registro_vrp_maestro_publicable.csv"); mB = os.path.join(V, "ciclo_B", "monitoreo_satelital", "registro_vrp_maestro_publicable.csv")
if os.path.exists(mA) and os.path.exists(mB):
    comparar("registro_vrp_maestro_publicable.csv (O = A)", mA, mA, mB, rep)
