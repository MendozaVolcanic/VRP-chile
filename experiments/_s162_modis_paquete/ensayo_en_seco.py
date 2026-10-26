# -*- coding: utf-8 -*-
"""Ensayo en seco del evaluador de MOD-D sobre el lote real de S159 (run 39712862945, 150 pasadas MODIS), §10.1 del
pre-registro. No mide nada sobre el paquete: prueba la E/S del evaluador con datos reales (records de K tal como los
dejó el probe de S159, resultados del port, unión con la población de MOD-B, datos de producción y referencia
congelada para el contexto, re-etiquetado por subproceso, predicado con node).

QUÉ TIENE QUE DAR, y por qué (si da otra cosa, el evaluador o este ensayo están mal):
  * cobertura INDECIDIBLE: el lote trae 150 de las 5.465 pasadas (faltan 5.316).
  * port_s159 OK con 148 comunes evaluables (149 menos una escena invalida) y 91 con píxeles: es el mismo resultado, la identidad es por construcción; aquí sólo
    prueba que el control encuentra las pasadas comunes en un lote real.
  * k_produccion: el K de S159 lo corrió el árbol de S159 (0e18e1053), no main; las diferencias con data/ que deciden
    no tienen re-corrida en su codigo_sha, así que puede salir INDECIDIBLE. Se informa, no se espera un valor.
  * veredicto INDECIDIBLE (por la cobertura). Las pruebas del §4 corren igual y se imprimen.
Uso: python ensayo_en_seco.py --ref D:/vrp-trabajo/temporales/s162_mxd03/ref
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))


def convertir(dir_s159, destino):
    import banco_paridad as bp
    pob = json.load(open(RAIZ / "experiments/_s162_mxd03/poblacion.json", encoding="utf-8"))
    pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
    filas = []
    for p in sorted(Path(dir_s159).glob("resultados_MODIS_*.json")):
        filas += json.loads(p.read_text(encoding="utf-8"))
    out, casos, idx = [], [], []
    for r in filas:
        f = pobf.get((r["volcan"], r["hora_utc"]))
        if f is None:
            continue
        rec = ((r.get("K") or {}).get("record")) if r.get("estado") == "ok" else None
        slim = None
        if rec is not None:
            slim = {k: rec.get(k) for k in bp.CAMPOS_JS}
            slim["anomaly_pixels"] = slim.get("anomaly_pixels") or []
            casos.append([slim, f["inner"]])
            idx.append(len(out))
        pc = ((rec or {}).get("primary_cluster") or {}).get("vrp_mw")
        out.append({"tipo": "record", "estado": "ok" if r.get("estado") == "ok" else r.get("estado"),
                    "clave": f["clave"], "vol": f["vol"], "dt": f["dt"], "noche": f["noche"], "sensor": f["sensor"],
                    "lab": f["lab"], "z": f["z"], "inner": f["inner"], "k_slim": slim,
                    "brazos": {"K": {"pc_vrp": pc}, "K33": None}, "pub": {"K": 0, "K33": 0},
                    "k33_igual_k": None, "decide": f["lab"] in ("protegida", "bajo1") or bool(f["expuesta"])
                    or (f["lab"] == "neg_limpio" and bool(f["pub_guardada"])),
                    "port_estado": r.get("estado"), "port_grilla": r.get("port_estado"), "port": r.get("port"),
                    "saturados": r.get("saturados"), "s1": {"estado": "sin_grilla"},
                    "crater_mxd03": None})
    for i, p in zip(idx, bp.correr_node(casos)):
        out[i]["pub"]["K"] = int(p[4])
        out[i]["pub"]["K33"] = int(p[4])
    for o in out:
        o["k_difiere_de_guardado"] = (o["pub"]["K"] != pobf[(o["vol"], o["dt"])]["pub_guardada"])
    destino.mkdir(parents=True, exist_ok=True)
    with open(destino / "ab_parte00.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"tipo": "cabecera", "parte": 0, "commit": "s159-run-39712862945",
                             "blobs": {"experiments/_s159/portes/probe_portes.py": "8ec50e7bbb76c16e765a92e2773270c26c6ed9ac",
                                       "experiments/_s159/portes/mirova_port.py": "96769a89e6ee2233d86d973917c696cdb2405f29",
                                       "experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py": "07da701094f5aca7f14d7d9de39741589721c478"},
                             "sha256_frontend_index": None}) + "\n")
        for o in out:
            fh.write(json.dumps(o, default=float) + "\n")
    return len(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        n = convertir(AQUI / "referencia_s159", Path(td))
        print("pasadas del lote S159 unidas a la poblacion:", n)
        p = subprocess.run([sys.executable, "-I", str(AQUI / "evaluar_paquete.py"), "--art", td, "--ref", a.ref,
                            "--salida", str(Path(td) / "res.json")], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        print(p.stdout[-6000:])
        print(p.stderr[-2000:])
        res = json.loads((Path(td) / "res.json").read_text(encoding="utf-8")) if (Path(td) / "res.json").exists() else {}
        c = res.get("controles", {})
        print("== lo que el ensayo exige")
        exig = {"cobertura INDECIDIBLE": (c.get("cobertura") or {}).get("estado") == "INDECIDIBLE",
                "port_s159 OK con 148 comunes y 91 con pixeles": (c.get("port_s159") or {}).get("estado") == "OK"
                and c["port_s159"].get("comunes") == 148 and c["port_s159"].get("comunes_con_pixeles") == 91,
                "veredicto INDECIDIBLE": res.get("veredicto") == "INDECIDIBLE",
                "predicado INDECIDIBLE (la cabecera del ensayo no trae el hash del tablero)": (c.get("predicado") or {}).get("estado") == "INDECIDIBLE",
                "referencia y reetiquetado OK": (c.get("referencia") or {}).get("estado") == "OK"
                and (c.get("reetiquetado") or {}).get("estado") == "OK",
                # adenda 4: sin --commit la procedencia no puede quedar verde; el manifiesto del arbol si
                "procedencia INDECIDIBLE (sin --commit)": (c.get("procedencia") or {}).get("estado") == "INDECIDIBLE",
                "manifiesto OK": (c.get("manifiesto") or {}).get("estado") == "OK"}
        for k, v in exig.items():
            print("  %-48s %s" % (k, "SI" if v else "NO"))
        sys.exit(0 if p.returncode == 0 and all(exig.values()) else 1)


if __name__ == "__main__":
    main()
