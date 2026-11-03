# -*- coding: utf-8 -*-
"""Nulo de `probar_adenda2.py`: mutaciones de una línea del lector de posición, del separador y del generador.

POR QUÉ (S156, A110). Una batería que pasa no dice nada si tampoco falla cuando el código se rompe. Cada mutación es
una copia con UNA línea cambiada y cuenta como atrapada sólo si la batería sale 1 con «FALLAS» (sale 2 si el lector se
cayó, y eso no es atrapar). La identidad tiene que pasar y el control que se cae tiene que salir CAÍDA.
Las copias viven al lado del original (las rutas del lector son relativas a su carpeta) y se borran al terminar cada
una: son temporales que crea y consume este mismo proceso.
Límite declarado: apagar un control (C1 o C2) no lo atrapa ninguna escena, porque con datos sanos el control ya da
verde; esos controles se prueban por las mutaciones que rompen lo que vigilan (L3 y L5 hacen caer C2 o C1).
Uso: python mutar_adenda2.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta temporal>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LEC, SEP, GEN = "leer_posicion_v750b.py", "separar_resultados_v750b.py", "objetivos_supl_v750b.py"
MUT = [
    ("identidad", LEC, None, None, "PASA"),
    ("L1 cercano toma el más lejano", LEC,
     "p = min(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))",
     "p = max(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))", "ATRAPADA"),
    ("L2 pico toma el más débil", LEC, "    p = max(px, key=lambda p: p[4])\n    return float(p[0]), float(p[1])",
     "    p = min(px, key=lambda p: p[4])\n    return float(p[0]), float(p[1])", "ATRAPADA"),
    ("L3 todos los brazos son radiante", LEC, 'if brazo == "radiante" or not rec.get("primary_cluster"):',
     "if True:", "ATRAPADA"),
    ("L4 distancia a MIROVA medida desde el cráter", LEC,
     "dd.append(abs(float(np.hypot(pt[0] - A.C, pt[1] - A.C) * 0.75) - float(ref)))",
     "dd.append(abs(float(np.hypot(pt[0] - ancla(i)[0], pt[1] - ancla(i)[1]) * 0.75) - float(ref)))", "ATRAPADA"),
    ("L5 el nulo del predicado no cambia nada", LEC, '                r["distance_class"] = "far"\n                nulo',
     "                nulo", "ATRAPADA"),
    ("L6 acepta el sin gránulo de otra lista", LEC, 'all(o.get("lab") == "far_ref" for o in supl) and sg_ok)',
     'all(o.get("lab") == "far_ref" for o in supl))', "ATRAPADA"),
    ("L7 las far_ref salen de la lista sellada", LEC, "far = [i for i in oks if i in ids_p]",
     "far = [i for i in oks if i in ids_s]", "ATRAPADA"),
    ("L8 métricas sólo en la ventana T", LEC, 'm = ns["metricas"](x, "TO", canal)', 'm = ns["metricas"](x, "T", canal)',
     "ATRAPADA"),
    ("L9 C4 acepta cualquier analizador", LEC, "c4 = sha_lf(a.analizador) == SHA_ANALIZADOR_LF", "c4 = True",
     "ATRAPADA"),
    ("L10 radio interior exclusivo", LEC, 'rec["distance_class"] = "summit" if d <= inner else "far"',
     'rec["distance_class"] = "summit" if d < inner - 2.0 else "far"', "ATRAPADA"),
    ("S1 separar deja todo en la sellada", SEP, 'sel in (("sellado", [r for r in filas if r["id"] < ID0]),',
     'sel in (("sellado", filas),', "ATRAPADA"),
    ("G1 generador acepta el filtro repetido", GEN, "    if n != 1:", "    if n < 1:", "ATRAPADA"),
    ("G2 generador no cambia el filtro", GEN, 'exec(compile(src.replace(FILTRO_SELLADO, FILTRO_SUPL), str(ruta), "exec"), m.__dict__)',
     'exec(compile(src, str(ruta), "exec"), m.__dict__)', "ATRAPADA"),
    # las que sobrevivían al verificador limpio (VAD2-04, su ver_mutar.py), ahora en el nulo oficial
    ("V3 ancla siempre el centro", LEC, 'return tuple(obj[i].get("pos_crater") or (A.C, A.C))', "return (A.C, A.C)",
     "ATRAPADA"),
    ("V5 sin filtro de dayflag", LEC, 'part[i] == "observada" and res[i].get("dayflag") == 0',
     'part[i] == "observada" and True', "ATRAPADA"),
    ("V6 sólo el canal decide", LEC, 'for canal in ("decide", "tabla"):', 'for canal in ("decide",):', "ATRAPADA"),
    ("V7 P2 contra cercano", LEC, 'ref=f"{c}|radiante")', 'ref=f"{c}|cercano")', "ATRAPADA"),
    ("V8 los cambios cuentan las suplementarias", LEC, 'for i in oks if obj[i]["id"] < ID0 and pub(i, x)',
     "for i in oks if pub(i, x)", "ATRAPADA"),
    ("V9 C3 no exige ids sellados bajos", LEC, "and all(i < ID0 for i in ids_s)", "and True", "ATRAPADA"),
    ("V13 C1 sin exigir casos", LEC, "c1 = n1 > 0 and not dif1", "c1 = not dif1", "ATRAPADA"),
    ("V14 vara 3 sólo B0", LEC, 'for c in ("B0", "B1"):\n            lin = []', 'for c in ("B0",):\n            lin = []',
     "ATRAPADA"),
    ("V18 SIN DATO sin separar las listas", LEC, "SIN DATO {sum(i in ids for i in sin)}", "SIN DATO {len(sin)}",
     "ATRAPADA"),
    ("S2 separar manda la suplementaria a ninguna parte", SEP, '("supl", [r for r in filas if r["id"] >= ID0])',
     '("supl", [])', "ATRAPADA"),
    ("G3 el control de listas siempre igual", GEN, "    return pn == ss, pn, ss", "    return True, pn, ss", "ATRAPADA"),
    ("G5 sin corte de días excluidos", GEN, 'if p["hora_utc"][:10] not in excluidos and p["hora_utc"] < corte]',
     'if p["hora_utc"] < corte]', "ATRAPADA"),
    ("G6 la lista del run pone la suplementaria primero", GEN, "    return list(sellado) + list(far)",
     "    return list(far) + list(sellado)", "ATRAPADA"),
    ("G8 la selección toma far_ref y pos", GEN, 'far = [dict(p) for p in pob if p["lab"] == "far_ref"]',
     'far = [dict(p) for p in pob if p["lab"] in ("far_ref", "pos")]', "ATRAPADA"),
    # las del verificador corto (N1 a N3 y su E4)
    ("N1 K distinto sólo por publicación", LEC, "\n              or abs(vrp_k(i) - (obj[i].get(\"pc_vrp\") or 0)) > 0.001]",
     "]", "ATRAPADA"),
    ("E4 con algún alertado cuenta todas", LEC, "        con = sum(bool(", "        con = len(far) + 0 * sum(bool(",
     "ATRAPADA"),
    ("G10 generar con el control fijo IGUALES", GEN, "    if not igual:\n        faltan", "    if False:\n        faltan",
     "ATRAPADA"),
    ("G11 generar sin la guarda de la carpeta sellada", GEN, "    if dest.resolve() == Path(sellada).resolve():",
     "    if False:", "ATRAPADA"),
    ("G12 generar sin la guarda de salidas previas", GEN, "    if previos:\n", "    if False:\n", "ATRAPADA"),
    ("G13 la población fallida no cuenta como salida previa", GEN, ', "poblacion_supl_CONTROL_FALLIDO.json")', ")",
     "ATRAPADA"),
    ("control que se cae", LEC, "    L = []\n", '    L = []\n    raise RuntimeError("control: el lector se cae")\n', "CAÍDA"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    a = ap.parse_args()
    malas = 0
    for nombre, archivo, viejo, nuevo, espera in MUT:
        src = (AQUI / archivo).read_text(encoding="utf-8")
        if viejo is not None and src.count(viejo) != 1:
            print(f"{nombre}: la línea a mutar aparece {src.count(viejo)} veces, no 1: MUTACIÓN INVÁLIDA")
            malas += 1
            continue
        copia = AQUI / f"_mut_{re.sub(r'[^A-Za-z0-9]+', '_', nombre)}.py"
        copia.write_text(src if viejo is None else src.replace(viejo, nuevo), encoding="utf-8")
        opcion = {LEC: "--lector", SEP: "--separar", GEN: "--generador"}[archivo]
        try:
            r = subprocess.run([sys.executable, str(AQUI / "probar_adenda2.py"), opcion, str(copia),
                                "--evaluador", a.evaluador, "--dest", str(a.dest / copia.stem)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        finally:
            copia.unlink()
        out = r.stdout + r.stderr
        if r.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in out:
            estado = "PASA"
        elif r.returncode == 2 and "CAÍDA DEL LECTOR" in out:
            estado = "CAÍDA"
        elif r.returncode == 1 and "FALLAS" in out:
            estado = "ATRAPADA"
        else:
            estado = f"OTRA (salida {r.returncode})"
        fallas = re.search(r"== PRUEBAS: FALLAS \d+ \(\d+\): (.*)", out)
        print(f"{nombre}: {estado} (se espera {espera})" + (f" | {fallas.group(1)[:160]}" if fallas else ""), flush=True)
        malas += estado != espera
    n_mut = sum(1 for m in MUT if m[4] == "ATRAPADA")
    print(f"== mutaciones: {n_mut} que deben quedar atrapadas; "
          + ("TODAS COMO SE ESPERA, con identidad y control" if not malas else f"{malas} NO COMO SE ESPERA"))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
