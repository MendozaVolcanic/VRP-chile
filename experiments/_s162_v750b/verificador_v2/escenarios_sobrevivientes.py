# -*- coding: utf-8 -*-
"""VB2: escenarios que MATAN a las mutaciones que la bateria v2 del autor deja vivas (A110).

Preguntas del instrumento. (1) Si la decision o la compuerta estuvieran rotas como dice cada mutacion, ¿este escenario lo
veria? Cada escenario se corre contra el analizador original y contra el mutado; la mutacion «cae» si la firma
(compuerta, rc, elegibles, ROI, P2) cambia. Control positivo: la mutacion M0 (rompe la sintaxis) tiene que caer en todos los
escenarios; control de determinismo: el original contra si mismo tiene que dar IGUAL. (2) Si el analizador no corriera, la
firma queda con None y el escenario se marca SIN DATO, no «cae».
Reusa el generador de pasadas de escenarios_v2.py (exec de su cabecera).
Uso: python escenarios_sobrevivientes.py --arbol <arbol> --dest <tmp>
"""
from __future__ import annotations
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
src = (AQUI / "escenarios_v2.py").read_text(encoding="utf-8").split("# C0 control positivo")[0]
exec(compile(src, "escenarios_v2_cabecera", "exec"), globals())     # define a, A, Pob, todos, base, correr, ANALIZAR...

ORIG = ANALIZAR
MUTDIR = ORIG.parent
texto = ORIG.read_text(encoding="utf-8")
MUT = {
    "M0 sintaxis": ('FRONTERA_OCR = "2026-06-13"', 'FRONTERA_OCR = "2026-06-13" +'),
    "M2 sin filtro de tabla en 6.2": ('\n             and ver[(b, "TO", "tabla")][1] in ("GANA", "EMPATE", "SIN SUSTRATO")]', ']'),
    "M3 6.3 admite BLOQUEA": ('("EMPATE", "SIN SUSTRATO"))]', '("EMPATE", "SIN SUSTRATO", "BLOQUEA"))]'),
    "M5 frontera OCR 07-01": ('FRONTERA_OCR = "2026-06-13"', 'FRONTERA_OCR = "2026-07-01"'),
    "M8 ancla = centro": ('return tuple(obj[i].get("pos_crater") or (C, C))', 'return (C, C)'),
    "M9 cobertura ignora protegidas SIN DATO": ('and not prot_sin\n', '\n'),
    "M10 compuerta ignora K = produccion": ('c_nulo == 0 and k_ok and cob_ok', 'c_nulo == 0 and cob_ok'),
    "M13 tope SIN DATO 50 %": ('MAX_SIN_DATO = 0.02', 'MAX_SIN_DATO = 0.5'),
    "M16 bloque = solo la noche": ('sumas[(o["hora_utc"][:10], o["volcan"])] += c', 'sumas[o["hora_utc"][:10]] += c'),
    "M18 K distinta no sale de los brazos": ('oks = [i for i in oks if i not in set(k_dist)]', 'pass'),
    "M19 desempate 6.2 por MAYOR E": ('elegido = min(ganan, key=lambda b: ver[(b, "TO", "decide")][2])',
                                       'elegido = max(ganan, key=lambda b: ver[(b, "TO", "decide")][2])'),
    "M21 6.2 con canal todo": ('ver[(b, "TO", "decide")][1] == "GANA"', 'ver[(b, "TO", "todo")][1] == "GANA"'),
}


def firma(nombre, p, analizador):
    global ANALIZAR
    ANALIZAR = analizador
    nombre = re.sub(r"[^A-Za-z0-9_]", "_", nombre)
    a.dest.mkdir(parents=True, exist_ok=True)
    r = correr(nombre, p)
    ANALIZAR = ORIG
    if r["roi"] is None and r["elegibles"] is None and r["rc"] not in (0, 3):
        return ("SIN DATO", r["rc"])
    return (r["rc"], r["compuerta"], r["elegibles"], r["roi"], tuple(sorted(r["p2_decide"].items())),
            tuple(sorted(r["p2_tabla"].items())))


def PUBT(f, c):
    return {"motivo_vacio": None, "n_abs": 0, "n_p1": 1, "n_p2": 0, "npix": 1, "vrp_mw": 0.5, "pixeles": [[f, c, 2, 0.0, 0.9]]}


def esc():
    out = {}
    # S2: B2 GANA con el canal que decide (14 bajas solo-OCR que B1 no publica) pero PIERDE con la tabla sola (6 negativos).
    p = base()
    for n in range(6):
        p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True})
    for n in range(14):
        p.pasada("Lascar", f"2026-09-{16 + n:02d} 05:00", "pos",
                 {**todos(), "B0": False, "B1": False, "B3": False, "B5": False, "B2": True}, tabla=False, ocr_vrp=0.4)
    for n in range(10):
        p.pasada("Tupungatito", f"2026-09-{16 + n:02d} 05:10", "pos",
                 {**todos(), "B0": False, "B1": False, "B3": False, "B5": False, "B2": True}, tabla=False, ocr_vrp=0.4)
    out["S2 B2 gana con todo y pierde con la tabla"] = (p, ["M2 sin filtro de tabla en 6.2", "M21 6.2 con canal todo"])
    # S3: B2 y B0 BLOQUEAN (6 de 8 bloques adversos, neto +4); B5 = B1.
    p = base()
    for n in range(6):
        p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True, "B0": True})
    for n in range(2):
        p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B1": True, "B3": True,
                                                                         "B5": True})
    out["S3 B2 y B4 BLOQUEAN"] = (p, ["M3 6.3 admite BLOQUEA"])
    # S5: protegida solo-OCR el 2026-06-13 00:10 (O): B2 no la publica -> B2 pierde una protegida en O.
    p = base()
    p.pasada("Lascar", "2026-06-13 00:10", "pos", {**todos(), "B2": False}, vrp_mirova=0.6, ocr_vrp=1.3)
    out["S5 protegida solo-OCR en O (2026-06-13 00:10)"] = (p, ["M5 frontera OCR 07-01"])
    # S8: Tupungatito, cumulo a (22, 28): lejos del centro (9,06 km, inner 7) pero a 4,0 km del crater (27, 30).
    p = Pob()
    for b_ in ("K",):
        pass
    i0 = len(p.objs)
    p.pasada("Tupungatito", "2026-07-10 05:00", "pos", todos(), vrp_mirova=2.0)
    p.res[-1]["oraculo"] = {b: PUBT(22, 28) for b in BR}
    for n in range(4):
        p.pasada("Lascar", f"2026-07-{15 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
    p.pasada("PuyehueCordonCaulle", "2026-09-01 05:00", "pos", {**todos(), "B0": False, "B5": False}, vrp_mirova=1.2)
    out["S8 cumulo cerca del crater y lejos del centro"] = (p, ["M8 ancla = centro"])
    # S9: 1 protegida SIN DATO de 100 (1 %): la regla exige que ninguna protegida quede sin dato.
    p = base(n_neg=40)
    p.pasada("Lascar", "2026-07-29 05:00", "pos", todos(), vrp_mirova=2.0)
    p.res[-1]["estado"] = "error_K"
    out["S9 una protegida SIN DATO de ~100"] = (p, ["M9 cobertura ignora protegidas SIN DATO"])
    # S13: 3 negativos SIN DATO de 100 (3 % > 2 %), ninguna protegida.
    p = base(n_neg=40)
    for n in range(3):
        p.pasada("Lascar", f"2026-07-{27 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
        p.res[-1]["estado"] = "sin_granulo"
        p.res[-1].pop("oraculo")
    out["S13 3 % SIN DATO sin protegidas"] = (p, ["M13 tope SIN DATO 50 %"])
    # S10: K distinto de produccion en 3 de ~100 pasadas no protegidas (3 % > 1 %).
    p = base(n_neg=40)
    for n in range(3):
        p.pasada("Lascar", f"2026-07-{27 + n:02d} 05:00", "neg_limpio", {**todos(b=False), "K": True}, k_prod=False)
    out["S10 K distinto en 3 % de las pasadas"] = (p, ["M10 compuerta ignora K = produccion"])
    # S16: dos volcanes la misma noche con contribuciones opuestas de B2 (4 noches): bloques (noche, volcan) = 8, neto 0.
    p = base()
    for n in range(4):
        p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True})
        p.pasada("Tupungatito", f"2026-09-{10 + n:02d} 05:10", "pos", {**todos(), "B2": True, "B1": False, "B0": True,
                                                                       "B3": False, "B5": False}, vrp_mirova=0.4)
    out["S16 dos volcanes la misma noche"] = (p, ["M16 bloque = solo la noche"])
    # S18: una pasada con K distinto (no protegida, <1 % de 160) donde B2 publica un negativo que B1 no.
    p = base(n_neg=60)
    p.pasada("Lascar", "2026-09-30 05:00", "neg_limpio", {**todos(b=False), "K": True, "B2": True, "B0": True}, k_prod=False)
    out["S18 K distinta en 1 pasada donde B2 se equivoca"] = (p, ["M18 K distinta no sale de los brazos"])
    # S19: B2 y B3 GANAN; B3 con menor E (B2 ademas pierde una baja).
    p = base()
    for n in range(8):
        p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B1": True, "B0": True,
                                                                         "B5": True})
    p.pasada("Lascar", "2026-09-25 05:00", "pos", {**todos(), "B2": False}, vrp_mirova=0.4)
    out["S19 dos ganadores, menor E"] = (p, ["M19 desempate 6.2 por MAYOR E"])
    return out


if __name__ == "__main__":
    d = a.dest
    espejo = MUTDIR / "analizar_v750b_mut.py"
    resultado = {}
    for nom, (p, muts) in esc().items():
        base_f = firma("o_" + nom.split()[0], p, ORIG)
        base_f2 = firma("o2_" + nom.split()[0], p, ORIG)
        print(f"\n== {nom}\n   original: rc={base_f[0]} compuerta={base_f[1] if len(base_f) > 1 else None} "
              f"elegibles={base_f[2] if len(base_f) > 2 else None} ROI={base_f[3] if len(base_f) > 3 else None}"
              f" | determinismo: {'IGUAL' if base_f == base_f2 else 'DISTINTO'}")
        print(f"   P2 decide {dict(base_f[4]) if len(base_f) > 4 else None}\n   P2 tabla  {dict(base_f[5]) if len(base_f) > 5 else None}")
        for m in ["M0 sintaxis"] + muts:
            v, nv = MUT[m]
            assert texto.count(v) == 1, (m, texto.count(v))
            espejo.write_text(texto.replace(v, nv), encoding="utf-8")
            f_m = firma("m_" + nom.split()[0] + m.split()[0], p, espejo)
            est = "SIN DATO" if f_m[0] == "SIN DATO" and m != "M0 sintaxis" else ("CAE" if f_m != base_f else "SOBREVIVE")
            resultado[(nom, m)] = est
            print(f"   {m}: {est}  (rc={f_m[0]}, ROI={f_m[3] if len(f_m) > 3 else None}, "
                  f"elegibles={f_m[2] if len(f_m) > 2 else None})", flush=True)
    espejo.unlink()
    print("\nresumen (sin contar M0):", {k: sum(1 for (n, m), e in resultado.items() if e == k and not m.startswith('M0'))
                                       for k in ("CAE", "SOBREVIVE", "SIN DATO")})
