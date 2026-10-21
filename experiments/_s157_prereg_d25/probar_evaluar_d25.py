# -*- coding: utf-8 -*-
"""S157, tarea 1.29, candado. Prueba de evaluar_d25.py ANTES de despachar: cada veredicto que el evaluador puede dar
tiene que poder salir con un caso que lo produce, y cada caso tiene que fallar por la razón que dice (A110, A116,
S140). Los brazos se fabrican desde los records con K en disco (la copia unida de sustrato_k.py: histórico con K antes
del 2026-09-18, producción desde ahí), con la línea FLAGS_BRAZO igual que la escribe el workflow.

Casos V1 (ventana de prueba 2026-09-18 a 2026-10-18, donde producción ya es K; 7 volcanes):
  nulo            K, K' y D idénticos (D con la huella de D25)            -> controles OK, P1 sin pérdidas, P2 EMPATE,
                                                                              M sin MEJORA ni EMPEORA, SIN EFECTO
  modis           D trae un record MODIS                                  -> cableado de D roto, INDECIDIBLE
  huella          D sin la huella de D25                                  -> cableado de D roto
  flag            el log de D dice D25 de VIIRS 750 apagado               -> cableado de D roto
  determ          K' cambia la publicación en 100 pasadas VIIRS 375       -> determinismo FALLA, INDECIDIBLE
  mejora750       D lleva VIIRS 750 a mitad de camino hacia MIROVA (log)  -> M VIIRS 750 MEJORA, estado MEJORA
  empeora750      D divide VIIRS 750 por 20                               -> M VIIRS 750 EMPEORA, DECIDE NICOLAS (H6)
  bloq_mejora     D mejora sólo VIIRS 375 sin kernel con cenit > 40°      -> la regla da MEJORA pero no cuenta: SIN EFECTO
  bloq_empeora    D multiplica por 20 sólo ese estrato                    -> EMPEORA bloquea CUMPLE: DECIDE NICOLAS (H6)
  kernel          D mejora sólo los 5 volcanes con kernel en VIIRS 375    -> informa, no decide: SIN EFECTO
  corte           D mejora sólo VIIRS 375 sin kernel con cenit de 40 a 50° -> sigue SIN EFECTO (con el corte en 50 sería MEJORA)
  veto            D apaga una protegida A de VIIRS 375 que K publica      -> P1 VETADO, NO CUMPLE (veto)
  veto_gemelo     lo mismo y K' también la apaga                          -> P1 INDECIDIBLE (ruidosa)
  snpp            D apaga una protegida que descansa sólo en OCR de SNPP  -> no veta
  p1b             D muestra bajo 1 MW una protegida que K muestra sobre 1 -> P1b la lista, estado con "decide Nicolas"
  p2              D publica en 30 negativos limpios de VIIRS 375          -> P2 PIERDE, NO CUMPLE (suma)
  p2_m_indec      lo mismo con M de VIIRS 750 INDECIDIBLE (sellada)       -> sigue NO CUMPLE (suma): H2
  un_volcan       D mejora VIIRS 750 sólo en Chillán (simétrica)          -> MEJORA de un volcán no cuenta: SIN EFECTO
Casos V2 (2026-04-01 a 2026-06-12, sin gemelo, tabla sola, dos despachos, --ruido-de):
  v2_nulo         K y D idénticos                                         -> controles OK, SIN EFECTO
  v2_veto         D apaga una protegida A                                 -> PENDIENTE DE REPETICION
  rep_si / rep_no con --repeticion que la vuelve a perder / no            -> VETADO / CUMPLE (H7)
Combinar:
  (MEJORA, MEJORA) -> CUMPLE; (MEJORA, SIN EFECTO) -> DECIDE NICOLAS; (veto, MEJORA) -> NO CUMPLE
Unidad:
  calibración     diez pasadas iguales por noche, signo al azar por noche: el bootstrap por pasada da falsos MEJORA por
                  sobre el 5 % y el de bloques no (la calibración detecta una regla mal calibrada)
  estratos, orden la función de estratos con z = 40 y 40,5, kernel y VIIRS 750; la regla más estricta entre etiquetas
  calib_simetrica lo mismo con el nulo simétrico de la adenda, con su poder
  sellada         el caso mejora750 con la calibración del texto sellado: se informa qué da (INDECIDIBLE, H1)
Los casos de magnitud corren con --calibracion simetrica (ADENDA_CALIBRACION.md): con la sellada no decide ni el
control positivo.

Uso: python probar_evaluar_d25.py <TMP>     (salida de cada caso en <TMP>/<caso>.txt; resumen por stdout)
"""
import copy
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402

TMP = Path(sys.argv[1]).resolve()
TMP.mkdir(parents=True, exist_ok=True)
VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Lastarria", "Villarrica", "PuyehueCordonCaulle", "Tupungatito"]
V1 = ("2026-09-18", "2026-10-18")
V2 = ("2026-04-01", "2026-06-12")
CORTE_V2 = "2026-05-07"
RESULTADOS = []


def base_k():
    datos, _ = S.unir_k(TMP / "k")
    return datos


def cargar(datos, vols, desde, hasta):
    out = {}
    for v in vols:
        p = Path(datos) / (v + ".json")
        recs = json.load(open(p, encoding="utf-8"))["records"] if p.exists() else []
        out[v] = [r for r in recs if desde <= r["datetime_utc"][:10] <= hasta and X.bp.bucket(r.get("sensor")) in X.SENS]
    return out


def con_huella(recs):
    out = copy.deepcopy(recs)
    for v in out.values():
        for r in v:
            if r.get("primary_cluster"):
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
    return out


def escribir(caso, arms, flags=None, partir=None):
    """arms: {'K': recs, 'G': recs, 'D': recs}. Escribe raiz/<perfil>/<vol>.json y logs con FLAGS_BRAZO."""
    raices = []
    tramos = [(None, None)] if not partir else [("0000", partir), (partir + "z", "9999")]
    for i, (a, b) in enumerate(tramos):
        raiz = TMP / caso / ("raiz%d" % i)
        if raiz.exists():
            shutil.rmtree(raiz)
        (raiz / "logs").mkdir(parents=True)
        for n, recs in arms.items():
            (raiz / X.BRAZOS[n]).mkdir()
            for v, rr in recs.items():
                sel = [r for r in rr if a is None or a <= r["datetime_utc"][:10] <= b]
                json.dump({"records": sel}, open(raiz / X.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
                fl = dict(X.DECLARADO[n], PROFILE_NAME=X.BRAZOS[n], DATA_SUBDIR=X.BRAZOS[n])
                if flags and n in flags:
                    fl.update(flags[n])
                (raiz / "logs" / ("%s_%s.log" % (X.BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n", encoding="utf-8")
        raices.append(raiz)
    return raices


def correr(caso, raices, ventana, desde, hasta, extra=(), placebo=False):
    """S159: los casos de reglas corren con --omitir-placebo-solo-prueba (el placebo de M daría INVALIDO sobre los K
    reales, que quedan bajo MIROVA, y taparía la regla que cada caso prueba); el caso `placebo` lo corre."""
    out = TMP / caso / "out.json"
    cmd = [sys.executable, str(AQUI / "evaluar_d25.py"), "--ventana", ventana, "--out", str(out), "--tmp", str(TMP / caso / "tmp"),
           "--vols", ",".join(VOLS if ventana == "V1" else [v for v in VOLS if v != "NevadosDeChillan"]),
           "--desde", desde, "--hasta", hasta] + list(extra) + ([] if placebo else ["--omitir-placebo-solo-prueba"])
    for r in raices:
        cmd += ["--raiz", str(r), "--logs", str(r / "logs")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(p.stdout + p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError("%s: el evaluador falló\n%s" % (caso, p.stderr[-2000:]))
    return json.load(open(out, encoding="utf-8"))


def check(caso, cond, detalle):
    RESULTADOS.append((caso, bool(cond), detalle))
    print("%-14s %s  %s" % (caso, "OK   " if cond else "FALLA", detalle), flush=True)


def regla(res, r="SN"):
    return res["por_regla"][r]


def tabla_kd(caso):
    return json.load(open(TMP / caso / "tmp" / "t_K_D.json", encoding="utf-8"))["pasadas"]


def buscar(recs, clave):
    vol, b, t = clave.split("|")
    for r in recs[vol]:
        if r["datetime_utc"][:16] == t and X.bp.bucket(r.get("sensor")) == b:
            return r
    raise KeyError(clave)


def escalar(r, f):
    pc = r.get("primary_cluster") or {}
    if pc.get("vrp_mw") is not None:
        pc["vrp_mw"] = pc["vrp_mw"] * f
    if r.get("f5_core_vrp_mw") is not None:
        r["f5_core_vrp_mw"] = r["f5_core_vrp_mw"] * f


def apagar(r):
    escalar(r, 0.0)


def pares(t, filtro):
    """Claves de la tabla del nulo con alerta, publicadas por K, con VRP de MIROVA, que cumplen el filtro."""
    out = []
    for k, v in t.items():
        c = v.get("control")
        if c and c["lab"] == "pos" and c["pub"] and c["vrp_ref"] and (c["disp"] or 0) > 0 and filtro(k, c):
            out.append((k, c))
    return out


def mover(recs, sel, hacia):
    """hacia = 0,5: a mitad de camino en log hacia MIROVA; otro número: factor fijo."""
    D = copy.deepcopy(recs)
    for k, c in sel:
        f = math.sqrt(c["vrp_ref"] / c["disp"]) if hacia == "mitad" else hacia
        escalar(buscar(D, k), f)
    return D


def m_veredictos(res, r="SN"):
    return {k: v for k, v in regla(res, r)["veredicto"].items() if k.startswith("M|")}


def main():
    datos = base_k()
    base = cargar(datos, VOLS, *V1)
    D0 = con_huella(base)
    arms0 = {"K": base, "G": copy.deepcopy(base), "D": D0}
    mej = ["--calibracion", "simetrica"]   # la propuesta de ADENDA_CALIBRACION.md; la sellada se prueba aparte

    # ---- nulo
    res = correr("nulo", escribir("nulo", arms0), "V1", *V1)
    t = tabla_kd("nulo")
    mv = m_veredictos(res)
    check("nulo", res["controles_ok"] and all(res["cableado"].values()) and res["estado"].startswith("SIN EFECTO")
          and not any(v in ("MEJORA", "EMPEORA") for v in mv.values())
          and all(regla(res)["veredicto"]["P2|%s" % s] == "EMPATE" for s in X.SENS),
          "estado %s | M %s" % (res["estado"], mv))
    n_v750 = len(pares(t, lambda k, c: "|VIIRS750|" in k))
    # S159 (I2, R2-8): el mismo nulo con el placebo obligatorio. Lo que tiene que pasar: el placebo se calcula (no
    # OMITIDO) y, si da MEJORA en un estrato que decide, el veredicto es INVALIDO POR INSTRUMENTO con el motivo.
    res_p = correr("placebo", escribir("placebo", arms0), "V1", *V1, placebo=True)
    pl = regla(res_p)["veredicto"].get("PLACEBO", "")
    check("placebo", pl and not pl.startswith("OMITIDO") and (res_p["estado"].startswith("INVALIDO POR INSTRUMENTO")
                                                              if pl.startswith("INVALIDO") else pl == "OK"),
          "PLACEBO %s -> estado %s" % (pl, res_p["estado"]))
    print("   pares VIIRS 750 en el nulo: %d" % n_v750)
    json.dump({"ruido_frac": res["ruido_frac"]}, open(TMP / "ruido_v1.json", "w", encoding="utf-8"))

    # ---- cableado y controles
    Dm = copy.deepcopy(D0)
    Dm["Lascar"].append(dict(Dm["Lascar"][0], sensor="MODIS_AQUA", datetime_utc=V1[0] + " 05:00"))
    res = correr("modis", escribir("modis", dict(arms0, D=Dm)), "V1", *V1)
    check("modis", not res["cableado"]["D"] and res["estado"].startswith("INDECIDIBLE"), "cableado %s, estado %s" % (res["cableado"], res["estado"]))
    res = correr("huella", escribir("huella", dict(arms0, D=copy.deepcopy(base))), "V1", *V1)
    check("huella", not res["cableado"]["D"] and res["estado"].startswith("INDECIDIBLE"), "cableado %s" % res["cableado"])
    res = correr("flag", escribir("flag", arms0, flags={"D": {"ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750": False}}), "V1", *V1)
    check("flag", not res["cableado"]["D"] and res["estado"].startswith("INDECIDIBLE"), "cableado %s" % res["cableado"])
    G = copy.deepcopy(base)
    flips = pares(t, lambda k, c: "|VIIRS375|" in k)[:60] + [(k, v["control"]) for k, v in t.items()
                                                            if "|VIIRS375|" in k and v.get("control", {}).get("pub")][:100]
    vistos = set()
    for k, _ in flips:
        if k not in vistos:
            vistos.add(k); apagar(buscar(G, k))
    res = correr("determ", escribir("determ", dict(arms0, G=G)), "V1", *V1)
    check("determ", not res["determinismo_ok"] and res["estado"].startswith("INDECIDIBLE"), "determinismo %s (%d apagadas en K')" % (res["determinismo_ok"], len(vistos)))

    # ---- magnitud
    sel = pares(t, lambda k, c: "|VIIRS750|" in k)
    res = correr("mejora750", escribir("mejora750", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1, extra=mej)
    mv = m_veredictos(res)
    check("mejora750", "MEJORA" in (mv["M|VIIRS750|z<=40"], mv["M|VIIRS750|z>40"]) and res["estado"].startswith("MEJORA"),
          "M %s | estado %s" % ({k: v for k, v in mv.items() if "750" in k}, res["estado"]))
    res_s = correr("sellada", escribir("sellada", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1,
                   extra=["--calibracion", "sellada"])   # S159: el default ya es la simétrica (sello D-27)
    print("   sellada (calibración 'ambos'): M %s | estado %s" % ({k: v for k, v in m_veredictos(res_s).items() if "750" in k}, res_s["estado"]))
    res = correr("empeora750", escribir("empeora750", dict(arms0, D=con_huella(mover(base, sel, 1 / 20)))), "V1", *V1, extra=mej)
    mv = m_veredictos(res)
    check("empeora750", "EMPEORA" in (mv["M|VIIRS750|z<=40"], mv["M|VIIRS750|z>40"]) and res["estado"].startswith("DECIDE NICOLAS (M empeora"),
          "estado %s" % res["estado"])
    sk = lambda k, c: "|VIIRS375|" in k and k.split("|")[0] not in X.KERNEL  # noqa: E731
    sel = pares(t, lambda k, c: sk(k, c) and (c["z"] or 0) > 40)
    res = correr("bloq_mejora", escribir("bloq_mejora", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1, extra=mej)
    i = regla(res)["info"]["M|VIIRS375|sin_kernel|z>40"]
    check("bloq_mejora", i.get("regla") == "MEJORA" and m_veredictos(res)["M|VIIRS375|sin_kernel|z>40"] == "NEUTRO"
          and res["estado"].startswith("SIN EFECTO"), "regla %s, decide %s, estado %s (n %d)" % (
              i.get("regla"), m_veredictos(res)["M|VIIRS375|sin_kernel|z>40"], res["estado"], len(sel)))
    res = correr("bloq_empeora", escribir("bloq_empeora", dict(arms0, D=con_huella(mover(base, sel, 20.0)))), "V1", *V1, extra=mej)
    check("bloq_empeora", m_veredictos(res)["M|VIIRS375|sin_kernel|z>40"] == "EMPEORA" and res["estado"].startswith("DECIDE NICOLAS (M empeora"),
          "estado %s" % res["estado"])
    sel = pares(t, lambda k, c: "|VIIRS375|" in k and k.split("|")[0] in X.KERNEL)
    res = correr("kernel", escribir("kernel", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1, extra=mej)
    ik = [regla(res)["info"]["M|VIIRS375|kernel|%s" % z].get("regla") for z in ("z<=40", "z>40")]
    check("kernel", "MEJORA" in ik and res["estado"].startswith("SIN EFECTO"), "regla kernel %s, estado %s (n %d)" % (ik, res["estado"], len(sel)))
    sel = pares(t, lambda k, c: sk(k, c) and 40 < (c["z"] or 0) <= 50)
    res = correr("corte", escribir("corte", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1, extra=mej)
    check("corte", res["estado"].startswith("SIN EFECTO") and m_veredictos(res)["M|VIIRS375|sin_kernel|z<=40"] != "MEJORA",
          "estado %s, M sin kernel z<=40 %s (n mejorados %d, todos de 40 a 50°)" % (
              res["estado"], m_veredictos(res)["M|VIIRS375|sin_kernel|z<=40"], len(sel)))

    # un volcán solo (adenda, H4): D lleva hacia MIROVA sólo a Chillán en VIIRS 750
    sel = pares(t, lambda k, c: "|VIIRS750|" in k and k.startswith("NevadosDeChillan|"))
    res = correr("un_volcan", escribir("un_volcan", dict(arms0, D=con_huella(mover(base, sel, "mitad")))), "V1", *V1, extra=mej)
    notas = [regla(res)["info"]["M|VIIRS750|%s" % z].get("nota") for z in ("z<=40", "z>40")]
    check("un_volcan", res["estado"].startswith("SIN EFECTO") and any(notas), "estado %s | notas %s (n %d)" % (res["estado"], notas, len(sel)))
    # H2: un M INDECIDIBLE (calibración sellada) no esconde una suma perdida
    sel750 = pares(t, lambda k, c: "|VIIRS750|" in k)
    Dh = con_huella(mover(base, sel750, "mitad"))

    # ---- detección
    from datetime import datetime, timezone
    import evaluar_fk as E
    cfg = dict(X.VENTANAS["V1"], desde=V1[0], hasta=V1[1])
    prot = E.proteccion(set(t), E.archivos_ref(cfg, TMP / "nulo" / "tmp"), *V1)
    publ = [(k, v["control"]) for k, v in t.items() if "|VIIRS375|" in k and len(v) == 2 and v["control"]["pub"] and prot[k]["A"]]
    normal = [(k, c) for k, c in publ if not E.ocr_snpp(k, c, prot)]
    snpp = [(k, c) for k, c in publ if E.ocr_snpp(k, c, prot)]
    k0 = normal[0][0]
    Dv = con_huella(base); apagar(buscar(Dv, k0))
    res = correr("veto", escribir("veto", dict(arms0, D=Dv)), "V1", *V1)
    check("veto", regla(res)["veredicto"]["P1|VIIRS375"] == "VETADO" and res["estado"].startswith("NO CUMPLE (veto)"), "%s -> %s" % (k0, res["estado"]))
    Gv = copy.deepcopy(base); apagar(buscar(Gv, k0))
    res = correr("veto_gemelo", escribir("veto_gemelo", dict(arms0, D=Dv, G=Gv)), "V1", *V1)
    check("veto_gemelo", regla(res)["veredicto"]["P1|VIIRS375"] == "INDECIDIBLE", "P1 %s" % regla(res)["veredicto"]["P1|VIIRS375"])
    if snpp:
        Ds = con_huella(base); apagar(buscar(Ds, snpp[0][0]))
        res = correr("snpp", escribir("snpp", dict(arms0, D=Ds)), "V1", *V1)
        check("snpp", regla(res)["veredicto"]["P1|VIIRS375"] != "VETADO", "%s -> P1 %s" % (snpp[0][0], regla(res)["veredicto"]["P1|VIIRS375"]))
    else:
        check("snpp", False, "la ventana de prueba no trae protegidas sólo OCR de Suomi NPP publicadas en VIIRS 375")
    uno = [(k, c) for k, c in normal if (c["disp"] or 0) >= 1]
    Db = con_huella(base); escalar(buscar(Db, uno[0][0]), 0.9 / uno[0][1]["disp"])
    res = correr("p1b", escribir("p1b", dict(arms0, D=Db)), "V1", *V1)
    check("p1b", regla(res)["veredicto"]["P1b|VIIRS375"].startswith("LISTA") and "decide Nicolas" in res["estado"], "estado %s" % res["estado"])
    negs = [k for k, v in t.items() if "|VIIRS375|" in k and len(v) == 2 and v["control"]["lab"] == "neg_limpio" and not v["control"]["pub"]][:30]
    Dp = con_huella(base)
    for k in negs:
        r = buscar(Dp, k)
        r["distance_class"] = "summit"
        r["primary_cluster"] = {"n_pixels": 1, "vrp_mw": 0.5, "centroid_lat": r.get("volcano_lat"), "centroid_lon": r.get("volcano_lon"),
                                "centroid_dist_km": 0.5}
        r["f5_core_vrp_mw"] = 0.5
        r["diag_bg_vecinos_n_sin_vecinos"] = 0
    res = correr("p2", escribir("p2", dict(arms0, D=Dp)), "V1", *V1)
    check("p2", regla(res)["veredicto"]["P2|VIIRS375"] == "PIERDE" and res["estado"].startswith("NO CUMPLE (suma"), "%d negativos -> %s" % (len(negs), res["estado"]))
    for k in negs:                     # los mismos 30 negativos sobre la D que mejora VIIRS 750 (con la sellada, M INDECIDIBLE)
        r = buscar(Dh, k)
        r.update(distance_class="summit", f5_core_vrp_mw=0.5, diag_bg_vecinos_n_sin_vecinos=0,
                 primary_cluster={"n_pixels": 1, "vrp_mw": 0.5, "centroid_lat": r.get("volcano_lat"),
                                  "centroid_lon": r.get("volcano_lon"), "centroid_dist_km": 0.5})
    res = correr("p2_m_indec", escribir("p2_m_indec", dict(arms0, D=Dh)), "V1", *V1,
                 extra=["--calibracion", "sellada"])   # S159: el default ya es la simétrica (sello D-27)
    mi = [v for k, v in m_veredictos(res).items() if "750" in k]
    check("p2_m_indec", "INDECIDIBLE" in mi and res["estado"].startswith("NO CUMPLE (suma"), "M VIIRS 750 %s -> %s" % (mi, res["estado"]))

    # ---- V2
    b2 = cargar(datos, [v for v in VOLS if v != "NevadosDeChillan"], *V2)
    arms2 = {"K": b2, "D": con_huella(b2)}
    res2 = correr("v2_nulo", escribir("v2_nulo", arms2, partir=CORTE_V2), "V2", *V2, extra=["--ruido-de", str(TMP / "ruido_v1.json")])
    check("v2_nulo", res2["controles_ok"] and all(res2["cableado"].values()) and res2["estado"].startswith("SIN EFECTO"), "estado %s" % res2["estado"])
    t2 = tabla_kd("v2_nulo")
    cfg2 = dict(X.VENTANAS["V2"], desde=V2[0], hasta=V2[1])
    prot2 = E.proteccion(set(t2), E.archivos_ref(cfg2, TMP / "v2_nulo" / "tmp"), *V2)
    p2k = [k for k, v in t2.items() if "|VIIRS375|" in k and len(v) == 2 and v["control"]["pub"] and prot2[k]["A"]]
    D2 = con_huella(b2); apagar(buscar(D2, p2k[0]))
    res = correr("v2_veto", escribir("v2_veto", dict(arms2, D=D2), partir=CORTE_V2), "V2", *V2, extra=["--ruido-de", str(TMP / "ruido_v1.json")])
    check("v2_veto", res["estado"].startswith("PENDIENTE DE REPETICION"), "estado %s" % res["estado"])
    # repetición dirigida (H7): si la repetición la vuelve a perder es VETADO; si no, ruido confirmado y CUMPLE
    for caso, Dr, espera in (("rep_si", D2, "VETADO"), ("rep_no", con_huella(b2), "CUMPLE")):
        rr = escribir(caso + "_rep", {"K": b2, "D": Dr})[0]
        res = correr(caso, escribir(caso, dict(arms2, D=D2), partir=CORTE_V2), "V2", *V2,
                     extra=["--ruido-de", str(TMP / "ruido_v1.json"), "--repeticion", str(rr)])
        check(caso, regla(res)["veredicto"]["P1|VIIRS375"] == espera, "P1 %s, estado %s" % (regla(res)["veredicto"]["P1|VIIRS375"], res["estado"]))

    # ---- combinar
    falsos = {"MEJORA": {"ventana": "V1", "estado": "MEJORA", "mejora": True, "empeora": False},
              "SIN": {"ventana": "V2", "estado": "SIN EFECTO", "mejora": False, "empeora": False},
              "VETO": {"ventana": "V1", "estado": "NO CUMPLE (veto)", "mejora": False, "empeora": False}}
    for n, d in falsos.items():
        json.dump(d, open(TMP / ("c_%s.json" % n), "w", encoding="utf-8"))
    m2 = dict(falsos["MEJORA"], ventana="V2"); json.dump(m2, open(TMP / "c_MEJORA2.json", "w", encoding="utf-8"))
    c1 = X.combinar([TMP / "c_MEJORA.json", TMP / "c_MEJORA2.json"])
    c2 = X.combinar([TMP / "c_MEJORA.json", TMP / "c_SIN.json"])
    c3 = X.combinar([TMP / "c_VETO.json", TMP / "c_MEJORA2.json"])
    check("combinar", c1 == "CUMPLE" and c2.startswith("DECIDE NICOLAS") and c3.startswith("NO CUMPLE"), "%s | %s | %s" % (c1, c2, c3))

    # ---- unidad: estratos (fuente única, corte de 40° inclusive; H3, H17) y orden de veredictos (H15)
    e_ok = (X.estrato("Isluga|VIIRS375|x", 40.0) == ("VIIRS375|sin_kernel|z<=40", "decide")
            and X.estrato("Isluga|VIIRS375|x", 40.5) == ("VIIRS375|sin_kernel|z>40", "bloquea")
            and X.estrato("Villarrica|VIIRS375|x", 20.0) == ("VIIRS375|kernel|z<=40", "informa")
            and X.estrato("Villarrica|VIIRS750|x", 60.0) == ("VIIRS750|z>40", "decide")
            and X.estrato("Isluga|VIIRS375|x", None)[1] == "informa")
    check("estratos", e_ok, "z 40 -> <=40 decide; 40,5 -> >40 bloquea; kernel informa; VIIRS 750 decide")
    o_ok = (X.peor(["MEJORA", "SIN EFECTO"]) == "SIN EFECTO" and X.peor(["NO CUMPLE (veto)", "MEJORA"]).startswith("NO CUMPLE")
            and X.peor(["MEJORA", "DECIDE NICOLAS (x)"]).startswith("DECIDE"))
    check("orden", o_ok, "la regla más estricta manda entre original y SN")

    # ---- unidad: la calibración detecta una regla mal calibrada
    rng = np.random.default_rng(7)
    P, bloques = [], []
    for noche in range(15):
        e = abs(rng.normal(0, 0.05))
        for _ in range(10):                 # diez pasadas idénticas por noche: dependencia total dentro del bloque
            P.append({"k": 1.0, "m": 3.0, "d": 10 ** e}); bloques.append(noche)
    Wp, Wb = X.pesos_pasada(len(P)), X.pesos_bloque(bloques)
    fm_p, fe_p, _ = X.calibrar(P, Wp, bloques=bloques)   # bootstrap por pasada, signo por noche: mal calibrada
    fm_b, fe_b, _ = X.calibrar(P, Wb, bloques=bloques)   # bootstrap por bloques: nominal
    check("calibracion", fm_p > X.MAX_FALSOS_CALIB and fm_b <= X.MAX_FALSOS_CALIB,
          "nulo sellado: falsos MEJORA por pasada %.3f, por bloques %.3f" % (fm_p, fm_b))
    dd = np.log10(np.array([p["d"] for p in P]))     # K = 1 y MIROVA = 3: d = |log D/M| - |log K/M| = -log10 D
    dd = -dd
    sm_p, se_p, _ = X.calibrar_simetrico(dd, Wp, bloques)
    sm_b, se_b, poder = X.calibrar_simetrico(dd, Wb, bloques)
    check("calib_simetrica", sm_p > X.MAX_FALSOS_CALIB and sm_b <= X.MAX_FALSOS_CALIB and se_b <= X.MAX_FALSOS_CALIB and poder,
          "nulo simétrico: por pasada MEJORA %.3f EMPEORA %.3f; por bloques %.3f y %.3f; poder %s" % (sm_p, se_p, sm_b, se_b, poder))

    malas = [c for c, ok, _ in RESULTADOS if not ok]
    print("\nRESUMEN: %d de %d casos OK%s" % (len(RESULTADOS) - len(malas), len(RESULTADOS), "" if not malas else " | FALLAN: %s" % malas))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
