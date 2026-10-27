# -*- coding: utf-8 -*-
"""S158: que trae M13 en los pixeles donde M15 viene en 65533 (Bowtie_Deleted). Solo lectura, sin pipeline de deteccion.

POR QUE. El probe de M15 (run 39597022719) encontro, en 125 pasadas, 0 pixeles con M13 valido y M15 NaN segun el
lector: donde M15 trae 65533, M13 tambien es NaN para el lector, aunque su DN no es ninguno de los cuatro sentinelas
(65532 a 65535). Falta saber por que, para no dejarlo como inferencia: si es otro codigo de relleno, la marca 256 en
los flags de M13, o un valor de la LUT que el lector descarta. Toma los tres gránulos de mayor cenit de pasadas.json
(sin elegir a mano) y vuelca, en los pixeles de la escena con M15 = 65533: DN de M13, flags de M13 y BT de la LUT,
mas los atributos del SDS de M13 (valid_min, valid_max, _FillValue, flag_masks).
"""
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
for p in (ROOT, ROOT / "scripts", HERE):
    sys.path.insert(0, str(p))
import numpy as np  # noqa: E402


def _txt(v):
    v = v.tolist() if hasattr(v, "tolist") else v
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, list):
        return [_txt(x) for x in v]
    return v if isinstance(v, (int, float, str, bool)) or v is None else str(v)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    import h5py
    import probe_m15 as pm
    import pipeline.process_viirs_mod as mod
    from pipeline.fetch import auth
    from run_pipeline import load_volcanoes
    pas = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    # los gránulos se toman de pasadas.json: los de mayor cenit con M15 = 65533 en la ventana (ver README)
    elegidos = sorted([p for p in pas if (p.get("z") or 0) >= 45], key=lambda p: -(p["z"] or 0))[:3]
    vols = {v["name"]: v for v in load_volcanoes()}
    auth()
    dest = Path(os.environ.get("VRP_TMP_DIR", str(HERE / "_granulos")))
    out = []
    for p in elegidos:
        print("==", p["vol"], p["dt"], p["granule"], "cenit", p["z"], flush=True)
        l1b, geo, nota = pm.bajar(vols[p["vol"]], p["sensor"], p["granule"], dest)
        with h5py.File(l1b, "r") as f:
            obs = f["observation_data"]
            dn13 = obs["M13"][:].astype(np.int64)
            dn15 = obs["M15"][:].astype(np.int64)
            qf13 = obs["M13_quality_flags"][:].astype(np.int64)
            lut13 = np.asarray(obs["M13_brightness_temperature_lut"][:], dtype=np.float64)
            at13 = {k: _txt(v) for k, v in obs["M13"].attrs.items() if k != "DIMENSION_LIST"}
            atq13 = {k: _txt(v) for k, v in obs["M13_quality_flags"].attrs.items() if k != "DIMENSION_LIST"}
        bt13 = mod.read_viirs_mod_l1b(l1b)["M13"]
        m = dn15 == 65533
        r = {"pasada": p, "nota": nota, "n_m15_65533_escena": int(m.sum()),
             "m13_dn_en_esos": dict(Counter(int(x) for x in dn13[m]).most_common(8)),
             "m13_qf_en_esos": dict(Counter(int(x) for x in qf13[m]).most_common(8)),
             "m13_bt_lector_finita_en_esos": int(np.isfinite(bt13[m]).sum()),
             "m13_lut_en_dn_frecuente": None, "m13_attrs": at13, "m13_qf_attrs": atq13,
             "lut13_len": int(lut13.size), "lut13_ultimos": [float(x) for x in lut13[-8:]],
             "m13_dn_fuera_de_m15_65533": dict(Counter(int(x) for x in dn13[~m] if x >= 65520).most_common(8))}
        if r["m13_dn_en_esos"]:
            d0 = max(r["m13_dn_en_esos"], key=r["m13_dn_en_esos"].get)
            r["m13_lut_en_dn_frecuente"] = float(lut13[min(d0, lut13.size - 1)]) if d0 < lut13.size else "fuera de la LUT"
        print(json.dumps({k: v for k, v in r.items() if k not in ("pasada", "m13_attrs", "m13_qf_attrs")}, ensure_ascii=False))
        print("   attrs M13:", json.dumps(at13, ensure_ascii=False)[:600])
        out.append(r)
        import shutil
        shutil.rmtree(dest, ignore_errors=True)
    Path("out").mkdir(exist_ok=True)
    Path("out/probe_m13_bowtie.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
