# -*- coding: utf-8 -*-
"""Re-conteo de los meses de S150 (abril a agosto, brazos B y F, VIIRS 375 y 750) con la referencia congelada de
cada mes en la que las filas OCR que cambian de lado (medir.py, variante C) llevan el tipo que da la serie.
Mismas publicaciones de cada brazo (pasadas_meses_B_F.csv del estudio D-9), mismo etiquetador
(banco_paridad.indexar_referencia + etiquetar) y misma suma (suma_errores.contar). Reglas: original y SN.

Dos alternativas:
  todas      la serie reemplaza a la distancia OCR en toda fila OCR decidida (lo que pregunta la tarea);
  sin_tabla  solo en las filas OCR sin pasada de la tabla a +-180 s (donde la tabla existe, ella es la verdad).
Control: con la alternativa "ninguna" la suma tiene que ser la de veredictos_tres_reglas_salida.txt.
"""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
EST = REPO / "experiments" / "_s151_alertas_minimas"
sys.path.insert(0, str(EST))
import suma_errores as se  # noqa: E402  (deja stdout en utf-8)
bp, ev = se.bp, se.ev
sys.path.insert(0, str(REPO / "scripts"))
import clase_mirova as cm  # noqa: E402

AQUI = Path(__file__).resolve().parent
CONG = REPO / "experiments" / "_s149_prereg_invierno" / "_congelado"


def cambios(var="C"):
    """{(vol, sensor, minuto): (tipo_nuevo, con_tabla)} desde pasadas_<var>.csv de medir.py."""
    out = {}
    for p in csv.DictReader(open(AQUI / f"pasadas_{var}.csv", encoding="utf-8")):
        if p["hoy_alerta"] != p["alt_alerta"]:
            nuevo = "FALSO_POSITIVO_OCR" if p["hoy_alerta"] == "True" else "ALERTA_TERMICA_OCR"
            out[(p["vol"], p["sensor"], p["t"])] = (nuevo, p["con_tabla"] == "True")
    return out


def aplicar(filas, camb, modo):
    n = 0
    out = []
    for f in filas:
        k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
        if modo != "ninguna" and f["source"] == "OCR" and k in camb and (modo == "todas" or not camb[k][1]):
            f = dict(f, tipo=camb[k][0]); n += 1
        out.append(f)
    return out, n


def etiquetar(filas, claves, ventana, regla):
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), tuple(ventana), regla_minimas=regla,
                                              umbral_minima_mw=cm.UMBRAL_MINIMA_MW if regla != "original" else None)
    recs = []
    for c in claves:
        vol, b, t = c.split("|")
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "clave": c})
    bp.etiquetar(recs, por_vb, ns, nv)
    ev.anotar_vrp_mirova(recs, por_vb)
    return {r["clave"]: (r["lab"], r.get("vrp_ref")) for r in recs}


def main():
    camb = cambios()
    print(f"cambios de alerta (pasadas): {len(camb)}; con tabla a +-180 s: {sum(v[1] for v in camb.values())}")
    for sensor in ("VIIRS375", "VIIRS750"):
        grupos = se.leer_pasadas(EST / "pasadas_meses_B_F.csv", ["B", "F"], lambda r, s=sensor: f"|{s}|" in r["clave"])
        for regla in ("original", "SN"):
            for modo in ("ninguna", "todas", "sin_tabla"):
                tot = {b: Counter() for b in "BF"}
                napl = 0
                cambiadas = []
                for mes in se.MESES:
                    pas = grupos[mes]
                    ventana = se.verificar_congelado(CONG / mes, se.CONG_MESES_MANIF / mes / "MANIFIESTO.json")
                    filas, n = aplicar(se.cargar_ref(CONG / mes, historico=False), camb, modo)
                    napl += n
                    etq = etiquetar(filas, sorted(pas), ventana, regla)
                    if modo != "ninguna":
                        base = etiquetar(se.cargar_ref(CONG / mes, historico=False), sorted(pas), ventana, regla)
                        cambiadas += [(k, base[k], etq[k]) for k in pas if base[k] != etq[k]]
                    for b in "BF":
                        tot[b].update(se.contar(pas, b, etq, (sensor,)))
                for b in "BF":
                    tot[b]["suma"] = tot[b]["perdidas"] + tot[b]["fp"]
                print(f"{sensor} regla {regla:8s} alternativa {modo:9s} filas OCR cambiadas {napl:3d} | " + " | ".join(
                    f"{b}: perdidas {c['perdidas']} de {c['pos']}, neg pub {c['fp']} de {c['neg']}, SUMA {c['suma']}, "
                    f"protegidas perdidas {c['prot_perdidas']} de {c['prot']}" for b, c in tot.items()))
                for k, a_, b_ in sorted(cambiadas):
                    print(f"      etiqueta {k}: {a_} -> {b_}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
