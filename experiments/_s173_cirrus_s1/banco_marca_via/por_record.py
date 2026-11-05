"""Salida por record del banco (vol, sensor, dt, disp, pub) en cada carpeta de datos que el banco lee."""
import json, sys, os
raiz, salida = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(raiz, "scripts"))
import banco_paridad as bp
print("CAMPOS_JS:", bp.CAMPOS_JS, file=sys.stderr)
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
out = {}
for sub in ["mirova_equivalent", "guardia_k_modis", "experimental_v2"]:
    d = os.path.join(raiz, "data", sub)
    try:
        recs = bp.cargar_nuestros(coords, inner, ("2000-01-01", "2100-12-31"), data=d)
    except FileNotFoundError as e:
        print(sub, "FALTA", e, file=sys.stderr); continue
    out[sub] = [[r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["disp"], r["pub"]] for r in recs]
    # cuantos records crudos de la via en esa carpeta
    nv = 0
    for v in bp.VOLS:
        with open(os.path.join(d, v + ".json"), encoding="utf-8") as fh:
            nv += sum(1 for r in json.load(fh)["records"] if r.get("via_codigo_mirova") is True)
    print(sub, "records en banco:", len(recs), "publicados:", sum(r["pub"] for r in recs), "via crudos:", nv, file=sys.stderr)
json.dump(out, open(salida, "w"), indent=0)
