"""S147 - lectura de un brazo del A/B contra su control, SOLO sobre el tramo con cobertura exacta.

POR QUE EXISTE. El A/B de la conectiva (run 35548121381) termino con 22 de 22 reprocesos en verde
y con el brazo de CONTROL corto en 71 pasadas: Chaiten, Tupungatito y Villarrica, todas del 18 al
20 de septiembre, en todos los sensores. Es la firma de un corte de disponibilidad de NASA para las
fechas mas recientes (A64), y es justo el lado que el contador de cobertura ignoraba hasta el
arreglo simetrico de S147 (hallazgo H3 del verificador): antes habria impreso COBERTURA PAREJA.

La regla pre-registrada es INDECIDIBLE hasta reparar, y se respeta: este script NO da el veredicto.
Da una lectura PRELIMINAR sobre el tramo de la ventana donde los dos brazos tienen exactamente las
mismas pasadas, y se niega a leer si en ese tramo la cobertura no es identica.

QUE MIDE: las cuatro cantidades de las predicciones P1 a P4 del pre-registro
(experiments/_s147_ab_conectiva/PREREGISTRO.md): publicacion en negativos limpios, por zona del
barrido, la celda borde con fondo frio, la razon borde sobre nadir, y el recall por pasada.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el brazo no cambiara nada, esto lo mostraria? SI: las dos columnas saldrian iguales. Se
   comprueba corriendolo con --brazo igual a --control.
2. Si el instrumento estuviera muerto? Aborta si la cobertura del tramo no es exacta, y los totales
   del control tienen que parecerse a los de estructura_del_residual.py sobre el run anterior
   (29 % de publicacion en negativos limpios, razon borde sobre nadir cercana a 2).

Uso:
  git archive origin/s146-ab/<RUN> experiments/_s146_ab_sin_test1/salidas/<RUN> | tar -x -C experiments/_s147_lectura
  python experiments/_s147_lectura/lectura_por_tramo.py --run <RUN> --control _s146_ab_sin_test1 \
      --brazo _s147_ab_sin_test1_max --fin 2026-09-17
  (OJO: `git archive` SIEMPRE con la ruta; sin ruta extrae el repo entero.)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

AQUI = Path(__file__).resolve().parent
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"


def zona(z):
    return "nadir" if z < 36 else ("medio" if z < 52 else "borde")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", required=True)
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default="2026-09-20")
    ap.add_argument("--sensor", default="VIIRS375")
    a = ap.parse_args()
    D = AQUI / "experiments" / "_s146_ab_sin_test1" / "salidas" / a.run
    V = (a.inicio, a.fin)

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)

    def carga(br):
        recs = cargar_brazo(D / br, coords, inner, V)
        bp.etiquetar(recs, por_vb, ns, nv)
        raw = {}
        for vol in bp.VOLS:
            p = D / br / f"{vol}.json"
            if p.exists():
                for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
                    b = bp.bucket(r.get("sensor"))
                    if b:
                        raw[(vol, b, r.get("datetime_utc"))] = r
        return [(r, raw[clave(r)]) for r in recs if clave(r) in raw]

    C, B = carga(a.control), carga(a.brazo)
    kc, kb = {clave(r) for r, _ in C}, {clave(r) for r, _ in B}
    print(f"cobertura del tramo {V[0]} a {V[1]}: control {len(kc)}, brazo {len(kb)}, "
          f"faltan en el control {len(kb - kc)}, faltan en el brazo {len(kc - kb)}")
    if kc != kb:
        print("::error::la cobertura del tramo NO es exacta: no se lee. Acortar --fin o reparar.")
        return 1

    def tabla(datos):
        d = [(r, x) for r, x in datos if r["b"] == a.sensor
             and x.get("sensor_zenith_deg") is not None and x.get("t_bg_k") is not None]
        neg = [(r, x) for r, x in d if r["lab"] == "neg_limpio"]
        pos = [r for r, _ in d if r["lab"] == "pos"]
        t = lambda s: (sum(r["pub"] for r, _ in s), len(s))  # noqa: E731
        res = {"neg": t(neg), "pos": (sum(r["pub"] for r in pos), len(pos))}
        for z in ("nadir", "medio", "borde"):
            res[z] = t([(r, x) for r, x in neg if zona(x["sensor_zenith_deg"]) == z])
        res["borde_frio"] = t([(r, x) for r, x in neg
                               if zona(x["sensor_zenith_deg"]) == "borde" and x["t_bg_k"] < 260])
        return res

    rc, rb = tabla(C), tabla(B)
    pc = lambda q: f"{100 * q[0] / q[1]:5.1f}% ({q[0]}/{q[1]})" if q[1] else "n/a"  # noqa: E731
    raz = lambda r: ((r["borde"][0] / r["borde"][1]) / (r["nadir"][0] / r["nadir"][1])  # noqa: E731
                     if r["nadir"][0] and r["borde"][1] else float("nan"))
    completa = (a.inicio, a.fin) == ("2026-09-01", "2026-09-20")
    print(f"\n{'LECTURA SOBRE LA VENTANA COMPLETA' if completa else 'PRELIMINAR: tramo parcial, NO es el veredicto'}"
          f" | {a.sensor}")
    print(f"{'':36} {a.control[-22:]:>24} {a.brazo[-22:]:>24}")
    for k, n in (("neg", "publica en negativos limpios (P1)"), ("nadir", "  nadir"), ("medio", "  medio"),
                 ("borde", "  borde"), ("borde_frio", "  borde con fondo frio (P3)"),
                 ("pos", "recall por pasada (P4)")):
        print(f"{n:36} {pc(rc[k]):>24} {pc(rb[k]):>24}")
    print(f"{'razon borde sobre nadir (P2)':36} {raz(rc):24.2f} {raz(rb):24.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
