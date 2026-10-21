"""O1 (S159): arma el paquete O2 para MATLAB Online: Etna + 40 matrices chilenas guardadas + 150 variantes + las 120
primeras sintéticas (311 escenas). Copia exacta de entradas.mat (mismas matrices, mismo orden relativo)."""
import json
from pathlib import Path
import numpy as np, scipy.io as sio
AQUI = Path(__file__).resolve().parent
E = sio.loadmat(AQUI / "entradas.mat"); etq = json.loads((AQUI / "entradas_etiquetas.json").read_text(encoding="utf-8"))
idx = [k for k, e in enumerate(etq) if e["familia"] != "sintetica" or int(e["id"][5:]) < 120]
sio.savemat(AQUI / "o2_paquete" / "entradas_o2.mat", {
    "M13": E["M13"][:, :, idx], "M15": E["M15"][:, :, idx], "BOX": E["BOX"][:, :, idx],
    "DAY": E["DAY"].ravel()[idx], "SG": E["SG"].ravel()[idx], "IDX_O1": np.array(idx) + 1}, do_compression=True)
(AQUI / "o2_paquete" / "entradas_o2_etiquetas.json").write_text(
    json.dumps([dict(etq[k], idx_o1=k) for k in idx], ensure_ascii=False, indent=0), encoding="utf-8")
print("escenas O2:", len(idx))
