# -*- coding: utf-8 -*-
"""Verificador v3, pregunta 2: ¿la regla nueva de N-5 (raiz con un brazo en 0 records) y la exigencia de 40 caracteres
pueden romper una corrida REAL del A/B sobre K?

Como todavia no hay corrida sobre K, se arma una con la forma exacta de una real: las diez medias ventanas de C0
(C:/Users/nmend/AppData/Local/Temp/claude/diurno_eval/W2a..W6b, 9.762 records del control y 17.552 del diurno), copiadas a
D:/vrp-trabajo/temporales/v3_raices_k/ con los directorios y logs renombrados a los brazos K, la linea FLAGS_BRAZO con
los tres flags de K, y en cada record triggered_test1 = False, test1_roi -> ctx_cluster y regimen = {perfil K, sha
FALSO de 40 caracteres}. Lo unico que se toca es lo que H2a y el cableado leen: la forma (raices, volcanes, conteos,
fechas) es la real.

Escenarios sobre cableado_records (la funcion de H2a del evaluador, importada sin copiar):
  a. las diez raices disfrazadas, limpias                     -> esperado: sin problemas, conteos 9762 / 17552
  b. a + una raiz de repeticion con SOLO el brazo diurno de un volcan (PREREGISTRO §7: «una repeticion por cobertura
     se agrega como otra --raiz despues de la original»)       -> ¿la regla N-5 la marca como rota?
  c. a + una raiz de repeticion con los DOS brazos de un volcan -> esperado: sin problemas
  d. a con un volcan sin JSON en el control de una raiz         -> H2a no lo ve (es trabajo de la cobertura); se informa
  e. a con UN record de una raiz del medio con el sha del tag abreviado a 12 -> control positivo: tiene que salir roto
Y una corrida de punta a punta de evaluar_diurno.py con --brazos K --base k --sha-codigo <sha falso> (stdout a archivo).

Las dos preguntas del instrumento: (1) si N-5 rompiera una corrida real, el escenario a o b lo veria, porque usan las
raices con su forma real; (2) si el disfraz no hubiera pasado (el script muerto), a daria 0 records y el control
positivo e no saldria roto: los dos se imprimen.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ORIGEN = Path("C:/Users/nmend/AppData/Local/Temp/claude/diurno_eval")
DEST = Path("D:/vrp-trabajo/temporales/v3_raices_k")
EVAL = Path(__file__).resolve().parents[1] / "evaluar_diurno.py"
C0 = ("_s151_ab_diurno_control", "_s151_ab_diurno_on")
K = ("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on")
SHA = "f" * 8 + "0123456789abcdef0123456789abcdef"
assert len(SHA) == 40


def disfrazar():
    if DEST.exists():
        shutil.rmtree(DEST)
    for raiz in sorted(ORIGEN.iterdir()):
        if not raiz.is_dir():
            continue
        for c0, k in zip(C0, K):
            (DEST / raiz.name / k).mkdir(parents=True)
            for p in sorted((raiz / c0).glob("*.json")):
                d = json.loads(p.read_text(encoding="utf-8"))
                for r in d.get("records", []):
                    r["triggered_test1"] = False
                    if r.get("final_hotspot_source") == "test1_roi":
                        r["final_hotspot_source"] = "ctx_cluster"
                    r["regimen"] = {"perfil": k, "codigo_sha": SHA, "origen": "actions"}
                (DEST / raiz.name / k / p.name).write_text(json.dumps(d), encoding="utf-8")
        (DEST / raiz.name / "logs").mkdir()
        for p in sorted((raiz / "logs").glob("*.log")):
            txt = p.read_text(encoding="utf-8", errors="replace")
            for c0, k in zip(C0, K):
                txt = txt.replace(c0, k)
            txt = (txt.replace('"ENABLE_TEST1_PATH": true', '"ENABLE_TEST1_PATH": false')
                      .replace('"ENABLE_TESTS_23_PROSE_BRANCH": false', '"ENABLE_TESTS_23_PROSE_BRANCH": true')
                      .replace('"ENABLE_MODIS_B22_PRIMARY": false', '"ENABLE_MODIS_B22_PRIMARY": true'))
            nombre = p.name
            for c0, k in zip(C0, K):
                nombre = nombre.replace(c0, k)
            (DEST / raiz.name / "logs" / nombre).write_text(txt, encoding="utf-8")


def main():
    disfrazar()
    sys.path.insert(0, str(EVAL.parent))
    os.chdir(EVAL.parent)
    import evaluar_diurno as ED
    ED.configurar_brazos(K[0], K[1], "k")
    raices = [str(DEST / w) for w in sorted(x.name for x in DEST.iterdir())]
    print("raices:", [Path(r).name for r in raices])

    def corre(etq, rr):
        cont = {}
        p = ED.cableado_records(rr, SHA, cont)
        print("%s: conteo %s | problemas %d | %s" % (etq, cont, len(p), p[:3]))
        return p

    corre("a. diez raices limpias", raices)

    rep_d = DEST.parent / "v3_rep_solo_diurno"
    if rep_d.exists():
        shutil.rmtree(rep_d)
    (rep_d / K[1]).mkdir(parents=True)
    shutil.copy2(DEST / "W4a" / K[1] / "Llaima.json", rep_d / K[1] / "Llaima.json")
    corre("b. + repeticion con solo el brazo diurno (Llaima, W4a)", raices + [str(rep_d)])

    rep_2 = DEST.parent / "v3_rep_dos_brazos"
    if rep_2.exists():
        shutil.rmtree(rep_2)
    for k in K:
        (rep_2 / k).mkdir(parents=True)
        shutil.copy2(DEST / "W4a" / k / "Llaima.json", rep_2 / k / "Llaima.json")
    corre("c. + repeticion con los dos brazos (Llaima, W4a)", raices + [str(rep_2)])

    falta = DEST / "W5a" / K[0] / "Copahue.json"
    guardado = falta.read_text(encoding="utf-8")
    falta.unlink()
    corre("d. sin Copahue.json en el control de W5a", raices)
    falta.write_text(guardado, encoding="utf-8")

    p = DEST / "W4b" / K[1] / "Villarrica.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    original = json.dumps(d)
    d["records"][5]["regimen"]["codigo_sha"] = SHA[:12]
    p.write_text(json.dumps(d), encoding="utf-8")
    corre("e. control positivo: un record de W4b diurno Villarrica con sha de 12", raices)
    p.write_text(original, encoding="utf-8")
    corre("a'. de vuelta limpio", raices)

    # punta a punta, sobre las diez raices disfrazadas (y con la repeticion de un solo brazo al final)
    for etq, sha, extra in (("sha completo", SHA, []), ("sha de 12", SHA[:12], []), ("sha en mayusculas", SHA.upper(), []),
                            ("con repeticion de un solo brazo", SHA, [str(rep_d)])):
        args = [sys.executable, "-I", "-B", str(EVAL)] + sum((["--raiz", r] for r in raices + extra), []) + [
            "--brazos", ",".join(K), "--base", "k", "--sha-codigo", sha, "--repetidas", "W2,W3,W5,W6"]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        o = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        sal = Path(__file__).with_name("m7_punta_a_punta_%s.txt" % etq.replace(" ", "_"))
        sal.write_text(o.stdout + "\n--- stderr (ultimas 40 lineas)\n" + "\n".join(o.stderr.splitlines()[-40:]) + "\nrc=%d\n" % o.returncode, encoding="utf-8")
        claves = [x for x in o.stdout.splitlines() if re.search(r"\[brazos\]|H2a|== VEREDICTO|records control", x)]
        ultima_err = (o.stderr.strip().splitlines() or [""])[-1]
        print("punta a punta, %s: rc %d | %s | stderr final: %s" % (etq, o.returncode, " || ".join(x.strip()[:220] for x in claves), ultima_err[:200]))


if __name__ == "__main__":
    main()
