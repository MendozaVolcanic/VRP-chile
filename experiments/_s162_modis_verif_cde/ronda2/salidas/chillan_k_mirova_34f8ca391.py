# -*- coding: utf-8 -*-
"""S162 MOD-D (verificador VCD-11): razon K/MIROVA de Chillan en la poblacion congelada de MOD-B (la que usa MOD-D), en
las alertas MODIS que K publica, con su cenit. Fuente: poblacion.json (pc_vrp_guardada de data/ en main 80b819828,
vrp_mirova = mayor alerta de MIROVA a 120 s, referencia del MANIFIESTO). Control: el total de alertas de Chillan tiene
que dar 10 (pre-registro de MxD03, §5).
Uso: python -I chillan_k_mirova.py
"""
import json, statistics as st
from pathlib import Path
pob = json.load(open(Path(__file__).with_name("poblacion.json"), encoding="utf-8"))
al = [f for g in pob["granulos"] for f in g["records"] if f["vol"] == "NevadosDeChillan" and f["lab"] in ("protegida", "bajo1")]
print("alertas MODIS de Chillan en la poblacion:", len(al), "(control: 10)")
pub = [f for f in al if f["pub_guardada"] and f["pc_vrp_guardada"]]
for f in sorted(al, key=lambda x: x["dt"]):
    r = (f["pc_vrp_guardada"] / f["vrp_mirova"]) if f["pub_guardada"] and f["pc_vrp_guardada"] else None
    print(f"  {f['dt']} {f['lab']:<9} cenit {f['z']:5.1f} MIROVA {f['vrp_mirova']:6.2f} K {f['pc_vrp_guardada']} pub {f['pub_guardada']} razon {r if r is None else round(r, 3)}")
rs = [f["pc_vrp_guardada"] / f["vrp_mirova"] for f in pub]
print(f"K/MIROVA mediana en las que K publica: {st.median(rs):.3f} (n {len(rs)}); cenit <= 50: "
      f"{st.median([f['pc_vrp_guardada'] / f['vrp_mirova'] for f in pub if f['z'] <= 50]):.3f}")
