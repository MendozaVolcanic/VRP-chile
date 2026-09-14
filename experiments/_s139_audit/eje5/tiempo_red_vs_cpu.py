"""Reparte el tiempo de un job de reproceso entre red (DOWNLOAD elapsed) y el resto (busqueda+proceso).
P1: si la red dominara, la suma de elapsed se acercaria al total del step. P2: si el log no trae marcadores
[diag], n_downloads=0 y se reporta SIN_DATO, no 0 s. Ventana: la del job (ver ventanas_runs.sh)."""
import re, sys, io
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for f in sys.argv[1:]:
    txt = open(f, encoding="utf-8", errors="replace").read().splitlines()
    el = [float(m.group(1)) for l in txt for m in [re.search(r"DOWNLOAD_DONE .*elapsed=([\d.]+)s", l)] if m]
    ts = [l[:28] for l in txt if ">>> " in l]
    if not el or not ts: print(f, "SIN_DATO"); continue
    t0 = datetime.fromisoformat(ts[0][:26]); t1 = datetime.fromisoformat(ts[-1][:26])
    tot = (t1 - t0).total_seconds()
    proc = len([l for l in txt if re.search(r"\| VRP=", l)])
    print(f"{f}: dias={len(ts)} total_s(1er a ultimo dia)={tot:.0f} descargas={len(el)} red_s={sum(el):.0f} ({100*sum(el)/tot:.0f}%) granules_con_VRP_impreso={proc}")
