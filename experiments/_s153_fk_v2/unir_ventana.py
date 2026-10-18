"""Une dos intentos de un A/B por brazo y volcán con unir_intentos.unir (S153, regla de adopción de K, §3).

POR QUÉ: la regla aprobada (#848) fija el instrumento en el commit 2766c198 (merge de #847); V1 y V2a se re-unen con
ese mismo `unir_intentos.py` antes de evaluar V2, y la unión se compara byte a byte con la anterior.
Uso: python unir_ventana.py <raiz_intento_a> <raiz_intento_b> <salida> [<union_anterior>]
"""
import hashlib, importlib.util, json, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("unir_intentos", RAIZ / "experiments" / "_s151_ab_diurno" / "unir_intentos.py")
ui = importlib.util.module_from_spec(spec); spec.loader.exec_module(ui)


def brazos(raiz):
    out = {}
    for f in Path(raiz).rglob("*.json"):
        if f.parent.name.startswith("_") and not f.name.startswith("cobertura"):
            out.setdefault(f.parent.name, {})[f.stem] = f
    return out


def main(a, b, salida, anterior=None):
    A, B = brazos(a), brazos(b)
    salida = Path(salida)
    n_dist = 0
    for arm in sorted(set(A) | set(B)):
        (salida / arm).mkdir(parents=True, exist_ok=True)
        for v in sorted(set(A.get(arm, {})) | set(B.get(arm, {}))):
            fa, fb = A.get(arm, {}).get(v), B.get(arm, {}).get(v)
            dst = salida / arm / (v + ".json")
            if fa and fb:
                docs = [json.load(open(fa, encoding="utf-8")), json.load(open(fb, encoding="utf-8"))]
                res, inf = ui.unir(docs, v)
                if not inf["ok"]:
                    n_dist += 1
                    print("NO SE UNE %s %s: %d distintos" % (arm, v, len(inf["distintos"])))
                    continue
                json.dump(res, open(dst, "w", encoding="utf-8"))
                print("%s %s: %s %s" % (arm, v, inf["modo"], inf["estados"]))
            else:
                shutil.copyfile(fa or fb, dst)
                print("%s %s: sólo en un intento" % (arm, v))
    if anterior:
        P = brazos(anterior); S = brazos(salida)
        h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        iguales = sum(1 for arm in S for v in S[arm] if P.get(arm, {}).get(v) and h(P[arm][v]) == h(S[arm][v]))
        total = sum(len(x) for x in S.values())
        print("byte a byte iguales a la unión anterior: %d de %d" % (iguales, total))
    print("NO UNIDOS: %d" % n_dist)


if __name__ == "__main__":
    main(*sys.argv[1:])
