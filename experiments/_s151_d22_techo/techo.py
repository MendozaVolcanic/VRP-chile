# -*- coding: utf-8 -*-
"""Tarea 1.3 del loop: techo del A/B de D22 bajo el criterio de victoria (S151).

POR QUE. El A/B "max sin la compuerta D22" quedo suspendido en S150 (docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md).
Con el criterio de Nicolas (2026-10-13), por debajo de 1 MW una alerta recuperada y una publicacion de mas pesan
igual. Antes de rehacer el pre-registro conviene saber: (1) si alguna de las perdidas del camino D22 es una alerta
PROTEGIDA (VRP >= 1 MW, docs/S151_CRITERIO_CLASE_MIROVA.md), porque eso la volveria veto y no suma; (2) cuanto es lo
maximo que el A/B puede ganar en la suma de errores, contra la cota de lo que puede reabrir (271 negativos limpios
del mismo camino, H4 del verificador).

Lee experiments/_s150_debiles/filas.json con las mismas reglas de camino y etiqueta que clases_rechazo.py.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
FILAS = AQUI.parent / "_s150_debiles" / "filas.json"
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}
COTA_REAPERTURA = 271  # VERIFICADOR_PREREGISTRO_D22.md H4, negativos limpios de VIIRS 375 del camino D22


def camino_d22(r):
    b = r["B"]
    if b["diag_n_first_pass_pixels"]:
        return False
    exc = (b["ap_bt_max"] - b["t_bg_k"]) if b.get("ap_bt_max") is not None and b.get("t_bg_k") else None
    return exc is not None and exc < 3.0


def confiable(r):
    return r["clave"] not in MALAS and not (r["solo_ocr"] and r["dt"] < "2026-06-13")


def vrp_mirova(r):
    vs = [m["vrp_mw"] for m in r["mirova"] if m.get("vrp_mw") is not None and "ALERTA" in m.get("tipo", "")]
    return max(vs) if vs else None


def main():
    filas = json.load(open(FILAS, encoding="utf-8"))
    sel = [r for r in filas if r["b"] == "VIIRS375" and r["perdida"] and camino_d22(r)]
    conf = [r for r in sel if confiable(r)]
    print(f"perdidas de max en VIIRS 375 por el camino D22: {len(sel)}; con etiqueta confiable: {len(conf)}")
    for r in sorted(conf, key=lambda r: r["clave"]):
        v = vrp_mirova(r)
        print(f"  {r['clave']:42s} VRP MIROVA {v if v is not None else 'NA':>6} MW  "
              f"{'PROTEGIDA' if v is not None and v >= 1 else 'Muy Bajo'}  fuente {'solo OCR' if r['solo_ocr'] else 'tabla'}")
    protegidas = [r for r in conf if (vrp_mirova(r) or 0) >= 1]
    noches = {(r["vol"], r["dt"][:10]) for r in conf}
    print(f"protegidas entre las confiables: {len(protegidas)}")
    print(f"techo de ganancia en la suma de errores (todas recuperadas, ninguna reapertura): {len(conf)} pasadas, "
          f"{len(noches)} noches-volcan")
    print(f"cota de reapertura en negativos limpios por el mismo camino (H4): {COTA_REAPERTURA}; el A/B gana solo si "
          f"reabre menos de {len(conf)} de ellos, o sea menos del {100 * len(conf) / COTA_REAPERTURA:.1f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
