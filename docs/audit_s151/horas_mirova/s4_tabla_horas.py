"""s4: tabla de horas de pasada y de atraso de publicacion, por sensor, plataforma, regimen y dia/noche.
- Plataforma: se cruza cada pasada de MIROVA con los records de VRP Chile (origin/main) del mismo
  tipo de sensor a +-4 min (el gránulo es el mismo para todos los volcanes).
- Atraso: Fecha_Proceso_GitHub (hora America/Santiago de la corrida que vio la fila por primera vez,
  validado contra commits en s3) pasado a UTC, y el commit siguiente como reloj (lista de commits de s2).
Uso: python s4_tabla_horas.py cons.csv commits_verano.csv commits_invierno2.csv RUTA_REPO_VRP
"""
import sys, io, json, subprocess, bisect
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pandas as pd, numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
Z = ZoneInfo("America/Santiago")
cons_p, cv_p, ci_p, repo = sys.argv[1:5]
VOLS = ["Villarrica", "Llaima", "Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Copahue",
        "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle", "Chaiten"]

# --- plataforma desde records VRP Chile
plat = {"MODIS": [], "VIIRS375": [], "VIIRS": []}
for v in VOLS:
    r = subprocess.run(["git", "-C", repo, "show", f"origin/main:data/mirova_equivalent/{v}.json"],
                       capture_output=True)
    if r.returncode != 0:
        print("sin archivo", v); continue
    for rec in json.loads(r.stdout.decode("utf-8"))["records"]:
        s = rec.get("sensor", ""); t = rec.get("datetime_utc")
        if not t: continue
        t = datetime.strptime(t[:16], "%Y-%m-%d %H:%M")
        if s.startswith("MODIS"):
            plat["MODIS"].append((t, s.replace("MODIS_", "").title()))
        elif s.endswith("_750"):
            plat["VIIRS"].append((t, s.split("_")[1]))
        elif s.startswith("VIIRS"):
            plat["VIIRS375"].append((t, s.split("_")[1]))
for k in plat:
    plat[k] = sorted(set(plat[k])); print("records de plataforma", k, len(plat[k]))
idx = {k: [x[0] for x in v] for k, v in plat.items()}

def plataforma(sensor, t):
    L, T = plat.get(sensor, []), idx.get(sensor, [])
    i = bisect.bisect_left(T, t - timedelta(minutes=4))
    cands = set()
    while i < len(T) and T[i] <= t + timedelta(minutes=4):
        cands.add(L[i][1]); i += 1
    return cands.pop() if len(cands) == 1 else ("ambigua" if cands else "sin_cruce")

d = pd.read_csv(cons_p)
d["u"] = pd.to_datetime(d.Fecha_Satelite_UTC)
VENT = {"verano (UTC-3)": ("2026-09-07", "2026-10-15"), "invierno (UTC-4)": ("2026-07-26", "2026-09-06")}
commits = {}
for nombre, p in [("verano (UTC-3)", cv_p), ("invierno (UTC-4)", ci_p)]:
    c = pd.concat([pd.read_csv(x) for x in p.split(",")]).drop_duplicates("sha"); commits[nombre] = sorted(pd.to_datetime(c.committer_utc).dt.tz_convert(None))

def hhmm(m):  # minutos del dia -> HH:MM
    m = int(round(m)) % 1440; return f"{m//60:02d}:{m%60:02d}"

def mediana_circ(mins):
    # mediana de minutos del dia, tolerante al cruce de medianoche (pivote en la mediana circular aprox.)
    a = np.array(mins) * 2 * np.pi / 1440
    c = np.angle(np.mean(np.exp(1j * a))) * 1440 / (2 * np.pi)
    x = ((np.array(mins) - c + 720) % 1440) - 720
    return (np.median(x) + c) % 1440, np.percentile(x, 10) + c, np.percentile(x, 90) + c

filas_tab = []
for nombre, (a, b) in VENT.items():
    w = d[(d.u >= a) & (d.u < b)].copy()
    # una fila por pasada (gránulo), no por volcan
    w["plat"] = [plataforma(s, t.to_pydatetime()) for s, t in zip(w.Sensor, w.u)]
    w["noche"] = w.u.dt.hour < 11
    # de dia no hay records VRP Chile (solo noche): MODIS se separa por hora (Terra 10:30 / Aqua 13:30 hora solar)
    m = (w.plat == "sin_cruce") & (w.Sensor == "MODIS") & ~w.noche
    w.loc[m & (w.u.dt.hour < 16), "plat"] = "Terra (por hora)"
    w.loc[m & (w.u.dt.hour >= 16), "plat"] = "Aqua (por hora)"
    w.loc[(w.plat == "sin_cruce") & ~w.noche, "plat"] = "las 3 (sin separar)"
    fp = pd.to_datetime(w.Fecha_Proceso_GitHub, errors="coerce")
    fpu = fp.dt.tz_localize(Z, ambiguous="NaT", nonexistent="NaT").dt.tz_convert(None)
    w["fproc_utc"] = fpu
    C = commits[nombre]
    def commit_sig(t):
        if pd.isna(t): return pd.NaT
        i = bisect.bisect_left(C, t)
        return C[i] if i < len(C) else pd.NaT
    w["commit_utc"] = [commit_sig(t) for t in w.fproc_utc]
    def commit_prev(t):
        if pd.isna(t): return pd.NaT
        i = bisect.bisect_left(C, t)
        return C[i-1] if i > 0 else pd.NaT
    w["commit_prev"] = [commit_prev(t) for t in w.commit_utc]
    w["espera_min"] = (w.commit_utc - w.commit_prev).dt.total_seconds() / 60
    gaps = pd.Series(np.diff(np.array(C, dtype="datetime64[s]")).astype(float) / 60)
    print(f"  separacion entre commits del scraper (min): mediana {gaps.median():.1f} p90 {gaps.quantile(.9):.1f} p99 {gaps.quantile(.99):.1f} max {gaps.max():.1f}; huecos > 15 min: {(gaps > 15).sum()}")
    w["d_fproc_commit_min"] = (w.commit_utc - w.fproc_utc).dt.total_seconds() / 60
    w["atraso_h"] = (w.commit_utc - w.u).dt.total_seconds() / 3600
    w["pub_cl"] = w.commit_utc.dt.tz_localize("UTC").dt.tz_convert(Z)
    print(f"\n===== {nombre}: pasadas {a} a {b}, {len(w)} filas, {w.u.nunique()} instantes de pasada")
    print("  plataforma:", w.drop_duplicates(["u", "Sensor"]).plat.value_counts().to_dict())
    print(f"  commit - Fecha_Proceso (Santiago->UTC), min: mediana {w.d_fproc_commit_min.median():.2f} p99 {w.d_fproc_commit_min.quantile(.99):.2f} max {w.d_fproc_commit_min.max():.2f}; sin commit: {w.commit_utc.isna().sum()}")
    for (sens, pl, noche), g in w.groupby(["Sensor", "plat", "noche"]):
        gp = g.drop_duplicates("u")       # una por pasada para la hora
        mins = (gp.u.dt.hour * 60 + gp.u.dt.minute + gp.u.dt.second / 60).tolist()
        med, p10, p90 = mediana_circ(mins)
        off = -3 if "verano" in nombre else -4
        # atraso: primera aparicion de la pasada (minimo entre volcanes de la misma pasada)
        ga = g.sort_values("commit_utc").groupby("u").agg(atraso_h=("atraso_h", "min"), pub=("commit_utc", "min"), esp=("espera_min", "first")).dropna()
        pubcl = [(t + timedelta(hours=off)) for t in ga.pub]
        pmins = [t.hour * 60 + t.minute for t in pubcl]
        pmed = mediana_circ(pmins)[0] if pmins else np.nan
        filas_tab.append(dict(regimen=nombre, sensor=sens, plataforma=pl, periodo="noche" if noche else "dia",
                              n_pasadas=len(gp), utc_med=hhmm(med), utc_p10_p90=f"{hhmm(p10)}-{hhmm(p90)}",
                              chile_med=hhmm(med + off * 60), chile_p10_p90=f"{hhmm(p10 + off*60)}-{hhmm(p90 + off*60)}",
                              atraso_med_h=round(ga.atraso_h.median(), 2) if len(ga) else None,
                              atraso_p90_h=round(ga.atraso_h.quantile(.9), 2) if len(ga) else None,
                              espera_scraper_max_med_min=round(ga.esp.median(), 1) if len(ga) else None,
                              espera_scraper_max_p90_min=round(ga.esp.quantile(.9), 1) if len(ga) else None,
                              publica_chile_med=hhmm(pmed) if pmins else None, n_atraso=len(ga)))
    # atraso de filas individuales tambien (para ver re-escrituras tardias)
    print("  atraso por fila (h): mediana", round(w.atraso_h.median(), 2), "p90", round(w.atraso_h.quantile(.9), 2),
          "max", round(w.atraso_h.max(), 1), "| filas con atraso > 24 h:", int((w.atraso_h > 24).sum()))
tab = pd.DataFrame(filas_tab)
pd.set_option("display.width", 250)
print("\n", tab.to_string(index=False))
tab.to_csv("s4_tabla.csv", index=False)
