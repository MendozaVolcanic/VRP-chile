# -*- coding: utf-8 -*-
"""S162 V375-E: la curva de magnitud con el cenit, nuestra contra la de MIROVA (no contra 1).

POR QUÉ. Visto de lado, el píxel de VIIRS se estira y el foco caliente queda diluido en un área mayor; MIROVA también
pierde magnitud en las pasadas oblicuas. El verificador del paquete oblicuo de VIIRS 750 (rama s159-pruebas,
experiments/_s159/oblicuo_paquete/verificador/INFORME.md VO-1) lo midió dentro de la misma noche y el mismo volcán: la
pasada más oblicua sobre la menos oblicua (diferencia de cenit de 15° o más) da 0,503 en MIROVA, 0,517 en el oráculo y
0,239 en K; el nulo (los mismos pares ordenados por hora) da 1,054. Para la réplica la meta no es aplanar esa curva sino
reproducir la de MIROVA (programa §1.6). Esta función mide, por noche, la RAZÓN DOBLE

    D = (nuestro VRP oblicuo / nuestro VRP menos oblicuo) / (VRP de MIROVA oblicuo / VRP de MIROVA menos oblicuo)

que vale 1 si nuestra caída con el cenit es la misma que la de MIROVA, y menos de 1 si caemos más.

Las dos preguntas del instrumento. (1) Si la medición no viera el cenit, un nulo sin diferencia de cenit daría lo mismo
que la lectura. El nulo de VIIRS 750 (los mismos pares ordenados por hora) NO sirve en 375: medido sobre la población
de S159 (linea_base_curva_salida.txt), el VRP de MIROVA baja de una pasada a la siguiente de la misma noche (mediana
0,818, n 365), así que el orden por hora también cae (0,786) aunque la pasada oblicua sea la más tardía sólo en 110 de
229 noches. El nulo de aquí son los PARES DE CENIT PARECIDO:
en la misma noche y volcán, dos pasadas con alerta de MIROVA que difieren en menos de 5° de cenit, ordenadas con la MISMA
regla que la lectura (la de menor cenit primero). Mide si el método, con su selección (las dos con alerta, las dos
publicadas), da una razón doble distinta de 1 cuando casi no hay diferencia de cenit: si la da, NULO SESGADO. En un
borrador el orden del nulo se sorteaba; el verificador (verificador/INFORME.md) mostró que así d y 1/d son
equiprobables y el nulo no puede fallar (con un sesgo de plataforma de x0,3 lo marcaba en 6 % de las corridas, el
nivel del azar). Un sesgo de PLATAFORMA (nuestra razón contra MIROVA distinta en Suomi NPP, NOAA-20 y NOAA-21) no lo ve
ningún nulo de pares: se mide aparte con sesgo_plataforma() y con la razón doble separada en pares de la misma
plataforma y de plataformas distintas. Si el IC de MIROVA por cenit contiene la mediana de MIROVA en el nulo, la curva
de MIROVA no se separa de «plana» y se marca (no bloquea). (2) Una noche sin dos pasadas con alerta de MIROVA y
publicación nuestra no entra; la versión «no condicionada» cuenta como 0 la pasada que no publicamos (no publicar una
alerta oblicua es la caída más grande posible) y se informa al lado.
"""
from __future__ import annotations

import collections
import math

import numpy as np

DZ_MIN = 15.0
DZ_NULO = 5.0
SEMILLA = 162


def pares_por_noche(pasadas, campo_vrp, campo_pub, dz_min=DZ_MIN, condicionar=True):
    """`pasadas`: dicts con vol, hora (AAAA-MM-DD HH:MM), z (cenit del sensor), mir (VRP de MIROVA > 0 si alertó), y los
    campos de nuestro VRP y de si publicamos. Por noche-volcán: la pasada de menor cenit y la de mayor, si difieren en
    dz_min o más y MIROVA alertó en las dos. Devuelve una lista de pares con las razones."""
    por = collections.defaultdict(list)
    for p in pasadas:
        if p.get("z") is None or not (p.get("mir") or 0) > 0:
            continue
        if condicionar and not p.get(campo_pub):
            continue
        por[(p["vol"], p["hora"][:10])].append(p)
    out = []
    for (vol, noche), lst in sorted(por.items()):
        if len(lst) < 2:
            continue
        lst = sorted(lst, key=lambda p: (p["z"], p["hora"]))
        a, b = lst[0], lst[-1]                      # menos oblicua, más oblicua
        if b["z"] - a["z"] < dz_min:
            continue
        va = (a.get(campo_vrp) or 0.0) if a.get(campo_pub) else 0.0
        vb = (b.get(campo_vrp) or 0.0) if b.get(campo_pub) else 0.0
        if va <= 0:
            continue
        t = sorted([a, b], key=lambda p: p["hora"])  # para el nulo: el mismo par, ordenado por hora
        vt = [((p.get(campo_vrp) or 0.0) if p.get(campo_pub) else 0.0) for p in t]
        out.append({"vol": vol, "noche": noche, "z": [a["z"], b["z"]], "mir": [a["mir"], b["mir"]], "x": [va, vb],
                    "plat": [a.get("plat"), b.get("plat")],
                    "r_mir": b["mir"] / a["mir"], "r_x": vb / va, "d": (vb / va) / (b["mir"] / a["mir"]),
                    "r_mir_hora": t[1]["mir"] / t[0]["mir"],
                    "r_x_hora": (vt[1] / vt[0]) if vt[0] > 0 else float("nan")})
    return out


def pares_nulo(pasadas, campo_vrp, campo_pub, dz_max=DZ_NULO, condicionar=True, semilla=SEMILLA):
    """El nulo: por noche-volcán, el par de pasadas con alerta de MIROVA de menor diferencia de cenit, si es menor que
    dz_max, ordenado como la lectura (menor cenit primero). Mismas claves que pares_por_noche. `semilla` no se usa
    (queda en la firma por compatibilidad)."""
    por = collections.defaultdict(list)
    for p in pasadas:
        if p.get("z") is None or not (p.get("mir") or 0) > 0:
            continue
        if condicionar and not p.get(campo_pub):
            continue
        por[(p["vol"], p["hora"][:10])].append(p)
    out = []
    for (vol, noche), lst in sorted(por.items()):
        lst = sorted(lst, key=lambda p: p["hora"])
        mejor = None
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                dz = abs(lst[i]["z"] - lst[j]["z"])
                if dz < dz_max and (mejor is None or dz < mejor[0]):
                    mejor = (dz, lst[i], lst[j])
        if mejor is None:
            continue
        a, b = sorted([mejor[1], mejor[2]], key=lambda p: (p["z"], p["hora"]))   # la misma regla que la lectura
        va = (a.get(campo_vrp) or 0.0) if a.get(campo_pub) else 0.0
        vb = (b.get(campo_vrp) or 0.0) if b.get(campo_pub) else 0.0
        if va <= 0:
            continue
        out.append({"vol": vol, "noche": noche, "z": [a["z"], b["z"]], "r_mir": b["mir"] / a["mir"], "r_x": vb / va,
                    "d": (vb / va) / (b["mir"] / a["mir"])})
    return out


def sesgo_plataforma(pasadas, campo_vrp, campo_pub, margen=math.log10(1.25)):
    """Mediana de log10(nuestro VRP / VRP de MIROVA) por plataforma, en las pasadas con alerta de MIROVA que publicamos,
    con su IC por bootstrap. SESGADO si dos plataformas difieren en más de log10(1,25) con los IC sin solaparse."""
    por = collections.defaultdict(list)
    for p in pasadas:
        if (p.get("mir") or 0) > 0 and p.get(campo_pub) and (p.get(campo_vrp) or 0) > 0 and p.get("plat"):
            por[p["plat"]].append(math.log10(p[campo_vrp] / p["mir"]))
    res = {k: mediana_ic(v) for k, v in sorted(por.items())}
    sesgo = False
    ks = list(res)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a, b = res[ks[i]], res[ks[j]]
            if abs(a[0] - b[0]) > margen and (a[1][1] < b[1][0] or b[1][1] < a[1][0]):
                sesgo = True
    return {"por_plataforma": {k: {"mediana_log10": v[0], "ic": v[1], "n": v[2], "factor": 10 ** v[0]}
                               for k, v in res.items()}, "sesgado": sesgo}


def mediana_ic(vals, n_boot=2000, semilla=SEMILLA):
    v = np.array([x for x in vals if x is not None and math.isfinite(x)], float)
    if not len(v):
        return float("nan"), (float("nan"), float("nan")), 0
    rng = np.random.default_rng(semilla)
    b = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(n_boot)]
    return float(np.median(v)), (float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))), len(v)


def resumen(pares, tramos=((0, 50), (50, 90)), nulo=None):
    """Mediana e IC (bootstrap por noche: un par por noche, así que es por noche) de r_mir, r_x y d, en total y por
    tramo del cenit de la pasada oblicua; y el nulo por hora."""
    out = {}
    for nom, sel in [("todas", pares)] + [(f"oblicua {a}-{b}", [p for p in pares if a <= p["z"][1] < b])
                                          for a, b in tramos]:
        out[nom] = {k: mediana_ic([p[k] for p in sel]) for k in ("r_mir", "r_x", "d", "r_mir_hora", "r_x_hora")}
        out[nom]["bajo_1_mir"] = sum(1 for p in sel if p["r_mir"] < 1)
        out[nom]["n_noches"] = len(sel)
    for nom, sel in (("misma plataforma", [p for p in pares if p.get("plat") and p["plat"][0] == p["plat"][1]]),
                     ("plataformas distintas", [p for p in pares if p.get("plat") and p["plat"][0] != p["plat"][1]])):
        out[nom] = {"d": mediana_ic([p["d"] for p in sel]), "n_noches": len(sel)}
    if nulo is not None:
        out["nulo"] = {k: mediana_ic([p[k] for p in nulo]) for k in ("r_mir", "r_x", "d")}
        out["nulo"]["n_noches"] = len(nulo)
    return out


def veredicto(res, d_min=0.8, d_max=1.25, n_min=8):
    """PREREGISTRO_E.md §5.3. SIN SUSTRATO con menos de n_min noches en la lectura o en el nulo. NULO SESGADO si el IC de
    la razón doble en el nulo de cenit parecido no contiene 1 (nuestra razón contra MIROVA cambia sin cambiar el cenit:
    hay un sesgo de pasada a pasada que no es el cenit). Si no: CAE MAS QUE MIROVA si el IC de la mediana de d queda
    entero bajo 1; CAE MENOS si queda entero sobre 1; REPRODUCE LA CURVA si lo contiene y la mediana está en
    [0,8; 1,25]; NO RESUELTO en otro caso. La marca «curva de MIROVA no separada del nulo» (el IC de MIROVA por cenit
    contiene la mediana de MIROVA en el nulo) se informa al lado y no bloquea: d compara las dos caídas en los mismos
    pares, y si MIROVA casi no cae, un d bajo 1 sigue diciendo que nosotros caemos más."""
    t = res["todas"]
    nu = res.get("nulo")
    if t["n_noches"] < n_min or nu is None or nu["n_noches"] < n_min:
        return "SIN SUSTRATO"
    if not (nu["d"][1][0] <= 1 <= nu["d"][1][1]):
        return "NULO SESGADO"
    d, ic, _ = t["d"]
    if ic[1] < 1:
        return "CAE MAS QUE MIROVA"
    if ic[0] > 1:
        return "CAE MENOS QUE MIROVA"
    return "REPRODUCE LA CURVA" if d_min <= d <= d_max else "NO RESUELTO"


def curva_mirova_separada(res):
    t, nu = res["todas"], res.get("nulo")
    if nu is None or not nu["n_noches"]:
        return None
    return not (t["r_mir"][1][0] <= nu["r_mir"][0] <= t["r_mir"][1][1])
