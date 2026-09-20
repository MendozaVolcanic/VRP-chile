"""S145 D26 - La interseccion que decide el veredicto: records donde el segundo
pase SI recaptura Y ademas el umbral NO lo fija el piso C1.

POR QUE: "efecto nulo bajo la conectiva min" solo es cierto en los records donde
min(C1, mu + C2*sigma) devuelve C1 en los cuatro umbrales, porque solo ahi
ensuciar sigma deja el umbral quieto. Donde el termino estadistico es el menor,
el umbral depende del pool, y si ademas el segundo pase esta recapturando
pixeles, el pool sucio tiene por donde mover la mascara publicada.

PROXY DECLARADO: mu y sigma persistidos son los del PRIMER pase (fp_diag). El
pool del segundo pase no se persiste en ningun campo, asi que esta interseccion
usa el primer pase como proxy del regimen de cada escena. No es el pool que D26
denuncia; es la mejor cota disponible sin reprocesar granules.

Salida: 05_d26_interseccion.json
"""
import json
import glob
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "05_d26_interseccion.json"
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(ROOT))
import pipeline.profile as prof  # noqa: E402

C1S, C1E = prof.DNTI_CONTEXTUAL_C1_SUMMIT, prof.DNTI_CONTEXTUAL_C1_SCENE
UMBRALES = [
    ("dnti_summit", "dnti", prof.C2_DNTI_SUMMIT_NIGHT, C1S),
    ("dnti_scene", "dnti", prof.C2_DNTI_SCENE_NIGHT, C1E),
    ("deti_summit", "deti", prof.C2_DETI_SUMMIT_NIGHT, C1S),
    ("deti_scene", "deti", prof.C2_DETI_SCENE_NIGHT, C1E),
]


def bucket(sensor):
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "OTRO"


st = defaultdict(lambda: defaultdict(int))
ejemplos = defaultdict(list)

for f in sorted(glob.glob(str(ROOT / "data/mirova_equivalent/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    vol = Path(f).stem
    for r in recs:
        b = bucket(r.get("sensor"))
        if b == "OTRO":
            continue
        mu = {"dnti": r.get("diag_mu_dnti"), "deti": r.get("diag_mu_deti")}
        sd = {"dnti": r.get("diag_sd_dnti"), "deti": r.get("diag_sd_deti")}
        rec = r.get("diag_n_second_pass_recapture")
        if rec is None or any(v is None for v in mu.values()) \
                or any(v is None for v in sd.values()):
            st[b]["sin_datos"] += 1
            continue
        st[b]["evaluables"] += 1
        sigma_manda = [n for n, ax, c2, c1 in UMBRALES
                       if mu[ax] + c2 * sd[ax] <= c1]
        hay_recaptura = rec > 0
        if hay_recaptura:
            st[b]["con_recaptura"] += 1
        if sigma_manda:
            st[b]["con_sigma_gobernando"] += 1
        if hay_recaptura and sigma_manda:
            st[b]["EXPUESTOS_recaptura_y_sigma"] += 1
            st[b]["pixeles_recapturados_en_expuestos"] += int(rec)
            for n in sigma_manda:
                st[b][f"expuesto_por__{n}"] += 1
            if "deti_summit" in sigma_manda or "dnti_summit" in sigma_manda:
                st[b]["EXPUESTOS_en_umbral_SUMMIT"] += 1
                if len(ejemplos[b]) < 6:
                    ejemplos[b].append({
                        "volcan": vol, "datetime_utc": r.get("datetime_utc"),
                        "sensor": r.get("sensor"),
                        "recaptura": rec,
                        "n_first_pass_pixels": r.get("diag_n_first_pass_pixels"),
                        "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                        "vrp_mw": r.get("vrp_mw"),
                        "umbrales_gobernados_por_sigma": sigma_manda,
                    })


def pct(a, b):
    return round(100.0 * a / b, 3) if b else None


out = {"definiciones": {
    "EXPUESTOS_recaptura_y_sigma": "el segundo pase agrego pixeles Y al menos uno "
                                   "de los cuatro umbrales lo fija mu + C2*sigma, "
                                   "no el piso C1",
    "EXPUESTOS_en_umbral_SUMMIT": "de esos, los que tienen sigma gobernando un "
                                  "umbral de CUMBRE (el ROI que publica)",
    "proxy": "mu/sigma del PRIMER pase (fp_diag); el pool del segundo pase no se "
             "persiste",
}, "por_bucket": {}}
for b in sorted(st):
    n = st[b]["evaluables"]
    out["por_bucket"][b] = {
        "conteos": dict(sorted(st[b].items())),
        "porcentajes_sobre_evaluables": {
            k: pct(v, n) for k, v in sorted(st[b].items())
            if k.startswith(("con_", "EXPUESTOS", "expuesto_"))},
        "ejemplos_summit": ejemplos[b],
    }

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for b, v in out["por_bucket"].items():
    print(f"\n== {b}  evaluables={v['conteos']['evaluables']}")
    for k, p in v["porcentajes_sobre_evaluables"].items():
        print(f"   {k:42s} {v['conteos'][k]:7d}  {p} %")
