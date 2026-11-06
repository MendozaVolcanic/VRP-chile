"""S172, VS34-02: las mutaciones que el verificador vio pasar en verde, contra las pruebas nuevas.

POR QUÉ: una prueba que no puede fallar no vigila nada. El verificador (D:/vrp-trabajo/temporales/ver_s172_sombra34/
v5_mutaciones.py) encontró 10 de 34 mutaciones que pasaban en verde; aquí se repiten esas 10 (mismos nombres) más las
de las piezas nuevas de esta ronda (monitor, vecinos, Pages), y cada una tiene que hacer caer alguna prueba por
ASERCIÓN (un error de importación o de sintaxis no cuenta: S152, una mutación que cae no es una mutación atrapada).

Cómo: modifica el archivo en el worktree, corre tests/test_sombra_34_s172.py sin las 34 corridas de gránulo (salvo
-k propio), y restaura el texto original en un finally. Control: sin mutar, todo verde.
Uso: python experiments/_s172_sombra34/mutaciones_vs34_02.py   (salida: mutaciones_vs34_02_salida.txt al lado)
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
T = "tests/test_sombra_34_s172.py"
K = "not foco_en_el_crater"
VW, WF, VG, G = (".github/workflows/vigilancia-sombra-34.yml", ".github/workflows/sombra-34.yml",
                 "scripts/vigilar_sombra_34.py", "pipeline/grillas_mirova.yaml")
MON, PAG, VEC = (".github/workflows/nrt-monitor.yml", ".github/workflows/pages-deploy.yml",
                 "experiments/_s172_sombra34/vecinos.yaml")
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")

MUTACIONES = [
    # las 10 que pasaban en verde (nombres del verificador)
    ("VW1 CIEGA no abre issue (se mezcla con OK)", VW, "OK|ESPERA) echo", "OK|ESPERA|CIEGA) echo"),
    ("VW2 --dir apunta a la sombra de los 11", VW, "--dir data/sombra_34", "--dir data/sombra_codigo_mirova"),
    ("VW3 cron imposible (31 de febrero)", VW, 'cron: "27 23 * * *"', 'cron: "27 23 31 2 *"'),
    ("VW4 checkout de otra rama", VW, "ref: main", "ref: gh-pages"),
    ("W8 timeout del paso 75 -> 5 min", WF, "timeout-minutes: 75", "timeout-minutes: 5"),
    ("W9 permissions contents write -> read", WF, "contents: write", "contents: read"),
    ("W11 paso Tachar sin always", WF,
     "id: tachar\n        if: always() && steps.correr.outputs.corrio == 'true'",
     "id: tachar\n        if: steps.correr.outputs.corrio == 'true'"),
    ("W12 revision de records pierde always()", WF,
     "if: always() && steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_sombra.py",
     "if: steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_sombra.py"),
    ("G4 Antuco roi_v750 def->sens", G, "centro_lon: -71.34900, roi_v750: def}", "centro_lon: -71.34900, roi_v750: sens}"),
    ("V5 exit 0 aun en CIEGA", VG, 'return 1 if d["veredicto"] == "CIEGA" else 0', "return 0"),
    # las que el verificador ya veía caer, por si el cambio de prueba las soltó
    ("VW5 permissions issues write -> read", VW, "issues: write", "issues: read"),
    ("VW6 abrir() nunca crea", VW, "gh issue create --title", "echo omitido --title"),
    ("VW7 veredicto leido de otro archivo", VW, "veredicto.json'))['veredicto']", "veredicto_x.json'))['veredicto']"),
    ("VW8 Open issue sin always()", VW, "      - name: Open issue\n        if: always()", "      - name: Open issue"),
    # piezas nuevas de esta ronda
    ("M1 monitor: el paso de los 34 pierde always()", MON,
     "      - name: Vigilar la sombra de los 34 y su vigilancia\n        if: always()",
     "      - name: Vigilar la sombra de los 34 y su vigilancia"),
    ("M2 monitor: deja de mirar la vigilancia", MON, "{ wf: 'vigilancia-sombra-34.yml'", "{ wf: 'otra.yml'"),
    ("M3 monitor: tope de 26 h a 260 h", "scripts/nrt_monitor_decision.js",
     "function decidirAusencia(runs, ahoraMs, fijo, altaIso, maxHoras = 26",
     "function decidirAusencia(runs, ahoraMs, fijo, altaIso, maxHoras = 260"),
    ("M4 monitor: ignora el alta", "scripts/nrt_monitor_decision.js",
     "  if (!Number.isFinite(alta)) return fijo;", "  return fijo;"),
    ("P1 Pages excluye sólo la sombra de los 11", PAG, "cp -r data _site/data",
     "cp -r data _site/data\n          rm -rf _site/data/sombra_codigo_mirova"),
    ("N1 vecinos.yaml: Quetrupillan pierde a Villarrica", VEC, "  - vecino: Villarrica\n", "  - vecino: Villarica\n"),
]


def correr():
    p = subprocess.run([sys.executable, "-m", "pytest", T, "-q", "-p", "no:cacheprovider", "-k", K], cwd=REPO,
                       env=ENV, capture_output=True, text=True, encoding="utf-8")
    out = p.stdout + p.stderr
    fallas = [ln for ln in out.splitlines() if ln.startswith("FAILED")]
    errores = [ln for ln in out.splitlines() if ln.startswith("ERROR")]
    resumen = (out.strip().splitlines() or [""])[-1]
    return p.returncode, fallas, errores, resumen


def main():
    rc, f, e, r = correr()
    print(f"CONTROL sin mutar: rc={rc} | {r}", flush=True)
    if rc != 0:
        print("el control no está en verde; no se mide nada")
        return 1
    atrapadas = 0
    for nombre, ruta, viejo, nuevo in MUTACIONES:
        p = REPO / ruta
        original = p.read_bytes()
        texto = original.decode("utf-8").replace("\r\n", "\n")
        assert viejo in texto, f"{nombre}: patrón no encontrado en {ruta}"
        try:
            p.write_bytes(texto.replace(viejo, nuevo, 1).encode("utf-8"))
            rc, f, e, r = correr()
        finally:
            p.write_bytes(original)
        por_asercion = rc != 0 and f and not e
        atrapadas += bool(por_asercion)
        estado = "ATRAPADA" if por_asercion else ("CAE SIN ASERCION" if rc != 0 else "NO ATRAPADA")
        print(f"{estado:16s} | {nombre} | {r} | {f[:2]}", flush=True)
    print(f"\n{atrapadas} de {len(MUTACIONES)} atrapadas por aserción")
    rc, f, e, r = correr()
    print(f"CONTROL final sin mutar: rc={rc} | {r}")
    return 0 if atrapadas == len(MUTACIONES) and rc == 0 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
