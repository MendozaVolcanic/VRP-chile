# -*- coding: utf-8 -*-
"""F4-07: razon de magnitud nuestra/MIROVA en pasadas con ALERTA de MIROVA (regla SN), PAREADA: mismas pasadas
en el tag C0 y en main K (18-sep a 17-oct). 'nuestra' = mirovaEqVrpDisplay del node (lo que dibuja el tablero).
Se informan dos medianas: sobre pasadas que AMBOS regimenes publican (mismo conjunto) y sobre las que cada uno
publica (conjunto propio, lo que hace un audit ingenuo). Y la serie no pareada C0 29ago-17sep vs K.
P1: el control positivo es que en el conjunto comun la razon C0/K de MODIS debe moverse (banda 22 cambia la
   radiancia); si nada se moviera en ningun sensor, sospechar del pareo. P2: n de cada celda impreso.
"""
import io, json, sys, collections, statistics
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
from auto_audit_weekly import _coords_por_volcan
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
por_vb, *_ = bp.indexar_referencia(cargar_referencia_unificada(SNAP_CONS, SNAP_OCR), _coords_por_volcan(),
                                    ("2026-08-29", "2026-10-19"), regla_minimas="SN")
def mirova(r):
    dt = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    v = [f["vrp_mw"] for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), dt) if bp.es_alerta(f["tipo"]) and f["vrp_mw"]]
    return max(v) if v else None
L = lambda f: [json.loads(x) for x in open(f, encoding="utf-8")]
Mall = L("main_jul_oct.jsonl"); M = {(r["vol"], r["dt"], r["sensor"]): r for r in Mall}
T = [t for t in L("tag_c0_ventana.jsonl") if t["noche"] <= "2026-10-17"]
med = lambda xs: (round(statistics.median(xs), 3), len(xs)) if xs else (None, 0)
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    comun_c0, comun_k, prop_c0, prop_k = [], [], [], []
    for t in T:
        if t["b"] != b or t.get("lab_SN") != "pos": continue
        m = M.get((t["vol"], t["dt"], t["sensor"]))
        mv = mirova(t)
        if m is None or not mv: continue
        if t["pub"]: prop_c0.append(t["disp"] / mv)
        if m["pub"]: prop_k.append(m["disp"] / mv)
        if t["pub"] and m["pub"]: comun_c0.append(t["disp"] / mv); comun_k.append(m["disp"] / mv)
    print(b, "PAREADO 18sep-17oct | conjunto propio C0", med(prop_c0), "K", med(prop_k),
          "| conjunto comun C0", med(comun_c0), "K", med(comun_k))
    nc0 = [r["disp"] / mirova(r) for r in Mall if r["b"] == b and "2026-08-29" <= r["noche"] <= "2026-09-17"
           and r.get("lab_SN") == "pos" and r["pub"] and mirova(r)]
    nk = [r["disp"] / mirova(r) for r in Mall if r["b"] == b and "2026-09-18" <= r["noche"] <= "2026-10-19"
          and r.get("lab_SN") == "pos" and r["pub"] and mirova(r) and r["reg"] == "K"]
    print(b, "NO PAREADO C0 29ago-17sep", med(nc0), "K 18sep-19oct", med(nk))
