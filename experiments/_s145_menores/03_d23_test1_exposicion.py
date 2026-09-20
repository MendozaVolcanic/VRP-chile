"""S145 D23 - Cuantos records tienen pixeles del Test 1 (NTI > K1) y cuantos de
esos pixeles NO pueden estar en la mascara publicada.

POR QUE: D23 dice que el Test 1 se calcula y se tira, porque `hot_mask_2d = fp_hot`
pisa la salida de combine_hot_paths. El catalogo da la frecuencia de K1 por sensor
(MODIS 0,09 %, VIIRS375 1,34 %, VIIRS750 0,12 %) pero declara que la magnitud del
efecto es SOSPECHA porque no se reproceso sobre granules reales. Aca se re-deriva
la frecuencia sobre el corpus de hoy y se acota lo que SI se puede acotar desde
disco: los records donde por CONTEO es imposible que los pixeles K1 esten dentro
del primer pase.

Acotacion honesta: los records guardan CONTEOS, no mascaras. Con
n_nti_path <= n_first_pass_pixels no se puede decidir si los pixeles K1 estan o
no dentro del primer pase. Con n_nti_path > n_first_pass_pixels sobran al menos
(n_nti_path - n_first_pass_pixels) pixeles K1 fuera. Ese es un piso, no el total.

Salida: 03_d23_test1_exposicion.json
"""
import json
import glob
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "03_d23_test1_exposicion.json"


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
casos = defaultdict(list)
k1_perdidos = defaultdict(int)

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
        k1 = r.get("diag_n_nti_path")
        fp = r.get("diag_n_first_pass_pixels")
        if k1 is None:
            st[b]["sin_diag_n_nti_path"] += 1
            continue
        st[b]["con_diag_n_nti_path"] += 1
        if k1 > 0:
            st[b]["records_con_k1"] += 1
            st[b]["pixeles_k1_totales"] += int(k1)
            st[b]["max_pixeles_k1_en_un_record"] = max(
                st[b]["max_pixeles_k1_en_un_record"], int(k1))
            if k1 >= 9:
                st[b]["records_con_k1_mayor_igual_9"] += 1
            if fp is not None and k1 > fp:
                st[b]["records_con_k1_fuera_del_primer_pase_seguro"] += 1
                k1_perdidos[b] += int(k1) - int(fp)
                if fp == 0:
                    st[b]["records_con_k1_y_primer_pase_vacio"] += 1
                if len(casos[b]) < 8:
                    casos[b].append({
                        "volcan": vol, "datetime_utc": dt,
                        "sensor": r.get("sensor"),
                        "n_nti_path": k1, "n_first_pass_pixels": fp,
                        "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                        "vrp_mw": r.get("vrp_mw"),
                        "t_max_k": r.get("t_max_k"), "t_bg_k": r.get("t_bg_k"),
                        "nti_max": r.get("diag_nti_max"),
                    })


def pct(a, b):
    return round(100.0 * a / b, 3) if b else None


out = {
    "definiciones": {
        "records_con_k1": "diag_n_nti_path > 0 = hubo pixeles con NTI > K1 y "
                          "BT > t_bg + 3 K dentro del ROI",
        "k1_fuera_del_primer_pase_seguro": "n_nti_path > n_first_pass_pixels: por "
                                           "conteo sobran pixeles K1 que el primer "
                                           "pase no pudo contener (PISO, no total)",
        "limite": "los records guardan conteos, no mascaras: el solape real entre "
                  "la mascara K1 y fp_hot no es reconstruible desde disco",
    },
    "por_bucket": {},
}
for b in sorted(st):
    n = st[b]["con_diag_n_nti_path"]
    out["por_bucket"][b] = {
        "ventana_utc": ventana[b],
        "conteos": dict(sorted(st[b].items())),
        "pct_records_con_k1_sobre_con_diag": pct(st[b]["records_con_k1"], n),
        "pct_k1_fuera_seguro_sobre_con_diag": pct(
            st[b]["records_con_k1_fuera_del_primer_pase_seguro"], n),
        "piso_pixeles_k1_fuera_del_primer_pase": k1_perdidos[b],
        "casos": casos[b],
    }

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for b, v in out["por_bucket"].items():
    c = v["conteos"]
    print(f"\n== {b}  n_records={c['n_records']}  con_diag={c.get('con_diag_n_nti_path')}"
          f"  ventana={v['ventana_utc'][0][:10]}..{v['ventana_utc'][1][:10]}")
    print(f"   records con K1            : {c.get('records_con_k1',0):6d}  "
          f"{v['pct_records_con_k1_sobre_con_diag']} %")
    print(f"   pixeles K1 totales        : {c.get('pixeles_k1_totales',0)}")
    print(f"   K1 fuera del 1er pase (piso): "
          f"{c.get('records_con_k1_fuera_del_primer_pase_seguro',0):6d}  "
          f"{v['pct_k1_fuera_seguro_sobre_con_diag']} %   "
          f"pixeles={v['piso_pixeles_k1_fuera_del_primer_pase']}")
    print(f"   de esos, 1er pase VACIO   : {c.get('records_con_k1_y_primer_pase_vacio',0)}")
