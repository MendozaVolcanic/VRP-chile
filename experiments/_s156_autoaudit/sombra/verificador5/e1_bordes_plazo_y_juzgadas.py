"""Verificador 5 de S156: casos borde del plazo pasada por pasada (F1) y de las juzgadas (F2), llamando a
disparadores() del worktree de solo lectura. Uso: python e1_bordes_plazo_y_juzgadas.py <raiz_worktree>"""
import sys
from pathlib import Path

raiz = Path(sys.argv[1])
sys.path.insert(0, str(raiz))
sys.path.insert(0, str(raiz / "scripts"))
import scripts.vigilancia_sombra as vs  # noqa: E402

ADOP = "2026-10-18 09:57:30"


def P(vol, b, instante, protegida=True, prod=False, sombra=True, minima=False):
    return {"volcano": vol, "sensor": b, "fecha_utc": instante[:16], "instante_utc": instante,
            "vrp_mirova_mw": 2.0 if protegida else 0.3, "protegida": protegida, "minima": minima,
            "referencia_sospechosa": False, "prod_pub": prod, "sombra_pub": sombra}


def D(pas, hoy, juz=None):
    d = vs.disparadores(list(pas), [], hoy=hoy, adopcion=ADOP, juzgadas=juz or {})
    return d


def resumen(d):
    return (d["veredicto"], [(p["volcano"], p["fecha_utc"]) for p in d["reversion"]],
            [(p["volcano"], p["fecha_utc"]) for p in d["fuera_de_plazo"]], d["duracion"]["protegidas_vistas_en_sombra"])


# 28 protegidas vistas que ambos publican (no son candidatas)
base = [P("Lascar", "VIIRS375", f"2026-10-{19 + i // 10:02d} 0{i % 10}:00:00", prod=True) for i in range(28)]

print("P1 empate de instante en el borde 29/30 (dos candidatas del mismo granulo, volcanes distintos)")
emp = [P("Villarrica", "VIIRS375", "2026-10-25 06:00:00"), P("Llaima", "VIIRS375", "2026-10-25 06:00:00")]
print("   ", resumen(D(base + emp, "2026-10-26")))

print("P2 fila tardia de la referencia con instante ANTERIOR: la candidata 29.a pasa a ser la 30.a")
cand = [P("Villarrica", "MODIS", "2026-10-25 07:20:00")]
print("    dia 1:", resumen(D(base + cand, "2026-10-26")))
tardia = [P("Isluga", "VIIRS750", "2026-10-20 05:00:00", prod=True)]
print("    dia 2 (llega una protegida anterior):", resumen(D(base + tardia + cand, "2026-10-27")))
print("    dia 3 (el consolidado pierde dos filas):", resumen(D(base[2:] + tardia + cand, "2026-10-28")))

print("P3 la sombra llega tarde a una pasada anterior (sombra_pub None -> True)")
tarde_none = [P("Isluga", "VIIRS750", "2026-10-20 05:00:00", prod=True, sombra=None)]
tarde_ok = [P("Isluga", "VIIRS750", "2026-10-20 05:00:00", prod=True, sombra=False)]
print("    sombra sin record:", resumen(D(base + tarde_none + cand, "2026-10-26")))
print("    sombra con record:", resumen(D(base + tarde_ok + cand, "2026-10-27")))

print("P4 borde del vencimiento (adopcion 2026-10-18 09:57:30, +120 d = 2027-02-15 09:57:30)")
for inst in ("2027-02-14 23:59:59", "2027-02-15 00:00:00", "2027-02-15 05:00:00", "2027-02-15 09:57:29",
             "2027-02-15 09:57:30"):
    print("   ", inst, resumen(D([P("Villarrica", "MODIS", inst)], "2027-02-16"))[:3])

print("P5 protegida sin record de produccion (prod_pub None) cuenta como vista; sin record de sombra, no")
x = [P("Lascar", "MODIS", "2026-10-20 07:00:00", prod=None), P("Lascar", "MODIS", "2026-10-21 07:00:00", sombra=None)]
print("   ", resumen(D(x, "2026-10-22")))

print("P6 juzgadas en tres noches seguidas: INVESTIGAR por persistencia, para siempre")
tres = [P("Villarrica", "MODIS", f"2026-10-2{d} 07:20:00") for d in (2, 3, 4)]
juz = {vs._clave(p): {"decision": "no revertir"} for p in tres}
for hoy in ("2026-10-25", "2026-12-31", "2027-06-01", "2028-01-01"):
    d = D(tres, hoy, juz)
    print("   ", hoy, d["veredicto"], d["persistencia"])
print("    y sin juzgar, una sola racha de 3 Muy Bajo (no protegidas) tambien queda para siempre:")
mb = [P("Villarrica", "VIIRS375", f"2026-10-2{d} 07:20:00", protegida=False) for d in (2, 3, 4)]
for hoy in ("2026-10-25", "2028-01-01"):
    print("   ", hoy, D(mb, hoy)["veredicto"])

print("P7 candidata juzgada fuera de plazo: no dispara FUERA (codigo actual)")
fp = [P("Villarrica", "MODIS", "2027-03-01 07:20:00")]
print("   ", resumen(D(fp, "2027-03-02", {vs._clave(fp[0]): {"decision": "x"}})))

print("P8 reversion y fuera de plazo en la misma corrida: gana REVERSION (prioridad sin prueba)")
both = base + [P("Villarrica", "MODIS", "2026-10-25 07:20:00"), P("Llaima", "MODIS", "2026-10-26 07:20:00")]
print("   ", resumen(D(both, "2026-10-27")))

print("P9 la juzgada ocupa un lugar en las 29 (cuenta en el orden): la 30.a por eso queda fuera")
j = base + [P("Chaiten", "MODIS", "2026-10-24 07:20:00"), P("Villarrica", "MODIS", "2026-10-25 07:20:00")]
print("   ", resumen(D(j, "2026-10-26", {vs._clave(j[28]): {"decision": "x"}})))
