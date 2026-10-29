# -*- coding: utf-8 -*-
"""Segunda vuelta del verificador: escenarios PROPIOS contra el evaluar_f4.py actual (el del arbol, sha256 7b5bf045...).
Importa el mundo sintetico de probar_evaluar_f4.py (no lo copia). Uso: python escenarios_2v.py [T1,T2,...]
No modifica ningun archivo del repo."""
import copy, json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
F4 = AQUI.parents[1]
sys.path.insert(0, str(F4))
import probar_evaluar_f4 as P

P.EV = P.cargar(str(F4 / "evaluar_f4.py"))
EV = P.EV
F, mundo, dia, VOLS, correr, g, ident_ok = P.F, P.mundo, P.dia, P.VOLS, P.correr, P.g, P.ident_ok


def resumen(r):
    b = r["brazos"]
    return {"veredicto": r["veredicto"], "posicion": r["posicion_elegida"], "motivo": r["posicion_motivo"],
            "P1": {k: b[k]["p1"]["estado"] for k in b},
            "P2": {k: (b[k]["p2"]["estado"], b[k]["p2"]["neto"], b[k]["p2"]["B"]) for k in b},
            "otra_pos_publica": r["protegidas_que_otra_posicion_publica"],
            "e_excluido": bool(r["e_excluido"]),
            "rojos": [k for k, c in r["controles"].items() if (c if isinstance(c, str) else c.get("estado")) != "OK"]}


def mostrar(nombre, r, extra=""):
    print(nombre, json.dumps(resumen(r), ensure_ascii=False, default=str), extra)


# ---------------------------------------------------------------- VF4-01
def T1a_S1_pico_pierde_protegida_de_V():
    f = mundo()
    for i in range(6):
        f.append(F(VOLS[i % 5], dia(100 + i) + " 05:00", "neg_limpio", v=0.2,
                   vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}))
    f.append(F("NevadosDeChillan", dia(120) + " 07:20", "protegida", k=None, v=1.5, mir=1.6, z=58.0,
               vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}))
    r = correr(f)
    mostrar("T1a", r, "| P1 V-pico vs V: %s" % r["brazos"]["V-pico"]["p1_vs_V"]["estado"])


def T1b_pico_pierde_protegida_de_V_solo_ocr():
    """La protegida que V-pico pierde es solo OCR: no quita elegibilidad (por diseno); el veredicto tiene que ir a DECIDE."""
    f = mundo()
    for i in range(6):
        f.append(F(VOLS[i % 5], dia(100 + i) + " 05:00", "neg_limpio", v=0.2,
                   vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}))
    f.append(F("NevadosDeChillan", dia(120) + " 07:20", "protegida", k=None, v=1.5, mir=1.6, z=58.0,
               vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}, solo_ocr=True))
    r = correr(f)
    mostrar("T1b", r)


def T1c_doc_dice_de_la_tabla_codigo_incluye_ocr():
    """Doc 6 bis: 'si alguna protegida DE LA TABLA la publica otra regla...'. Codigo: lista tambien las solo OCR."""
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", v=1.5, mir=1.6, solo_ocr=True,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0})]
    r = correr(f)
    mostrar("T1c", r)


def T1d_recupera_protegida_sin_credito():
    f = mundo() + [F("Lascar", dia(120) + " 03:00", "protegida", k=None, v=2.0, mir=2.1,
                     vd={"radiante": 9.0, "cercano": 0.5, "pico": 9.0})]
    r = correr(f)
    mostrar("T1d", r)


# ---------------------------------------------------------------- VF4-02 y nuevo
def T2a_identidad_motivo_sellado_con_grilla():
    """Una pasada con grilla del censo que el runner marca 'volcan_fuera_del_granulo' sale de con_grilla y del
    denominador: la identidad (y la cobertura) quedan en OK sin haberla medido."""
    f = mundo()
    n = sum(1 for x in f if x["grilla_censo"])
    for x in f[:10]:
        x["motivo"] = "volcan_fuera_del_granulo"
    idn = ident_ok(f)
    for x in f[:10]:
        idn.pop((x["vol"], x["dt"]), None)               # identidad_f4.py tampoco la mide (no hay V del runner)
    r = correr(f, ident=idn, n_grillas=n)
    c = r["controles"]["identidad"]
    mostrar("T2a", r, "| identidad %s n_pob %s n_con_grilla %s faltan %s" % (c["estado"], c["n_grillas_en_poblacion"],
                                                                          c["n_con_grilla"], c["n_faltan"]))
    f = mundo()
    for x in f[:10]:
        x["motivo"] = "escena_invalida"
    idn = ident_ok(f)
    for x in f[:10]:
        idn.pop((x["vol"], x["dt"]), None)
    r = correr(f, ident=idn, n_grillas=n)
    mostrar("T2a'", r, "| identidad %s (escena_invalida)" % r["controles"]["identidad"]["estado"])


def T2b_n_pob_cuenta_filas_no_poblacion():
    """n_pob sale de las filas del runner (merge de main), no de poblacion_f4.json: una fila de mas con grilla_censo
    (aunque sea repetida) lo cambia; una fila de menos tambien. Solo informativo."""
    f = mundo()
    n = sum(1 for x in f if x["grilla_censo"])
    r = correr(f + [copy.deepcopy(f[0])], n_grillas=n)
    c = r["controles"]
    print("T2b repetida:", c["identidad"]["n_grillas_en_poblacion"], c["identidad"]["estado"], "| cobertura", c["cobertura"]["estado"])


# ---------------------------------------------------------------- VF4-03 y familia
def T3a_k_difiere_none():
    f = mundo()
    for x in f:
        x["k_difiere_de_guardado"] = None             # 'no se comparo' escrito como None
    r = correr(f)
    mostrar("T3a (k_difiere=None en TODAS las filas)", r, "| k_produccion %s" % r["controles"]["k_produccion"]["estado"])


def T3b_pub_runner_ausente():
    f = mundo()
    for x in f:
        x.pop("pub_runner", None)
    r = correr(f)
    c = r["controles"]["k_produccion"]
    mostrar("T3b (sin pub_runner en todas)", r, "| k_produccion %s distinto %d" % (c["estado"], len(c["predicado_distinto_del_runner"])))
    f = mundo()
    for x in f:
        if not (x["k_slim"]["vrp_mw"] or 0) > 0:
            x.pop("pub_runner", None)                  # solo en las filas donde K no publica (la mayoria)
    r = correr(f)
    mostrar("T3b' (sin pub_runner donde K no publica)", r, "| k_produccion %s" % r["controles"]["k_produccion"]["estado"])


# ---------------------------------------------------------------- VF4-06 / protocolo E
def _cola(n=3, ini=18, **kw):
    return [F(VOLS[i % 5], "2026-10-%02d 03:00" % (ini + i), "neg_limpio", tramo="E", **kw) for i in range(n)]


def T4a_via_no_corrio_en_toda_E():
    """E entera con v_marca='geo_distinta' (la via no corrio en datos nuevos): el protocolo saca E y el veredicto sale
    de C solo."""
    f = mundo() + _cola(8)
    for x in f:
        if x["tramo"] == "E":
            x["v_marca"] = "geo_distinta"
    r = correr(f)
    mostrar("T4a", r)


def T4b_borde_16_17():
    f = mundo() + [F("Lascar", "2026-10-16 23:59", "neg_limpio")]
    f[-1]["estado"] = "error_descarga"
    r = correr(f)
    mostrar("T4b (falla 2026-10-16 23:59 = C)", r)
    f = mundo() + [F("Lascar", "2026-10-17 00:00", "neg_limpio", tramo="E")]
    f[-1]["estado"] = "error_descarga"
    r = correr(f)
    mostrar("T4b' (falla 2026-10-17 00:00 = E)", r)


def T4c_k_produccion_rojo_solo_en_E():
    f = mundo() + _cola(3)
    f[-1]["k_difiere_de_guardado"] = True              # no reproducida en su sha
    r = correr(f)
    mostrar("T4c (k_produccion rojo solo en E, cobertura OK)", r)


def T4d_E_excluido_oculta_k_produccion_de_E():
    f = mundo() + _cola(3)
    f[-1]["k_difiere_de_guardado"] = True              # rojo de K en E
    f[-2]["estado"] = "error_descarga"                 # y ademas una falla de arnes en E (cobertura roja solo en E)
    r = correr(f)
    mostrar("T4d (k_produccion rojo en E + falla arnes en E)", r)


def T4e_sin_pasada_E_por_dia_excluido():
    """Dia de E excluido al armar la poblacion (HEAD 404): MIROVA tuvo una pasada ese dia, queda en sin_pasada_nuestra."""
    f = mundo() + _cola(3)
    r = correr(f, sin=[("Lascar", "2026-10-19 03:00", "bajo1")])
    mostrar("T4e", r)


# ---------------------------------------------------------------- Chillan: magnitud cero
def T5_chillan_mag_cero():
    f = mundo() + [F("NevadosDeChillan", dia(120 + i) + " 07:20", "protegida", k=0.5, v=1.0, mir=1.0, z=15) for i in range(5)]
    def pred(casos):
        out = []
        for r, _ in casos:
            pc = (r or {}).get("primary_cluster") or {}
            pub = int(r is not None and r.get("distance_class") == "summit")
            out.append((pub, float(pc.get("vrp_mw") or 0.0)))
        return out
    f[-1]["v_slim"]["primary_cluster"]["vrp_mw"] = 0.0
    f[-1]["vcerc_slim"]["primary_cluster"]["vrp_mw"] = 0.0
    f[-1]["vpico_slim"]["primary_cluster"]["vrp_mw"] = 0.0
    try:
        r = correr(f, pred=pred)
        print("T5", r["chillan"]["estado"], r["chillan"]["n_pares"])
    except Exception as e:
        print("T5 CAE", type(e).__name__, e)


TODOS = [("T1a", T1a_S1_pico_pierde_protegida_de_V), ("T1b", T1b_pico_pierde_protegida_de_V_solo_ocr),
         ("T1c", T1c_doc_dice_de_la_tabla_codigo_incluye_ocr), ("T1d", T1d_recupera_protegida_sin_credito),
         ("T2a", T2a_identidad_motivo_sellado_con_grilla), ("T2b", T2b_n_pob_cuenta_filas_no_poblacion),
         ("T3a", T3a_k_difiere_none), ("T3b", T3b_pub_runner_ausente),
         ("T4a", T4a_via_no_corrio_en_toda_E), ("T4b", T4b_borde_16_17), ("T4c", T4c_k_produccion_rojo_solo_en_E),
         ("T4d", T4d_E_excluido_oculta_k_produccion_de_E), ("T4e", T4e_sin_pasada_E_por_dia_excluido),
         ("T5", T5_chillan_mag_cero)]

if __name__ == "__main__":
    sel = sys.argv[1].split(",") if len(sys.argv) > 1 else [n for n, _ in TODOS]
    for n, fn in TODOS:
        if n in sel:
            P._ID[0] = 0
            fn()
