"""S163 H3, tamaño en la unidad del operador (A94): noches publicadas antes y después del reemplazo con K (#883).

Compara dos commits (por defecto el tag pre-s158-reemplazo-k, corpus que el tablero sirvió hasta el despliegue de #883
el 2026-10-21 11:48 UTC, contra origin/main de hoy). Una noche es (volcán, fecha local de la noche): la fecha UTC de
(datetime_utc − 12 h), así que las pasadas de 12:00 UTC del día D a 12:00 UTC del D+1 son la noche D. «La noche publica»
si el tablero publica al menos un record de ella en cualquier sensor (predicado con node, A97). Se cuentan sólo
observaciones del 2025-02-15 al 2026-09-17 (antes de la marca de régimen de los datos, S155), que es el tramo de H3.
Se informa también separando por sensor. Sólo lectura. Uso: python -I noches_h3.py [antes] [despues]
"""
import collections
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_h3 as c  # noqa: E402

ANTES = sys.argv[1] if len(sys.argv) > 1 else "pre-s158-reemplazo-k"
DESPUES = sys.argv[2] if len(sys.argv) > 2 else "origin/main"
DESDE, HASTA = "2025-02-15", "2026-09-18"


def noche(dtu):
    return (datetime.strptime(dtu[:16], "%Y-%m-%d %H:%M") - timedelta(hours=12)).date().isoformat()


def publicadas(commit):
    sha = c.git("rev-parse", commit).stdout.strip()
    html = c.git("show", f"{sha}:frontend/index.html").stdout
    c.bp.HTML = Path(c.os.environ.get("TMP", "/tmp")) / f"h3_noches_{sha[:9]}.html"
    c.bp.HTML.write_text(html, encoding="utf-8")
    inner = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', html):
        inner.setdefault(m.group(1), float(m.group(2)))
    todas, pub, pub_sensor = set(), set(), set()
    for v in c.VOLS:
        recs = json.loads(c.git("show", f"{sha}:data/mirova_equivalent/{v}.json").stdout)["records"]
        recs = [r for r in recs if DESDE <= r["datetime_utc"][:10] < HASTA]
        res = c.bp.correr_node([[r, inner[v]] for r in recs])
        for r, p in zip(recs, res):
            k = (v, noche(r["datetime_utc"]))
            todas.add(k)
            if p[4]:
                pub.add(k)
                pub_sensor.add(k + (r.get("sensor", "").replace("_750", "|750").split("_")[0] + (
                    "_750" if r.get("sensor", "").endswith("_750") else ""),))
    return sha, todas, pub, pub_sensor


def main():
    sa, ta, pa, psa = publicadas(ANTES)
    sd, td, pd, psd = publicadas(DESPUES)
    print(f"antes  = {ANTES} ({sa[:9]}); después = {DESPUES} ({sd[:9]}); observaciones {DESDE} a {HASTA} (excl.)")
    print(f"noches con algún record: antes {len(ta)}, después {len(td)}, en ambos {len(ta & td)}")
    comunes = ta & td
    a, d = pa & comunes, pd & comunes
    print(f"noches publicadas (sobre las {len(comunes)} con record en ambos): antes {len(a)}, después {len(d)}")
    print(f"  publica -> no publica: {len(a - d)}")
    print(f"  no publica -> publica: {len(d - a)}")
    print(f"  publica en ambos: {len(a & d)}")
    print("\n== por volcán: noches publica->no publica / no publica->publica / publicadas antes / después ==")
    for v in c.VOLS:
        aa = {k for k in a if k[0] == v}
        dd = {k for k in d if k[0] == v}
        print(f"  {v:20s} {len(aa - dd):5d} {len(dd - aa):5d} {len(aa):5d} {len(dd):5d}")
    print("\n== por familia de sensor (noche-sensor): publica->no / no->publica ==")
    fam = sorted({k[2] for k in psa | psd})
    for f in fam:
        aa = {k for k in psa if k[2] == f and k[:2] in comunes}
        dd = {k for k in psd if k[2] == f and k[:2] in comunes}
        print(f"  {f:12s} {len(aa - dd):5d} {len(dd - aa):5d}")


if __name__ == "__main__":
    main()
