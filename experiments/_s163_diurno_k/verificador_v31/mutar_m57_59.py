import sys, json, subprocess, pathlib, os
copia = pathlib.Path(sys.argv[1])
muts = {m["id"]: m for m in json.loads((copia / "experiments/_s163_diurno_k/mutaciones.json").read_text(encoding="utf-8"))["mutaciones"]}
f = copia / "experiments/_s163_diurno_k/evaluar_diurno_k.py"
orig = f.read_bytes().decode("utf-8").replace(chr(13) + chr(10), chr(10))
for i in ("M57", "M58", "M59"):
    m = muts[i]
    assert orig.count(m["viejo"]) == 1, (i, orig.count(m["viejo"]))
    f.write_bytes(orig.replace(m["viejo"], m["nuevo"]).encode("utf-8"))
    r = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(copia / "experiments/_s163_diurno_k/test_evaluar_diurno_k.py")],
                       capture_output=True, text=True, cwd=str(copia))
    fallos = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")]
    print(i, m["que"], "| rc", r.returncode, "|", fallos, "|", [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:])
f.write_bytes(orig.encode("utf-8"))
