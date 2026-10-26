# -*- coding: utf-8 -*-
"""S162 V375-B y V375-C: cobertura del MARCO contra la referencia de MIROVA (programa §8.1), con el evaluador común de
la sesión del instrumento (PR #904, rama `instrumento/evaluador-comun`, sin mergear; instrucción de la coordinadora del
2026-10-24: «corre su código desde la rama del instrumento y declara el commit»).

POR QUÉ. El lote de B y C es una MUESTRA sorteada desde los records de producción (la población congelada de S159,
records de 533398f8f). Una pasada en que MIROVA alertó y producción no dejó record nunca pudo entrar al sorteo: no está
en ningún denominador y ningún brazo la mide. Con un solo lado (producción como control), `evaluador_comun.cobertura`
marca esas pasadas como «no observadas»; este script las cuenta por clase (protegida, bajo 1 MW), por canal (tabla u
OCR) y por la etiqueta de protegida de cráter (V375-A), y comprueba que las observadas son las del marco.

Las dos preguntas del instrumento. (1) Si la carga de records o el pareo estuvieran rotos, las alertas observadas no
coincidirían con las alertas del marco (control impreso: deben coincidir con las pasadas «pos» de la población que
deciden, por clave volcán y hora). (2) Una pasada de MIROVA sin record es «no observada», nunca un 0 silencioso: se
lista entera.
Uso: python -I cobertura_marco.py --codigo <carpeta con scripts/ de la rama del instrumento> [--data ...] [--ref ...]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
EXCLUIDOS = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
VENTANA = ("2026-04-01", "2026-10-21")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codigo", required=True, help="carpeta con scripts/ extraídos del commit del instrumento")
    ap.add_argument("--commit", required=True, help="commit del que salió --codigo (se declara en la salida)")
    ap.add_argument("--data", default=r"D:\vrp-trabajo\temporales\s159_n\data_main")
    ap.add_argument("--ref", default=r"C:\vrp-trabajo\temporales\s162_v375\ref_marco",
                    help="tabla y OCR del marco (consolidado fe2d0a57, OCR 4ddd5481) más respaldo_20260408.csv y "
                         "consolidado_filas_perdidas.csv de ca034d66e: las cuatro capas que cargó el marco de S159")
    ap.add_argument("--salida", default=str(AQUI / "cobertura_marco.json"))
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.codigo) / "scripts"))
    sys.path.insert(1, str(Path(a.codigo)))   # pipeline/ y la raíz del commit del instrumento, no la de esta rama
    import banco_paridad as bp  # noqa: E402
    import clase_mirova as cm  # noqa: E402
    import evaluador_comun as ev  # noqa: E402
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    print("código del evaluador común:", a.commit, "desde", a.codigo)
    print("módulos:", ev.__file__, cm.__file__)
    R = Path(a.ref)
    ref = cargar_referencia_unificada(R / "registro_vrp_consolidado.csv", R / "registro_vrp_ocr.csv",
                                      respaldo_path=R / "respaldo_20260408.csv",
                                      historico_path=R / "consolidado_filas_perdidas.csv")
    import hashlib
    print("referencia:", {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:12] for f in sorted(R.glob("*.csv"))})
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    recs, faltan = ev.cargar_lado(a.data, VENTANA, ("VIIRS375",), coords, inner)
    assert recs and not faltan, ("carga de producción", len(recs), faltan)
    pob = json.loads((RAIZ / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    marco_pos = {(o["volcan"], o["hora_utc"]) for o in pob if o["b"] == "VIIRS375" and o["lab"] == "pos"
                 and o["decide"] and o["hora_utc"][:10] not in EXCLUIDOS}
    plat = {(r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M")): r.get("sensor") for r in recs}
    out = {"commit_evaluador_comun": a.commit, "ventana": VENTANA, "excluidos": EXCLUIDOS}
    for canal in ("union", "tabla"):
        pasadas = ev.pasadas_nocturnas(ref, VENTANA, ("VIIRS375",), coords, canal, "SN")
        T = ev.tabla_por_pasada(pasadas, {"produccion": recs}, "produccion")
        cov = ev.cobertura(T, {"produccion": recs}, "produccion", EXCLUIDOS)
        alert = [f for f in T if f["pasada"].estado == "alerta" and f["dia"] not in EXCLUIDOS]
        obs = [f for f in alert if f["cob"]["produccion"] == ev.OBSERVADO]
        noobs = [f for f in alert if f["cob"]["produccion"] == ev.NO_OBSERVADO]
        print(f"\n== canal {canal}: pasadas de MIROVA {len(pasadas)}; alertas {len(alert)} (sin días excluidos); "
              f"observadas por producción {len(obs)}, NO observadas {len(noobs)}; veredicto del evaluador común "
              f"{cov['veredicto']}")
        print("   por lado:", cov["por_lado"])
        # control (1): las observadas que deciden tienen que ser las «pos» del marco
        claves_obs = set()
        for f in obs:
            r = f["rec"]["produccion"]
            claves_obs.add((r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M")))
        if canal == "union":
            print(f"   control: alertas observadas {len(claves_obs)} | «pos» del marco {len(marco_pos)} | en las dos "
                  f"{len(claves_obs & marco_pos)} | sólo observadas {len(claves_obs - marco_pos)} | sólo marco "
                  f"{len(marco_pos - claves_obs)}")
        filas = []
        for f in noobs:
            p = f["pasada"]
            cr, mot = cm.protegida_de_crater(p, radio_km=inner[p.volcano])
            filas.append({"clave": f["clave"], "volcan": p.volcano, "instante": p.instante.strftime("%Y-%m-%d %H:%M"),
                          "vrp_mw": p.vrp_mw, "dist_km": p.dist_km, "fuente": p.fuente, "solo_ocr": p.solo_ocr,
                          "protegida": f["protegida"], "crater": cr, "motivos": list(mot),
                          "tramo": "T" if f["dia"] < "2026-06-13" else "O"})
        c = collections.Counter(("protegida" if x["protegida"] else "bajo 1 MW", "OCR" if x["solo_ocr"] else "tabla",
                                 x["tramo"]) for x in filas)
        print("   NO observadas por clase, canal y tramo:", dict(sorted(c.items())))
        prot = [x for x in filas if x["protegida"]]
        print(f"   protegidas NO observadas: {len(prot)}; de cráter (V375-A) {sum(x['crater'] for x in prot)}; por "
              f"volcán {dict(collections.Counter(x['volcan'] for x in prot))}")
        for x in sorted(prot, key=lambda x: (not x["crater"], x["instante"]))[:40]:
            print("     ", x["volcan"], x["instante"], x["vrp_mw"], "MW a", x["dist_km"], "km,", x["fuente"],
                  "cráter" if x["crater"] else "no cráter " + ",".join(x["motivos"]))
        out[canal] = {"pasadas": len(pasadas), "alertas": len(alert), "observadas": len(obs), "no_observadas": filas,
                      "veredicto_evaluador_comun": cov["veredicto"], "por_lado": cov["por_lado"]}
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nescrito", a.salida)


if __name__ == "__main__":
    main()
