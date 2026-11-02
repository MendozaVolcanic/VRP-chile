# -*- coding: utf-8 -*-
"""V2, 206: ¿cuántas noches con alerta de MIROVA en MODIS (lectura A: 1 MW o más... no: el recall cuenta TODA noche con
alerta, D-9 SN) junta el audit por semana, y cuántas semanas tarda la vía en llegar a MIN_N_RECALL=15?

Instrumento: el cargador del propio audit (aa.alertas_mirova + aa.aplicar_d9) sobre la referencia del worktree de B
(sha256 comprobado antes). Cuento noches (volcán, fecha) con alerta de MIROVA en el bucket MODIS de los 11 Tier A por
semana en las últimas 12 semanas. Denominador: noches con alerta, no pasadas (A90). Pregunta 1: si la tasa fuera 0 lo
veo (conteo 0); pregunta 2: control = VIIRS375 tiene que dar un conteo mayor que 0 y distinto de MODIS.
"""
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import scripts.auto_audit_weekly as aa  # noqa: E402

for f, esperado in (("registro_vrp_consolidado.csv", "ab1a208c89b32df2fd5622c102ac2a984fa8a0102cfe0fe9f65cb8ff54b7d88f"),
                    ("registro_vrp_ocr.csv", "d4ad8c44d5112ca44751552d4aee6e920c20ac5dc0d73f4fc5d9f6594785026e")):
    p = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / f
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"sha256 {f}: {h} {'OK' if h == esperado else 'DISTINTO del esperado ' + esperado[:12]}")

hoy = date(2026, 11, 2)
alertas = aa.alertas_mirova()
print("alertas cargadas:", len(alertas), "| MIN_N_RECALL =", aa.MIN_N_RECALL, "| MIN_N_RATIO =", aa.MIN_N_RATIO)
try:
    alertas = aa.aplicar_d9(alertas)
    print("tras D-9 SN:", len(alertas))
except Exception as e:  # noqa: BLE001
    print("aplicar_d9 falló (se sigue sin D-9):", type(e).__name__, e)

noches = defaultdict(set)   # (sensor_bucket) -> {(vol, fecha)}
for a in alertas:
    vol = a.get("volcano")
    if vol not in aa.VOLS:
        continue
    fecha = str(a.get("fecha_utc") or "")[:10]
    noches[a.get("sensor_bucket")].add((vol, fecha))

for s in ("MODIS", "VIIRS375", "VIIRS750"):
    print(f"\n== {s}: noches con alerta por semana (11 Tier A), 12 semanas hasta {hoy} ==")
    por_sem = Counter()
    for vol, fecha in noches.get(s, ()):
        try:
            d = date.fromisoformat(fecha)
        except ValueError:
            continue
        if 0 <= (hoy - d).days < 84:
            por_sem[(hoy - d).days // 7] += 1
    serie = [por_sem.get(k, 0) for k in range(12)]
    print("   semanas (0 = la última):", serie, "| mediana:", sorted(serie)[6], "| total 12 sem:", sum(serie))
    if s == "MODIS":
        med = sorted(serie)[6]
        ult4 = sum(serie[:4]) / 4
        print(f"   semanas para juntar {aa.MIN_N_RECALL} noches: a la mediana {med}/sem -> "
              f"{(aa.MIN_N_RECALL / med) if med else float('inf'):.1f}; a la tasa de las últimas 4 ({ult4:.1f}/sem) -> "
              f"{(aa.MIN_N_RECALL / ult4) if ult4 else float('inf'):.1f}")
        por_vol = Counter(vol for vol, fecha in noches.get(s, ()) if 0 <= (hoy - date.fromisoformat(fecha)).days < 84)
        print("   por volcán (12 sem):", dict(por_vol.most_common()))
