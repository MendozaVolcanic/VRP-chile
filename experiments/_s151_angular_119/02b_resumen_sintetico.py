"""Tarea 1.19 (ii): resumen del sintetico. beta de ln(VRP_nuestro/VRP_verdadero) sobre -ln A_nativo (fisica: 1),
escalones entre 35,9/36,8 y 52,2/53,1 grados (fisica: +0,405 y +0,693 menos el crecimiento suave entre los dos
puntos), detecciones perdidas, y error relativo contra la prediccion pre-registrada."""
import json, pathlib, numpy as np
d = json.loads(pathlib.Path(__file__).with_name('02_salida.json').read_text())
out = {}
for v in (1.0, 3.0):
    s = [r for r in d if r['vrp_true'] == v]
    det = [r for r in s if r['f5'] is not None]
    y = np.log([r['f5'] / v for r in det]); x = -np.log([r['area_rel'] for r in det])
    beta = float(np.polyfit(x, y, 1)[0])
    err = [r['f5'] / r['pred_nuestro'] - 1 for r in det]
    med = lambda z: float(np.median([r['f5'] for r in det if r['cenit'] == z]))
    pr = lambda z: next(r['pred_nuestro'] for r in s if r['cenit'] == z)
    o = dict(n=len(s), detectadas=len(det), beta=round(beta, 4),
             err_rel_max=round(float(np.max(np.abs(err))), 4),
             escalon_36=dict(medido=round(np.log(med(36.8) / med(35.9)), 3), predicho=round(np.log(pr(36.8) / pr(35.9)), 3)),
             escalon_53=dict(medido=round(np.log(med(53.1) / med(52.2)), 3), predicho=round(np.log(pr(53.1) / pr(52.2)), 3)),
             nadir_2=round(med(2.0) / v, 3), borde_67=round(med(67.0) / v, 3))
    out[str(v)] = o; print(v, o)
pathlib.Path(__file__).with_name('02b_salida.json').write_text(json.dumps(out, indent=1))
