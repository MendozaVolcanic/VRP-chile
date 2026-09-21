# -*- coding: utf-8 -*-
"""S149, verificador con contexto limpio. Recuento INDEPENDIENTE del sustrato del pre-registro de
invierno. Lee los dos CSV del snapshot directamente (sin evaluar.py ni banco_paridad.py), con su
propia elevacion solar. Una pasada = (volcan, sensor, minuto); es alerta si CUALQUIER fila de esa
pasada tiene Tipo_Registro que empieza con ALERTA (CONS u OCR). Noche = elevacion solar <= 0."""
import csv, sys, io, math, collections, json
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
COORD = {"Lascar": (-23.37, -67.73), "Villarrica": (-39.42, -71.93), "Nevados de Chillan": (-36.86, -71.38),
         "Isluga": (-19.15, -68.83), "Lastarria": (-25.17, -68.50), "Tupungatito": (-33.40, -69.80),
         "PlanchonPeteroa": (-35.24, -70.57), "Llaima": (-38.69, -71.73), "Copahue": (-37.85, -71.17),
         "Puyehue-Cordon Caulle": (-40.59, -72.12), "Chaiten": (-42.83, -72.65)}
SENSOR = {"VIIRS": "VIIRS750", "VIIRS375": "VIIRS375", "MODIS": "MODIS"}


def elev_solar(lat, lon, dt):
    n = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60.0
    g = 2 * math.pi / 365.0 * (n - 1 + (h - 12) / 24.0)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = h * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4.0 - 180.0)
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)))


pasadas = {}
for nombre, fuente in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
    with open(SNAP / nombre, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            vol, b = r["Volcan"].strip(), SENSOR.get(r["Sensor"].strip())
            if vol not in COORD or b is None:
                continue
            dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
            k = (vol, b, dt.strftime("%Y-%m-%d %H:%M"))
            p = pasadas.setdefault(k, {"dt": dt, "tipos": set(), "fuentes": set(), "vrp": [], "fproc": []})
            p["tipos"].add(r["Tipo_Registro"]); p["fuentes"].add(fuente)
            try:
                p["vrp"].append(float(r["VRP_MW"]))
            except ValueError:
                pass
            p["fproc"].append(r.get("Fecha_Proceso_GitHub") or "")
for k, p in pasadas.items():
    la, lo = COORD[k[0]]
    p["elev"] = elev_solar(la, lo, p["dt"])
    p["noche"] = p["elev"] <= 0
    p["alerta"] = any(t.startswith("ALERTA") for t in p["tipos"])


def contar(v0, v1, solo_noche=True):
    c = collections.Counter()
    for (vol, b, m), p in pasadas.items():
        if v0 <= m[:10] <= v1 and p["alerta"] and (p["noche"] or not solo_noche):
            c[(b, vol)] += 1
    return c


print("== 1. Alertas por ventana (pasada = volcan, sensor, minuto; noche por elevacion solar propia)")
for nom, v in (("junio", ("2026-06-01", "2026-06-30")), ("julio", ("2026-07-01", "2026-07-31")),
               ("agosto 01-27", ("2026-08-01", "2026-08-27")), ("sept 01-20", ("2026-09-01", "2026-09-20"))):
    c, ct = contar(*v), contar(*v, solo_noche=False)
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        d = {vol: n for (bb, vol), n in c.items() if bb == b}
        dia = sum(n for (bb, _), n in ct.items() if bb == b) - sum(d.values())
        print("  %-13s %-8s noche %4d (diurnas excluidas %3d) | %s" % (nom, b, sum(d.values()), dia, dict(sorted(d.items(), key=lambda x: -x[1]))))

print("\n== 2. Doble conteo: pasadas de alerta nocturna con fila CONS y fila OCR en el mismo minuto (agosto 01-27 y junio)")
for v in (("2026-08-01", "2026-08-27"), ("2026-06-01", "2026-06-30")):
    n2 = sum(1 for (vol, b, m), p in pasadas.items() if v[0] <= m[:10] <= v[1] and p["alerta"] and p["noche"]
             and sum(1 for t in p["tipos"] if t.startswith("ALERTA")) > 1)
    print("  ", v, "pasadas con dos tipos de ALERTA en el mismo minuto:", n2)

print("\n== 3. Ventanas deslizantes de 27 dias, V375 nocturno, Villarrica + Chillan (del 2026-05-01 al 2026-08-27 como fin)")
d0 = date(2026, 3, 1)
mejor = []
while d0 + timedelta(days=26) <= date(2026, 8, 27):
    v = (d0.isoformat(), (d0 + timedelta(days=26)).isoformat())
    c = contar(*v)
    mejor.append((c[("VIIRS375", "Villarrica")] + c[("VIIRS375", "Nevados de Chillan")], c[("VIIRS375", "Villarrica")],
                  c[("VIIRS375", "Nevados de Chillan")], v))
    d0 += timedelta(days=1)
mejor.sort(reverse=True)
for x in mejor[:6]:
    print("   suma %2d (Villarrica %2d, Chillan %2d) ventana %s" % x)
ago = [x for x in mejor if x[3][0] == "2026-08-01"][0]
print("   la ventana del pre-registro:", ago, "| puesto", mejor.index(ago) + 1, "de", len(mejor))

print("\n== 4. Ventanas deslizantes de 30 dias, MODIS nocturno, Lascar (todo el snapshot)")
d0 = date(2026, 1, 10); m = []
while d0 + timedelta(days=29) <= date(2026, 9, 14):
    v = (d0.isoformat(), (d0 + timedelta(days=29)).isoformat())
    m.append((contar(*v)[("MODIS", "Lascar")], v)); d0 += timedelta(days=1)
m.sort(reverse=True)
for x in m[:5]:
    print("   %2d alertas MODIS Lascar en %s" % x)
print("   junio calendario:", [x for x in m if x[1][0] == "2026-06-01"])
lj = sorted((k[2], max(p["vrp"] or [None]), sorted(p["tipos"]), round(p["elev"], 1)) for k, p in pasadas.items()
            if k[0] == "Lascar" and k[1] == "MODIS" and "2026-06-01" <= k[2][:10] <= "2026-06-30" and p["alerta"] and p["noche"])
print("   detalle junio Lascar MODIS:")
for x in lj:
    print("     ", x)
print("   con 0,5 MW o mas:", sum(1 for x in lj if (x[1] or 0) >= 0.5), "de", len(lj))

print("\n== 5. Sustrato de P6: alertas nocturnas V375 de Villarrica y Chillan en agosto 01-27, con su VRP")
for vol in ("Villarrica", "Nevados de Chillan"):
    for b in ("VIIRS375", "VIIRS750"):
        xs = sorted((k[2], max(p["vrp"] or [None]), sorted(p["tipos"])) for k, p in pasadas.items() if k[0] == vol and k[1] == b
                    and "2026-08-01" <= k[2][:10] <= "2026-08-27" and p["alerta"] and p["noche"])
        print("  ", vol, b, "n", len(xs), "| con 0,15 MW o mas:", sum(1 for x in xs if (x[1] or 0) >= 0.15), "| con 0,5 o mas:", sum(1 for x in xs if (x[1] or 0) >= 0.5))
        for x in xs:
            print("       ", x)

print("\n== 6. Regimen del scraper dentro de las ventanas: filas CONS por dia (huecos) y version del OCR")
for v in (("2026-08-01", "2026-08-27"), ("2026-06-01", "2026-06-30")):
    por_dia = collections.Counter(m[:10] for (vol, b, m), p in pasadas.items() if v[0] <= m[:10] <= v[1] and "CONS" in p["fuentes"])
    dias = [(date.fromisoformat(v[0]) + timedelta(days=i)).isoformat() for i in range((date.fromisoformat(v[1]) - date.fromisoformat(v[0])).days + 1)]
    vals = [por_dia.get(d, 0) for d in dias]
    print("  ", v, "filas CONS por dia: min %d mediana %d max %d | dias bajo la mitad de la mediana: %s"
          % (min(vals), sorted(vals)[len(vals) // 2], max(vals), [(d, por_dia.get(d, 0)) for d in dias if por_dia.get(d, 0) < sorted(vals)[len(vals) // 2] / 2]))
with open(SNAP / "registro_vrp_ocr.csv", encoding="utf-8") as fh:
    ver = collections.defaultdict(collections.Counter)
    for r in csv.DictReader(fh):
        ver[r["Fecha_Satelite_UTC"][:7]][(r.get("Version_OCR") or "?", r.get("Metodo_Validacion") or "?")] += 1
for mes in sorted(ver):
    if mes >= "2026-05":
        print("   OCR", mes, dict(ver[mes]))

print("\n== 7. Filas por plataforma no disponibles en el CSV (sin columna de satelite): SIN VERIFICAR el 60 % de SNPP")
print("\n== 8. RUTINA VRP 0 en noche de volcan con alerta, V375, agosto 01-27 (sustrato de P5, en filas de referencia)")
noches_alerta = {(k[0], k[2][:10]) for k, p in pasadas.items() if p["alerta"] and p["noche"]}
n5 = collections.Counter()
for (vol, b, mm), p in pasadas.items():
    if b == "VIIRS375" and "2026-08-01" <= mm[:10] <= "2026-08-27" and p["noche"] and not p["alerta"] \
            and p["tipos"] == {"RUTINA"} and max(p["vrp"] or [0]) == 0 and (vol, mm[:10]) in noches_alerta:
        n5[vol] += 1
print("   total", sum(n5.values()), dict(n5))
