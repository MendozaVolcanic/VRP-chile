# -*- coding: utf-8 -*-
"""S141: ¿por qué subió la publicación en pasadas donde MIROVA miró y no vio nada, a fines de agosto?

POR QUÉ. En VIIRS 375 m, sobre los 11 Tier A, la fracción de negativos limpios en que el dashboard
publica pasó de ~0,6 a ~0,87 en la semana del 31 de agosto. En esa semana entraron dos cambios que
pueden explicarlo por mecanismos distintos, y cada uno deja una huella propia en los records:
  * PR #535 (2026-08-28 23:00:56 UTC) apagó en producción la máscara de nube de 260 K de VIIRS
    (D14; #537 lo documentó). Con la máscara, a esta altitud la nieve fría caía como nube y el primer
    pase se quedaba SIN FONDO: la pasada no podía publicar. Huella: antes del corte, pasadas no
    publicadas con `diag_n_bg_used_first_pass == 0`.
  * PR #571 (2026-08-31 20:34:53 UTC) quitó el piso VRP (VIIRS 375: 0,02 MW), que ponía en cero el
    `vrp_mw` y dejaba el record invisible salvo que viniera por el Test 1. Huella: después del corte,
    publicaciones con 0 < vrp_mw < 0,02 y sin `triggered_test1`.
Un cambio estacional golpearía a todos los volcanes a la vez, pero no produciría un escalón en el tramo
de tres días entre los dos merges.

INSTRUMENTO. P1: los tres tramos usan el mismo predicado del dashboard y las mismas etiquetas del banco
de paridad (scripts/banco_paridad.py). P2: si el salto viniera del piso, el tramo entre merges (máscara
apagada, piso puesto) quedaría en el nivel de antes. Límite: ese tramo tiene pocas pasadas.

Fuente de verdad de los números del informe (regla S91): escribe regimen_535.json.
USO: python experiments/_s141_ndc/regimen_535.py [--inicio 2026-08-10] [--fin 2026-09-15]
"""
import argparse
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

M535 = datetime(2026, 8, 28, 23, 0, 56, tzinfo=timezone.utc)
M571 = datetime(2026, 8, 31, 20, 34, 53, tzinfo=timezone.utc)
PISO_V375 = 0.02


def tramo(dt):
    return "1_antes_535" if dt < M535 else ("2_entre_535_y_571" if dt < M571 else "3_despues_571")


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description="Atribución del cambio de régimen de publicación (S141)")
    ap.add_argument("--inicio", default="2026-08-10")
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(bp.cargar_referencia_unificada(cons, ocr), coords, ventana)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    crudos = collections.defaultdict(list)
    for v in bp.VOLS:
        for r in json.loads((ROOT / "data" / "mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8"))["records"]:
            if bp.bucket(r.get("sensor")) == "VIIRS375":
                crudos[(v, r["datetime_utc"])].append(r)

    total = collections.defaultdict(collections.Counter)
    por_volcan = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    ambiguas = 0
    for r in recs:
        if r["b"] != "VIIRS375" or r["lab"] != "neg_limpio":
            continue
        cand = crudos.get((r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M")), [])
        if len(cand) != 1:
            ambiguas += 1
            continue
        x = cand[0]
        ciega = x.get("diag_n_bg_used_first_pass") == 0
        vrp = x.get("vrp_mw") or 0
        for c in (total[tramo(r["dt"])], por_volcan[r["vol"]][tramo(r["dt"])]):
            c["n"] += 1
            c["publicadas"] += r["pub"]
            c["ciegas"] += int(ciega)
            if r["pub"]:
                c["publicadas_bajo_piso"] += int(0 < vrp < PISO_V375)
                c["publicadas_bajo_piso_sin_test1"] += int(0 < vrp < PISO_V375 and not x.get("triggered_test1"))
            else:
                c["no_publicadas"] += 1
                c["no_publicadas_ciegas"] += int(ciega)

    def con_tasa(c):
        d = dict(c)
        d["tasa_publicacion"] = round(c["publicadas"] / c["n"], 4) if c["n"] else None
        return d

    out = {
        "meta": {"ventana": list(ventana), "referencia": {k: v["sha"] for k, v in info.items()},
                 "sha_index_html": bp.sha_git(bp.HTML), "merge_535_utc": M535.isoformat(), "merge_571_utc": M571.isoformat(),
                 "pasadas_ambiguas_excluidas": ambiguas,
                 "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "definiciones": {
            "universo": "VIIRS 375 m, 11 Tier A, pasadas nocturnas etiquetadas neg_limpio por scripts/banco_paridad.py",
            "publicada": "predicado del dashboard ejecutado con node",
            "ciega": "diag_n_bg_used_first_pass == 0",
            "publicadas_bajo_piso_sin_test1": f"publicada con 0 < vrp_mw < {PISO_V375} y sin triggered_test1: el piso la habria dejado invisible",
            "pasadas_ambiguas_excluidas": "dos records VIIRS 375 del mismo volcan a la misma hora (satelites distintos): no se puede unir sin sensor",
        },
        "total": {k: con_tasa(v) for k, v in sorted(total.items())},
        "por_volcan": {vol: {k: con_tasa(v) for k, v in sorted(t.items())} for vol, t in sorted(por_volcan.items())},
    }
    (HERE / "regimen_535.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"meta": out["meta"], "total": out["total"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
