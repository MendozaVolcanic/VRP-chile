"""S147 - la ESTABILIDAD del cumulo publicado separa lo que MIROVA confirma de lo que niega.

DE DONDE SALE. El A/B sin Test 1 mueve el cumulo publicado mas de 500 m en 96 de 532 pasadas. Yo
habia convertido eso en un criterio con un umbral inventado ("cero cumulos movidos"), y Nicolas
señalo el error: el objetivo del proyecto es parecerse a MIROVA, asi que el umbral no lo elige
nadie, lo dice el dato. Al medirlo contra la referencia aparecio algo mejor que el criterio.

EL FENOMENO. Si en el crater hay un objeto termico real, cambiar QUE DETECTOR gana el ancla no lo
mueve: el objeto esta ahi y domina la seleccion del cumulo. Si solo hay ruido, el "cumulo" es lo
que el ruido armo esa noche, y cambiar el detector vuelve a tirar los dados. O sea que la
ESTABILIDAD DE LA POSICION entre dos configuraciones es una firma de que hay un objeto.

POR QUE NO LO ENCONTRO S116. Esa auditoria barrio todos los candidatos ESCALARES por record y
concluyo que ninguno separa el foco debil real del artefacto. Es cierto. Esto no es un escalar: es
una propiedad de la pasada bajo DOS configuraciones, asi que no estaba en el espacio que se barrio.

LO QUE ESTO NO ES: no es un detector. Para calcularlo hay que correr dos configuraciones del
pipeline sobre la misma pasada, asi que sirve como instrumento de validacion y de diagnostico, no
como criterio en linea. Un detector tendria que decidir con una sola corrida.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el brazo no cambiara nada, esto lo mostraria? SI: todas las tasas darian 0 %.
2. Si el instrumento estuviera muerto? `hacia_donde_se_movio.py` corre el control del control
   contra si mismo, que tiene que dar exactamente 0 movidas.

EL CONFUSOR, controlado. Una fuente fuerte da un cumulo estable, y MIROVA publica las fuertes, asi
que el contraste podria ser magnitud disfrazada. Se controla estratificando por la magnitud QUE VE
EL OPERADOR: si a igual magnitud el contraste desaparece, era magnitud. Medido: NO desaparece.

LIMITES DECLARADOS:
- Ventana 2026-09-01 a 2026-09-20, entera posterior al cambio de regimen de #535 (A104).
- Las etiquetas salen de la referencia de MIROVA congelada, no de nuestras detecciones.
- El tramo de mas de 1 MW tiene n = 3 en positivos: no dice nada por si solo.
- Se mide sobre UN par de configuraciones (control contra sin Test 1). Que la propiedad valga
  para otros pares es SOSPECHA hasta que se mida con otro brazo.

Uso:  python experiments/_s147_pos/estabilidad_del_cumulo.py
"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave, _hav  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

BASE = (ROOT / "experiments" / "_s147_pos" / "experiments" / "_s146_ab_sin_test1"
        / "salidas" / "35521542153")
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
VENTANA = ("2026-09-01", "2026-09-20")
MOVIMIENTO_MIN_KM = 0.5


def tramo(v: float) -> str:
    if v < 0.05:
        return "1 bajo 0,05 MW"
    if v < 0.2:
        return "2 0,05 a 0,2  "
    if v < 1.0:
        return "3 0,2 a 1,0   "
    return "4 sobre 1,0 MW"


def main() -> None:
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
    ctrl = cargar_brazo(BASE / "_s146_ab_control", coords, inner, VENTANA)
    brazo = cargar_brazo(BASE / "_s146_ab_sin_test1", coords, inner, VENTANA)
    bp.etiquetar(ctrl, por_vb, ns, nv)
    bp.etiquetar(brazo, por_vb, ns, nv)
    ib = {clave(r): r for r in brazo}

    tot, mov = Counter(), Counter()
    tot_t, mov_t = Counter(), Counter()
    for c in ctrl:
        b = ib.get(clave(c))
        if b is None or not (c["pub"] and b["pub"]):
            continue
        if None in (c.get("pc_lat"), c.get("pc_lon"), b.get("pc_lat"), b.get("pc_lon")):
            continue
        se_movio = _hav(c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"]) > MOVIMIENTO_MIN_KM
        tot[c["lab"]] += 1
        if se_movio:
            mov[c["lab"]] += 1
        if c["lab"] in ("pos", "neg_limpio"):
            k = (tramo(c.get("disp") or 0), c["lab"])
            tot_t[k] += 1
            if se_movio:
                mov_t[k] += 1

    print(f"ventana {VENTANA[0]} a {VENTANA[1]} | par de configuraciones: control contra sin Test 1")
    print(f"movimiento = el cumulo publicado se corre mas de {MOVIMIENTO_MIN_KM} km\n")
    print(f"{'lo que dice MIROVA':34} {'movidas':>8} {'de':>6} {'tasa':>7}")
    etiquetas = {"pos": "alerto", "neg_limpio": "miro y no vio nada",
                 "far_ref": "vio un foco fuera del volcan", "sin_info": "no dice nada"}
    for lab, nombre in etiquetas.items():
        if tot[lab]:
            print(f"{nombre:34} {mov[lab]:8} {tot[lab]:6} {100 * mov[lab] / tot[lab]:6.1f}%")
    n_tot, n_mov = sum(tot.values()), sum(mov.values())
    print(f"{'TOTAL':34} {n_mov:8} {n_tot:6} {100 * n_mov / n_tot:6.1f}%")

    print("\nCONTROL DEL CONFUSOR: a IGUAL magnitud publicada (una fuente fuerte da un cumulo")
    print("estable, y MIROVA publica las fuertes; si el contraste fuera eso, aca desapareceria)")
    print(f"\n{'magnitud':16} {'MIROVA alerto':>22} {'MIROVA no vio nada':>24}")
    for t in sorted(set(k[0] for k in tot_t)):
        a, b_ = tot_t[(t, "pos")], tot_t[(t, "neg_limpio")]
        ta = f"{100 * mov_t[(t, 'pos')] / a:5.1f}% ({mov_t[(t, 'pos')]:2} de {a:3})" if a else "n/a"
        tb = (f"{100 * mov_t[(t, 'neg_limpio')] / b_:5.1f}% ({mov_t[(t, 'neg_limpio')]:2} de {b_:3})"
              if b_ else "n/a")
        print(f"{t:16} {ta:>22} {tb:>24}")
    print("\nSi el contraste sobrevive la estratificacion, NO es magnitud disfrazada.")


if __name__ == "__main__":
    main()
