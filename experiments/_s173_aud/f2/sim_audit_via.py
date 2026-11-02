# -*- coding: utf-8 -*-
"""S173 F2 (e): ¿qué dice el audit semanal (detector VIA_MODIS del PR A) la primera semana después del merge de B?

Corre scripts/auto_audit_weekly.py REAL (el del árbol A+B+#932, worktree s173-f2-combo) dos veces sobre los datos de main
a3c5a9b49 (data/mirova_equivalent al 2026-11-02 02:44 UTC):
  control: los datos tal cual (sin records de la vía);
  via_D:   los records MODIS con datetime_utc >= D marcados `via_codigo_mirova: true` y nada más. Simula un encendido cuyo
           primer record de la vía es de la fecha D, con la vía publicando EXACTAMENTE lo mismo que K (aísla la
           contabilidad del audit de cualquier diferencia de detección).
  mezcla:  como via_D, pero la fecha D-1 sólo con MODIS_AQUA marcado (la frontera cae en una noche con un pase de K y
           otro de la vía, como pasa cuando el upgrade NRT->estándar re-escribe sólo una de las pasadas).
Pregunta 1 (si lo medido estuviera roto, ¿se vería?): si el detector VIA_MODIS no se activara, `por_detector` no traería
  VIA_MODIS y `detector_por_sensor` diría K en MODIS. Control positivo: la protegida de Chillán MODIS 2026-10-25 07:20
  (K no la publicó, flag actual del audit del 2026-10-26) tiene que pasar a decir «detector VIA_MODIS» con D=2026-10-25.
Pregunta 2 (instrumento muerto): si el audit no corriera, no habría latest.json nuevo (se comprueba generated_utc) y el
  script lo dice como SIN DATO.
Los JSON del worktree se restauran desde el índice (git checkout -- data/mirova_equivalent) al terminar.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
WT = Path(sys.argv[1])
D = sys.argv[2] if len(sys.argv) > 2 else "2026-10-25"
PARCHE = len(sys.argv) > 3 and sys.argv[3] == "parche"   # REGIMENES con VIA_MODIS sólo en memoria (medición)
OUT = Path(__file__).resolve().parent
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
        "Villarrica", "PuyehueCordonCaulle", "Chaiten"]


def correr(etiqueta):
    lat = WT / "data" / "audit_continuous" / "latest.json"
    antes = json.loads(lat.read_text(encoding="utf-8")).get("generated_utc")
    cmd = [sys.executable, str(OUT / "audit_parchado.py"), str(WT)] if PARCHE else [sys.executable, "scripts/auto_audit_weekly.py"]
    p = subprocess.run(cmd, cwd=WT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    (OUT / f"audit_{etiqueta}{'_parche' if PARCHE else ''}_stdout.txt").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr, encoding="utf-8")
    d = json.loads(lat.read_text(encoding="utf-8"))
    if d.get("generated_utc") == antes:
        print(f"[{etiqueta}] SIN DATO: latest.json no se regeneró (rc={p.returncode})")
        return None
    shutil.copy(lat, OUT / f"audit_{etiqueta}{'_parche' if PARCHE else ''}_latest.json")
    return d


def marcar(fecha_desde, solo_aqua_en=None):
    n = 0
    for v in VOLS:
        p = WT / "data" / "mirova_equivalent" / f"{v}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        for r in d["records"]:
            s, dt = str(r.get("sensor") or ""), str(r.get("datetime_utc") or "")
            if not s.startswith("MODIS"):
                continue
            if dt[:10] >= fecha_desde or (solo_aqua_en and dt[:10] == solo_aqua_en and s == "MODIS_AQUA"):
                r["via_codigo_mirova"] = True
                n += 1
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return n


def restaurar():
    subprocess.run(["git", "-C", str(WT), "checkout", "--", "data/mirova_equivalent"], check=True)


def resumen(etiqueta, d):
    if d is None:
        return
    print(f"\n== {etiqueta}: generated {d['generated_utc']} ventana {d['window']} veredicto {d['verdict']}")
    print(f"   detector: {d.get('detector')}")
    ev_m = (d.get("recall") or {}).get("MODIS")
    print(f"   recall MODIS que decide: {ev_m}")
    pdx = d.get("por_detector") or {}
    for det, ev in pdx.items():
        print(f"   por_detector[{det}] recall MODIS: {(ev.get('recall') or {}).get('MODIS')}")
    print(f"   fuera_de_detector: {d.get('fuera_de_detector')}")
    print(f"   avisos_detector: {d.get('avisos_detector')}")
    fl = d.get("flags") or []
    print(f"   flags ({len(fl)}):")
    for f in fl:
        if "MODIS" in f:
            print(f"     [MODIS] {f[:200]}")
    print(f"   flags sin MODIS: {sum(1 for f in fl if 'MODIS' not in f)}")
    pl = d.get("plataformas")
    print(f"   plataformas/sin juzgar: {json.dumps(pl, ensure_ascii=False)[:400] if pl else pl}")


def main():
    try:
        restaurar()
        c = correr("control")
        resumen("control (sin vía)", c)
        n = marcar(D)
        print(f"\nmarcados como vía: {n} records MODIS con datetime_utc >= {D} en los 11")
        v = correr(f"via_{D}")
        resumen(f"vía desde {D}", v)
        restaurar()
        from datetime import date, timedelta
        dm1 = (date.fromisoformat(D) - timedelta(days=1)).isoformat()
        n2 = marcar(D, solo_aqua_en=dm1)
        print(f"\nmezcla: marcados {n2} (desde {D} y sólo MODIS_AQUA el {dm1})")
        m = correr(f"mezcla_{dm1}")
        resumen(f"mezcla (frontera {dm1} con Terra en K)", m)
    finally:
        restaurar()
        print("\nJSON restaurados desde el índice del worktree")


if __name__ == "__main__":
    main()
