# -*- coding: utf-8 -*-
"""S168, prueba de identidad_f4.py con runners sintéticos armados sobre grillas REALES del censo MOD-D, y cruce con
evaluar_f4.control_identidad (el evaluador sellado, sin modificarlo) para comprobar que lee bien identidad.json.

POR QUÉ. Un control de identidad que no puede dar rojo no mide nada (A110, A116). Cada escenario arma un directorio de
artefactos como el que dejaría el runner (grilla_<vol>_<AAAAMMDDHHMM>.npz y f4_parte00.jsonl, el formato documentado
en identidad_f4.py), cambia UNA cosa, corre identidad_f4.main, carga su salida como la carga evaluar_f4.main y
asevera lo que tiene que dar control_identidad.

Escenarios:
  S1 igual        101 pasadas con grilla del runner = grilla del censo (float64) y su record: todas iguales, OK
  S2 celda        S1 con una celda caliente agregada al runner en una pasada (record recalculado): distinta, rojo
  S3 tope 1 %     S1 con una pasada de otro gránulo (1 de 101 < 1 %): OK; con dos (2 de 101 > 1 %): rojo
  S4 faltante     S1 sin nada del runner en una pasada: la identidad no la escribe, el evaluador la cuenta faltante, rojo
  S5 sellada      el runner saca una pasada con grilla del censo por «volcán fuera del gránulo» con el mismo gránulo:
                  rojo (N-01); la misma declarada con otro gránulo cuenta como otro gránulo (1 de 101): OK
  S6 captura      el runner guarda una máscara que no es la de su grilla: misma_mascara falsa y captura incoherente, rojo
  S8 probe_f4     el formato que guarda probe_f4.py (sin clase en el npz, l1b_usado en la fila, box y pos_crater):
                  iguales y OK; con un l1b_usado distinto y una celda cambiada, rojo
  S7 float32      grilla del runner = la del censo más un ruido menor que la resolución float32: igual, OK, y
                  grilla_igual_float32 verdadero
Uso: python probar_identidad_f4.py  (escribe probar_identidad_f4_salida.txt); temporales en TMP.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import identidad_f4 as ID  # noqa: E402
import poblacion_f4 as PF  # noqa: E402

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("evaluar_f4_sellado", AQUI / "evaluar_f4.py")
EV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EV)

L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def chk(c, msg):
    if not c:
        raise AssertionError(msg)


# ------------------------------------------------------------------ insumos reales
def elegir(n_total=101, n_alerta=6):
    """Pasadas del censo con grilla: n_alerta en que la vía alerta y el resto sin alerta (deterministas por id)."""
    ab, _npz = PF.leer_censo()
    cab = ID.leer_censo_ab(PF.CENSO)
    con = sorted((r["id"], k) for k, r in ab.items() if r["grilla"])
    al, sin = [], []
    for i, k in con:
        if len(al) >= n_alerta and len(sin) >= n_total - n_alerta:
            break
        z = np.load(PF.CENSO / ab[k]["grilla"])
        c = cab[i]
        rec = ID.via(z["mir"].astype(np.float64), z["tir"].astype(np.float64), k[0], c["dayflag"], c["sunglint"],
                     c["sensor"])
        tgt = al if rec.get("anomaly_pixels") else sin
        if (tgt is al and len(al) < n_alerta) or (tgt is sin and len(sin) < n_total - n_alerta):
            tgt.append({"vol": k[0], "dt": k[1], "l1b": ab[k]["l1b"], "geo": ab[k]["geo"], "id_censo": i,
                        "grilla_censo": ab[k]["grilla"], "tramo": "C", "lab": "neg_limpio"})
    return al + sin, cab


def runner_de(p, cab, mir=None, tir=None, mascara=None, l1b=None, otro=False, motivo=None, sin_npz=False,
              formato="propio"):
    """Lo que dejaría el runner para p: la grilla dada (por defecto la del censo en float64) y el record de la vía."""
    z = np.load(PF.CENSO / p["grilla_censo"])
    mir = z["mir"].astype(np.float64) if mir is None else mir
    tir = z["tir"].astype(np.float64) if tir is None else tir
    c = cab[p["id_censo"]]
    rec = ID.via(mir, tir, p["vol"], c["dayflag"], c["sunglint"], c["sensor"])
    m = ID.mascara_de(rec, mir.shape[0]) if mascara is None else mascara
    npz = None if sin_npz else {"mir": mir, "tir": tir, "mascara": m, "vrp_mw": float(rec.get("vrp_mw") or 0.0),
                                "distance_class": rec.get("distance_class") or "", "dayflag": c["dayflag"],
                                "sunglint": c["sunglint"], "l1b": l1b or p["l1b"], "geo": p["geo"]}
    fila = {"tipo": "record", "vol": p["vol"], "dt": p["dt"], "estado": "ok", "motivo": motivo,
            "otro_granulo": otro, "l1b": l1b or p["l1b"], "geo": p["geo"],
            "v_slim": {"vrp_mw": rec.get("vrp_mw"), "distance_class": rec.get("distance_class")}}
    if formato == "probe_f4":            # lo que guarda probe_f4.py: sin clase ni nombres en el npz, *_usado en la fila
        c_ = ID.contexto(p["vol"])
        if npz is not None:
            for k in ("distance_class", "l1b", "geo"):
                npz.pop(k)
            npz.update({"box": np.asarray(c_["box"], np.float64), "pos_crater": np.array(c_["pos"])})
        fila["l1b_usado"], fila["geo_usado"] = fila.pop("l1b"), fila.pop("geo")
        fila["l1b_pedido"], fila["geo_pedido"] = p["l1b"], p["geo"]
    return npz, fila


def escribir_art(d, runners):
    d.mkdir(parents=True)
    with open(d / "f4_parte00.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"tipo": "cabecera"}) + "\n")
        for (vol, dt), (npz, fila) in runners.items():
            if fila is not None:
                fh.write(json.dumps(fila) + "\n")
            if npz is not None:
                np.savez(d / ID.nombre_npz(vol, dt), **npz)


def correr(base, nombre, pasadas, runners):
    d = base / nombre
    escribir_art(d / "art", runners)
    pobf = d / "pob.json"
    pobf.write_text(json.dumps({"pasadas": pasadas}), encoding="utf-8")
    out = ID.main(["--art", str(d / "art"), "--poblacion", str(pobf), "--salida", str(d / "identidad.json")])
    # como evaluar_f4.main
    idn = json.load(open(d / "identidad.json", encoding="utf-8"))
    ident = {(x["vol"], x["dt"]): x for x in idn["pasadas"]}
    return out, ident


def filas_ev(pasadas, selladas=()):
    out = []
    for p in pasadas:
        sel = (p["vol"], p["dt"]) in selladas
        out.append({"vol": p["vol"], "dt": p["dt"], "grilla_censo": p["grilla_censo"], "_evaluable": not sel,
                    "_motivo": "volcan_fuera_del_granulo" if sel else None})
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    base = Path(tempfile.mkdtemp(prefix="probar_identidad_"))
    pr("probar_identidad_f4.py | temporales en", base)
    pasadas, cab = elegir()
    n = len(pasadas)
    pr(f"pasadas elegidas: {n} ({sum(1 for _ in pasadas[:6])} con alerta de la vía primero): "
       f"{[(p['vol'], p['dt'], p['id_censo']) for p in pasadas[:6]]}")
    base_runners = {(p["vol"], p["dt"]): runner_de(p, cab) for p in pasadas}
    resultados = []

    def escenario(nombre, fn):
        try:
            fn()
            resultados.append((nombre, "OK"))
            pr(f"{nombre}: OK")
        except AssertionError as e:
            resultados.append((nombre, "FALLA ASERCION"))
            pr(f"{nombre}: FALLA ASERCION {e}")
        except Exception:  # noqa: BLE001
            resultados.append((nombre, "CAE"))
            pr(f"{nombre}: CAE {traceback.format_exc()[-800:]}")

    def s1():
        out, ident = correr(base, "s1", pasadas, base_runners)
        chk(out["resumen"]["n_iguales"] == n, f"iguales {out['resumen']}")
        chk(all(e["captura_coherente"] and e["max_dif_radiancia"] == 0.0 for e in out["pasadas"]), "coherencia")
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   control_identidad:", {k: c[k] for k in ("estado", "n_con_grilla", "n_distintas", "n_otro_granulo",
                                                       "n_faltan")})
        chk(c["estado"] == "OK" and c["n_distintas"] == 0 and c["n_faltan"] == 0, f"evaluador {c}")
        # y con el total sellado de 5.321 (el de la corrida real) estas 101 no bastan: rojo
        chk(EV.control_identidad(ident, filas_ev(pasadas))["estado"] == "INDECIDIBLE", "n_grillas sellado")

    def s2():
        r = dict(base_runners)
        p = pasadas[-1]                                   # una sin alerta de la vía
        z = np.load(PF.CENSO / p["grilla_censo"])
        mir = z["mir"].astype(np.float64)
        f, c = (int(round(v)) for v in ID.contexto(p["vol"])["pos"])
        mir[f, c] += 5.0                                  # un píxel caliente en el cráter (W m-2 sr-1 um-1)
        r[(p["vol"], p["dt"])] = runner_de(p, cab, mir=mir)
        out, ident = correr(base, "s2", pasadas, r)
        e = ident[(p["vol"], p["dt"])]
        pr("   pasada cambiada:", {k: e.get(k) for k in ("mismo_granulo", "misma_mascara", "dvrp", "misma_clase",
                                                         "npix_runner", "npix_grilla", "max_dif_radiancia",
                                                         "captura_coherente")})
        chk(e["mismo_granulo"] and not e["misma_mascara"] and e["npix_runner"] > e["npix_grilla"], f"entrada {e}")
        chk(abs(e["max_dif_radiancia"] - 5.0) < 1e-4 and e["captura_coherente"], "radiancia o coherencia")
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   control_identidad:", {k: c[k] for k in ("estado", "n_distintas")})
        chk(c["estado"] == "INDECIDIBLE" and c["n_distintas"] == 1, f"evaluador {c}")

    def s3():
        r = dict(base_runners)
        p = pasadas[10]
        r[(p["vol"], p["dt"])] = runner_de(p, cab, l1b=p["l1b"].replace(".hdf", ".otro.hdf"))
        out, ident = correr(base, "s3a", pasadas, r)
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   1 de 101 con otro gránulo:", {k: c[k] for k in ("estado", "n_otro_granulo")})
        chk(not ident[(p["vol"], p["dt"])]["mismo_granulo"] and c["estado"] == "OK" and c["n_otro_granulo"] == 1,
            f"evaluador {c}")
        q = pasadas[11]
        r[(q["vol"], q["dt"])] = runner_de(q, cab, otro=True)      # declarado por el arnés, mismos nombres
        out, ident = correr(base, "s3b", pasadas, r)
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   2 de 101 con otro gránulo:", {k: c[k] for k in ("estado", "n_otro_granulo")})
        chk(not ident[(q["vol"], q["dt"])]["mismo_granulo"] and c["estado"] == "INDECIDIBLE"
            and c["n_otro_granulo"] == 2, f"evaluador {c}")

    def s4():
        r = dict(base_runners)
        p = pasadas[20]
        r[(p["vol"], p["dt"])] = (None, None)
        out, ident = correr(base, "s4", pasadas, r)
        chk(out["sin_runner"] == [[p["vol"], p["dt"]]] and (p["vol"], p["dt"]) not in ident, "sin_runner")
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   control_identidad:", {k: c[k] for k in ("estado", "n_faltan")})
        chk(c["estado"] == "INDECIDIBLE" and c["n_faltan"] == 1, f"evaluador {c}")

    def s5():
        r = dict(base_runners)
        p = pasadas[30]
        r[(p["vol"], p["dt"])] = runner_de(p, cab, motivo="volcan_fuera_del_granulo", sin_npz=True)
        out, ident = correr(base, "s5a", pasadas, r)
        e = ident[(p["vol"], p["dt"])]
        c = EV.control_identidad(ident, filas_ev(pasadas, {(p["vol"], p["dt"])}), n)
        pr("   sellada, mismo gránulo:", {k: e.get(k) for k in ("mismo_granulo", "misma_mascara", "dvrp")},
           {k: c[k] for k in ("estado", "n_selladas_sin_explicar")})
        chk(e["mismo_granulo"] and e.get("sin_grilla_del_runner") and c["estado"] == "INDECIDIBLE"
            and c["n_selladas_sin_explicar"] == 1, f"evaluador {c}")
        r[(p["vol"], p["dt"])] = runner_de(p, cab, motivo="volcan_fuera_del_granulo", sin_npz=True, otro=True)
        out, ident = correr(base, "s5b", pasadas, r)
        c = EV.control_identidad(ident, filas_ev(pasadas, {(p["vol"], p["dt"])}), n)
        pr("   sellada, otro gránulo:", {k: c[k] for k in ("estado", "n_otro_granulo", "n_selladas_sin_explicar")})
        chk(c["estado"] == "OK" and c["n_otro_granulo"] == 1 and c["n_selladas_sin_explicar"] == 0, f"evaluador {c}")

    def s6():
        r = dict(base_runners)
        p = pasadas[0]                                    # con alerta de la vía
        npz, fila = copy.deepcopy(base_runners[(p["vol"], p["dt"])])
        m = npz["mascara"].copy()
        m[0, 0] = not m[0, 0]
        npz["mascara"] = m
        r[(p["vol"], p["dt"])] = (npz, fila)
        out, ident = correr(base, "s6", pasadas, r)
        e = ident[(p["vol"], p["dt"])]
        pr("   captura alterada:", {k: e.get(k) for k in ("misma_mascara", "captura_coherente", "dvrp")})
        chk(not e["misma_mascara"] and e["captura_coherente"] is False, f"entrada {e}")
        chk(EV.control_identidad(ident, filas_ev(pasadas), n)["estado"] == "INDECIDIBLE", "evaluador")

    def s7():
        r = {}
        rng = np.random.default_rng(168)
        for p in pasadas:
            z = np.load(PF.CENSO / p["grilla_censo"])
            mir = z["mir"].astype(np.float64)
            eps = np.abs(mir) * 1e-9 * rng.standard_normal(mir.shape)   # muy por debajo de 2^-24 relativo
            r[(p["vol"], p["dt"])] = runner_de(p, cab, mir=mir + np.nan_to_num(eps))
        out, ident = correr(base, "s7", pasadas, r)
        n32 = out["resumen"]["n_grilla_igual_float32"]
        c = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   ruido sub-float32:", {k: out["resumen"][k] for k in ("n_iguales", "n_grilla_igual_float32",
                                                                    "max_dif_radiancia")}, c["estado"])
        chk(n32 == n and out["resumen"]["n_iguales"] == n and c["estado"] == "OK", f"{out['resumen']} {c['estado']}")

    def s8():
        r = {(p["vol"], p["dt"]): runner_de(p, cab, formato="probe_f4") for p in pasadas}
        out, ident = correr(base, "s8a", pasadas, r)
        es = out["pasadas"]
        pr("   formato probe_f4:", {k: out["resumen"][k] for k in ("n_iguales", "n_otro_granulo")},
           "box_igual", sum(e.get("box_igual") is True for e in es), "pos_crater_igual",
           sum(e.get("pos_crater_igual") is True for e in es), "clase de", {e["clase_runner_de"] for e in es})
        chk(out["resumen"]["n_iguales"] == n and all(e.get("box_igual") and e.get("pos_crater_igual") for e in es)
            and {e["clase_runner_de"] for e in es} == {"via_sobre_grilla_runner"}, "formato probe_f4")
        chk(EV.control_identidad(ident, filas_ev(pasadas), n)["estado"] == "OK", "evaluador probe_f4")
        q = pasadas[3]
        r[(q["vol"], q["dt"])] = runner_de(q, cab, l1b=q["l1b"].replace(".hdf", ".otro.hdf"), formato="probe_f4")
        q2 = pasadas[4]
        z = np.load(PF.CENSO / q2["grilla_censo"])
        mir = z["mir"].astype(np.float64)
        f, c = (int(round(v)) for v in ID.contexto(q2["vol"])["pos"])
        mir[f, c] += 5.0
        r[(q2["vol"], q2["dt"])] = runner_de(q2, cab, mir=mir, formato="probe_f4")
        out, ident = correr(base, "s8b", pasadas, r)
        cc = EV.control_identidad(ident, filas_ev(pasadas), n)
        pr("   probe_f4 con un l1b_usado distinto y una celda cambiada:", {k: cc[k] for k in ("estado", "n_otro_granulo",
                                                                                          "n_distintas")})
        chk(cc["estado"] == "INDECIDIBLE" and cc["n_otro_granulo"] == 1 and cc["n_distintas"] >= 1, f"evaluador {cc}")

    for nombre, fn in (("S1 igual", s1), ("S2 celda", s2), ("S3 tope 1 %", s3), ("S4 faltante", s4),
                       ("S5 sellada", s5), ("S6 captura", s6), ("S7 float32", s7), ("S8 formato probe_f4", s8)):
        escenario(nombre, fn)
    n_ok = sum(1 for _, r in resultados if r == "OK")
    pr(f"RESUMEN: {n_ok} de {len(resultados)} OK | {time.time() - t0:.0f} s")
    shutil.rmtree(base, ignore_errors=True)
    (AQUI / "probar_identidad_f4_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    sys.exit(0 if n_ok == len(resultados) else 1)


if __name__ == "__main__":
    main()
