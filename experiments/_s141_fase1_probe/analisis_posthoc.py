# -*- coding: utf-8 -*-
"""S141, Fase 1: análisis POST HOC del probe del vecino del foco (declarado como tal).

POR QUÉ EXISTE. El criterio pre-registrado (plan 2026-09-15, H_S141_VECINO_FOCO) salió
INDETERMINADO porque el control falló, y al revisar las primeras pasadas (Chaitén, antes de ver el
total) aparecieron dos defectos de diseño del instrumento, anotados en la memoria de la sesión antes
de juntar los 8 volcanes:
  D1. el control exigía >= 50 % de los 8 vecinos incluidos; una pasada que publica pc_n píxeles sólo
      puede incluir pc_n - 1 vecinos, así que con pc_n <= 4 el control no podía aprobar;
  D2. el aporte con fondo local sumaba max(exceso, 0) de los 8 vecinos aunque ningún test los
      marcara: en un campo con ruido la mitad de los píxeles queda sobre la media de sus vecinos, así
      que el aporte sale positivo sin calor. MIROVA sólo suma píxeles alertados.
Y un límite ya declarado en el plan: de los 8 vecinos nativos, MIROVA sólo suma Npix - 1.

NADA DE ESTO REEMPLAZA EL VEREDICTO PRE-REGISTRADO (que queda INDETERMINADO). Son lecturas
descriptivas para decidir cómo rehacer el instrumento, y cada una lleva su definición.

  M1 control corregido: incluido / min(8, pc_n_hoy - 1) sobre las pasadas control.
  M2 etapa de los vecinos más calientes: por candidato, los (Npix_OSF - 1) vecinos de mayor BT, como
     aproximación a los píxeles que MIROVA suma; se cuenta su etapa.
  M3 aporte sin ruido: aporte con fondo local sólo de vecinos que algún test marcó y no quedaron en el
     cúmulo, como fracción de la brecha (VRP OSF - publicado).
  M4 cota del fondo local: aporte con fondo local de los (Npix_OSF - 1) vecinos más calientes, sin
     importar la etapa, como fracción de la brecha (cuánto cerraría sumar esos píxeles).
  M5 exceso de BT de esos vecinos sobre su fondo local y sobre el fondo del anillo (K).
  M6 distancia del centro elegido al píxel caliente del OSF (km).

Todo por estrato focal/nevado y también sólo con candidatos que hoy publican 1 píxel (P3).
USO: python experiments/_s141_fase1_probe/analisis_posthoc.py  ->  posthoc.json
"""
import io
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import juntar  # noqa: E402


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 4) if xs else None


def _p90(xs):
    xs = sorted(x for x in xs if x is not None)
    return round(xs[int(0.9 * (len(xs) - 1))], 4) if xs else None


def _valida(f):
    return f.get("ok") and (f.get("resumen") or {}).get("grilla_ok")


def m1_control(filas):
    inc = esp = 0
    detalle = []
    for f in filas:
        if f["clase"] != "control" or not _valida(f):
            continue
        pc = (f.get("hoy") or {}).get("pc_n") or 1
        e = min(8, max(pc - 1, 0))
        i = f["resumen"]["conteo"].get("incluido", 0)
        inc += i
        esp += e
        detalle.append({"volcan": f["volcan"], "pasada_utc": f["pasada_utc"], "pc_n_hoy": pc,
                        "vecinos_incluidos": i, "alcanzables": e})
    return {"incluidos": inc, "alcanzables": esp,
            "fraccion": round(inc / esp, 4) if esp else None, "detalle": detalle}


def _calientes(f):
    npix = (f.get("osf") or {}).get("Npix") or 1
    vec = sorted(f["resumen"].get("vecinos") or [], key=lambda v: -(v.get("bt_k") or -1))
    return vec[:max(npix - 1, 0)]


def bloque(filas):
    cand = [f for f in filas if f["clase"] == "candidato" and _valida(f)]
    etapas_calientes = {}
    m3, m4, exc_local, exc_anillo, dist = [], [], [], [], []
    for f in cand:
        r = f["resumen"]
        brecha = (f["osf"]["vrp_mw"] or 0) - (f["persistido"]["pub_mw"] or 0)
        cal = _calientes(f)
        for v in cal:
            etapas_calientes[v["etapa"]] = etapas_calientes.get(v["etapa"], 0) + 1
            if v.get("bt_k") is None:      # píxel sin dato (NaN en la escena): no entra al exceso
                continue
            if v.get("fondo_local_k") is not None:
                exc_local.append(v["bt_k"] - v["fondo_local_k"])
            tbg = (f.get("record") or {}).get("t_bg_k") or (f.get("persistido") or {}).get("t_bg_k")
            if tbg:
                exc_anillo.append(v["bt_k"] - tbg)
        marcados = [v for v in r.get("vecinos") or [] if v["etapa"] not in ("incluido", "nunca_candidato")]
        if brecha > 0:
            m3.append(sum(v["aporte_fondo_local_mw"] for v in marcados) / brecha)
            m4.append(sum(v["aporte_fondo_local_mw"] for v in cal) / brecha)
        dist.append(r.get("dist_centro_a_osf_km"))
    n_cal = sum(etapas_calientes.values())
    return {
        "n_candidatos": len(cand),
        "M2_etapa_de_los_vecinos_mas_calientes": etapas_calientes,
        "M2_fraccion_nunca_candidato": round(etapas_calientes.get("nunca_candidato", 0) / n_cal, 4) if n_cal else None,
        "M3_mediana_fraccion_brecha_marcados_perdidos": _med(m3),
        "M3_pasadas_con_aporte_cero": sum(1 for x in m3 if x == 0),
        "M4_mediana_fraccion_brecha_calientes_fondo_local": _med(m4),
        "M5_mediana_exceso_sobre_fondo_local_k": _med(exc_local),
        "M5_mediana_exceso_sobre_anillo_k": _med(exc_anillo),
        "M6_mediana_dist_centro_osf_km": _med(dist),
        "M6_p90_dist_centro_osf_km": _p90(dist),
    }


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    filas = juntar.cargar(HERE / "artefactos")
    hoy1 = [f for f in filas if f["clase"] == "control" or (f.get("hoy") or {}).get("pc_n") == 1]
    out = {"advertencia": "POST HOC: no reemplaza el veredicto pre-registrado (INDETERMINADO)",
           "M1_control_corregido": m1_control(filas)}
    for nombre, base in (("todos", filas), ("hoy_1px", hoy1)):
        out[nombre] = {"total": bloque(base),
                       "focal": bloque([f for f in base if f.get("regimen") == "focal"]),
                       "nevado": bloque([f for f in base if f.get("regimen") == "nevado"])}
    (HERE / "posthoc.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
