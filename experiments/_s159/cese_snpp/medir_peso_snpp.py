"""S159 cese SNPP: cuanto pesa Suomi NPP en lo que el tablero publica y en lo que MIROVA alerta.

Uso: python -I medir_peso_snpp.py <arbol_origin_main> [inicio] [fin]
  arbol = git archive origin/main de pipeline, scripts, frontend, data/mirova_reference y los 11 JSON Tier A.
Predicado de publicacion: el del tablero, ejecutado con node (banco_paridad.cargar_nuestros, A97).
Etiquetas MIROVA: banco_paridad.etiquetar sobre la referencia snapshot del repo (sin red).
Ventana por defecto: 2026-09-18 (frontera de observacion del detector K) a 2026-10-20, sólo pasadas nocturnas.

Pregunta 1: si SNPP no pesara nada, los conteos de abajo darian 0; si el reparto por plataforma estuviera roto
(todo cayera en una), la suma por plataforma no cuadraria con el total o una plataforma saldria vacia.
Pregunta 2: control positivo: NOAA-20 y NOAA-21 deben salir con conteos > 0; si la carga muriera, n_records = 0
y el script lo dice como SIN DATO.
Unidad: noche = (volcan, sensor, fecha UTC), la del banco.
"""
import sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
INI = sys.argv[2] if len(sys.argv) > 2 else "2026-09-18"
FIN = sys.argv[3] if len(sys.argv) > 3 else "2026-10-20"
sys.path.insert(0, str(ARBOL)); sys.path.insert(0, str(ARBOL / "scripts"))
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402
import clase_mirova as cm  # noqa: E402


def plat(sensor):
    s = sensor or ""
    return "SNPP" if "SNPP" in s else "NOAA21" if "NOAA21" in s else "NOAA20" if "NOAA20" in s else "MODIS"


coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
ventana = (INI, FIN)
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
print("ultima fecha en la referencia snapshot:", max((f.get("fecha_utc") or f.get("Fecha_Satelite_UTC") or "")
                                                   for f in filas if isinstance(f, dict))[:16])
por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
recs = bp.cargar_nuestros(coords, inner, ventana)
bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
print(f"ventana {INI}..{FIN} | records nocturnos Tier A: {len(recs)}")
if not recs:
    print("SIN DATO"); sys.exit(0)

for b in ("VIIRS375", "VIIRS750"):
    R = [r for r in recs if r["b"] == b]
    pc = collections.Counter(plat(r["sensor"]) for r in R)
    pub = collections.Counter(plat(r["sensor"]) for r in R if r.get("pub"))
    pos = collections.Counter(plat(r["sensor"]) for r in R if r["lab"] == "pos")
    neg = collections.Counter(plat(r["sensor"]) for r in R if r["lab"] == "neg_limpio")
    negpub = collections.Counter(plat(r["sensor"]) for r in R if r["lab"] == "neg_limpio" and r.get("pub"))
    print(f"\n=== {b}: {len(R)} records nocturnos ===")
    print("  records por plataforma:", dict(pc))
    print("  records publicados por plataforma:", dict(pub))
    print("  pasadas pareadas a ALERTA de MIROVA (lab=pos) por plataforma:", dict(pos))
    print("  negativos limpios por plataforma:", dict(neg), "| de esos publicados:", dict(negpub))
    noches = collections.defaultdict(list)
    for r in R:
        noches[(r["vol"], r["b"], r["noche"])].append(r)
    solo_snpp = [k for k, v in noches.items() if all(plat(x["sensor"]) == "SNPP" for x in v)]
    pub_n = {k: [x for x in v if x.get("pub")] for k, v in noches.items()}
    pub_solo_snpp = [k for k, v in pub_n.items() if v and all(plat(x["sensor"]) == "SNPP" for x in v)]
    al = [k for k in noches if noche_sensor.get(k, {}).get("alerta")]
    al_pub = [k for k in al if pub_n[k]]
    al_pub_solo_snpp = [k for k in al_pub if all(plat(x["sensor"]) == "SNPP" for x in pub_n[k])]
    # de esas, cuantas tienen la alerta de MIROVA pareada SOLO a pasadas SNPP (MIROVA la perderia igual)
    al_mir_snpp = [k for k in al_pub_solo_snpp
                   if all(plat(x["sensor"]) == "SNPP" for x in noches[k] if x["lab"] == "pos")
                   and any(x["lab"] == "pos" for x in noches[k])]
    print(f"  noches con algun record: {len(noches)} | solo con records SNPP: {len(solo_snpp)}")
    print(f"  noches publicadas: {sum(1 for v in pub_n.values() if v)} | publicadas SOLO por SNPP: {len(pub_solo_snpp)}")
    print(f"  noches con ALERTA de MIROVA en este sensor: {len(al)} | publicadas: {len(al_pub)} | "
          f"publicadas SOLO por SNPP: {len(al_pub_solo_snpp)} (de esas, la alerta MIROVA pareada sólo a SNPP: {len(al_mir_snpp)})")
    for k in sorted(al_pub_solo_snpp):
        print("    ", k, [(x["dt"].strftime("%H:%M"), plat(x["sensor"]), x["lab"]) for x in noches[k]])
