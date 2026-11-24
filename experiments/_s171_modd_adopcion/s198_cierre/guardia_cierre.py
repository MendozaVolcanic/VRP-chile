"""S198: informe de cierre de la guardia K de MODIS.

Reproduce scripts/vigilancia_guardia_modis.py (main, sin escribir en data/) con la referencia fresca de Mirova-v1 y
lista una por una las protegidas posteriores al encendido que cuentan para el plazo (§4.6), con su fuente en MIROVA
(tabla consolidada / sólo OCR), qué hizo producción (la vía) y qué hizo la guardia (K).

Uso (desde la raíz de un checkout de origin/main):
  python experiments/_s171_modd_adopcion/s198_cierre/guardia_cierre.py --cons <consolidado.csv> --ocr <ocr.csv> --out <dir>
La referencia se baja de Mirova-v1 como lo hace .github/workflows/vigilancia-guardia-modis.yml (tabla consolidada + OCR).
La fuente y la razón vía/MIROVA salen de fuente_y_magnitud.py, que lee el CSV que escribe este script.
"""
import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import vigilancia_guardia_modis as vgm  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cons", required=True)
ap.add_argument("--ocr", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
vgm.aa.CONS = a.cons
vgm.aa.OCR = a.ocr

capt = {}
_orig = vgm.pasadas_modis


def _espia(*args, **kw):
    r = _orig(*args, **kw)
    capt["pasadas"] = r
    return r


vgm.pasadas_modis = _espia
hoy = datetime.now(timezone.utc).date().isoformat()
out = vgm.evaluar(hoy)
pasadas = capt["pasadas"]
enc = out["encendido_modis_utc"]

# fuente en MIROVA: la pasada está en la tabla consolidada con >= 1 MW, o sólo en el OCR
filas = vgm.cargar_referencia_unificada(vgm.aa.CONS, vgm.aa.OCR) if hasattr(vgm, "cargar_referencia_unificada") else None
if filas is None:
    from referencia_mirova_unificada import cargar_referencia_unificada
    filas = cargar_referencia_unificada(vgm.aa.CONS, vgm.aa.OCR)

vistas = sorted((p for p in pasadas if p["instante_utc"] >= enc and p["protegida"] and p["guardia_pub"] is not None
                 and p.get("prod_via") is not False), key=lambda p: (p["instante_utc"], p["volcano"]))
todas_pros = sorted((p for p in pasadas if p["instante_utc"] >= enc and p["protegida"]),
                    key=lambda p: (p["instante_utc"], p["volcano"]))

os.makedirs(a.out, exist_ok=True)
claves = ["orden", "volcano", "sensor", "fecha_utc", "vrp_mirova_mw", "prod_pub", "prod_via", "guardia_pub",
          "cuenta_plazo"]
orden = {(p["volcano"], p["instante_utc"]): i + 1 for i, p in enumerate(vistas)}
with open(os.path.join(a.out, "protegidas_posteriores_encendido.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(claves + ["claves_extra"])
    for p in todas_pros:
        o = orden.get((p["volcano"], p["instante_utc"]))
        extra = {k: v for k, v in p.items() if k not in claves and k not in ("instante_utc",)}
        w.writerow([o, p["volcano"], p.get("sensor"), p["fecha_utc"], p["vrp_mirova_mw"], p["prod_pub"],
                    p.get("prod_via"), p["guardia_pub"], o is not None, json.dumps(extra, ensure_ascii=False,
                                                                                  default=str)])
with open(os.path.join(a.out, "guardia_modis_fresca.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False, default=str)

print(f"generado {out['generated_utc']} · veredicto {out['veredicto']} · fase {out['fase']} · encendido {enc}")
print(f"avisos: {out['avisos']}")
print(f"duracion: {out['duracion']}")
print(f"reversion {len(out['reversion'])} · fuera_de_plazo {len(out['fuera_de_plazo'])} · "
      f"calladas_por_k {len(out['protegidas_calladas_por_k_de_produccion'])} · "
      f"sin_record_prod {len(out['protegidas_sin_record_produccion'])} · "
      f"sin_publicar_prod {len(out['protegidas_sin_publicar_produccion'])}")
print(f"muy_bajo {out['muy_bajo']['k']}/{out['muy_bajo']['n']} (cota {out['muy_bajo']['cota']}) · "
      f"sobrepublicacion {out['sobrepublicacion']['k']}/{out['sobrepublicacion']['n']} "
      f"(cota {out['sobrepublicacion']['cota']}) · nulo {out['nulo']['distintas']}/{out['nulo']['pares']}")
print(f"protegidas posteriores al encendido: {len(todas_pros)}; cuentan para el plazo: {len(vistas)}")
pv = sum(1 for p in todas_pros if p["prod_pub"] is True)
gv = sum(1 for p in todas_pros if p["guardia_pub"] is True)
print(f"de ellas, produccion (la via) publica {pv}; la guardia (K) publica {gv}")
por_vol = {}
for p in todas_pros:
    por_vol.setdefault(p["volcano"], [0, 0, 0])
    por_vol[p["volcano"]][0] += 1
    por_vol[p["volcano"]][1] += p["prod_pub"] is True
    por_vol[p["volcano"]][2] += p["guardia_pub"] is True
for v, (n, pr, g) in sorted(por_vol.items(), key=lambda x: -x[1][0]):
    print(f"  {v}: {n} protegidas, via publica {pr}, K publica {g}")
for p in todas_pros:
    print(f"  {orden.get((p['volcano'], p['instante_utc']), '-'):>3} {p['volcano']:<20} {p['fecha_utc']} "
          f"{p['vrp_mirova_mw']:>6} MW  via={p['prod_pub']} K={p['guardia_pub']} prod_via={p.get('prod_via')}")
