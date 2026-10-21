# -*- coding: utf-8 -*-
"""S158: resume el probe de M15 (artefactos del run) con la regla de lectura escrita antes de correr (README).

Uso:  python experiments/_s158_v750/analizar_probe.py <carpeta con probe_m15_parte*.json>
"""
from __future__ import annotations

import collections
import json
import statistics
import sys
from pathlib import Path


def mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def main(carpeta):
    res = []
    for f in sorted(Path(carpeta).rglob("probe_m15_parte*.json")):
        res.extend(json.loads(f.read_text(encoding="utf-8")))
    print(f"pasadas en los artefactos: {len(res)} | ok {sum(r.get('ok', False) for r in res)}")
    errores = [r for r in res if not r.get("ok")]
    for r in errores:
        print(f"  sin medir: {r['pasada']['grupo']} {r['pasada']['vol']} {r['pasada']['dt']} {r.get('error')}")
    ok = [r for r in res if r.get("ok")]
    print(f"C-P1 en verde: {sum(bool(r.get('C_P1')) for r in ok)} de {len(ok)}")
    for r in ok:
        if not r.get("C_P1"):
            p, c = r["pasada"], r.get("control") or {}
            print(f"  C-P1 rojo: {p['grupo']} {p['vol']} {p['dt']} persistido pc {p['pc_vrp']} npx {p['n_anomalous_pixels']} "
                  f"dc {p['dc']} | control pc {(c.get('primary_cluster') or {}).get('vrp_mw')} "
                  f"npx {c.get('n_anomalous_pixels')} dc {c.get('distance_class')} | nota {r.get('nota_granulo')}")
    nulos = [r for r in ok if "C_NULO" in r]
    print(f"C-NULO (escena sin nti_perdido): {sum(r['C_NULO'] for r in nulos)} de {len(nulos)} identicos")
    # control del predicado: el control debe reproducir la etiqueta publica/no publica del grupo
    pub_ctrl = collections.Counter((r["pasada"]["grupo"], r.get("pub_control")) for r in ok)
    print("publica el control, por grupo:", dict(pub_ctrl))
    v = [r for r in ok if r.get("C_P1")]
    for g in ("P", "C"):
        s = [r for r in v if r["pasada"]["grupo"] == g]
        if not s:
            continue
        toca = [r for r in s if r["ventana"]["nti_perdido"] > 0]
        foco = [r for r in s if r["ventana"].get("max_m13_nti_perdido")]
        top3 = [r for r in s if (r["ventana"].get("top3_m13_nti_perdido") or 0) > 0]
        print(f"\n[{g}] n {len(s)} | toca {len(toca)} | toca el foco (max M13) {len(foco)} | "
              f"alguno de los 3 mas calientes {len(top3)}")
        cod = collections.Counter()
        for r in s:
            cod.update(r["ventana"]["nti_perdido_por_codigo_m15"])
        print(f"  nti_perdido por codigo de M15 (suma): {dict(cod)} | sin sentinela "
              f"{sum(r['ventana']['nti_perdido_sin_sentinela'] for r in s)} | mascara 4 "
              f"{sum(r['ventana']['m15_mask4_sat'] for r in s)} | mascara 256 {sum(r['ventana']['m15_mask256_bowtie'] for r in s)}"
              f" | mascara 2048 {sum(r['ventana']['m15_mask2048_dead'] for r in s)} | sobre techo "
              f"{sum(r['ventana']['m15_sobre_techo'] for r in s)} | M13 sentinela "
              f"{dict(sum((collections.Counter(r['ventana']['m13_sentinela']) for r in s), collections.Counter()))}")
        con65533 = [r for r in s if r["ventana"]["m15_sentinela"].get("65533")]
        print(f"  pasadas con M15 = 65533 en la ventana: {len(con65533)} (pixeles {sum(r['ventana']['m15_sentinela'].get('65533', 0) for r in s)}"
              f" de {sum(r['ventana']['n'] for r in s)}); M15 sentinela por codigo: "
              f"{dict(sum((collections.Counter(r['ventana']['m15_sentinela']) for r in s), collections.Counter()))}")
        print(f"  ventanas con m13_valido == m15_valido: {sum(r['ventana']['m13_valido'] == r['ventana']['m15_valido'] for r in s)} de {len(s)}"
              f" | escena entera con nti_perdido > 0: {sum(r['escena_nti_perdido'] > 0 for r in s)}")
        for lo, hi in ((0, 20), (20, 35), (35, 50), (50, 90)):
            b = [r for r in s if r["pasada"]["z"] is not None and lo <= r["pasada"]["z"] < hi]
            if b:
                print(f"    cenit {lo}-{hi}: {len(b)} pasadas, con 65533 en la ventana {sum(1 for r in b if r in con65533)}")
        d = [x for r in toca for x in (r["cobertura"].get("dist_km") or []) if x is not None]
        esp = [r["cobertura"].get("espaciado_validos_km_mediana") for r in toca]
        print(f"  cobertura: distancia al valido mas cercano, mediana {mediana(d)} km, max {max(d) if d else None}; "
              f"espaciado tipico mediana {mediana(esp)} km")
        print(f"  cenit de la ventana: toca {mediana([r.get('cenit_ventana_mediana') for r in toca])} | "
              f"no toca {mediana([r.get('cenit_ventana_mediana') for r in s if r not in toca])}")
        cambia = [r for r in s if r.get("pub_control") != r.get("pub_relleno")]
        print(f"  publicacion control -> relleno: " + str(dict(collections.Counter(
            (r.get("pub_control"), r.get("pub_relleno")) for r in s))))
        for r in cambia:
            p = r["pasada"]
            print(f"    cambia: {p['vol']} {p['dt']} {p['mecanismo']} M={p['mirova_vrp_mw']} "
                  f"control {r.get('pub_control')} relleno {r.get('pub_relleno')} toca {r['ventana']['nti_perdido']}")
        if g == "P":
            dec = [r for r in s if not r.get("pub_control") and r.get("pub_relleno")]
            print(f"  EL LECTOR DECIDE (publica solo con relleno): {len(dec)} de {len(s)}")
            print("  por mecanismo, toca:", dict(collections.Counter(r["pasada"]["mecanismo"] for r in toca)),
                  "| total:", dict(collections.Counter(r["pasada"]["mecanismo"] for r in s)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
