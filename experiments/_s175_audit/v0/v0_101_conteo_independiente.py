"""V0-101: conteo independiente de cumulos de cumbre de VIIRS 750 con pc.vrp_mw == 0, leyendo directo
data/mirova_equivalent/*.json de la base 752d348bc (git show), sin pasar por banco_paridad.
P1: si el recorte a cero no existiera, el conteo seria 0; aqui se ve. P2: el control es el total de cumbres con
primary_cluster no nulo (si fuera 0, el instrumento estaria muerto) y el cruce de nocturnidad por solar_zenith_deg.
Denominador: pasadas VIIRS 750 con primary_cluster y distance_class == 'summit'. Ventanas = las del auditor.
La nocturnidad aqui es solar_zenith_deg >= 90 (otro camino que el del auditor, que usa la del banco)."""
import json
import subprocess
from datetime import datetime

REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
B = "752d348bc67190e53b610989877e2405d238a1bc"
VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Lastarria", "PlanchonPeteroa", "Copahue",
        "Tupungatito", "PuyehueCordonCaulle", "Chaiten"]
VENT = [("2026-09-18", "2026-10-21"), ("2026-10-22", "2026-11-02"), ("2026-11-03", "2026-11-07")]


def leer(vol):
    out = subprocess.run(["git", "-C", REPO, "show", f"{B}:data/mirova_equivalent/{vol}.json"], capture_output=True)
    if out.returncode:
        return None
    return json.loads(out.stdout.decode("utf-8"))


tot = {v: [0, 0, 0] for v in VENT}  # cumbres, con cero, publicables(>0)
ejemplos = []
for vol in VOLS:
    d = leer(vol)
    if d is None:
        print("SIN DATO", vol)
        continue
    for r in d["records"]:
        if "750" not in str(r.get("sensor")):
            continue
        dt = str(r.get("datetime_utc"))[:10]
        pc = r.get("primary_cluster")
        if not pc or r.get("distance_class") != "summit":
            continue
        sz = r.get("solar_zenith_deg")
        if sz is None or sz < 90:
            continue
        for v in VENT:
            if v[0] <= dt <= v[1]:
                tot[v][0] += 1
                if (pc.get("vrp_mw") or 0) == 0:
                    tot[v][1] += 1
                    ejemplos.append((vol, r["sensor"], r["datetime_utc"], r.get("via_codigo_mirova")))
for v, (n, z, _) in tot.items():
    print(v, "cumbres nocturnas V750", n, "con 0,0 MW", z, f"({100 * z / n:.1f} %)" if n else "SIN DATO")
print("ultimo dato de la base:", max(e[2] for e in ejemplos) if ejemplos else "SIN DATO")
for e in sorted(ejemplos, key=lambda x: x[2])[:50]:
    print(e)
