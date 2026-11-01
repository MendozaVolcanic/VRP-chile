# -*- coding: utf-8 -*-
"""Ensayo, SIN aplicar, del reemplazo de la serie operacional por el historico con K, los 11 juntos (1.24 b, S158).

Copia de `experiments/_s154_reproc_k/ensayo_s157/ensayo.py` (S157, los 10 sin Chillan) con dos cambios: suma
NevadosDeChillan (rearmado en #878) y acepta volcanes por argumento para correr un avance parcial. Se corre de
nuevo, completo, despues del relleno de las 31 `standard` (plan `experiments/_s157_relleno/`).

POR QUE: el reemplazo de 2025-02-15..2026-09-17 toca la serie que ve el operador. Antes de aplicarlo (paso d, en
un solo commit y con tag defensivo) se corre `scripts/reemplazar_ventana_reproceso.py` en modo ensayo para los 11
volcanes Tier A. Este script:

1. llama al `main` del script de reemplazo SIN `--aplicar` y con el tope por defecto del 2 %, un volcan a la vez,
   y deja su informe en `informe_<Volcan>.json`;
2. comprueba que el archivo operacional quedo identico (sha256 antes y despues): un ensayo que escribe no es ensayo;
3. agrega a cada informe, en `resumen.json`, lo que el conteo del script no dice: cuantas de las pasadas que se
   conservarian en C0 son `nrt` (producto de LANCE, quiza irrecuperable) o `standard` (el reproceso las perdio,
   repetir el trozo puede traerlas), por mes los records que se agregarian, y cuantos reemplazos cambian
   el campo `record.vrp_mw` o `distance_class`. OJO (verificador S157, G3): eso NO es lo que el tablero
   publica, que pasa por mirovaEqVrp; lo publicado lo cuenta `verificador/scripts/publicadas.py`.

Uso (desde la raiz del repo):
    python experiments/_s158_reemplazo/ensayo_11.py                      # los 11
    python experiments/_s158_reemplazo/ensayo_11.py NevadosDeChillan     # avance parcial
"""
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
DESDE, HASTA, PERFIL = "2025-02-15", "2026-09-17", "_s154_reproc_k_historico"
VOLCANES = ["NevadosDeChillan", "Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    resumen = {"commit_del_arbol": commit, "desde": DESDE, "hasta": HASTA, "perfil_esperado": PERFIL,
               "max_solo_operacional": 0.02, "volcanes": {}}
    elegidos = sys.argv[1:] or VOLCANES
    if any(v not in VOLCANES for v in elegidos):
        raise SystemExit(f"volcan desconocido en {elegidos}")
    resumen["parcial"] = elegidos != VOLCANES
    for v in elegidos:
        op_p = RAIZ / "data" / "mirova_equivalent" / f"{v}.json"
        re_p = RAIZ / "data" / "_s154_reproc_k_historico" / f"{v}.json"
        inf_p = AQUI / f"informe_{v}.json"
        antes = sha(op_p)
        proc = subprocess.run(
            [sys.executable, str(RAIZ / "scripts" / "reemplazar_ventana_reproceso.py"),
             "--operacional", str(op_p), "--reproceso", str(re_p), "--desde", DESDE, "--hasta", HASTA,
             "--perfil-esperado", PERFIL, "--informe", str(inf_p)],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
        despues = sha(op_p)
        if antes != despues:
            raise SystemExit(f"{v}: el archivo operacional cambio durante el ensayo")
        inf = json.loads(inf_p.read_text(encoding="utf-8"))
        if inf.get("aplicado"):
            raise SystemExit(f"{v}: el informe dice aplicado")

        op = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in json.loads(op_p.read_text(encoding="utf-8"))["records"]}
        re_ = {(r.get("datetime_utc"), r.get("sensor")): r
               for r in json.loads(re_p.read_text(encoding="utf-8"))["records"]}
        en_v = lambda k: DESDE <= (k[0] or "")[:10] <= HASTA  # noqa: E731
        solo_op_pv = Counter(op[tuple(k)].get("product_version") for k in inf["solo_operacional_claves"])
        agregados = [k for k in re_ if en_v(k) and k not in op]
        comunes = [k for k in re_ if en_v(k) and k in op]
        cambia_vrp = sum(1 for k in comunes if op[k].get("vrp_mw") != re_[k].get("vrp_mw"))
        cambia_clase = sum(1 for k in comunes if op[k].get("distance_class") != re_[k].get("distance_class"))
        resumen["volcanes"][v] = {
            "codigo_salida": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(),
            "veredicto": "REHUSADO" if proc.returncode == 2 else ("PASA" if proc.returncode == 0 else "ERROR"),
            "sha256_operacional": antes,
            "operacional_en_ventana": inf["operacional_en_ventana"], "reemplazados": inf["reemplazados"],
            "agregados": inf["agregados"], "solo_operacional": inf["solo_operacional"],
            "fraccion_solo_operacional": inf["fraccion_solo_operacional"],
            "solo_operacional_por_product_version": dict(solo_op_pv),
            "agregados_por_mes": dict(sorted(Counter(k[0][:7] for k in agregados).items())),
            "reemplazos_que_cambian_vrp_mw": cambia_vrp,
            "reemplazos_que_cambian_distance_class": cambia_clase,
            "records_antes": inf["records_antes"], "records_despues": inf["records_despues"],
        }
        print(f"{v}: {resumen['volcanes'][v]['veredicto']} | {proc.stdout.strip()}")
    (AQUI / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
