# -*- coding: utf-8 -*-
"""Rearma el JSON de NevadosDeChillan del historico con K y cuenta su cobertura (S157).

POR QUE. El historico con K (run 39125546355, perfil _s154_reproc_k_historico) dejo 6 trozos de Chillan caidos
(5 por el tope de 170 min, 1 por el runner). Se relanzaron en tres runs (39363774747, 39363796988 y 39370713699),
pero el job merge de reproc-chunked.yml escribe el archivo SOLO con los trozos de su propia corrida: cada run nuevo
dejo en main el JSON de Chillan con unicamente sus ventanas. Este script lo rearma con los 21 trozos de los cuatro
runs, usando la misma funcion de union que el workflow, y lo controla antes de que nadie lo use para el reemplazo.

QUE HACE
1. Lee cada carpeta `chunk-NevadosDeChillan-<idx>-<inicio>_<fin>` bajo `--artefactos` (una subcarpeta por run) y
   saca la ventana del nombre, igual que el paso "Unir por volcan" del workflow.
2. Exige que las ventanas cubran 2025-02-15..2026-09-17 sin huecos ni solapes.
3. Une con `merge_stores` de scripts/merge_chunk_stores.py (cada trozo aporta solo su ventana).
4. Control: los records de las ventanas del run original deben ser identicos (registro a registro) a los del
   archivo del tag `pre-s157-chillan-trozos`, que es la union que hizo el workflow con esos mismos 10 trozos.
5. Cobertura (A108): cuenta dia por dia y sensor por sensor las claves (datetime_utc, sensor) del rearmado contra
   la serie operacional data/mirova_equivalent/NevadosDeChillan.json, en la misma ventana, y ubica cada dia con
   deficit en su trozo y su run.

Uso (desde la raiz del repo):
    python experiments/_s157_chillan_rearmado/rearmar_y_contar.py --artefactos <dir> --tag-json <json del tag>
        --operacional <json operacional> [--relleno <dir de la segunda pasada>] [--escribir]

RELLENO (agregado en S157 al medir la cobertura): los 10 trozos VERDES del run original perdieron 316 pasadas
`standard` en 51 dias, porque la busqueda en CMR dio ReadTimeout y el cortacircuito de la corrida salto dias
enteros sin fallar el job (log del trozo 15: SEARCH_CMR_TIMEOUT -> breaker ON). Se despacho una segunda pasada
completa de Chillan (run 39391332259, trozos de 19 dias, mismo codigo de pipeline/) y de ella se toman SOLO las
claves (datetime_utc, sensor) que faltan en la union primaria.
Sin --escribir no toca data/. Salida: experiments/_s157_chillan_rearmado/resumen.json y cobertura.md
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
from merge_chunk_stores import merge_stores, _key  # noqa: E402

AQUI = Path(__file__).resolve().parent
VOL = "NevadosDeChillan"
DESDE, HASTA = "2025-02-15", "2026-09-17"
RUN_ORIGINAL = "39125546355"
DESTINO = RAIZ / "data" / "_s154_reproc_k_historico" / f"{VOL}.json"
PATRON = re.compile(rf"chunk-{VOL}-(\d+)-(\d{{4}}-\d\d-\d\d)_(\d{{4}}-\d\d-\d\d)$")


def trozos(raiz: Path) -> list[dict]:
    out = []
    for d in sorted(raiz.glob(f"run_*/chunk-{VOL}-*")):
        m = PATRON.match(d.name)
        if not m:
            raise SystemExit(f"nombre de trozo inesperado: {d}")
        f = d / f"{VOL}.json"
        if not f.exists():
            raise SystemExit(f"trozo sin JSON: {d}")
        out.append({"run": d.parent.name.removeprefix("run_"), "idx": int(m.group(1)),
                    "inicio": m.group(2), "fin": m.group(3), "path": f})
    out.sort(key=lambda t: t["inicio"])
    return out


def exigir_cobertura_contigua(ts: list[dict]) -> None:
    esperado = date.fromisoformat(DESDE)
    for t in ts:
        ini, fin = date.fromisoformat(t["inicio"]), date.fromisoformat(t["fin"])
        if ini != esperado:
            raise SystemExit(f"hueco o solape antes de {t['run']}/{t['idx']}: esperaba {esperado}, hay {ini}")
        esperado = fin + timedelta(days=1)
    if esperado - timedelta(days=1) != date.fromisoformat(HASTA):
        raise SystemExit(f"la union termina en {esperado - timedelta(days=1)}, no en {HASTA}")


def en_ventana(rec: dict, ini: str, fin: str) -> bool:
    f = (rec.get("datetime_utc") or "")[:10]
    return ini <= f <= fin


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artefactos", required=True, type=Path)
    ap.add_argument("--tag-json", required=True, type=Path)
    ap.add_argument("--operacional", required=True, type=Path)
    ap.add_argument("--relleno", type=Path, default=None,
                    help="carpeta con los trozos de una segunda pasada completa (run_*/chunk-...)")
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args(argv)

    ts = trozos(a.artefactos)
    exigir_cobertura_contigua(ts)
    print(f"{len(ts)} trozos, {DESDE}..{HASTA} contiguo")

    store, dup = merge_stores([t["path"] for t in ts], [(t["inicio"], t["fin"]) for t in ts])
    recs = store["records"]
    print(f"union: {len(recs)} records, {dup} duplicados entre trozos")

    # Control contra el tag: mismas ventanas del run original, mismos records.
    originales = [t for t in ts if t["run"] == RUN_ORIGINAL]
    tag = json.loads(a.tag_json.read_text(encoding="utf-8"))["records"]
    def de_original(r):
        return any(en_ventana(r, t["inicio"], t["fin"]) for t in originales)
    lado_union = {_key(r): r for r in recs if de_original(r)}
    lado_tag = {_key(r): r for r in tag}
    fuera_tag = [k for k, r in lado_tag.items() if not de_original(r)]
    distintos = [k for k in lado_tag if k in lado_union and lado_union[k] != lado_tag[k]]
    control = {
        "trozos_originales": len(originales),
        "records_tag": len(lado_tag),
        "records_union_en_ventanas_originales": len(lado_union),
        "solo_en_tag": len(set(lado_tag) - set(lado_union)),
        "solo_en_union": len(set(lado_union) - set(lado_tag)),
        "distintos": len(distintos),
        "tag_fuera_de_ventanas_originales": len(fuera_tag),
    }
    control["ok"] = (control["solo_en_tag"] == 0 and control["solo_en_union"] == 0
                     and control["distintos"] == 0 and control["tag_fuera_de_ventanas_originales"] == 0)
    print("control contra el tag:", control)

    # Relleno: una segunda pasada completa (otro run, mismo codigo) aporta SOLO las claves que faltan. Los records
    # de la union primaria no se tocan; asi una pasada que la segunda copia perdio por CMR no borra nada (A108).
    rellenadas = []
    if a.relleno:
        tr = trozos(a.relleno)
        exigir_cobertura_contigua(tr)
        store_r, _ = merge_stores([t["path"] for t in tr], [(t["inicio"], t["fin"]) for t in tr])
        presentes = {_key(r) for r in recs}
        for r in store_r["records"]:
            if _key(r) not in presentes:
                rellenadas.append(r)
        recs = sorted(recs + rellenadas, key=lambda r: r.get("datetime_utc", ""))
        store["records"] = recs
        store["updated"] = max(store.get("updated", ""), store_r.get("updated", ""))
        print(f"relleno desde {len(tr)} trozos: {len(rellenadas)} records agregados; union final {len(recs)}")

    # Cobertura contra la operacional, dia por dia y sensor por sensor.
    oper = json.loads(a.operacional.read_text(encoding="utf-8"))["records"]
    def claves(rs):
        c = defaultdict(set)
        for r in rs:
            f = (r.get("datetime_utc") or "")[:10]
            if DESDE <= f <= HASTA:
                c[(f, r.get("sensor"))].add(r.get("datetime_utc"))
        return c
    co, cr = claves(oper), claves(recs)
    por_sensor = defaultdict(lambda: {"oper": 0, "reproc": 0, "solo_oper": 0, "solo_reproc": 0})
    deficit = []
    for k in sorted(set(co) | set(cr)):
        o, r = co.get(k, set()), cr.get(k, set())
        s = por_sensor[k[1]]
        s["oper"] += len(o); s["reproc"] += len(r)
        s["solo_oper"] += len(o - r); s["solo_reproc"] += len(r - o)
        if o - r:
            t = next(t for t in ts if t["inicio"] <= k[0] <= t["fin"])
            for dt in sorted(o - r):
                rec = next(x for x in oper if x.get("datetime_utc") == dt and x.get("sensor") == k[1])
                deficit.append({"datetime_utc": dt, "sensor": k[1], "run": t["run"], "trozo": t["idx"],
                                "product_version_oper": rec.get("product_version")})
    por_mes_solo_reproc = Counter(dt[:7] for k in cr for dt in (cr[k] - co.get(k, set())))

    resumen = {
        "volcan": VOL, "ventana": [DESDE, HASTA],
        "trozos": [{k: (str(v) if k == "path" else v) for k, v in t.items() if k != "path"} for t in ts],
        "records_union": len(recs), "duplicados_entre_trozos": dup,
        "rellenadas_desde_segunda_pasada": len(rellenadas),
        "rellenadas_por_mes": dict(sorted(Counter(r["datetime_utc"][:7] for r in rellenadas).items())),
        "control_tag": control,
        "cobertura_por_sensor": dict(por_sensor),
        "pasadas_solo_en_operacional": deficit,
        "pasadas_solo_en_reproceso_por_mes": dict(sorted(por_mes_solo_reproc.items())),
    }
    (AQUI / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    filas = ["| sensor | operacional | reproceso | solo operacional | solo reproceso |", "|---|---:|---:|---:|---:|"]
    for s, v in sorted(por_sensor.items()):
        filas.append(f"| {s} | {v['oper']} | {v['reproc']} | {v['solo_oper']} | {v['solo_reproc']} |")
    filas.append("")
    filas.append("Pasadas que estan en la operacional y no en el rearmado:")
    filas.append("")
    filas += [f"- {d['datetime_utc']} {d['sensor']} (run {d['run']}, trozo {d['trozo']}, "
              f"operacional {d['product_version_oper']})" for d in deficit] or ["- ninguna"]
    (AQUI / "cobertura.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
    print("\n".join(filas[: 2 + len(por_sensor)]))
    print(f"solo en operacional: {len(deficit)}; solo en reproceso por mes: {dict(sorted(por_mes_solo_reproc.items()))}")

    if not control["ok"]:
        print("CONTROL FALLIDO: no se escribe nada", file=sys.stderr)
        return 1
    if a.escribir:
        with open(DESTINO, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        print(f"escrito {DESTINO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
