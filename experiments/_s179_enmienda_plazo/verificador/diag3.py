"""Verificador: pasadas MODIS nocturnas con alerta (lectura A) posteriores al encendido, con la referencia de origin/main,
con la misma construccion que vigilancia_sombra.pasadas_de_alerta (sin records: solo la referencia)."""
import collections, io, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import clase_mirova as cm
import auto_audit_weekly as aa
from referencia_mirova_unificada import cargar_referencia_unificada
V = sys.argv[1]
filas = cargar_referencia_unificada(V + "/ref_main/cons.csv", V + "/ref_main/ocr.csv")
print("ultima fila ref main:", max(f["fecha_utc"] for f in filas))
coords = aa._coords_por_volcan()
ENC = "2026-11-02 20:11:43"
pp = collections.defaultdict(list)
for f in filas:
    if f.get("tipo") in cm.TIPOS_ALERTA and "2026-10-19" <= f["fecha_utc"][:10] <= "2026-11-11":
        pp[cm.clave_pasada(f)].append(f)
for sensor in ("MODIS", "VIIRS375", "VIIRS750"):
    pros, retro = [], []
    for (vol, b, minuto), fs in sorted(pp.items()):
        if b != sensor: continue
        dt = datetime.fromisoformat(fs[0]["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
        if aa.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt): continue
        prot = any(cm.alerta_protegida(f) for f in fs)
        vr = max((f["vrp_mw"] for f in fs if f.get("vrp_mw") is not None), default=None)
        src = "+".join(sorted({f.get("source") for f in fs}))
        (pros if dt.strftime("%Y-%m-%d %H:%M:%S") >= ENC else retro).append((minuto, vol, prot, vr, src))
    print(f"\n== {sensor}: pasadas de alerta nocturnas en ventana: {len(pros)+len(retro)}; antes del encendido MODIS {len(retro)}; despues {len(pros)}")
    print("   despues, protegidas por volcan:", dict(collections.Counter(v for _, v, p, _, _ in pros if p)), "| no protegidas:", dict(collections.Counter(v for _, v, p, _, _ in pros if not p)))
    if sensor == "MODIS":
        for x in pros: print("   ", x)
