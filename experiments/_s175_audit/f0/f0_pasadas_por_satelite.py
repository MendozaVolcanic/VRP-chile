"""F0 S175: pasadas que nunca bajamos, por satélite (mejora 5 de S174).

Fenómeno: un satélite que deja de entregar (Suomi NPP desde el 2026-11-02 13:00 UTC, o NOAA-21 si NASA cambia la
colección) no deja hueco en el tablero mientras otro satélite del mismo sensor pase esa noche. El recall del audit
semanal mira por sensor (MODIS, VIIRS375, VIIRS750) y por noche (`recall_por_sensor`, `noches_sin_datos`), así que
no ve la plataforma que se calla. Este script cuenta por satélite.

Insumos (todos de la base 752d348bc67190e53b610989877e2405d238a1bc, sin red):
- records: data/mirova_equivalent/<11 Tier A>.json, extraídos con git show a BASE_DATA.
- referencia: copia latest_consolidado.csv y registro_vrp_ocr.csv de la base (insumos de la ola 0).
- historia del audit: data/audit_continuous/latest.json en cada commit que lo tocó (git show, local).

Las dos preguntas del instrumento:
1. Si un satélite se callara, ¿lo vería? Sí: cuenta records por satélite y por semana; el control de mutación
   (quitar NOAA-21 de los últimos 14 días) tiene que bajar su conteo a 0 y dejar igual la métrica por sensor.
2. Si el instrumento estuviera muerto (no lee records), ¿se vería distinto? Sí: el control positivo exige
   records de NOAA-20 después del cese y records de Suomi NPP antes; un cero en ambos es instrumento muerto.
"""
import bisect
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
BASE_DATA = r"C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data"
INSUMOS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
CESE = datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)
TOL_S = 120  # clase_mirova.VENTANA_S en la base (scripts/clase_mirova.py:112)


def t(s):
    s = s.strip().replace("T", " ").replace("Z", "")
    fmt = "%Y-%m-%d %H:%M:%S" if s.count(":") == 2 else "%Y-%m-%d %H:%M"
    return datetime.strptime(s[:19] if s.count(":") == 2 else s[:16], fmt).replace(tzinfo=timezone.utc)


def bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


def norm(v):
    return re.sub(r"[^a-z]", "", v.lower())


NOMBRE = {norm(v): v for v in VOLS}


def cargar_records(quitar=None):
    """quitar: función(record) -> True para simular un satélite callado (control de mutación)."""
    out = []
    for v in VOLS:
        with open(f"{BASE_DATA}\\{v}.json", encoding="utf-8") as fh:
            for r in json.load(fh)["records"]:
                rr = {"vol": v, "sensor": r["sensor"], "t": t(r["datetime_utc"])}
                if quitar and quitar(rr):
                    continue
                out.append(rr)
    return out


def cargar_mirova():
    filas = []
    for nombre, canal in (("latest_consolidado_base.csv", "tabla"), ("snapshot_ocr_base.csv", "ocr")):
        with open(f"{INSUMOS}\\{nombre}", encoding="utf-8") as fh:
            for f in csv.DictReader(fh):
                v = NOMBRE.get(norm(f["Volcan"]))
                if not v:
                    continue
                try:
                    b = {"VIIRS": "VIIRS750"}.get(f["Sensor"].strip(), f["Sensor"].strip())  # MIROVA llama «VIIRS» al 750
                    filas.append({"vol": v, "b": b, "t": t(f["Fecha_Satelite_UTC"]),
                                  "canal": canal, "tipo": f.get("Tipo_Registro", ""),
                                  "vrp": f.get("VRP_MW", "")})
                except ValueError:
                    pass
    return filas


def semana(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def main():
    recs = cargar_records()
    print(f"# base {BASE}; records Tier A leídos: {len(recs)}; último record: {max(r['t'] for r in recs)}")
    sats = sorted({r["sensor"] for r in recs})

    # 1. Línea base roja: Suomi NPP después del cese
    print("\n## 1. Línea base roja: records Suomi NPP después de 2026-11-02 13:00 UTC")
    snpp_post = [r for r in recs if "SNPP" in r["sensor"] and r["t"] >= CESE]
    print(f"records SNPP (375 y 750) con t >= cese: {len(snpp_post)}")
    for s in ("VIIRS_SNPP", "VIIRS_SNPP_750"):
        ult = max((r["t"] for r in recs if r["sensor"] == s), default=None)
        print(f"  último {s}: {ult}")
    # control positivo
    n20_post = sum(1 for r in recs if r["sensor"].startswith("VIIRS_NOAA20") and r["t"] >= CESE)
    n21_post = sum(1 for r in recs if r["sensor"].startswith("VIIRS_NOAA21") and r["t"] >= CESE)
    snpp_pre = sum(1 for r in recs if "SNPP" in r["sensor"] and CESE - timedelta(days=4) <= r["t"] < CESE)
    print(f"control positivo: NOAA-20 tras el cese {n20_post}; NOAA-21 tras el cese {n21_post}; "
          f"SNPP en los 4 días previos al cese {snpp_pre}")
    print("ROJO REENCONTRADO" if (not snpp_post and n20_post and snpp_pre) else "ROJO NO REENCONTRADO / instrumento dudoso")

    # 2. Pasadas por satélite y semana (pasada = volcán + satélite + datetime distinto)
    print("\n## 2. Pasadas por satélite y semana ISO (11 Tier A; denominador: pasadas con record, todas las horas)")
    pas = defaultdict(set)
    for r in recs:
        pas[(r["sensor"], semana(r["t"]))].add((r["vol"], r["t"]))
    semanas = sorted({w for (_, w) in pas})[-12:]
    print("satélite," + ",".join(semanas))
    for s in sats:
        print(s + "," + ",".join(str(len(pas.get((s, w), ()))) for w in semanas))

    # 3. Último record por satélite y volcán, contra la última fila de MIROVA del mismo sensor
    mir = cargar_mirova()
    print(f"\n## 3. Último record por satélite y volcán contra la última fila MIROVA (tabla+OCR) del mismo sensor")
    print(f"filas MIROVA leídas (11 Tier A): {len(mir)}; última: {max(m['t'] for m in mir)}")
    ult_mir = {}
    for m in mir:
        k = (m["vol"], m["b"])
        ult_mir[k] = max(ult_mir.get(k, m["t"]), m["t"])
    ult_rec = {}
    for r in recs:
        k = (r["vol"], r["sensor"])
        ult_rec[k] = max(ult_rec.get(k, r["t"]), r["t"])
    print("volcan,satelite,ultimo_record,ultima_fila_mirova_sensor,horas_record_antes_que_mirova")
    for v in VOLS:
        for s in sats:
            ur = ult_rec.get((v, s))
            um = ult_mir.get((v, bucket(s)))
            dh = round((um - ur).total_seconds() / 3600, 1) if ur and um else None
            print(f"{v},{s},{ur},{um},{dh}")

    # 4. Filas MIROVA sin ningún record nuestro del mismo sensor a ±TOL_S (pasadas que MIROVA tiene y nosotros no)
    print(f"\n## 4. Filas MIROVA sin record nuestro del mismo sensor a ±{TOL_S} s, por semana y sensor")
    idx = defaultdict(list)
    for r in recs:
        idx[(r["vol"], bucket(r["sensor"]))].append(r["t"])
    for k in idx:
        idx[k].sort()
    pass
    hasta = max(r["t"] for r in recs)
    sin = Counter(); tot = Counter(); lista_post = []; lista_todas = []
    for m in mir:
        if m["t"] > hasta - timedelta(hours=6):
            continue  # cola: el NRT todavía no procesa lo último
        if m["t"].hour >= 12:
            continue  # pasada diurna (12-23 UTC): el NRT sólo procesa la noche (records de 00 a 09 UTC)
        k = (m["vol"], m["b"])
        ts = idx.get(k, [])
        i = bisect.bisect_left(ts, m["t"] - timedelta(seconds=TOL_S))
        ok = i < len(ts) and ts[i] <= m["t"] + timedelta(seconds=TOL_S)
        w = (semana(m["t"]), m["b"])
        tot[w] += 1
        if not ok:
            sin[w] += 1
            if m["t"] >= datetime(2026, 9, 14, tzinfo=timezone.utc):
                lista_todas.append(m)
            if m["t"] >= CESE and m["b"] != "MODIS":
                lista_post.append(m)
    print(f"(ventana: filas MIROVA nocturnas, 00 a 11 UTC, hasta {hasta - timedelta(hours=6)}; la cola de 6 h no se juzga)")
    print("semana,sensor,filas_mirova,sin_record_nuestro,pct")
    for w in sorted(tot):
        if w[0] < semanas[0]:
            continue
        print(f"{w[0]},{w[1]},{tot[w]},{sin[w]},{round(100*sin[w]/tot[w],1)}")
    print(f"\nfilas MIROVA VIIRS nocturnas después del cese sin record nuestro: {len(lista_post)}")
    for m in sorted(lista_post, key=lambda x: x["t"]):
        print(f"  {m['vol']} {m['b']} {m['t']:%Y-%m-%d %H:%M:%S} canal={m['canal']} tipo={m['tipo']} vrp={m['vrp']}")

    print(f"\n## 4c. Todas las filas MIROVA nocturnas sin record nuestro desde 2026-09-14 ({len(lista_todas)}), "
          "con el record nuestro más cercano del mismo sensor")
    for m in sorted(lista_todas, key=lambda x: (x["b"], x["t"])):
        ts = idx.get((m["vol"], m["b"]), [])
        j = bisect.bisect_left(ts, m["t"])
        cand = [x for x in ts[max(0, j - 1):j + 1]]
        dmin = min((abs((x - m["t"]).total_seconds()) for x in cand), default=None)
        print(f"  {m['b']} {m['vol']} {m['t']:%Y-%m-%d %H:%M:%S} canal={m['canal']} tipo={m['tipo']} vrp={m['vrp']} "
              f"record_mas_cercano_s={dmin}")

    # 4b. La noche del cese: filas MIROVA VIIRS375 nocturnas del 2026-10-31 al 2026-11-03 y su pareo
    print("\n## 4b. Filas MIROVA VIIRS375 nocturnas 2026-10-31 a 2026-11-03 (un volcán por hora; pareo a ±TOL_S)")
    vistos = set()
    for m in sorted(mir, key=lambda x: x["t"]):
        if m["b"] != "VIIRS375" or not (datetime(2026, 10, 31, tzinfo=timezone.utc) <= m["t"] < datetime(2026, 11, 4, tzinfo=timezone.utc)) or m["t"].hour >= 12:
            continue
        clave = (m["t"].strftime("%Y-%m-%d %H:%M"))
        if clave in vistos:
            continue
        vistos.add(clave)
        cerca = sorted({(r["sensor"], r["t"]) for r in recs if r["vol"] == m["vol"] and abs((r["t"] - m["t"]).total_seconds()) <= TOL_S})
        print(f"  {m['t']:%Y-%m-%d %H:%M:%S} {m['vol']}: {[s for s, _ in cerca] or 'SIN RECORD NUESTRO'}")

    # 5. Control de mutación: ¿la métrica por sensor y noche ve un satélite callado?
    print("\n## 5. Control de mutación: NOAA-21 callado los últimos 14 días")
    corte = hasta - timedelta(days=14)
    mut = cargar_records(quitar=lambda r: r["sensor"].startswith("VIIRS_NOAA21") and r["t"] >= corte)
    def noches_por_sensor(rs):
        return {(r["vol"], bucket(r["sensor"]), (r["t"] - timedelta(hours=12)).date()) for r in rs if r["t"] >= corte}
    a, b = noches_por_sensor(recs), noches_por_sensor(mut)
    print(f"volcán-sensor-noche con algún record, últimos 14 días: original {len(a)}, con NOAA-21 quitado {len(b)}")
    n21a = sum(1 for r in recs if r["sensor"].startswith("VIIRS_NOAA21") and r["t"] >= corte)
    n21b = sum(1 for r in mut if r["sensor"].startswith("VIIRS_NOAA21") and r["t"] >= corte)
    print(f"records NOAA-21 en la ventana: original {n21a}, mutado {n21b}")
    print("=> la métrica por satélite cae a 0; la de sensor y noche (la de noches_sin_datos) "
          + ("no cambia" if len(a) == len(b) else f"cambia en {len(a)-len(b)}"))

    # 6. Historia del audit semanal: noches_sin_datos por sensor
    print("\n## 6. noches_sin_datos por sensor en cada data/audit_continuous/latest.json (git, local)")
    log = subprocess.run(["git", "-C", REPO, "log", "--format=%h %cI", BASE, "--", "data/audit_continuous/latest.json"],
                         capture_output=True, text=True, encoding="utf-8").stdout.split("\n")
    print("commit,fecha,ventana,MODIS,VIIRS375,VIIRS750,plataformas_avisos")
    for ln in [x for x in log if x][:14]:
        h, f = ln.split()
        raw = subprocess.run(["git", "-C", REPO, "show", f"{h}:data/audit_continuous/latest.json"],
                             capture_output=True, text=True, encoding="utf-8").stdout
        try:
            d = json.loads(raw)
        except ValueError:
            print(f"{h},{f},ilegible"); continue
        rc = d.get("recall", {})
        nsd = [str(rc.get(s, {}).get("noches_sin_datos", "SIN CAMPO")) for s in ("MODIS", "VIIRS375", "VIIRS750")]
        pl = d.get("plataformas", "SIN CAMPO")
        pl_av = (pl.get("avisos") if isinstance(pl, dict) else pl)
        print(f"{h},{f},{d.get('window')},{','.join(nsd)},{json.dumps(pl_av, ensure_ascii=False)[:120]}")


if __name__ == "__main__":
    main()
