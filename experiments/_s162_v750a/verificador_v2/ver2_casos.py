# -*- coding: utf-8 -*-
"""Segunda vuelta del verificador (V750-A): escenarios propios con el formato de Pob de probar_evaluar_v750a.py.
Uso: python ver2_casos.py --dest <tmp> --evaluador <evaluar_d25.py> [--analizador <copia>] [--solo C1,C2]
No toca nada fuera de --dest. Cada escenario se corre con `correr` de las pruebas del autor (misma clasificación
OK / FALLA / CAÍDA)."""
import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import probar_evaluar_v750a as T  # noqa: E402


def _borde(f):
    return lambda m, k: round(f * m, 3)


def _tope_50000(pb):
    """K de 45.000 MW con t_max tibio: publica; por 1,2 = 54.000 MW cae en el tope de 50.000 de mirovaEqVrp y no
    publica. La diferencia NO la explican los filtros de artefacto (t_max 300 K): el pre-registro dice que esta clase
    «no se puede producir» con el predicado de hoy."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=45000.0, P=None, k_tmax=300.0)


def _frio_y_tibio(pb):
    """Una explicada (9 MW, 270 K) y una sin explicar (45.000 MW, 300 K) en la misma población."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=9.0, P=None, k_tmax=270.0)
    pb.pasada("Villarrica", "2026-07-31 05:40", "neg_limpio", K=45000.0, P=None, k_tmax=300.0)


def _prot_ocr_k_distinto(pb):
    """Protegida SÓLO del OCR (tabla=False) cuyo VRP de K difiere de producción: `protegida` es verdadera, así que
    tiene que cerrar aunque quepa en el 1 %."""
    j = pb.pasada("Villarrica", "2026-08-05 06:40", "pos", K=0.9, P=2.0, mirova_vrp=2.0, tabla=False)
    pb.objs[j]["pc_vrp"] = round(pb.objs[j]["pc_vrp"] + 0.01, 3)


def _t_sin_protegidas_publicadas(pb):
    """En T, ni K ni P publican ninguna protegida: P1 = 0 vacío; la razón de M queda sin protegidas (tiene que ser
    NO CUMPLE por «M razón sin protegidas», no un CUMPLE vacío)."""
    for j, o in enumerate(pb.objs):
        if o["lab"] == "pos" and o["hora_utc"].startswith("2026-04"):
            o["pub_prod"] = False
            o["pc_vrp"] = 0.0
            pb.res[j]["brazos"]["K"] = {"record": T.k_record(None)}
            pb.res[j]["brazos"]["Kgemelo"] = {"record": T.k_record(None)}
            for b in ("P", "Pdef", "O"):
                pb.res[j]["paquete"][b] = T.salida_paquete(None, o["volcan"])


def _k_distinto_y_p_distinto_de_o(pb):
    """La única pasada con K distinto de producción (cabe en el 1 %) es también P distinto de O fuera de la banda.
    Si «sale de todos los brazos», §6.1 no la ve; el código la mira sobre oks0."""
    j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
    pb.objs[j]["pub_prod"] = False
    pb.res[j]["paquete"]["P"] = T.salida_paquete(0.2, pb.objs[j]["volcan"])
    pb.res[j]["paquete"]["O"] = T.salida_paquete(0.2 + 1e-4, pb.objs[j]["volcan"])


def _prot_k_no_p_igual(pb):
    """12 protegidas que K no publica y P publica a la magnitud de MIROVA: entran a la razón y la dejan en 1,0."""
    for n in range(12):
        pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 06:00", "pos", K=None, P=2.0,
                  mirova_vrp=2.0)


def esc_sombra_k_distinto(relleno=0):
    pb = T.esc_sombra()
    for n in range(relleno):
        pb.pasada("Villarrica", f"2026-{11 + n // 28:02d}-{1 + n % 28:02d} 03:00", "neg_limpio", K=None, P=None)
    j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
    pb.objs[j]["pub_prod"] = False
    return pb


def esc_sombra_k_distinto_prot():
    pb = T.esc_sombra()
    for n in range(90):
        pb.pasada("Villarrica", f"2026-{11 + n // 28:02d}-{1 + n % 28:02d} 03:00", "neg_limpio", K=None, P=None)
    j = next(i for i, o in enumerate(pb.objs) if o["protegida"])
    pb.objs[j]["pc_vrp"] = round(pb.objs[j]["pc_vrp"] + 0.01, 3)
    return pb


def _estado_none(pb):
    pb.res[5]["estado"] = None


def _kgeo_sin_record(pb):
    for r in pb.res:
        r["brazos"]["Kgeo"] = {}


def esc_sombra_p_legado():
    """Sombra: el record de P publicado no trae primary_cluster (record legado): el nulo del contador lo perturba."""
    pb = T.esc_sombra()
    for r in pb.res:
        rec = r["brazos"]["P"]["record"]
        if rec.get("primary_cluster"):
            rec.pop("primary_cluster")
    return pb


ESC = {
    # VA-06: datos mal formados que antes hacían caer el analizador
    "C12": dict(pob=lambda: T.base(extra=_estado_none), rc=3,
                tiene=[("   SIN DATO por motivo", ["sin_estado"]), ("== cobertura: INSUFICIENTE", [])]),
    "C13": dict(pob=lambda: T.base(extra=_kgeo_sin_record), rc=0,
                tiene=[("== §6 censo: CUMPLE", []), ("   Kgeo", ["sin datos"])]),
    "C14": dict(pob=lambda: esc_sombra_p_legado(), fase="sombra", rc=0,
                tiene=[("== control nulo del contador", ["OK"]), ("== §6.3 sombra: CUMPLE", [])]),
    # L4, bordes de la banda incluidos (§6.2: «bordes incluidos»)
    # (primera versión esperaba CUMPLE; el comparador d′ de evaluar_d25 da NEUTRO en T con P = 0,9 o 1,1 x MIROVA,
    # que no es lo que se mide aquí: lo que se fija es que la razón 0,900 y 1,100 NO entre a los motivos)
    "C1": dict(pob=lambda: T.base(p_de=_borde(0.9)), rc=0,
               tiene=[("== §6.2 ventana T, canal tabla", ["M razón en protegidas 0.900 (n 10)"]),
                      ("== §6.2 ventana O, canal tabla", ["M razón en protegidas 0.900 (n 11)"])],
               no_contiene=[("== §6 censo:", "M razón"), ("== §6.2 ventana", "no cumple: M razón"),
                            ("== §6.2 ventana", "; M razón")]),
    "C2": dict(pob=lambda: T.base(p_de=_borde(1.1)), rc=0,
               tiene=[("== §6.2 ventana T, canal tabla", ["M razón en protegidas 1.100 (n 10)"]),
                      ("== §6.2 ventana O, canal tabla", ["M razón en protegidas 1.100 (n 11)", "-> cumple"])],
               no_contiene=[("== §6 censo:", "M razón"), ("== §6.2 ventana", "no cumple: M razón"),
                            ("== §6.2 ventana", "; M razón")]),
    # L7: la clase «sin explicar» SÍ se produce con el predicado de hoy (tope de 50.000 MW)
    "C3": dict(pob=lambda: T.base(extra=_tope_50000), rc=3,
               tiene=[("== control placebo K×1,2 (publicación)", ["sin explicar 1", "Lascar 2026-07-31 05:30", "FALLA"]),
                      ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "C9": dict(pob=lambda: T.base(extra=_frio_y_tibio), rc=3,
               tiene=[("== control placebo K×1,2 (publicación)", ["distintas de K 2", "explicadas por los filtros",
                                                                  "Lascar 2026-07-31 05:30", "sin explicar 1",
                                                                  "Villarrica 2026-07-31 05:40", "FALLA"])],
               no_tiene=["== §6 censo:"]),
    # L18: una protegida sólo del OCR con K distinto cierra aunque quepa en el 1 %
    "C4": dict(pob=lambda: T.base(relleno=61, extra=_prot_ocr_k_distinto), rc=3,
               tiene=[("== control K = producción", ["distintas 1 de 111", "Villarrica 2026-08-05 06:40", "FALLA"])],
               no_tiene=["== §6 censo:"]),
    # L18 en la sombra: 1 distinta entre 24 ok (4 %) cierra; entre 114 (0,9 %) no cierra
    "C5": dict(pob=lambda: esc_sombra_k_distinto(), fase="sombra", rc=3,
               tiene=[("== control K = producción", ["distintas 1 de 24", "FALLA"]),
                      ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6.3 sombra:"]),
    "C6": dict(pob=lambda: esc_sombra_k_distinto(90), fase="sombra", rc=0,
               tiene=[("== control K = producción", ["distintas 1 de 114", "OK"]), ("== §6.3 sombra: CUMPLE", [])]),
    "C7": dict(pob=lambda: esc_sombra_k_distinto_prot(), fase="sombra", rc=3,
               tiene=[("== control K = producción", ["distintas 1 de 114", "FALLA"])], no_tiene=["== §6.3 sombra:"]),
    # L4: sin protegidas publicadas en T, la razón no puede «cumplir vacío»
    "C8": dict(pob=lambda: T.base(extra=_t_sin_protegidas_publicadas), rc=0,
               tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: M razón sin protegidas"])], no_tiene=["== §6 censo: CUMPLE"]),
    # L18 y §6.1: la pasada con K distinto «sale de todos los brazos» (texto) pero §6.1 la mira sobre oks0 (código)
    "C10": dict(pob=lambda: T.base(relleno=60, extra=_k_distinto_y_p_distinto_de_o), rc=6,
                tiene=[("== control K = producción", ["distintas 1 de 109", "OK"]),
                       ("== §6.1 equivalencia: NO SE CUMPLE", ["Lascar 2026-04-20"])]),
    # L4, dirección positiva: protegidas que K no publica y P publica bien no empeoran la razón
    "C11": dict(pob=lambda: T.base(extra=_prot_k_no_p_igual), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("== §6.2 ventana O, canal tabla", ["M razón en protegidas 1.000 (n 23)"])]),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--analizador", default=str(AQUI.parent / "evaluar_v750a.py"))
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    sel = [x for x in a.solo.split(",") if x] or list(ESC)
    L, nf, nc = [], 0, 0
    for nom in sel:
        est, det = T.correr(nom, ESC[nom], Path(a.analizador), Path(a.evaluador), a.dest)
        nf += est == "FALLA"
        nc += est == "CAÍDA"
        s = f"{nom} | {est}" + (" | " + " ; ".join(det) if det else "")
        print(s, flush=True)
        L.append(s)
    res = (f"== CASOS V2: CAÍDAS {nc} (fallas {nf}) de {len(sel)}" if nc else
           f"== CASOS V2: FALLAS {nf} de {len(sel)}" if nf else f"== CASOS V2: TODOS COMO SE ESPERA ({len(sel)})")
    print(res)
    L.append(res)
    (a.dest / "casos_v2_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 2 if nc else (1 if nf else 0)


if __name__ == "__main__":
    sys.exit(main())
