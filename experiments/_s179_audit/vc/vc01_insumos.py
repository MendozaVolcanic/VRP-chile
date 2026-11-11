# -*- coding: utf-8 -*-
"""Verificador VC, S179. vc01: arma los insumos de la retrospectiva con codigo propio (no reusa c01 del auditor).

QUE HACE. (1) VIA = union de los trozos de D2 y D4 (carpetas trozo-* de C:/Users/nmend/vrp-temporales/s177_d2 y
s177_d4); K-gemelo = trozos de D3. Si una clave (volcan, sensor, hora) sale en dos trozos, se cuenta. (2) K de disco =
data/mirova_equivalent/<volcan>.json de los 11 Tier A en e7cfbaf54, sin recortar (el lector recorta). (3) Compara K de
disco de 47cdc446f, a7a6ae360 y e7cfbaf54 dentro de las ventanas de los tramos (afirmacion 517).

PREGUNTAS DEL INSTRUMENTO. (1) Si el aplanado estuviera roto, lo veria? Cuenta trozos, records y repetidas; el uso
siguiente (vc02) re-corre el lector y compara su JSON con el commiteado: un aplanado roto no lo reproduce. (2) Si el
instrumento estuviera muerto? 0 records aborta. Control positivo de (3): fuera de las ventanas K TIENE que diferir
entre commits (el NRT escribe a diario): se imprime el total de cada commit.
Salida: D:/vrp-trabajo/temporales/s179-audit/vc/insumos/{via,kgemelo,k_e7cfbaf54}/
"""
import collections, json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
ART = "C:/Users/nmend/vrp-temporales"
OUT = "D:/vrp-trabajo/temporales/s179-audit/vc/insumos"
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Copahue", "Llaima", "Villarrica", "NevadosDeChillan"]
VENT = [("2025-02-15", "2025-12-31"), ("2026-02-01", "2026-03-31"), ("2026-10-01", "2026-10-16")]


def aplanar(carpetas, nombre):
    por = collections.defaultdict(dict)
    n_tr, rep = 0, 0
    for c in carpetas:
        for t in sorted(os.listdir(f"{ART}/{c}")):
            if not t.startswith("trozo-"):
                continue
            js = [x for x in os.listdir(f"{ART}/{c}/{t}") if x.endswith(".json")]
            for j in js:
                d = json.load(open(f"{ART}/{c}/{t}/{j}", encoding="utf-8"))
                n_tr += 1
                for r in d["records"]:
                    k = (r.get("sensor"), r.get("datetime_utc"))
                    rep += k in por[d["volcano"]]
                    por[d["volcano"]][k] = r
    os.makedirs(f"{OUT}/{nombre}", exist_ok=True)
    tot = 0
    for v, recs in por.items():
        json.dump({"volcano": v, "records": list(recs.values())}, open(f"{OUT}/{nombre}/{v}.json", "w", encoding="utf-8"))
        tot += len(recs)
    print(f"{nombre}: archivos json de trozo {n_tr}; volcanes {len(por)}; records {tot}; claves repetidas {rep}")
    if not tot:
        sys.exit("ABORTA: 0 records")


def k_git(commit):
    out = {}
    for v in TIER_A:
        s = subprocess.run(["git", "-C", REPO, "show", f"{commit}:data/mirova_equivalent/{v}.json"],
                           capture_output=True, check=True).stdout
        out[v] = json.loads(s)
    return out


def en_v(d):
    return any(a <= (d or "")[:10] <= b for a, b in VENT)


aplanar(["s177_d2", "s177_d4"], "via")
aplanar(["s177_d3"], "kgemelo")
ks = {c: k_git(c) for c in ("e7cfbaf54", "a7a6ae360", "47cdc446f")}
os.makedirs(f"{OUT}/k_e7cfbaf54", exist_ok=True)
for v, d in ks["e7cfbaf54"].items():
    json.dump(d, open(f"{OUT}/k_e7cfbaf54/{v}.json", "w", encoding="utf-8"))
dic = {}
for c, por in ks.items():
    dic[c] = {(v, r.get("sensor"), r.get("datetime_utc")): json.dumps(r, sort_keys=True)
              for v, d in por.items() for r in d["records"]}
    print(f"K {c}: records totales {len(dic[c])}; en ventanas {sum(en_v(k[2]) for k in dic[c])}")
for c in ("a7a6ae360", "47cdc446f"):
    a = {k: x for k, x in dic[c].items() if en_v(k[2])}
    b = {k: x for k, x in dic["e7cfbaf54"].items() if en_v(k[2])}
    print(f"K {c} contra e7cfbaf54 en ventanas: iguales {sum(a[k] == b.get(k) for k in a)}; distintos "
          f"{sum(k in b and a[k] != b[k] for k in a)}; solo en {c} {len(set(a) - set(b))}; solo en e7cfbaf54 {len(set(b) - set(a))}")
    fa = {k: x for k, x in dic[c].items() if not en_v(k[2])}
    fb = {k: x for k, x in dic["e7cfbaf54"].items() if not en_v(k[2])}
    print(f"   control positivo fuera de ventanas: claves solo en uno {len(set(fa) ^ set(fb))}; distintos "
          f"{sum(k in fb and fa[k] != fb[k] for k in fa)}")
