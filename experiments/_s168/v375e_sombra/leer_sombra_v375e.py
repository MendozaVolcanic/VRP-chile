# -*- coding: utf-8 -*-
"""S168 V375-E: lector de la sombra prospectiva (PREREGISTRO_E.md §9.8, §10 y §11; arreglos de S169 en §11.11).

POR QUÉ. La retrospectiva (experiments/_s168/v375e_lectura_lejana/) dejó el paquete en «CUMPLE (falta la sombra)» con
el brazo cercano, y Nicolás decidió que en la sombra decide cercano y radiante se informa al lado, rotulado «posterior a
la lectura» (§10). La sombra corre la vía «código MIROVA» hacia adelante desde el 2026-11-03, en pasadas que nadie había
visto al escribir la regla. Este lector la compara con lo que publica producción (K) y con lo que publica MIROVA, con las
MISMAS funciones de la retrospectiva (lector sellado, evaluar.py, curva_cenit.py, evaluador_comun.py, identificadas por
sha256 antes de cargarlas), para que la sombra mida lo mismo que la retrospectiva midió.

POR QUÉ el corte lo fija el lector y no quien lo corre (VS168-01, §11.8): si se pudiera elegir después de ver salidas
provisionales en qué noche termina la ventana, o desde cuál empieza, la lectura dejaría de ser una prueba. Por eso la
ventana empieza exactamente el 2026-11-03, termina en la primera noche en que se alcanza la parada, antes de la parada
no se imprime ninguna lectura, y la lectura que decide se escribe una sola vez.

Qué hace, en el orden de §11: procedencia y controles S0 a S7, S9 y S10 (si cae uno sale 3 y NO imprime nada de la
población, ni conteos), la marca de régimen S8, población por banco_paridad sobre los records de K (censo, peso 1), los
brazos cercano, radiante y P-sinfiltro desde el record de la vía (distancias_desde_record y variante del lector sellado,
predicado del tablero con node), las lecturas (a) a (d), los controles de la curva del brazo y de K, las lejanas
(informa), las mitades en lugar de A104, el borde del radio (vuelta conjunta y mixta), la regla del paquete y la parada.

Nada de pipeline/, data/ ni frontend/ se escribe. Los records y la referencia se pasan por ruta; el lector escribe el
sha256 de cada archivo que lee. Se corre desde un checkout del tag del lector (S0).

Uso: python -I leer_sombra_v375e.py --data-k <carpeta de data/mirova_equivalent> --data-sombra <carpeta de
     data/sombra_codigo_mirova> --cons <registro_vrp_consolidado.csv> --ocr <registro_vrp_ocr.csv> --hasta AAAA-MM-DD
     --commit <sha de origin/main de los records> --dir-salida <carpeta>
Salida: 0 lectura que decide escrita; 3 LECTURA NO LEGIBLE; 5 parada no alcanzada (sólo controles y contadores);
        2 la lectura de ese corte ya existe (no se vuelve a leer) o el archivo de salida ya existe.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
V375 = RAIZ / "experiments" / "_s162_v375"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(V375))

# S0: los del tag s168-v375e-cuerpo-sellado (sha256 con fin de línea LF)
SHA_DEPS = {
    V375 / "e_adenda2" / "leer_posicion_v375e.py": "a40364ab01668db5849b0fb7fb8044bafb4e75f66946132f80aa85373221ce06",
    V375 / "evaluar.py": "2126b7439809cc541d3e8c3aec26b09b0b4b02eb562ea716d165a8ab2742bc66",
    V375 / "curva_cenit.py": "7fdd8e40735b3cf9de068755126b4973fdee79df3182422add82de5a6dd84353",
    RAIZ / "scripts" / "evaluador_comun.py": "c151b29f51f61171b8fd9f115fff73856058628abf79c95da6df4242969ee5c9",
}
# S0 (VS168-04, §11.4): los módulos que etiquetan y publican, fijos al sellar este lector
SHA_SELLO_LECTOR = {
    RAIZ / "scripts" / "banco_paridad.py": "f2418f981860a784b91f12c368f6bfb298e570b040b7a173d3feb38de9d7bb3d",
    RAIZ / "scripts" / "clase_mirova.py": "efb5c6a93702070021244241d50765af9ac3ef57810e1a275c789696a6127ed0",
    RAIZ / "scripts" / "referencia_mirova_unificada.py": "0c04778552158b2d040fe3f5fa9fc906f23d7a17f91c48a90f6c045815052525",
    RAIZ / "scripts" / "auto_audit_weekly.py": "3afd3e650ac208b37196614a6c63d32495a23951c8cf089a8db0be477cac71df",
    RAIZ / "scripts" / "calidad_referencia_mirova.py": "824a7c6572f4ce30408aacb5159d2cfc482caf467c14cbdad10bcd1764d07a69",
    RAIZ / "pipeline" / "mirova_csv_loader.py": "74a08b41bfa80d9cf43e3fe66c9d9d670ad701505faf853df939bfe2c94b8673",
    RAIZ / "pipeline" / "diurno.py": "aff71c0677e05d7c900e592744fc2fdfe712968b7c30aaabb8c6cd4f649e0ddb",
    RAIZ / "frontend" / "index.html": "260b4a193075c772e02e1549566fbcbe85f608abef6131c5c808444f543e54b2",
}
DESDE_P = "2026-11-03"                 # §3.3 y §11.1: la ventana P empieza exactamente aquí
SENSOR_SNPP = "VIIRS_SNPP"             # §3.3: la ventana P es sin Suomi NPP
DECIDE = ("VIA", "cercano")            # §10: cercano decide
INFORMAN = (("VIA", "radiante"), ("VIA", "sinfiltro"))
ROTULO = {DECIDE: "cercano (decide)", ("VIA", "radiante"): "radiante (informa, posterior a la lectura)",
          ("VIA", "sinfiltro"): "P-sinfiltro (informa)"}
CLASES_DECIDEN = ("pos_prot", "pos_bajo", "neg_pub", "neg_resto", "far_tabla")
UMBRAL_COBERTURA = 0.10                # S7
TOL_UNO_KM = 0.0051                    # S3: 0,005 km del redondeo de dist_km, más la media unidad de centroid_dist_km
TOL_S4_KM = 5e-4 + 1e-9                # S4 (VS168-10): centroid_dist_km redondeado a 1e-3 km
BORDE_KM = 0.005                       # §11.5 (VA168-08)
TOL_GANANCIA_LOG10 = 0.01              # §11.6: la ganancia pareja no mueve la mediana de D más que esto
PARADA_NOCHES, PARADA_ALERTAS = 30, 40  # §11.8
REZAGO_DIAS = 2                        # S9 (VS168-05)
BASE_REGIMEN = "c42ee0eb709a9df6c6d4bef92cc6b2f6e610775d"   # S8: #926, el commit que encendió la sombra
PERFIL_K, PERFIL_VIA = "mirova_equivalent", "sombra_codigo_mirova"
IDENTIDAD_ESPERADA = ([0, 1, 1, 1, 0], [1, 0])   # S2: la misma vara que banco_paridad.controles
CUMPLE, NO_CUMPLE, NICOLAS = "CUMPLE", "NO CUMPLE", "DECIDE NICOLAS"
# §11.4 (VS168-02): lo único que se imprime de un control fuera de la lectura que decide
MOTIVO = {"S0": "una dependencia no es la del sello",
          "S1": "la ventana no es la del §11.1 o hay claves de pasada repetidas",
          "S2": "el predicado no responde a la clase o no hay pasada para comprobarlo",
          "S3": "radiante y cercano difieren con un solo alertado, o no hay caso",
          "S4": "la variante radiante no reproduce la clase del record, o no hay caso",
          "S5": "el placebo K x 1,2 publica distinto que K, o no hay caso",
          "S6": "el placebo de M da MEJORA, o el comparador no tuvo sustrato",
          "S7": "más del 10 % sin dato en una clase de las que deciden, o población vacía",
          "S9": "la referencia no llega a 2 días después de la noche del corte",
          "S10": "hay pasadas de la vía con alertados sin distancias"}
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def sha256_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def cargar_deps():
    """S0: cada dependencia se identifica ANTES de importarla; si una no es la del tag o del sello del lector, no se
    carga ninguna."""
    malos = {str(p.relative_to(RAIZ)): (sha256_lf(p) if p.exists() else None)
             for p, s in list(SHA_DEPS.items()) + list(SHA_SELLO_LECTOR.items())
             if not p.exists() or sha256_lf(p) != s}
    if malos:
        return None, malos
    spec = importlib.util.spec_from_file_location("leer_posicion_v375e", V375 / "e_adenda2" / "leer_posicion_v375e.py")
    LP = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(LP)
    import curva_cenit as CC
    import evaluador_comun as EC
    import evaluar as E
    return {"LP": LP, "E": E, "CC": CC, "EC": EC}, {}


# ---------------------------------------------------------------- población (§11.2)
def clase_de(r, ref, B, alerta_protegida):
    """La clase de §11.2 de una pasada etiquetada por banco_paridad, o None si queda fuera."""
    if r["lab"] == "pos":
        return "pos_prot" if any(alerta_protegida(f) for f in ref) else "pos_bajo"
    if r["lab"] == "neg_limpio":
        return "neg_pub" if r["pub"] else "neg_resto"
    if r["lab"] == "far_ref":
        return "far_tabla" if any(B.es_fp(f["tipo"]) and f["source"] == "CONS" for f in ref) else "far_ocr"
    return None


def poblacion(recs, por_vb, B, alerta_protegida):
    """recs: los de banco_paridad.cargar_nuestros ya etiquetados. Devuelve (población, cuántas quedan fuera por
    etiqueta, cuántas de Suomi NPP)."""
    pob, fuera, snpp = [], collections.Counter(), 0
    for r in recs:
        if r["b"] != "VIIRS375":
            continue
        if r.get("sensor") == SENSOR_SNPP:
            snpp += 1
            continue
        ref = B.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        c = clase_de(r, ref, B, alerta_protegida)
        if c is None:
            fuera[r["lab"]] += 1
            continue
        alertas = [f for f in ref if B.es_alerta(f["tipo"])]
        z = r.get("z")
        pob.append({"volcan": r["vol"], "hora_utc": r["dt"].strftime("%Y-%m-%d %H:%M"), "noche": r["noche"],
                    "sensor": r.get("sensor"), "clase": c, "protegida": c == "pos_prot",
                    "alerta_tabla": any(f["source"] == "CONS" for f in alertas),
                    "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0),
                    "z": z, "estrato": f"{r['vol']}|{'z?' if z is None else ('z<=40' if z <= 40 else 'z>40')}",
                    "pub_prod": bool(r["pub"]), "disp_k": r.get("disp"), "dist_ref": r.get("dist_ref"),
                    "lote": "P", "partida": False})
    for i, o in enumerate(pob):
        o["id"] = i
    return pob, fuera, snpp


def cargar_records(carpeta, vols, desde, hasta, solo_via=False):
    """Los VIIRS 375 de una carpeta de records, por (volcán, sensor, datetime_utc), con el sha256 de cada archivo."""
    out, shas = {}, {}
    for vol in vols:
        p = Path(carpeta) / f"{vol}.json"
        if not p.exists():
            shas[vol] = None
            continue
        shas[vol] = sha256_lf(p)
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            dt = r.get("datetime_utc") or ""
            if not (desde <= dt[:10] <= hasta) or "VIIRS" not in (r.get("sensor") or "") or "750" in r["sensor"]:
                continue
            if solo_via and r.get("via_codigo_mirova") is not True:
                continue
            out[(vol, r["sensor"], dt)] = r
    return out, shas


def clave(o):
    return (o["volcan"], o["sensor"], o["hora_utc"])


# ---------------------------------------------------------------- brazos (§11.3)
def brazos(pob, via, inner, publicar, LP, flip=frozenset()):
    """Para cada pasada con record de la vía: (publica, magnitud mostrada, npix) de cercano, radiante y P-sinfiltro, y
    las distancias. `flip`: ids de borde con la clase de cercano dada vuelta (§11.5). Las pasadas sin vía no entran."""
    arms, info, casos, idx = {}, {}, [], []
    for o in pob:
        rv = via.get(clave(o))
        if rv is None:
            continue
        inn = inner[o["volcan"]]
        npix = len(rv.get("anomaly_pixels") or [])
        d = LP.distancias_desde_record(rv) if npix else None
        info[o["id"]] = {"npix": npix, "dist": d, "dc": rv.get("distance_class"), "vrp": float(rv.get("vrp_mw") or 0)}
        arms[o["id"]] = {("VIA", "sinfiltro"): (npix > 0, float(rv.get("vrp_mw") or 0.0), npix)}
        if d is None:
            for a in (DECIDE, ("VIA", "radiante")):
                arms[o["id"]][a] = (False, 0.0, npix)
            continue
        dc = d["cercano"]
        if o["id"] in flip:
            dc = inn + 0.01 if LP.clase_dc(d["cercano"], inn) == "summit" else inn - 0.01
        for a, dist in ((DECIDE, dc), (("VIA", "radiante"), d["radiante"])):
            casos.append((LP.variante(rv, dist, inn), inn))
            idx.append((o["id"], a, npix))
    for (i, a, npix), (disp, pub) in zip(idx, publicar(casos) if casos else []):
        arms[i][a] = (bool(pub), float(disp or 0.0), npix)
    return arms, info


def borde(pob, info, inner):
    """§11.5: pasadas cuyo cercano queda a menos de 0,005 km del radio interior."""
    return sorted(o["id"] for o in pob if (info.get(o["id"]) or {}).get("dist")
                  and abs(info[o["id"]]["dist"]["cercano"] - inner[o["volcan"]]) < BORDE_KM)


def borde_mixto(pob, info, inner, ids_borde, LP):
    """§11.5 (VS168-09): la vuelta que más perjudica a cercano. Alertas de borde hoy en summit pasan a far (callan);
    las que no son alertas y hoy están en far pasan a summit (publican)."""
    por = {o["id"]: o for o in pob}
    out = []
    for i in ids_borde:
        es_alerta = por[i]["clase"] in ("pos_prot", "pos_bajo")
        cl = LP.clase_dc(info[i]["dist"]["cercano"], inner[por[i]["volcan"]])
        if (es_alerta and cl == "summit") or (not es_alerta and cl == "far"):
            out.append(i)
    return frozenset(out)


def noche_parada(pob, con_dato):
    """§11.8: la primera noche N en que hay 30 noches y 40 alertas acumuladas (pasadas con dato). Devuelve (N o None,
    contadores en N o en la última noche)."""
    por_noche = collections.Counter()
    for o in pob:
        if o["id"] in con_dato:
            por_noche[o["noche"]] += int(o["clase"] in ("pos_prot", "pos_bajo"))
    noches = alertas = 0
    for n in sorted(por_noche):
        noches += 1
        alertas += por_noche[n]
        if noches >= PARADA_NOCHES and alertas >= PARADA_ALERTAS:
            return n, {"noches": noches, "alertas": alertas, "alcanzada": True, "noche": n}
    return None, {"noches": noches, "alertas": alertas, "alcanzada": False, "noche": None}


# ---------------------------------------------------------------- controles (§11.4)
def control_s1(desde, hasta, pob):
    claves = [clave(o) for o in pob]
    malos = [o["hora_utc"] for o in pob if not (desde <= o["noche"] <= hasta)]
    return desde == DESDE_P and hasta >= desde and not malos and len(claves) == len(set(claves)), \
        {"desde": desde, "hasta": hasta, "fuera_de_ventana": malos[:10], "repetidas": len(claves) - len(set(claves))}


def control_s2(pob, via, inner, publicar, LP, n_max=20):
    """En una pasada real de la vía con VRP > 0: summit publica, far no, summit de nuevo publica."""
    cand = []
    for o in pob:
        rv = via.get(clave(o))
        if rv and rv.get("primary_cluster") and (rv.get("vrp_mw") or 0) > 0:
            cand.append((rv, inner[o["volcan"]]))
        if len(cand) >= n_max:
            break
    for rv, inn in cand:
        r = [bool(p) for _, p in publicar([(LP.variante(rv, 0.0, inn), inn), (LP.variante(rv, inn + 1.0, inn), inn),
                                           (LP.variante(rv, 0.0, inn), inn)])]
        if r[0]:
            return r == [True, False, True], r
    return False, "sin pasada de la vía que publique en summit: S2 no se puede comprobar"


def control_s3(info):
    uno = [v for v in info.values() if v["npix"] == 1 and v["dist"]]
    malos = [v["dist"] for v in uno if abs(v["dist"]["radiante"] - v["dist"]["cercano"]) > TOL_UNO_KM]
    return bool(uno) and not malos, {"n": len(uno), "malos": malos[:5]}


def control_s4(pob, info, inner, LP):
    """S4, salvo las pasadas con radiante a 0,0005 km del radio (VS168-10), que se cuentan aparte."""
    con = [o for o in pob if (info.get(o["id"]) or {}).get("dist")]
    exc = {o["id"] for o in con if abs(info[o["id"]]["dist"]["radiante"] - inner[o["volcan"]]) <= TOL_S4_KM}
    usa = [o for o in con if o["id"] not in exc]
    malos = [o["hora_utc"] for o in usa
             if LP.clase_dc(info[o["id"]]["dist"]["radiante"], inner[o["volcan"]]) != info[o["id"]]["dc"]]
    return len(usa) > 0 and not malos, {"n": len(usa), "malos": malos[:10], "excluidas_por_redondeo": len(exc)}


def control_s5(pob, kfull, inner, publicar, LP):
    """PLACEBO (C8): K x 1,2 publica igual que K, con al menos una pasada."""
    casos, pub_k = [], []
    for o in pob:
        rk = kfull.get(clave(o))
        if rk is not None:
            casos.append((LP.placebo_k(rk, 1.2), inner[o["volcan"]]))
            pub_k.append(o["pub_prod"])
    res = [bool(p) for _, p in publicar(casos)] if casos else []
    dist = sum(1 for a, b in zip(res, pub_k) if a != b)
    return bool(casos) and dist == 0, {"n": len(casos), "discordantes": dist}


def control_s6(marco, LP, EC):
    """S6 placebo de M (C9): sin MEJORA con el comparador, y el comparador tiene que haber corrido (VS168-08)."""
    ok, pl = LP.control_placebo_m(marco, EC)
    pk = LP.pares_k(marco)
    sustrato = all(v["con_comparador"] != "SIN SUSTRATO" for v in pl.values())
    return ok and sustrato, {"pares": len(pk), "noches": len({p["bloque"] for p in pk}), "placebo": pl}


def control_s7(pob, arms):
    por = {}
    falla = False
    for c in sorted({o["clase"] for o in pob} | set(CLASES_DECIDEN)):
        n = sum(1 for o in pob if o["clase"] == c)
        s = [(o["volcan"], o["hora_utc"]) for o in pob if o["clase"] == c and o["id"] not in arms]
        por[c] = {"n": n, "sin_dato": len(s), "lista": s}
        if c in CLASES_DECIDEN and n and len(s) / n > UMBRAL_COBERTURA:
            falla = True
    return bool(pob) and not falla, por


def diff_git(a, b):
    """Archivos de pipeline/ que cambian entre dos commits, o None si git no los resuelve."""
    try:
        p = subprocess.run(["git", "-C", str(RAIZ), "diff", "--name-only", a, b, "--", "pipeline/"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return [x for x in p.stdout.splitlines() if x.strip()]


def control_s8(recs_k, recs_via, commit, diff_fn):
    """S8, marca de régimen (VS168-04): cada codigo_sha de los records y el de --commit, contra c42ee0eb7 en pipeline/;
    perfiles mirova_equivalent y sombra_codigo_mirova. Devuelve (sin cambio, detalle)."""
    shas = collections.Counter()
    perf_malos = collections.Counter()
    for recs, perfil in ((recs_k, PERFIL_K), (recs_via, PERFIL_VIA)):
        for r in recs:
            reg = r.get("regimen") or {}
            shas[reg.get("codigo_sha")] += 1
            if reg.get("perfil") != perfil:
                perf_malos[f"{perfil}: {reg.get('perfil')}"] += 1
    shas[commit] += 0
    cambios = {}
    for s in sorted(shas, key=str):
        if not s:
            cambios[str(s)] = "sin sha"
            continue
        f = diff_fn(BASE_REGIMEN, s)
        if f is None:
            cambios[s] = "git no lo resuelve"
        elif f:
            cambios[s] = f
    return not cambios and not perf_malos, {"shas": dict(shas), "cambios": cambios, "perfiles": dict(perf_malos)}


def control_s9(ultima_tabla, corte):
    """S9 rezago (VS168-05): la fila más nueva de la tabla es de al menos 2 días después de la noche del corte."""
    if not ultima_tabla:
        return False, {"ultima_tabla": None, "corte": corte}
    ok = date.fromisoformat(ultima_tabla[:10]) >= date.fromisoformat(corte) + timedelta(days=REZAGO_DIAS)
    return ok, {"ultima_tabla": ultima_tabla, "corte": corte}


def control_s10(info):
    """S10 (VS168-11): pasadas de la vía con alertados y sin distancias: deben ser 0."""
    malos = sorted(i for i, v in info.items() if v["npix"] > 0 and v["dist"] is None)
    return not malos, {"n": len(malos)}


# ---------------------------------------------------------------- lecturas (§11.6) y regla (§11.7)
def filas_de(pob, arms, E):
    obj = {o["id"]: o for o in pob if o["id"] in arms}
    pub_k = {i: o["pub_prod"] for i, o in obj.items()}
    vk = {i: (o["disp_k"] if o["pub_prod"] else None) for i, o in obj.items()}
    pesos = {(o["clase"], o["estrato"]): 1.0 for o in obj.values()}
    filas = E.armar(obj, {i: {"geometria_centro": {}} for i in obj}, arms, None, pub_k, vk, True, pesos)
    for x in filas:
        x["sensor"] = obj[x["i"]]["sensor"]
        x["dref"] = obj[x["i"]]["dist_ref"]
        x["noche"] = obj[x["i"]]["noche"]
    return filas


def controles_curva(filas, a, E, CC):
    """§11.6 (VA168-02): sesgo de plataforma, ganancia pareja y ganancia que crece con el cenit sobre la curva
    condicionada del brazo a (o de K). Devuelve (algún control cae, detalle)."""
    pas = [{"vol": x["vol"], "hora": x["hora"], "z": x["z"], "mir": x["mir"], "plat": x.get("sensor"),
            "pub": bool(E.publica(x, a)), "vrp": x.get("VK") if a == "K" else x["V"].get(a)}
           for x in filas if x["c"].startswith("pos")]

    def med_d(pp):
        r = CC.resumen(CC.pares_por_noche(pp, "vrp", "pub", condicionar=True))
        return r["todas"]["d"][0], r["todas"]["n_noches"]

    d0, n0 = med_d(pas)
    sesgo = CC.sesgo_plataforma(pas, "vrp", "pub")
    out = {"d0": d0, "n": n0, "sesgo_plataforma": sesgo["sesgado"], "por_plataforma": sesgo["por_plataforma"]}
    if not n0:
        out["ganancia_pareja"] = out["ganancia_cenit"] = "SIN SUSTRATO"
        return sesgo["sesgado"], out
    g1 = [dict(p, vrp=(p["vrp"] or 0) * 1.2) for p in pas]
    g2 = [dict(p, vrp=(p["vrp"] or 0) * (1 + 0.01 * max((p["z"] or 0) - 20, 0))) for p in pas]
    d1, _ = med_d(g1)
    d2, _ = med_d(g2)
    out["ganancia_pareja"] = {"d": d1, "ok": abs(np.log10(d1 / d0)) <= TOL_GANANCIA_LOG10}
    out["ganancia_cenit"] = {"d": d2, "ok": d2 > d0}
    return sesgo["sesgado"] or not out["ganancia_pareja"]["ok"] or not out["ganancia_cenit"]["ok"], out


def mitades(filas, a, deps):
    """§11.6: en lugar de A104, la primera mitad de las noches contra la segunda; informa."""
    LP, E, EC = deps["LP"], deps["E"], deps["EC"]
    noches = sorted({x["noche"] for x in filas})
    corte = noches[(len(noches) - 1) // 2] if noches else ""
    out = {"corte_noche": corte}
    for nom, sel in (("primera", [x for x in filas if x["noche"] <= corte]),
                     ("segunda", [x for x in filas if x["noche"] > corte])):
        P, _ = LP.pares_magnitud(sel, a)
        out[nom] = {"M": EC.decidir_estrato(P, "informa")[0], "P2_K": E.p2(sel, a, "K")["veredicto"], "n": len(sel)}
    return out


def criterios_sombra(veta, p2k, silencio, p2l, est_c, cae_curva, est_d, regimen_ok=True):
    """§11.7: (a) ninguna protegida que K publica y el brazo calla; (b) P2 contra K GANA, EMPATE o SIN SUSTRATO, el
    silencio no ENCIENDE DE MAS y P2-L no PIERDE ni BLOQUEA (tabla de §9.7); (c) el estado de M; (d) el
    estado_d_sombra de §9.7, llevado a DECIDE NICOLAS si cae un control de la curva (§11.6). Con la marca de régimen
    (S8), un CUMPLE de (b), (c) o (d) pasa a DECIDE NICOLAS. Estado: NO CUMPLE si algún criterio no cumple; si no,
    DECIDE NICOLAS si alguno lo pide; si no, CUMPLE."""
    c = {"a": CUMPLE if not veta else NO_CUMPLE,
         "b": CUMPLE if (p2k in ("GANA", "EMPATE", "SIN SUSTRATO") and silencio != "ENCIENDE DE MAS"
                         and p2l not in ("PIERDE", "BLOQUEA")) else NO_CUMPLE,
         "c": est_c,
         "d": NICOLAS if cae_curva else est_d}
    if not regimen_ok:
        for k in ("b", "c", "d"):
            if c[k] == CUMPLE:
                c[k] = NICOLAS
    v = list(c.values())
    c["estado"] = NO_CUMPLE if NO_CUMPLE in v else NICOLAS if NICOLAS in v else CUMPLE
    return c


def estado_c_sombra(veredicto_m, LP):
    """§11.6 (c) (VS168-06): en la sombra, M en SIN SUSTRATO es DECIDE NICOLAS; lo demás, como en §9.7."""
    return NICOLAS if veredicto_m == "SIN SUSTRATO" else LP.estado_c(veredicto_m)


def leer_brazo(filas, a, deps, N_neg, tasa_k_neg, sin_dato_prot, cae_k, regimen_ok):
    LP, E, CC, EC = deps["LP"], deps["E"], deps["CC"], deps["EC"]
    marco = [x for x in filas if x["c"] not in LP.CLASES_FAR]
    far_t = [x for x in filas if x["c"] == "far_tabla"]
    rng = np.random.default_rng(E.SEMILLA)
    hay_neg = all(N_neg.get(c, 0) for c in E.CLASES_NEG)
    lk = E.lecturas(marco, a, rng, N_neg, tasa_k_neg) if hay_neg else None
    p2k = E.p2(marco, a, "K")
    p2l = LP.p2_con(far_t, a, "K", E, lambda x, k: x["c"] == "far_tabla" and E.publica(x, k))
    veta = [(x["vol"], x["hora"]) for x in marco if x["c"] == "pos_prot" and x["K"] and not x["X"][a]]
    veta += [(o["volcan"], o["hora_utc"]) for o in sin_dato_prot if o["pub_prod"]]   # VS168-03
    n3 = [(x["vol"], x["hora"]) for x in marco if x["c"] == "pos_prot" and LP.no_veta_n3(x)]
    m = LP.magnitud(marco, a, EC)
    cur_p, cur_k = LP.curva(marco, a, E, CC), LP.curva(marco, "K", E, CC)
    cae_curva, ctl_curva = controles_curva(marco, a, E, CC)
    silencio = lk["silencio"]["veredicto"] if lk else "SIN SUSTRATO (faltan negativos de alguna clase)"
    est_c = estado_c_sombra(m["veredicto"], LP)
    est_d = LP.estado_d_sombra(cur_p["condicionada"], cur_k["condicionada"])
    c = criterios_sombra(veta, p2k["veredicto"], silencio, p2l["veredicto"], est_c, cae_curva or cae_k, est_d,
                         regimen_ok)
    lej = LP.lecturas_far(filas, a, E)
    return {"criterios": c, "P1_veta": veta, "n3_filas": n3, "lecturas": lk, "silencio": silencio, "P2_K": p2k,
            "P2L_K": p2l, "M": m, "curva": cur_p, "curva_K": cur_k, "controles_curva": ctl_curva,
            "P1_sin_dato": [(o["volcan"], o["hora_utc"], "K publica" if o["pub_prod"] else "K calla")
                            for o in sin_dato_prot],
            "b_sin_evidencia": (not hay_neg) and p2k["veredicto"] == "SIN SUSTRATO",
            "lejanas": lej["far_tabla"], "lejanas_ocr": lej["far_ocr"], "mitades": mitades(marco, a, deps)}


def paquete(pob, arms, deps, regimen_ok=True):
    LP, E, CC = deps["LP"], deps["E"], deps["CC"]
    filas = filas_de(pob, arms, E)
    n_neg = collections.Counter(x["c"] for x in filas)
    N_neg = {c: n_neg.get(c, 0) for c in E.CLASES_NEG}
    tot = sum(N_neg.values())
    tasa = N_neg["neg_pub"] / tot if tot else float("nan")
    sin_dato_prot = [o for o in pob if o["clase"] == "pos_prot" and o["id"] not in arms]
    cae_k, ctl_k = controles_curva([x for x in filas if x["c"] not in LP.CLASES_FAR], "K", E, CC)   # VS168-07
    br = {a: leer_brazo(filas, a, deps, N_neg, tasa, sin_dato_prot, cae_k, regimen_ok) for a in (DECIDE,) + INFORMAN}
    return filas, br, ctl_k


def estado_final(base, vueltas):
    """§11.7 y §11.5: el estado de cercano; si alguna vuelta del borde lo cambia, DECIDE NICOLAS."""
    e = base[DECIDE]["criterios"]["estado"]
    for nom, f in vueltas:
        if f[DECIDE]["criterios"]["estado"] != e:
            return NICOLAS, f"la vuelta {nom} del borde cambia el estado (§11.5)"
    return e, ""


def analizar(pob, via, kfull, inner, publicar, deps, desde, hasta, identidad_ok=True, ultima_tabla=None,
             commit=None, diff_fn=diff_git):
    """Todo el §11 sin imprimir. Devuelve (out, fallas). El corte es la noche de la parada si se alcanzó (§11.8); si no,
    `out` trae sólo controles y contadores. Con fallas, `out` trae sólo controles, el corte y si hubo parada."""
    LP = deps["LP"]
    con_dato = {o["id"] for o in pob if clave(o) in via}
    n_par, cont = noche_parada(pob, con_dato)
    alcanzada = n_par is not None
    corte = n_par if alcanzada else hasta
    pob = [o for o in pob if o["noche"] <= corte]
    out, fallas = {"controles": {}, "corte": corte, "hasta_pedido": hasta, "parada_alcanzada": alcanzada}, []
    ok1, d1 = control_s1(desde, corte, pob)
    arms, info = brazos(pob, via, inner, publicar, LP)
    ok2, d2 = control_s2(pob, via, inner, publicar, LP)
    ok2 = ok2 and identidad_ok
    ok3, d3 = control_s3(info)
    ok4, d4 = control_s4(pob, info, inner, LP)
    ok5, d5 = control_s5(pob, kfull, inner, publicar, LP)
    ok7, d7 = control_s7(pob, arms)
    filas = filas_de(pob, arms, deps["E"])
    ok6, d6 = control_s6([x for x in filas if x["c"] not in LP.CLASES_FAR], LP, deps["EC"])
    ok10, d10 = control_s10(info)
    ctl = [("S1", ok1, d1), ("S2", ok2, d2), ("S3", ok3, d3), ("S4", ok4, d4), ("S5", ok5, d5), ("S6", ok6, d6),
           ("S7", ok7, d7), ("S10", ok10, d10)]
    if alcanzada:
        ctl.append(("S9",) + control_s9(ultima_tabla, corte))
    for nom, ok, det in ctl:
        out["controles"][nom] = {"ok": bool(ok), "detalle": det}
        if not ok:
            fallas.append(nom)
    if fallas:
        return {k: out[k] for k in ("controles", "corte", "hasta_pedido", "parada_alcanzada")}, fallas
    out["parada"] = cont
    if not alcanzada:
        return out, fallas
    ok8, d8 = control_s8([kfull[clave(o)] for o in pob if clave(o) in kfull],
                         [via[clave(o)] for o in pob if clave(o) in via], commit, diff_fn)
    filas, base, ctl_k = paquete(pob, arms, deps, regimen_ok=ok8)
    ids_borde = borde(pob, info, inner)
    vueltas = []
    if ids_borde:
        conj = frozenset(ids_borde)
        mixto = borde_mixto(pob, info, inner, ids_borde, LP)
        for nom, fl in (("conjunta", conj), ("mixta", mixto)):
            if fl and (nom == "conjunta" or fl != conj):
                arms_f, _ = brazos(pob, via, inner, publicar, LP, flip=fl)
                vueltas.append((nom, paquete(pob, arms_f, deps, regimen_ok=ok8)[1]))
    est, motivo = estado_final(base, vueltas)
    por = {o["id"]: o for o in pob}
    out.update({"brazos": base, "controles_curva_K": ctl_k, "regimen": {"sin_cambio": ok8, "detalle": d8},
                "lejanas_K": LP.lecturas_far(filas, "K", deps["E"]),
                "borde": [(por[i]["volcan"], por[i]["hora_utc"]) for i in ids_borde],
                "estado_vueltas": {nom: f[DECIDE]["criterios"]["estado"] for nom, f in vueltas},
                "estado": est, "motivo": motivo})
    return out, fallas


# ---------------------------------------------------------------- reporte
def reporte_controles(out, detalle):
    pr("== controles (§11.4)")
    for k, v in out["controles"].items():
        if detalle:
            pr(f"  {k} {'OK' if v['ok'] else 'CAE'}: {v['detalle']}")
        else:
            pr(f"  {k} {'OK' if v['ok'] else 'CAE: ' + MOTIVO[k]}")


def reporte(out, pob, fuera, snpp, sin_record):
    pr("\n== población (§11.2, censo, peso 1)")
    pr("  por clase:", dict(sorted(collections.Counter(o["clase"] for o in pob).items())))
    pr("  fuera por etiqueta:", dict(sorted(fuera.items())), "| Suomi NPP fuera:", snpp)
    pr("  cobertura (S7):", {c: (v["n"], v["sin_dato"]) for c, v in out["controles"]["S7"]["detalle"].items()})
    pr("  SIN DATO por nombre:", {c: v["lista"] for c, v in out["controles"]["S7"]["detalle"].items() if v["lista"]})
    pr(f"  alertas de MIROVA sin record de K (informa): {sum(sin_record.values())} {dict(sorted(sin_record.items()))}")
    pa = out["parada"]
    pr(f"\n== parada (§11.8): noches {pa['noches']} de {PARADA_NOCHES}, alertas {pa['alertas']} de {PARADA_ALERTAS}: "
       f"ALCANZADA en la noche {pa['noche']}; corte que decide {out['corte']}"
       + (f" (recortado: --hasta {out['hasta_pedido']})" if out["hasta_pedido"] != out["corte"] else ""))
    rg = out["regimen"]
    pr(f"\n== régimen (S8, contra {BASE_REGIMEN[:9]} en pipeline/): "
       + ("SIN CAMBIO" if rg["sin_cambio"] else "CAMBIO: los CUMPLE de (b), (c) y (d) pasan a DECIDE NICOLAS")
       + f" | {rg['detalle']}")
    for a, r in out["brazos"].items():
        pr(f"\n== {ROTULO[a]}")
        lk = r["lecturas"]
        pr(f"  (a) P1 que veta: {len(r['P1_veta'])} {r['P1_veta']}; protegidas SIN DATO: {r['P1_sin_dato']}; "
           f"filas que tocaría N-3 (deben ser 0): {len(r['n3_filas'])}")
        if lk:
            pr(f"      P1 perdidas {lk['P1']['perdidas']} de {lk['P1']['de']}, que K publica "
               f"{lk['P1']['perdidas_que_K_publica']} {lk['P1']['lista']} | recall prot {lk['recall_prot']['crudo']}"
               f" bajo {lk['recall_bajo']['crudo']} | MISSION (informa) {lk['MISSION_K']['veredicto']}")
        pr(f"  (b) P2 contra K {r['P2_K']['veredicto']} (neto {r['P2_K']['neto']:+.1f}, B {r['P2_K']['B']}) | "
           f"silencio {r['silencio']} | P2-L {r['P2L_K']['veredicto']} (neto {r['P2L_K']['neto']:+.1f}, "
           f"B {r['P2L_K']['B']})" + (" | CUMPLE POR FALTA DE EVIDENCIA" if r["b_sin_evidencia"] else ""))
        d = r["M"]["detalle"]
        pr(f"  (c) M {r['M']['veredicto']} (n {r['M']['n']}, salen {r['M']['salen_publica_uno']}; d {d.get('d_mediana')} "
           f"IC {d.get('ic95')}; d′ {d.get('regla_dprima')} {d.get('ic95_dprima')}) | informa {r['M']['informa']}")
        pr(f"  (d) curva condicionada {r['curva']['condicionada']} | sin condicionar (informa) "
           f"{r['curva']['sin_condicionar']} | K {r['curva_K']['condicionada']}")
        pr(f"      controles de la curva: {r['controles_curva']}")
        pr(f"  lejanas (informa): publica {r['lejanas']['publica']} de {r['lejanas']['n']} far_tabla "
           f"{r['lejanas']['lista']} | far_ocr {r['lejanas_ocr']['publica']} de {r['lejanas_ocr']['n']}")
        pr(f"  mitades (informa, en lugar de A104): {r['mitades']}")
        if a == DECIDE:
            pr(f"  criterios: {r['criterios']}")
    pr(f"\n== controles de la curva de K (§11.6): {out['controles_curva_K']}")
    lk = out["lejanas_K"]
    pr(f"\n== lejanas de K (informa): publica {lk['far_tabla']['publica']} de {lk['far_tabla']['n']} far_tabla "
       f"{lk['far_tabla']['lista']} | far_ocr {lk['far_ocr']['publica']} de {lk['far_ocr']['n']}")
    pr(f"\n== borde (§11.5): {len(out['borde'])} {out['borde']}; estado con el borde dado vuelta: "
       f"{out['estado_vueltas']}")
    pr(f"\n== PAQUETE en la sombra (§11.7), brazo cercano: {out['estado']}"
       + (f" ({out['motivo']})" if out["motivo"] else ""))


def a_json(o):
    """Las claves de tupla (los brazos, ("VIA", "cercano")) pasan a texto con «|» para el json."""
    if isinstance(o, dict):
        return {("|".join(map(str, k)) if isinstance(k, tuple) else k): a_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [a_json(v) for v in o]
    return o


def para_json(out, tipo):
    """VS168-02 y VS168-13: fuera de la lectura que decide, sólo nombre, OK o CAE y motivo de cada control; en la
    lectura, los brazos que informan van sin criterios."""
    if tipo != "decide":
        sal = {"controles": {k: {"ok": v["ok"], "motivo": "" if v["ok"] else MOTIVO[k]}
                             for k, v in out.get("controles", {}).items()}}
        if tipo == "provisional":
            sal["parada"] = {k: out["parada"][k] for k in ("noches", "alertas", "alcanzada")}
        return sal
    sal = dict(out)
    sal["brazos"] = {a: ({k: v for k, v in r.items() if k != "criterios"} if a != DECIDE else r)
                     for a, r in out["brazos"].items()}
    return sal


def git_head():
    try:
        p = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-k", required=True)
    ap.add_argument("--data-sombra", required=True)
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--desde", default=DESDE_P)          # sólo para que la batería pruebe que otro valor cae (S1)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--dir-salida", required=True)
    a = ap.parse_args(argv)
    del L[:]
    ahora = datetime.now(timezone.utc)
    pr("== procedencia")
    pr(f"  hora: {ahora.strftime('%Y-%m-%d %H:%M UTC')} | records de origin/main {a.commit}")
    pr(f"  lector sha256 LF {sha256_lf(Path(__file__))} | checkout del lector {git_head()}")
    deps, malos = cargar_deps()
    pr(f"  S0 dependencias del tag s168-v375e-cuerpo-sellado y del sello del lector: "
       f"{'OK' if deps else 'CAE: ' + MOTIVO['S0'] + ' ' + str(sorted(malos))}")
    out = {"procedencia": {"commit": a.commit, "lector": sha256_lf(Path(__file__)), "checkout": git_head(),
                           "S0": not malos, "S0_malos": malos}}
    tipo, corte, fallas, res = "no_legible", a.hasta, ["S0"], {}
    if deps:
        import banco_paridad as B
        from clase_mirova import alerta_protegida
        from referencia_mirova_unificada import cargar_referencia_unificada
        ref_sha = {"cons": sha256_lf(a.cons), "ocr": sha256_lf(a.ocr)}
        pr(f"  referencia congelada (sha256 LF, sin capas locales): {ref_sha}")
        coords, inner = B._coords_por_volcan(), B.inner_desde_html()
        filas_ref = cargar_referencia_unificada(Path(a.cons), Path(a.ocr), respaldo_path=None, historico_path=None)
        ultima_tabla = max((f["fecha_utc"] for f in filas_ref if f.get("source") == "CONS"), default=None)
        por_vb, ns, nv, _ = B.indexar_referencia(filas_ref, coords, (a.desde, a.hasta), regla_minimas="SN")
        recs = B.cargar_nuestros(coords, inner, (a.desde, a.hasta), data=a.data_k)
        B.etiquetar(recs, por_vb, ns, nv)
        pob, _, _ = poblacion(recs, por_vb, B, alerta_protegida)
        via, sha_s = cargar_records(a.data_sombra, B.VOLS, a.desde, a.hasta, solo_via=True)
        kfull, sha_k = cargar_records(a.data_k, B.VOLS, a.desde, a.hasta)
        pr(f"  records (sha256 LF): K {sha_k} | sombra {sha_s}")
        out["procedencia"].update({"referencia": ref_sha, "records_k": sha_k, "records_sombra": sha_s})
        E = deps["E"]

        def publicar(casos):
            return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inn] for r, inn in casos])]

        n_pre, _ = noche_parada(pob, {o["id"] for o in pob if clave(o) in via})
        ya = Path(a.dir_salida) / f"lectura_sombra_corte_{n_pre}.txt"
        if n_pre is not None and (ya.exists() or ya.with_suffix(".json").exists()):
            pr(f"\nYA EXISTE {ya.name}: el corte {n_pre} no se vuelve a leer ni a escribir (§11.8)")
            return 2
        ident = B.control_identidad_predicado()
        res, fallas = analizar(pob, via, kfull, inner, publicar, deps, a.desde, a.hasta,
                               identidad_ok=ident == IDENTIDAD_ESPERADA, ultima_tabla=ultima_tabla, commit=a.commit)
        corte = res["corte"]
        tipo = "no_legible" if fallas else ("decide" if res["parada_alcanzada"] else "provisional")
        out.update(res)
    dsal = Path(a.dir_salida)
    dsal.mkdir(parents=True, exist_ok=True)
    base = (f"lectura_sombra_corte_{corte}" if tipo == "decide"
            else f"controles_sombra_{corte}_{ahora.strftime('%Y%m%dT%H%M%S%fZ')}")
    txt, js = dsal / (base + ".txt"), dsal / (base + ".json")
    if tipo != "decide" and (txt.exists() or js.exists()):    # la de la lectura que decide ya se miró antes
        pr(f"\nYA EXISTE {txt.name}: no se sobrescribe (§11.8)")
        return 2
    cod = {"decide": 0, "provisional": 5, "no_legible": 3}[tipo]
    if deps:
        reporte_controles(res, detalle=tipo == "decide")
    if tipo == "no_legible":
        pr(f"\nLECTURA NO LEGIBLE (§11.4): caen {fallas}; no se imprime nada de la población")
    elif tipo == "provisional":
        pa = res["parada"]
        pr(f"\n== parada (§11.8): noches {pa['noches']} de {PARADA_NOCHES}, alertas {pa['alertas']} de "
           f"{PARADA_ALERTAS}: NO ALCANZADA; no hay lectura")
    else:
        rc = [r for r in recs if r["noche"] <= corte]
        pob_c, fuera, snpp = poblacion(rc, por_vb, B, alerta_protegida)
        pv = {k: [(dt, f) for dt, f in v if dt.strftime("%Y-%m-%d") <= corte]
              for k, v in por_vb.items() if k[1] == "VIIRS375"}
        sin_rec = {k[0]: n for k, n in B.alertas_sin_record(pv, rc).items()}
        reporte(res, pob_c, fuera, snpp, sin_rec)
        out["alertas_sin_record_K"] = sin_rec
    sal = {"procedencia": out["procedencia"], "corte": corte, **para_json(out, tipo)} if tipo != "decide" \
        else para_json(out, tipo)
    txt.write_text("\n".join(L) + "\n", encoding="utf-8")
    js.write_text(json.dumps(a_json(sal), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return cod


if __name__ == "__main__":
    sys.exit(main())
