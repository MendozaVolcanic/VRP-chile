# -*- coding: utf-8 -*-
"""S168, candado de MOD-D fase 4, control 8.7 (PREREGISTRO_MODD_F4.md §8.7): referencia y re-etiquetado.

POR QUÉ. Toda la vara del A/B son las etiquetas de la población (`lab` decide, `lab_union` informa). Si las copias de
la referencia no fueran las congeladas, o si el etiquetador no fuera el mismo instrumento que etiquetó el censo, el
veredicto mediría otra cosa sin dar error. El pre-registro pide tres pruebas:
  (a) sha256 de las dos copias congeladas (consolidado cb91eb50 y OCR cfc57c4d de Mirova-v1);
  (b) el re-etiquetado corrido dos veces da lo mismo (y lo mismo que trae poblacion_f4.json);
  (c) con la referencia sellada del censo (consolidado 47303dcd y OCR 534003b3, con las capas histórica y de respaldo
      del checkout del censo, 80b81982) reproduce las etiquetas selladas de experiments/_s162_mxd03/poblacion.json en
      las 5.465 pasadas (prueba de que el etiquetador de hoy es el mismo instrumento).
El etiquetador es `poblacion_f4.etiquetar`, que corre `poblacion_mxd03.main()` sin modificarlo.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el etiquetador hubiera cambiado, ¿se vería? Sí: (c) compara pasada por pasada contra las etiquetas selladas; una
   sola distinta deja `reetiquetado` en INDECIDIBLE.
2. Si (c) no pudiera fallar, ¿se vería? Control de poder: la misma comparación con la referencia de HOY sobre C tiene
   que dar distintas (son los cambios de etiqueta que poblacion_f4 lista); si diera 0, la comparación no distingue
   referencias y no prueba nada.

Uso: python -I reetiquetado_f4.py --ref D:/vrp-trabajo/temporales/s168_candado/ref
         --ref-censo D:/vrp-trabajo/temporales/s168_candado/ref_censo
Escribe externos_referencia.json (claves `referencia` y `reetiquetado`) y reetiquetado_f4_salida.txt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import poblacion_f4 as PF  # noqa: E402

RAIZ = PF.RAIZ
CHECKOUT_CENSO = "80b819828f16e19ceacbd21dc7c4e474d46122b4"
MANIF_CENSO = RAIZ / "experiments/_s162_mxd03/MANIFIESTO.json"


def sha256_del_blob(ruta, rev="HEAD"):
    """S168, VC169-01: el sha256 de los BYTES DEL BLOB en git (`git -c core.autocrlf=false show HEAD:<ruta>`), que es lo
    que lee el runner Linux y cualquier checkout LF. PF.sha256 sobre la copia de Windows daba el de la copia CRLF
    (5e0147b0...) y externos_f4 dejaba referencia y reetiquetado en INDECIDIBLE en un checkout LF. Devuelve
    (sha256 del blob, sha256 LF de la copia local, ruta relativa); si el blob no existe, sha256 del blob None."""
    rel = Path(ruta).resolve().relative_to(Path(RAIZ).resolve()).as_posix()
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "show", f"{rev}:{rel}"], cwd=RAIZ, capture_output=True)
    blob = hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
    return blob, PF.sha256(ruta, lf=True), rel


def etiquetas(pob_filas):
    return {k: (f["lab"], f.get("vrp_mirova")) for k, f in pob_filas.items()}


def de_poblacion_f4(pob):
    """Lo que la población trae, en la forma de dos canales: {tramo: {canal: {(vol, dt): (lab, vrp)}}}."""
    out = {"C": {"tabla": {}, "union": {}}, "E": {"tabla": {}, "union": {}}}
    for p in [p for p in pob["pasadas"] if p["tramo"] == "C"] + pob["e_candidatas"]:   # E: antes de excluir días
        k = (p["vol"], p["dt"])
        out[p["tramo"]]["tabla"][k] = (p["lab"], p["vrp_mirova"] if p["lab"] in ("protegida", "bajo1") else None)
        lu = p.get("lab_union", p["lab"])
        vu = p.get("vrp_mirova_union", p["vrp_mirova"])
        out[p["tramo"]]["union"][k] = (lu, vu if lu in ("protegida", "bajo1") else None)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--ref-censo", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion_f4.json"))
    ap.add_argument("--salida", default=str(AQUI / "externos_referencia.json"))
    a = ap.parse_args()
    t0 = time.time()
    L = []

    def pr(*x):
        s = " ".join(str(v) for v in x)
        L.append(s)
        print(s, flush=True)

    pr("reetiquetado_f4.py | UTC", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "| HEAD",
       PF.git("rev-parse", "HEAD"))
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    sha_blob, sha_local_lf, rel_pob = sha256_del_blob(a.poblacion)
    pr("población:", rel_pob, "| sha256 del blob en HEAD", sha_blob, "| sha256 LF de la copia local", sha_local_lf,
       "| sha256 de la copia local tal cual", PF.sha256(a.poblacion), "| checkout", pob["checkout"],
       "| head_e", pob["head_e"]["estado"])
    if sha_blob is None or sha_blob != sha_local_lf:
        pr("ALTO: la población local no es el blob de HEAD (sin commitear o cambiada); no se registra un sha que el "
           "runner no va a ver")
        (AQUI / "reetiquetado_f4_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
        sys.exit(3)

    # ---------------- (a) referencia congelada
    ref = PF.bajar_ref(a.ref, sin_bajar=True)
    filas_a = {}
    ok_a = True
    for n in PF.NOMBRES:
        r = ref[n]
        reg = pob["referencia"][n]
        igual_pob = r["sha256"] == reg["sha256"] and r["sha_commit"] == reg["sha_commit"]
        ok_a &= bool(r["igual_a_s165"]) and igual_pob
        filas_a[n] = {"sha_commit": r["sha_commit"], "sha256": r["sha256"], "sha256_lf": r["sha256_lf"],
                      "bytes": r["bytes"], "igual_al_sha256_de_s165": r["igual_a_s165"],
                      "igual_a_lo_que_registra_la_poblacion": igual_pob, "url": r["url"]}
        pr(f"(a) {n}: commit {r['sha_commit'][:9]} sha256 {r['sha256']} | igual a S165 {r['igual_a_s165']} | "
           f"igual a poblacion_f4.json {igual_pob}")
    referencia = {"estado": "OK" if ok_a else "INDECIDIBLE", "copias": filas_a,
                  "capas_referencia": pob.get("capas_referencia"),
                  "evidencia": "experiments/_s166_modd_f4/reetiquetado_f4_salida.txt (a)"}

    # ---------------- (b) dos corridas iguales, e iguales a la población
    desde_pob = de_poblacion_f4(pob)
    corridas = []
    for i in (1, 2):
        c = {}
        for tramo, ven in (("C", PF.VENTANA_C), ("E", PF.VENTANA_E)):
            for canal in ("tabla", "union"):
                t1 = time.time()
                pb, _log, cod = PF.etiquetar(ven, ref, canal)
                c[(tramo, canal)] = etiquetas(PF.filas_de(pb))
                pr(f"(b) corrida {i} {tramo} {canal}: {len(c[(tramo, canal)])} pasadas, código {cod}, "
                   f"{time.time() - t1:.0f} s")
        corridas.append(c)
    iguales_12 = corridas[0] == corridas[1]
    dif_pob = {}
    for (tramo, canal), et in corridas[0].items():
        pp = desde_pob[tramo][canal]
        d = sorted(k for k in set(et) | set(pp) if et.get(k) != pp.get(k))
        dif_pob[f"{tramo}_{canal}"] = d
        pr(f"(b) {tramo} {canal}: distintas contra poblacion_f4.json {len(d)} {d[:5]}")
    pr("(b) corrida 1 = corrida 2:", iguales_12)
    ok_b = iguales_12 and not any(dif_pob.values())

    # ---------------- (c) referencia sellada del censo -> etiquetas selladas del censo
    man = json.loads(MANIF_CENSO.read_text(encoding="utf-8"))
    ref_censo_spec = {n: {"sha_commit": man["referencia"][n]["sha_commit"]} for n in PF.NOMBRES}
    rc = PF.bajar_ref(a.ref_censo, ref=ref_censo_spec, sin_bajar=True)
    ok_sha_c = all(rc[n]["sha256_lf"] == man["referencia"][n]["sha256_lf"] for n in PF.NOMBRES)
    for n in PF.NOMBRES:
        pr(f"(c) {n}: commit {rc[n]['sha_commit'][:9]} sha256_lf {rc[n]['sha256_lf']} | igual al MANIFIESTO del "
           f"censo {rc[n]['sha256_lf'] == man['referencia'][n]['sha256_lf']}")
    tmp = Path(tempfile.mkdtemp(prefix="capas_censo_"))
    capas = {}
    for nom, rel in (("historico", "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"),
                     ("respaldo", "data/mirova_reference/mirova_v1_snapshot/"
                                  "registro_vrp_consolidado_respaldo_20260408.csv")):
        b = subprocess.run(["git", "show", f"{CHECKOUT_CENSO}:{rel}"], cwd=RAIZ, capture_output=True).stdout
        p = tmp / Path(rel).name
        p.write_bytes(b)
        capas[nom] = p
        pr(f"(c) capa {nom} del checkout del censo {CHECKOUT_CENSO[:9]}: {len(b)} bytes, sha256_lf "
           f"{PF.sha256(p, lf=True)}")
    pb, log, cod = PF.etiquetar(PF.VENTANA_C, rc, "union", historico=capas["historico"], respaldo=capas["respaldo"])
    nuevo = PF.filas_de(pb)
    cen = PF.filas_de(json.load(open(PF.POB_CENSO, encoding="utf-8")))
    distintas = sorted(k for k in set(cen) | set(nuevo)
                       if (cen.get(k) or {}).get("lab") != (nuevo.get(k) or {}).get("lab")
                       or (cen.get(k) or {}).get("vrp_mirova") != (nuevo.get(k) or {}).get("vrp_mirova"))
    pr(f"(c) con la referencia sellada: {len(nuevo)} pasadas (censo {len(cen)}), código {cod}; etiquetas o VRP de "
       f"MIROVA distintos de los sellados: {len(distintas)} {distintas[:5]}")
    for ln in PF.controles_del_log(log):
        pr("    ", ln)
    # control de poder: la referencia de hoy, mismo canal, sí da distintas
    poder = sorted(k for k in cen if desde_pob["C"]["union"].get(k, (None,))[0] != cen[k]["lab"])
    pr(f"(c) control de poder: con la referencia de hoy (unión) cambian {len(poder)} etiquetas de C contra el censo "
       f"(tiene que ser > 0)")
    ok_c = ok_sha_c and len(nuevo) == len(cen) and not distintas and len(poder) > 0
    for p in capas.values():
        p.unlink()
    tmp.rmdir()

    reetiquetado = {"estado": "OK" if (ok_b and ok_c) else "INDECIDIBLE",
                    "dos_corridas_iguales": iguales_12,
                    "distintas_contra_poblacion": {k: len(v) for k, v in dif_pob.items()},
                    "censo": {"sha256_lf_igual_al_manifiesto": ok_sha_c, "n_pasadas": len(nuevo),
                              "n_distintas": len(distintas), "distintas": [list(k) for k in distintas[:20]],
                              "control_de_poder_cambios_con_ref_de_hoy": len(poder)},
                    "evidencia": "experiments/_s166_modd_f4/reetiquetado_f4_salida.txt (b) y (c)"}
    out = {"referencia": referencia, "reetiquetado": reetiquetado,
           "generado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
           "poblacion_sha256": sha_blob, "poblacion_ruta": rel_pob,
           "poblacion_sha256_es": "sha256 de los bytes del blob en git (git -c core.autocrlf=false show HEAD:ruta)",
           "checkout": PF.git("rev-parse", "HEAD")}
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    pr("referencia:", referencia["estado"], "| reetiquetado:", reetiquetado["estado"], f"| {time.time() - t0:.0f} s")
    pr("escrito", a.salida)
    (AQUI / "reetiquetado_f4_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    sys.exit(0 if referencia["estado"] == reetiquetado["estado"] == "OK" else 2)


if __name__ == "__main__":
    main()
