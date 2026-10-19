# ¿La decision (c) resuelve la falsa alarma de (i) con evaluacion diaria? Tasa de pasadas Muy Bajo (VIIRS 375, no
# minima, no protegida, con record en los dos lados) por volcan medida en el periodo con sombra (retrospectivo), y
# Monte Carlo: K pierde cada una con la tasa del A/B (SE: 7/161) y la sombra siempre publica; ¿con que
# probabilidad algun volcan dispara (i) en 120 dias? Comparado con la cota y tasa de antes (16/194).
import os, sys, random
from collections import Counter
W, REF = sys.argv[1], sys.argv[2]
sys.path[:0] = [W, os.path.join(W, "scripts")]
import scripts.vigilancia_sombra as vs
vs.aa.CONS = os.path.join(REF, "registro_vrp_consolidado.csv"); vs.aa.OCR = os.path.join(REF, "registro_vrp_ocr.csv")
win = (vs.aa.leer_frontera_k(), "2026-10-19")
filas, prod, sombra = vs.cargar_insumos(win)
pas = vs.pasadas_de_alerta(filas, prod, sombra, win)
d0, d1 = "2026-10-02", "2026-10-18"   # dias con sombra
mb = [p for p in pas if p["sensor"] == "VIIRS375" and not p["protegida"] and not p["minima"]
      and p["prod_pub"] is not None and p["sombra_pub"] is not None and d0 <= p["fecha_utc"][:10] <= d1]
mb_con = [p for p in pas if p["sensor"] == "VIIRS375" and not p["protegida"]
          and p["prod_pub"] is not None and p["sombra_pub"] is not None and d0 <= p["fecha_utc"][:10] <= d1]
dias = 17
por = Counter(p["volcano"] for p in mb); por_con = Counter(p["volcano"] for p in mb_con)
print("Muy Bajo VIIRS375 con los dos lados, sin minimas, del", d0, "al", d1, ":", dict(por))
print("   con minimas (etiqueta original):", dict(por_con))
print("   sombra publica en", sum(1 for p in mb if p["sombra_pub"]), "de", len(mb), "| K calla y sombra publica:",
      sum(1 for p in mb if p["sombra_pub"] and not p["prod_pub"]))
def sim(tasas, p_loss, cota, reps=20000, seed=0):
    rnd = random.Random(seed); fired = 0
    for _ in range(reps):
        f = False
        for v, lam in tasas.items():
            n = sum(1 for _ in range(round(lam * 120)))   # numero esperado, determinista
            k = 0
            for t in range(1, n + 1):
                k += rnd.random() < p_loss
                if k and vs.wilson(k, t)[0] > cota:
                    f = True; break
            if f: break
        fired += f
    return fired / reps
tasas = {v: c / dias for v, c in por.items()}
tasas_con = {v: c / dias for v, c in por_con.items()}
print("P(al menos un INVESTIGAR por (i) en 120 dias) si K pierde como en el A/B:")
print("   regla nueva (sin minimas, p=7/161, cota %.4f): %.3f" % (vs.cota_superior("muy_bajo", "VIIRS375"),
      sim(tasas, 7 / 161, vs.cota_superior("muy_bajo", "VIIRS375"))))
print("   regla vieja (con minimas, p=16/194, cota %.4f): %.3f" % (vs.wilson(16, 194)[1],
      sim(tasas_con, 16 / 194, max(vs.wilson(16, 194)[1], vs.wilson(26, 388)[1]))))
print("   Wilson inferior de 1 de 1 = %.4f, de 1 de 2 = %.4f (cota nueva %.4f)" % (vs.wilson(1, 1)[0], vs.wilson(1, 2)[0],
      vs.cota_superior("muy_bajo", "VIIRS375")))
