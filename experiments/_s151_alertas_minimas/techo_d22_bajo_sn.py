# -*- coding: utf-8 -*-
"""D-9 (issue #811) y la tarea 1.3: el umbral de equilibrio del A/B de D22, recalculado con la regla SN.

POR QUE. La tarea 1.3 (experiments/_s151_d22_techo/techo.py) concluyo que quitar la compuerta D22 solo gana si
reabre menos de 14 de los 271 negativos limpios de VIIRS 375 que el mismo camino puede reabrir (5,2 %). Con SN cambian
las dos cosas: el numerador, porque 9 de las 14 alertas recuperables son de 0,05 MW o menos y dejan de ser alertas
(quedan 5; 8 con la variante que deja 0,05 como alerta); y el denominador, porque esas pasadas, y otras de las mismas
noches que quedan sin alerta, pasan a ser negativos limpios. Un negativo nuevo entra al denominador si es del mismo
estrato que los 271: B (sin Test 1) lo publica, F (max) no, y el record de B va por el camino D22.

Camino D22, la regla del anexo de docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md (la misma de clases_rechazo.camino):
el record de B no tiene pixeles del primer pase (`diag_n_first_pass_pixels == 0`) y su pixel alertado mas caliente
esta a menos de 3 K sobre el fondo (`max(anomaly_pixels.bt_k) - t_bg_k < 3`).

CONTROL. Con la etiqueta original, la misma regla sobre los mismos records tiene que dar los 271 del verificador.

Los records de B salen de las ramas `s146-ab/<run>` de los meses de S150 (las de
experiments/_s150_debiles/extraer_y_tabular.py), con `git archive` CON RUTA a un temporal fuera del repo.

Uso: python techo_d22_bajo_sn.py --congelado-meses DIR --tmp DIR_TEMPORAL > techo_d22_bajo_sn_salida.txt
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import suma_errores as se  # deja sys.stdout en utf-8
import veredictos_tres_reglas as V
from comun import RAIZ

B = "_s146_ab_sin_test1"
RUNS = {"abril": ["35639417826", "37823348991"], "mayo": ["35599902448"], "junio": ["35675490175"],
        "julio": ["35728617326"], "agosto": ["35759688167"]}   # extraer_y_tabular.py: el run posterior pisa
NUMERADOR_ORIGINAL, COTA_ORIGINAL = 14, 271   # experiments/_s151_d22_techo/salida.txt


def records_b(mes, tmp: Path):
    """{clave de pasada: [records de B]} del mes, VIIRS 375."""
    base = tmp / mes
    if not base.exists():
        for r in RUNS[mes]:
            subprocess.run(["git", "fetch", "-q", "origin", "refs/heads/s146-ab/%s:refs/remotes/origin/s146-ab/%s" % (r, r)],
                           cwd=RAIZ, check=True)
            ruta = "experiments/_s146_ab_sin_test1/salidas/%s/%s" % (r, B)
            if not subprocess.run(["git", "ls-tree", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, text=True).stdout.strip():
                continue
            tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
            with tarfile.open(fileobj=io.BytesIO(tar)) as t:
                for m in t.getmembers():
                    if m.isfile() and m.name.endswith(".json"):
                        dst = base / Path(m.name).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(t.extractfile(m).read())
    out = collections.defaultdict(list)
    for p in sorted(base.glob("*.json")):
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            if V.bp.bucket(r.get("sensor")) == "VIIRS375":
                out["|".join((p.stem, "VIIRS375", r.get("datetime_utc", "")[:16]))].append(r)
    return out


def camino_d22(r):
    bts = [q.get("bt_k") for q in (r.get("anomaly_pixels") or []) if q.get("bt_k") is not None]
    if r.get("diag_n_first_pass_pixels") or not bts or r.get("t_bg_k") is None:
        return False
    return max(bts) - r["t_bg_k"] < 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--congelado-meses", required=True)
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    grupos = se.leer_pasadas(V.AQUI / "pasadas_meses_B_F.csv", ["B", "F"], lambda r: "|VIIRS375|" in r["clave"])
    cota = collections.Counter(); sin_record = collections.Counter(); varios = collections.Counter(); detalle = []
    for mes in se.MESES:
        pas = grupos[mes]
        ventana = se.verificar_congelado(Path(a.congelado_meses) / mes, se.CONG_MESES_MANIF / mes / "MANIFIESTO.json")
        ref = se.cargar_ref(Path(a.congelado_meses) / mes, historico=False)
        recs = records_b(mes, Path(a.tmp))
        for nombre, modo, umbral in V.REGLAS:
            if modo == "SE":
                continue   # en SE no hay negativos nuevos: la noche no cambia
            etq = V.etiquetar(ref, sorted(pas), ventana, modo, umbral)
            for k, v in pas.items():
                if etq[k][0] != "neg_limpio" or v["pub"].get("B") != 1 or v["pub"].get("F") != 0:
                    continue
                rs = recs.get(k, [])
                if not rs:
                    sin_record[nombre] += 1; continue
                varios[nombre] += len(rs) > 1
                if any(camino_d22(r) for r in rs):
                    cota[nombre] += 1
                    if v["lab"] != "neg_limpio":
                        detalle.append((nombre, k, v["lab"]))
        print(f"   {mes}: records de B VIIRS 375 {sum(len(x) for x in recs.values())}")
    print("\n== COTA DE REAPERTURA (negativos limpios de VIIRS 375 que B publica, F no y van por el camino D22)")
    for nombre in ("original", "SN", "SN_004"):
        print(f"   regla {nombre:8s} {cota[nombre]} (sin record de B {sin_record[nombre]}; con mas de un record {varios[nombre]})")
    ok = cota["original"] == COTA_ORIGINAL
    print(f"   control: con la regla original da {cota['original']}, el verificador dio {COTA_ORIGINAL}: {'OK' if ok else 'FALLA'}")
    print("   negativos nuevos que entran a la cota:")
    for d in sorted(detalle):
        print(f"      {d[0]:8s} {d[1]} (antes {d[2]})")
    print("\n== UMBRAL DE EQUILIBRIO DEL A/B DE D22 (gana solo si reabre menos que lo que recupera)")
    import re
    vrps = [float(m.group(1)) for m in re.finditer(r"VRP MIROVA\s+([0-9.]+) MW", se.D22.read_text(encoding="utf-8"))]
    assert len(vrps) == NUMERADOR_ORIGINAL
    nums = {"original": len(vrps), "SN": sum(not V.cm.es_alerta_minima(x, "VIIRS375") for x in vrps),
            "SN_004": sum(not V.cm.es_alerta_minima(x, "VIIRS375", V.cm.UMBRAL_MINIMA_VARIANTE_MW) for x in vrps)}
    for nombre, num in nums.items():
        print(f"   regla {nombre:8s} recupera como maximo {num} | cota {cota[nombre]} | umbral {100 * num / cota[nombre]:.1f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
