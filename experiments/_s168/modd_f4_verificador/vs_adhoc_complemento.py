# -*- coding: utf-8 -*-
"""Verificador S168: mutaciones a medida (reglas/constantes que el medidor NO muta) contra la bateria. Primero un
subconjunto de escenarios relacionados; si alguno falla por aserción, ATRAPADA (la bateria entera lo contiene).
Las que sobreviven al subconjunto se re-corren con la bateria entera (vs_adhoc_completa.py)."""
import os, sys, tempfile, json
from pathlib import Path
F = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/elated-bell-62d203/experiments/_s166_modd_f4")
sys.path.insert(0, str(F)); os.environ["F4_RAIZ"] = str(F.parents[1])
import mutar_evaluar_f4 as M
import probar_evaluar_f4 as P
AD = [
 ("A1_N_GRILLAS_CENSO_5322", "N_GRILLAS_CENSO = 5321 ", "N_GRILLAS_CENSO = 5322 "),
 ("A2_k_prod_sin_distinto", "ok = not sin_campo and not sin_pub and not sin_explicar and not distinto",
                            "ok = not sin_campo and not sin_pub and not sin_explicar"),
 ("A3_posicion_sin_n", '"OK" if n and not malas else "INDECIDIBLE", "n_con_alertados"', '"OK" if not malas else "INDECIDIBLE", "n_con_alertados"'),
 ("A4_identidad_sin_bool_con_grilla", "n_pob == n_grillas_censo and bool(con_grilla) and not faltan",
                                     "n_pob == n_grillas_censo and not faltan"),
 ("A5_control_predicado_siempre_ok", '"OK" if r == [1, 0] else "INDECIDIBLE", "publica"', '"OK", "publica"'),
 ("A6_contador_sin_no_pasan", "ok = not siguen and len(sel) == N_INYECTAR and not no_pasan and", "ok = not siguen and len(sel) == N_INYECTAR and"),
 ("A7_externos_sin_procedencia", '"manifiesto", "procedencia", "predicado")', '"manifiesto", "predicado")'),
 ("A8_chillan_empates_como_pares", "(empates if db == dk else pares).append(par)", "pares.append(par)"),
 ("A9_p1b_contraria_decide", "        elif _mag(f, \"K\") < CORTE_MW <= _mag(f, b):\n            sube.append(fila)", "        elif _mag(f, \"K\") < CORTE_MW <= _mag(f, b):\n            baja.append(fila)"),
 ("A10_rojo_e_acepta_sin_medir", 'if cob["estado"] == "OK" or cob["sin_pasada_nuestra_no_medida"]:', 'if cob["estado"] == "OK":'),
]
SUB = "E10,E11,E12,E17,E18,E29,E33,E41,E42,E49,E51,E55,E59,E60,E58,E50,E52,E61,E43,E47,E27,E28,E37,E24,E25,E26,E15,E45,E46"
only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
res = {}
for nombre, viejo, nuevo in AD:
    if only and nombre.split("_")[0] not in only:
        continue
    n = M.FUENTE.count(viejo)
    if n != 1:
        print(nombre, "NO APLICA", n, flush=True); res[nombre] = "NO APLICA"; continue
    ruta = Path(tempfile.mkdtemp(prefix="vs_")) / "ev_mut.py"; ruta.write_text(M.FUENTE.replace(viejo, nuevo), encoding="utf-8")
    P.EV = P.cargar(str(ruta))
    cae, aser, ok = [], [], []
    for e in P.ESCENARIOS:
        if e.__name__.split("_")[0] in SUB.split(","):
            continue
        P._ID[0] = 0
        try:
            e(); ok.append(e.__name__.split("_")[0])
        except AssertionError:
            aser.append(e.__name__.split("_")[0])
        except Exception as x:
            cae.append(e.__name__.split("_")[0] + ":" + type(x).__name__)
    clase = "ATRAPADA" if aser else ("CAE" if cae else "VIVA_EN_TODA_LA_BATERIA")
    print(nombre, clase, "| aserción:", aser, "| caen:", cae, flush=True)
    res[nombre] = clase
json.dump(res, open("vs_adhoc_complemento.json", "w"), indent=1)
