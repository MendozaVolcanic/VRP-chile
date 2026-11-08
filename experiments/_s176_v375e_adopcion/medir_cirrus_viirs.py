# -*- coding: utf-8 -*-
"""S176 (diseño docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisión 5): la regla de cirrus del tablero sobre
los records de VIIRS de la vía en data/sombra_codigo_mirova/.

POR QUÉ, COMO GEÓLOGO. El tablero oculta un record con el píxel más caliente bajo 0 °C y más de 10 MW: es la firma de la nube
fina que el path D de K confundía con calor. La vía no tiene path D, y desde S173 los records de la vía quedan exentos de esa
regla (`CambioDetector.esViaCodigoMirova`). Falta saber qué pasa en VIIRS: si hay records fríos y grandes, ¿qué mostraría el
tablero con la exención y qué ocultaría sin ella? Si hubiera muchos y sin alerta de MIROVA, el encendido publicaría cirrus.

Qué hace: ejecuta con node el predicado real del tablero (banco_paridad.correr_node sobre frontend/index.html) dos veces sobre
los mismos records, con la marca de la vía tal cual y con la marca quitada, y cuenta por sensor. Control positivo (A110): un
record sintético frío de 20 MW tiene que publicarse con la marca y ocultarse sin ella.
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for p in (RAIZ, RAIZ / "scripts"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
import banco_paridad as bp  # noqa: E402

SOMBRA = RAIZ / "data" / "sombra_codigo_mirova"


def correr(recs):
    return bp.correr_node(recs)


def main():
    inner = bp.inner_desde_html()
    con, sin, meta = [], [], []
    for f in sorted(SOMBRA.glob("*.json")):
        vol = f.stem
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if b not in ("VIIRS375", "VIIRS750"):
                continue
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            s2 = dict(slim)
            s2.pop("via_codigo_mirova", None)
            con.append([slim, inner[vol]])
            sin.append([s2, inner[vol]])
            meta.append((vol, b, r.get("datetime_utc"), r.get("t_max_k"), r.get("via_codigo_mirova")))
    pc, ps = correr(con), correr(sin)
    print(f"records de VIIRS en la sombra: {len(meta)}; fechas {min(m[2] for m in meta)} a {max(m[2] for m in meta)}")
    por = Counter(m[1] for m in meta)
    frio = [i for i, m in enumerate(meta) if m[3] is not None and m[3] < 273.15]
    print("por sensor:", dict(por))
    print("marca de la vía:", dict(Counter(str(m[4]) for m in meta)))
    print("con t_max bajo 273,15 K:", dict(Counter(meta[i][1] for i in frio)), "de", len(frio))
    grandes = [i for i in frio if pc[i][3] > 10]
    print("fríos con la magnitud del tablero sobre 10 MW (regla de cirrus):", dict(Counter(meta[i][1] for i in grandes)),
          "de", len(grandes))
    cambia = [i for i in range(len(meta)) if pc[i][4] != ps[i][4]]
    print("records cuya publicación cambia al quitar la exención de la vía:", len(cambia))
    for i in cambia[:40]:
        print("   ", meta[i], "disp con marca", round(pc[i][3], 3), "publica con/sin", pc[i][4], ps[i][4])
    pub_con = sum(p[4] for p in pc)
    print("publicados con la marca:", pub_con, "| sin la marca:", sum(p[4] for p in ps))
    print("fríos sobre 10 MW publicados con la exención:", sum(1 for i in grandes if pc[i][4]))
    for i in grandes[:40]:
        print("   ", meta[i], "disp", round(pc[i][3], 3))
    print("fríos bajo 10 MW:", len(frio) - len(grandes), "; su magnitud máxima:",
          round(max([pc[i][3] for i in frio if pc[i][3] <= 10] or [0]), 3))
    # control positivo
    frio_grande = {"vrp_mw": 20.0, "distance_class": "summit", "t_max_k": 260.0, "sensor": "VIIRS_NOAA20",
                   "primary_cluster": {"vrp_mw": 20.0, "centroid_dist_km": 1.0, "n_pixels": 3}}
    r = correr([[dict(frio_grande, via_codigo_mirova=True), 5.0], [frio_grande, 5.0]])
    print("control positivo: sintético frío de 20 MW, publica con marca / sin marca:", r[0][4], r[1][4],
          "(tiene que ser 1 y 0)")
    assert r[0][4] == 1 and r[1][4] == 0


if __name__ == "__main__":
    main()
