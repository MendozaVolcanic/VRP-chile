# -*- coding: utf-8 -*-
"""S175: ¿qué le pasó a la descomposición de magnitud de S139 tras el reproceso con K (#883)?

POR QUÉ. `tests/test_descomponer_magnitud_s139.py` congela los números de S139 (n 1.499, R_gm 0,659,
F_n 0,553; 0,995 a igual conteo) y falla en local con n 1.579. Su mensaje dice «re-medir». Que el n
cambie no dice si cambió sólo el denominador o también lo que se mide por pasada, y de eso depende si
basta actualizar un número. Esta pregunta se contesta pasada contra pasada.

CÓMO. Corre el instrumento real (`scripts/descomponer_magnitud_osf.py`, sin tocarlo) sobre dos juegos
de records: los del árbol actual y los del padre del merge de #883, exportados con `git show` a una
carpeta temporal. Separa pares comunes, pares que entraron y pares que salieron.

CONTROL. Si los records del padre de #883 no reprodujeran 1.499 / 0,659 / 0,553 / 0,995, la causa no
sería #883 y este script no contestaría la pregunta. La primera línea de la salida lo muestra.

USO: python comparar_magnitud_post_883.py --osf <VRP_GLOBAL_ARCHIVE_2025.csv> --temporal <carpeta>
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PADRE_883 = "600968644279126de74ac59af33f8a98a17373ed"  # primer padre del merge 8471add46 (#883)
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten", "Copahue", "PlanchonPeteroa",
        "PuyehueCordonCaulle", "NevadosDeChillan", "Tupungatito"]


def cargar_instrumento():
    spec = importlib.util.spec_from_file_location("dmo", ROOT / "scripts" / "descomponer_magnitud_osf.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def exportar_padre(temporal):
    destino = Path(temporal) / ("records_" + PADRE_883[:9])
    (destino / "data" / "mirova_equivalent").mkdir(parents=True, exist_ok=True)
    for v in VOLS:
        f = destino / "data" / "mirova_equivalent" / f"{v}.json"
        if not f.exists():
            with open(f, "wb") as fh:
                subprocess.run(["git", "-C", str(ROOT), "show", f"{PADRE_883}:data/mirova_equivalent/{v}.json"],
                               stdout=fh, check=True)
    return destino


def medir(raiz, osf):
    """Los pares V375 con las mismas definiciones de main() del instrumento."""
    m = cargar_instrumento()
    m.R = Path(raiz)
    m.cargar(osf)
    d = m.build(0)
    d["R"] = d.pub_mw / d.osf_mw
    d["F_n"] = d.pub_n / d.Npix
    d["ex_ours"] = d.pub_mw * 1e6 / (d.res.map(m.KA) * d.pub_n)
    d["F_ex"] = d.ex_ours / d.ex1
    d["F_hot"] = (d.hot1_ours - d.bk1) / d.ex1
    d["F_bg"] = d.F_ex / d.F_hot
    d = d[d.res == 375].copy()
    d["k"] = list(zip(d.vol, d.t_osf))
    return d


def gm(x):
    x = x[(x > 0) & np.isfinite(x)]
    return float(np.exp(np.log(x).mean())) if len(x) else float("nan")


def fila(g):
    return dict(n=len(g), R=round(gm(g.R), 3), Fn=round(gm(g.F_n), 3), Fex=round(gm(g.F_ex), 3),
                Fhot=round(gm(g.F_hot), 3), Fbg=round(gm(g.F_bg), 3))


def igual_conteo(g):
    s = g[g.Lbg_imp.notna() & (g.R > 0) & (g.F_hot > 0)]
    return s[s.pub_n == s.Npix]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--osf", required=True)
    ap.add_argument("--temporal", required=True)
    a = ap.parse_args()

    viejo = medir(exportar_padre(a.temporal), a.osf)
    hoy = medir(ROOT, a.osf)
    print("control, padre de #883:   total", fila(viejo), "| igual conteo", fila(igual_conteo(viejo)))
    print("hoy (records con K):      total", fila(hoy), "| igual conteo", fila(igual_conteo(hoy)))

    kv, kh = set(viejo.k), set(hoy.k)
    com = kv & kh
    print("pares: antes", len(kv), "| hoy", len(kh), "| comunes", len(com), "| salieron", len(kv - kh),
          "| entraron", len(kh - kv))
    vc = viejo[viejo.k.isin(com)].set_index("k")
    hc = hoy[hoy.k.isin(com)].set_index("k").loc[vc.index]
    print("comunes, antes:", fila(vc))
    print("comunes, hoy:  ", fila(hc))
    print("salieron:      ", fila(viejo[viejo.k.isin(kv - kh)]))
    print("entraron:      ", fila(hoy[hoy.k.isin(kh - kv)]))
    iguales = np.isclose(vc.pub_mw.values, hc.pub_mw.values, atol=1e-6) & (vc.pub_n.values == hc.pub_n.values)
    print("comunes con pub_mw y pub_n identicos:", int(iguales.sum()), "de", len(vc))
    print("comunes con pub_n distinto:", int((vc.pub_n.values != hc.pub_n.values).sum()),
          "| sube", int((hc.pub_n.values > vc.pub_n.values).sum()),
          "| baja", int((hc.pub_n.values < vc.pub_n.values).sum()))
    for nombre, d in (("antes", viejo), ("hoy", hoy)):
        print("igual conteo por volcan,", nombre)
        for v, g in igual_conteo(d).groupby("vol"):
            print("  ", v, fila(g))


if __name__ == "__main__":
    main()
