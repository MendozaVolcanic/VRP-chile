# -*- coding: utf-8 -*-
"""Segundo instrumento para F/K (regla de adopcion de K, REGLA_ADOPCION.md 4.3).

POR QUE. La mejora de K es grande (VIIRS 375: de ~85 % a ~3,7 % de publicacion donde MIROVA no vio nada)
y en S33 una metrica con un bug produjo una adopcion equivocada. Este script reimplementa las
definiciones desde el TEXTO (PREREGISTRO.md 5 y 6, docs/S151_CRITERIO_CLASE_MIROVA.md lectura A, y la
definicion de negativo limpio de scripts/banco_paridad.py leida como especificacion). NO importa
evaluar_fk, banco_paridad, clase_mirova, referencia_mirova_unificada ni pipeline/. El predicado del
tablero se ejecuta con node desde frontend/index.html, extrayendo las funciones por nombre (A97).

Definiciones (todas por pasada = volcan, sensor completo del record, hora al minuto):
- nocturna: elevacion solar <= 0 en las coordenadas del volcan (volcanoes.yaml), calculada aca con
  el algoritmo de la NOAA (los flags diurnos de produccion estan apagados: rechaza todo lo diurno).
- referencia: CONS principal + OCR principal + capa historica (CONS) + respaldo (CONS); clave
  (volcan, cajon de sensor, minuto, canal); dentro de un archivo gana la Ultima_Actualizacion mas nueva;
  entre capas gana la primera que trae la clave. V2: se sacan las filas OCR (tabla sola).
- pareo: filas nocturnas de la referencia a +-120 s de la hora del record, mismo volcan y cajon.
- alerta (pos): alguna fila pareada de tipo ALERTA_TERMICA o ALERTA_TERMICA_OCR.
- protegida A: alguna fila pareada de alerta con VRP_MW >= 1. Protegida B: alguna fila no RUTINA >= 1.
- solo OCR Suomi NPP (sólo V1): record VIIRS_SNPP* cuyas filas de alerta pareadas son todas OCR.
- far_ref: sin alerta y con alguna fila FALSO_POSITIVO*.
- negativo limpio: sin alerta ni FP pareados, con fila CONS RUTINA de VRP 0 pareada, y la noche
  (fecha UTC) de ese volcan y cajon sin ninguna fila de alerta ni FP nocturna.
- Muy Bajo: alerta que no es protegida A (en V1 sin las solo OCR Suomi NPP, que salen de la suma).
- P2: Muy Bajo no publicadas + negativos limpios publicados.
"""
from __future__ import annotations

import bisect
import collections
import csv
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
TMP = Path(r"C:\Users\nmend\AppData\Local\Temp\claude")
OUT = TMP / "r3_fk"
HTML = REPO / "frontend" / "index.html"
PRE = REPO / "experiments" / "_s151_prereg_fk_11"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
SENS = ["MODIS", "VIIRS375", "VIIRS750"]
ARMDIR = {"C0": "_s146_ab_control", "F": "_s147_ab_sin_test1_max",
          "K": "_s149_ab_sin_test1_b22_max", "G": "_s151_ab_control_gemelo"}

VENTANAS = {
    "V1": dict(desde="2026-08-29", hasta="2026-10-08", ocr=True, viirs_desde="2026-08-29",
               ref=PRE / "_congelado_v1", raices=[TMP / "v1_38639658446" / "union_2766"],
               brazos=["C0", "F", "K", "G"]),
    "V2": dict(desde="2026-03-01", hasta="2026-06-12", ocr=False, viirs_desde="2026-04-01",
               ref=PRE / "_congelado_v2",
               raices=[TMP / "v2a_38648773684" / "union_2766", TMP / "v2b_39033530622" / "union"],
               brazos=["C0", "K"]),
}


# ------------------------------------------------------------------ utilidades
def cajon(sensor: str):
    s = (sensor or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def cajon_csv(s: str):
    s = (s or "").strip().upper()
    if "MODIS" in s:
        return "MODIS"
    if "375" in s:
        return "VIIRS375"
    if "VIIRS" in s:
        return "VIIRS750"
    return None


def norm_vol(nombre: str):
    k = re.sub(r"[^a-z]", "", (nombre or "").lower()
               .replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    tabla = {re.sub(r"[^a-z]", "", v.lower()): v for v in VOLS}
    tabla.update({"puyehuecordoncaulle": "PuyehueCordonCaulle", "cordoncaulle": "PuyehueCordonCaulle",
                  "planchonpeteroa": "PlanchonPeteroa", "peteroa": "PlanchonPeteroa",
                  "nevadosdechillan": "NevadosDeChillan"})
    return tabla.get(k)


def coords():
    # lectura minima de volcanoes.yaml sin depender de pipeline/
    import yaml
    d = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    return {v["name"]: (float(v["lat"]), float(v["lon"])) for v in d["volcanoes"] if v["name"] in VOLS}


def elev_solar(lat, lon, dt):
    """Elevacion solar aparente sin refraccion (NOAA Solar Calculator, ecuaciones de Meeus)."""
    jd = dt.timestamp() / 86400.0 + 2440587.5
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + 0.0003032 * T)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    Mr = math.radians(M)
    C = (math.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T)) + math.sin(2 * Mr) * (0.019993 - 0.000101 * T)
         + math.sin(3 * Mr) * 0.000289)
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * T))
    eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * T))
    decl = math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam)))
    y = math.tan(math.radians(eps / 2)) ** 2
    L0r = math.radians(L0)
    eqt = 4 * math.degrees(y * math.sin(2 * L0r) - 2 * e * math.sin(Mr) + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
                           - 0.5 * y * y * math.sin(4 * L0r) - 1.25 * e * e * math.sin(2 * Mr))
    minutos = dt.hour * 60 + dt.minute + dt.second / 60
    tst = (minutos + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    latr = math.radians(lat)
    cosz = math.sin(latr) * math.sin(decl) + math.cos(latr) * math.cos(decl) * math.cos(math.radians(ha))
    return 90 - math.degrees(math.acos(max(-1, min(1, cosz))))


# ------------------------------------------------------------------ predicado del tablero (node)
JS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function cuerpo(nombre) {
  const re = new RegExp('\\nfunction ' + nombre + '\\s*\\(');
  const m = re.exec(src);
  if (!m) throw new Error('falta function ' + nombre);
  const ini = m.index + 1;
  let k = src.indexOf('{', src.indexOf(')', ini)), prof = 0, enStr = null;
  for (; k < src.length; k++) {
    const c = src[k];
    if (enStr) { if (c === '\\') { k++; continue; } if (c === enStr) enStr = null; continue; }
    if (c === '"' || c === "'" || c === '`') { enStr = c; continue; }
    if (c === '/' && src[k+1] === '/') { k = src.indexOf('\n', k); continue; }
    if (c === '{') prof++;
    else if (c === '}') { prof--; if (prof === 0) return src.slice(ini, k + 1); }
  }
  throw new Error('sin cierre ' + nombre);
}
function cte(nombre) {
  const m = new RegExp('\\nconst ' + nombre + '\\s*=\\s*[^;]+;').exec(src);
  if (!m) throw new Error('falta const ' + nombre);
  return m[0];
}
// Valor por defecto del toggle en el tablero: persistedFlag("vrp_f5_core", true) -> true.
var USE_F5_CORE = true;
function isSensorVisible(r) { return true; }  // todas las pastillas encendidas por defecto
eval([cte('F5_R_CORE_KM'), cte('F5_BT_EXT_K')].concat(
  ['_havKm', 'mirovaEqVrp', 'f5CoreMagnitude', 'mirovaEqVrpCore', 'mirovaEqVrpDisplay',
   'isCirrusArtifact', 'isDiffuseFieldArtifact', 'isThermalArtifact', 'isValidDetection',
   'isSummitDetection'].map(cuerpo)).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
// Las guardas de latestDetection (la tarjeta "ultima deteccion"): summit, valida, sensor visible,
// no artefacto y magnitud de display > 0.
const out = casos.map(([r, inner]) => {
  if (!isSummitDetection(r)) return 0;
  if (!isValidDetection(r)) return 0;
  if (!isSensorVisible(r)) return 0;
  if (isThermalArtifact(r, inner)) return 0;
  return mirovaEqVrpDisplay(r, inner, false) > 0 ? 1 : 0;
});
console.log(JSON.stringify(out));
"""


def inner_html():
    src = HTML.read_text(encoding="utf-8")
    out = {}
    for linea in src.splitlines():
        m = re.search(r'name:\s*"(\w+)"', linea)
        n = re.search(r'inner_radius_km:\s*([\d.]+)', linea)
        if m and n and m.group(1) in VOLS and m.group(1) not in out:
            out[m.group(1)] = float(n.group(1))
    assert set(out) == set(VOLS), out
    return out


def publica(casos):
    d = tempfile.mkdtemp(dir=OUT)
    js, cj = Path(d) / "p.js", Path(d) / "c.json"
    js.write_text(JS, encoding="utf-8")
    cj.write_text(json.dumps(casos), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=6144", str(js), str(HTML), str(cj)],
                       capture_output=True, text=True)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-2000:])
    return json.loads(o.stdout)


def control_predicado():
    """Casos sinteticos: tiene que dar 1 en el caso cumbre con cumulo y 0 en los demas."""
    casos = [
        [{"vrp_mw": 0.4, "distance_class": "summit", "sensor": "MODIS_AQUA", "t_max_k": 290,
          "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}, 5.0],
        [{"vrp_mw": 5.0, "distance_class": "far", "sensor": "MODIS_AQUA", "t_max_k": 290,
          "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}, 5.0],
        [{"vrp_mw": 0.4, "distance_class": "summit", "sensor": "MODIS_AQUA", "t_max_k": 290,
          "primary_cluster": {"vrp_mw": 0.0, "centroid_dist_km": 1.0, "n_pixels": 2}}, 5.0],
        [{"vrp_mw": 0.4, "distance_class": "summit", "sensor": "MODIS_AQUA", "t_max_k": 290,
          "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 9.0, "n_pixels": 2}}, 5.0],
    ]
    return publica(casos)


# ------------------------------------------------------------------ referencia
def leer_csv(path: Path, canal: str):
    por = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            vol = norm_vol(r.get("Volcan"))
            f = (r.get("Fecha_Satelite_UTC") or "").strip()
            if vol is None or len(f) < 16:
                continue
            try:
                vrp = float(r.get("VRP_MW"))
            except (TypeError, ValueError):
                vrp = None
            fila = {"vol": vol, "b": cajon_csv(r.get("Sensor")), "f": f, "canal": canal,
                    "tipo": (r.get("Tipo_Registro") or "").strip(), "vrp": vrp,
                    "upd": (r.get("Ultima_Actualizacion") or "").strip()}
            k = (vol, fila["b"], f[:16], canal)
            if k not in por or fila["upd"] > por[k]["upd"]:
                por[k] = fila
    return por


def referencia(dirref: Path, con_ocr: bool):
    filas = dict(leer_csv(dirref / "registro_vrp_consolidado.csv", "CONS"))
    for capa, canal in (("registro_vrp_ocr.csv", "OCR"), ("consolidado_filas_perdidas.csv", "CONS"),
                        ("respaldo_20260408.csv", "CONS")):
        for k, v in leer_csv(dirref / capa, canal).items():
            filas.setdefault(k, v)
    out = list(filas.values())
    if not con_ocr:
        out = [x for x in out if x["canal"] != "OCR"]
    return out


es_alerta = lambda t: t in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")
es_fp = lambda t: t.startswith("FALSO_POSITIVO")


# ------------------------------------------------------------------ evaluacion
def cargar_brazo(raices, sub, vol):
    recs = {}
    for raiz in raices:
        p = raiz / sub / f"{vol}.json"
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            k = (vol, r["sensor"], r["datetime_utc"])
            if k in recs:
                recs.setdefault("__dup__", []).append(k)
            recs[k] = r
    dups = recs.pop("__dup__", [])
    return recs, dups


def evaluar(nombre, cfg, co, inner):
    lin = []
    p = lambda s="": (lin.append(s), print(s))
    ref = referencia(cfg["ref"], cfg["ocr"])
    # filas nocturnas en ventana
    idx = collections.defaultdict(list)
    noche = collections.defaultdict(lambda: [False, False])
    for x in ref:
        n = x["f"][:10]
        if not (cfg["desde"] <= n <= cfg["hasta"]):
            continue
        dt = datetime.strptime(x["f"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = co[x["vol"]]
        if elev_solar(lat, lon, dt) > 0:
            continue
        idx[(x["vol"], x["b"])].append((dt, x))
        e = noche[(x["vol"], x["b"], n)]
        e[0] |= es_alerta(x["tipo"])
        e[1] |= es_fp(x["tipo"])
    for v in idx.values():
        v.sort(key=lambda t: t[0])
    tiempos = {k: [t for t, _ in v] for k, v in idx.items()}

    # records por brazo
    brazos = cfg["brazos"]
    R = {a: {} for a in brazos}
    for a in brazos:
        for vol in VOLS:
            recs, dups = cargar_brazo(cfg["raices"], ARMDIR[a], vol)
            if dups:
                p(f"   AVISO {a} {vol}: {len(dups)} claves repetidas entre raices")
            R[a].update(recs)
    # pasadas nocturnas en ventana (base: C0)
    def entra(k):
        vol, s, d = k
        b = cajon(s)
        if b is None:
            return False
        n = d[:10]
        if not (cfg["desde"] <= n <= cfg["hasta"]):
            return False
        if b != "MODIS" and n < cfg["viirs_desde"]:
            return False
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        return elev_solar(*co[vol], dt) <= 0
    base = sorted(k for k in R["C0"] if entra(k))
    cob = {a: sum(1 for k in R[a] if entra(k)) for a in brazos}
    falt = {a: sum(1 for k in base if k not in R[a]) for a in brazos}
    p(f"== {nombre} {cfg['desde']} a {cfg['hasta']} | OCR {'si' if cfg['ocr'] else 'no (tabla sola)'} | VIIRS desde {cfg['viirs_desde']}")
    p(f"   pasadas nocturnas por brazo: {cob} | de C0 que faltan en el brazo: {falt}")

    # predicado
    pub = {}
    for a in brazos:
        ks = [k for k in base if k in R[a]]
        casos = []
        for k in ks:
            r = {kk: vv for kk, vv in R[a][k].items() if kk != "discarded_anomaly_pixels"}
            casos.append([r, inner[k[0]]])
        res = publica(casos)
        pub[a] = dict(zip(ks, res))

    # etiquetas
    lab = {}
    for k in base:
        vol, s, d = k
        b = cajon(s)
        t = datetime.strptime(d, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        ts = tiempos.get((vol, b), [])
        i = bisect.bisect_left(ts, t - timedelta(seconds=120))
        fil = []
        while i < len(ts) and ts[i] <= t + timedelta(seconds=120):
            fil.append(idx[(vol, b)][i][1])
            i += 1
        al = [f for f in fil if es_alerta(f["tipo"])]
        e = {"b": b, "alerta": bool(al),
             "protA": any((f["vrp"] or 0) >= 1 for f in al),
             "protB": any((f["vrp"] or 0) >= 1 and f["tipo"] != "RUTINA" for f in fil),
             "vrpA": max([f["vrp"] or 0 for f in al], default=None),
             "snpp_ocr": bool(cfg["ocr"] and al and s.startswith("VIIRS_SNPP") and all(f["canal"] == "OCR" for f in al)),
             "fp": any(es_fp(f["tipo"]) for f in fil)}
        ns = noche.get((vol, b, d[:10]), [False, False])
        e["neg"] = (not al and not e["fp"]
                    and any(f["tipo"] == "RUTINA" and f["canal"] == "CONS" and (f["vrp"] or 0) == 0 for f in fil)
                    and not ns[0] and not ns[1])
        lab[k] = e

    res = {}
    for b in SENS:
        ks = [k for k in base if lab[k]["b"] == b]
        al = [k for k in ks if lab[k]["alerta"]]
        pa = [k for k in al if lab[k]["protA"]]
        pa_snpp = [k for k in pa if lab[k]["snpp_ocr"]]
        pb = [k for k in ks if lab[k]["protB"]]
        mb_dec = [k for k in al if not lab[k]["protA"] and not lab[k]["snpp_ocr"]]
        mb_snpp = [k for k in al if not lab[k]["protA"] and lab[k]["snpp_ocr"]]
        neg = [k for k in ks if lab[k]["neg"]]
        p(f"   {b:9s} sustrato: pasadas {len(ks):5d} | alertas {len(al):4d} | protegidas A {len(pa):3d} "
          f"(C0 publica {sum(pub['C0'].get(k,0) for k in pa):3d}; solo OCR Suomi NPP {len(pa_snpp)}) | protegidas B {len(pb):3d} "
          f"| negativos limpios {len(neg):5d} | Muy Bajo que deciden {len(mb_dec)} (+{len(mb_snpp)} solo OCR SNPP)")
        res[b] = {}
        for a in brazos:
            P = pub[a]
            m = {
                "recall": sum(P.get(k, 0) for k in al), "n_alertas": len(al),
                "protA_pub": sum(P.get(k, 0) for k in pa), "n_protA": len(pa),
                "neg_pub": sum(P.get(k, 0) for k in neg), "n_neg": len(neg),
                "mb_perd": sum(1 - P.get(k, 0) for k in mb_dec), "n_mb": len(mb_dec),
                "mb_perd_snpp": sum(1 - P.get(k, 0) for k in mb_snpp),
            }
            m["suma"] = m["mb_perd"] + m["neg_pub"]
            m["suma_con_snpp"] = m["suma"] + m["mb_perd_snpp"]
            if a != "C0":
                perdA = [k for k in pa if pub["C0"].get(k, 0) and not P.get(k, 0)]
                recA = [k for k in pa if not pub["C0"].get(k, 0) and P.get(k, 0)]
                perdB = [k for k in pb if pub["C0"].get(k, 0) and not P.get(k, 0)]
                m["P1A_netas"] = [k for k in perdA if not lab[k]["snpp_ocr"]]
                m["P1A_snpp"] = [k for k in perdA if lab[k]["snpp_ocr"]]
                m["P1A_recuperadas"] = recA
                m["P1B_perdidas"] = perdB
            res[b][a] = m
    p("")
    p("   P1 (lectura A): protegidas que C0 publica y el brazo no")
    for b in SENS:
        for a in brazos[1:]:
            m = res[b][a]
            p(f"      {a} {b:9s} netas {len(m['P1A_netas'])} | solo OCR SNPP {len(m['P1A_snpp'])} | recuperadas {len(m['P1A_recuperadas'])} | lectura B perdidas {len(m['P1B_perdidas'])}")
            for k in m["P1A_netas"] + m["P1A_snpp"]:
                p(f"         {'SNPP-OCR' if lab[k]['snpp_ocr'] else 'NETA'} {k} MIROVA {lab[k]['vrpA']}")
    p("")
    p("   P2 (lectura A): Muy Bajo perdidas + negativos limpios publicados")
    for b in SENS:
        for a in brazos:
            m = res[b][a]
            p(f"      {b:9s} {a:2s} Muy Bajo perdidas {m['mb_perd']:4d} de {m['n_mb']:4d} | negativos publicados {m['neg_pub']:4d} de {m['n_neg']:5d} "
              f"| suma {m['suma']:4d} (con SNPP solo OCR {m['suma_con_snpp']:4d})")
    p("")
    p("   Seccion 9: recall, protegidas A publicadas, negativos limpios publicados")
    for b in SENS:
        for a in brazos:
            m = res[b][a]
            pct = 100 * m["neg_pub"] / m["n_neg"] if m["n_neg"] else float("nan")
            p(f"      {b:9s} {a:2s} recall {m['recall']:4d} de {m['n_alertas']:4d} | protegidas A {m['protA_pub']:3d} de {m['n_protA']:3d} "
              f"| negativos limpios publicados {m['neg_pub']:4d} de {m['n_neg']:5d} ({pct:.1f} %)")
    return res, lab, pub, lin


def main():
    co, inner = coords(), inner_html()
    ctl = control_predicado()
    print("control del predicado (espera [1,0,0,0]):", ctl)
    assert ctl == [1, 0, 0, 0], ctl
    salida = {"control_predicado": ctl}
    todo = []
    for nombre, cfg in VENTANAS.items():
        res, lab, pub, lin = evaluar(nombre, cfg, co, inner)
        todo += lin + [""]
        ser = {}
        for b, porbr in res.items():
            ser[b] = {a: {kk: ([list(x) for x in vv] if isinstance(vv, list) else vv) for kk, vv in m.items()}
                      for a, m in porbr.items()}
        salida[nombre] = ser
        # volcado por pasada para auditar diferencias
        with open(OUT / f"pasadas_{nombre}.jsonl", "w", encoding="utf-8") as fh:
            for k, e in lab.items():
                fh.write(json.dumps({"k": list(k), **e, **{f"pub_{a}": pub[a].get(k) for a in pub}}) + "\n")
    (OUT / "resultado.json").write_text(json.dumps(salida, indent=1), encoding="utf-8")
    (OUT / "salida.txt").write_text("\n".join(todo), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
