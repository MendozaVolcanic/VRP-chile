"""Fabrica artefactos falsos de V375-B2 a partir de los del lote S162 para medir el nulo del control de vida (2.2b).

Verificador v3 del pre-registro B2. No toca nada del repo: escribe en C:/vrp-trabajo/temporales/s162_v375/verif_v3/<caso>/.

Donantes: para cada pasada de B2 (ids 3000 a 4199) se toma un record ok de neg_resto de S162 DEL MISMO VOLCAN (la grilla
es fija por volcan, comprobado), se le cambia el id y se copia su grilla byte a byte (mismo sha256, asi la cache de S162
se puede trasladar al id nuevo y el recalculo 2.1 sale honesto). El CTL (5000 a 5019) copia el record de su id_ref.

Casos (--caso):
  sano          todo copiado tal cual                              -> esperado: instrumento OK, VEREDICTO B != INVALIDO
  muerto        M14 npix 0 / vrp None en TODO B2 y CTL             -> esperado: INVALIDO (control_vida)
  todo          M14 caliente fijo en TODO B2 y CTL                 -> esperado: INVALIDO (control_vida)
  magx2         M14 vrp x 2, npix igual, en TODO B2 y CTL          -> esperado: INVALIDO (control_vida)
  magx1e7       M14 vrp x (1 + 1e-7) (bajo la tolerancia 1e-6 MW)  -> esperado: pasa (limite declarado del control)
  caida_ctl3    sano, 3 CTL con estado error                       -> esperado: INVALIDO (control_vida, 17 de 20)
  caida_ctl2    sano, 2 CTL con estado error                       -> esperado: pasa (18 de 20, por diseno)
  caida_lote12  sano, 12 % del lote S162b con estado error         -> esperado: VEREDICTO B = NO DECIDE
  sin_ctl       sano pero sin ningun artefacto del CTL             -> esperado: INVALIDO (0 de 20)
  muerto_solo_ctl  M14 muerto SOLO en el CTL, lote sano            -> esperado: INVALIDO (control_vida)
  muerto_ctl_mitad M14 muerto en 10 de 20 del CTL (las con pixeles sanas, las otras muertas)... ver codigo

--cache-envenenada: la cache del caso lleva, para cada grilla fabricada, el port FABRICADO (simula que el codigo del
evaluador esta roto igual que el del runner: el recalculo 2.1 no puede verlo). Sin esa opcion, la cache lleva el port
del donante (recalculo honesto de S162 trasladado) y 2.1 tambien dispara en los casos rotos.
"""
import argparse
import copy
import json
import random
import shutil
from pathlib import Path

ART162 = Path("C:/vrp-trabajo/temporales/s162_v375/run_40116289866")
AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent.parent          # experiments/_s162_v375
SALIDA = Path("C:/vrp-trabajo/temporales/s162_v375/verif_v3")
CACHE_ORIG = AQUI / "cache_lote_copia.json"


def leer_s162():
    R, G = {}, {}
    for f in sorted(ART162.rglob("resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in R:
                R[r["id"]] = r
    for g in ART162.rglob("grilla_*.npz"):
        G[int(g.stem.split("_")[1])] = g
    return R, G


M14_MUERTO = {"modo": "M14", "motivo_vacio": "fabricado_muerto", "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0,
              "vrp_mw": None, "pixeles": [], "nan_mir": 0, "nan_tir": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", required=True)
    ap.add_argument("--cache-envenenada", action="store_true")
    ap.add_argument("--objetivos", default=str(EXP / "b2/objetivos_v375_b2.json"))
    a = ap.parse_args()
    caso = a.caso
    out = SALIDA / caso
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    R, G = leer_s162()
    o162 = {o["id"]: o for o in json.loads((EXP / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]}
    b2 = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))["pasadas"]
    cache = json.loads(CACHE_ORIG.read_text(encoding="utf-8"))
    cache_nueva = {}
    donantes = {}
    for i, r in R.items():
        if r["estado"] == "ok" and o162[i]["clase"] == "neg_resto":
            donantes.setdefault(o162[i]["volcan"], []).append(i)
    rng = random.Random(7)
    # el M14 caliente fijo para «todo»: el de la referencia del CTL 5000 (Lascar protegida, 5 px, 1,41 MW)
    hot = None
    for o in b2:
        if o.get("lote") == "CTL" and o["id"] == 5000:
            hot = copy.deepcopy(R[o["id_ref"]]["port"]["M14"])
    if hot is None:
        hot = copy.deepcopy(R[1047]["port"]["M14"])

    n_lote = sum(1 for o in b2 if o.get("lote") != "CTL")
    caidas_lote = set(rng.sample([o["id"] for o in b2 if o.get("lote") != "CTL"], int(round(0.12 * n_lote)))) \
        if caso == "caida_lote12" else set()
    ctl_ids = [o["id"] for o in b2 if o.get("lote") == "CTL"]
    caidas_ctl = set(ctl_ids[:3]) if caso == "caida_ctl3" else (set(ctl_ids[:2]) if caso == "caida_ctl2" else set())

    resultados = {}
    n_chunks = 48
    for n, o in enumerate(b2):
        es_ctl = o.get("lote") == "CTL"
        if es_ctl and caso == "sin_ctl":
            continue
        if es_ctl:
            don = o["id_ref"]
        else:
            lst = donantes[o["volcan"]]
            don = lst[n % len(lst)]
        r = copy.deepcopy(R[don])
        r["id"] = o["id"]
        r["volcan"], r["hora_utc"], r["granule"] = o["volcan"], o["hora_utc"], o["granule"]
        r["fabricado_de"] = don
        if o["id"] in caidas_lote or o["id"] in caidas_ctl:
            r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "b": "VIIRS375",
                 "granule": o["granule"], "estado": "error: FabricadoError: caida simulada", "fabricado_de": don}
            resultados.setdefault(n % n_chunks, []).append(r)
            continue
        m = r["port"]["M14"]
        romper = caso in ("muerto", "todo", "magx2", "magx1e7") or (caso == "muerto_solo_ctl" and es_ctl) or (
            caso == "muerto_ctl_mitad" and es_ctl and (o["id"] % 2 == 1))
        if romper:
            if caso in ("muerto", "muerto_solo_ctl", "muerto_ctl_mitad"):
                r["port"]["M14"] = copy.deepcopy(M14_MUERTO)
            elif caso == "todo":
                r["port"]["M14"] = copy.deepcopy(hot)
            elif caso == "magx2" and m["vrp_mw"] is not None:
                m["vrp_mw"] = m["vrp_mw"] * 2
            elif caso == "magx1e7" and m["vrp_mw"] is not None:
                m["vrp_mw"] = m["vrp_mw"] * (1 + 1e-7)
        resultados.setdefault(n % n_chunks, []).append(r)
        # grilla: copia byte a byte del donante (mismo sha256)
        d = out / f"s162-v375-b2-{n % n_chunks}"
        d.mkdir(exist_ok=True)
        shutil.copyfile(G[don], d / f"grilla_{o['id']:04d}.npz")
        # cache trasladada: la clave de S162 es "don|sha"; la nueva, "id|sha"
        for k, v in cache.items():
            if k.startswith(f"{don}|"):
                sha = k.split("|")[1]
                vv = copy.deepcopy(v)
                if a.cache_envenenada:
                    vv["M14"] = copy.deepcopy(r["port"]["M14"])
                cache_nueva[f"{o['id']}|{sha}"] = vv
    for c, lst in resultados.items():
        d = out / f"s162-v375-b2-{c}"
        d.mkdir(exist_ok=True)
        (d / f"resultados_VIIRS375_{c:02d}.json").write_text(json.dumps(lst, default=float), encoding="utf-8")
    cache_nueva.update(cache)   # la de S162 y S159, intacta
    (out / "cache.json").write_text(json.dumps(cache_nueva), encoding="utf-8")
    tot = sum(len(v) for v in resultados.values())
    print(f"caso {caso}: {tot} records en {len(resultados)} trozos; cache {len(cache_nueva)} claves; "
          f"caidas lote {len(caidas_lote)}, caidas ctl {len(caidas_ctl)}; envenenada={a.cache_envenenada}; -> {out}")


if __name__ == "__main__":
    main()
