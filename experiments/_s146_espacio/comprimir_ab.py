"""Comprime los artefactos de A/B y reprocesos (clase ARCHIVAR_COMPRIMIDO_AB y los data/_* de REVISAR)
a un zip por carpeta en experiments/_archivo_ab_local/ (ignorado por git). NO borra nada.
(1) Si la compresion estuviera rota, la verificacion testzip() y el conteo de entradas fallan.
(2) Si no hubiera nada que comprimir, el manifiesto sale vacio y el script lo dice.
"""
import json, os, zipfile, hashlib, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
inv = json.load(open("experiments/_s146_espacio/inventario_ignorados.json", encoding="utf-8"))
dest = "experiments/_archivo_ab_local"
os.makedirs(dest, exist_ok=True)
man = []
for f in inv["filas"]:
    p = f["ruta"].rstrip("/")
    if not (f["clase"] == "ARCHIVAR_COMPRIMIDO_AB" or (f["clase"] == "REVISAR" and p.startswith("data/_"))):
        continue
    if not os.path.isdir(p):
        continue
    zname = os.path.join(dest, p.replace("/", "__") + ".zip")
    n = 0
    with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for r, _, fs in os.walk(p):
            for x in fs:
                fp = os.path.join(r, x)
                z.write(fp, os.path.relpath(fp, ROOT)); n += 1
    with zipfile.ZipFile(zname) as z:
        bad = z.testzip(); ne = len(z.namelist())
    ok = bad is None and ne == n
    man.append({"origen": p, "zip": zname.replace("\\", "/"), "archivos": n, "mb_origen": f["mb"],
                "mb_zip": round(os.path.getsize(zname) / 1e6, 2), "verificado": ok})
    print(p, f["mb"], "->", man[-1]["mb_zip"], "OK" if ok else "FALLA", flush=True)
json.dump(man, open("experiments/_s146_espacio/manifiesto_zip.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("total origen MB", round(sum(m["mb_origen"] for m in man)), "zip MB", round(sum(m["mb_zip"] for m in man)),
      "carpetas", len(man), "todas verificadas", all(m["verificado"] for m in man))
sys.exit(0 if man and all(m["verificado"] for m in man) else 1)
