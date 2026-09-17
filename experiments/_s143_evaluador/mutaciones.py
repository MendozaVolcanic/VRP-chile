# -*- coding: utf-8 -*-
"""S143: batería de mutaciones del evaluador, para saber qué vigilan de verdad sus tests.

POR QUÉ. Una suite verde no dice qué cubre. El verificador externo del PR #686 (H3) corrió 22
mutaciones sobre el evaluador y encontró que 9 sobrevivían, todas concentradas en las REGLAS DE
VEREDICTO: qué extremo del intervalo decide el criterio 2, la dirección de la desigualdad del
criterio 3, el umbral 0 del criterio 1, la exclusión de volcanes desparejos, el castigo al brazo sin
pares decisivos y los valores por defecto de la cota y la tolerancia. Un instrumento sin fusible
justo donde importa: si mañana alguien "simplifica" una de esas líneas, nada se pone rojo.

QUÉ HACE. Aplica cada mutación sola sobre el archivo, corre `tests/test_evaluador_ab_s143.py`,
restaura el archivo y anota si la mutación MUERE (algún test falla) o VIVE (suite verde). Escribe
`MUTACIONES.md` con la tabla. Las inocuas (comentario, orden de claves) tienen que vivir: son el
control de que la batería no se está engañando sola.

USO (read-only sobre el repo salvo `MUTACIONES.md`):
    python experiments/_s143_evaluador/mutaciones.py [--repeticiones 1]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EV = HERE / "evaluar.py"
FU = HERE / "fusionar.py"
TESTS = "tests/test_evaluador_ab_s143.py"

# (id, archivo, texto viejo, texto nuevo, qué rompe, esperado: "muerta" o "viva")
MUTACIONES = [
    ("M1", EV, "if cota <= presupuesto:", "if cota > presupuesto:",
     "invierte la cota de mismo objeto", "muerta"),
    ("M2", EV, '"perdidas": sorted(conf - b["pub_cota"]),', '"perdidas": sorted(conf - b["pub"]),',
     "no le exige la cota al brazo (revierte el hallazgo 2)", "muerta"),
    ("M3", EV, "tot_d += (sel[:, :, 2] - sel[:, :, 1]).sum(axis=1)",
     "tot_d += (sel[:, :, 1] - sel[:, :, 2]).sum(axis=1)",
     "da vuelta el signo del bootstrap", "muerta"),
    ("M4", EV, """    for vol in sorted(grupos):
        arr = np.asarray(grupos[vol], dtype=float)""",
     """    for vol in ["__pool__"]:
        arr = np.asarray([x for v in sorted(grupos) for x in grupos[v]], dtype=float)""",
     "bootstrap sin estratificar", "muerta"),
    ("M5", EV, 'hi = r["total"]["ic95"][1]', 'hi = r["total"]["ic95"][0]',
     "criterio 2 decide con el extremo BAJO del intervalo", "muerta"),
    ("M6", EV, 'if b is not None and c["pub"] and b["pub"] and c["disp"] > 0 and b["disp"] > 0:',
     'if b is not None and c["pub"] and c["disp"] > 0:',
     "criterio 3 sin exigir que publiquen los dos", "muerta"),
    ("M7", EV, 'for fuente in ("CONS", "OCR"):', 'for fuente in ("OCR", "CONS"):',
     "fila de MIROVA: OCR antes que CONS", "muerta"),
    ("M8", EV, '"solo_brazo": len(k.keys() - base.keys()),', '"solo_brazo": 0,',
     "cobertura ciega a las pasadas de más del brazo", "muerta"),
    ("M9", EV, '"product_version_distinto": sum(1 for c in comunes if base[c] != k[c])',
     '"product_version_distinto": 0', "cobertura ciega a product_version", "muerta"),
    ("M10", EV, 'blq["evaluado"] = blq["n_pos_control"] >= n_min',
     'blq["evaluado"] = blq["n_pares_decisivo"] >= n_min',
     "n mínimo contado en los pares y no en las pos del control", "muerta"),
    ("M11", EV, 'dec_b.append(b["disp"] / m)', 'dec_b.append(c["disp"] / m)',
     "magnitud del brazo tomada del control", "muerta"),
    ("M12", FU, "if _canon(unido[k][1]) != _canon(r):", "if False:",
     "fusión que no avisa conflictos entre tramos", "muerta"),
    ("M13", EV, "# ------------------------------------------------------------------ criterio 1",
     "# ---- criterio 1 (comentario cambiado)", "sólo cambia un comentario", "viva"),
    ("M15", EV, 'pares = [(c, idx[c["clave"]]) for c in pas_ctrl if c["lab"] == "neg_limpio" and c["clave"] in idx]',
     'pares = [(c, idx[c["clave"]]) for c in pas_ctrl if c["clave"] in idx and idx[c["clave"]]["lab"] == "neg_limpio"]',
     "criterio 2 filtra por la etiqueta del brazo y no la del control", "viva"),
    ("M16", EV, 'and t["dist_a_1_brazo"] <= t["dist_a_1_control"] + 1e-12',
     'and t["dist_a_1_brazo"] >= t["dist_a_1_control"] - 1e-12',
     "criterio 3 con la desigualdad invertida", "muerta"),
    ("M17", EV, "rng = np.random.default_rng(semilla)", "rng = np.random.default_rng()",
     "bootstrap sin semilla", "muerta"),
    ("M18", EV, "if bp.es_pasada_diurna_descartada(b, lat, lon, dt):",
     "if False and bp.es_pasada_diurna_descartada(b, lat, lon, dt):",
     "sin filtro de pasada diurna", "muerta"),
    ("M19", EV, "if cota <= presupuesto:", "if True:",
     "la noche se acepta siempre (cota apagada)", "muerta"),
    ("M20", EV, 'TOL_MAGNITUD = PARAMETROS["tol_magnitud"]', "TOL_MAGNITUD = 0.10",
     "tolerancia de magnitud 0,05 a 0,10", "muerta"),
    ("M21", EV, '"por_volcan": por_vol, "cumple": len(perd) == 0}',
     '"por_volcan": por_vol, "cumple": len(perd) <= 1}',
     "criterio 1 cumple con hasta una pérdida", "muerta"),
    ("M22", EV, "evaluados = [v for v in vols if v not in desparejos]", "evaluados = list(vols)",
     "los volcanes desparejos ya no se excluyen", "muerta"),
    ("M23", EV, """                blq["n_pares_decisivo"] == 0
                or blq["dist_a_1_brazo"] - blq["dist_a_1_control"] > tol + 1e-12)""",
     """                False
                or blq["dist_a_1_brazo"] - blq["dist_a_1_control"] > tol + 1e-12)""",
     "brazo sin pares decisivos deja de contar como que empeora", "muerta"),
    ("M24", EV, 'PRESUPUESTO_COTA_KM = PARAMETROS["cota_km"]', "PRESUPUESTO_COTA_KM = 5.0",
     "cota por defecto 0,55 a 5,0 km", "muerta"),
]


def correr_suite():
    r = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True)
    cola = [l for l in r.stdout.splitlines() if " passed" in l or " failed" in l]
    return r.returncode == 0, (cola[-1] if cola else r.stdout[-200:])


def main(argv=None):
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeticiones", type=int, default=1,
                    help="corridas por mutación (para las que dependen del azar, como M17)")
    ap.add_argument("--solo", nargs="+", default=None,
                    help="ids a probar, p. ej. --solo M17 (por defecto, todas)")
    ap.add_argument("--sin-escribir", action="store_true",
                    help="no sobrescribe MUTACIONES.md ni mutaciones.json (corridas parciales)")
    a = ap.parse_args(argv)
    mutaciones = [m for m in MUTACIONES if a.solo is None or m[0] in a.solo]

    verde, linea_base = correr_suite()
    if not verde:
        print(f"La suite ya está roja antes de mutar nada: {linea_base}")
        return 1
    filas = []
    originales = {p: p.read_text(encoding="utf-8") for p in {m[1] for m in mutaciones}}
    try:
        for mid, path, viejo, nuevo, desc, esperado in mutaciones:
            if viejo not in originales[path]:
                filas.append({"id": mid, "descripcion": desc, "esperado": esperado,
                              "estado": "NO APLICABLE", "detalle": "el texto mutado ya no existe"})
                continue
            resultados = []
            for _ in range(a.repeticiones):
                path.write_text(originales[path].replace(viejo, nuevo, 1), encoding="utf-8")
                ok, linea = correr_suite()
                resultados.append((ok, linea))
                path.write_text(originales[path], encoding="utf-8")
            muere_siempre = all(not ok for ok, _ in resultados)
            vive_siempre = all(ok for ok, _ in resultados)
            estado = "muerta" if muere_siempre else ("viva" if vive_siempre else "inestable")
            filas.append({"id": mid, "archivo": path.name, "descripcion": desc,
                          "esperado": esperado, "estado": estado,
                          "corridas": a.repeticiones, "detalle": resultados[-1][1]})
            print(f"{mid:4s} {estado:10s} (esperado {esperado:7s}) {desc}")
    finally:
        for p, t in originales.items():
            p.write_text(t, encoding="utf-8")

    coinciden = all(f["estado"] == f["esperado"] for f in filas if f["estado"] != "NO APLICABLE")
    salida = {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "linea_base": linea_base, "repeticiones": a.repeticiones,
              "muertas": sum(1 for f in filas if f["estado"] == "muerta"),
              "vivas": sum(1 for f in filas if f["estado"] == "viva"),
              "total": len(filas), "todas_como_se_esperaba": coinciden, "filas": filas}
    if a.sin_escribir:
        print(json.dumps(salida, indent=1, ensure_ascii=False))
        return 0 if coinciden else 1
    (HERE / "mutaciones.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False),
                                          encoding="utf-8")
    L = ["# Batería de mutaciones del evaluador", "",
         f"> Generada por `experiments/_s143_evaluador/mutaciones.py` el {salida['generado_utc']}, "
         f"{a.repeticiones} corrida(s) por mutación. Suite de referencia: `{linea_base}`. "
         f"Mueren {salida['muertas']} de {salida['total']}; viven {salida['vivas']}, todas "
         "declaradas como inocuas o equivalentes. Ningún número está escrito a mano.", "",
         "| id | archivo | qué cambia | esperado | estado |", "|---|---|---|---|---|"]
    for f in filas:
        L.append(f"| {f['id']} | {f.get('archivo', '')} | {f['descripcion']} | {f['esperado']} | "
                 f"**{f['estado']}** |")
    L += ["", "## Las que viven, y por qué",
          "",
          "- **M13**: cambia un comentario. Si muriera, la batería estaría midiendo otra cosa.",
          "- **M15**: equivalente. La etiqueta `neg_limpio` la fija la referencia de MIROVA, que es",
          "  la misma para el control y para el brazo en la misma pasada, así que filtrar por una o",
          "  por otra selecciona el mismo conjunto. No es un hueco de cobertura.",
          ""]
    (HERE / "MUTACIONES.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nmueren {salida['muertas']} de {salida['total']}, viven {salida['vivas']}, "
          f"todas como se esperaba: {coinciden}")
    return 0 if coinciden else 1


if __name__ == "__main__":
    sys.exit(main())
