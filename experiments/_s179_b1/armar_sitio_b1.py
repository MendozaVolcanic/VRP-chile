"""S179: arma un sitio local que muestra el tablero como quedaría con B1 encendido, para probarlo en navegador.

POR QUÉ: la regla de VIIRS (§5) pide probar `index.html`, `diario.html` y `mosaico.html` con records de la vía en VIIRS
375 antes del merge de B1. Producción todavía no tiene esos records; la sombra (`data/sombra_codigo_mirova/`) sí, desde
el 2026-11-03, con el mismo código y el mismo perfil de producción salvo el directorio. Este script copia el frontend y
los datos de una rama, y en cada volcán reemplaza los records de VIIRS 375 (Suomi NPP, NOAA-20 y NOAA-21, sin `_750`)
desde la primera pasada de la sombra por los de la sombra. MODIS y VIIRS 750 quedan como en producción. No escribe en
el repositorio: todo va a la carpeta de salida.

Uso: python armar_sitio_b1.py --repo <worktree> --salida <carpeta vacía>
Control: imprime por volcán cuántos records de VIIRS 375 salieron de producción y cuántos entraron de la sombra, y
cuántos de los que entraron traen `via_codigo_mirova: true` (si fuera 0, el sitio no probaría nada).
"""
import argparse
import io
import json
import shutil
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
V375 = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    repo, sal = Path(a.repo), Path(a.salida)
    if sal.exists() and any(sal.iterdir()):
        sys.exit(f"la salida {sal} no está vacía")
    shutil.copytree(repo / "frontend", sal / "frontend")
    shutil.copytree(repo / "data" / "mirova", sal / "data" / "mirova")
    for f in ("latest_consolidado.csv",):
        if (repo / f).exists():
            shutil.copy2(repo / f, sal / f)
    (sal / "data" / "mirova_equivalent").mkdir(parents=True)
    for s in sorted((repo / "data" / "sombra_codigo_mirova").glob("*.json")):
        prod_p = repo / "data" / "mirova_equivalent" / s.name
        if not prod_p.exists():
            continue
        prod = json.loads(prod_p.read_text(encoding="utf-8"))
        som = json.loads(s.read_text(encoding="utf-8"))
        som375 = [r for r in som["records"] if r.get("sensor") in V375]
        if not som375:
            continue
        desde = min(r["datetime_utc"] for r in som375)
        fuera = [r for r in prod["records"] if r.get("sensor") in V375 and r.get("datetime_utc", "") >= desde]
        prod["records"] = [r for r in prod["records"]
                           if not (r.get("sensor") in V375 and r.get("datetime_utc", "") >= desde)] + som375
        prod["records"].sort(key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
        (sal / "data" / "mirova_equivalent" / s.name).write_text(json.dumps(prod, ensure_ascii=False), encoding="utf-8")
        via = sum(1 for r in som375 if r.get("via_codigo_mirova") is True)
        print(f"{s.stem:22s} desde {desde}: VIIRS 375 salen {len(fuera):3d} de producción, entran {len(som375):3d} de la "
              f"sombra ({via} con via_codigo_mirova true)")
    # sin *_recent.json el tablero carga el JSON completo (index.html l. 991 a 996, diario.html l. 196 a 197)


if __name__ == "__main__":
    main()
