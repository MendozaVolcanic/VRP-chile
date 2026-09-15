# -*- coding: utf-8 -*-
"""S142: linea base de sobre-publicacion re-medida solo con el regimen posterior a #535.

POR QUE. La banda de terminado de la Fase 1 (<= 10 % focales, <= 15 % nevados; spec
docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:82) se juzga contra una linea
base (63,5 % en S139). Esa linea base mezcla dos regimenes: con la mascara de nube de 260 K (hasta
#535, 2026-08-28 23:00:56 UTC) la nieve fria caia como nube, el primer pase quedaba sin fondo y la
pasada no podia publicar; esas pasadas ciegas bajaban artificialmente la tasa de publicacion en
negativos. #571 (2026-08-31 20:34:53 UTC) quito ademas el piso VRP. Un A/B de Fase 1 medido contra
la mezcla se juzga contra un numero que ya no describe produccion.

INSTRUMENTO. No se reescribe nada: se importa scripts/banco_paridad.py (predicado del dashboard
ejecutado con node, etiquetas pos / far_ref / neg_limpio / sin_info, controles P1/P2) y se corta el
resultado por tramo de NOCHE UTC. Los dos merges caen de dia en Chile (19:00 y 16:34 hora local), sin
pasadas nocturnas cerca: cortar por fecha de noche equivale a cortar por hora de merge; el script lo
comprueba pasada a pasada (`pasadas_con_tramo_discordante` debe dar 0).

Tramos:
  * antes_535_misma_longitud: tantas noches antes de #535 como noches tiene el tramo despues_571;
  * entre_535_y_571: 2026-08-29 a 2026-08-31;
  * despues_571: 2026-09-01 al ultimo dato (linea base propuesta);
  * contexto_marzo_a_535: 2026-03-01 a 2026-08-28 (lo que mezclaba la linea base S139/S140).
Referencia: remoto MendozaVolcanic/Mirova-v1 fijado a sha (bajar_remoto), fecha del commit en meta.

Fuente de verdad (regla S91): linea_base_post535.json. RESULTADOS.md se genera desde ese JSON.
USO: python experiments/_s142_linea_base/linea_base_post535.py [--fin YYYY-MM-DD] [--solo-informe]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

M535 = datetime(2026, 8, 28, 23, 0, 56, tzinfo=timezone.utc)
M571 = datetime(2026, 8, 31, 20, 34, 53, tzinfo=timezone.utc)
# Particion de regimen S131 (scripts/build_c2ab_windows.py:41-42), la misma de auto_audit_weekly.py:135-138
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
BANDA = {"focal": 0.10, "nevado": 0.15}
N_MIN = 20
OUT = HERE / "linea_base_post535.json"
MD = HERE / "RESULTADOS.md"


def _git(*args, cwd=ROOT):
    return subprocess.run(list(args), capture_output=True, text=True, check=True, cwd=cwd).stdout.strip()


def tramo_por_dt(dt):
    return "antes" if dt < M535 else ("entre" if dt < M571 else "despues")


def resumir_controles(ctrl):
    tp = {b: {"tasa_pub_neg": v["tasa_pub_neg"], "recall_pos": v["recall_pos"], "n_neg": v["n_neg_limpio"]}
          for b, v in ctrl["todo_publica"].items()}
    np_ = {b: {"tasa_pub_neg": v["tasa_pub_neg"], "recall_pos": v["recall_pos"], "n_neg": v["n_neg_limpio"]}
           for b, v in ctrl["nada_publica"].items()}
    ok_tp = all((v["tasa_pub_neg"] in (1.0, None)) and (v["recall_pos"] in (1.0, None)) for v in tp.values())
    ok_np = all((v["tasa_pub_neg"] in (0.0, None)) and (v["recall_pos"] in (0.0, None)) for v in np_.values())
    bar = ctrl["auc_barajado_por_volcan"]
    ok_bar = all(0.4 <= a <= 0.6 for a in bar.values()) if bar else None
    return {"identidad_predicado": ctrl["identidad_predicado"],
            "todo_publica": tp, "nada_publica": np_, "auc_oraculo": ctrl["auc_oraculo"],
            "auc_real_disp_v375_por_volcan": ctrl["auc_real_disp_v375_por_volcan"],
            "auc_barajado_por_volcan": bar,
            "pasa": {"identidad": ctrl["identidad_predicado"], "todo_publica_1": ok_tp, "nada_publica_0": ok_np,
                     "oraculo_1": ctrl["auc_oraculo"] == 1.0 if ctrl["auc_oraculo"] is not None else None,
                     "barajado_en_0_4_0_6": ok_bar,
                     "n_volcanes_con_auc": len(bar)}}


def medir():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args([x for x in sys.argv[1:] if x != "--solo-informe"])

    head, remoto = _git("git", "rev-parse", "HEAD"), _git("git", "ls-remote", "origin", "-h", "refs/heads/main").split()[0]
    info = bp.bajar_remoto(HERE / "_dl_referencia")
    fechas_ref = {n: _git("gh", "api", f"repos/{bp.REPO_MIROVA if hasattr(bp, 'REPO_MIROVA') else 'MendozaVolcanic/Mirova-v1'}/commits/{v['sha']}",
                          "-q", ".commit.committer.date") for n, v in info.items()}
    cons, ocr = Path(info["registro_vrp_consolidado.csv"]["path"]), Path(info["registro_vrp_ocr.csv"]["path"])

    inicio_total = "2026-03-01"
    ventana = (inicio_total, a.fin)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    identidad = bp.control_identidad_predicado()
    filas = bp.cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    ultimo_dato = max(r["noche"] for r in recs)
    ultima_ref = {b: max((f["fecha_utc"][:10] for f in filas if f["sensor_bucket"] == b), default=None)
                  for b in bp.BUCKETS}
    d_post0 = date(2026, 9, 1)
    n_noches_post = (date.fromisoformat(ultimo_dato) - d_post0).days + 1
    d_ante_fin = date(2026, 8, 28)
    d_ante_ini = d_ante_fin - timedelta(days=n_noches_post - 1)
    tramos = {
        "antes_535_misma_longitud": (d_ante_ini.isoformat(), d_ante_fin.isoformat()),
        "entre_535_y_571": ("2026-08-29", "2026-08-31"),
        "despues_571": (d_post0.isoformat(), ultimo_dato),
        "contexto_marzo_a_535": (inicio_total, "2026-08-28"),
    }
    esperado = {"antes_535_misma_longitud": "antes", "entre_535_y_571": "entre",
                "despues_571": "despues", "contexto_marzo_a_535": "antes"}

    salida = {"meta": {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": head, "origin_main": remoto, "checkout_igual_a_origin": head == remoto,
        "referencia": {n: {"sha": v["sha"], "fecha_commit": fechas_ref[n]} for n, v in info.items()},
        "ultima_fila_ref_por_sensor": ultima_ref,
        "sha_index_html": bp.sha_git(bp.HTML), "ultimo_dato_nuestro_noche": ultimo_dato,
        "n_noches_tramo_despues_571": n_noches_post, "n_filas_ref_nocturnas": n_ref,
        "merge_535_utc": M535.isoformat(), "merge_571_utc": M571.isoformat(),
        "estratos": {"focal": FOCAL, "nevado": NEVADO, "fuente": "scripts/build_c2ab_windows.py:41-42"},
        "banda_terminado": BANDA, "n_min_marca": N_MIN,
        "definiciones": {
            "tasa_pub_neg": "fraccion de pasadas neg_limpio (banco_paridad) en que el dashboard publica",
            "tasa_pub_neg_estricto_noche_volcan": "idem, sin ALERTA ni FP en la noche del volcan en ningun sensor",
            "noche_volcan": "unidad del banco: neg si hay neg_limpio y ninguna pos ni far_ref; publica si alguna pasada publica",
            "tramo": "por fecha de noche UTC; comprobado contra la hora de los merges pasada a pasada"}},
        "tramos": {}}

    for nombre, (i, f) in tramos.items():
        sel = [r for r in recs if i <= r["noche"] <= f]
        discord = sum(1 for r in sel if tramo_por_dt(r["dt"]) != esperado[nombre])
        pvb = {k: [x for x in v if i <= x[0].strftime("%Y-%m-%d") <= f] for k, v in por_vb.items()}
        sin_rec = bp.alertas_sin_record(pvb, sel)
        por_sensor, por_volcan = bp.resumen(sel, sin_rec)
        por_estrato = {}
        for est, vols in (("focal", FOCAL), ("nevado", NEVADO)):
            por_estrato[est] = {}
            for b in bp.BUCKETS + [None]:
                p, n = bp.metricas(sel, sin_rec, lambda r, b=b, vols=vols: r["vol"] in vols and (b is None or r["b"] == b))
                por_estrato[est][b or "CUALQUIERA"] = {"pasada": p, "noche_volcan": n}
        chicos = sorted(f"{v}|{b}|{u}" for v, d in por_volcan.items() for b, x in d.items() if b != "CUALQUIERA"
                        for u, nn in (("pasada", x["pasada"]["n_neg_limpio"]), ("noche", x["noche_volcan"]["n_neg"]))
                        if 0 < nn < N_MIN)
        salida["tramos"][nombre] = {
            "ventana_noches_utc": [i, f], "n_noches": (date.fromisoformat(f) - date.fromisoformat(i)).days + 1,
            "n_records_nocturnos": len(sel), "pasadas_con_tramo_discordante": discord,
            "etiquetas": dict(collections.Counter(r["lab"] for r in sel)),
            "por_sensor": por_sensor, "por_estrato": por_estrato, "por_volcan": por_volcan,
            "celdas_volcan_sensor_con_n_neg_menor_20": chicos,
            "controles": resumir_controles(bp.controles(sel, sin_rec, identidad)) if sel else None}
        s = por_sensor["VIIRS375"]["pasada"]
        print(f"{nombre} {i}..{f} recs {len(sel)} discord {discord} V375 pub_neg {s['tasa_pub_neg']} (n {s['n_neg_limpio']})")

    OUT.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    return salida


# ------------------------------------------------------------------------------------ informe
def pct(x):
    return "s/d" if x is None else f"{100 * x:.1f}".replace(".", ",") + " %"


def celda(tasa, n):
    marca = " (n<20)" if n is not None and 0 < n < N_MIN else ""
    return f"{pct(tasa)} de {n}{marca}"


def informe(d):
    T = d["tramos"]
    orden = ["antes_535_misma_longitud", "entre_535_y_571", "despues_571", "contexto_marzo_a_535"]
    m = d["meta"]
    L = []
    w = L.append
    w("# S142: linea base de sobre-publicacion, regimen posterior a #535\n")
    w("Generado por `experiments/_s142_linea_base/linea_base_post535.py` desde `linea_base_post535.json` "
      "(regla S91: ningun numero de este archivo se escribio a mano).\n")
    w("## El fenomeno\n")
    w("Hasta el PR #535 la mascara de nube de 260 K trataba la nieve fria de invierno como nube. En esas "
      "pasadas el primer pase quedaba sin pixeles de fondo y el record no podia publicar, hubiera o no calor. "
      "Eso no era precision: era ceguera, y bajaba la tasa de publicacion en pasadas donde MIROVA miro y no vio "
      "nada. Al apagar la mascara las pasadas vuelven a tener fondo y el dashboard publica en ellas como en el "
      "resto. La linea base de S139 (63,5 %) y la del auto-audit mezclan ambos regimenes, asi que "
      "subestiman lo que produccion hace hoy.\n")
    w("## Procedencia\n")
    w(f"- Checkout `{m['git_head'][:9]}`, igual a origin/main: {m['checkout_igual_a_origin']}.")
    for n, v in m["referencia"].items():
        w(f"- Referencia `{n}`: sha `{v['sha'][:9]}`, commit {v['fecha_commit']} (remoto Mirova-v1).")
    w(f"- Ultima fila de referencia por sensor: {m['ultima_fila_ref_por_sensor']}. Ultimo dato nuestro: noche {m['ultimo_dato_nuestro_noche']}.")
    w(f"- Predicado: `frontend/index.html` sha `{m['sha_index_html'][:9]}`. Estratos: `{m['estratos']['fuente']}` "
      f"(focal {', '.join(m['estratos']['focal'])}; nevado {', '.join(m['estratos']['nevado'])}).")
    w("- Tramos por noche UTC; `pasadas_con_tramo_discordante` contra la hora exacta de los merges: " +
      ", ".join(f"{k} {T[k]['pasadas_con_tramo_discordante']}" for k in orden) + ".\n")

    w("## 1. Tabla principal: publicacion en negativos limpios por sensor y tramo\n")
    w("Cada celda: tasa, de n. Pasada = variante principal del banco; estricta = sin ALERTA ni FP en la noche del volcan; "
      "noche = noche de volcan.\n")
    w("| Sensor | Tramo | Noches UTC | Pasada | Pasada estricta | Noche de volcan | Recall pasada | Recall noche | sin_info |")
    w("|---|---|---|---|---|---|---|---|---|")
    for b in bp.BUCKETS + ["CUALQUIERA"]:
        for k in orden:
            t = T[k]
            p, n = t["por_sensor"][b]["pasada"], t["por_sensor"][b]["noche_volcan"]
            w(f"| {b} | {k} | {t['ventana_noches_utc'][0]} a {t['ventana_noches_utc'][1]} ({t['n_noches']}) | "
              f"{celda(p['tasa_pub_neg'], p['n_neg_limpio'])} | "
              f"{celda(p['tasa_pub_neg_estricto_noche_volcan'], p['n_neg_estricto_noche_volcan'])} | "
              f"{celda(n['tasa_pub_neg'], n['n_neg'])} | {celda(p['recall_pos'], p['n_pos'])} | "
              f"{celda(n['recall_pos'], n['n_pos'])} | {p['n_sin_info']} |")
    w("")

    w("## 2. Estrato focal y nevado (banda de terminado: focal 10 %, nevado 15 %)\n")
    w("| Estrato | Sensor | Tramo | Pasada | Estricta | Noche de volcan | Recall noche |")
    w("|---|---|---|---|---|---|---|")
    for est in ("focal", "nevado"):
        for b in bp.BUCKETS:
            for k in orden:
                x = T[k]["por_estrato"][est][b]
                p, n = x["pasada"], x["noche_volcan"]
                w(f"| {est} | {b} | {k} | {celda(p['tasa_pub_neg'], p['n_neg_limpio'])} | "
                  f"{celda(p['tasa_pub_neg_estricto_noche_volcan'], p['n_neg_estricto_noche_volcan'])} | "
                  f"{celda(n['tasa_pub_neg'], n['n_neg'])} | {celda(n['recall_pos'], n['n_pos'])} |")
    w("")

    w("## 3. Por volcan (tramo despues_571 contra antes_535_misma_longitud)\n")
    for b in bp.BUCKETS:
        w(f"### {b}\n")
        w("| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |")
        w("|---|---|---|---|---|---|---|")
        for v in bp.VOLS:
            a_, z = T["antes_535_misma_longitud"]["por_volcan"][v][b], T["despues_571"]["por_volcan"][v][b]
            est = "focal" if v in FOCAL else "nevado"
            w(f"| {v} | {est} | {celda(a_['pasada']['tasa_pub_neg'], a_['pasada']['n_neg_limpio'])} | "
              f"{celda(z['pasada']['tasa_pub_neg'], z['pasada']['n_neg_limpio'])} | "
              f"{celda(a_['noche_volcan']['tasa_pub_neg'], a_['noche_volcan']['n_neg'])} | "
              f"{celda(z['noche_volcan']['tasa_pub_neg'], z['noche_volcan']['n_neg'])} | "
              f"{celda(z['noche_volcan']['recall_pos'], z['noche_volcan']['n_pos'])} |")
        w("")

    w("## 4. Control del instrumento por tramo\n")
    w("| Tramo | identidad predicado | todo_publica da 1 | nada_publica da 0 | AUC oraculo 1 | barajado en [0,4; 0,6] | volcanes con AUC |")
    w("|---|---|---|---|---|---|---|")
    for k in orden:
        c = T[k]["controles"]["pasa"]
        w(f"| {k} | {c['identidad']} | {c['todo_publica_1']} | {c['nada_publica_0']} | {c['oraculo_1']} | "
          f"{c['barajado_en_0_4_0_6']} | {c['n_volcanes_con_auc']} |")
    w("\nAUC barajado y real (magnitud del display V375, por volcan) en despues_571: "
      f"barajado {T['despues_571']['controles']['auc_barajado_por_volcan']}; real {T['despues_571']['controles']['auc_real_disp_v375_por_volcan']}.\n")

    w("## 5. Caveats medidos\n")
    for k in orden:
        t = T[k]
        w(f"- **{k}**: {t['n_records_nocturnos']} pasadas nocturnas; etiquetas {t['etiquetas']}; "
          f"celdas volcan-sensor con 0 < n_neg < 20: {len(t['celdas_volcan_sensor_con_n_neg_menor_20'])}.")
    w(f"\nCeldas chicas en despues_571: {', '.join(T['despues_571']['celdas_volcan_sensor_con_n_neg_menor_20'])}.\n")
    interpretacion(d, w)
    return "\n".join(L)


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return c - h, c + h


def interpretacion(d, w):
    T = d["tramos"]
    post, ante, ctx = T["despues_571"], T["antes_535_misma_longitud"], T["contexto_marzo_a_535"]

    def linea(x, clave_n="n_neg_limpio", clave_t="tasa_pub_neg"):
        n, t = x[clave_n], x[clave_t]
        lo, hi = wilson(round(t * n), n) if t is not None else (None, None)
        return f"{pct(t)} de {n} (IC 95 % Wilson {pct(lo)} a {pct(hi)})"

    w("## 6. Lectura\n")
    w("**Que muestra el corte.** En VIIRS 375 m el salto es de regimen, no de estacion: el tramo de 15 noches "
      f"inmediatamente anterior a #535 (mismo invierno) publica en {linea(ante['por_sensor']['VIIRS375']['pasada'])} de los "
      f"negativos limpios por pasada; los tres dias entre merges ya estan en {linea(T['entre_535_y_571']['por_sensor']['VIIRS375']['pasada'])}; "
      f"y despues de #571 en {linea(post['por_sensor']['VIIRS375']['pasada'])}. Que el tramo entre merges ya este alto con el piso "
      "VRP todavia puesto atribuye el salto a la mascara (#535), no al piso (#571), igual que `experiments/_s141_ndc/regimen_535.json`. "
      "Por noche de volcan el tramo nuevo publica en "
      f"{pct(post['por_sensor']['VIIRS375']['noche_volcan']['tasa_pub_neg'])} de {post['por_sensor']['VIIRS375']['noche_volcan']['n_neg']} noches negativas: "
      "hoy toda noche en que MIROVA miro sin ver nada termina con algo publicado en el dashboard. El recall no se pago: "
      f"{pct(post['por_sensor']['VIIRS375']['noche_volcan']['recall_pos'])} de {post['por_sensor']['VIIRS375']['noche_volcan']['n_pos']} noches positivas.\n")
    w("VIIRS 750 m y MODIS no muestran escalon: VIIRS 750 "
      f"{pct(ante['por_sensor']['VIIRS750']['pasada']['tasa_pub_neg'])} antes y {pct(post['por_sensor']['VIIRS750']['pasada']['tasa_pub_neg'])} despues; "
      f"MODIS {pct(ante['por_sensor']['MODIS']['pasada']['tasa_pub_neg'])} y {pct(post['por_sensor']['MODIS']['pasada']['tasa_pub_neg'])}. "
      "SOSPECHA (no medido aca): la mascara de 260 K de #535 era la de VIIRS 375 (D14); este informe no verifico en codigo si alcanzaba a los otros sensores.\n")
    w("**Volcanes que se salen.** En VIIRS 375 los mayores saltos por pasada son focales de altura "
      f"(Lascar {pct(ante['por_volcan']['Lascar']['VIIRS375']['pasada']['tasa_pub_neg'])} a {pct(post['por_volcan']['Lascar']['VIIRS375']['pasada']['tasa_pub_neg'])}, "
      f"Lastarria {pct(ante['por_volcan']['Lastarria']['VIIRS375']['pasada']['tasa_pub_neg'])} a {pct(post['por_volcan']['Lastarria']['VIIRS375']['pasada']['tasa_pub_neg'])}) "
      f"y Tupungatito ({pct(ante['por_volcan']['Tupungatito']['VIIRS375']['pasada']['tasa_pub_neg'])} a {pct(post['por_volcan']['Tupungatito']['VIIRS375']['pasada']['tasa_pub_neg'])}), "
      "pero los tres con n menor que 20 en al menos un tramo. En MODIS la tasa focal la sostiene Puyehue-Cordon Caulle "
      f"({pct(post['por_volcan']['PuyehueCordonCaulle']['MODIS']['pasada']['tasa_pub_neg'])} de {post['por_volcan']['PuyehueCordonCaulle']['MODIS']['pasada']['n_neg_limpio']}), "
      "el campo difuso del lacolito ya descrito en A20/A68; el resto de los focales MODIS esta bajo 5 %. En VIIRS 750 Puyehue-Cordon Caulle "
      f"({pct(post['por_volcan']['PuyehueCordonCaulle']['VIIRS750']['pasada']['tasa_pub_neg'])}) e Isluga ({pct(post['por_volcan']['Isluga']['VIIRS750']['pasada']['tasa_pub_neg'])}) encabezan.\n")
    fp, nv = post["por_estrato"]["focal"]["VIIRS375"]["pasada"], post["por_estrato"]["nevado"]["VIIRS375"]["pasada"]
    w("**Linea base propuesta para la Fase 1 (tramo despues_571, noches "
      f"{post['ventana_noches_utc'][0]} a {post['ventana_noches_utc'][1]}).**\n")
    w("| Sensor | Estrato | Pasada | Noche de volcan | Banda de terminado |")
    w("|---|---|---|---|---|")
    for b in bp.BUCKETS:
        for est in ("focal", "nevado"):
            x = post["por_estrato"][est][b]
            w(f"| {b} | {est} | {linea(x['pasada'])} | {celda(x['noche_volcan']['tasa_pub_neg'], x['noche_volcan']['n_neg'])} | {pct(BANDA[est])} |")
    w("")
    w(f"Reemplazo del 63,5 % (S139) y del valor del auto-audit (`data/audit_continuous/latest.json`, ventana movil de 60 dias): "
      f"VIIRS 375 total {linea(post['por_sensor']['VIIRS375']['pasada'])}; focal {linea(fp)}; nevado {linea(nv)}. "
      f"Como referencia, el mismo instrumento sobre marzo a #535 da {linea(ctx['por_sensor']['VIIRS375']['pasada'])}, "
      "o sea la mezcla subestimaba la linea base de produccion en mas de 20 puntos.\n")
    w("**Recomendaciones.**\n")
    w("1. El auto-audit deberia fijar el inicio de su ventana de falsas publicaciones en 2026-09-01 hasta que la ventana de 60 dias "
      "quede entera dentro del regimen nuevo (a partir de fines de octubre). Con la ventana movil actual mezcla regimenes y el numero "
      "sube solo, semana a semana, sin que cambie el pipeline (A90).\n")
    w("2. La banda de terminado (10 % focal, 15 % nevado por pasada) sigue siendo defendible como destino, porque se ancla en el ~5 % de "
      "falsas que declara MIROVA (spec §2 y §7.2), no en la linea base. Lo que cambia es la distancia: hay que bajar unos 75 puntos en "
      "VIIRS 375, no 50. Y en noche de volcan la linea base es el techo, asi que todo A/B debe reportarse por pasada y por noche: un brazo "
      "que baje la tasa por pasada sin sacar ninguna noche de 100 % no cambia lo que el operador ve.\n")
    w("3. Con 15 noches por tramo la mayoria de las celdas volcan-sensor por noche tiene n < 20 (ver §5). La linea base solo es firme por "
      "sensor y por estrato. Un A/B de Fase 1 debe correr sobre al menos este mismo tramo (despues de #571) para ambos brazos y no "
      "compararse contra la mezcla de marzo.\n")
    w("**Caveats.** (a) Estacion: el tramo anterior es de la segunda quincena de agosto y el posterior de la primera de septiembre; ambos "
      "invierno, y el escalon ocurre dentro de los tres dias entre merges, lo que es dificil de explicar por estacion, pero un aporte "
      "estacional menor no esta descartado (SOSPECHA, no medido). (b) `sin_info`: en despues_571, "
      f"{post['por_sensor']['VIIRS375']['pasada']['n_sin_info']} de "
      f"{sum(post['por_sensor']['VIIRS375']['pasada'][k] for k in ('n_pos', 'n_neg_limpio', 'n_far_ref', 'n_sin_info'))} pasadas VIIRS 375 "
      f"({pct(post['por_sensor']['VIIRS375']['pasada']['n_sin_info'] / sum(post['por_sensor']['VIIRS375']['pasada'][k] for k in ('n_pos', 'n_neg_limpio', 'n_far_ref', 'n_sin_info')))}) "
      "no tienen fila CONS RUTINA con VRP 0 a +-2 min y quedan fuera del denominador; si MIROVA deja de listar pasadas de forma "
      "no aleatoria el negativo limpio podria sesgarse (SOSPECHA). (c) La referencia incluye filas del mismo dia de la corrida; las pasadas "
      "de la ultima noche que aun no tienen fila caen en `sin_info`, no en el denominador.\n")


def main():
    if "--solo-informe" in sys.argv:
        d = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        d = medir()
    MD.write_text(informe(d), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
