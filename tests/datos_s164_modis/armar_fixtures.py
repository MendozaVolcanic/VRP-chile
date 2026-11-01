# Script con que se armaron las fixtures de esta carpeta (S164), copiado tal cual se corrió.
# Uso: python armar_fixtures.py <repo> <dir con dp/delaunay_perturbado.py (blob f273a47a) y dp/grillas.json del tag s162-modd-tag>
# Los datos de origen (grillas y records del censo MOD-D) están fuera del repo, en D:/vrp-trabajo/temporales/s162_modd/censo/.
# Arma las fixtures de la vía MODIS desde el censo MOD-D (fuera del repo) y las salidas esperadas por código independiente.
import json, glob, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation
REPO = Path(sys.argv[1]); SP = Path(sys.argv[2]); OUT = REPO / "tests/datos_s164_modis"
sys.path.insert(0, str(SP / "dp")); sys.path.insert(0, str(REPO / "experiments/_s159/portes"))
import delaunay_perturbado as DP
import mirova_port as MP
G = json.load(open(SP / "dp/grillas.json", encoding="utf-8"))
IDS = [1611, 1638, 1545, 3392, 4943, 3933]   # 3933: PCC, alerta fuera de la envolvente (V164-01, verificador S164)
recs = {}
for f in glob.glob(r"D:/vrp-trabajo/temporales/s162_modd/censo/run_*/*/ab_*.jsonl"):
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and r.get("id") in IDS and r.get("estado") == "ok":
            recs[r["id"]] = (r, Path(f).parent / f"grilla_{r['id']:03d}.npz")
COEF = 1.89e7 * 1.0 / 1e6
def hueco(m, mask):
    enm = m.copy(); enm[mask] = np.nan; n = int(mask.sum()); k = 3 if n <= 4 else (5 if n <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan; return enm
salida = []
for i in IDS:
    r, gp = recs[i]
    z = np.load(gp); mir32, tir32 = z["mir"], z["tir"]
    np.savez_compressed(OUT / f"grilla_{i}.npz", mir=mir32, tir=tir32)
    mir, tir = mir32.astype(float), tir32.astype(float)
    g = G[r["vol"]]
    p = r["port"]["fisica"]
    mask = np.zeros(mir.shape, bool)
    for q in p["pixeles"]: mask[q[0], q[1]] = True
    vr = vr_nan = None
    n_fuera = 0
    if mask.any():
        enm = hueco(mir, mask)
        fondo = DP.rellenar(enm, "xy_fila_col")[0]
        vr = (float(np.nansum(mir[mask])) - float(np.nansum(fondo[mask]))) * COEF
        # MATLAB no extrapola: lo que queda fuera de la envolvente convexa de las celdas con dato es NaN, y el .m lo
        # descarta del fondo con sum(..., 'omitnan'). Envolvente con scipy (find_simplex), independiente de la vía.
        from scipy.spatial import Delaunay
        ff, cc = np.indices(enm.shape)
        ok = np.isfinite(enm)
        tri = Delaunay(np.column_stack([ff[ok], cc[ok]]).astype(float))
        fuera = (~ok) & (tri.find_simplex(np.column_stack([ff.ravel(), cc.ravel()]).astype(float)).reshape(enm.shape) < 0)
        fondo_nan = fondo.copy()
        fondo_nan[fuera] = np.nan
        n_fuera = int((fuera & mask).sum())
        vr_nan = (float(np.nansum(mir[mask])) - float(np.nansum(fondo_nan[mask]))) * COEF
    rp = MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], MP.SENSORES["MODIS"], semillas=0)
    salida.append({"id": i, "vol": r["vol"], "dt": r["dt"], "sensor": r["sensor"], "lab": r["lab"], "inner": r["inner"],
                   "dayflag": r["dayflag"], "sunglint": r["sunglint"], "grilla_censo": g,
                   "censo_npix": p["npix"], "censo_pixeles": [q[:3] for q in p["pixeles"]], "censo_vrp_port": p["vrp_mw"],
                   "censo_n_abs": p["n_abs"], "censo_n_p1": p["n_p1"], "censo_n_p2": p["n_p2"],
                   "vrp_regla_matlab": vr, "vrp_regla_matlab_sin_extrapolar": vr_nan,
                   "alertas_fuera_de_la_envolvente": n_fuera,
                   "port_sobre_npz_npix": rp["npix"], "port_sobre_npz_pixeles": [q[:3] for q in rp["pixeles"]],
                   "port_sobre_npz_vrp": rp["vrp_mw"]})
    print(i, r["vol"], r["dt"], p["npix"], rp["npix"], p["vrp_mw"], rp["vrp_mw"], vr, vr_nan, n_fuera)
json.dump({"origen": "censo MOD-D (runs 40336655402, 40344051900, 40349358358), D:/vrp-trabajo/temporales/s162_modd/censo",
           "regla": "delaunay_perturbado.py blob f273a47a (tag s162-modd-tag), ejes xy_fila_col; hueco y COEF de m_con_regla_matlab.py",
           "pasadas": salida}, open(OUT / "esperado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
