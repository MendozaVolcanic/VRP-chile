# -*- coding: utf-8 -*-
"""S162, A/B de MxD03, control 4 del §8 (H9 del verificador del pre-registro): en los records que deciden (alertas,
negativos que K publica, expuestas) se exige que el K del arnes reproduzca el record de data/ exacto (publicacion y
pc.vrp_mw a 0,001 MW). 5.449 de los 5.465 records fueron escritos con un `pipeline/` distinto del de hoy, asi que una
diferencia puede ser deriva de version y no un arnes roto. Este paso re-corre K con el codigo del `codigo_sha` de cada
record retenido (git worktree de ese commit, proceso aparte con k_en_sha.py) y dice cual de las dos es:
  "deriva_de_version"  el K del commit viejo reproduce data/: el arnes esta bien, el codigo cambio desde entonces;
  "no_reproduce"       ni el K de main ni el del commit viejo dan data/: arnes roto o insumo distinto (el evaluador lo
                       declara INDECIDIBLE, §8 punto 4).
Corre despues de probe_mxd03_ab.py en el mismo job, sobre out/retenidos/, y borra cada HDF al terminar.

Las dos preguntas del instrumento:
1. Si el worktree viejo no se usara de verdad, ¿se veria? Si: k_en_sha.py afirma que pipeline se importo desde ese arbol
   y aqui se guarda el commit del arbol (`git rev-parse HEAD` dentro del worktree).
2. Si la re-corrida se cayera, ¿se veria distinto de «no reproduce»? Si: el estado es "error" con su traza.

Uso: python recorrer_en_sha.py --out out --parte N
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--parte", type=int, required=True)
    args = ap.parse_args()
    import probe_mxd03_ab as A     # publica (predicado de main con node) y difiere_de_guardado, sin copiarlos
    out = Path(args.out)
    pob = json.load(open(AQUI / "poblacion.json", encoding="utf-8"))
    pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
    filas = [json.loads(x) for x in open(out / f"ab_parte{args.parte:02d}.jsonl", encoding="utf-8")]
    pend = [f for f in filas if f.get("tipo") == "record" and f.get("retenido_para_sha")]
    res = open(out / f"recorridos_parte{args.parte:02d}.jsonl", "w", encoding="utf-8")
    arboles = {}
    errores = 0
    for f in pend:
        sha = f["retenido_para_sha"]
        r = {"vol": f["vol"], "dt": f["dt"], "clave": f["clave"], "codigo_sha": sha}
        try:
            if sha not in arboles:
                d = out / "arboles" / sha[:12]
                if not d.exists():
                    # el checkout del job es superficial: se trae solo ese commit (alcanzable desde main)
                    subprocess.run(["git", "-C", str(RAIZ), "fetch", "--depth", "1", "origin", sha], check=True,
                                   capture_output=True, text=True)
                    subprocess.run(["git", "-C", str(RAIZ), "worktree", "add", "--detach", str(d), sha], check=True,
                                   capture_output=True, text=True)
                arboles[sha] = d
            d = arboles[sha]
            r["arbol_head"] = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True,
                                             text=True).stdout.strip()
            l1b, geo = out / "retenidos" / f["l1b"], out / "retenidos" / f["geo"]
            p = subprocess.run([sys.executable, str(AQUI / "k_en_sha.py"), "--arbol", str(d), "--l1b", str(l1b),
                                "--geo", str(geo), "--vol", f["vol"]], capture_output=True, text=True, cwd=str(d))
            if p.returncode != 0:
                raise RuntimeError(p.stderr[-1500:])
            salida = json.loads(p.stdout.strip().splitlines()[-1])
            rec = salida["rec"]
            pub = A.P.publica([rec], f["inner"])[0] if rec is not None else 0
            resu = A.resumen(rec)
            r.update({"firma_omitidos": salida["firma_omitidos"], "pub_sha": pub,
                      "pc_vrp_sha": None if resu is None else resu.get("pc_vrp"),
                      "dc_sha": None if resu is None else resu.get("dc")})
            r["estado"] = ("no_reproduce" if A.difiere_de_guardado(pobf[(f["vol"], f["dt"])], resu, pub)
                           else "deriva_de_version")
        except Exception as e:  # noqa: BLE001
            r["estado"] = "error"
            r["error"] = f"{type(e).__name__}: {e}"[:2000]
            errores += 1
        res.write(json.dumps(r, ensure_ascii=False) + "\n")
        res.flush()
        print(json.dumps({k: r.get(k) for k in ("vol", "dt", "codigo_sha", "estado")}), flush=True)
    res.close()
    for p in (out / "retenidos").glob("*.hdf") if (out / "retenidos").exists() else []:
        p.unlink(missing_ok=True)
    print(f"parte {args.parte}: {len(pend)} records re-corridos en su codigo_sha, {errores} con error")
    sys.exit(2 if errores else 0)


if __name__ == "__main__":
    main()
