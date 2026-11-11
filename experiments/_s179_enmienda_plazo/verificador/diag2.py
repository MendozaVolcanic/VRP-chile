"""Verificador: detalle por encendido simulado. Simulador PROPIO (no importa cierre() del instrumento), con tope
parametrico y composicion por volcan al cerrar. Uso: python diag2.py INICIO FIN [FIN_DATOS]"""
import collections, io, sys, statistics
from datetime import date, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
ini_s, fin_s = sys.argv[1], sys.argv[2]
fin_datos_s = sys.argv[3] if len(sys.argv) > 3 else fin_s
ventana = (ini_s, fin_s)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
recs = bp.cargar_nuestros(coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv)
prot = collections.defaultdict(list)
for r in recs:
    if r["lab"] != "pos": continue
    fp = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
    if fp and max((f["vrp_mw"] or 0) for f in fp) >= 1.0:
        prot[r["b"]].append((r["dt"], r["vol"]))
for s in prot: prot[s].sort()
ini, fin, fin_datos = date.fromisoformat(ini_s), date.fromisoformat(fin_s), date.fromisoformat(fin_datos_s)

def sim(L, d0, tope, objetivo=29, dias=120):
    """Cuenta en orden temporal desde d0 (dia inclusive), hasta d0+dias (exclusive). Devuelve (dia de cierre o None, Counter)."""
    c = collections.Counter(); n = 0
    lim = d0 + timedelta(days=dias)
    for dt, vol in L:
        d = dt.date()
        if d < d0: continue
        if d >= lim or d > fin_datos: break
        if tope is not None and c[vol] >= tope: continue
        c[vol] += 1; n += 1
        if n >= objetivo: return (d - d0).days, c
    return None, c

for s in sorted(prot):
    L = [x for x in prot[s] if x[0].date() <= fin_datos]
    print(f"\n== {s}: {len(L)} protegidas hasta {fin_datos}")
    for tope in (None, 15, 12, 10, 8, 5):
        ks, comp, d = [], [], ini
        n_eval = 0
        det = []
        while (fin_datos - d).days >= 120:
            n_eval += 1
            k, c = sim(L, d, tope)
            if k is not None:
                ks.append(k); comp.append(c); det.append((d, k, c))
            d += timedelta(days=1)
        if not ks:
            print(f"   tope {tope}: de {n_eval} encendidos cierran por cuenta 0"); continue
        mayor = [max(c.values()) for c in comp]            # cuantas aporta el volcan que mas aporta
        nv3 = [sum(1 for v in c.values() if v >= 3) for c in comp]
        print(f"   tope {tope}: de {n_eval} encendidos cierran por cuenta {len(ks)}; dias mediana {statistics.median(ks)}, min {min(ks)}, max {max(ks)}; "
              f"aporte del volcan mayor: mediana {statistics.median(mayor)}, max {max(mayor)}; "
              f"cierres con un volcan >= 20 de 29: {sum(1 for m in mayor if m >= 20)}; con >= 26: {sum(1 for m in mayor if m >= 26)}")
        if tope in (None, 10):
            # tramos: encendidos que cierran, agrupados por rango de fecha
            print("      primer y ultimo encendido que cierra:", det[0][0], "->", det[-1][0])
            for dd, k, c in (det[0], det[len(det)//2], det[-1]):
                print(f"      encendido {dd}: cierra a los {k} dias ({dd + timedelta(days=k)}), composicion {dict(c.most_common())}")
            # distribucion de dias a cierre
            h = collections.Counter(("<=30" if k <= 30 else "31-60" if k <= 60 else "61-90" if k <= 90 else "91-119") for k in ks)
            print("      dias a cierre:", dict(h))
