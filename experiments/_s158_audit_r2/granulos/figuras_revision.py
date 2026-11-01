"""Figuras para la revisión visual de Nicolás: M13 remuestreado a la grilla de MIROVA (lineal, sin desplazar) con los
píxeles que alerta el oráculo (círculos rojos), la caja de cumbre de 7 x 7 y el anillo de 21 x 21. Sin red: usa los
recortes del run 39641637298. Norte arriba (fila 0 = norte), celdas de 750 m, centro de la grilla = centro de MIROVA."""
import glob, json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "oraculo")); sys.path.insert(0, str(AQUI))
import mirova_v750_r2 as ORA
from probe_granulos import caja_mirova
run = AQUI / "run_39641637298"
res = json.loads(Path(glob.glob(str(run / "**" / "resultados.json"), recursive=True)[0]).read_text())
for r in res:
    if r.get("estado") != "ok":
        continue
    clave = f"{r['volcan']}_{r['hora_utc'].replace(' ', '_').replace(':', '')}"
    z = np.load(glob.glob(str(run / "**" / f"recorte_{clave}.npz"), recursive=True)[0])
    m13, m15 = z["grilla_linear_M13"], z["grilla_linear_M15"]
    mk, _ = ORA.detectar(m13, m15, caja_mirova(), r["dayflag"], r["sunglint"])
    v = ORA.vrp(m13, mk)["VRP_MW"] if mk.any() else None
    fig, ax = plt.subplots(figsize=(6, 6))
    bt = ORA.radiancia_a_temperatura(m13, ORA.LAMBDA_M13)
    im = ax.imshow(bt, cmap="inferno", extent=(-25.125, 25.125, -25.125, 25.125))
    plt.colorbar(im, ax=ax, label="BT M13 (K)", shrink=0.8)
    for lado, c in ((7 * 0.75, "cyan"), (21 * 0.75, "white")):
        ax.add_patch(plt.Rectangle((-lado / 2, -lado / 2), lado, lado, fill=False, ec=c, lw=1))
    rr, cc = np.nonzero(mk)
    ax.scatter((cc - 33) * 0.75, (33 - rr) * 0.75, s=80, facecolors="none", edgecolors="red", lw=1.5)
    mir = r["mirova"][0] if r["mirova"] else {}
    ax.set_title(f"{r['volcan']} {r['hora_utc']} UTC, VIIRS 750\n"
                 f"oráculo {mk.sum()} px, {v and round(v, 2)} MW | MIROVA {mir.get('VRP_MW')} MW a {mir.get('Distancia_km')} km"
                 f" | producción {r['produccion'].get('pc_vrp_mw')} MW", fontsize=8)
    ax.set_xlabel("km al este del centro de MIROVA"); ax.set_ylabel("km al norte")
    fig.tight_layout(); fig.savefig(AQUI / "figuras" / f"{clave}.png", dpi=110); plt.close(fig)
    print("ok", clave)
