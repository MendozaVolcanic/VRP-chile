# -*- coding: utf-8 -*-
"""Mutaciones PROPIAS del verificador sobre el lector, el generador y el separador de la adenda 2 (no son las del autor).
Cada copia vive en verificador/_m/ (no se toca ningun archivo del autor) con una preamble que fija las rutas absolutas;
la bateria del autor (probar_adenda2.py, solo lectura) corre con --lector/--separar/--generador apuntando a la copia.
Estados: ATRAPADA (sale 1 con FALLAS: la bateria lo ve por asercion), CAIDA (sale 2), PASA (la bateria NO lo ve),
OTRA (otro codigo). Pregunta 1: si el codigo estuviera roto, lo veria? Para eso estan las mutaciones; la identidad debe
dar PASA y el control CAIDA, o el arnes no vale. Pregunta 2: instrumento muerto? 'MUTACION INVALIDA' si el texto a
mutar no aparece exactamente una vez."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import ADENDA2, V750B, EV, TMP  # noqa: E402

AQUI = Path(__file__).resolve().parent
M = AQUI / "_m"
M.mkdir(exist_ok=True)
LEC, SEP, GEN = "leer_posicion_v750b.py", "separar_resultados_v750b.py", "objetivos_supl_v750b.py"
RAIZ = V750B.parents[1]

MUT = [
    ("identidad lector", LEC, None, None),
    ("identidad separador", SEP, None, None),
    ("identidad generador", GEN, None, None),
    ("M1 km por celda 1.0 en record_pos", LEC, "d = float(np.hypot(f - ancla[0], c - ancla[1]) * 0.75)",
     "d = float(np.hypot(f - ancla[0], c - ancla[1]) * 1.0)"),
    ("M2 centro de la grilla corrido una celda en la vara 3", LEC,
     "dd.append(abs(float(np.hypot(pt[0] - A.C, pt[1] - A.C) * 0.75) - float(ref)))",
     "dd.append(abs(float(np.hypot(pt[0] - A.C - 1, pt[1] - A.C - 1) * 0.75) - float(ref)))"),
    ("M3 ancla siempre el centro", LEC, 'return tuple(obj[i].get("pos_crater") or (A.C, A.C))', "return (A.C, A.C)"),
    ("M4 el predicado lee la columna 3", LEC, "P = {k: bool(p[4]) for k, p in zip(idx, A.B.correr_node(casos))}",
     "P = {k: bool(p[3]) for k, p in zip(idx, A.B.correr_node(casos))}"),
    ("M5 sin filtro de dayflag", LEC, 'and res[i].get("dayflag") == 0\n', "\n"),
    ("M6 solo el canal decide", LEC, 'for canal in ("decide", "tabla"):', 'for canal in ("decide",):'),
    ("M7 P2 contra cercano", LEC, 'ref=f"{c}|radiante")\n                    camb', 'ref=f"{c}|cercano")\n                    camb'),
    ("M8 cambios cuentan tambien las suplementarias", LEC, 'for i in oks if obj[i]["id"] < ID0 and pub(i, x)',
     "for i in oks if pub(i, x)"),
    ("M9 C3 no exige ids sellados bajos", LEC, "and all(i < ID0 for i in ids_s)", "and True"),
    ("M10 C3 no exige disjuntos", LEC, "and not (ids_s & ids_p)", "and True"),
    ("M11 pico usa la columna de distancia", LEC, "    p = max(px, key=lambda p: p[4])\n    return float(p[0]), float(p[1])",
     "    p = max(px, key=lambda p: p[3])\n    return float(p[0]), float(p[1])"),
    ("M12 centroide radiante con filas y columnas cruzadas", LEC,
     "return float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))",
     "return float(np.mean([b for _, b in cu])), float(np.mean([a for a, _ in cu]))"),
    ("M13 C1 sin exigir casos", LEC, "c1 = n1 > 0 and not dif1", "c1 = not dif1"),
    ("M14 vara 3 solo B0", LEC, 'for c in ("B0", "B1"):\n            lin = []', 'for c in ("B0",):\n            lin = []'),
    ("M15 vara 3 far_ref usa la distancia de la alerta", LEC,
     'ref = o.get("dist_ref") if o["lab"] == "far_ref" else next(', 'ref = None if o["lab"] == "far_ref" else next('),
    ("M16 C2 pasa a summit en vez de far", LEC, '                r["distance_class"] = "far"\n                nulo',
     '                r["distance_class"] = "summit"\n                nulo'),
    ("M17 cercano desempata al reves", LEC, "(np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))",
     "(np.hypot(p[0] - ancla[0], p[1] - ancla[1]), -p[0], -p[1]))"),
    ("M18 la suplementaria cuenta como sellada en el sin dato", LEC,
     'for nombre, ids in (("selladas", ids_s), ("suplementarias", ids_p)):',
     'for nombre, ids in (("selladas", ids_s | ids_p), ("suplementarias", ids_p)):'),
    ("M19 la clase de distancia no se recalcula", LEC, '    rec["distance_class"] = "summit" if d <= inner else "far"\n', "\n"),
    ("M20 sin distancia en el record", LEC, '    rec["primary_cluster"]["centroid_dist_km"] = round(d, 3)\n', "\n"),
    ("S2 separar manda la suplementaria a ninguna parte", SEP, '("supl", [r for r in filas if r["id"] >= ID0])',
     '("supl", [])'),
    ("S3 separar corta en > ID0 (pierde el id 100000)", SEP, '("supl", [r for r in filas if r["id"] >= ID0])',
     '("supl", [r for r in filas if r["id"] > ID0])'),
    ("S4 separar escribe encima de una carpeta no vacia", SEP, "if dest.exists() and any(dest.iterdir()):",
     "if False:"),
    ("G3 el control de listas siempre IGUALES", GEN, "igual = pn == ss", "igual = True"),
    ("G4 ids suplementarios desde 0", GEN, "ID0 = 100000", "ID0 = 0"),
    ("G5 sin corte de dias excluidos", GEN,
     'if p["hora_utc"][:10] not in GS.EXCLUIDOS and p["hora_utc"] < GS.CORTE_SNPP]',
     'if p["hora_utc"] < GS.CORTE_SNPP]'),
    ("G6 la lista del run pone la suplementaria primero", GEN, "run = json.dumps(sellado + far,", "run = json.dumps(far + sellado,"),
    ("G7 las suplementarias entran al subconjunto nativo", GEN, 'p["en_sc"] = False', 'p["en_sc"] = True'),
    ("G8 la seleccion toma far_ref y pos", GEN, 'far = [p for p in pob if p["lab"] == "far_ref"]',
     'far = [p for p in pob if p["lab"] in ("far_ref", "pos")]'),
    ("G9 la distancia sale de cualquier fila", GEN,
     'fp = [f for f in p.get("mirova") or [] if str(f.get("tipo", "")).startswith("FALSO_POSITIVO")]',
     'fp = [f for f in p.get("mirova") or []]'),
    ("control que se cae", LEC, "    L = []\n", '    L = []\n    raise RuntimeError("control")\n'),
]


def preparar(archivo, src):
    if archivo in (LEC, GEN):
        src = src.replace("V750B = AQUI.parent", f"V750B = Path(r'{V750B}')", 1)
    if archivo == GEN:
        src = src.replace("RAIZ = V750B.parents[1]", f"RAIZ = Path(r'{RAIZ}')", 1)
    return src


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sel = sys.argv[1:]
    for n, (nombre, archivo, viejo, nuevo) in enumerate(MUT):
        if sel and not any(s in nombre for s in sel):
            continue
        src = (ADENDA2 / archivo).read_text(encoding="utf-8")
        if viejo is not None and src.count(viejo) != 1:
            print(f"{nombre}: MUTACION INVALIDA (aparece {src.count(viejo)} veces)", flush=True)
            continue
        src = preparar(archivo, src)
        if viejo is not None:
            src = src.replace(viejo, nuevo)
        copia = M / f"m{n:02d}_{archivo}"
        copia.write_text(src, encoding="utf-8")
        opcion = {LEC: "--lector", SEP: "--separar", GEN: "--generador"}[archivo]
        r = subprocess.run([sys.executable, str(ADENDA2 / "probar_adenda2.py"), opcion, str(copia), "--evaluador", str(EV),
                            "--dest", str(TMP / "mut" / copia.stem)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        out = r.stdout + r.stderr
        if r.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in out:
            est = "PASA"
        elif r.returncode == 2 and "CAÍDA DEL LECTOR" in out:
            est = "CAIDA"
        elif r.returncode == 1 and "FALLAS" in out:
            est = "ATRAPADA"
        else:
            est = f"OTRA({r.returncode})"
        f = re.search(r"== PRUEBAS: FALLAS \d+ \(\d+\): (.*)", out)
        print(f"{nombre}: {est}" + (f" | {f.group(1)[:140]}" if f else ""), flush=True)


if __name__ == "__main__":
    main()
