# -*- coding: utf-8 -*-
"""Verificador del candado MOD-D: ¿pueden ponerse en rojo los controles externos del evaluador (referencia,
reetiquetado, blobs, procedencia)? La batería los recibe ya en OK (OK_EXT) y el ensayo en seco sólo mide el caso
positivo; A110 pide medir el nulo. Aquí se convierte el lote de S159 como hace ensayo_en_seco.convertir y se corre
evaluar_paquete.py tres veces:
  A. referencia congelada tal cual (control positivo del instrumento: referencia y reetiquetado OK)
  B. copia de la referencia con UNA fila del consolidado alterada (VRP de una alerta de Láscar): referencia tiene que
     dar INDECIDIBLE (sha256 distinto) y el veredicto INDECIDIBLE
  C. artefacto con la cabecera de una segunda parte en OTRO commit: procedencia INDECIDIBLE
Sólo escribe en verificador_candado/ y en temporales. Uso: python -I nulo_controles_externos.py --ref <dir ref>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CANDADO = AQUI.parent
sys.path.insert(0, str(CANDADO))
import ensayo_en_seco as EN  # noqa: E402


def evaluar(art, ref):
    p = subprocess.run([sys.executable, "-I", str(CANDADO / "evaluar_paquete.py"), "--art", str(art), "--ref", str(ref),
                        "--salida", str(Path(art) / "res.json")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    res = json.loads((Path(art) / "res.json").read_text(encoding="utf-8")) if (Path(art) / "res.json").exists() else {}
    return res, p.returncode, (p.stdout + p.stderr)[-1200:]


def estados(res):
    c = res.get("controles", {})
    return {k: (v if isinstance(v, str) else v.get("estado")) for k, v in c.items()}, res.get("veredicto")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(dir=AQUI) as td:
        td = Path(td)
        art = td / "art"
        n = EN.convertir(CANDADO / "referencia_s159", art)
        print("pasadas convertidas:", n)
        # A
        resA, rcA, logA = evaluar(art, a.ref)
        eA, vA = estados(resA)
        print("A (ref intacta):", vA, eA, "" if rcA == 0 else logA)
        # B: referencia alterada en un byte útil (una fila de alerta de Lascar)
        ref2 = td / "ref_alterada"
        shutil.copytree(a.ref, ref2)
        cons = ref2 / "registro_vrp_consolidado.csv"
        lineas = cons.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        i = next(i for i, l in enumerate(lineas) if "Lascar" in l and "ALERTA" in l)
        print("fila alterada:", lineas[i].strip()[:160])
        lineas[i] = lineas[i].replace("ALERTA", "RUTINA", 1)
        cons.write_text("".join(lineas), encoding="utf-8")
        art2 = td / "art2"
        shutil.copytree(art, art2)
        (art2 / "res.json").unlink(missing_ok=True)
        resB, rcB, logB = evaluar(art2, ref2)
        eB, vB = estados(resB)
        print("B (ref alterada):", vB, eB, "" if rcB == 0 else logB)
        # C: segunda parte con otro commit
        art3 = td / "art3"
        shutil.copytree(art, art3)
        (art3 / "res.json").unlink(missing_ok=True)
        cab = json.loads((art3 / "ab_parte00.jsonl").read_text(encoding="utf-8").splitlines()[0])
        cab.update(parte=1, commit="otro-commit")
        (art3 / "ab_parte01.jsonl").write_text(json.dumps(cab) + "\n", encoding="utf-8")
        resC, rcC, logC = evaluar(art3, a.ref)
        eC, vC = estados(resC)
        print("C (dos commits):", vC, eC, "" if rcC == 0 else logC)
        ok = (eA.get("referencia") == "OK" and eA.get("reetiquetado") == "OK"
              and eB.get("referencia") == "INDECIDIBLE" and vB == "INDECIDIBLE"
              and eC.get("procedencia") == "INDECIDIBLE")
        print("NULO DE LOS CONTROLES EXTERNOS:", "PUEDEN FALLAR" if ok else "ALGO NO FALLA COMO DEBE")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
