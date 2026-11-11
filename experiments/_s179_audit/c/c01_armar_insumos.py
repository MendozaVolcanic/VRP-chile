# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c01: arma los insumos de la retrospectiva con codigo propio.

QUE HACE. (1) Aplana los trozos de D2 y D4 (brazo VIA) y de D3 (K-gemelo) desde los artefactos en
C:/Users/nmend/vrp-temporales/s177_d{2,3,4}; (2) saca K de disco de git (commit dado) y lo recorta a las ventanas
de los tramos del pre-registro; (3) compara K de disco entre commits (47cdc446f del pre-registro, a7a6ae360 del tag
de despacho, e7cfbaf54 de la lectura) dentro de las ventanas.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el aplanado de la lectura estuviera roto (trozos faltantes o repetidos), lo veria? Si: cuenta trozos, records
   y claves repetidas, y los numeros se cruzan con pasadas_por_tramo de lectura.json en c02.
2. Si este instrumento estuviera muerto, se veria distinto? Si: 0 records o 0 archivos sale escrito y aborta.
Control positivo: K de e7cfbaf54 y de a7a6ae360 TIENEN que diferir fuera de las ventanas (el NRT escribe todos los
dias); se imprime el conteo total de records de cada commit.

Uso: python c01_armar_insumos.py   (salida: stdout; datos en D:/vrp-trabajo/temporales/s179-audit/c/insumos/)
"""
import collections, hashlib, json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
ART = "C:/Users/nmend/vrp-temporales"
OUT = "D:/vrp-trabajo/temporales/s179-audit/c/insumos"
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Copahue", "Llaima", "Villarrica", "NevadosDeChillan"]
VENTANAS = [("2025-02-15", "2025-12-31"), ("2026-02-01", "2026-03-31"), ("2026-10-01", "2026-10-16")]


def en_ventana(dts):
    d = (dts or "")[:10]
    return any(a <= d <= b for a, b in VENTANAS)


def aplanar(dirs, nombre):
    pat = re.compile(r"trozo-(.+?)-(\d+)-(\d{4}-\d\d-\d\d)_(\d{4}-\d\d-\d\d)-intento-(\d+)$")
    por_vol = collections.defaultdict(dict)
    rep, rep_dist, n_trozos = [], [], collections.Counter()
    intentos = collections.Counter()
    for d in dirs:
        grupos = collections.defaultdict(list)
        for n in sorted(os.listdir(f"{ART}/{d}")):
            m = pat.match(n)
            if m:
                vol, idx, ini, fin, it = m.groups()
                grupos[(vol, int(idx), ini, fin)].append((int(it), n))
        for (vol, idx, ini, fin), its in sorted(grupos.items()):
            its.sort()
            it, n = its[-1]
            intentos[(d, it, len(its))] += 1
            p = f"{ART}/{d}/{n}/{vol}.json"
            if not os.path.exists(p):
                print(f"  SIN JSON: {d}/{n}")
                continue
            n_trozos[(d, vol)] += 1
            for r in json.load(open(p, encoding="utf-8"))["records"]:
                k = (r.get("sensor"), r.get("datetime_utc"))
                if k in por_vol[vol]:
                    rep.append((vol,) + k)
                    if json.dumps(por_vol[vol][k], sort_keys=True) != json.dumps(r, sort_keys=True):
                        rep_dist.append((vol,) + k)
                por_vol[vol][k] = r
    os.makedirs(f"{OUT}/{nombre}", exist_ok=True)
    tot = 0
    for vol, recs in sorted(por_vol.items()):
        rs = [recs[k] for k in sorted(recs, key=lambda x: (str(x[0]), str(x[1])))]
        tot += len(rs)
        json.dump({"volcano": vol, "records": rs}, open(f"{OUT}/{nombre}/{vol}.json", "w", encoding="utf-8"))
    print(f"== {nombre}: carpetas {dirs}; trozos {sum(n_trozos.values())}; volcanes {len(por_vol)}; records {tot}; "
          f"claves repetidas entre trozos {len(rep)} (con contenido distinto {len(rep_dist)})")
    print("   trozos por (carpeta, intento final, n intentos en disco):", dict(intentos))
    if rep_dist:
        print("   REPETIDAS DISTINTAS:", rep_dist[:10])
    if not tot:
        sys.exit("ABORTA: 0 records")
    return por_vol


def k_de_git(commit, guardar=None):
    out = {}
    tot_todo = 0
    for vol in TIER_A:
        raw = subprocess.run(["git", "-C", REPO, "show", f"{commit}:data/mirova_equivalent/{vol}.json"],
                             capture_output=True, check=True).stdout
        d = json.loads(raw.decode("utf-8"))
        tot_todo += len(d["records"])
        rs = [r for r in d["records"] if en_ventana(r.get("datetime_utc"))]
        out[vol] = rs
        if guardar:
            os.makedirs(f"{OUT}/{guardar}", exist_ok=True)
            json.dump({"volcano": vol, "records": rs}, open(f"{OUT}/{guardar}/{vol}.json", "w", encoding="utf-8"))
    n = sum(len(v) for v in out.values())
    print(f"== K de disco {commit}: records totales {tot_todo}; dentro de las ventanas {n}")
    if not n:
        sys.exit("ABORTA: 0 records de K")
    return out


def huella(rs):
    return {(r.get("sensor"), r.get("datetime_utc")): hashlib.sha256(
        json.dumps(r, sort_keys=True).encode()).hexdigest() for r in rs}


def comparar(a, b, na, nb):
    solo_a = solo_b = dist = igual = 0
    ej = []
    campos = collections.Counter()
    for vol in TIER_A:
        ha, hb = huella(a[vol]), huella(b[vol])
        ra = {(r.get("sensor"), r.get("datetime_utc")): r for r in a[vol]}
        rb = {(r.get("sensor"), r.get("datetime_utc")): r for r in b[vol]}
        for k in set(ha) | set(hb):
            if k not in hb:
                solo_a += 1; ej.append(("solo " + na, vol) + k)
            elif k not in ha:
                solo_b += 1; ej.append(("solo " + nb, vol) + k)
            elif ha[k] != hb[k]:
                dist += 1
                for c in set(ra[k]) | set(rb[k]):
                    if ra[k].get(c) != rb[k].get(c):
                        campos[c] += 1
                if len(ej) < 12:
                    ej.append(("distinto", vol) + k)
            else:
                igual += 1
    print(f"== K {na} contra K {nb}, dentro de las ventanas (R25, F26, DM): iguales {igual}; distintos {dist}; "
          f"solo en {na} {solo_a}; solo en {nb} {solo_b}")
    if campos:
        print("   campos que cambian:", dict(campos.most_common(12)))
    for e in ej[:12]:
        print("   ", e)


if __name__ == "__main__":
    print("ventanas:", VENTANAS)
    aplanar(["s177_d2", "s177_d4"], "via")
    aplanar(["s177_d3"], "kgemelo")
    k_lect = k_de_git("e7cfbaf54", guardar="k_e7cfbaf54")
    k_tag = k_de_git("a7a6ae360")
    k_pre = k_de_git("47cdc446f")
    comparar(k_tag, k_lect, "a7a6ae360 (tag de despacho)", "e7cfbaf54 (lectura)")
    comparar(k_pre, k_lect, "47cdc446f (pre-registro §7)", "e7cfbaf54 (lectura)")
