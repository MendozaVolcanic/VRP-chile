"""S145 D26 - Cuanto manda el piso C1 y cuanto el termino estadistico mu + C2*sigma.

POR QUE: el catalogo declara D26 con "efecto nulo bajo la conectiva min". Ese
veredicto es un silogismo, no una medicion propia: si el umbral efectivo es
min(C1, mu + C2*sigma) y el piso C1 siempre es el menor, entonces ensuciar el
sigma no mueve el umbral. El veredicto cae si (a) la conectiva cambia o (b) hay
records donde el termino estadistico SI es el menor. Aca se mide (b) sobre el
corpus entero, con la ventana declarada (A90).

LIMITE DECLARADO: los diagnosticos persistidos (diag_mu_dnti, diag_sd_dnti,
diag_mu_deti, diag_sd_deti) vienen de fp_diag, o sea del PRIMER pase
(process_modis.py:1540-1549 y equivalentes). El pool del SEGUNDO pase, que es
el que D26 denuncia, no se persiste en ningun campo. Lo que este script mide
es la premisa "el piso gobierna" sobre el primer pase; para el segundo pase la
premisa queda sin verificar desde disco.

Salida: 02_d26_piso_vs_sigma.json
"""
import json
import glob
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "02_d26_piso_vs_sigma.json"
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(ROOT))
import pipeline.profile as prof  # noqa: E402

C1_SUM = prof.DNTI_CONTEXTUAL_C1_SUMMIT
C1_SCE = prof.DNTI_CONTEXTUAL_C1_SCENE
C2_DNTI_SUM = prof.C2_DNTI_SUMMIT_NIGHT
C2_DNTI_SCE = prof.C2_DNTI_SCENE_NIGHT
C2_DETI_SUM = prof.C2_DETI_SUMMIT_NIGHT
C2_DETI_SCE = prof.C2_DETI_SCENE_NIGHT
assert prof.C1_SUMMIT_OVERRIDE is None and prof.C2_SUMMIT_OVERRIDE is None
assert prof.VIIRS_C2_OVERRIDE_NIGHT is None


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
ventana = defaultdict(lambda: ["9999", "0000"])
ejemplos = defaultdict(list)
margen = defaultdict(list)

for f in sorted(glob.glob(str(ROOT / "data/mirova_equivalent/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    vol = Path(f).stem
    for r in recs:
        b = bucket(r.get("sensor"))
        if b == "OTRO":
            continue
        st[b]["n_records"] += 1
        dt = str(r.get("datetime_utc") or "")
        if dt:
            ventana[b][0] = min(ventana[b][0], dt)
            ventana[b][1] = max(ventana[b][1], dt)
        mu_n, sd_n = r.get("diag_mu_dnti"), r.get("diag_sd_dnti")
        mu_e, sd_e = r.get("diag_mu_deti"), r.get("diag_sd_deti")
        if mu_n is None or sd_n is None or mu_e is None or sd_e is None:
            st[b]["sin_diag_mu_sigma"] += 1
            continue
        st[b]["con_diag_mu_sigma"] += 1
        # Los cuatro umbrales que el codigo arma por record (dual-ROI).
        casos = {
            "dnti_summit": (mu_n + C2_DNTI_SUM * sd_n, C1_SUM),
            "dnti_scene": (mu_n + C2_DNTI_SCE * sd_n, C1_SCE),
            "deti_summit": (mu_e + C2_DETI_SUM * sd_e, C1_SUM),
            "deti_scene": (mu_e + C2_DETI_SCE * sd_e, C1_SCE),
        }
        manda_piso_en_los_4 = True
        for nombre, (estad, c1) in casos.items():
            if estad > c1:
                st[b][f"piso_gobierna__{nombre}"] += 1
                margen[(b, nombre)].append(estad / c1)
            else:
                st[b][f"sigma_gobierna__{nombre}"] += 1
                manda_piso_en_los_4 = False
                if len(ejemplos[(b, nombre)]) < 5:
                    ejemplos[(b, nombre)].append({
                        "volcan": vol, "datetime_utc": dt,
                        "sensor": r.get("sensor"),
                        "mu": mu_n if "dnti" in nombre else mu_e,
                        "sd": sd_n if "dnti" in nombre else sd_e,
                        "mu_mas_c2_sigma": round(estad, 6), "c1": c1,
                    })
        if manda_piso_en_los_4:
            st[b]["piso_gobierna_los_4_umbrales"] += 1
        else:
            st[b]["algun_umbral_lo_decide_sigma"] += 1


def pct(a, b):
    return round(100.0 * a / b, 3) if b else None


out = {
    "definiciones": {
        "piso_gobierna": "min(C1, mu + C2*sigma) == C1, o sea mu + C2*sigma > C1: "
                         "ensuciar sigma NO mueve el umbral",
        "sigma_gobierna": "mu + C2*sigma <= C1: el termino estadistico es el menor "
                          "y el umbral SI depende del pool mu/sigma",
        "origen_de_mu_y_sigma": "fp_diag = PRIMER pase (first_pass_tests_2_and_3). "
                                "El pool del SEGUNDO pase no se persiste.",
        "umbrales_efectivos": {
            "C1_summit": C1_SUM, "C1_scene": C1_SCE,
            "C2_dnti_summit": C2_DNTI_SUM, "C2_dnti_scene": C2_DNTI_SCE,
            "C2_deti_summit": C2_DETI_SUM, "C2_deti_scene": C2_DETI_SCE,
        },
        "conectiva_efectiva_hoy": (
            "min  (ENABLE_TESTS_23_PROSE_BRANCH = "
            f"{prof.ENABLE_TESTS_23_PROSE_BRANCH})"),
    },
    "por_bucket": {},
}
for b in sorted(st):
    n = st[b]["n_records"]
    ncon = st[b]["con_diag_mu_sigma"]
    out["por_bucket"][b] = {
        "ventana_utc": ventana[b],
        "n_records": n,
        "conteos": dict(sorted(st[b].items())),
        "porcentaje_sobre_records_con_diag": {
            k: pct(v, ncon) for k, v in sorted(st[b].items())
            if k.startswith(("piso_", "sigma_", "algun_"))},
        "margen_estadistico_sobre_C1_mediana": {
            nombre: round(sorted(margen[(b, nombre)])[len(margen[(b, nombre)]) // 2], 1)
            for nombre in ["dnti_summit", "dnti_scene", "deti_summit", "deti_scene"]
            if margen[(b, nombre)]},
        "ejemplos_donde_sigma_gobierna": {
            nombre: ejemplos[(b, nombre)]
            for nombre in ["dnti_summit", "dnti_scene", "deti_summit", "deti_scene"]
            if ejemplos[(b, nombre)]},
    }

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for b, v in out["por_bucket"].items():
    print(f"\n== {b}  n={v['n_records']}  ventana={v['ventana_utc'][0][:10]}..{v['ventana_utc'][1][:10]}")
    print("   con diag mu/sigma:", v["conteos"].get("con_diag_mu_sigma"),
          " sin:", v["conteos"].get("sin_diag_mu_sigma"))
    for k, p in v["porcentaje_sobre_records_con_diag"].items():
        print(f"   {k:38s} {v['conteos'][k]:7d}  {p} %")
    print("   margen (mu+C2sigma)/C1 mediana:", v["margen_estadistico_sobre_C1_mediana"])
