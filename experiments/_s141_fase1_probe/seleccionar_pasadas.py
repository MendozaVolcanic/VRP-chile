# -*- coding: utf-8 -*-
"""S141, Fase 1: muestra de pasadas VIIRS 375 m para el probe del vecino del foco.

POR QUÉ. Sumamos 1 píxel donde MIROVA suma 3 o más (S139, F_n 0,553). Se eligen pasadas OSF
pareadas con nuestro record donde pasa eso (candidatos) y, como control del instrumento, pasadas
donde publicamos tantos píxeles como MIROVA (controles). El OSF está supervisado a mano: se usa
pasada contra pasada, nunca para conteos.

INSTRUMENTO. P1: los controles deben salir con los vecinos incluidos; P2: la muestra es
determinista (mismo resultado dos veces) y se reparte parejo en el tiempo dentro de cada volcán.

USO: python experiments/_s141_fase1_probe/seleccionar_pasadas.py [--por-volcan 4] [--controles 2]
Salida: experiments/_s141_fase1_probe/pasadas.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R / "scripts"))

from build_c2ab_windows import FOCAL  # noqa: E402

OUT = Path(__file__).resolve().parent / "pasadas.json"


def _espaciados(g, k):
    g = g.sort_values("t_osf")
    if len(g) <= k:
        return g
    idx = sorted(set(np.linspace(0, len(g) - 1, k).round().astype(int)))
    return g.iloc[idx]


def _num(v):
    return None if v is None or v != v else float(v)


def _fila(x, clase):
    return {
        "volcan": x.vol, "pasada_utc": x.t_ours.strftime("%Y-%m-%d %H:%M"), "sensor": x.sensor,
        "clase": clase, "regimen": "focal" if x.vol in FOCAL else "nevado",
        "osf": {"Npix": int(x.Npix), "vrp_mw": float(x.osf_mw), "satzen": float(x.satzen),
                "t_osf": x.t_osf.strftime("%Y-%m-%d %H:%M"),
                "lat": _num(getattr(x, "lat", None)), "lon": _num(getattr(x, "lon", None))},
        "persistido": {"pub_n": int(x.pub_n), "pub_mw": float(x.pub_mw), "pc_n": int(x.pc_n),
                       "t_bg_k": _num(x.t_bg)},
    }


def seleccionar(d, por_volcan=4, controles_por_volcan=2):
    v = d[d.res == 375]
    cand = v[(v.Npix >= 3) & (v.pub_n == 1)]
    ctl = v[(v.Npix >= 3) & (v.pub_n >= v.Npix)]
    filas = []
    for clase, base, k in (("candidato", cand, por_volcan), ("control", ctl, controles_por_volcan)):
        for vol in sorted(base.vol.unique()):
            for x in _espaciados(base[base.vol == vol], k).itertuples():
                filas.append(_fila(x, clase))
    return filas


def main(argv=None):
    ap = argparse.ArgumentParser(description="Muestra de pasadas para el probe del vecino (S141)")
    ap.add_argument("--por-volcan", type=int, default=4)
    ap.add_argument("--controles", type=int, default=2)
    a = ap.parse_args(argv)
    import descomponer_magnitud_osf as m
    m.cargar(str(m.OSF_DEFECTO))
    d = m.build(0)
    osf = m.o[["t", "vol", "res", "LAT", "LON"]].rename(columns={"t": "t_osf", "LAT": "lat", "LON": "lon"})
    d = d.merge(osf, on=["t_osf", "vol", "res"], how="left").drop_duplicates(subset=["t_osf", "vol", "res"])
    filas = seleccionar(d, a.por_volcan, a.controles)
    OUT.write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(filas)} pasadas -> {OUT}")


if __name__ == "__main__":
    main()
