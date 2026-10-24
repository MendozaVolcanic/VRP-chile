# -*- coding: utf-8 -*-
"""S162 MODIS, lote de negativos neg_resto (decision D-36/D-48 de Nicolas, 2026-10-24): sorteo del lote de solo
lectura que resuelve o refuta el «GANA» del port de MIROVA en MODIS (experiments/_s159/portes/INFORME.md P-1,
verificador V-1).

POR QUE ESTE LOTE. En S159 el port publico en 0 de 37 pasadas sorteadas del estrato neg_resto (MIROVA miro y no vio
nada; produccion tampoco publica). Ese estrato son 5.093 pasadas MODIS, cada sorteada pesaba ~134, y con 0 eventos
el bootstrap estratificado no ve nada: el silencio del port quedaba acotado solo por Wilson (hasta 9,4 %). Este
script sortea un lote nuevo del MISMO estrato, de la MISMA poblacion congelada (poblacion_completa.json de S159, sin
reconstruirla: la poblacion viva cambia sola, A90), SIN repetir las pasadas ya sorteadas.

DISENO. Asignacion PROPORCIONAL por estrato volcan x cenit (<= 40, > 40), redondeo por mayor resto, semilla 162.
Proporcional y no igual (como S159) para que la muestra sea autoponderada: la tasa del estrato se estima con x / n
crudo y la cota de Wilson / Jeffreys vale sin pesos. El marco excluye las 38 sorteadas en S159 (clave volcan, hora,
granulo); su resultado ya se conoce y se suma aparte (PREREGISTRO.md §5).

ETIQUETA. La de la poblacion de S159: banco_paridad.etiquetar a +-120 s, regla D-9 en modo SN (en MODIS no actua:
clase_mirova.SENSORES_MINIMA = VIIRS375), negativo limpio = MIROVA miro (hay fila suya a +-120 s) y ninguna fila es
alerta, en la tabla Y en el OCR. A119: en MODIS la tabla esta completa y es plana desde marzo; el OCR se informa
aparte: este script cuenta las pasadas que serian negativas con la tabla sola (alerta solo del OCR) y no las sortea.

Uso: python -I 01_seleccion.py [--previos <carpeta con poblacion_completa.json y objetivos_portes.json de S159>]
     [--n 400]
Por defecto lee experiments/_s159/portes/ del arbol donde corre (en el runner, el commit base 0e18e1053).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import math
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SEMILLA = 162
EXCLUIDOS = ("2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")   # los mismos de S159 (02_seleccion.py)
ID0 = 1000          # ids nuevos desde 1000: no chocan con los 0 a 309 del lote de S159 al juntar resultados
SHA_POBLACION = "cb48ddd4c90498aaff5bdd3a3341ea3e7688337c"   # git blob de poblacion_completa.json en 0e18e1053
SHA_OBJETIVOS = "7455d89c5312acc435f2e740fb39c43990478e0f"   # git blob de objetivos_portes.json en 0e18e1053


def blob_sha(p: Path) -> str:
    """sha1 del blob de git, con fin de linea LF (un checkout con autocrlf en Windows lo deja en CRLF)."""
    b = p.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def wilson_sup(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d


def clave(o):
    return (o["volcan"], o["hora_utc"], o["granule"])


def asignar_proporcional(tam, n):
    """Mayor resto (Hamilton). tam: {estrato: N_h}. Devuelve {estrato: n_h} con suma n y n_h <= N_h."""
    N = sum(tam.values())
    cuota = {k: n * v / N for k, v in tam.items()}
    a = {k: min(int(math.floor(c)), tam[k]) for k, c in cuota.items()}
    resto = n - sum(a.values())
    for k in sorted(tam, key=lambda k: (-(cuota[k] - math.floor(cuota[k])), k)):
        if resto <= 0:
            break
        if a[k] < tam[k]:
            a[k] += 1
            resto -= 1
    assert sum(a.values()) == n
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previos", default=str(RAIZ / "experiments/_s159/portes"))
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--salida", default=str(AQUI / "objetivos_neg_resto_modis.json"))
    a = ap.parse_args()
    prev = Path(a.previos)
    fp, fo = prev / "poblacion_completa.json", prev / "objetivos_portes.json"
    sp, so = blob_sha(fp), blob_sha(fo)
    print("insumos:", fp.name, sp, "(esperado", SHA_POBLACION + ")", "|", fo.name, so, "(esperado", SHA_OBJETIVOS + ")")
    assert sp == SHA_POBLACION and so == SHA_OBJETIVOS, "insumos distintos de los del lote S159: no se sortea"
    pob = json.loads(fp.read_text(encoding="utf-8"))
    print("meta de la poblacion:", json.dumps(pob["meta"], ensure_ascii=False))
    todas = [o for o in pob["pasadas"] if o["b"] == "MODIS"]
    print(f"\n== MODIS en la poblacion congelada: {len(todas)} pasadas (pos + negativos limpios, "
          f"{pob['meta']['ventanas']['MODIS']})")
    d = [o for o in todas if o["hora_utc"][:10] not in EXCLUIDOS and o["decide"]]
    print("  sin 17 a 20 de octubre y solo las que deciden:", len(d))
    clases = collections.defaultdict(list)
    for o in d:
        if o["lab"] == "pos":
            k = "pos_prot" if o["protegida"] else "pos_bajo"
        else:
            k = "neg_pub" if o["pub_prod"] else "neg_resto"
        clases[k].append(o)
    print("  clases:", {k: len(v) for k, v in sorted(clases.items())},
          "(S159, 02_seleccion_salida.txt: pos_prot 50, neg_resto 5093, pos_bajo 42, neg_pub 39)")
    neg = clases["neg_resto"]
    assert len(neg) == 5093, "no reproduce los 5.093 de S159"
    assert len({clave(o) for o in neg}) == len(neg), "clave volcan-hora-granulo repetida"

    # A119: lo que la tabla sola diria y la etiqueta conjunta no (no se sortea, se informa)
    solo_ocr = [o for o in clases["pos_prot"] + clases["pos_bajo"] if not o.get("alerta_tabla")]
    tabla_rutina = [o for o in solo_ocr if any(f["source"] == "CONS" for f in o["mirova"])]
    print("\n== A119, canal por canal (MODIS)")
    print(f"  alertas MODIS solo del OCR (la tabla no alerta): {len(solo_ocr)}; de ellas con fila RUTINA en la tabla "
          f"(serian negativo con la tabla sola): {len(tabla_rutina)}; K no publica en "
          f"{sum(not o['pub_prod'] for o in tabla_rutina)}")
    for o in solo_ocr:
        print("    ", o["volcan"], o["hora_utc"], "K publica" if o["pub_prod"] else "K no publica",
              [(f["source"], f["tipo"], f["vrp_mw"]) for f in o["mirova"]])
    fuentes = collections.Counter(tuple(sorted({f["source"] for f in o["mirova"]})) for o in neg)
    tipos_ocr = collections.Counter(f["tipo"] for o in neg for f in o["mirova"] if f["source"] == "OCR")
    print("  neg_resto por canal con fila de MIROVA:", dict(fuentes))
    print("  tipos de fila OCR dentro de neg_resto:", dict(tipos_ocr))

    # lo ya sorteado en S159
    objp = json.loads(fo.read_text(encoding="utf-8"))
    ya = [o for o in objp if o["b"] == "MODIS" and o["clase"] == "neg_resto"]
    ya_k = {clave(o) for o in ya}
    assert ya_k <= {clave(o) for o in neg}, "una sorteada de S159 no esta en el estrato"
    print(f"\n== ya sorteadas en S159 (neg_resto MODIS): {len(ya)}; ids {sorted(o['id'] for o in ya)}")
    marco = [o for o in neg if clave(o) not in ya_k]
    print("  marco del sorteo (estrato sin las ya sorteadas):", len(marco))

    est = collections.defaultdict(list)
    for o in marco:
        est[(o["volcan"], o["estrato_z"])].append(o)
    tam = {k: len(v) for k, v in est.items()}
    asign = asignar_proporcional(tam, a.n)
    rng = random.Random(SEMILLA)
    grilla = {}
    for o in objp:
        if o["b"] == "MODIS":
            grilla.setdefault(o["volcan"], o["grilla"])
    elegidos = []
    for k in sorted(est):
        lst = sorted(est[k], key=lambda o: (o["hora_utc"], o["granule"]))
        for o in rng.sample(lst, asign[k]):
            assert o["volcan"] in grilla, f"sin grilla MODIS para {o['volcan']}"
            elegidos.append({**o, "clase": "neg_resto", "peso": tam[k] / asign[k], "estrato": f"{k[0]}|{k[1]}",
                             "grilla": grilla[o["volcan"]]})
    print(f"\n== sorteo: n = {len(elegidos)}, semilla {SEMILLA}, asignacion proporcional volcan x cenit")
    for k in sorted(est):
        print(f"   {k[0]:<22} {k[1]:<6} N_h {tam[k]:>4}  n_h {asign[k]:>3}  peso {tam[k] / asign[k]:.2f}")
    pesos = [e["peso"] for e in elegidos]
    print(f"  pesos: min {min(pesos):.2f} max {max(pesos):.2f} (autoponderada si son casi iguales); suma "
          f"{sum(pesos):.1f} (= marco {len(marco)})")
    print("  partidas elegidas:", sum(bool(e.get("partida")) for e in elegidos))
    print("  por mes:", dict(sorted(collections.Counter(e["hora_utc"][:7] for e in elegidos).items())))
    print("  por plataforma:", dict(collections.Counter(e["sensor"] for e in elegidos)))
    t535 = "2026-08-28 23:00"
    print(f"  tramos A104: antes de #535 ({t535} UTC) {sum(e['hora_utc'] < t535 for e in elegidos)}, desde "
          f"{sum(e['hora_utc'] >= t535 for e in elegidos)}; antes de 2026-09-18 "
          f"{sum(e['hora_utc'] < '2026-09-18' for e in elegidos)}")
    print("  sha de los records elegidos:", dict(collections.Counter(e["sha"] for e in elegidos)))
    assert not ({clave(e) for e in elegidos} & ya_k), "repite una sorteada de S159"
    assert len({clave(e) for e in elegidos}) == len(elegidos)

    print("\n== cota de Wilson (95 %) con 0 eventos, para el tamano")
    for n in (37, 100, 200, 300, 350, 400):
        print(f"   n {n:>3}: superior {wilson_sup(0, n):.4f} -> {wilson_sup(0, n) * len(marco):.1f} pasadas del marco")
    elegidos.sort(key=lambda e: (e["granule"], e["volcan"]))
    for i, e in enumerate(elegidos):
        e["id"] = ID0 + i
    print("  granulos unicos:", len({e["granule"] for e in elegidos}), "| ids", elegidos[0]["id"], "a",
          elegidos[-1]["id"])

    # CONTROL de instrumento (peso 0, no entra a ningun denominador): pasadas del lote S159 re-corridas con el
    # mismo id. Un estrato donde se espera 0 no distingue «el port calla» de «el port esta muerto» (A116): las
    # protegidas tienen que volver a encender con el mismo npix y VRP que en S159, y las neg_resto a callar.
    # Generador aparte (semilla 163) para no mover el sorteo principal.
    rc = random.Random(SEMILLA + 1)
    prot_prev = sorted((o for o in objp if o["b"] == "MODIS" and o["clase"] == "pos_prot"), key=lambda o: o["id"])
    neg_prev = sorted((o for o in ya if o["id"] not in (4, 57)), key=lambda o: o["id"])   # sin la escena invalida
    ctl = rc.sample(prot_prev, 8) + rc.sample(neg_prev, 2)                                  # ni la fuera del granulo
    for o in ctl:
        elegidos.append({**o, "clase": "control_s159", "clase_s159": o["clase"], "peso": 0.0})
    print("  control de instrumento (lote S159, mismo id):",
          [(o["id"], o["volcan"], o["hora_utc"], o["clase"]) for o in ctl])
    assert len({e["id"] for e in elegidos}) == len(elegidos)
    Path(a.salida).write_bytes(json.dumps(elegidos, ensure_ascii=False, indent=0, default=str).encode("utf-8"))
    print("escrito", Path(a.salida).name, "sha", blob_sha(Path(a.salida)))


if __name__ == "__main__":
    main()
