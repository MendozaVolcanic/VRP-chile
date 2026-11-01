# -*- coding: utf-8 -*-
"""Verificador B1, otro camino que el del auditor.

El auditor compara el port rearmado desde el npz contra `port.fisica` del lote (B22 primaria) y usa como control
negativo que la B21 primaria da distinto. Aqui:
  (1) la B21 primaria rearmada se compara contra `port.fisica_b21` que el lote TAMBIEN guardo: si la igualdad del
      auditor fuera un artefacto del comparador (p. ej. que `igual` devuelva True por construccion), este segundo
      pareo lo veria;
  (2) la geometria de 5 km (`lat_5km`, `lon_5km`) rearmada se compara contra `port.fisica_geo5km` del lote: control
      de que una geometria DISTINTA produce una grilla distinta y de que el pareo sigue siendo exacto con otra
      geolocalizacion (si fuera igual a fisica, el rearme no estaria usando la lat/lon que cree usar);
  (3) control positivo del comparador: se muta UNA celda del resultado y `igual` tiene que dar False; se corre UNA
      fila de lat/lon un pixel y la grilla tiene que cambiar.
Pregunta 1: si la reproduccion estuviera rota (otra banda, otro recorte), (1) y (2) darian distinto. Pregunta 2: si
el comparador estuviera muerto, (3) daria True donde tiene que dar False.
Denominador: 403 pasadas evaluables del lote 40120713181 (ventana 2026-03-01 a 2026-10-21, 11 volcanes Tier A).
Uso: python -I v01_reproduccion_otro_camino.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # comun.py del auditor
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent


def igual(a, b):
    """Misma comparacion que 01_reproducir.py del auditor (copiada para no depender de su modulo)."""
    if a["npix"] != b["npix"]:
        return False
    if (a["vrp_mw"] is None) != (b["vrp_mw"] is None):
        return False
    if a["vrp_mw"] is not None and abs(a["vrp_mw"] - b["vrp_mw"]) > 1e-9:
        return False
    return sorted(tuple(p[:2]) for p in a["pixeles"]) == sorted(tuple(p[:2]) for p in b["pixeles"])


def correr(n, o, r, b22_primary=True, geo="mxd03"):
    g = o["grilla"]
    crop = CM.crop_desde_nativo(n)
    crop["mir"] = CM.merge_mir_bands(n["b21"], n["b22"], b22_primary)
    if geo == "5km":
        crop["lat"] = n["lat_5km"].astype(np.float64)
        crop["lon"] = n["lon_5km"].astype(np.float64)
    mir, tir = CM.PP.grillar(crop, g, g["epsg"])
    p = CM.MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], CM.MP.SENSORES["MODIS"],
                     modo="fisica", semillas=0)
    return p, mir


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    pr(f"evaluables: {len(ids)} de {len(obj)} objetivos MODIS")
    hs = sorted(obj[i]["hora_utc"] for i in ids)
    pr(f"ventana de los datos: {hs[0]} a {hs[-1]} UTC")
    claves = set()
    for i in ids:
        claves |= set(res[i]["port"].keys())
    pr("variantes guardadas por el lote:", sorted(claves))

    ig_b21, dist_b21, con_det_b21, ig_5km, dist_5km, geo_cambia, con_det_5km = 0, [], 0, 0, [], 0, 0
    b21_vs_b22_distinto = 0
    for i in ids:
        n = CM.cargar_nativo(i)
        o, r = obj[i], res[i]
        p21, _ = correr(n, o, r, b22_primary=False)
        ref21 = r["port"].get("fisica_b21")
        if ref21 is None:
            dist_b21.append((i, "sin fisica_b21 en el lote"))
        elif igual(p21, ref21):
            ig_b21 += 1
        else:
            dist_b21.append((i, p21["npix"], p21["vrp_mw"], ref21["npix"], ref21["vrp_mw"]))
        if ref21 and ref21["npix"]:
            con_det_b21 += 1
        b21_vs_b22_distinto += not igual(p21, r["port"]["fisica"])
        p5, mir5 = correr(n, o, r, geo="5km")
        ref5 = r["port"].get("fisica_geo5km")
        if ref5 is None:
            dist_5km.append((i, "sin fisica_geo5km en el lote"))
        elif igual(p5, ref5):
            ig_5km += 1
        else:
            dist_5km.append((i, p5["npix"], p5["vrp_mw"], ref5["npix"], ref5["vrp_mw"]))
        if ref5 and ref5["npix"]:
            con_det_5km += 1
        _p, mir0 = correr(n, o, r)
        geo_cambia += not np.array_equal(mir0, mir5, equal_nan=True)
    pr(f"(1) B21 primaria rearmada = port.fisica_b21 del lote: {ig_b21} de {len(ids)}; pasadas con deteccion en "
       f"fisica_b21: {con_det_b21}; distintos: {dist_b21[:10]}")
    pr(f"    B21 rearmada distinta de fisica (B22) del lote en {b21_vs_b22_distinto} de {len(ids)} pasadas (en las "
       f"390 sin deteccion un 'igual' vacio no distingue nada: el control del auditor solo informa sobre 13)")
    pr(f"(2) geo 5 km rearmada = port.fisica_geo5km del lote: {ig_5km} de {len(ids)}; con deteccion: {con_det_5km}; "
       f"distintos: {dist_5km[:10]}")
    pr(f"    la grilla MIR con geo 5 km difiere de la grilla con MxD03 en {geo_cambia} de {len(ids)} pasadas "
       f"(control: una geolocalizacion distinta tiene que mover la grilla)")

    # (3) control positivo del comparador y del rearme
    i = 141   # Chillan protegida, 8 celdas
    n = CM.cargar_nativo(i)
    p, mir = correr(n, obj[i], res[i])
    ref = res[i]["port"]["fisica"]
    pr(f"(3) comparador: igual(port, lote) en {i} = {igual(p, ref)}")
    import copy
    pm = copy.deepcopy(p)
    pm["pixeles"][0][1] += 1
    pr(f"    una celda corrida una columna -> igual = {igual(pm, ref)} (tiene que ser False)")
    pm = copy.deepcopy(p)
    pm["vrp_mw"] += 2e-9
    pr(f"    VRP + 2e-9 MW -> igual = {igual(pm, ref)} (tiene que ser False)")
    n2 = {k: v.copy() for k, v in n.items()}
    n2["lat_mxd03"] = np.roll(n2["lat_mxd03"], 1, axis=0)
    n2["lon_mxd03"] = np.roll(n2["lon_mxd03"], 1, axis=0)
    p2, mir2 = correr(n2, obj[i], res[i])
    pr(f"    lat/lon corridas una fila -> grilla MIR distinta: {not np.array_equal(mir, mir2, equal_nan=True)}; "
       f"igual(port, lote) = {igual(p2, ref)} (tiene que ser False); npix {p['npix']} -> {p2['npix']}")
    (AQUI / "v01_reproduccion_otro_camino_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
