import sys, json, subprocess, pathlib
copia=pathlib.Path(sys.argv[1]); spec=json.load(open(copia/"experiments/_s163_diurno_k/mutaciones_dias_excluidos.json",encoding="utf-8"))
for m in spec["mutaciones"]:
    f=copia/m["archivo"]; o=f.read_text(encoding="utf-8")
    assert o.count(m["viejo"])==1,(m["id"],o.count(m["viejo"]))
    f.write_text(o.replace(m["viejo"],m["nuevo"]),encoding="utf-8")
    p=subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider","-x","--tb=line",spec["pruebas"][0]],cwd=copia,capture_output=True,text=True)
    f.write_text(o,encoding="utf-8")
    out=p.stdout
    asercion=("AssertionError" in out) or ("assert " in out)
    print(m["id"], "rc=%d"%p.returncode, "asercion" if asercion else "SIN aserción (caída/otro)", "|", out.strip().splitlines()[-1][:110])
