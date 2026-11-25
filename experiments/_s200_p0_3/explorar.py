"""Exploración (antes del pre-registro): qué hay en cada escena con el detector de producción de origin/main.
Salida: explorar_salida.txt (se corre con > explorar_salida.txt)."""
import numpy as np

import comun as C

C.utf8()
for esc in C.escenas():
    E = C.Escena(esc)
    mask, d = E.detectar(E.m13g, E.m15g)
    v = C.MV.vrp_mirova(E.m13g, mask)
    n_nan = int(np.isnan(E.m13g).sum())
    s1 = d.get("pasada1", {}); s2 = d.get("pasada2", {})
    print(f"{esc['clave']:42s} roi={E.roi:6s} cenit={E.geom['sensor_zenith']:5.1f} day={E.dayflag} sg={E.sg:6.1f} "
          f"sel={int(E.sel.sum())}/{E.sel.size} nan_celdas={n_nan} npix={int(mask.sum())} "
          f"VRP={v['VRP_MW'] if v['npix'] else 0:.3f} motivo={d.get('motivo')}")
    if s1:
        print(f"    p1 sd_nti={s1['sd_nti']:.5f} u_nti1={s1['u_nti1']:.4f} u_nti2={s1['u_nti2']:.4f} "
              f"u_eti1={s1.get('u_eti1', float('nan')):.4f} u_eti2={s1.get('u_eti2', float('nan')):.4f} | "
              f"p2 sd_nti={s2['sd_nti']:.5f} u_nti1={s2['u_nti1']:.4f} u_nti2={s2['u_nti2']:.4f} "
              f"u_eti1={s2.get('u_eti1', float('nan')):.4f} u_eti2={s2.get('u_eti2', float('nan')):.4f}")
    if mask.any():
        f, k = np.nonzero(mask)
        dist = np.hypot(f - E.pos[0], k - E.pos[1]) * 0.75
        bt = C.MV.radiancia_a_temperatura(E.m13g[mask], C.MV.LAMBDA_M13)
        print(f"    alertadas: dist_crater km {np.round(np.sort(dist), 1).tolist()[:20]} BT13 max {np.nanmax(bt):.1f} "
              f"zonas {np.unique(E.box[mask], return_counts=True)}")
