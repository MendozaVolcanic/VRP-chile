"""S147 - diseccion del RESIDUAL: que publica la replica donde MIROVA miro y no vio nada,
una vez descontado el Test 1 integrado.

LA PREGUNTA. El A/B de S147 mostro que sin el Test 1 la publicacion en negativos limpios de
VIIRS 375 baja de 86 % a 29 %. Ese 29 % es lo que queda por explicar: son publicaciones del
camino CONTEXTUAL, el que si esta en el paper, y aun asi MIROVA calla. Este script no propone
nada: separa las publicaciones del brazo sin Test 1 en dos poblaciones (MIROVA alerto contra
MIROVA miro y no vio) y compara, variable por variable, en que se diferencian. Las variables son
las que corresponden a las hipotesis abiertas del catalogo de divergencias:

  H-conectiva  (S136): Tests 2 y 3 usan min(C1, mu + C2*sigma). Con `min` manda el MENOR de los
               dos, asi que casi siempre manda el piso C1. Con `max` mandaria el mas estricto.
               Se mide: en que fraccion mu + C2*sigma queda POR ENCIMA del piso, o sea en que
               fraccion `max` exigiria mas que lo que hoy se exige.
  H-tamano:    cumulos de un solo pixel (ruido) contra cumulos de varios (objeto).
  H-magnitud:  MIROVA casi no publica bajo ~0,05 MW (su p05). Cuanto del residual vive ahi.
  H-etapa:     primer pase contra recaptura del segundo pase.
  H-geometria: angulo cenital (borde de barrido = pixel mas grande), plataforma, distancia.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si las dos poblaciones fueran iguales, esto lo mostraria? SI: cada fila compara la MISMA
   variable en las dos poblaciones; sin diferencia, las dos columnas coinciden.
2. Si el instrumento estuviera muerto? Se imprime el conteo de cada poblacion y tiene que cuadrar
   con el del evaluador del A/B (105 publicadas en negativos limpios de VIIRS 375).

LIMITES: ventana 2026-09-01 a 2026-09-20 (posterior a #535, A104); las etiquetas salen de la
referencia congelada; es descriptivo, no causal: una variable que separa es un CANDIDATO.

Uso: python experiments/_s147_residual/diseccion.py [--brazo _s146_ab_sin_test1]
"""
from __future__ import annotations
import argparse
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

DATOS = (ROOT / "experiments" / "_s147_residual" / "_datos" / "experiments"
         / "_s146_ab_sin_test1" / "salidas" / "35521542153")
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
VENTANA = ("2026-09-01", "2026-09-20")
C1_SUMMIT, C2 = 0.003, 5.0   # Tabla 1 de Coppola 2016a, noche, ROI interno


def crudos(brazo_dir: Path) -> dict:
    out = {}
    for vol in bp.VOLS:
        p = brazo_dir / f"{vol}.json"
        if not p.exists():
            continue
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if b:
                out[(vol, b, r.get("datetime_utc"))] = r
    return out


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float)) and x == x]
    return round(st.median(xs), 4) if xs else None


def frac(xs):
    xs = list(xs)
    return f"{100 * sum(xs) / len(xs):5.1f}% ({sum(xs)} de {len(xs)})" if xs else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazo", default="_s146_ab_sin_test1")
    ap.add_argument("--sensor", default="VIIRS375")
    a = ap.parse_args()

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
    recs = cargar_brazo(DATOS / a.brazo, coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)
    raw = crudos(DATOS / a.brazo)

    pobl = {"pos": [], "neg_limpio": []}
    for r in recs:
        if r["b"] != a.sensor or not r["pub"] or r["lab"] not in pobl:
            continue
        x = raw.get(clave(r))
        if x is not None:
            pobl[r["lab"]].append((r, x))

    print(f"brazo {a.brazo} | sensor {a.sensor} | ventana {VENTANA[0]} a {VENTANA[1]}")
    print(f"publicadas donde MIROVA ALERTO: {len(pobl['pos'])} | donde MIROVA MIRO Y NO VIO: "
          f"{len(pobl['neg_limpio'])}\n")

    def col(lab, f):
        return [f(r, x) for r, x in pobl[lab]]

    def fila(nombre, f, modo="med"):
        if modo == "med":
            print(f"{nombre:52} {str(med(col('pos', f))):>16} {str(med(col('neg_limpio', f))):>22}")
        else:
            print(f"{nombre:52} {frac(col('pos', f)):>16} {frac(col('neg_limpio', f)):>22}")

    print(f"{'variable':52} {'MIROVA alerto':>16} {'MIROVA no vio nada':>22}")
    print("-" * 92)
    pc = lambda x: x.get("primary_cluster") or {}
    fila("magnitud que ve el operador, MW (mediana)", lambda r, x: r.get("disp"))
    fila("  fraccion bajo 0,05 MW (el p05 de lo que MIROVA publica)",
         lambda r, x: (r.get("disp") or 0) < 0.05, "frac")
    fila("pixeles del cumulo publicado (mediana)", lambda r, x: pc(x).get("n_pixels"))
    fila("  fraccion de cumulos de UN solo pixel", lambda r, x: pc(x).get("n_pixels") == 1, "frac")
    fila("pixeles anomalos en toda la escena (mediana)", lambda r, x: x.get("n_anomalous_pixels"))
    fila("pixeles del primer pase (mediana)", lambda r, x: x.get("diag_n_first_pass_pixels"))
    fila("pixeles recapturados en el segundo pase (mediana)",
         lambda r, x: x.get("diag_n_second_pass_recapture"))
    fila("distancia del cumulo al crater, km (mediana)", lambda r, x: pc(x).get("centroid_dist_km"))
    fila("angulo cenital del sensor, grados (mediana)", lambda r, x: x.get("sensor_zenith_deg"))
    fila("  fraccion con cenital sobre 40 grados",
         lambda r, x: (x.get("sensor_zenith_deg") or 0) > 40, "frac")
    fila("temperatura del fondo, K (mediana)", lambda r, x: x.get("t_bg_k"))
    fila("t_max menos t_bg, K (mediana)",
         lambda r, x: (x.get("t_max_k") - x.get("t_bg_k"))
         if x.get("t_max_k") and x.get("t_bg_k") else None)
    fila("NTI maximo (mediana)", lambda r, x: x.get("nti_max"))
    print()
    print("H-CONECTIVA: el umbral del paper es una combinacion del piso C1 y de mu + C2*sigma.")
    fila("mu + 5 sigma del dNTI (mediana)",
         lambda r, x: (x.get("diag_mu_dnti") or 0) + C2 * (x.get("diag_sd_dnti") or 0)
         if x.get("diag_sd_dnti") is not None else None)
    fila("  fraccion donde mu+5sigma del dNTI SUPERA el piso 0,003",
         lambda r, x: ((x.get("diag_mu_dnti") or 0) + C2 * (x.get("diag_sd_dnti") or 0)) > C1_SUMMIT
         if x.get("diag_sd_dnti") is not None else False, "frac")
    fila("mu + 5 sigma del dETI (mediana)",
         lambda r, x: (x.get("diag_mu_deti") or 0) + C2 * (x.get("diag_sd_deti") or 0)
         if x.get("diag_sd_deti") is not None else None)
    fila("  fraccion donde mu+5sigma del dETI SUPERA el piso 0,003",
         lambda r, x: ((x.get("diag_mu_deti") or 0) + C2 * (x.get("diag_sd_deti") or 0)) > C1_SUMMIT
         if x.get("diag_sd_deti") is not None else False, "frac")
    print()
    for lab, nombre in (("pos", "MIROVA alerto"), ("neg_limpio", "MIROVA no vio nada")):
        print(f"{nombre}: por volcan   {dict(Counter(r['vol'] for r, _ in pobl[lab]).most_common())}")
        print(f"{'':{len(nombre)}}  por plataforma {dict(Counter(x.get('sensor') for _, x in pobl[lab]).most_common())}")
        print(f"{'':{len(nombre)}}  por fuente     {dict(Counter(x.get('final_hotspot_source') for _, x in pobl[lab]).most_common())}")


if __name__ == "__main__":
    main()
