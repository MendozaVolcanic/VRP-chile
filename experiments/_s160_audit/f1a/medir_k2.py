# -*- coding: utf-8 -*-
"""F1a, segunda tanda de placebos (R6) sobre evaluar_fk.py, despues de ver la primera (medir_k.py):

1. En V1 el control de determinismo compara K con F en VIIRS (misma decision en 98 % o mas): un placebo puesto
   SOLO en K cae en INDECIDIBLE por ese control, no por el criterio. Aqui el placebo reemplaza a F y a K juntos
   (en VIIRS son el mismo codigo, PREREGISTRO.md §2), que es como el pre-registro los entiende.
2. El disfraz `triggered_test1 = False` (huella que exige el control de cableado a un brazo sin Test 1) NO es
   inocuo: el predicado del tablero lo lee (frontend/index.html:1609-1613, isSummitDetection) y cambia la
   publicacion de records con vrp_mw 0 y discarded_reason. Por eso cada placebo se corre en dos versiones:
   `t1off` (disfrazado: pasa el cableado) y `t1keep` (sin disfraz: el cableado lo marca ROTO y el global sale
   INDECIDIBLE, pero las sumas de P2 se calculan igual y son las que se leen). Y un caso `solo_t1off` que mide el
   efecto del disfraz solo, sin ganancia ni desplazamiento.
Uso: python medir_k2.py <D_union_v1> <D_union_v2a> <D_union_v2b> <salida_dir> <produccion> <v1_rep.json>
"""
import copy, json, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import medir_k as M  # noqa: E402


def escalar_keep(r, g):
    for c in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw", "vrp_vent_mw"):
        if r.get(c): r[c] = r[c] * g
    pc = r.get("primary_cluster")
    if pc and pc.get("vrp_mw"): pc["vrp_mw"] = pc["vrp_mw"] * g
    for q in r.get("anomaly_pixels") or []:
        if q.get("vrp_mw"): q["vrp_mw"] = q["vrp_mw"] * g
    return r


def placebo(docs, tipo, g, t1off):
    if tipo == "shift":
        out = M.placebo_shift(docs)   # ya pone t1 False
        if not t1off:   # restaurar el valor original por pasada
            for v, d in docs.items():
                orig = {r.get("datetime_utc", "") + "|" + (r.get("sensor") or ""): bool(r.get("triggered_test1")) for r in d["records"]}
                for r in out[v]["records"]:
                    r["triggered_test1"] = orig.get(r.get("datetime_utc", "") + "|" + (r.get("sensor") or ""), False)
        return out
    out = {}
    for v, d in docs.items():
        recs = []
        for r in d["records"]:
            r = copy.deepcopy(r)
            if g != 1.0: escalar_keep(r, g)
            if t1off: r["triggered_test1"] = False
            recs.append(r)
        out[v] = {"records": recs}
    return out


def resumen_de(res):
    S = ("MODIS", "VIIRS375", "VIIRS750")
    return {"global_K": res.get("global", {}).get("K"), "cobertura_ok": res.get("cobertura_ok"), "cableado": res.get("cableado"),
            "determinismo_ok": res.get("determinismo_ok"),
            "P1_K_A": {s: res.get("veredicto", {}).get("P1|K|%s|A" % s) for s in S},
            "P2_K_A": {s: res.get("veredicto", {}).get("P2|K|%s|A" % s) for s in S},
            "suma_K_A": {s: res.get("suma", {}).get("K|%s|A" % s, {}).get("decide") for s in S},
            "suma_C0_A": {s: res.get("suma", {}).get("C0|%s|A" % s, {}).get("decide") for s in S}}


def main():
    d_v1, d_v2a, d_v2b, salida, prod, v1json = sys.argv[1:7]
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    work = Path(d_v1).parent / "placebos2"; shutil.rmtree(work, ignore_errors=True)
    resumen = {}
    casos = [("x110_t1off", "escala", 1.10, True), ("x120_t1off", "escala", 1.20, True), ("shift_t1off", "shift", 1.0, True),
             ("solo_t1off", "escala", 1.0, True), ("x110_t1keep", "escala", 1.10, False), ("x120_t1keep", "escala", 1.20, False),
             ("shift_t1keep", "shift", 1.0, False)]
    base = {n: M.leer(d_v1, n) for n in ("C0", "F", "K", "G")}
    for caso, tipo, g, t1off in casos:
        dst = work / ("v1_" + caso)
        pl = placebo(base["C0"], tipo, g, t1off)
        for n in ("C0", "G"): M.escribir(dst, n, base[n])
        for n in ("F", "K"): M.escribir(dst, n, pl)
        shutil.copytree(Path(d_v1) / "logs", dst / "logs")
        args = ["--ventana", "V1", "--raiz", str(dst), "--logs", str(dst / "logs"), "--out", str(dst / "res.json"), "--tmp", str(dst / "tmp"), "--produccion", prod]
        res, _ = M.correr("v1_" + caso, args, salida)
        resumen["v1_" + caso] = resumen_de(res)
        print("V1", caso, json.dumps(resumen["v1_" + caso], ensure_ascii=False)); sys.stdout.flush()
    base2 = {n: {"a": M.leer(d_v2a, n), "b": M.leer(d_v2b, n)} for n in ("C0", "K")}
    for caso, tipo, g, t1off in casos:
        dst = work / ("v2_" + caso)
        for parte, d_src in (("a", d_v2a), ("b", d_v2b)):
            M.escribir(dst / parte, "C0", base2["C0"][parte])
            M.escribir(dst / parte, "K", placebo(base2["C0"][parte], tipo, g, t1off))
            shutil.copytree(Path(d_src) / "logs", dst / parte / "logs")
        args = ["--ventana", "V2", "--raiz", str(dst / "a"), "--raiz", str(dst / "b"), "--logs", str(dst / "a" / "logs"), "--logs", str(dst / "b" / "logs"),
                "--ruido-de", v1json, "--out", str(dst / "res.json"), "--tmp", str(dst / "tmp"), "--produccion", prod]
        res, _ = M.correr("v2_" + caso, args, salida)
        resumen["v2_" + caso] = resumen_de(res)
        print("V2", caso, json.dumps(resumen["v2_" + caso], ensure_ascii=False)); sys.stdout.flush()
    (salida / "resumen2.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
