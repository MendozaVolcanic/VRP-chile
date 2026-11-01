# -*- coding: utf-8 -*-
"""F1a, punto 11.1.2 del plan: `clase_mirova.alerta_protegida` mira solo la fila que recibe y
`evaluar_fk.proteccion` (l. 194) la aplica fila por fila sin cruzar canales. Pregunta: cuantas pasadas que el
veredicto de K trata como PROTEGIDAS (lectura A) descansan en una fila OCR de 1 MW o mas mientras la TABLA
(CONS) dice para esa misma pasada FALSO_POSITIVO (o RUTINA con VRP 0).

Las dos preguntas del instrumento:
 1. Si el cruce existiera y fuera frecuente, lo veria: cuento por pasada las filas CONS y OCR pareadas a +-120 s
    con el mismo pareo del evaluador (bp.parear) y clasifico. Control positivo: una fila OCR sintetica de 2 MW
    pegada a una pasada con CONS FALSO_POSITIVO tiene que salir contada (se imprime).
 2. Si el instrumento estuviera muerto, el denominador (protegidas A) seria 0 o no coincidiria con el del
    evaluador (v1_rep.json: VIIRS375 21, VIIRS750 12, MODIS 4 en V1). Se imprime y se compara.
Uso: python prot_cruce_canales.py <tmp_v1> <tmp_v2_con_ocr> <v1_rep.json>
"""
import json, sys, collections
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E  # noqa: E402
bp, cm, ev = E.bp, E.cm, E.ev


def cruce(ventana, tmp, solo_tabla):
    cfg = dict(E.VENTANAS[ventana]); cfg["solo_tabla"] = solo_tabla
    ref = E.archivos_ref(cfg, Path(tmp))
    cons, ocr, capas = ref
    kw = {"historico_path": capas["historico"], "respaldo_path": capas["respaldo"]} if capas else {}
    filas = ev.cargar_referencia_unificada(Path(cons), Path(ocr), **kw)
    por_vb, _, _, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), (cfg["desde"], cfg["hasta"]))
    T = json.load(open(Path(tmp) / "t_C0_K.json", encoding="utf-8"))["pasadas"]
    out = collections.Counter(); casos = []
    for k, v in T.items():
        vol, b, t = k.split("|")
        if "control" not in v:
            continue
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        ff = bp.parear(por_vb.get((vol, b), []), dt)
        pa = [f for f in ff if cm.alerta_protegida(f, lectura="A")]
        if not pa:
            continue
        out[(b, "protegidas_A")] += 1
        if v["control"]["pub"]:
            out[(b, "protegidas_A_que_C0_publica")] += 1
        fuentes = {f["source"] for f in pa}
        cons_f = [f for f in ff if f["source"] == "CONS"]
        tipos_cons = sorted({f["tipo"] for f in cons_f})
        if fuentes == {"OCR"}:
            out[(b, "prot_solo_por_OCR")] += 1
            if any(f["tipo"].startswith("FALSO_POSITIVO") for f in cons_f):
                out[(b, "prot_OCR_con_CONS_FALSO_POSITIVO")] += 1
                casos.append((k, "CONS=%s" % tipos_cons, "OCR=%s MW" % [f["vrp_mw"] for f in pa], "C0 pub %d K pub %d" % (v["control"]["pub"], v.get("brazo", {}).get("pub", -1))))
            elif any(f["tipo"] == "RUTINA" for f in cons_f):
                out[(b, "prot_OCR_con_CONS_RUTINA")] += 1
                casos.append((k, "CONS=%s" % tipos_cons, "OCR=%s MW" % [f["vrp_mw"] for f in pa], "C0 pub %d K pub %d" % (v["control"]["pub"], v.get("brazo", {}).get("pub", -1))))
            elif not cons_f:
                out[(b, "prot_OCR_sin_fila_CONS")] += 1
            else:
                out[(b, "prot_OCR_con_CONS_otro")] += 1
    return out, casos


def main():
    tmp1, tmp2, v1json = sys.argv[1:4]
    print("== V1 (tabla y OCR, como decide el pre-registro)")
    c, casos = cruce("V1", tmp1, False)
    for k in sorted(c): print("   %-9s %-36s %d" % (k[0], k[1], c[k]))
    for x in casos: print("   caso:", x)
    v1 = json.load(open(v1json, encoding="utf-8"))
    print("   control 2 (denominador del evaluador, P1 'protegidas que C0 publica' de v1_rep.json): K A MODIS/V375/V750 =",
          [v1["veredicto"].get("P1|K|%s|A" % s) for s in E.SENS])
    print("== V2 con OCR (informa, no decide; §4.2 de la regla)")
    c, casos = cruce("V2", tmp2, False)
    for k in sorted(c): print("   %-9s %-36s %d" % (k[0], k[1], c[k]))
    for x in casos: print("   caso:", x)
    # control positivo 1: fila OCR sintetica de 2 MW con CONS FALSO_POSITIVO en la misma pasada
    fila_cons = {"tipo": "FALSO_POSITIVO", "vrp_mw": 3.0, "source": "CONS"}
    fila_ocr = {"tipo": "ALERTA_TERMICA_OCR", "vrp_mw": 2.0, "source": "OCR"}
    pa = [f for f in (fila_cons, fila_ocr) if cm.alerta_protegida(f, lectura="A")]
    print("== control positivo 1: pasada sintetica CONS FALSO_POSITIVO 3 MW + OCR ALERTA 2 MW -> protegida A por fila:",
          [f["source"] for f in pa], "(el evaluador la contaria como protegida: %s)" % bool(pa))


if __name__ == "__main__":
    main()
