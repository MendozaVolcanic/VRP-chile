# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos. Paso 0 (local): arma la lista EXACTA de pasadas y la deja en
pasadas.json, antes de correr nada. La lista es parte del pre-registro.

POR QUE ASI. Las 42 alertas de VIIRS 375 que la conectiva `max` pierde salen de
experiments/_s150_debiles/filas.json, pero los controles negativos (pasadas donde MIROVA miro y no
vio nada) no estan en ese archivo: hay que reconstruir la tabla por pasada de los dos brazos. Se
reconstruye con el MISMO instrumento del informe S150 (armar_tabla.py del pre-registro S149, predicado
del tablero ejecutado con node), sobre las MISMAS salidas (ramas origin/s146-ab/<run>, leidas con
`git archive`, que no toca el arbol de trabajo) y las MISMAS referencias congeladas.

CONTROL DE REPRODUCCION (las dos preguntas del instrumento, version seleccion):
  - si el pareo estuviera roto, el conteo de perdidas no daria 42 en VIIRS 375 (S150 §2) ni 32 con
    etiqueta confiable (S150 §0.1), y el de alertas publicadas por B no daria 988 / 946 conservadas;
  - las 42 claves tienen que ser exactamente las de filas.json.
Si algo no cuadra, el script termina con error y no escribe pasadas.json.

  python seleccionar_pasadas.py --tmp <dir temporal FUERA del repo> --indice <index.csv del archivo de TIF>

El indice de TIF se baja fijado por sha (nunca pull ni clone de mirova-tif-archive, 17 GB):
  gh api -H "Accept: application/vnd.github.raw" \
    "repos/MendozaVolcanic/mirova-tif-archive/contents/index.csv?ref=<sha>" > index.csv
"""
import argparse, collections, io, json, random, subprocess, sys, tarfile
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402

PRE = RAIZ / "experiments" / "_s149_prereg_invierno"
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
MESES = {   # igual que experiments/_s150_debiles/extraer_y_tabular.py (el run posterior pisa)
    "abril": ("2026-04-01", "2026-04-30", ["35639417826", "37823348991"]),
    "mayo": ("2026-05-01", "2026-05-31", ["35599902448"]),
    "junio": ("2026-06-01", "2026-06-30", ["35675490175"]),
    "julio": ("2026-07-01", "2026-07-31", ["35728617326"]),
    "agosto": ("2026-08-01", "2026-08-27", ["35759688167"]),
}
# S150 §2 y sigma_residual.py: filas OCR con la imagen de otra pasada.
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}
OCR_CONFIABLE_DESDE = "2026-06-13"   # A119: OCR sin distancia medida hasta el 2026-06-13
SHA_INDICE_TIF = "3660cdfa77bdb177ce7de7f2743a1161f0736ef7"   # ultimo commit que toca index.csv (gh api, 2026-10-09)
TIF2VOL = {"ChillanNevadosde": "NevadosDeChillan"}
TOL_TIF_S = 180          # S150 §5: pareo por acquisition_utc a +-180 s
SEMILLA = 150
POR_PERDIDA = {"conservada_debil": 2, "residual_apagado": 2, "residual_sobrevive": 1, "negativo_b_no_publica": 1}
TAM_LOTE = 12
N_MUESTRA_D22 = 80      # de los 271: con 80, error estandar de una tasa de 25 % cerca de 5 puntos


def extraer(tmp):
    for mes, (_, _, runs) in MESES.items():
        base = tmp / mes
        for r in runs:
            for perfil in (B, F):
                ruta = "experiments/_s146_ab_sin_test1/salidas/%s/%s" % (r, perfil)
                ls = subprocess.run(["git", "ls-tree", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ,
                                    capture_output=True, text=True).stdout
                if not ls.strip():
                    continue
                tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ,
                                     capture_output=True, check=True).stdout
                with tarfile.open(fileobj=io.BytesIO(tar)) as t:
                    for m in t.getmembers():
                        if m.isfile() and m.name.endswith(".json"):
                            dst = base / perfil / Path(m.name).name
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            dst.write_bytes(t.extractfile(m).read())


def tabular(tmp):
    for mes, (d0, d1, _) in MESES.items():
        base = tmp / mes
        out = base / "tabla.json"
        if out.exists():
            continue
        C = PRE / "_congelado" / mes
        p = subprocess.run([sys.executable, str(PRE / "armar_tabla.py"), "--control", str(base / B),
                            "--brazo", str(base / F), "--cons", str(C / "registro_vrp_consolidado.csv"),
                            "--ocr", str(C / "registro_vrp_ocr.csv"), "--desde", d0, "--hasta", d1,
                            "--out", str(out)], capture_output=True, text=True, encoding="utf-8")
        print("tabla", mes, p.stdout.strip(), "| rc", p.returncode)
        if p.returncode:
            print(p.stderr[-3000:])
            sys.exit(1)


def crudos(d):
    out = {}
    for p in Path(d).glob("*.json"):
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            if bp.bucket(r.get("sensor")) == "VIIRS375":
                out["%s|VIIRS375|%s" % (p.stem, r.get("datetime_utc"))] = r
    return out


def camino_b(r):
    """Misma regla que experiments/_s150_debiles/clases_rechazo.camino y que el verificador D22 (anexo):
    camino D22 = B sin ningun pixel del primer pase en la escena y el pixel publicado mas caliente a menos
    de 3 K sobre el fondo (la compuerta lo bloquea en los dos brazos; solo el segundo pase lo rescata)."""
    if r.get("diag_n_first_pass_pixels"):
        return "primer_pase"
    bts = [q.get("bt_k") for q in (r.get("anomaly_pixels") or []) if q.get("bt_k") is not None]
    tbg = r.get("t_bg_k")
    if bts and tbg and (max(bts) - tbg) < 3.0:
        return "d22"
    return "segundo_pase_3k_o_mas"


def amplio_d22(r):
    """Criterio amplio del verificador D22 (H4): algun pixel publicado de B a menos de 3 K del fondo."""
    bts = [q.get("bt_k") for q in (r.get("anomaly_pixels") or []) if q.get("bt_k") is not None]
    tbg = r.get("t_bg_k")
    return bool(bts and tbg and (min(bts) - tbg) < 3.0)


def resumen_record(r):
    pc = r.get("primary_cluster") or {}
    return {
        "granule": r.get("granule"), "sensor": r.get("sensor"), "product_version": r.get("product_version"),
        "sensor_zenith_deg": r.get("sensor_zenith_deg"), "t_bg_k": r.get("t_bg_k"),
        "diag_mu_dnti": r.get("diag_mu_dnti"), "diag_sd_dnti": r.get("diag_sd_dnti"),
        "diag_mu_deti": r.get("diag_mu_deti"), "diag_sd_deti": r.get("diag_sd_deti"),
        "diag_n_bg_used_first_pass": r.get("diag_n_bg_used_first_pass"),
        "diag_n_first_pass_pixels": r.get("diag_n_first_pass_pixels"),
        "diag_n_second_pass_recapture": r.get("diag_n_second_pass_recapture"),
        "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"), "pc_n": pc.get("n_pixels"),
        "pc_vrp_mw": pc.get("vrp_mw"), "pc_dist_km": pc.get("centroid_dist_km"),
        "distance_class": r.get("distance_class"), "final_hotspot_source": r.get("final_hotspot_source"),
        "anomaly_pixels": [{k: q.get(k) for k in ("lat", "lon", "dist_km", "bt_k", "vrp_mw")}
                           for q in (r.get("anomaly_pixels") or [])],
    }


def indice_tif(ruta):
    import pandas as pd
    ix = pd.read_csv(ruta)
    ix = ix[(ix.sensor == "VIIRS375") & ix.acquisition_utc.notna() & (ix.size_bytes > 0)].copy()
    ix["t"] = pd.to_datetime(ix.acquisition_utc, utc=True, errors="coerce")
    ix["vol"] = ix.volcano.map(lambda v: TIF2VOL.get(v, v))
    horas_por_md5 = ix.groupby("md5")["t"].nunique()
    ix["md5_reusado"] = ix.md5.map(lambda m: bool(horas_por_md5[m] > 1))
    return ix


def parear_tif(ix, vol, dt):
    g = ix[ix.vol == vol]
    if g.empty:
        return None
    d = (g.t - dt).abs().dt.total_seconds()
    g = g.assign(dt_s=d)[d <= TOL_TIF_S].sort_values("dt_s")
    if g.empty:
        return None
    x = g.iloc[0]
    return {"tif_path": x.tif_path, "acquisition_utc": x.acquisition_utc, "dt_s": float(x.dt_s), "md5": x.md5,
            "md5_reusado": bool(x.md5_reusado), "usable": not bool(x.md5_reusado),
            "n_candidatos": int(len(g))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--indice", required=True)
    a = ap.parse_args()
    tmp = Path(a.tmp)
    extraer(tmp)
    tabular(tmp)
    ix = indice_tif(a.indice)
    filas_s150 = {r["clave"]: r for r in json.load(open(AQUI.parent / "_s150_debiles" / "filas.json", encoding="utf-8"))}
    perd_s150 = {k for k, r in filas_s150.items() if r["perdida"] and r["b"] == "VIIRS375"}

    pools = collections.defaultdict(list)    # grupo -> [pasada]
    noches_f = collections.defaultdict(set)  # (volcan, fecha UTC) -> claves que F publica, cualquier sensor
    totales = collections.Counter()
    pub_b = cons_f = 0
    for mes in MESES:
        T = json.loads((tmp / mes / "tabla.json").read_text(encoding="utf-8"))["pasadas"]
        rb, rf = crudos(tmp / mes / B), crudos(tmp / mes / F)
        for k, v in T.items():
            if len(v) == 2 and v["brazo"]["pub"]:          # cualquier sensor: la unidad del operador es la noche
                vv, _, dd = k.split("|")
                noches_f[(vv, dd[:10])].add(k)
        for k, v in T.items():
            if "|VIIRS375|" not in k or len(v) != 2:
                continue
            c, f = v["control"], v["brazo"]
            if c["lab"] == "pos" and c["pub"]:
                pub_b += 1; cons_f += bool(f["pub"])
            if c["lab"] == "pos" and c["pub"] and not f["pub"]:
                g = "perdida"
            elif c["lab"] == "pos" and c["pub"] and f["pub"] and (c.get("vrp_ref") if c.get("vrp_ref") is not None else 9) < 0.10:
                g = "conservada_debil"
            elif c["lab"] == "neg_limpio" and c["pub"] and not f["pub"]:
                g = "residual_apagado"
            elif c["lab"] == "neg_limpio" and c["pub"] and f["pub"]:
                g = "residual_sobrevive"
            elif c["lab"] == "neg_limpio" and not c["pub"] and not f["pub"]:
                g = "negativo_b_no_publica"
            elif c["lab"] == "neg_limpio" and not c["pub"] and f["pub"]:
                g = "negativo_solo_f_publica"
            else:
                continue
            totales[g] += 1
            xb, xf = rb.get(k), rf.get(k)
            if xb is None or xf is None:
                continue
            vol, _, dts = k.split("|")
            dt = datetime.strptime(dts, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            solo_ocr = bool(c.get("alerta_solo_ocr"))
            confiable = None
            if c["lab"] == "pos":
                confiable = (k not in MALAS) and (not solo_ocr or dts[:10] >= OCR_CONFIABLE_DESDE)
            pools[g].append({
                "clave": k, "vol": vol, "mes": mes, "pasada_utc": dts, "grupo": g,
                "camino_b": camino_b(xb), "noche_utc": dts[:10],
                "plataforma": xb.get("sensor"), "granule": xb.get("granule"),
                "etiqueta": c["lab"], "vrp_mirova_mw": c.get("vrp_ref"), "solo_ocr": solo_ocr,
                "fila_mala": k in MALAS, "etiqueta_confiable": confiable,
                "B": resumen_record(xb), "F": resumen_record(xf),
                "tif": parear_tif(ix, vol, dt),
            })

    # --- control de reproduccion ---
    perd = {p["clave"] for p in pools["perdida"]}
    n_conf = sum(1 for p in pools["perdida"] if p["etiqueta_confiable"])
    print("B publica alertas VIIRS 375:", pub_b, "| F conserva:", cons_f, "| esperado 988 / 946 (S150 §1)")
    print("perdidas VIIRS 375:", len(perd), "(esperado 42) | con etiqueta confiable:", n_conf, "(esperado 32)")
    print("iguales a filas.json:", perd == perd_s150, "| solo aca:", sorted(perd - perd_s150), "| solo en filas.json:", sorted(perd_s150 - perd))
    print("totales por grupo en la ventana (VIIRS 375, abril a agosto):", dict(totales))
    # camino D22 (verificador docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md, H4 y anexo)
    perd_d22 = [p for p in pools["perdida"] if p["camino_b"] == "d22"]
    perd_d22_conf = [p for p in perd_d22 if p["etiqueta_confiable"]]
    neg_d22 = sorted((p for p in pools["residual_apagado"] if p["camino_b"] == "d22"), key=lambda p: p["clave"])
    neg_amplio = sorted((p["clave"] for p in pools["residual_apagado"] if amplio_d22(p["B"])), key=str)
    print("perdidas por el camino D22:", len(perd_d22), "(esperado 15, S150 §3) | confiables:", len(perd_d22_conf), "(esperado 14)")
    print("negativos limpios del residual por el camino D22:", len(neg_d22), "(esperado 271) | criterio amplio:", len(neg_amplio), "(esperado 576)")
    ok = ((pub_b, cons_f, len(perd), n_conf) == (988, 946, 42, 32) and perd == perd_s150
          and (len(perd_d22), len(perd_d22_conf), len(neg_d22), len(neg_amplio)) == (15, 14, 271, 576))
    if not ok:
        print("CONTROL DE REPRODUCCION FALLIDO: no se escribe pasadas.json")
        sys.exit(2)
    # lista congelada ANTES de correr la sonda (pedido del verificador D22, H4 b)
    (AQUI / "negativos_camino_d22.json").write_text(json.dumps({
        "regla": "residual apagado (negativo limpio, B publica, F no), VIIRS 375, abril a agosto 2026; camino D22 = "
                 "B diag_n_first_pass_pixels == 0 y max(anomaly_pixels.bt_k) - t_bg_k < 3; amplio = "
                 "min(anomaly_pixels.bt_k) - t_bg_k < 3",
        "n_camino_d22": len(neg_d22), "n_amplio": len(neg_amplio),
        "camino_d22": [p["clave"] for p in neg_d22], "amplio": neg_amplio,
        "perdidas_camino_d22": sorted(p["clave"] for p in perd_d22),
        "perdidas_camino_d22_confiables": sorted(p["clave"] for p in perd_d22_conf)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    for g in pools.values():
        for p in g:
            otras = noches_f.get((p["vol"], p["noche_utc"]), set()) - {p["clave"]}
            p["f_publica_otra_pasada_esa_noche"] = bool(otras)

    # --- muestreo de controles, semilla fija, mismo volcan y mes que cada perdida ---
    rng = random.Random(SEMILLA)
    usados = set()
    elegidas = sorted(pools["perdida"], key=lambda p: p["clave"])
    for g, n_por in POR_PERDIDA.items():
        pool = sorted(pools[g], key=lambda p: p["clave"])
        rng.shuffle(pool)
        for per in sorted(pools["perdida"], key=lambda p: p["clave"]):
            for nivel in ("vol_mes", "vol", "cualquiera"):
                cand = [p for p in pool if p["clave"] not in usados and (
                    (nivel == "vol_mes" and p["vol"] == per["vol"] and p["mes"] == per["mes"]) or
                    (nivel == "vol" and p["vol"] == per["vol"]) or nivel == "cualquiera")]
                faltan = n_por - sum(1 for e in elegidas if e.get("pareada_con") == per["clave"] and e["grupo"] == g)
                for p in cand[:faltan]:
                    q = dict(p); q["pareada_con"] = per["clave"]; q["nivel_pareo"] = nivel
                    elegidas.append(q); usados.add(p["clave"])
                if sum(1 for e in elegidas if e.get("pareada_con") == per["clave"] and e["grupo"] == g) >= n_por:
                    break

    for e in elegidas:
        e["grupos"] = [e["grupo"]]
    # --- muestra UNIFORME de los negativos del camino D22 (selectividad dentro del estrato, verificador D22 H4) ---
    rng_d22 = random.Random(SEMILLA + 22)
    muestra = rng_d22.sample(neg_d22, N_MUESTRA_D22)
    por_clave = {e["clave"]: e for e in elegidas}
    for p in muestra:
        if p["clave"] in por_clave:
            por_clave[p["clave"]]["grupos"].append("muestra_negativos_d22")
        else:
            q = dict(p); q["grupo"] = "muestra_negativos_d22"; q["grupos"] = ["residual_apagado", "muestra_negativos_d22"]
            elegidas.append(q); por_clave[q["clave"]] = q

    # --- lotes por volcan (un job de CI por lote) ---
    por_vol = collections.defaultdict(list)
    for e in elegidas:
        por_vol[e["vol"]].append(e)
    lote = 0
    for vol in sorted(por_vol):
        xs = sorted(por_vol[vol], key=lambda e: e["pasada_utc"])
        for i in range(0, len(xs), TAM_LOTE):
            for e in xs[i:i + TAM_LOTE]:
                e["lote"] = lote
            lote += 1

    c = collections.Counter(g for e in elegidas for g in e["grupos"])
    print("muestra D22 ya presente en la seleccion previa:", sum(1 for e in elegidas if "muestra_negativos_d22" in e["grupos"] and e["grupo"] != "muestra_negativos_d22"))
    print("perdidas D22 cuya noche ya tiene otra publicacion de F:", sum(1 for e in elegidas if e["grupo"] == "perdida" and e["camino_b"] == "d22" and e["f_publica_otra_pasada_esa_noche"]), "de", sum(1 for e in elegidas if e["grupo"] == "perdida" and e["camino_b"] == "d22"))
    con_tif = collections.Counter(e["grupo"] for e in elegidas if e["tif"])
    tif_ok = collections.Counter(e["grupo"] for e in elegidas if e["tif"] and e["tif"]["usable"])
    print("elegidas por grupo:", dict(c))
    print("con TIF pareado a +-%d s:" % TOL_TIF_S, dict(con_tif), "| usables (md5 no reusado):", dict(tif_ok))
    print("perdidas confiables con TIF usable:", sum(1 for e in elegidas if e["grupo"] == "perdida" and e["etiqueta_confiable"] and e["tif"] and e["tif"]["usable"]))
    print("pareo de controles por nivel:", dict(collections.Counter((e["grupo"], e.get("nivel_pareo")) for e in elegidas if e["grupo"] != "perdida")))
    print("lotes:", lote, "| pasadas:", len(elegidas))
    salida = {"semilla": SEMILLA, "por_perdida": POR_PERDIDA, "n_muestra_d22": N_MUESTRA_D22,
              "n_negativos_camino_d22": len(neg_d22), "sha_indice_tif": SHA_INDICE_TIF,
              "tol_tif_s": TOL_TIF_S, "totales_ventana": dict(totales), "n_lotes": lote,
              "pasadas": sorted(elegidas, key=lambda e: (e["lote"], e["pasada_utc"]))}
    (AQUI / "pasadas.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito pasadas.json")


if __name__ == "__main__":
    main()
