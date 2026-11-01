# -*- coding: utf-8 -*-
"""S158: arma `pasadas.json` para el probe L1B de M15 en sentinela, sin elegir a mano y sin red.

Grupo P: TODAS las alertas de VIIRS 750 que K no publica y que tienen record (75, de `perdidas_v750.json`).
Grupo C (control, A110): por cada pasada P, la positiva PUBLICADA del mismo volcan y el mismo satelite mas cercana en
el tiempo, sin repetir; si no queda ninguna del mismo satelite, la del mismo volcan mas cercana. Sirve para medir la
tasa base: si los sentinelas de M15 junto al crater son igual de frecuentes donde SI publicamos, no explican la
perdida.

Uso: python experiments/_s158_v750/seleccionar_pasadas.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def main():
    d = json.loads((HERE / "perdidas_v750.json").read_text(encoding="utf-8"))
    campos = ("vol", "dt", "sensor", "granule", "z", "mecanismo", "pc_vrp", "pc_dist", "n_anomalous_pixels",
              "dc", "t_bg_k", "t_max_k", "mirova_vrp_mw", "mirova_dist_km", "inner")
    P = [dict({k: e.get(k) for k in campos}, grupo="P") for e in d["perdidas"]]
    libres = list(d["publicadas"])
    C = []
    for p in P:
        cands = [e for e in libres if e["vol"] == p["vol"] and e["sensor"] == p["sensor"]] or \
                [e for e in libres if e["vol"] == p["vol"]]
        if not cands:
            continue
        e = min(cands, key=lambda x: abs((_t(x["dt"]) - _t(p["dt"])).total_seconds()))
        libres.remove(e)
        c = {k: e.get(k) for k in campos}
        c.update(grupo="C", mecanismo="publica", par_de=p["granule"])
        C.append(c)
    out = P + C
    assert all(x["granule"] for x in out), "pasada sin nombre de granulo"
    assert len({(x["vol"], x["granule"]) for x in out}) == len(out), "pasada repetida"
    (HERE / "pasadas.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"P {len(P)} | C {len(C)} | total {len(out)} | granulos distintos {len({x['granule'] for x in out})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
