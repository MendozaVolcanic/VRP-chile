"""Verificador S159 Chillan MODIS, v1: lee el jsonl del probe y recalcula por cuenta propia
sigma-distancia, rama que gobierna, compuerta y todos los pixeles <=5 km (no solo el 'mejor').
Pregunta 1: si el Test 2 estuviera roto (p.ej. umbral mal armado), lo veria? Si: recalculo el umbral
desde mu y sd guardados y lo comparo con thr_dnti por pixel. Pregunta 2: instrumento muerto -> los
campos vendrian None y el script lo imprime como SIN DATO."""
import json, sys
p = sys.argv[1]
for line in open(p, encoding="utf-8"):
    fila = json.loads(line)
    P = fila.get("P") or {}
    if not P.get("pixeles"):
        print(fila["tag"], "SIN DATO", fila.get("error")); continue
    mu, sd, tbg = P["mu_dnti"], P["sd_dnti"], P["t_bg"]
    mue, sde = P["mu_deti"], P["sd_deti"]
    thr_rec = max(0.003, mu + 5 * sd); thre_rec = max(0.003, mue + 5 * sde)
    print(f"\n{fila['tag']} {fila['granulo']} t_bg={tbg:.2f} mu={mu:.5f} sd={sd:.5f} mu+5sd={mu+5*sd:.5f} C1gob={0.003>mu+5*sd} | "
          f"deti mu={mue:.5f} sd={sde:.5f} thr={thre_rec:.5f} | btmir_anillo_med(vol)={P.get('btmir_anillo_mediana')} bt31_anillo={P.get('bt31_anillo_mediana')}")
    for q in P["pixeles"]:
        if q["d_km"] > 5.0: continue
        z = (q["dnti"] - mu) / sd if q["dnti"] is not None else None
        ok_thr = abs(q["thr_dnti"] - thr_rec) < 1e-9 if q.get("thr_dnti") is not None else None
        print(f"  d={q['d_km']:.2f} i={q['i']} j={q['j']} btmir={q['btmir']:.2f} bt31={q['bt31']:.2f} mir-tir={q['btmir']-q['bt31']:+.2f} "
              f"dNTI={q['dnti']:.5f} z={z:+.2f} thr={q['thr_dnti']:.5f}(recalc ok {ok_thr}) dETI={q['deti']:.5f}/{q['thr_deti']:.5f} "
              f"p2={q['pasa2']} p3={q['pasa3']} gate={q['pasa_compuerta']} bt-tbg={q['btmir']-tbg:+.2f} hot={q['hot']} F1={q['F1']} F2={q['F2']} F3={q['F3']} "
              f"sp={q.get('sp_out')} pool={q['en_pool_bg']} cumbre={q['cumbre']}")
