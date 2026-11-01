# -*- coding: utf-8 -*-
"""S165, Tarea 3 paso 0 del plan 2026-10-25-flag-mxd03-modis: ¿la regla de «sin dato» deja fuera sólo lo que debe?

POR QUÉ. La regla `crater_cubierto` del plan dice que el cráter está en la imagen si el píxel MxD03 más cercano no está
en la primera o última línea o frame del gránulo y sus 8 vecinos tienen posición. Es una hipótesis (A115): antes de
escribirla en pipeline/ se mide en el censo MOD-D (5.465 pasadas nocturnas, MxD03 real), que guardó para cada pasada
`crater_mxd03` = {borde, vecinos_validos, dist_km} con la misma definición (probe_paquete.py, l. 140 a 145). Con
`vecinos_validos` la ventana se recorta en el borde, así que `borde` implica `vecinos_validos` falso: la regla del plan
es exactamente `vecinos_validos`.

Lo que se mide:
  1. cuántas pasadas quedan «sin dato» y por qué (borde, relleno);
  2. la distancia del píxel más cercano al cráter en las cubiertas (una cubierta normal está a menos de ~0,7 km: medio
     píxel en la diagonal, más el estiramiento del barrido) y en las no cubiertas;
  3. qué etiqueta de la referencia tienen las no cubiertas (protegida, bajo 1 MW, negativo limpio, otra) y si K las
     publicaba: si una alerta de MIROVA cae en «sin dato», se lista y decide Nicolás (plan §1).

Uso: python experiments/_s165_mxd03_flag/paso0_regla_sin_dato.py D:/vrp-trabajo/temporales/s162_modd/censo
"""
import collections
import glob
import json
import statistics
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def cargar(raiz):
    recs = []
    for f in sorted(glob.glob(str(Path(raiz) / "**" / "ab_parte*.jsonl"), recursive=True)):
        for linea in open(f, encoding="utf-8"):
            r = json.loads(linea)
            if r.get("tipo") == "record":
                recs.append(r)
    return recs


def cuantiles(xs):
    if not xs:
        return "sin casos"
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]
    return f"n={len(xs)} min={xs[0]} p50={statistics.median(xs)} p99={q(0.99)} max={xs[-1]}"


def main(raiz):
    recs = cargar(raiz)
    print(f"records del censo: {len(recs)}")
    sin_campo = [r for r in recs if not r.get("crater_mxd03")]
    print(f"sin crater_mxd03: {len(sin_campo)}")
    con = [r for r in recs if r.get("crater_mxd03")]
    c = lambda r: r["crater_mxd03"]
    cubierta = lambda r: bool(c(r)["vecinos_validos"]) and not bool(c(r)["borde"])
    print("\n1. clasificación (borde, vecinos_validos):",
          dict(collections.Counter((bool(c(r)["borde"]), bool(c(r)["vecinos_validos"])) for r in con)))
    print("   borde verdadero con vecinos válidos (debería ser 0):",
          sum(1 for r in con if c(r)["borde"] and c(r)["vecinos_validos"]))
    no = [r for r in con if not cubierta(r)]
    si = [r for r in con if cubierta(r)]
    print(f"   cubiertas: {len(si)}  sin dato: {len(no)} ({100 * len(no) / max(len(con), 1):.2f} %)")
    print(f"   sin dato por borde: {sum(1 for r in no if c(r)['borde'])}, por relleno (no borde): "
          f"{sum(1 for r in no if not c(r)['borde'])}")

    print("\n2. distancia del píxel MxD03 más cercano al cráter (km)")
    print("   cubiertas:", cuantiles([c(r)["dist_km"] for r in si]))
    print("   sin dato, borde:", cuantiles([c(r)["dist_km"] for r in no if c(r)["borde"]]))
    print("   sin dato, relleno:", cuantiles([c(r)["dist_km"] for r in no if not c(r)["borde"]]))
    lejos = [r for r in si if c(r)["dist_km"] > 1.0]
    print(f"   cubiertas con el píxel a más de 1 km (cráter quizá fuera aunque la regla diga cubierto): {len(lejos)}")
    for r in lejos[:20]:
        print("    ", r["vol"], r["dt"], r["sensor"], r["lab"], c(r))

    print("\n3. etiqueta de la referencia y publicación K")
    print("   todas:", dict(collections.Counter(r["lab"] for r in con)))
    print("   sin dato:", dict(collections.Counter((r["lab"], int((r.get("pub") or {}).get("K") or 0)) for r in no)))
    alertas = [r for r in no if r["lab"] in ("protegida", "bajo1")]
    print(f"   alertas de MIROVA en «sin dato»: {len(alertas)}")
    for r in alertas:
        print("    ", r["vol"], r["dt"], r["sensor"], r["lab"], "K publica:", (r.get("pub") or {}).get("K"), c(r))
    pub_k = [r for r in no if int((r.get("pub") or {}).get("K") or 0)]
    print(f"   sin dato que K publicaba: {len(pub_k)}")
    for r in pub_k:
        print("    ", r["vol"], r["dt"], r["sensor"], r["lab"], c(r))
    print("\n   sin dato por volcán:", dict(collections.Counter(r["vol"] for r in no).most_common()))


if __name__ == "__main__" and len(sys.argv) == 2:
    main(sys.argv[1])


def borde_cerca(raiz):
    """4. Las de borde con el cráter cerca del píxel (≤ 1 km) SÍ tienen el cráter en la imagen, en la primera o última
    línea o frame. ¿Tiene el volcán otra pasada del mismo satélite a ±5 min (el gránulo vecino) en el censo?"""
    from datetime import datetime, timedelta
    recs = [r for r in cargar(raiz) if r.get("crater_mxd03")]
    idx = {(r["vol"], r["sensor"], r["dt"]): r for r in recs}
    b = [r for r in recs if r["crater_mxd03"]["borde"]]
    print("\n4. borde por distancia del píxel más cercano:",
          dict(collections.Counter("<=1km" if r["crater_mxd03"]["dist_km"] <= 1 else ">1km" for r in b)))
    for umbral in ("<=1km", ">1km"):
        sub = [r for r in b if (r["crater_mxd03"]["dist_km"] <= 1) == (umbral == "<=1km")]
        vecino = 0
        for r in sub:
            t = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
            for d in (-5, 5):
                o = idx.get((r["vol"], r["sensor"], (t + timedelta(minutes=d)).strftime("%Y-%m-%d %H:%M")))
                if o and not o["crater_mxd03"]["borde"] and o["crater_mxd03"]["vecinos_validos"]:
                    vecino += 1
                    break
        print(f"   {umbral}: {len(sub)}, con gránulo vecino cubierto en el censo: {vecino}")


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2] == "--borde":
    borde_cerca(sys.argv[1])
