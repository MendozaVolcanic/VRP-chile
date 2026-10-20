# -*- coding: utf-8 -*-
"""C-SIN del probe de saturación: el contador sobre arreglos sintéticos, sin red. ESCRITO ANTES DE CORRER EL PROBE.

POR QUÉ (A110, A116). Un cero del probe sólo vale si el contador PUEDE dar distinto de cero. Acá se arma una escena
de 9 x 9 con bits y topes puestos a mano y se exige que el contador los encuentre todos y sólo esos, que la cota de
energía de un píxel perdido sea k·A·(L - L_anillo), y que una escena sin nada dé ceros en todo.
Uso: python experiments/_s157_saturacion/prueba_saturacion.py   (sale 1 si algo falla)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import probe_saturacion as ps  # noqa: E402


def escena(con_saturacion):
    sh = (9, 9)
    lut_max = 367.0
    bt_mir = np.full(sh, 270.0)
    bt_tir = np.full(sh, 265.0)
    qf_mir = np.zeros(sh, dtype=np.int64)
    qf_tir = np.zeros(sh, dtype=np.int64)
    if con_saturacion:
        bt_mir[4, 4] = lut_max          # MIR saturada: tope de la LUT y bit 4
        qf_mir[4, 4] = 4
        qf_tir[4, 5] = 4                # sólo la TIR saturada: MIR sana a 330 K
        bt_mir[4, 5] = 330.0
        qf_mir[3, 3] = 2                # Out_of_Range, no se pierde
        qf_mir[0, 0] = 4                # fuera de la ventana
    raw = {"I04": {"dn": np.zeros(sh, dtype=np.int64), "qf": qf_mir, "bt": bt_mir, "lut_max": lut_max,
                   "qf_attrs": {}, "valid_max": None},
           "I05": {"dn": np.zeros(sh, dtype=np.int64), "qf": qf_tir, "bt": bt_tir, "lut_max": 380.0,
                   "qf_attrs": {}, "valid_max": None}}
    pipe = {"I04": np.where((qf_mir & 4) != 0, np.nan, bt_mir), "I05": np.where((qf_tir & 4) != 0, np.nan, bt_tir)}
    yy, xx = np.mgrid[0:9, 0:9]
    dist = np.hypot(yy - 4, xx - 4) * 0.375
    return raw, pipe, dist


def main():
    fallas = []
    k_area, t_bg, lam = 2531250.0, 270.0, 3.74
    for con in (True, False):
        raw, pipe, dist = escena(con)
        c0 = [(4, 3)]
        ven, _, cum, vec = ps.mascaras(dist.shape, dist, 1.0, c0)
        cont, perdido = ps.contar_viirs(raw, pipe, "I04", "I05", ven, cum, vec)
        filas = ps.cota_viirs(raw, "I04", perdido, ven, t_bg, lam, k_area, dist)
        got = (cont["I04"]["ventana"]["bit4_sat"], cont["I05"]["ventana"]["bit4_sat"], cont["I04"]["ventana"]["bit2_oor"],
               cont["I04"]["ventana"]["tope_lut"], int((perdido & ven).sum()), cont["I04"]["vecinos_cumulo"]["bit4_sat"])
        esperado = (1, 1, 1, 1, 2, 1) if con else (0, 0, 0, 0, 0, 0)
        print("con_saturacion=%s conteos %s esperado %s" % (con, got, esperado))
        if got != esperado:
            fallas.append("conteos %s" % con)
        L = lambda t: float(ps.planck(np.array([t]), lam)[0])  # noqa: E731
        cota_esp = ((L(367.0) - L(t_bg)) + (L(330.0) - L(t_bg))) * k_area / 1e6 if con else 0.0
        cota = sum(f["mw"] for f in filas)
        print("   cota %.4f MW esperada %.4f" % (cota, cota_esp))
        if abs(cota - cota_esp) > 1e-9:
            fallas.append("cota %s" % con)
    # Verificador S157: C-SIN tampoco probaba la lectura cruda ni el contador de MODIS.
    # crudo_viirs sobre un HDF5 sintético con la forma del L1B (observation_data/<banda>, _quality_flags, _lut).
    import tempfile
    import h5py
    with tempfile.TemporaryDirectory() as td:
        fn = Path(td) / "sintetico.nc"
        lut = np.linspace(200.0, 367.0, 65528).astype(np.float32)
        lut = np.concatenate([lut, np.full(8, -999.9, dtype=np.float32)])
        dn = np.full((3, 3), 1000, dtype=np.uint16)
        dn[1, 1] = 65527                     # tope de la LUT
        dn[0, 0] = 65533                     # sentinela
        qf = np.zeros((3, 3), dtype=np.uint16)
        qf[1, 1] = 4
        qf[0, 0] = 256
        with h5py.File(fn, "w") as f:
            g = f.create_group("observation_data")
            g["I04"] = dn
            g["I04_quality_flags"] = qf
            g["I04_quality_flags"].attrs["flag_masks"] = np.array([1, 2, 4, 256], dtype=np.uint16)
            g["I04_quality_flags"].attrs["flag_meanings"] = np.array(
                [b"Substitute_Cal", b"Out_of_Range", b"Saturation", b"Bowtie_Deleted"])
            g["I04_brightness_temperature_lut"] = lut
        raw = ps.crudo_viirs(fn, ("I04",))
    r = raw["I04"]
    got = (bool(np.isnan(r["bt"][0, 0])), round(float(r["bt"][1, 1]), 2), round(r["lut_max"], 2),
           r["qf_attrs"]["flag_meanings"][2], int(r["qf"][1, 1]))
    esp = (True, 367.0, 367.0, "Saturation", 4)
    print("crudo_viirs %s esperado %s" % (got, esp))
    if got != esp:
        fallas.append("crudo_viirs")
    raw["I05"] = dict(r)
    pipe = {"I04": np.where(r["qf"] == 4, np.nan, r["bt"]), "I05": r["bt"].copy()}
    nada = np.zeros((3, 3), dtype=bool)
    cont, _ = ps.contar_viirs(raw, pipe, "I04", "I05", np.ones((3, 3), dtype=bool), nada, nada)
    v = cont["I04"]["ventana"]
    got = (v["bit4_sat"], v["mask256_bowtie"], v["sentinela"], v["sentinela_codigos"], v["perdidos_pipeline"])
    esp = (1, 1, 1, {"65533": 1}, 1)
    print("contar_viirs (máscaras 4 y 256, sentinela) %s esperado %s" % (got, esp))
    if got != esp:
        fallas.append("contar_viirs máscaras")
    # contar_modis: B22 saturada (65533) con B21 sana no es pérdida; B31 inválida sí.
    sh = (3, 3)

    def banda(si):
        return {"si": si, "rad": np.where(si > 32767, np.nan, si * 0.001), "rad_tope": 32.767, "lam": 3.9}
    si22 = np.full(sh, 1000)
    si22[1, 1] = 65533
    si31 = np.full(sh, 1000)
    si31[0, 2] = 65533
    rawm = {"B21": banda(np.full(sh, 1000)), "B22": banda(si22), "B31": banda(si31)}
    cm, perdm = ps.contar_modis(rawm, np.ones(sh, dtype=bool), np.zeros(sh, dtype=bool), np.zeros(sh, dtype=bool))
    got = (cm["B22"]["ventana"]["si_65533_sat"], cm["B31"]["ventana"]["si_invalido"], int(perdm.sum()), bool(perdm[0, 2]))
    esp = (1, 1, 1, True)
    print("contar_modis %s esperado %s" % (got, esp))
    if got != esp:
        fallas.append("contar_modis")
    print("FALLAS: %s" % fallas if fallas else "C-SIN OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
