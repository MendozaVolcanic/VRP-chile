"""S163 H3: ¿el tablero muestra hoy records del detector anterior a K?

Censo de los 11 Tier A en data/mirova_equivalent/<vol>.json leído de un commit dado (por defecto origin/main),
sin tocar el checkout. Para cada record decide el régimen por DOS caminos independientes:

  (a) la marca `regimen` que escribe pipeline/store.py:_marca_regimen (perfil + codigo_sha del run). Es K si el
      codigo_sha desciende del merge de K (#850, 34cea39e4, 2026-10-18 09:57:30 UTC) y el perfil, leído en ESE sha,
      trae los tres flags de K (enable_test1_path false, enable_tests_23_prose_branch true,
      enable_modis_b22_primary true). Sin marca, sha desconocido o flags distintos: NO-K (o SIN DATO si el sha no
      está en el repo local).
  (b) la huella física del Test 1 integrado, que K apaga: triggered_test1 True o final_hotspot_source test1/test1_roi.

«Publica» es el predicado del tablero ejecutado con node sobre frontend/index.html del mismo commit
(banco_paridad._JS: isSummitDetection ∧ isValidDetection ∧ ¬isThermalArtifact ∧ mirovaEqVrpDisplay > 0), A97.

Pregunta 1 del instrumento (¿puede dar distinto de cero?): el control positivo corre el mismo censo sobre el tag
pre-s158-reemplazo-k (corpus anterior a #883), donde el caso de S162 (Láscar 2026-08-22 05:06) era del detector
anterior. Uso: python -I censo_h3.py [commit]   (salida a stdout; sólo lectura)
"""
import collections
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402

COMMIT = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
K_MERGE = "34cea39e4b64f0862e4bad949016a57ea181f8c4"
VOLS = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima", "Chaiten",
        "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
FLAGS_K = {"enable_test1_path": "false", "enable_tests_23_prose_branch": "true", "enable_modis_b22_primary": "true"}


def git(*a):
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    return subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", env=env)


def flags_perfil(sha, perfil):
    """Flags de K efectivos del perfil en ese sha (siguiendo un `extends` de un nivel)."""
    vals = {}
    nombre = perfil
    for _ in range(3):
        o = git("show", f"{sha}:pipeline/profiles/{nombre}.yaml")
        if o.returncode != 0:
            return None
        txt = o.stdout
        for f in FLAGS_K:
            m = re.search(rf"^\s*{f}:\s*(\w+)", txt, re.M)
            if m and f not in vals:
                vals[f] = m.group(1).lower()
        m = re.search(r"^extends:\s*(\S+)", txt, re.M)
        if not m:
            break
        nombre = m.group(1)
    return vals


_cache = {}


def regimen_de(g):
    if not g:
        return "NO-K (sin marca)"
    clave = (g.get("perfil"), g.get("codigo_sha"))
    if clave in _cache:
        return _cache[clave]
    perfil, sha = clave
    if not sha or git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        res = "SIN DATO (sha ausente)"
    elif git("merge-base", "--is-ancestor", K_MERGE, sha).returncode != 0:
        res = "NO-K (sha anterior a #850)"
    else:
        fl = flags_perfil(sha, perfil)
        res = "K" if fl is not None and all(fl.get(f) == v for f, v in FLAGS_K.items()) else f"NO-K (flags {fl})"
    _cache[clave] = res
    return res


def huella_test1(r):
    return bool(r.get("triggered_test1")) or r.get("final_hotspot_source") in ("test1", "test1_roi")


def main():
    sha = git("rev-parse", COMMIT).stdout.strip()
    html = git("show", f"{sha}:frontend/index.html").stdout
    bp.HTML = Path(os.environ.get("TMP", "/tmp")) / f"h3_index_{sha[:9]}.html"
    bp.HTML.write_text(html, encoding="utf-8")
    inner = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', html):
        inner.setdefault(m.group(1), float(m.group(2)))
    print(f"commit medido: {COMMIT} = {sha}")
    print(f"control de identidad del predicado (5 isValidDetection, 2 publica): {bp.control_identidad_predicado()}")

    filas = []  # (vol, sensor, mes, regimen, huella, publica, noche_key, datetime)
    for v in VOLS:
        recs = json.loads(git("show", f"{sha}:data/mirova_equivalent/{v}.json").stdout)["records"]
        pub = bp.correr_node([[r, inner[v]] for r in recs])
        for r, p in zip(recs, pub):
            dtu = r["datetime_utc"]
            filas.append((v, r.get("sensor"), dtu[:7], regimen_de(r.get("regimen")), huella_test1(r), p[4], dtu))

    n = len(filas)
    fechas = sorted(f[6] for f in filas)
    print(f"\nDenominador: {n} records de los 11 Tier A, ventana de observación {fechas[0]} a {fechas[-1]} UTC")
    print("Régimen por la marca:", dict(collections.Counter(f[3] for f in filas)))
    print("Records con huella del Test 1 integrado:", sum(f[4] for f in filas))
    print("Publicados por el tablero:", sum(f[5] for f in filas))

    nok = [f for f in filas if f[3] != "K"]
    nok_pub = [f for f in nok if f[5]]
    hue_pub = [f for f in filas if f[4] and f[5]]
    print(f"\nNO-K o SIN DATO (cualquier publicación): {len(nok)} de {n}")
    print(f"NO-K o SIN DATO que el tablero PUBLICA: {len(nok_pub)} de {sum(f[5] for f in filas)} publicados")
    print(f"Con huella del Test 1 que el tablero PUBLICA: {len(hue_pub)}")

    def tabla(sub, titulo):
        print(f"\n== {titulo} (volcán / sensor / mes de observación: n) ==")
        c = collections.Counter((f[0], f[1], f[2]) for f in sub)
        if not c:
            print("  (ninguno)")
        for k in sorted(c):
            print(f"  {k[0]:20s} {k[1]:18s} {k[2]}: {c[k]}")

    tabla(nok_pub, "NO-K publicados")
    tabla(hue_pub, "huella Test 1 publicados")

    # Ventana previa a la marca de régimen de los datos (S155): observaciones antes del 2026-09-18
    pre = [f for f in filas if f[6] < "2026-09-18"]
    print(f"\nObservaciones anteriores al 2026-09-18: {len(pre)}; de ellas NO-K: {sum(f[3] != 'K' for f in pre)}; "
          f"publicadas: {sum(f[5] for f in pre)}; publicadas NO-K: {sum(f[5] and f[3] != 'K' for f in pre)}")

    # Por mes de observación, régimen (todas, publicadas)
    print("\n== por mes de observación: total / K / NO-K / publicados / publicados NO-K ==")
    meses = sorted({f[2] for f in filas})
    for m in meses:
        s = [f for f in filas if f[2] == m]
        print(f"  {m}: {len(s)} / {sum(f[3] == 'K' for f in s)} / {sum(f[3] != 'K' for f in s)} / "
              f"{sum(f[5] for f in s)} / {sum(f[5] and f[3] != 'K' for f in s)}")

    # Caso de S162
    for f in filas:
        if f[0] == "Lascar" and f[6] == "2026-08-22 05:06":
            print(f"\nCaso S162 Láscar 2026-08-22 05:06 {f[1]}: régimen {f[3]}, huella {f[4]}, publica {f[5]}")


if __name__ == "__main__":
    main()
