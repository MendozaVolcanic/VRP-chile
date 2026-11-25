"""Variante post hoc T+ (ADENDA_POSTHOC.md): trasplante sólo del exceso positivo de Chillán, escalas 1, 3, 10 y 30.
Escribe resultados_posthoc.jsonl y umbrales_posthoc.json."""
import json
import time
from concurrent.futures import ProcessPoolExecutor

import comun as C
import medir as M

ESCALAS = (1, 3, 10, 30)


def parche_positivo():
    return {k: (max(a, 0.0), max(b, 0.0)) for k, (a, b) in M.parche_fuente().items()}


def por_escena(esc):
    t0 = time.time()
    E = C.Escena(esc)
    par = parche_positivo()
    crat = (int(round(E.pos[0])), int(round(E.pos[1])))
    brazos = {"T-sin": (E.m13g, E.m15g)}
    for s in ESCALAS:
        brazos[f"T+-con-{s}"] = M.aplicar_parche(E.m13g, E.m15g, par, crat, s)
    regs, umb = M.correr_serie(E, "T+", brazos, crat, "T-sin")
    return esc["clave"], regs, umb, time.time() - t0


def main():
    C.utf8()
    escs = [e for e in C.escenas() if e["clave"] != M.CLAVE_FUENTE]
    todos, umbs = [], {}
    with ProcessPoolExecutor(max_workers=5) as ex:
        for clave, regs, umb, seg in ex.map(por_escena, escs):
            print(f"{clave}: {len(regs)} registros en {seg:.0f} s", flush=True)
            todos += regs
            umbs[clave] = {"T+": umb}
    with open(C.AQUI / "resultados_posthoc.jsonl", "w", encoding="utf-8", newline="") as fh:
        for r in todos:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (C.AQUI / "umbrales_posthoc.json").write_text(json.dumps(umbs, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
