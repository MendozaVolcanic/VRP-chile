# S182: por qué la caja del cráter (B2) alerta MÁS píxeles que la sensible (B4) en 5 pasadas con alerta de MIROVA.
# Imprime, por caja, los umbrales y estadísticos de cada pase del port y qué píxeles alerta cada una. Sin red.
import importlib.util, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
port_spec = importlib.util.spec_from_file_location("port", r"D:\vrp-trabajo\temporales\s182_pcc\_port_main.py")
port = importlib.util.module_from_spec(port_spec); port_spec.loader.exec_module(port)
import glob
BASE = r"D:\vrp-trabajo\temporales\v750b_r4_20261103"
filas = {f["hora"]: f for f in json.load(open(r"D:\vrp-trabajo\temporales\s182_pcc\11_cajas_pcc_filas.json", encoding="utf-8"))}
res = {}
for f in glob.glob(BASE + r"\art_*\*\resultados_*.json"):
    for r in json.load(open(f, encoding="utf-8")):
        res.setdefault(r["id"], r)
for hora in ("2026-09-18 05:24", "2026-10-28 06:18", "2026-07-03 05:48"):
    i = filas[hora]["id"]
    npz = glob.glob(BASE + rf"\art_*\*\grilla_{i:05d}.npz")[0]
    z = np.load(npz); m13, m15 = z["m13"].astype(float), z["m15"].astype(float)
    print(f"\n== {hora} id {i}  MIROVA {filas[hora]['mirova_vrp']} MW")
    for t in ("crater", "sens"):
        box = port.caja_roi(t, n=67, celda_crater=(23, 30))
        mask, d = port.detectar_mirova(m13, m15, box, res[i]["dayflag"], res[i]["sunglint"], devolver_diag=True)
        print(f"  [{t}] px {[(int(a), int(b)) for a, b in zip(*np.nonzero(mask))]}  n_abs {d.get('n_abs')} n_p1 {d.get('n_p1')} n_p2 {d.get('n_p2')}")
        for p in (1, 2):
            dp = d.get(f"pasada{p}")
            if dp:
                print("     pase", p, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in dp.items() if not hasattr(v, 'shape')})
