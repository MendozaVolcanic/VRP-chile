"""S147 - cuando el cumulo publicado se mueve, se acerca o se aleja de donde MIROVA lo pone?

LA PREGUNTA, Y POR QUE IMPORTA. El A/B sin Test 1 mueve el cumulo publicado mas de 500 m en 96 de
532 pasadas. "Se movio" no es lo mismo que "empeoro": el Test 1 trabaja sobre MIR absoluto y en
volcanes nevados eso se deja arrastrar por el valle tibio de baja altitud (A69), asi que es
posible que estuviera corriendo el punto HACIA AFUERA del crater y apagarlo lo devuelva. La
pregunta no es cuanto se mueve sino hacia donde, y para el perfil que replica a MIROVA el "donde"
correcto es donde MIROVA lo pone.

EL LIMITE MAS IMPORTANTE, declarado antes del resultado (A93, A107, D15). El CSV de MIROVA trae
`Distancia_km` y NO trae acimut. Comparar dos radios NO es comparar dos posiciones: la diferencia
de radios es una cota INFERIOR de la distancia entre los puntos, asi que dos objetos en lados
opuestos del crater pueden tener el mismo radio. Ademas ese radio esta CUANTIZADO a la celda de la
grilla de MIROVA (D15), por eso aparecen tantos 0,0. Este instrumento responde "el radio se acerco
o se alejo", que es mas debil que "el punto se acerco", y no hay que leerlo como lo segundo. Lo
unico que daria la respuesta fuerte es el acimut, o sea los GeoTIFF de MIROVA, y de esos solo ocho
adquisiciones estan en UTM nativo (A106).

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el brazo no cambiara nada, esto lo mostraria? SI: la columna "se movio" saldria vacia y el
   balance seria 0 contra 0.
2. Si el instrumento estuviera muerto? El control de abajo compara el CONTROL contra si mismo: su
   balance tiene que dar exactamente 0 acercamientos y 0 alejamientos, porque es el mismo dato.

Uso:  python experiments/_s147_pos/hacia_donde_se_movio.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s146_ab_sin_test1"))

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave, _hav  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

BASE = ROOT / "experiments" / "_s147_pos" / "experiments" / "_s146_ab_sin_test1" / "salidas" / "35521542153"
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
VENTANA = ("2026-09-01", "2026-09-20")
MOVIMIENTO_MIN_KM = 0.5


def indice(recs):
    return {clave(r): r for r in recs}


def dist_mirova(por_vb, r):
    """Distancia que MIROVA publico para ESA pasada, si publico alguna."""
    filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
    ds = [f["dist_km"] for f in filas if f.get("dist_km") is not None and bp.es_alerta(f["tipo"])]
    return ds[0] if ds else None


def comparar(ctrl, brazo, por_vb, etiqueta):
    ib = indice(brazo)
    acerca = aleja = igual = sin_ref = 0
    detalle = []
    for c in ctrl:
        b = ib.get(clave(c))
        if b is None or not (c["pub"] and b["pub"]):
            continue
        if None in (c.get("pc_lat"), c.get("pc_lon"), b.get("pc_lat"), b.get("pc_lon")):
            continue
        sep = _hav(c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"])
        if sep <= MOVIMIENTO_MIN_KM:
            continue
        dm = dist_mirova(por_vb, c)
        if dm is None:
            sin_ref += 1
            continue
        ec, eb = abs((c.get("pc_dist") or 0) - dm), abs((b.get("pc_dist") or 0) - dm)
        if abs(eb - ec) < 0.05:
            igual += 1
        elif eb < ec:
            acerca += 1
        else:
            aleja += 1
        detalle.append((c["vol"], c["b"], c["dt"].strftime("%m-%d %H:%M"), round(sep, 2),
                        c.get("pc_dist"), b.get("pc_dist"), dm, round(eb - ec, 2)))
    print(f"\n=== {etiqueta} ===")
    print(f"  pasadas con el cumulo movido mas de {MOVIMIENTO_MIN_KM} km: "
          f"{acerca + aleja + igual + sin_ref}")
    print(f"  de esas, SIN alerta de MIROVA con distancia (no comparables): {sin_ref}")
    print(f"  comparables: {acerca + aleja + igual}  ->  se ACERCA al radio de MIROVA: {acerca} | "
          f"se ALEJA: {aleja} | igual dentro de 50 m: {igual}")
    if detalle:
        print(f"  {'volcan':22} {'sensor':9} {'pasada':12} {'movio':>6} {'ctrl':>6} {'brazo':>6} "
              f"{'MIROVA':>7} {'delta':>6}")
        for d in sorted(detalle, key=lambda x: x[7])[:20]:
            pcd = f"{d[4]:.2f}" if d[4] is not None else "  -  "
            pbd = f"{d[5]:.2f}" if d[5] is not None else "  -  "
            print(f"  {d[0]:22} {d[1]:9} {d[2]:12} {d[3]:6.2f} {pcd:>6} {pbd:>6} {d[6]:7.2f} {d[7]:+6.2f}")
    return acerca, aleja, igual


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)

    ctrl = cargar_brazo(BASE / "_s146_ab_control", coords, inner, VENTANA)
    brazo = cargar_brazo(BASE / "_s146_ab_sin_test1", coords, inner, VENTANA)
    bp.etiquetar(ctrl, por_vb, ns, nv)
    bp.etiquetar(brazo, por_vb, ns, nv)

    comparar(ctrl, brazo, por_vb, "control contra sin Test 1")
    # Control del instrumento: el control contra si mismo no puede mover nada.
    a, al, ig = comparar(ctrl, ctrl, por_vb, "CONTROL DEL INSTRUMENTO: control contra si mismo")
    assert a == al == ig == 0, "el control contra si mismo movio algo: el instrumento esta roto"
    print("\nLIMITE: `Distancia_km` de MIROVA es un RADIO sin acimut y cuantizado a su celda.")
    print("Esto responde 'el radio se acerco o se alejo', que es mas debil que 'el punto se acerco'.")


if __name__ == "__main__":
    main()
