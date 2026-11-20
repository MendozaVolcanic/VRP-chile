# FICHA (SDA, CPLT 372): probe de solo lectura (S192). Lee los atributos y el rango de DN de M13 y M15 en un L1B VJ202MOD
# para saber cómo codifica M13 sus banderas. No es detección; no escribe en data/, no commitea.
"""POR QUÉ. El probe de bow-tie (run 44818788733) vio que los píxeles bow-tie de M13 traen DN 327678, que no cabe en 16
bits: M13 no es uint16 en este producto, y el UserGuide (pág. 23) lo describe como uint16 con banderas 65532-65534.
leer_radiancia_l1b pone en NaN todo DN >= 65528 (FLAG_MIN_DN). Si M13 tiene DN válidos por encima de 65527, ese corte
borraría radiancia válida de M13 (justo la caliente). Este probe mide: tipo, atributos, largo de la LUT de BT, y cuántos
DN de M13 caen en [65528, primer valor de bandera) en el gránulo entero.

Uso: python experiments/_s192_bowtie/medir_m13.py --out out
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AQUI))
import numpy as np  # noqa: E402


def attrs(ds):
    out = {}
    for k, v in ds.attrs.items():
        v = np.asarray(v)
        out[k] = v.tolist() if v.dtype.kind != "S" and v.dtype.kind != "O" else str(v)
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=os.environ.get("VRP_TMP_DIR", str(ROOT / "granulos_tmp")))
    a = ap.parse_args()
    if not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 2
    import h5py
    from pipeline.fetch import auth
    import medir_bowtie as MB
    auth()
    tmp = Path(a.tmp) / "m13"
    tmp.mkdir(parents=True, exist_ok=True)
    rl = MB.bajar("VIIRS_NOAA21_MOD_L1B", "A2026324.0448", -36.863, -71.377, tmp)
    if rl is None:
        print("sin gránulo")
        return 2
    res = {"l1b": rl.name, "bandas": {}}
    with h5py.File(rl, "r") as f:
        obs = f["observation_data"]
        res["variables"] = sorted(obs.keys())
        for b in ("M13", "M15"):
            ds = obs[b]
            dn = ds[:]
            q = obs[f"{b}_quality_flags"][:]
            fv = [int(x) for x in np.ravel(ds.attrs.get("flag_values", []))]
            primer_flag = min(fv) if fv else None
            info = {"dtype": str(ds.dtype), "attrs": attrs(ds), "dn_max": int(dn.max()),
                    "dn_max_sin_bandera_qf": int(dn[(q & (256 | 512 | 1024)) == 0].max()),
                    "valores_unicos_con_bit_bowtie": sorted(set(int(x) for x in np.unique(dn[(q & 256) != 0])))[:10],
                    "valores_unicos_con_bit_missing": sorted(set(int(x) for x in np.unique(dn[(q & 512) != 0])))[:10],
                    "valores_unicos_con_bit_calfail": sorted(set(int(x) for x in np.unique(dn[(q & 1024) != 0])))[:10],
                    "n_dn_ge_65528": int((dn >= 65528).sum()),
                    "n_dn_ge_65528_sin_bandera_qf": int(((dn >= 65528) & ((q & (256 | 512 | 1024)) == 0)).sum()),
                    "n_saturacion_bit4": int(((q & 4) != 0).sum())}
            if primer_flag is not None:
                info["n_dn_entre_65528_y_primer_flag"] = int(((dn >= 65528) & (dn < primer_flag)).sum())
            lut = obs.get(f"{b}_brightness_temperature_lut")
            if lut is not None:
                info["lut_largo"] = int(lut.shape[0])
                info["lut_attrs"] = attrs(lut)
            res["bandas"][b] = info
            print(b, json.dumps({k: v for k, v in info.items() if k != "lut_attrs"}, ensure_ascii=False), flush=True)
    for f in tmp.glob("*"):
        f.unlink()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    json.dump(res, open(Path(a.out) / "m13_atributos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
