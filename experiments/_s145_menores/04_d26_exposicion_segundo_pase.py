"""S145 D26 - Exposicion real del segundo pase: cuantos records reciben pixeles
recapturados por el paso cuyo pool mu/sigma denuncia D26.

POR QUE: si el segundo pase no recaptura nada, el pool sucio no puede cambiar
nada y D26 es nula por falta de sustrato, sin importar la conectiva (A-S130:
medir el sustrato antes de discutir el efecto). Si recaptura, el pool si tiene
por donde morder y el veredicto "efecto nulo" necesita apoyarse en la conectiva,
que es la premisa bajo sospecha.

Salida: 04_d26_exposicion_segundo_pase.json
"""
import json
import glob
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "04_d26_exposicion_segundo_pase.json"


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
por_volcan = defaultdict(lambda: defaultdict(int))

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
        rec = r.get("diag_n_second_pass_recapture")
        fp = r.get("diag_n_first_pass_pixels")
        if rec is None:
            st[b]["sin_diag_recapture"] += 1
            continue
        st[b]["con_diag_recapture"] += 1
        if rec > 0:
            st[b]["records_con_recaptura"] += 1
            st[b]["pixeles_recapturados"] += int(rec)
            st[b]["max_recaptura_en_un_record"] = max(
                st[b]["max_recaptura_en_un_record"], int(rec))
            por_volcan[vol][b] += 1
            if fp is not None and fp > 0 and rec >= fp:
                st[b]["recaptura_mayor_igual_que_primer_pase"] += 1


def pct(a, b):
    return round(100.0 * a / b, 3) if b else None


out = {
    "definiciones": {
        "records_con_recaptura": "diag_n_second_pass_recapture > 0 = el segundo "
                                 "pase agrego pixeles a la mascara publicada",
        "nota": "el segundo pase operacional corre sobre hot_mask_2d = fp_hot y su "
                "salida REEMPLAZA la mascara (process_modis.py:954 y equivalentes)",
    },
    "por_bucket": {},
    "top_volcanes_con_recaptura": {},
}
for b in sorted(st):
    n = st[b]["con_diag_recapture"]
    out["por_bucket"][b] = {
        "ventana_utc": ventana[b],
        "conteos": dict(sorted(st[b].items())),
        "pct_records_con_recaptura": pct(st[b]["records_con_recaptura"], n),
    }
tot = defaultdict(int)
for vol, d2 in por_volcan.items():
    tot[vol] = sum(d2.values())
out["top_volcanes_con_recaptura"] = {
    v: dict(por_volcan[v]) for v in sorted(tot, key=tot.get, reverse=True)[:12]}

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for b, v in out["por_bucket"].items():
    c = v["conteos"]
    print(f"\n== {b}  n_records={c['n_records']}  con_diag={c.get('con_diag_recapture')}"
          f"  ventana={v['ventana_utc'][0][:10]}..{v['ventana_utc'][1][:10]}")
    print(f"   records con recaptura : {c.get('records_con_recaptura',0):6d}  "
          f"{v['pct_records_con_recaptura']} %")
    print(f"   pixeles recapturados  : {c.get('pixeles_recapturados',0)}   "
          f"max en un record: {c.get('max_recaptura_en_un_record',0)}")
    print(f"   recaptura >= 1er pase : {c.get('recaptura_mayor_igual_que_primer_pase',0)}")
print("\ntop volcanes:", json.dumps(out["top_volcanes_con_recaptura"], ensure_ascii=False))
